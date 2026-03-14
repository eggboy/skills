# /// script
# requires-python = ">=3.12"
# dependencies = ["dspy"]
# ///
"""DSPy-based evaluation of the CLI Creator Agent Skill.

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

    You are preparing evidence for an evaluator of Agent Skills — modular
    instruction documents that extend AI coding assistants with domain-specific
    knowledge about building command-line interfaces.

    Extract only facts directly supported by the provided content. Do not score
    the skill. Focus on observable details such as:
      - files, references, and templates present,
      - whether negative triggers exist,
      - whether language-specific examples cover all major patterns,
      - whether clig.dev principles are explicitly referenced,
      - whether code examples are complete and runnable,
      - whether bad-vs-good comparisons exist,
      - whether shellcheck/lint validation is mentioned,
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

    Produce a prioritized, actionable improvement plan for the CLI Creator skill.
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
# Rubric — CLI Creator-specific dimensions
# ---------------------------------------------------------------------------

# Dimensions evaluated against SKILL.md only (what the agent sees first)
SKILL_ONLY_DIMS = {
    "description_trigger_quality",
    "context_efficiency",
    "structural_quality",
}

# Dimensions evaluated against SKILL.md + references/ (full skill package)
FULL_PACKAGE_DIMS = {
    "clig_principles_coverage",
    "language_breadth_and_depth",
    "example_quality",
    "error_prevention",
}

RUBRIC = {
    "description_trigger_quality": {
        "weight": 0.15,
        "criteria": textwrap.dedent("""\
            Evaluate the YAML frontmatter 'description' field as a triggering mechanism.
            The skill should trigger when users want to create, improve, or review
            command-line interface tools across multiple languages.
            1 = Missing or vague, would rarely trigger correctly
            2 = Partially describes what skill does but missing when-to-use triggers
            3 = Describes what AND when, but could be more comprehensive
            4 = Clear what + when, includes key trigger phrases (e.g., "CLI tool",
                "command-line", "argument parsing", "clig.dev"); covers multiple
                languages and frameworks
            5 = Excellent: comprehensive what + when, lists explicit trigger phrases
                for all supported languages/frameworks, includes negative triggers
                (when NOT to use — e.g., "not for GUI apps" or "not for TUI
                frameworks"); mentions the full scope of CLI concerns (help, errors,
                output, signals, config)"""),
    },
    "context_efficiency": {
        "weight": 0.15,
        "criteria": textwrap.dedent("""\
            Evaluate token efficiency and progressive disclosure of SKILL.md itself.
            A skill about creating CLIs should be lean and quickly scannable.
            1 = Bloated; includes information an LLM already knows; no references split
            2 = Some redundancy; large sections could move to references/
            3 = Reasonable length but some sections could be split out
            4 = Concise; only non-obvious rules inline; detailed patterns in references;
                good use of tables for language/framework selection
            5 = Excellent: every paragraph earns its tokens; progressive disclosure
                with clear references for deeper content; SKILL.md under 200 lines;
                workflow is immediately actionable; language selection via compact
                table; references are well-described so agent knows what to fetch"""),
    },
    "structural_quality": {
        "weight": 0.10,
        "criteria": textwrap.dedent("""\
            Evaluate the document's organization and navigability for an AI agent.
            1 = Poorly organized; hard to find specific guidance
            2 = Basic headings but inconsistent structure
            3 = Well-structured with clear sections
            4 = Logical flow; easy to locate rules for any topic; scannable tables
            5 = Excellent: consistent section pattern, clear hierarchy, agent can
                extract rules without ambiguity; two clear workflow paths (new vs
                improve); language selection table is easy to parse; reference
                descriptions are informative; checklist is comprehensive"""),
    },
    "clig_principles_coverage": {
        "weight": 0.20,
        "criteria": textwrap.dedent("""\
            Evaluate coverage of clig.dev best practices across the entire skill
            package (SKILL.md + all reference files).
            1 = Mentions clig.dev but covers only a few principles
            2 = Covers basics (help, errors) but misses many areas
            3 = Covers most standard areas but has notable gaps
            4 = Comprehensive coverage: philosophy, help text design, output
                formatting (human + machine), error handling (stderr, exit codes,
                actionable messages), arguments and flags, interactivity (TTY
                detection, prompts), configuration (files, env vars, precedence),
                signals (SIGINT, SIGTERM), naming conventions
            5 = Excellent: exhaustive coverage of all clig.dev sections including
                philosophy, help, output, errors, arguments/flags, interactivity,
                robustness, future-proofing, signals, configuration, environment
                variables, naming, distribution, and analytics; cross-language
                patterns for each; audit checklist for compliance"""),
    },
    "language_breadth_and_depth": {
        "weight": 0.20,
        "criteria": textwrap.dedent("""\
            Evaluate coverage of language-specific CLI patterns across the entire
            skill package (SKILL.md + all reference files + templates).
            1 = Covers only one language superficially
            2 = Covers 2-3 languages but missing key patterns (subcommands,
                testing, distribution)
            3 = Covers all claimed languages but some have shallow treatment
            4 = Good coverage across all languages (Python, Node.js, Go, Rust,
                Bash); each has: basic template, subcommand pattern, colors/
                progress, stdin/stdout handling, testing, distribution/packaging
            5 = Excellent: all languages covered deeply with: multiple framework
                options, starter templates, subcommand patterns, advanced patterns
                (progress bars, prompts, config files), testing approaches,
                packaging/distribution, and language-specific idioms; templates
                are complete and runnable; Bash includes shellcheck; style
                conventions are documented for each language"""),
    },
    "example_quality": {
        "weight": 0.10,
        "criteria": textwrap.dedent("""\
            Evaluate the quality and coverage of code examples across the entire
            skill package (SKILL.md + all reference files + templates).
            1 = No examples or trivial/broken ones
            2 = Few examples; missing diversity across languages
            3 = Adequate examples but gaps in coverage
            4 = Good coverage: each language has working examples for common
                patterns (arg parsing, subcommands, colors, stdin, JSON output);
                templates are runnable starter projects
            5 = Excellent: comprehensive examples across all languages with
                bad-vs-good comparisons for common mistakes, realistic complexity,
                complete runnable templates, testing examples; examples demonstrate
                clig.dev compliance; Bash examples pass shellcheck"""),
    },
    "error_prevention": {
        "weight": 0.10,
        "criteria": textwrap.dedent("""\
            Evaluate how well the skill package prevents common CLI-building
            mistakes across SKILL.md + all reference files.
            1 = No mention of pitfalls or common errors
            2 = Mentions a few warnings in passing
            3 = Addresses some common mistakes but could be more systematic
            4 = Covers key CLI pitfalls: printing errors to stdout instead of
                stderr, missing exit codes, swallowing Ctrl+C, hardcoded colors
                ignoring NO_COLOR, missing TTY detection, poor help text
            5 = Excellent: systematic anti-patterns coverage, common gotchas per
                language, explicit "do NOT" rules, recovery guidance; covers:
                stdout/stderr confusion, exit code misuse, signal handling errors,
                color in pipes, interactive prompts in scripts, platform-specific
                pitfalls, security issues (secrets in flags/env), and testing gaps"""),
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


def load_templates(skill_dir: Path) -> str:
    """Concatenate all assets/templates/* files into a single string."""
    templates_dir = skill_dir / "assets" / "templates"
    if not templates_dir.is_dir():
        return ""

    parts = []
    for template in sorted(templates_dir.iterdir()):
        if template.is_file():
            parts.append(f"\n\n--- {template.name} ---\n\n{template.read_text()}")
    return "".join(parts)


def build_heuristic_facts(skill_content: str, refs_content: str, templates_content: str, skill_dir: Path) -> dict:
    """Build deterministic observations to ground DSPy scoring."""
    references_dir = skill_dir / "references"
    reference_files = sorted(path.name for path in references_dir.glob("*.md")) if references_dir.is_dir() else []
    templates_dir = skill_dir / "assets" / "templates"
    template_files = sorted(path.name for path in templates_dir.iterdir()) if templates_dir.is_dir() else []

    full_content = skill_content + refs_content + templates_content

    # Count code blocks
    code_block_count_skill = skill_content.count("```") // 2
    code_block_count_refs = refs_content.count("```") // 2

    # Check for key structural elements
    has_yaml_frontmatter = skill_content.startswith("---")
    has_language_table = "| Language |" in skill_content
    has_two_workflows = "### New CLI" in skill_content and "### Improve Existing CLI" in skill_content
    has_audit_checklist = "- Provides `-h`/`--help`" in skill_content or "checklist" in skill_content.lower()

    # clig.dev principle coverage
    clig_principles = [
        "help",
        "output",
        "error",
        "arguments",
        "flags",
        "interactivity",
        "robustness",
        "future-proofing",
        "signals",
        "configuration",
        "environment variables",
        "naming",
        "distribution",
        "analytics",
    ]
    principles_covered = sum(1 for p in clig_principles if p.lower() in full_content.lower())

    # Language coverage
    languages = {
        "python": "Click" in full_content or "Typer" in full_content,
        "nodejs": "Commander" in full_content or "yargs" in full_content,
        "go": "Cobra" in full_content,
        "rust": "Clap" in full_content,
        "bash": "getopts" in full_content or "bash" in full_content.lower(),
    }

    # Pattern coverage per language reference
    patterns_checked = [
        "subcommand",
        "progress",
        "color",
        "stdin",
        "json",
        "testing",
        "NO_COLOR",
        "exit code",
        "signal",
        "TTY",
    ]
    patterns_in_refs = sum(1 for p in patterns_checked if p.lower() in refs_content.lower())

    # Description analysis
    description = ""
    if has_yaml_frontmatter:
        frontmatter_end = skill_content.find("---", 3)
        if frontmatter_end > 0:
            frontmatter = skill_content[3:frontmatter_end]
            for line in frontmatter.splitlines():
                if line.startswith("description:"):
                    description = line[len("description:") :].strip()

    # Bash-specific checks
    has_shellcheck_mention = "shellcheck" in full_content.lower()
    has_style_conventions = "Style Conventions" in refs_content
    has_bats_mention = "bats" in refs_content.lower()

    # Long reference TOCs
    long_reference_tocs = {}
    if references_dir.is_dir():
        for path in sorted(references_dir.glob("*.md")):
            lines = path.read_text().splitlines()
            if len(lines) > 100:
                long_reference_tocs[path.name] = any(
                    "## Table of Contents" in line or "## TOC" in line for line in lines[:20]
                )

    return {
        "skill_lines": len(skill_content.splitlines()),
        "skill_chars": len(skill_content),
        "reference_file_count": len(reference_files),
        "reference_files": reference_files,
        "template_files": template_files,
        "long_reference_tocs": long_reference_tocs,
        "code_block_count_skill": code_block_count_skill,
        "code_block_count_refs": code_block_count_refs,
        "has_yaml_frontmatter": has_yaml_frontmatter,
        "has_language_table": has_language_table,
        "has_two_workflows": has_two_workflows,
        "has_audit_checklist": has_audit_checklist,
        "has_negative_triggers": "DO NOT USE" in skill_content.upper() or "NOT FOR" in skill_content.upper(),
        "clig_principles_covered": f"{principles_covered}/{len(clig_principles)}",
        "languages_covered": {k: v for k, v in languages.items()},
        "languages_with_templates": len(template_files),
        "patterns_in_refs": f"{patterns_in_refs}/{len(patterns_checked)}",
        "has_shellcheck_mention": has_shellcheck_mention,
        "has_style_conventions": has_style_conventions,
        "has_bats_mention": has_bats_mention,
        "description_length": len(description),
        "has_bad_good_examples": ("❌" in full_content and "✅" in full_content)
        or ("bad" in full_content.lower() and "good" in full_content.lower()),
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
    lines.append("  CLI CREATOR SKILL EVALUATION REPORT")
    lines.append("=" * 70)
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(report.executive_summary)
    lines.append("")
    lines.append("## Dimension Scores")
    lines.append("")
    lines.append(f"{'Dimension':<30} {'Score':>5}  {'Weighted':>8}  {'Scope':<16} {'Confidence'}")
    lines.append("-" * 90)
    for result in sorted(results, key=lambda item: item["score"]):
        bar = "█" * result["score"] + "░" * (5 - result["score"])
        lines.append(
            f"{result['dimension']:<30} {bar} {result['score']}/5  "
            f"({result['weighted_score']:.3f})  [{result['scope']:<13}]  {result['confidence']}"
        )
    lines.append("-" * 90)
    lines.append(f"{'OVERALL':<30}       {weighted_total:.2f}/5.00 = {overall:.1%}")
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
    """Run the CLI Creator evaluation pipeline and return a markdown report."""
    skill_file = Path(skill_path)
    skill_dir = skill_file.parent

    skill_content = skill_file.read_text()
    refs_content = load_references(skill_dir)
    templates_content = load_templates(skill_dir)
    full_content = skill_content + refs_content + templates_content

    heuristic_facts = build_heuristic_facts(skill_content, refs_content, templates_content, skill_dir)

    print(f"Evaluating: {skill_path}")
    print(f"SKILL.md: {len(skill_content)} chars, ~{len(skill_content) // 4} tokens")
    if refs_content:
        print(f"References: {len(refs_content)} chars, ~{len(refs_content) // 4} tokens")
    if templates_content:
        print(f"Templates: {len(templates_content)} chars, ~{len(templates_content) // 4} tokens")
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
        print(f"    Strict:    {normalize_score(reviewer_a.score)}/5")
        print(f"    Pragmatic: {normalize_score(reviewer_b.score)}/5")
        print(f"    Final:     {bar} {score}/5 ({reconciliation.confidence} confidence)")

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

    print(run_evaluation("../cli-creator/SKILL.md"))
