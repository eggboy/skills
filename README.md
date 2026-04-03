# Skills

A collection of AI agent skills — reusable procedural knowledge packages that extend AI assistants like GitHub Copilot, Claude, and others. Each skill encodes domain expertise, conventions, and workflows that agents can follow when performing specialized tasks.

## Skills

| Skill | Description |
|-------|-------------|
| [agentic-eval](agentic-eval/) | Patterns for evaluating and improving AI agent outputs — self-critique loops, evaluator-optimizer pipelines, rubric-based evaluation |
| [azure-cost-analysis](azure-cost-analysis/) | Analyze Azure costs via the CostManagement REST API — query construction, breakdowns by resource/meter/service, anomaly detection |
| [azure-naming-convention](azure-naming-convention/) | Generate compliant Azure resource names following Microsoft Cloud Adoption Framework (CAF) best practices |
| [azure-verified-modules](azure-verified-modules/) | Develop and consume certified Azure Verified Modules (AVM) for Terraform — VNet injection, subnet delegation, NSG rules |
| [cli-creator](cli-creator/) | Create CLI tools following clig.dev best practices — supports Python (Click/Typer), Node.js (Commander), Go (Cobra), Rust (Clap), and Bash |
| [eval-audit](eval-audit/) | Audit LLM eval pipelines to surface problems — missing error analysis, unvalidated judges, vanity metrics |
| [fastapi](fastapi/) | Build FastAPI applications with uv project setup, Pydantic models, dependency injection, async endpoints, SSE streaming |
| [generate-synthetic-data](generate-synthetic-data/) | Create diverse synthetic test inputs for LLM pipeline evaluation using dimension-based tuple generation |
| [java-best-practices](java-best-practices/) | Modern Java best practices (JDK 8–25) — records, sealed classes, pattern matching, virtual threads, Spring Boot, JUnit 5 |
| [microsoft-agent-framework](microsoft-agent-framework/) | Build AI agents using the Microsoft Agent Framework Python SDK 1.0.0 — OpenAI, Azure OpenAI, Foundry, Anthropic providers |
| [python-best-practices](python-best-practices/) | Modern Python best practices — PEP 8, type hints, pytest, dataframe workflows (Pandas/Polars/DuckDB), Python data model patterns |
| [skill-creator](skill-creator/) | Create and update Agent Skills following the agentskills.io specification |
| [skillshare](skillshare/) | Manage and sync AI CLI skills across 50+ tools from a single source |
| [terraform-style-guide](terraform-style-guide/) | Generate Terraform HCL following HashiCorp's official style conventions and best practices |
| [write-judge-prompt](write-judge-prompt/) | Design LLM-as-Judge evaluators for subjective criteria that code-based checks cannot handle |

## Structure

Each skill follows a consistent layout:

```
skill-name/
├── SKILL.md              # Main skill file with YAML frontmatter and instructions
├── references/           # Supporting reference material loaded on demand
│   ├── topic-a.md
│   └── topic-b.md
└── evals/                # Optional evaluation tasks for the skill
```

- **`SKILL.md`** — The entry point. Contains the skill name, description (used for matching), and the full procedural instructions the agent follows.
- **`references/`** — Supplementary docs that the skill loads as needed to keep the main file focused.
- **`evals/`** — Task definitions for testing skill quality (see `eval/` at the repo root).

## Usage

### With Skillshare

Install skills to any supported AI tool using [skillshare](skillshare/):

```bash
skillshare install <skill-name>
skillshare sync
```

### Manual

Copy or symlink a skill directory into your AI tool's skill/prompt configuration folder. For example, with GitHub Copilot in VS Code, place skills under `~/.copilot/skills/`.

## Evals

The `eval/` directory contains evaluation scripts that test skill quality:

```
eval/
├── eval_azure_verified_modules.py
├── eval_cli_creator.py
├── eval_java_best_practices.py
├── eval_skill_creator.py
└── eval_terraform_style_guide.py
```