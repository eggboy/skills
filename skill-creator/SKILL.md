---
name: skill-creator
description: Create and update Agent Skills following the agentskills.io specification. Use when building reusable procedural knowledge, workflows, or tool integrations that extend AI agent capabilities. Applicable to GitHub Copilot, Claude, and other AI assistants. DO NOT use when the task can be accomplished with a simple prompt or when the user is not creating reusable skill packages.
---

# Skill Creator

Guide for creating Agent Skills—modular packages of procedural knowledge, workflows, and tools that extend AI agents beyond what any model inherently knows.

## Core Principles

### Concise is Key

Skills share the context window with system prompts, conversation history, and other skills. Only add context the agent doesn't already have—challenge each paragraph's token cost. Prefer concise examples over verbose explanations.

### Set Appropriate Degrees of Freedom

Match the level of specificity to the task's fragility and variability:

**High freedom (text-based instructions)**: Use when multiple approaches are valid, decisions depend on context, or heuristics guide the approach.

**Medium freedom (pseudocode or scripts with parameters)**: Use when a preferred pattern exists, some variation is acceptable, or configuration affects behavior.

**Low freedom (specific scripts, few parameters)**: Use when operations are fragile and error-prone, consistency is critical, or a specific sequence must be followed.

### Anatomy of a Skill

Every skill consists of a required SKILL.md file and optional bundled resources:

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata (required)
│   │   ├── name: (required)
│   │   ├── description: (required)
│   │   └── compatibility: (optional, rarely needed)
│   └── Markdown instructions (required)
└── Bundled Resources (optional)
    ├── scripts/          - Executable code (Python/Bash/etc.)
    ├── references/       - Documentation intended to be loaded into context as needed
    └── assets/           - Files used in output (templates, icons, fonts, etc.)
```

#### SKILL.md (required)

Every SKILL.md consists of:

- **Frontmatter** (YAML): Contains `name` and `description` fields (required), plus optional fields like `license`, `metadata`, `compatibility`, and `allowed-tools`. Only `name` and `description` are read by the AI agent to determine when the skill triggers, so be clear and comprehensive about what the skill is and when it should be used. The `compatibility` field is for noting environment requirements (target product, system packages, etc.) but most skills don't need it.
- **Body** (Markdown): Instructions and guidance for using the skill. Only loaded AFTER the skill triggers (if at all).

#### Bundled Resources (optional)

##### Scripts (`scripts/`)

Executable code (Python/Bash/etc.) for tasks that require deterministic reliability or are repeatedly rewritten. Can be executed without loading into context. Scripts may still need to be read for patching or environment-specific adjustments.

**Python scripts**: Use PEP 723 inline script metadata so dependencies are declared in the script itself, then run with `uvx` for zero-install execution:

```python
# /// script
# requires-python = ">=3.12"
# dependencies = ["pdfplumber", "Pillow"]
# ///
```

Run via `uvx run script.py` — no virtual environment or `pip install` needed.

##### References (`references/`)

Documentation loaded as needed into context (schemas, API docs, domain knowledge, policies).

- Information should live in either SKILL.md or references, not both—prefer references for detailed content
- If files are large (>10k words), include grep search patterns in SKILL.md

##### Assets (`assets/`)

Files used in the agent's output but not loaded into context (templates, images, icons, boilerplate, fonts).

#### What to Not Include in a Skill

Do not include auxiliary files (README, CHANGELOG, installation guides, etc.). Only include files the agent needs to do the job.

### Progressive Disclosure Design Principle

Skills use a three-level loading system to manage context efficiently:

1. **Metadata (name + description)** - Loaded automatically (~100 tokens)
2. **SKILL.md body** - When skill triggers (<5000 tokens recommended)
3. **Bundled resources** - As needed by the agent (Unlimited because scripts can be executed without reading into context window)

#### Progressive Disclosure Patterns

Keep SKILL.md body to the essentials and under 500 lines to minimize context bloat. Split content into separate files when approaching this limit. When splitting out content into other files, it is very important to reference them from SKILL.md and describe clearly when to read them, to ensure the agent knows they exist and when to use them.

**Key principle:** When a skill supports multiple variations, frameworks, or options, keep only the core workflow and selection guidance in SKILL.md. Move variant-specific details (patterns, examples, configuration) into separate reference files.

**Pattern: High-level guide with references**

```markdown
# PDF Processing

## Quick start
Extract text with pdfplumber: [code example]

## Advanced features
- **Form filling**: See [FORMS.md](FORMS.md) for complete guide
- **API reference**: See [REFERENCE.md](REFERENCE.md) for all methods
```

The agent loads reference files only when needed. This same pattern applies to domain-specific splits (e.g., `references/finance.md`, `references/sales.md`) and conditional details (linking to advanced topics only when relevant).

**Guidelines:**

- Keep references one level deep from SKILL.md—all reference files should link directly from SKILL.md
- For reference files longer than 100 lines, include a table of contents at the top

### Skill Quality Validation

Run these checks before finalizing any skill to ensure optimal agent performance.

#### Anti-Pattern Scan

Scan SKILL.md for patterns that degrade agent performance:

- **Conflicting procedure paths**: Flag phrases like "but alternatively…", "or you could…", "another option is…" that create ambiguous execution paths. Pick one recommended approach and move alternatives to a reference file if needed.
- **Duplicate step sequences**: Identify repeated instruction blocks. Deduplicate by extracting shared steps into a single section and referencing it.
- **Excessive constraint keywords**: Count occurrences of "must not", "never", "always", "do not", "required" in the body. More than 5 triggers a warning—over-constraining narrows the agent's ability to adapt. Rewrite as positive guidance where possible (e.g., "prefer X" instead of "never use Y").

#### Procedural Language Check

Verify the description uses procedural language—action verbs ("deploy", "configure", "create", "analyze") and procedure keywords ("step", "then", "workflow", "process", "sequence"). Procedural content correlates with a +18.8pp improvement in skill activation rates across models.

#### Description Density Validation

Validate the `description` field for cross-model effectiveness:

- **Word count**: ≤60 words. Shorter descriptions trigger more reliably across different AI models.
- **First sentence**: Must lead with an action verb (e.g., "Create…", "Deploy…", "Analyze…").
- **No unquoted colons**: Reject any `description` value containing `:` unless the entire value is wrapped in double quotes. Rewrite to remove colonsfirst; quoting is a last resort.

## Skill Creation Process

Skill creation involves these steps:

1. Understand the skill with concrete examples
2. Plan reusable skill contents (scripts, references, assets)
3. Initialize the skill (create directory, SKILL.md, and placeholder resources)
4. Edit the skill (implement resources and write SKILL.md)
5. Iterate based on real usage

Follow these steps in order, skipping only if there is a clear reason why they are not applicable.

### Step 1: Understanding the Skill with Concrete Examples

Skip when the skill's usage patterns are already clearly understood.

Gather concrete examples of how the skill will be used—from the user directly or by generating examples and validating them. Ask focused questions like: "What functionality should this skill support?" and "What would a user say to trigger it?"

Avoid asking too many questions at once. Conclude when the skill's scope is clear.

### Step 2: Planning the Reusable Skill Contents

For each concrete example, analyze: (1) how to execute it from scratch, and (2) what would be helpful to have pre-built for repeated execution.

Example: A `pdf-editor` skill for "Help me rotate this PDF" → repeated code → add `scripts/rotate_pdf.py`. A `frontend-webapp-builder` → repeated boilerplate → add `assets/hello-world/` template. A `big-query` skill → repeated schema discovery → add `references/schema.md`.

Produce a list of reusable resources (scripts, references, assets) to include.

### Step 3: Initializing the Skill

Create the skill directory with a SKILL.md template and example `scripts/`, `references/`, `assets/` directories. Customize or remove generated example files as needed.

### Step 4: Edit the Skill

When editing the (newly-generated or existing) skill, remember that the skill is being created for an AI agent to use. Include information that would be beneficial and non-obvious to the agent. Consider what procedural knowledge, domain-specific details, or reusable assets would help an AI agent execute these tasks more effectively.

#### Learn Proven Design Patterns

Consult these helpful guides based on your skill's needs:

- **Multi-step processes**: See references/workflows.md for sequential workflows and conditional logic
- **Specific output formats or quality standards**: See references/output-patterns.md for template and example patterns

These files contain established best practices for effective skill design.

#### Start with Reusable Skill Contents

Implement the resources identified in Step 2. This may require user input (e.g., brand assets, documentation to store).

- Test added scripts by running them. For many similar scripts, test a representative sample.
- Delete any example files/directories not needed for the skill.

#### Update SKILL.md

**Writing Guidelines:** Always use imperative/infinitive form.

##### Frontmatter

Write the YAML frontmatter with required and optional fields:

**Required fields:**
- `name`: The skill name (1-64 characters, lowercase alphanumeric and hyphens only, must match parent directory name)
- `description`: Primary triggering mechanism (1-1024 characters). Include what the skill does AND when to use it. This is the only field read before the body loads.
  - **No colons (`:`)** — colons break YAML parsing. Rewrite to eliminate them (e.g., "Use when" instead of "Use for: when"). If a colon is unavoidable, wrap the entire value in double quotes.
  - Lead the first sentence with an action verb (e.g., "Create…", "Deploy…", "Analyze…")
  - Keep to ≤60 words for cross-model effectiveness — shorter descriptions trigger more reliably across different AI models
  - Use procedural language (action verbs, procedure keywords like "workflow", "configure", "step") — this correlates with stronger skill activation
  - Example: "Create and edit .docx files with tracked changes, comments, formatting preservation, and text extraction. Use when working with Word documents for creation, modification, or analysis tasks."

**Optional fields:**
- `license`: License name or reference to a bundled license file (e.g., "Apache-2.0" or "Proprietary. LICENSE.txt has complete terms")
- `compatibility`: Environment requirements (1-500 characters) - intended product, required system packages, network access needs, etc.
- `metadata`: Arbitrary key-value mapping for additional metadata (e.g., author, version)
- `allowed-tools`: Space-delimited list of pre-approved tools (experimental, support varies between agent implementations)

##### Body

Write instructions for using the skill and its bundled resources.


### Step 5: Iterate

After testing the skill, users may request improvements. Often this happens right after using the skill, with fresh context of how the skill performed.

**Iteration workflow:**

1. Use the skill on real tasks
2. Notice struggles or inefficiencies
3. Identify how SKILL.md or bundled resources should be updated
4. Implement changes and test again
