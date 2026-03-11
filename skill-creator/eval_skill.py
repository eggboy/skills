# /// script
# requires-python = ">=3.12"
# dependencies = ["dspy"]
# ///
"""DSPy-based evaluation of the Skill Creator Agent Skill.

Two-pass evaluation:
  Pass 1 (SKILL.md only): dimensions the agent sees on first load
  Pass 2 (SKILL.md + references/): dimensions measuring full skill coverage

Uses dual-reviewer reconciliation for scoring stability:
  - heuristic observations extracted directly from files,
  - a DSPy fact-extraction pass,
  - two independent rubric judges (strict + pragmatic), and
  - a DSPy reconciliation pass that produces the final score.
"""

import json
import os
import textwrap
from pathlib import Path

import dspy

# ---------------------------------------------------------------------------
# DSPy Signatures
# ---------------------------------------------------------------------------


class ExtractObservableFacts(dspy.Signature):
    """Extract grounded facts from the skill package before scoring.

    You are preparing evidence for an evaluator of Agent Skills.

    Extract only facts directly supported by the provided content. Do not score
    the skill. Focus on observable details such as:
      - files and references present,
      - whether negative triggers exist,
      - whether examples show complete skill directory structures,
      - whether step-by-step workflows are present,
      - whether bad-vs-good comparisons exist,
      - whether frontmatter field documentation is comprehensive,
      - whether progressive disclosure patterns are demonstrated.
    """

    skill_content: str = dspy.InputField(desc="Full text of the skill content in scope")
    heuristic_facts: str = dspy.InputField(desc="JSON summary of facts found via deterministic code")
    observable_facts: list[str] = dspy.OutputField(desc="Short, grounded fact bullets supported by the content")


class EvaluateDimension(dspy.Signature):
    """Evaluate a single dimension using grounded evidence and a reviewer stance.

    Score the skill strictly on the given dimension.

    Requirements:
      - Use the rubric exactly.
      - Base claims only on the provided content and facts.
      - Do not reward implied content that is not present.
      - If uncertain, score conservatively.
    """

    skill_content: str = dspy.InputField(desc="Full text of the skill content in scope")
    dimension: str = dspy.InputField(desc="Quality dimension to evaluate")
    criteria: str = dspy.InputField(desc="Detailed rubric for this dimension (1-5 scale)")
    reviewer_stance: str = dspy.InputField(desc="Reviewer stance such as strict or pragmatic")
    observable_facts: str = dspy.InputField(desc="Grounded fact bullets and heuristic observations")
    score: int = dspy.OutputField(desc="Integer score from 1 to 5")
    evidence: str = dspy.OutputField(desc="1-2 sentences of evidence grounded in the provided content")
    suggestions: list[str] = dspy.OutputField(desc="Concrete improvement suggestions; empty if score >= 4")


class ReconcileDimension(dspy.Signature):
    """Reconcile two judge outputs into one final dimension result.

    Produce the final score after comparing the two reviewers. Prefer the more
    conservative score when evidence is weak. Do not average mechanically;
    instead, pick the score best justified by the evidence.
    """

    dimension: str = dspy.InputField(desc="Quality dimension being reconciled")
    criteria: str = dspy.InputField(desc="Detailed rubric for this dimension")
    observable_facts: str = dspy.InputField(desc="Grounded fact bullets and heuristic observations")
    reviewer_a: str = dspy.InputField(desc="JSON for reviewer A result")
    reviewer_b: str = dspy.InputField(desc="JSON for reviewer B result")
    final_score: int = dspy.OutputField(desc="Final integer score from 1 to 5")
    evidence: str = dspy.OutputField(desc="Best supported evidence for the final score")
    suggestions: list[str] = dspy.OutputField(desc="Merged, deduplicated suggestions")
    confidence: str = dspy.OutputField(desc="high, medium, or low")


class SynthesizeReport(dspy.Signature):
    """Synthesize per-dimension evaluations into a final improvement report.

    Produce a prioritized, actionable improvement plan for the skill-creator skill.
    Focus on the dimensions with the lowest scores first. Each recommendation must
    be concrete (say exactly what to add/change/remove and where).
    """

    skill_content: str = dspy.InputField(desc="Full text of the SKILL.md + references")
    dimension_results: str = dspy.InputField(desc="JSON array of reconciled per-dimension evaluation results")
    overall_score: float = dspy.InputField(desc="Weighted overall score (0-1)")
    executive_summary: str = dspy.OutputField(desc="2-3 sentence overall assessment")
    top_recommendations: list[str] = dspy.OutputField(desc="Top 5-7 prioritized recommendations")
    strengths: list[str] = dspy.OutputField(desc="Top 3-4 strengths to preserve")


# ---------------------------------------------------------------------------
# Rubric — Skill Creator-specific dimensions
# ---------------------------------------------------------------------------

# Dimensions evaluated against SKILL.md only (what the agent sees first)
SKILL_ONLY_DIMS = {
    "description_trigger_quality",
    "context_efficiency",
    "structural_quality",
}

# Dimensions evaluated against SKILL.md + references/ (full skill package)
FULL_PACKAGE_DIMS = {
    "process_completeness",
    "example_quality",
    "progressive_disclosure_guidance",
    "error_prevention",
}

RUBRIC = {
    "description_trigger_quality": {
        "weight": 0.15,
        "criteria": textwrap.dedent("""\
            Evaluate the YAML frontmatter 'description' field as a triggering mechanism.
            The skill should trigger when users want to create, update, or review
            Agent Skills for AI assistants.
            1 = Missing or vague, would rarely trigger correctly
            2 = Partially describes what skill does but missing when-to-use triggers
            3 = Describes what AND when, but could be more comprehensive
            4 = Clear what + when, includes key trigger phrases (e.g., "create skill",
                "update skill", "SKILL.md", "agentskills.io")
            5 = Excellent: comprehensive what + when, lists explicit positive triggers
                AND negative triggers (when NOT to use — e.g., "not for using
                existing skills" or "not for general documentation"); mentions
                target audience (GitHub Copilot, Claude, etc.)"""),
    },
    "context_efficiency": {
        "weight": 0.15,
        "criteria": textwrap.dedent("""\
            Evaluate token efficiency and progressive disclosure of SKILL.md itself.
            A skill about creating skills should exemplify its own advice.
            1 = Bloated; includes information an LLM already knows; no references split
            2 = Some redundancy; large sections could move to references/
            3 = Reasonable length but some sections could be split out
            4 = Concise; only non-obvious rules inline; detailed patterns in references
            5 = Excellent: every paragraph earns its tokens; progressive disclosure
                with clear references for deeper content; SKILL.md under 500 lines;
                the skill practices what it preaches about token efficiency"""),
    },
    "structural_quality": {
        "weight": 0.10,
        "criteria": textwrap.dedent("""\
            Evaluate the document's organization and navigability for an AI agent.
            1 = Poorly organized; hard to find specific guidance
            2 = Basic headings but inconsistent structure
            3 = Well-structured with clear sections
            4 = Logical flow; easy to locate rules for any topic; scannable
            5 = Excellent: consistent section pattern, clear hierarchy, agent can
                extract rules without ambiguity; the structure itself demonstrates
                best practices (core principles → anatomy → process → references)"""),
    },
    "process_completeness": {
        "weight": 0.20,
        "criteria": textwrap.dedent("""\
            Evaluate coverage of the complete skill creation lifecycle across the
            entire skill package (SKILL.md + all reference files).
            1 = Covers only a few steps; agent would be lost creating a skill
            2 = Covers basic creation but misses planning, iteration, or testing
            3 = Covers most steps but has notable gaps (e.g., no iteration guidance,
                no advice on when to use scripts vs references vs assets)
            4 = Comprehensive lifecycle: understanding → planning → initialization →
                editing → iteration; includes guidance on choosing resource types
                (scripts, references, assets) and when each is appropriate
            5 = Excellent: complete lifecycle with decision frameworks, covers
                frontmatter writing, body writing, resource selection, testing,
                iteration based on real usage; addresses cross-cutting concerns
                like versioning, compatibility, and multi-agent support"""),
    },
    "example_quality": {
        "weight": 0.20,
        "criteria": textwrap.dedent("""\
            Evaluate the quality and coverage of examples across the entire skill
            package (SKILL.md + all reference files). Examples should demonstrate
            real skill structures, YAML frontmatter, directory layouts, and
            patterns that an agent could directly apply.
            1 = No examples or trivial/broken ones
            2 = Few examples; missing diversity of skill types
            3 = Adequate examples but gaps in coverage (e.g., only simple skills,
                no complex multi-reference skills, no script examples)
            4 = Good coverage with examples for: frontmatter fields, directory
                layouts, progressive disclosure patterns, workflow patterns,
                output patterns; examples represent different skill complexities
            5 = Excellent: comprehensive examples covering simple to complex skills,
                bad-vs-good comparisons for common mistakes, complete SKILL.md
                samples, diverse skill types (code-gen, workflow, domain-knowledge),
                examples for all reference files; could serve as test fixtures"""),
    },
    "progressive_disclosure_guidance": {
        "weight": 0.10,
        "criteria": textwrap.dedent("""\
            Evaluate how well the skill teaches progressive disclosure — the
            three-level loading system (metadata → SKILL.md body → resources)
            that is central to effective skill design.
            1 = No mention of progressive disclosure or context management
            2 = Mentions the concept but lacks actionable guidance
            3 = Explains the three levels but missing concrete patterns for
                when/how to split content
            4 = Clear explanation with splitting guidelines, line limits, and
                reference linking patterns
            5 = Excellent: comprehensive guidance with decision framework for
                what belongs at each level, concrete examples of before/after
                splits, file size guidelines, table-of-contents requirements
                for long references, and anti-patterns to avoid"""),
    },
    "error_prevention": {
        "weight": 0.10,
        "criteria": textwrap.dedent("""\
            Evaluate how well the skill package prevents common skill-creation
            mistakes across SKILL.md + all reference files.
            1 = No mention of pitfalls or common errors
            2 = Mentions a few warnings in passing
            3 = Addresses some common mistakes but could be more systematic
            4 = Covers key pitfalls: bloated SKILL.md, poor description triggers,
                missing reference links, including LLM-obvious information,
                auxiliary files that don't belong
            5 = Excellent: systematic anti-patterns section, common gotchas
                (e.g., description too short for triggering, SKILL.md too long,
                orphaned references not linked from SKILL.md, scripts without
                PEP 723 metadata, inconsistent name field vs directory name),
                explicit "do NOT" rules, and recovery guidance"""),
    },
}


# ---------------------------------------------------------------------------
# Evaluation helpers
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


def build_heuristic_facts(skill_content: str, refs_content: str, skill_dir: Path) -> dict:
    """Build deterministic observations to ground DSPy scoring."""
    references_dir = skill_dir / "references"
    reference_files = sorted(path.name for path in references_dir.glob("*.md")) if references_dir.is_dir() else []
    scripts_dir = skill_dir / "scripts"
    script_files = sorted(path.name for path in scripts_dir.glob("*")) if scripts_dir.is_dir() else []
    assets_dir = skill_dir / "assets"
    asset_files = sorted(path.name for path in assets_dir.glob("*")) if assets_dir.is_dir() else []

    full_content = skill_content + refs_content

    # Count examples by looking for code blocks
    code_block_count = skill_content.count("```")
    refs_code_block_count = refs_content.count("```")

    # Check for key structural elements
    has_yaml_frontmatter = skill_content.startswith("---")
    has_directory_tree = "├──" in full_content or "└──" in full_content
    has_step_numbering = any(f"### Step {i}" in skill_content for i in range(1, 6))
    has_workflow_patterns = "## Sequential Workflows" in refs_content or "## Conditional Workflows" in refs_content
    has_output_patterns = "## Template Pattern" in refs_content or "## Examples Pattern" in refs_content

    # Description analysis
    description = ""
    if has_yaml_frontmatter:
        frontmatter_end = skill_content.find("---", 3)
        if frontmatter_end > 0:
            frontmatter = skill_content[3:frontmatter_end]
            for line in frontmatter.splitlines():
                if line.startswith("description:"):
                    description = line[len("description:"):].strip()

    return {
        "skill_lines": len(skill_content.splitlines()),
        "skill_chars": len(skill_content),
        "reference_file_count": len(reference_files),
        "reference_files": reference_files,
        "script_files": script_files,
        "asset_files": asset_files,
        "code_block_count_skill": code_block_count // 2,
        "code_block_count_refs": refs_code_block_count // 2,
        "has_yaml_frontmatter": has_yaml_frontmatter,
        "has_directory_tree_example": has_directory_tree,
        "has_step_numbering": has_step_numbering,
        "has_workflow_patterns_ref": has_workflow_patterns,
        "has_output_patterns_ref": has_output_patterns,
        "has_negative_triggers": "DO NOT USE" in skill_content.upper() or "NOT FOR" in skill_content.upper(),
        "has_progressive_disclosure_section": "Progressive Disclosure" in skill_content,
        "has_frontmatter_docs": "name:" in skill_content and "description:" in skill_content,
        "has_imperative_writing_guideline": "imperative" in skill_content.lower(),
        "has_pep723_mention": "PEP 723" in full_content or "uvx" in full_content,
        "has_token_budget_guidance": "500 lines" in full_content or "token" in full_content.lower(),
        "has_bad_good_examples": ("bad" in full_content.lower() and "good" in full_content.lower())
            or ("❌" in full_content and "✅" in full_content),
        "description_length": len(description),
        "mentions_github_copilot": "GitHub Copilot" in full_content,
        "mentions_claude": "Claude" in full_content,
        "has_iteration_step": "### Step 5" in skill_content or "Iterate" in skill_content,
        "has_what_not_to_include": "What to Not Include" in skill_content or "Do not include" in skill_content,
    }


def normalize_score(score: int) -> int:
    """Clamp model output to the supported rubric range."""
    return max(1, min(5, int(score)))


def format_observable_facts(heuristic_facts: dict, observable_facts: list[str]) -> str:
    """Combine deterministic and model-extracted facts into one prompt block."""
    payload = {
        "heuristic_facts": heuristic_facts,
        "observable_facts": observable_facts,
    }
    return json.dumps(payload, indent=2)


def render_report(results: list[dict], weighted_total: float, overall: float, report: dspy.Prediction) -> str:
    """Render the final evaluation report as markdown text."""
    lines = []
    lines.append("=" * 70)
    lines.append("  SKILL-CREATOR EVALUATION REPORT")
    lines.append("=" * 70)
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(report.executive_summary)
    lines.append("")
    lines.append("## Dimension Scores")
    lines.append("")
    lines.append(f"{'Dimension':<35} {'Score':>5}  {'Weighted':>8}  {'Scope':<16} {'Confidence'}")
    lines.append("-" * 90)
    for result in sorted(results, key=lambda item: item["score"]):
        bar = "█" * result["score"] + "░" * (5 - result["score"])
        lines.append(
            f"{result['dimension']:<35} {bar} {result['score']}/5  "
            f"({result['weighted_score']:.3f})  [{result['scope']:<13}]  {result['confidence']}"
        )
    lines.append("-" * 90)
    lines.append(f"{'OVERALL':<35}       {weighted_total:.2f}/5.00 = {overall:.1%}")
    lines.append("")
    lines.append("## Strengths")
    lines.append("")
    for strength in report.strengths:
        lines.append(f"  ✓ {strength}")
    lines.append("")
    lines.append("## Top Recommendations (Prioritized)")
    lines.append("")
    for index, recommendation in enumerate(report.top_recommendations, start=1):
        lines.append(f"  {index}. {recommendation}")
    lines.append("")
    lines.append("## Per-Dimension Details")
    lines.append("")
    for result in results:
        lines.append(f"### {result['dimension']} — {result['score']}/5 ({result['confidence']} confidence)")
        lines.append(f"  Evidence: {result['evidence']}")
        if result["suggestions"]:
            lines.append("  Suggestions:")
            for suggestion in result["suggestions"]:
                lines.append(f"    → {suggestion}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Evaluation pipeline
# ---------------------------------------------------------------------------


def run_evaluation(skill_path: str) -> str:
    """Run the skill-creator evaluation pipeline and return a markdown report."""
    skill_file = Path(skill_path)
    skill_dir = skill_file.parent

    skill_content = skill_file.read_text()
    refs_content = load_references(skill_dir)
    full_content = skill_content + refs_content

    heuristic_facts = build_heuristic_facts(skill_content, refs_content, skill_dir)

    print(f"Evaluating: {skill_path}")
    print(f"SKILL.md: {len(skill_content)} chars, ~{len(skill_content) // 4} tokens")
    if refs_content:
        print(f"References: {len(refs_content)} chars, ~{len(refs_content) // 4} tokens")
        print(f"Full package: {len(full_content)} chars, ~{len(full_content) // 4} tokens")
    print(f"Heuristic facts: {json.dumps(heuristic_facts, indent=2)}")
    print("=" * 70)

    extract_facts = dspy.ChainOfThought(ExtractObservableFacts)
    evaluate = dspy.ChainOfThought(EvaluateDimension)
    reconcile = dspy.ChainOfThought(ReconcileDimension)
    synthesize = dspy.ChainOfThought(SynthesizeReport)

    # Extract observable facts for both scopes
    print("\nExtracting observable facts (SKILL.md only)...")
    observable_skill_facts = extract_facts(
        skill_content=skill_content,
        heuristic_facts=json.dumps(heuristic_facts, indent=2),
    ).observable_facts

    print("Extracting observable facts (full package)...")
    observable_full_facts = extract_facts(
        skill_content=full_content,
        heuristic_facts=json.dumps(heuristic_facts, indent=2),
    ).observable_facts

    # Evaluate each dimension with dual reviewers + reconciliation
    results = []
    weighted_total = 0.0

    for dim_name, dim_cfg in RUBRIC.items():
        if dim_name in SKILL_ONLY_DIMS:
            content = skill_content
            scope = "SKILL.md only"
            facts = format_observable_facts(heuristic_facts, observable_skill_facts)
        else:
            content = full_content
            scope = "full package"
            facts = format_observable_facts(heuristic_facts, observable_full_facts)

        print(f"\n  Evaluating: {dim_name} (weight={dim_cfg['weight']}, {scope})...")

        reviewer_a = evaluate(
            skill_content=content,
            dimension=dim_name,
            criteria=dim_cfg["criteria"],
            reviewer_stance="strict rubric auditor: reward only explicit evidence and score conservatively",
            observable_facts=facts,
        )
        reviewer_b = evaluate(
            skill_content=content,
            dimension=dim_name,
            criteria=dim_cfg["criteria"],
            reviewer_stance=(
                "pragmatic operator: value usability and practical completeness but stay grounded in evidence"
            ),
            observable_facts=facts,
        )

        reconciliation = reconcile(
            dimension=dim_name,
            criteria=dim_cfg["criteria"],
            observable_facts=facts,
            reviewer_a=json.dumps(
                {
                    "score": normalize_score(reviewer_a.score),
                    "evidence": reviewer_a.evidence,
                    "suggestions": reviewer_a.suggestions,
                },
                indent=2,
            ),
            reviewer_b=json.dumps(
                {
                    "score": normalize_score(reviewer_b.score),
                    "evidence": reviewer_b.evidence,
                    "suggestions": reviewer_b.suggestions,
                },
                indent=2,
            ),
        )

        score = normalize_score(reconciliation.final_score)
        weighted_total += score * dim_cfg["weight"]

        result = {
            "dimension": dim_name,
            "score": score,
            "weight": dim_cfg["weight"],
            "weighted_score": round(score * dim_cfg["weight"], 3),
            "scope": scope,
            "confidence": reconciliation.confidence,
            "evidence": reconciliation.evidence,
            "suggestions": reconciliation.suggestions,
            "reviewers": {
                "strict": {
                    "score": normalize_score(reviewer_a.score),
                    "evidence": reviewer_a.evidence,
                },
                "pragmatic": {
                    "score": normalize_score(reviewer_b.score),
                    "evidence": reviewer_b.evidence,
                },
            },
        }
        results.append(result)

        bar = "█" * score + "░" * (5 - score)
        print(f"    Strict:  {normalize_score(reviewer_a.score)}/5")
        print(f"    Pragmatic: {normalize_score(reviewer_b.score)}/5")
        print(f"    Final:   {bar} {score}/5 ({reconciliation.confidence} confidence)")

    overall = round(weighted_total / 5, 3)
    print(f"\n{'=' * 70}")
    print(f"  OVERALL WEIGHTED SCORE: {overall:.1%} ({weighted_total:.2f}/5.00)")
    print(f"{'=' * 70}")

    # Synthesize final report
    print("\nSynthesizing improvement report...")
    report = synthesize(
        skill_content=full_content,
        dimension_results=json.dumps(results, indent=2),
        overall_score=overall,
    )

    return render_report(results, weighted_total, overall, report)


if __name__ == "__main__":
    lm = dspy.LM(
        model=f"azure/{os.environ['AZURE_OPENAI_DEPLOYMENT']}",
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_base=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version="2025-01-01-preview",
        temperature=1.0,
        max_tokens=16000,
    )
    dspy.configure(lm=lm)

    print(run_evaluation("SKILL.md"))
