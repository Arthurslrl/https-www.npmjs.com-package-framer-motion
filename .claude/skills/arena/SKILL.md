---
name: arena
description: "Run Arena Mode — spawn N agents on the same task, rank their solutions, and return the best. Use for ambiguous bugs, design trade-offs, refactors, or optimizations with multiple valid approaches."
disable-model-invocation: true
---

# Arena Mode

You are the **Arena Orchestrator**. Your job is to run a fair competition among independent solvers on the *identical* task, then rank the results and present a clear recommendation to the user.

## Argument Parsing

Parse the invocation carefully:

- The **task** is the main quoted string or the free-form text after `/arena`.
- Optional flags (order-independent):
  - `n=<number>` → number of solver agents (default: **4**, recommended range 3–6)
  - `strategy=<name>` → one of `judge` | `main` | `tournament` (default: **judge**)
  - `solver-model=<name>` → model used by all solver subagents (default: current session model)
  - `judge-model=<name>` → model used by the Judge subagent when strategy=judge (default: current session model)
  - `model=<name>` → shorthand that sets both solver-model and judge-model

Parsing rules for models:
- If only `model=` is given → apply it to both solvers and judge.
- If `solver-model=` or `judge-model=` is given → they override `model=` for that role.
- If nothing is specified → use the current session model for everything.
- Unknown or invalid model names → fall back to the current session model and warn the user.

Valid model names (aliases only): `opus`, `sonnet`, `haiku`, `fable`.
Version-suffixed names (e.g. `opus-4.8`, `sonnet-5`) are NOT accepted — the subagent model arg takes aliases only. Aliases track the current family default. Anything else falls back to the session model + warn.

Example that must work exactly:

/arena "Refactor the auth middleware to support both JWT and API keys without breaking existing clients" n=4 strategy=judge solver-model=sonnet judge-model=opus

→ Task = “Refactor the auth middleware…”, n = 4, strategy = judge, solver-model = sonnet, judge-model = opus.

If the user only gives a task with no flags, use the defaults (n=4, strategy=judge, current session model for everything).

**Before spawning any agents**, briefly confirm the parsed values to the user, e.g.:

> Running Arena Mode  
> Task: Refactor the auth middleware…  
> n = 4  
> strategy = judge  
> solver-model = sonnet  
> judge-model = opus  

Then proceed.

## Core Rules (apply to every strategy)

1. **Identical task** — Every solver receives the *exact same* locked task prompt. Do not let solvers see each other’s work or intermediate files.
2. **Isolation** — Prefer worktree isolation when the task involves writing or editing code so solvers cannot conflict.
3. **Anonymization for judging** — When a judge sees multiple solutions, present them as Solution A, B, C… with no agent identity.
4. **No automatic commit** — Never apply code changes until the user explicitly approves a candidate.
5. **Clear output** — Always return:
   - Ranked list (best first)
   - Short summary of each approach
   - Key differences between the top candidates
   - Explicit recommendation + why
   - Ask the user which one to apply (or confirm auto-apply if they already requested it)

## Strategy: judge (default)

**Best for:** Most cases. Clean separation of generation and evaluation.

### Steps

1. Lock the exact task prompt.
2. Spawn **N independent solver subagents** in parallel using the chosen **solver-model**.
   - Each gets the identical task.
   - Optionally give each a different light bias (examples: “prefer minimal change”, “prefer clean architecture”, “prefer performance”, “prefer readability”).
   - Require each solver to return:
     - Approach summary (2–4 sentences)
     - The actual solution (code / plan / diff)
     - Self-assessed confidence (1–5) and main risks
3. After all solvers finish, spawn **one Judge subagent** using the chosen **judge-model**.
   - Give the Judge:
     - The original task
     - The scoring rubric (see below)
     - All solutions, anonymized as Solution A, B, C…
   - Instruct the Judge to return a ranked list with clear reasons for each ranking decision.
4. Present the Judge’s ranking to the user in a clean, readable format. Add your own brief synthesis if helpful.
5. Wait for user choice before applying any changes.

## Strategy: main

**Best for:** Lower cost or when you want the orchestrator (you) to stay fully in control of the evaluation.

### Steps

1. Lock the exact task prompt.
2. Spawn **N independent solver subagents** in parallel using the chosen **solver-model** (same requirements as judge strategy).
3. Collect all results yourself.
4. Evaluate and rank them **yourself** using the scoring rubric. Do not spawn a separate Judge.
5. Present the ranked list + recommendation to the user.
6. Wait for user choice before applying any changes.

## Strategy: tournament

**Best for:** High-stakes decisions or when you want solutions to stress-test each other.

### Steps

1. Lock the exact task prompt.
2. Spawn **N independent solver subagents** in parallel using the chosen **solver-model** (same requirements as above).
3. Run a simple **tournament**:
   - If N is even, pair them randomly. If odd, give one a bye.
   - For each pair, have a short critique (you or a small critic subagent) compare the two solutions side-by-side and declare a winner with 2–3 concrete reasons.
   - Optionally run one more ranking pass on the winners (or full set) using the scoring rubric.
4. Produce the final ranking from the critique outcomes + rubric.
5. Present the tournament insights + final ranking + recommendation to the user.
6. Wait for user choice before applying any changes.

## Default Scoring Rubric

Use this rubric unless the user supplies a different one. Weight roughly:

| Criterion                        | Weight | Notes |
|----------------------------------|--------|-------|
| Correctness / completeness       | High   | Does it fully solve the stated task? |
| Compatibility / non-breaking     | High   | Especially important for refactors |
| Minimal & focused change         | Medium | Prefer smaller, targeted diffs when quality is equal |
| Clarity & maintainability        | Medium | Readable, well-structured, good names |
| Risk / side-effect surface       | Medium | Fewer new failure modes is better |
| Plan adherence (if a plan exists)| Medium | Stays faithful to any agreed design |

## Output Format (required)

## Arena Results (strategy: <name>, n=<N>)

### Ranking
1. **Solution A** — <one-line summary>
   - Why it ranked here: ...
2. **Solution B** — ...
...

### Key Differences
- ...

### Recommendation
I recommend **Solution X** because ...

Which solution would you like me to apply? (or say "apply 1" / "apply A")

## Tips for Good Results

- Keep N between 3 and 6 for most tasks. Higher N has diminishing returns and higher cost.
- For pure design/architecture questions you can ask solvers for approaches + trade-offs only (no code).
- If the task is a refactor, remind solvers to preserve existing behavior and mention compatibility explicitly in the task prompt.
- Always prefer isolation (worktrees) when code will be written.
- Use a cheaper model for solvers and a stronger model for the Judge when you want to balance cost and ranking quality.
