---
name: auto-reflection
description: "Apply a structured self-review before final answers. Use for coding, documentation, and planning tasks to catch requirement gaps, risky assumptions, missing validation, and unclear communication."
argument-hint: "Task goal, constraints, and required outputs"
user-invocable: true
---

# Auto Reflection

## Purpose

Use this skill to improve response quality by running a short, explicit reflection cycle before presenting final output.

## When to Use

- Multi-step implementation tasks
- Bug fixes with potential regressions
- Code reviews and change-risk analysis
- Documentation updates with strict structure or evidence needs
- Planning tasks that include decisions, tradeoffs, or assumptions
- Requests with strict constraints or formatting rules
- Any response where correctness and completeness are more important than speed

## Inputs

- User goal and success criteria
- Non-functional constraints (style, tools, performance, security)
- Required deliverables (files, tests, summary)

## Procedure

1. Restate target outcome in one sentence.
2. Build a requirement checklist from the user request.
3. Execute work and gather evidence (edits, command output, test results).
4. Run a reflection pass using the checklist below.
5. If a gap is found, fix it and re-validate.
6. Produce the final response with outcomes, evidence, and residual risks.

## Reflection Checklist

- Requirement coverage: Were all explicit asks addressed?
- Constraint compliance: Were tool, formatting, and safety constraints followed?
- Behavioral safety: Could changes introduce regressions or side effects?
- Validation strength: Were relevant tests, checks, or reasoning run?
- Communication quality: Is the result clear, specific, and action-ready?

## Decision Points

- If any requirement is missing, complete it before finalizing.
- If validation fails, fix and re-run validation.
- If uncertainty remains high, state assumptions and ask only the minimum blocking question.
- If no tooling is available for validation, provide manual verification steps and note the gap.

## Completion Criteria

- All checklist items pass or unresolved items are explicitly documented.
- The final response includes what changed, how it was validated, and any remaining risk.
- No hidden assumptions remain that would change implementation behavior.

## Output Contract

The final response should include:

1. Result summary
2. Concrete changes made
3. Validation performed
4. Known limitations or risks
5. Optional next steps (only when natural and useful)
