# /// script
# requires-python = ">=3.12"
# dependencies = ["dspy"]
# ///
"""
DSPy-based evaluation of the Terraform Style Guide Agent Skill.

Two-pass evaluation:
  Pass 1 (SKILL.md only): dimensions the agent sees on first load
  Pass 2 (SKILL.md + references/): dimensions measuring full skill coverage

Aligned with the agentskills.io skill-creator specification.
"""

import json
import os
import textwrap
from pathlib import Path

import dspy


# ---------------------------------------------------------------------------
# DSPy Signatures
# ---------------------------------------------------------------------------


class EvaluateDimension(dspy.Signature):
    """Evaluate an AI-agent skill document on a single quality dimension.

    You are an expert evaluator of Agent Skills — modular instruction documents
    that extend AI coding assistants (GitHub Copilot, Claude, etc.) with
    domain-specific knowledge.

    Score the skill strictly on the given dimension.  Return:
      - score: integer 1-5  (1=poor, 3=adequate, 5=excellent)
      - evidence: 1-2 sentences citing specific content from the skill
      - suggestions: concrete, actionable improvements (empty list if score >= 4)
    """

    skill_content: str = dspy.InputField(desc="Full text of the SKILL.md file")
    dimension: str = dspy.InputField(desc="Quality dimension to evaluate")
    criteria: str = dspy.InputField(desc="Detailed rubric for this dimension (1-5 scale)")
    score: int = dspy.OutputField(desc="Integer score from 1 to 5")
    evidence: str = dspy.OutputField(desc="1-2 sentences of supporting evidence from the skill")
    suggestions: list[str] = dspy.OutputField(desc="List of concrete improvement suggestions (empty if score >= 4)")


class SynthesizeReport(dspy.Signature):
    """Synthesize per-dimension evaluations into a final improvement report.

    Produce a prioritised, actionable improvement plan.  Focus on the
    dimensions with the lowest scores first.  Each recommendation must be
    concrete (say exactly what to add/change/remove and where).
    """

    skill_content: str = dspy.InputField(desc="Full text of the SKILL.md")
    dimension_results: str = dspy.InputField(desc="JSON array of per-dimension evaluation results")
    overall_score: float = dspy.InputField(desc="Weighted overall score (0-1)")
    executive_summary: str = dspy.OutputField(desc="2-3 sentence overall assessment")
    top_recommendations: list[str] = dspy.OutputField(desc="Top 5-7 prioritised, concrete recommendations")
    strengths: list[str] = dspy.OutputField(desc="Top 3-4 strengths to preserve")


# ---------------------------------------------------------------------------
# Rubric
# ---------------------------------------------------------------------------

# Dimensions evaluated against SKILL.md only (what the agent sees first)
SKILL_ONLY_DIMS = {
    "description_trigger_quality",
    "context_efficiency",
    "structural_quality",
}

# Dimensions evaluated against SKILL.md + references/ (full skill package)
FULL_PACKAGE_DIMS = {
    "actionability",
    "example_quality",
    "completeness",
    "error_prevention",
}

RUBRIC = {
    "description_trigger_quality": {
        "weight": 0.15,
        "criteria": textwrap.dedent("""\
            Evaluate the YAML frontmatter 'description' field as a triggering mechanism.
            1 = Missing or vague, would rarely trigger correctly
            2 = Partially describes what skill does but missing when-to-use triggers
            3 = Describes what AND when, but could be more comprehensive
            4 = Clear what + when, includes key trigger phrases
            5 = Excellent: comprehensive what + when, lists explicit trigger phrases,
                includes negative triggers (when NOT to use)"""),
    },
    "context_efficiency": {
        "weight": 0.15,
        "criteria": textwrap.dedent("""\
            Evaluate token efficiency and progressive disclosure.
            1 = Bloated; includes information an LLM already knows; no references split
            2 = Some redundancy; could move large sections to references/
            3 = Reasonable length but some sections could be split out
            4 = Concise; only non-obvious information; optional detail in references
            5 = Excellent: every paragraph earns its tokens; progressive disclosure
                with clear references for deeper content; under 500 lines"""),
    },
    "actionability": {
        "weight": 0.20,
        "criteria": textwrap.dedent("""\
            Evaluate how actionable the instructions are for an AI code-generation agent.
            1 = Mostly descriptive prose; agent would need to interpret intent
            2 = Some actionable rules but many are implicit or vague
            3 = Clear rules exist but gaps in edge-case handling
            4 = Concrete rules with good/bad examples covering common cases
            5 = Excellent: imperative rules, input/output examples for every convention,
                edge-case handling, and decision trees for ambiguous situations"""),
    },
    "example_quality": {
        "weight": 0.15,
        "criteria": textwrap.dedent("""\
            Evaluate the quality and coverage of code examples across the entire
            skill package (SKILL.md + all reference files).
            1 = No examples or trivial/broken ones
            2 = Few examples; missing bad-vs-good comparisons
            3 = Adequate examples but gaps in coverage
            4 = Good coverage with bad/good pairs for key conventions
            5 = Excellent: comprehensive bad/good pairs, realistic complexity,
                covering all major sections; examples are self-contained and
                could be used as test fixtures"""),
    },
    "completeness": {
        "weight": 0.15,
        "criteria": textwrap.dedent("""\
            Evaluate coverage of Terraform best practices across the entire skill
            package (SKILL.md + all reference files) for an agent generating HCL.
            1 = Covers only basic formatting
            2 = Covers formatting + naming but misses important areas
            3 = Covers most standard areas but has notable gaps
            4 = Comprehensive; covers formatting, naming, variables, outputs,
                modules, state, security, testing
            5 = Excellent: covers everything in 4 plus: modules, workspaces,
                data sources patterns, moved blocks, import blocks, check blocks,
                CI/CD integration, state backend configuration"""),
    },
    "structural_quality": {
        "weight": 0.10,
        "criteria": textwrap.dedent("""\
            Evaluate the document's organization and navigability for an AI agent.
            1 = Poorly organized; hard to find specific guidance
            2 = Basic headings but inconsistent structure
            3 = Well-structured with clear sections
            4 = Logical flow; easy to locate rules for any topic
            5 = Excellent: scannable structure, consistent section pattern,
                clear hierarchy; agent can extract rules without ambiguity"""),
    },
    "error_prevention": {
        "weight": 0.10,
        "criteria": textwrap.dedent("""\
            Evaluate how well the skill package (SKILL.md + all reference files)
            prevents common Terraform mistakes.
            1 = No mention of pitfalls or common errors
            2 = Mentions a few warnings in passing
            3 = Addresses some common mistakes but could be more systematic
            4 = Covers key pitfalls (state issues, dependency cycles, etc.)
            5 = Excellent: systematic anti-patterns section, common gotchas,
                explicit "do NOT" rules, and recovery guidance"""),
    },
}


# ---------------------------------------------------------------------------
# Evaluation pipeline
# ---------------------------------------------------------------------------


def load_references(skill_dir: Path) -> str:
    """Concatenate all references/*.md files into a single string."""
    refs_dir = skill_dir / "references"
    if not refs_dir.is_dir():
        return ""
    parts = []
    for md_file in sorted(refs_dir.glob("*.md")):
        parts.append(f"\n\n--- {md_file.name} ---\n\n{md_file.read_text()}")
    return "".join(parts)


def run_evaluation(skill_path: str) -> None:
    skill_file = Path(skill_path)
    skill_dir = skill_file.parent

    # Read SKILL.md
    skill_content = skill_file.read_text()

    # Read references
    refs_content = load_references(skill_dir)
    full_content = skill_content + refs_content

    print(f"Evaluating: {skill_path}")
    print(f"SKILL.md: {len(skill_content)} chars, ~{len(skill_content) // 4} tokens")
    if refs_content:
        print(f"References: {len(refs_content)} chars, ~{len(refs_content) // 4} tokens")
        print(f"Full package: {len(full_content)} chars, ~{len(full_content) // 4} tokens")
    print("=" * 70)

    evaluate = dspy.Predict(EvaluateDimension)
    synthesize = dspy.Predict(SynthesizeReport)

    # Evaluate each dimension with appropriate content scope
    results = []
    weighted_total = 0.0

    for dim_name, dim_cfg in RUBRIC.items():
        if dim_name in SKILL_ONLY_DIMS:
            content = skill_content
            scope = "SKILL.md only"
        else:
            content = full_content
            scope = "full package"

        print(f"\n  Evaluating: {dim_name} (weight={dim_cfg['weight']}, {scope})...")
        pred = evaluate(
            skill_content=content,
            dimension=dim_name,
            criteria=dim_cfg["criteria"],
        )
        score = int(pred.score)
        weighted_total += score * dim_cfg["weight"]

        result = {
            "dimension": dim_name,
            "score": score,
            "weight": dim_cfg["weight"],
            "weighted_score": round(score * dim_cfg["weight"], 3),
            "scope": scope,
            "evidence": pred.evidence,
            "suggestions": pred.suggestions,
        }
        results.append(result)

        bar = "█" * score + "░" * (5 - score)
        print(f"    Score: {bar} {score}/5")
        print(f"    Evidence: {pred.evidence}")
        if pred.suggestions:
            for s in pred.suggestions:
                print(f"    → {s}")

    overall = round(weighted_total / 5, 3)  # normalize to 0-1
    print("\n" + "=" * 70)
    print(f"  OVERALL WEIGHTED SCORE: {overall:.1%} ({weighted_total:.2f}/5.00)")
    print("=" * 70)

    # Synthesize final report
    print("\nSynthesizing improvement report...")
    report = synthesize(
        skill_content=full_content,
        dimension_results=json.dumps(results, indent=2),
        overall_score=overall,
    )

    print("\n" + "=" * 70)
    print("  EVALUATION REPORT")
    print("=" * 70)

    print(f"\n## Executive Summary\n\n{report.executive_summary}")

    print("\n## Dimension Scores\n")
    print(f"{'Dimension':<30} {'Score':>5}  {'Weighted':>8}  {'Scope'}")
    print("-" * 70)
    for r in sorted(results, key=lambda x: x["score"]):
        bar = "█" * r["score"] + "░" * (5 - r["score"])
        print(f"{r['dimension']:<30} {bar} {r['score']}/5  ({r['weighted_score']:.3f})  [{r['scope']}]")
    print("-" * 70)
    print(f"{'OVERALL':<30}       {weighted_total:.2f}/5.00 = {overall:.1%}")

    print("\n## Strengths\n")
    for s in report.strengths:
        print(f"  ✓ {s}")

    print("\n## Top Recommendations (Prioritised)\n")
    for i, rec in enumerate(report.top_recommendations, 1):
        print(f"  {i}. {rec}")

    print("\n## Per-Dimension Details\n")
    for r in results:
        print(f"### {r['dimension']} — {r['score']}/5")
        print(f"  Evidence: {r['evidence']}")
        if r["suggestions"]:
            print("  Suggestions:")
            for s in r["suggestions"]:
                print(f"    → {s}")
        print()


if __name__ == "__main__":
    # Configure DSPy with Azure OpenAI
    lm = dspy.LM(
        model=f"azure/{os.environ['AZURE_OPENAI_DEPLOYMENT']}",
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_base=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version="2025-01-01-preview",
        temperature=1.0,
        max_tokens=16000,
    )
    dspy.configure(lm=lm)

    run_evaluation("SKILL.md")
