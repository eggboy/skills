# /// script
# requires-python = ">=3.12"
# dependencies = ["dspy"]
# ///
"""DSPy-based evaluation of the Azure Verified Modules (AVM) Agent Skill.

Two-pass evaluation:
  Pass 1 (SKILL.md only): dimensions the agent sees on first load
  Pass 2 (SKILL.md + references/): dimensions measuring full skill coverage

This version improves stability by combining:
  - heuristic observations extracted directly from files,
  - a DSPy fact-extraction pass,
  - two independent rubric judges, and
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
      - whether examples are bad-vs-good,
      - whether VNet workflow names tools explicitly,
      - whether requirement IDs like TFNFR/TFFR appear,
      - whether checklists or TOCs exist.
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

    Produce a prioritized, actionable improvement plan for the AVM skill.
    Focus on the dimensions with the lowest scores first.
    """

    skill_content: str = dspy.InputField(desc="Full text of the SKILL.md + references")
    dimension_results: str = dspy.InputField(desc="JSON array of reconciled per-dimension evaluation results")
    overall_score: float = dspy.InputField(desc="Weighted overall score (0-1)")
    executive_summary: str = dspy.OutputField(desc="2-3 sentence overall assessment")
    top_recommendations: list[str] = dspy.OutputField(desc="Top 5-7 prioritized recommendations")
    strengths: list[str] = dspy.OutputField(desc="Top 3-4 strengths to preserve")


# ---------------------------------------------------------------------------
# Rubric — AVM-specific dimensions
# ---------------------------------------------------------------------------

SKILL_ONLY_DIMS = {
    "description_trigger_quality",
    "context_efficiency",
    "structural_quality",
}

FULL_PACKAGE_DIMS = {
    "avm_compliance_coverage",
    "vnet_injection_guidance",
    "example_quality",
    "error_prevention",
}

RUBRIC = {
    "description_trigger_quality": {
        "weight": 0.15,
        "criteria": textwrap.dedent("""\
            Evaluate the YAML frontmatter 'description' field as a triggering mechanism.
            The skill should trigger for AVM module development, consumption, review,
            and VNet injection / subnet delegation / NSG configuration.
            1 = Missing or vague, would rarely trigger correctly
            2 = Partially describes what skill does but missing when-to-use triggers
            3 = Describes what AND when, but could be more comprehensive
            4 = Clear what + when, includes key trigger phrases (e.g., "AVM module",
                "subnet delegation", "VNet injection")
            5 = Excellent: comprehensive what + when, lists explicit positive triggers
                AND negative triggers (when NOT to use — e.g., "not for generic
                Terraform style" or "not for non-AVM modules")"""),
    },
    "context_efficiency": {
        "weight": 0.15,
        "criteria": textwrap.dedent("""\
            Evaluate token efficiency and progressive disclosure.
            The SKILL.md should contain only what the agent needs on first load;
            full AVM requirement specs (TFFR/TFNFR details) belong in references/.
            1 = Bloated; duplicates the full AVM spec inline; no references split
            2 = Some redundancy; large sections could move to references/
            3 = Reasonable length but some sections could be split out
            4 = Concise; only non-obvious rules inline; detailed specs in references
            5 = Excellent: every paragraph earns its tokens; progressive disclosure
                with clear references for deeper content; SKILL.md under 500 lines;
                Quick Reference is scannable"""),
    },
    "structural_quality": {
        "weight": 0.10,
        "criteria": textwrap.dedent("""\
            Evaluate the document's organization and navigability for an AI agent.
            1 = Poorly organized; hard to find specific AVM guidance
            2 = Basic headings but inconsistent structure
            3 = Well-structured with clear sections (Quick Reference, Checklist, etc.)
            4 = Logical flow; easy to locate rules for any AVM topic; scannable
            5 = Excellent: consistent section pattern, clear hierarchy, agent can
                extract rules without ambiguity; Quick Reference → Detail → Checklist
                flow works well; markdown formatting aids machine parsing"""),
    },
    "avm_compliance_coverage": {
        "weight": 0.20,
        "criteria": textwrap.dedent("""\
            Evaluate coverage of AVM specification requirements (TFFR/TFNFR codes)
            across the entire skill package (SKILL.md + all reference files).
            1 = Covers only a few requirements superficially
            2 = Covers basic requirements (providers, naming) but misses many areas
            3 = Covers most MUST requirements but has notable gaps in SHOULD rules
            4 = Comprehensive coverage of MUST and SHOULD requirements including:
                module cross-referencing (TFFR1), providers (TFFR3), code style
                (TFNFR4-13), variables (TFNFR14-24), outputs (TFFR2, TFNFR29-30),
                locals, testing (TFNFR5), docs, breaking changes (TFNFR34-35)
            5 = Excellent: exhaustive coverage of all TFFR/TFNFR requirements,
                clearly distinguishes MUST vs SHOULD severity, includes contribution
                standards, branch protection rules, and version constraints"""),
    },
    "vnet_injection_guidance": {
        "weight": 0.15,
        "criteria": textwrap.dedent("""\
            Evaluate the quality and completeness of VNet injection, subnet
            delegation, and NSG configuration guidance across the skill package.
            This is a critical differentiator — incorrect networking config causes
            cryptic deployment failures.
            1 = No VNet/subnet guidance at all
            2 = Mentions VNet injection exists but lacks actionable workflow
            3 = Has a workflow but missing key details (tier-specific differences,
                DNS, subnet sizing specifics)
            4 = Good workflow with doc-search steps, covers tier-specific pitfalls,
                includes example of what can go wrong
            5 = Excellent: mandatory verification workflow with specific tool usage
                (microsoft_docs_search, microsoft_docs_fetch), tier/SKU-aware
                checklist, concrete pitfall examples, DNS and subnet sizing,
                cross-check step; actionable enough to prevent real failures"""),
    },
    "example_quality": {
        "weight": 0.15,
        "criteria": textwrap.dedent("""\
            Evaluate the quality and coverage of HCL code examples across the
            entire skill package (SKILL.md + all reference files).
            Examples should demonstrate AVM-compliant patterns.
            1 = No examples or trivial/broken ones
            2 = Few examples; missing bad-vs-good comparisons
            3 = Adequate examples but gaps in coverage of key AVM patterns
            4 = Good coverage with examples for: provider blocks, variable
                definitions, for_each with static keys, dynamic blocks, feature
                toggles, output patterns, block ordering
            5 = Excellent: comprehensive examples with bad/good pairs for key
                conventions; realistic complexity; covers module structure,
                variables, outputs, feature toggles, moved blocks, deprecated
                patterns, and VNet-related config"""),
    },
    "error_prevention": {
        "weight": 0.10,
        "criteria": textwrap.dedent("""\
            Evaluate how well the skill package prevents common AVM mistakes.
            1 = No mention of pitfalls or common errors
            2 = Mentions a few warnings in passing
            3 = Addresses some common mistakes but could be more systematic
            4 = Covers key AVM pitfalls: wrong provider versions, git refs instead
                of registry, sensitive defaults, missing feature toggles, breaking
                changes from renamed resources without moved blocks
            5 = Excellent: systematic coverage of AVM-specific anti-patterns,
                VNet/subnet misconfigurations, TFNFR35 breaking change scenarios,
                "do NOT" rules, tier-specific gotchas, and recovery guidance"""),
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


def count_occurrences(content: str, needles: list[str]) -> int:
    """Count how many candidate markers appear in the provided content."""
    lowered = content.lower()
    return sum(1 for needle in needles if needle.lower() in lowered)


def build_heuristic_facts(skill_content: str, refs_content: str, skill_dir: Path) -> dict:
    """Build deterministic observations to ground DSPy scoring."""
    references_dir = skill_dir / "references"
    reference_files = sorted(path.name for path in references_dir.glob("*.md")) if references_dir.is_dir() else []

    long_reference_tocs = {}
    if references_dir.is_dir():
        for path in sorted(references_dir.glob("*.md")):
            lines = path.read_text().splitlines()
            if len(lines) > 100:
                long_reference_tocs[path.name] = any("## Table of Contents" in line for line in lines[:20])

    full_content = skill_content + refs_content

    return {
        "skill_lines": len(skill_content.splitlines()),
        "skill_chars": len(skill_content),
        "reference_file_count": len(reference_files),
        "reference_files": reference_files,
        "long_reference_tocs": long_reference_tocs,
        "has_negative_triggers": "DO NOT use for" in skill_content,
        "has_reference_table": "| Reference | Content |" in skill_content,
        "has_quick_compliance_check": "## Quick Compliance Check" in skill_content,
        "has_vnet_workflow": "microsoft_docs_search" in full_content and "microsoft_docs_fetch" in full_content,
        "has_vnet_checklist": "## Checklist" in refs_content,
        "has_bad_good_examples": "# ❌ BAD" in refs_content and "# ✅ GOOD" in refs_content,
        "has_moved_block_example": "moved {" in refs_content,
        "has_deprecated_examples": (
            "deprecated_variables.tf" in refs_content and "deprecated_outputs.tf" in refs_content
        ),
        "has_tffr_codes": count_occurrences(full_content, ["TFFR1", "TFFR2", "TFFR3"]),
        "has_tfnfr_codes": count_occurrences(
            full_content,
            [
                "TFNFR4",
                "TFNFR5",
                "TFNFR10",
                "TFNFR14",
                "TFNFR24",
                "TFNFR25",
                "TFNFR29",
                "TFNFR34",
                "TFNFR35",
                "TFNFR36",
            ],
        ),
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
    lines.append("Evaluating complete")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(report.executive_summary)
    lines.append("")
    lines.append("## Dimension Scores")
    lines.append("")
    lines.append(f"{'Dimension':<30} {'Score':>5}  {'Weighted':>8}  {'Scope'}  {'Confidence'}")
    lines.append("-" * 90)
    for result in sorted(results, key=lambda item: item["score"]):
        bar = "█" * result["score"] + "░" * (5 - result["score"])
        lines.append(
            f"{result['dimension']:<30} {bar} {result['score']}/5  "
            f"({result['weighted_score']:.3f})  [{result['scope']}]  {result['confidence']}"
        )
    lines.append("-" * 90)
    lines.append(f"{'OVERALL':<30}       {weighted_total:.2f}/5.00 = {overall:.1%}")
    lines.append("")
    lines.append("## Strengths")
    lines.append("")
    for strength in report.strengths:
        lines.append(f"- {strength}")
    lines.append("")
    lines.append("## Top Recommendations")
    lines.append("")
    for index, recommendation in enumerate(report.top_recommendations, start=1):
        lines.append(f"{index}. {recommendation}")
    lines.append("")
    lines.append("## Per-Dimension Details")
    lines.append("")
    for result in results:
        lines.append(f"### {result['dimension']} — {result['score']}/5 ({result['confidence']} confidence)")
        lines.append(result["evidence"])
        if result["suggestions"]:
            lines.append("")
            lines.append("Suggestions:")
            for suggestion in result["suggestions"]:
                lines.append(f"- {suggestion}")
        lines.append("")
    return "\n".join(lines)


def run_evaluation(skill_path: str) -> str:
    """Run the AVM evaluation pipeline and return a markdown report."""
    skill_file = Path(skill_path)
    skill_dir = skill_file.parent

    skill_content = skill_file.read_text()
    refs_content = load_references(skill_dir)
    full_content = skill_content + refs_content

    heuristic_facts = build_heuristic_facts(skill_content, refs_content, skill_dir)

    extract_facts = dspy.ChainOfThought(ExtractObservableFacts)
    evaluate = dspy.ChainOfThought(EvaluateDimension)
    reconcile = dspy.ChainOfThought(ReconcileDimension)
    synthesize = dspy.ChainOfThought(SynthesizeReport)

    observable_skill_facts = extract_facts(
        skill_content=skill_content,
        heuristic_facts=json.dumps(heuristic_facts, indent=2),
    ).observable_facts

    observable_full_facts = extract_facts(
        skill_content=full_content,
        heuristic_facts=json.dumps(heuristic_facts, indent=2),
    ).observable_facts

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

        results.append(
            {
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
        )

    overall = round(weighted_total / 5, 3)
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

    print(run_evaluation("azure-verified-modules/SKILL.md"))
