# /// script
# requires-python = ">=3.12"
# dependencies = ["dspy"]
# ///
"""DSPy-based evaluation of the Java Best Practices Agent Skill.

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
import re
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
    knowledge about modern Java development best practices.

    Extract only facts directly supported by the provided content. Do not score
    the skill. Focus on observable details such as:
      - files and references present,
      - whether negative triggers exist,
      - whether JDK version annotations are consistently applied,
      - whether old-vs-modern comparisons exist,
      - whether testing/TDD patterns are present and comprehensive,
      - whether Spring Boot integration patterns are covered,
      - whether migration paths between JDK versions are documented,
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
    evidence: str = dspy.OutputField(desc="Detailed critique grounded in the provided content before scoring")
    score: int = dspy.OutputField(desc="Integer score from 1 to 5")
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
    evidence: str = dspy.OutputField(desc="Best supported evidence for the final score")
    final_score: int = dspy.OutputField(desc="Final integer score from 1 to 5")
    suggestions: list[str] = dspy.OutputField(desc="Merged, deduplicated suggestions")
    confidence: str = dspy.OutputField(desc="high, medium, or low")


class OpenCritique(dspy.Signature):
    """Perform an open-ended critique of the skill package to discover quality
    gaps that a fixed rubric might miss.

    You are a senior Java architect reviewing an Agent Skill that teaches modern
    Java best practices. Ignore the rubric dimensions entirely. Instead, read
    the full skill content and identify:
      - Important Java topics or patterns that are completely absent,
      - Advice that is outdated, misleading, or wrong,
      - Structural problems (e.g., orphaned references, circular guidance),
      - Anything that would confuse an AI agent consuming this skill.

    Be specific: name the missing topic, the incorrect advice, or the structural
    issue. Do not repeat observations that a rubric would naturally cover (e.g.,
    "needs more examples" is rubric territory; "missing JDBC connection pooling
    guidance" is a genuine gap).
    """

    skill_content: str = dspy.InputField(desc="Full text of the SKILL.md + all references")
    rubric_dimensions: str = dspy.InputField(desc="List of rubric dimension names already scored")
    blind_spots: list[str] = dspy.OutputField(
        desc="Quality gaps NOT covered by the rubric dimensions; each item is a concrete, specific observation"
    )
    outdated_or_wrong: list[str] = dspy.OutputField(
        desc="Advice in the skill that is outdated, misleading, or incorrect; empty if none found"
    )
    structural_issues: list[str] = dspy.OutputField(
        desc="Structural problems like orphaned refs, missing cross-links, or confusing organization; empty if none"
    )


class SynthesizeReport(dspy.Signature):
    """Synthesize per-dimension evaluations and open critique into a final
    improvement report.

    Produce a prioritized, actionable improvement plan for the Java Best Practices
    skill. Integrate both rubric scores AND open critique findings. Focus on the
    dimensions with the lowest scores first, then incorporate blind spots from the
    open critique. Each recommendation must be concrete (say exactly what to
    add/change/remove and where).
    """

    skill_content: str = dspy.InputField(desc="Full text of the SKILL.md + references")
    dimension_results: str = dspy.InputField(desc="JSON array of reconciled per-dimension evaluation results")
    open_critique: str = dspy.InputField(desc="JSON object with blind_spots, outdated_or_wrong, and structural_issues")
    overall_score: float = dspy.InputField(desc="Weighted overall score (0-1)")
    executive_summary: str = dspy.OutputField(desc="2-3 sentence overall assessment")
    top_recommendations: list[str] = dspy.OutputField(desc="Top 5-7 prioritized recommendations")
    strengths: list[str] = dspy.OutputField(desc="Top 3-4 strengths to preserve")


# ---------------------------------------------------------------------------
# Rubric — Java Best Practices-specific dimensions
# ---------------------------------------------------------------------------

# Dimensions evaluated against SKILL.md only (what the agent sees first)
SKILL_ONLY_DIMS = {
    "description_trigger_quality",
    "context_efficiency",
    "structural_quality",
}

# Dimensions evaluated against SKILL.md + references/ (full skill package)
FULL_PACKAGE_DIMS = {
    "jdk_version_coverage",
    "pattern_breadth_and_depth",
    "testing_and_tdd_coverage",
    "example_quality",
    "migration_and_modernization",
    "error_prevention",
    "spring_boot_integration",
}

RUBRIC = {
    "description_trigger_quality": {
        "weight": 0.10,
        "criteria": textwrap.dedent("""\
            Evaluate the YAML frontmatter 'description' field as a triggering mechanism.
            The skill should trigger when users want to write, review, refactor, or
            modernize Java code using best practices.
            1 = Missing or vague, would rarely trigger correctly
            2 = Partially describes what skill does but missing when-to-use triggers
            3 = Describes what AND when, but could be more comprehensive
            4 = Clear what + when, includes key trigger phrases (e.g., "Java best
                practices", "modern Java", "Records", "virtual threads", "pattern
                matching", "Spring Boot"); covers major JDK versions
            5 = Excellent: comprehensive what + when, lists explicit trigger phrases
                across all major domains (language features, concurrency, testing,
                Spring Boot, exception handling); includes negative triggers (when NOT
                to use); mentions the full scope of Java development concerns"""),
    },
    "context_efficiency": {
        "weight": 0.10,
        "criteria": textwrap.dedent("""\
            Evaluate token efficiency and progressive disclosure of SKILL.md itself.
            A skill about Java best practices should be lean and quickly actionable.
            1 = Bloated; includes information an LLM already knows; no references split
            2 = Some redundancy; large sections could move to references/
            3 = Reasonable length but some sections could be split out
            4 = Concise; only non-obvious rules inline; detailed patterns in references;
                good use of tables for reference routing; quick start is focused
            5 = Excellent: every paragraph earns its tokens; progressive disclosure
                with clear references for deeper content; SKILL.md under 250 lines;
                workflow is immediately actionable; reference routing via compact
                table; references are well-described so agent knows what to fetch"""),
    },
    "structural_quality": {
        "weight": 0.10,
        "criteria": textwrap.dedent("""\
            Evaluate the document's organization and navigability for an AI agent.
            1 = Poorly organized; hard to find specific guidance
            2 = Basic headings but inconsistent structure
            3 = Well-structured with clear sections
            4 = Logical flow; easy to locate rules for any topic; scannable tables;
                clear core principles; reference routing is intuitive
            5 = Excellent: consistent section pattern, clear hierarchy, agent can
                extract rules without ambiguity; quick start immediately useful;
                core principles enumerate actionable rules; reference routing table
                maps every domain; JDK version table is comprehensive; build
                verification is present"""),
    },
    "jdk_version_coverage": {
        "weight": 0.15,
        "criteria": textwrap.dedent("""\
            Evaluate coverage of JDK features from JDK 8 through JDK 25 across the
            entire skill package (SKILL.md + all reference files).
            1 = Covers only a few JDK versions superficially
            2 = Covers LTS versions (8, 11, 17) but misses recent features
            3 = Covers through JDK 21 well but JDK 22-25 is thin
            4 = Good coverage across all LTS versions (8, 11, 17, 21, 25) plus
                key interim releases; each pattern annotated with minimum JDK;
                migration paths mentioned
            5 = Excellent: exhaustive coverage from JDK 8 through 25 with every
                major feature annotated; old-vs-modern comparisons for each;
                migration checklists for major upgrade paths (8→17, 11→21, 17→25);
                preview features clearly marked; JDK 25 LTS features (primitive
                patterns, flexible constructor bodies) thoroughly covered"""),
    },
    "pattern_breadth_and_depth": {
        "weight": 0.15,
        "criteria": textwrap.dedent("""\
            Evaluate the breadth (how many domains) and depth (detail per domain)
            of Java patterns across the skill package (SKILL.md + all references).
            1 = Covers only 2-3 domains with shallow treatment
            2 = Covers most domains but several are too shallow to be useful
            3 = Reasonable coverage across all claimed domains
            4 = Good coverage across all 14 reference files: language, collections,
                streams, concurrency, I/O, strings, errors, datetime, security,
                tooling, testing, DTOs, exception handling, code quality; each
                domain has multiple patterns with code examples
            5 = Excellent: 90+ patterns across all domains; every pattern has
                old-vs-modern comparison; minimum JDK version noted; complete
                code examples; realistic complexity; enterprise patterns included
                (Spring Boot, JPA, REST APIs); interconnections between domains
                are documented (e.g., Records + sealed types + pattern matching)"""),
    },
    "testing_and_tdd_coverage": {
        "weight": 0.15,
        "criteria": textwrap.dedent("""\
            Evaluate the comprehensiveness of testing and TDD guidance across the
            skill package (SKILL.md + testing.md reference + any testing patterns
            in other references).
            1 = No testing guidance or only trivial mention
            2 = Basic JUnit examples but missing TDD workflow, mocking, or assertions
            3 = Covers JUnit 5 basics and some Mockito but incomplete patterns
            4 = Good coverage: JUnit 5 patterns (parameterized, nested, lifecycle),
                AssertJ fluent assertions, Mockito (stubbing, verification, argument
                capture), TDD Red-Green-Refactor workflow, test builders, AAA
                pattern, integration testing with Spring Boot and TestContainers
            5 = Excellent: all of level 4 plus: BDD-style testing, test naming
                conventions and anti-patterns, async testing, time-dependent testing
                with Clock, mutation testing, test coverage guidelines, contract
                testing, architecture testing (ArchUnit), performance testing
                patterns, test organization guidelines, what NOT to test"""),
    },
    "example_quality": {
        "weight": 0.10,
        "criteria": textwrap.dedent("""\
            Evaluate the quality and coverage of code examples across the entire
            skill package (SKILL.md + all reference files).
            1 = No examples or trivially broken ones
            2 = Few examples; lack realistic complexity
            3 = Adequate examples but inconsistent presence of old-vs-modern comparison
            4 = Good examples: each domain has working code; old-vs-modern comparisons
                present; JDK version annotations; ✅/❌ markers for good/bad patterns
            5 = Excellent: every pattern has complete, realistic code examples with
                old-vs-modern comparison; idiomatic Java style; enterprise-grade
                complexity; bad-vs-good anti-pattern examples; dependency import
                statements shown where needed; consistent formatting"""),
    },
    "migration_and_modernization": {
        "weight": 0.05,
        "criteria": textwrap.dedent("""\
            Evaluate guidance for migrating and modernizing Java codebases across the
            skill package (SKILL.md + all references).
            1 = No migration guidance
            2 = Mentions JDK versions but no migration paths
            3 = Some migration advice but not systematic
            4 = Clear migration paths for major upgrades (8→17, 11→21); common
                modernization patterns (anonymous class → lambda, Date → java.time);
                deprecation warnings; module system transition guidance
            5 = Excellent: systematic migration checklists for every major upgrade
                path including 17→25; API replacements documented; build tool
                updates (Maven/Gradle); module system migration; removal of
                deprecated APIs; performance improvements per version"""),
    },
    "error_prevention": {
        "weight": 0.05,
        "criteria": textwrap.dedent("""\
            Evaluate how well the skill package prevents common Java development
            mistakes across SKILL.md + all reference files.
            1 = No mention of pitfalls or common errors
            2 = Mentions a few warnings in passing
            3 = Addresses some common mistakes but could be more systematic
            4 = Covers key Java pitfalls: mutable collection returns, Optional.get()
                without check, raw types, checked exception overuse, Thread.sleep
                vs Duration, String concatenation in loops, == for object comparison,
                synchronized on wrong monitor
            5 = Excellent: systematic anti-patterns coverage with ❌/✅ markers for
                each; common gotchas per domain (e.g., Stream reuse, HashMap with
                mutable keys, LocalDateTime vs ZonedDateTime confusion, virtual
                thread pinning); explicit "do NOT" rules; code review checklist"""),
    },
    "spring_boot_integration": {
        "weight": 0.05,
        "criteria": textwrap.dedent("""\
            Evaluate how well the skill package integrates with Spring Boot patterns,
            which is the most common Java enterprise framework.
            1 = No Spring Boot mention
            2 = Mentions Spring Boot in passing but no integration patterns
            3 = Some Spring Boot examples (e.g., @RestController, @Valid) scattered
            4 = Good integration: validation with @Valid, @ControllerAdvice for
                exceptions, MockMvc testing, @WebMvcTest slicing, Spring Data
                repository testing, Spring property configuration
            5 = Excellent: comprehensive Spring Boot integration across all relevant
                domains; constructor injection patterns, Spring profiles, Spring
                Security basics, Spring Data query methods, @Transactional guidance,
                Spring Boot testing hierarchy (unit→slice→integration), actuator
                health patterns, virtual threads with Spring Boot 3.2+"""),
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


def build_heuristic_facts(skill_content: str, refs_content: str, skill_dir: Path, *, scope: str = "full") -> dict:
    """Build deterministic observations to ground DSPy scoring.

    scope: "skill_only" restricts checks to skill_content; "full" includes refs_content.
    """
    references_dir = skill_dir / "references"
    reference_files = sorted(path.name for path in references_dir.glob("*.md")) if references_dir.is_dir() else []

    target_content = skill_content if scope == "skill_only" else skill_content + refs_content

    # Count code blocks
    code_block_count_skill = skill_content.count("```") // 2
    code_block_count_refs = refs_content.count("```") // 2 if scope == "full" else 0

    # Check for key structural elements
    has_yaml_frontmatter = skill_content.startswith("---")
    has_reference_table = "| Domain |" in skill_content or "| domain" in skill_content.lower()
    has_quick_start = "## Quick Start" in skill_content
    has_core_principles = "## Core Principles" in skill_content
    has_build_verification = "## Build Verification" in skill_content

    # JDK version coverage
    jdk_versions = [
        "JDK 8",
        "JDK 9",
        "JDK 10",
        "JDK 11",
        "JDK 14",
        "JDK 15",
        "JDK 16",
        "JDK 17",
        "JDK 21",
        "JDK 22",
        "JDK 23",
        "JDK 24",
        "JDK 25",
    ]
    jdk_versions_in_skill = [v for v in jdk_versions if v in skill_content]
    jdk_versions_in_scope = [v for v in jdk_versions if v in target_content]

    # JDK 25 specific features
    jdk25_features = [
        "primitive type pattern",
        "flexible constructor",
        "primitive pattern",
        "constructor bodies",
        "stream gatherers",
    ]
    jdk25_coverage = sum(1 for f in jdk25_features if f.lower() in target_content.lower())

    # Pattern domain coverage
    pattern_domains = {
        "language": any(w in target_content for w in ["Records", "sealed class", "pattern matching", "var"]),
        "collections": any(w in target_content for w in ["List.of", "Map.of", "sequenced"]),
        "streams": any(w in target_content for w in ["Stream", ".stream()", "Collectors", "gatherer"]),
        "concurrency": any(
            w in target_content for w in ["virtual thread", "structured concurrency", "CompletableFuture"]
        ),
        "io": any(w in target_content for w in ["HTTP Client", "Files.readString", "Path.of"]),
        "strings": any(w in target_content for w in ["text block", "isBlank", "strip()"]),
        "errors": any(w in target_content for w in ["NullPointerException", "Optional", "multi-catch"]),
        "datetime": any(w in target_content for w in ["java.time", "Duration", "Instant"]),
        "security": any(w in target_content for w in ["TLS", "SecureRandom", "PEM"]),
        "tooling": any(w in target_content for w in ["jshell", "JFR", "jwebserver"]),
        "testing": any(w in target_content for w in ["JUnit", "@Test", "Mockito", "AssertJ"]),
        "dto_patterns": any(w in target_content for w in ["DTO", "Request", "Response"]),
        "exception_handling": any(
            w in target_content for w in ["@ControllerAdvice", "RuntimeException", "exception hierarchy"]
        ),
        "code_quality": any(w in target_content for w in ["naming", "code smell", "review checklist"]),
    }
    domains_covered = sum(1 for v in pattern_domains.values() if v)

    # Testing coverage details
    testing_elements = {
        "junit5_basics": any(w in target_content for w in ["@Test", "JUnit 5", "JUnit5"]),
        "parameterized_tests": "@ParameterizedTest" in target_content,
        "nested_tests": "@Nested" in target_content,
        "assertj": "assertThat" in target_content or "AssertJ" in target_content,
        "mockito": "Mockito" in target_content or "@Mock" in target_content,
        "tdd_workflow": "Red-Green-Refactor" in target_content or "TDD" in target_content,
        "aaa_pattern": "Arrange" in target_content and "Act" in target_content and "Assert" in target_content,
        "test_containers": "Testcontainers" in target_content or "TestContainers" in target_content,
        "spring_boot_test": "@SpringBootTest" in target_content or "MockMvc" in target_content,
        "web_mvc_test": "@WebMvcTest" in target_content,
        "test_builders": "TestBuilder" in target_content or "test builder" in target_content.lower(),
        "bdd_mockito": "BDDMockito" in target_content or "given(" in target_content,
        "argument_captor": "ArgumentCaptor" in target_content or "@Captor" in target_content,
        "soft_assertions": "assertSoftly" in target_content or "SoftAssertions" in target_content,
        "async_testing": "succeedsWithin" in target_content or "CompletableFuture" in target_content,
        "clock_testing": "Clock.fixed" in target_content,
        "coverage_guidelines": "coverage" in target_content.lower(),
        "what_not_to_test": "NOT to test" in target_content or "DON'T TEST" in target_content,
    }
    testing_elements_covered = sum(1 for v in testing_elements.values() if v)

    # Spring Boot integration
    spring_elements = {
        "controller_advice": "@ControllerAdvice" in target_content,
        "valid_annotation": "@Valid" in target_content,
        "rest_controller": "@RestController" in target_content or "@PostMapping" in target_content,
        "spring_boot_test": "@SpringBootTest" in target_content,
        "mock_mvc": "MockMvc" in target_content,
        "web_mvc_test": "@WebMvcTest" in target_content,
        "mock_bean": "@MockBean" in target_content,
        "dynamic_property": "@DynamicPropertySource" in target_content,
        "spring_data": "Repository" in target_content,
    }
    spring_elements_covered = sum(1 for v in spring_elements.values() if v)

    # Old-vs-modern comparison patterns
    has_old_vs_modern = (
        ("Old" in target_content and "Modern" in target_content)
        or ("old way" in target_content.lower() and "modern" in target_content.lower())
        or ("Java 8" in target_content and bool(re.search(r"\bJDK (1[7-9]|2[0-5])\b", target_content)))
    )
    has_good_bad_markers = "❌" in target_content and "✅" in target_content

    # Migration guidance
    migration_indicators = {
        "has_migration_paths": "migration" in target_content.lower() or "→" in skill_content,
        "has_deprecation_warnings": "deprecated" in target_content.lower(),
        "has_lts_guidance": "LTS" in target_content,
        "has_preview_warnings": "preview" in target_content.lower() or "--enable-preview" in target_content,
    }

    # Error prevention
    anti_pattern_indicators = {
        "optional_get_warning": "Optional.get()" in target_content or "orElseThrow" in target_content,
        "checked_exception_warning": "checked exception" in target_content.lower(),
        "empty_catch_warning": "empty catch" in target_content.lower(),
        "raw_types_warning": "raw type" in target_content.lower(),
        "mutable_collection_warning": "mutable" in target_content.lower() and "collection" in target_content.lower(),
        "null_safety": "NullPointer" in target_content or "null safe" in target_content.lower(),
    }
    anti_patterns_covered = sum(1 for v in anti_pattern_indicators.values() if v)

    # Description analysis
    description = ""
    if has_yaml_frontmatter:
        frontmatter_end = skill_content.find("---", 3)
        if frontmatter_end > 0:
            frontmatter = skill_content[3:frontmatter_end]
            lines = frontmatter.splitlines()
            for i, line in enumerate(lines):
                if line.startswith("description:"):
                    value = line[len("description:") :].strip()
                    if value in ("|", ">", "|+", ">+", "|-", ">-"):
                        parts = []
                        for cont in lines[i + 1 :]:
                            if cont and (cont[0] == " " or cont[0] == "\t"):
                                parts.append(cont.strip())
                            else:
                                break
                        description = " ".join(parts)
                    else:
                        description = value
                    break

    return {
        "skill_lines": len(skill_content.splitlines()),
        "skill_chars": len(skill_content),
        "reference_file_count": len(reference_files),
        "reference_files": reference_files,
        "code_block_count_skill": code_block_count_skill,
        "code_block_count_refs": code_block_count_refs,
        "has_yaml_frontmatter": has_yaml_frontmatter,
        "has_reference_table": has_reference_table,
        "has_quick_start": has_quick_start,
        "has_core_principles": has_core_principles,
        "has_build_verification": has_build_verification,
        "has_negative_triggers": "DO NOT USE" in skill_content.upper() or "NOT FOR" in skill_content.upper(),
        "jdk_versions_in_skill": jdk_versions_in_skill,
        "jdk_versions_in_scope": jdk_versions_in_scope,
        "jdk25_feature_coverage": f"{jdk25_coverage}/{len(jdk25_features)}",
        "pattern_domains_covered": f"{domains_covered}/{len(pattern_domains)}",
        "pattern_domain_details": {k: v for k, v in pattern_domains.items()},
        "testing_elements_covered": f"{testing_elements_covered}/{len(testing_elements)}",
        "testing_element_details": {k: v for k, v in testing_elements.items()},
        "spring_elements_covered": f"{spring_elements_covered}/{len(spring_elements)}",
        "spring_element_details": {k: v for k, v in spring_elements.items()},
        "has_old_vs_modern_comparisons": has_old_vs_modern,
        "has_good_bad_markers": has_good_bad_markers,
        "migration_indicators": migration_indicators,
        "anti_patterns_covered": f"{anti_patterns_covered}/{len(anti_pattern_indicators)}",
        "anti_pattern_details": {k: v for k, v in anti_pattern_indicators.items()},
        "description_length": len(description),
    }


def normalize_score(score: int) -> int:
    """Clamp model output to the supported rubric range."""
    try:
        value = int(re.search(r"\d+", str(score)).group())
    except (AttributeError, TypeError, ValueError):
        value = 3  # conservative midpoint fallback
    return max(1, min(5, value))


def compute_code_verdicts(heuristic_facts: dict) -> list[dict]:
    """Produce pass/fail verdicts for criteria checkable by code alone."""
    verdicts = []

    verdicts.append(
        {
            "check": "skill_under_250_lines",
            "pass": heuristic_facts["skill_lines"] < 250,
            "value": heuristic_facts["skill_lines"],
            "evidence": f"SKILL.md is {heuristic_facts['skill_lines']} lines (threshold: <250).",
        }
    )
    verdicts.append(
        {
            "check": "has_yaml_frontmatter",
            "pass": heuristic_facts["has_yaml_frontmatter"],
            "value": heuristic_facts["has_yaml_frontmatter"],
            "evidence": "YAML frontmatter present."
            if heuristic_facts["has_yaml_frontmatter"]
            else "Missing YAML frontmatter.",
        }
    )
    verdicts.append(
        {
            "check": "has_negative_triggers",
            "pass": heuristic_facts["has_negative_triggers"],
            "value": heuristic_facts["has_negative_triggers"],
            "evidence": "Negative triggers found."
            if heuristic_facts["has_negative_triggers"]
            else "No negative triggers found.",
        }
    )
    verdicts.append(
        {
            "check": "has_old_vs_modern_comparisons",
            "pass": heuristic_facts["has_old_vs_modern_comparisons"],
            "value": heuristic_facts["has_old_vs_modern_comparisons"],
            "evidence": "Old-vs-modern comparisons found."
            if heuristic_facts["has_old_vs_modern_comparisons"]
            else "No old-vs-modern code comparisons.",
        }
    )
    verdicts.append(
        {
            "check": "has_good_bad_markers",
            "pass": heuristic_facts["has_good_bad_markers"],
            "value": heuristic_facts["has_good_bad_markers"],
            "evidence": "Good/bad markers (✅/❌) found."
            if heuristic_facts["has_good_bad_markers"]
            else "No ✅/❌ markers for good/bad patterns.",
        }
    )
    verdicts.append(
        {
            "check": "has_reference_table",
            "pass": heuristic_facts["has_reference_table"],
            "value": heuristic_facts["has_reference_table"],
            "evidence": "Reference routing table present."
            if heuristic_facts["has_reference_table"]
            else "No reference routing table in SKILL.md.",
        }
    )
    # Parse testing elements
    t_covered, t_total = heuristic_facts["testing_elements_covered"].split("/")
    testing_ok = int(t_covered) >= 12
    verdicts.append(
        {
            "check": "testing_elements_>=12",
            "pass": testing_ok,
            "value": heuristic_facts["testing_elements_covered"],
            "evidence": f"{t_covered}/{t_total} testing elements covered (threshold: >=12).",
        }
    )
    # Parse spring elements
    s_covered, s_total = heuristic_facts["spring_elements_covered"].split("/")
    spring_ok = int(s_covered) >= 6
    verdicts.append(
        {
            "check": "spring_elements_>=6",
            "pass": spring_ok,
            "value": heuristic_facts["spring_elements_covered"],
            "evidence": f"{s_covered}/{s_total} Spring Boot elements covered (threshold: >=6).",
        }
    )
    # Parse pattern domains
    d_covered, d_total = heuristic_facts["pattern_domains_covered"].split("/")
    domains_ok = int(d_covered) >= 12
    verdicts.append(
        {
            "check": "pattern_domains_>=12",
            "pass": domains_ok,
            "value": heuristic_facts["pattern_domains_covered"],
            "evidence": f"{d_covered}/{d_total} pattern domains covered (threshold: >=12).",
        }
    )
    # JDK version coverage
    jdk_count = len(heuristic_facts["jdk_versions_in_scope"])
    jdk_ok = jdk_count >= 8
    verdicts.append(
        {
            "check": "jdk_versions_>=8",
            "pass": jdk_ok,
            "value": jdk_count,
            "evidence": f"{jdk_count} JDK versions referenced (threshold: >=8).",
        }
    )
    desc_ok = heuristic_facts["description_length"] >= 50
    verdicts.append(
        {
            "check": "description_length_adequate",
            "pass": desc_ok,
            "value": heuristic_facts["description_length"],
            "evidence": f"Description is {heuristic_facts['description_length']} chars (threshold: >=50).",
        }
    )

    return verdicts


def format_observable_facts(heuristic_facts: dict, observable_facts: list[str]) -> str:
    """Combine deterministic and model-extracted facts into one prompt block."""
    payload = {
        "heuristic_facts": heuristic_facts,
        "observable_facts": observable_facts,
    }
    return json.dumps(payload, indent=2)


def render_report(
    results: list[dict],
    weighted_total: float,
    overall: float,
    report: dspy.Prediction,
    critique: dict | None = None,
    code_verdicts: list[dict] | None = None,
) -> str:
    """Render the final evaluation report as markdown text."""
    lines = []
    lines.append("=" * 70)
    lines.append("  JAVA BEST PRACTICES SKILL EVALUATION REPORT")
    lines.append("=" * 70)
    lines.append("")

    if code_verdicts:
        lines.append("## Code-Based Verdicts")
        lines.append("")
        passed = sum(1 for v in code_verdicts if v["pass"])
        lines.append(f"  {passed}/{len(code_verdicts)} checks passed")
        lines.append("")
        for v in code_verdicts:
            marker = "✅ PASS" if v["pass"] else "❌ FAIL"
            lines.append(f"  {marker}  {v['check']}: {v['evidence']}")
        lines.append("")

    lines.append("## Executive Summary")
    lines.append("")
    lines.append(report.executive_summary)
    lines.append("")
    lines.append("## Dimension Scores")
    lines.append("")
    lines.append(f"{'Dimension':<32} {'Score':>5}  {'Weighted':>8}  {'Scope':<16} {'Confidence'}")
    lines.append("-" * 95)
    for result in sorted(results, key=lambda item: item["score"]):
        bar = "█" * result["score"] + "░" * (5 - result["score"])
        lines.append(
            f"{result['dimension']:<32} {bar} {result['score']}/5  "
            f"({result['weighted_score']:.3f})  [{result['scope']:<13}]  {result['confidence']}"
        )
    lines.append("-" * 95)
    lines.append(f"{'OVERALL':<32}       {weighted_total:.2f}/5.00 = {overall:.1%}")
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
    if critique:
        lines.append("## Open Critique (Beyond Rubric)")
        lines.append("")
        if critique.get("blind_spots"):
            lines.append("### Blind Spots (topics/patterns the rubric missed)")
            for item in critique["blind_spots"]:
                lines.append(f"  • {item}")
            lines.append("")
        if critique.get("outdated_or_wrong"):
            lines.append("### Outdated or Incorrect Advice")
            for item in critique["outdated_or_wrong"]:
                lines.append(f"  ⚠ {item}")
            lines.append("")
        if critique.get("structural_issues"):
            lines.append("### Structural Issues")
            for item in critique["structural_issues"]:
                lines.append(f"  ✗ {item}")
            lines.append("")
        if not any(critique.get(k) for k in ("blind_spots", "outdated_or_wrong", "structural_issues")):
            lines.append("  No issues found beyond rubric dimensions.")
            lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Evaluation pipeline
# ---------------------------------------------------------------------------


def run_evaluation(skill_path: str) -> str:
    """Run the Java Best Practices evaluation pipeline and return a markdown report."""
    skill_file = Path(skill_path)
    skill_dir = skill_file.parent

    skill_content = skill_file.read_text()
    refs_content = load_references(skill_dir)
    full_content = skill_content + refs_content

    skill_heuristics = build_heuristic_facts(skill_content, refs_content, skill_dir, scope="skill_only")
    full_heuristics = build_heuristic_facts(skill_content, refs_content, skill_dir, scope="full")

    # Code-based verdicts — deterministic pass/fail checks that bypass the LLM
    code_verdicts = compute_code_verdicts(full_heuristics)

    print(f"Evaluating: {skill_path}")
    print(f"SKILL.md: {len(skill_content)} chars, ~{len(skill_content) // 4} tokens")
    if refs_content:
        print(f"References: {len(refs_content)} chars, ~{len(refs_content) // 4} tokens")
    print(f"Full package: {len(full_content)} chars, ~{len(full_content) // 4} tokens")
    print(f"Heuristic facts (skill-only): {json.dumps(skill_heuristics, indent=2)}")
    print(f"Heuristic facts (full):       {json.dumps(full_heuristics, indent=2)}")
    print("=" * 70)

    extract_facts = dspy.ChainOfThought(ExtractObservableFacts)
    evaluate = dspy.ChainOfThought(EvaluateDimension)
    reconcile = dspy.ChainOfThought(ReconcileDimension)
    synthesize = dspy.ChainOfThought(SynthesizeReport)

    # Extract observable facts for both scopes
    print("\nExtracting observable facts (SKILL.md only)...")
    observable_skill_facts = extract_facts(
        skill_content=skill_content,
        heuristic_facts=json.dumps(skill_heuristics, indent=2),
    ).observable_facts

    print("Extracting observable facts (full package)...")
    observable_full_facts = extract_facts(
        skill_content=full_content,
        heuristic_facts=json.dumps(full_heuristics, indent=2),
    ).observable_facts

    # Evaluate each dimension with dual reviewers + reconciliation
    results = []
    weighted_total = 0.0

    for dim_name, dim_cfg in RUBRIC.items():
        if dim_name in SKILL_ONLY_DIMS:
            content = skill_content
            scope = "SKILL.md only"
            facts = format_observable_facts(skill_heuristics, observable_skill_facts)
        else:
            content = full_content
            scope = "full package"
            facts = format_observable_facts(full_heuristics, observable_full_facts)

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

    # Open-ended critique (blind-spot discovery beyond the rubric)
    print("\nRunning open critique (blind-spot discovery)...")
    open_critique_fn = dspy.ChainOfThought(OpenCritique)
    critique = open_critique_fn(
        skill_content=full_content,
        rubric_dimensions=json.dumps(list(RUBRIC.keys())),
    )
    critique_payload = {
        "blind_spots": critique.blind_spots,
        "outdated_or_wrong": critique.outdated_or_wrong,
        "structural_issues": critique.structural_issues,
    }
    print(f"  Blind spots found:      {len(critique.blind_spots)}")
    print(f"  Outdated/wrong found:   {len(critique.outdated_or_wrong)}")
    print(f"  Structural issues found: {len(critique.structural_issues)}")

    # Synthesize final report
    print("\nSynthesizing improvement report...")
    report = synthesize(
        skill_content=full_content,
        dimension_results=json.dumps(results, indent=2),
        open_critique=json.dumps(critique_payload, indent=2),
        overall_score=overall,
    )

    return render_report(results, weighted_total, overall, report, critique_payload, code_verdicts)


if __name__ == "__main__":
    _required_env = ["AZURE_OPENAI_DEPLOYMENT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"]
    _missing = [v for v in _required_env if v not in os.environ]
    if _missing:
        raise SystemExit(f"Missing required environment variables: {', '.join(_missing)}")

    lm = dspy.LM(
        model=f"azure/{os.environ['AZURE_OPENAI_DEPLOYMENT']}",
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_base=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
        max_tokens=16000,
    )
    dspy.configure(lm=lm)

    print(run_evaluation("../java-best-practices/SKILL.md"))
