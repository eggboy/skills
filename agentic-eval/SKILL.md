---
name: agentic-eval
description: |
  Patterns and techniques for evaluating and improving AI agent outputs. Use this skill when:
  - Implementing self-critique and reflection loops
  - Building evaluator-optimizer pipelines for quality-critical generation
  - Creating test-driven code refinement workflows
  - Designing rubric-based or LLM-as-judge evaluation systems
  - Adding iterative improvement to agent outputs (code, reports, analysis)
  - Measuring and improving agent response quality
  Do NOT use for unit testing, code linting, static analysis, benchmarking
  non-agent outputs, or simple pass/fail validation without iteration.
---

# Agentic Evaluation Patterns

Patterns for self-improvement through iterative evaluation and refinement.

## Overview

Evaluation patterns enable agents to assess and improve their own outputs, moving beyond single-shot generation to iterative refinement loops.

```
Generate → Evaluate → Critique → Refine → Output
    ↑                              │
    └──────────────────────────────┘
```

## When to Use

- **Quality-critical generation**: Code, reports, analysis requiring high accuracy
- **Tasks with clear evaluation criteria**: Defined success metrics exist
- **Content requiring specific standards**: Style guides, compliance, formatting

## Pattern Selection Guide

Choose the right pattern based on your task:

| Task type | Pattern | Key mechanism |
|-----------|---------|---------------|
| Quick single-pass improvement | Basic Reflection | Self-critique with PASS/FAIL per criterion |
| Multi-dimensional quality scoring | Evaluator-Optimizer | Separate generate/evaluate/optimize components |
| Code generation | Code-Specific Reflection | Test-driven: generate → run tests → fix errors |
| Tracking improvement over time | Rubric-Based | Weighted dimension scores |
| Discovering unknown quality gaps | Hybrid (Rubric + Open Critique) | Rubric scores + open-ended blind-spot discovery |
| Comparing two outputs | LLM-as-Judge | Pairwise comparison |

---

## Patterns

### Basic Reflection
Generate → self-critique (PASS/FAIL per criterion as JSON) → refine failed criteria → repeat until all pass or max iterations hit. **Non-obvious insight**: Always use structured JSON for critique output; free-text critique causes parse failures that break the loop.

### Evaluator-Optimizer
Separate generation and evaluation into distinct components: `generate()`, `evaluate()` (returns score 0-1 + per-dimension breakdown), `optimize()` (takes feedback). Stop when `overall_score >= threshold`. **Non-obvious insight**: The evaluator must not see the original task prompt to avoid anchoring bias — pass only the output and evaluation criteria.

### Code-Specific Reflection
Generate code → generate tests → run tests → fix errors from test output → repeat. **Non-obvious insight**: Generate tests from the *spec*, not from the code, to avoid testing implementation details rather than requirements.

---

## Evaluation Strategies

### Outcome-Based
Evaluate whether output achieves the expected result.

```python
def evaluate_outcome(task: str, output: str, expected: str) -> str:
    return llm(f"Does output achieve expected outcome? Task: {task}, Expected: {expected}, Output: {output}")
```

### LLM-as-Judge
Use LLM to compare and rank outputs.

```python
def llm_judge(output_a: str, output_b: str, criteria: str) -> str:
    return llm(f"Compare outputs A and B for {criteria}. Which is better and why?")
```

### Rubric-Based
Score outputs against weighted dimensions.

```python
RUBRIC = {
    "accuracy": {"weight": 0.4},
    "clarity": {"weight": 0.3},
    "completeness": {"weight": 0.3}
}

def evaluate_with_rubric(output: str, rubric: dict) -> float:
    scores = json.loads(llm(f"Rate 1-5 for each dimension: {list(rubric.keys())}\nOutput: {output}"))
    return sum(scores[d] * rubric[d]["weight"] for d in rubric) / 5
```

### Rubric + Open Critique (Hybrid)

Rubric-based scoring tracks measurable improvement over time but can only score
what the rubric author thought to measure. Pair it with an **open critique** pass
to discover blind spots — important gaps the rubric doesn't cover.

**When to use**: Any rubric-based eval where the output space is broad enough that
a fixed set of dimensions may miss important quality signals (e.g., evaluating a
knowledge base, a style guide, or a multi-file skill package).

```python
def open_critique(output: str, rubric_dimensions: list[str]) -> dict:
    """Discover quality gaps a fixed rubric misses."""
    return json.loads(llm(f"""
    You are a senior reviewer. Ignore these rubric dimensions (already scored):
      {rubric_dimensions}
    
    Instead, independently read the output and identify:
    1. blind_spots: Important topics or patterns completely absent
    2. outdated_or_wrong: Advice that is outdated, misleading, or incorrect
    3. structural_issues: Organizational problems (orphaned refs, circular guidance)
    
    Be specific. Do not repeat rubric-territory observations like "needs more examples".
    Return JSON: {{"blind_spots": [...], "outdated_or_wrong": [...], "structural_issues": [...]}}
    
    Output:
    {output}
    """))

def hybrid_evaluate(output: str, rubric: dict) -> dict:
    """Rubric scoring + open critique in one pipeline."""
    # Phase 1: Rubric scores (trackable over time)
    rubric_score = evaluate_with_rubric(output, rubric)
    
    # Phase 2: Open critique (discovery of unknowns)
    critique = open_critique(output, list(rubric.keys()))
    
    # Phase 3: Synthesize — feed BOTH into final report
    report = llm(f"""
    Produce a prioritized improvement plan integrating:
    - Rubric scores: {rubric_score}
    - Open critique findings: {json.dumps(critique)}
    Focus on lowest rubric scores first, then blind spots from the critique.
    """)
    return {"rubric_score": rubric_score, "critique": critique, "report": report}
```

**Key tradeoffs**:

| Approach | Tracks progress | Discovers unknowns | Cost |
|----------|:-:|:-:|:-:|
| Rubric only | ✅ | ❌ | Lower |
| Open critique only | ❌ | ✅ | Lower |
| Hybrid (rubric + critique) | ✅ | ✅ | ~1 extra LLM call |

**When to graduate**: Once rubric scores plateau at the ceiling (e.g., all 5/5),
the rubric stops being useful. Switch to pairwise LLM-as-Judge comparison against
a gold-standard reference, or recalibrate the rubric with harder criteria.

---

## Common Pitfalls

| Pitfall | Symptom | Mitigation |
|---------|---------|------------|
| **Score inflation in self-critique** | Model rates own output 4-5/5 consistently | Use a separate evaluator model, or add "score conservatively" to the evaluator prompt |
| **Convergence oscillation** | Output flips between two states across iterations | Track score history; stop if score doesn't improve for 2 consecutive iterations |
| **JSON parse failures** | LLM returns malformed JSON, crashing the loop | Wrap parsing in try/except with regex fallback extraction; never let one bad parse kill the pipeline |
| **Rubric ceiling effect** | All dimensions hit 5/5 but output is clearly not perfect | The rubric has gone stale — recalibrate with harder criteria or switch to pairwise comparison |
| **Open critique echoing rubric** | Open critique repeats rubric-territory observations despite instructions | Explicitly list rubric dimension names in the critique prompt and instruct: "do NOT comment on these" |
| **Evaluation cost explosion** | Dual-reviewer + reconciliation + critique = 4+ LLM calls per dimension | Budget-gate: use single reviewer for low-weight dimensions; reserve dual-reviewer for top-weighted ones |

---

## Best Practices

| Practice | Rationale |
|----------|-----------|
| **Clear criteria** | Define specific, measurable evaluation criteria upfront |
| **Iteration limits** | Set max iterations (3-5) to prevent infinite loops |
| **Convergence check** | Stop if output score isn't improving between iterations |
| **Log history** | Keep full trajectory for debugging and analysis |
| **Structured output** | Use JSON for reliable parsing of evaluation results |
| **Scope heuristics to content** | When grounding scores with heuristic facts, match scope to what the evaluator sees |

---

## Quick Start Checklist

### Evaluation Implementation Checklist

#### Setup
- [ ] Define evaluation criteria/rubric
- [ ] Set score threshold for "good enough"
- [ ] Configure max iterations (default: 3)

#### Implementation
- [ ] Implement generate() function
- [ ] Implement evaluate() function with structured output
- [ ] Implement optimize() function
- [ ] Wire up the refinement loop
- [ ] Consider hybrid approach: rubric + open critique

### Safety
- [ ] Add convergence detection (stop if no improvement for 2 iterations)
- [ ] Log all iterations for debugging
- [ ] Handle evaluation parse failures gracefully (regex fallback)
- [ ] Harden score parsing (extract first integer, fallback to midpoint)