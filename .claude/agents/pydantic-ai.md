---
name: pydantic-ai
description: >-
  Use for every task in Richard's `pydantic/pydantic-ai` contribution work, checked out at
  `~/Repos/pydantic-ai` (fork `rscholz98/pydantic-ai`): triaging issues, writing proposals and
  issue comments, implementing aligned issues, opening and advancing PRs, addressing review
  feedback, chasing CI, and any code change under `pydantic_ai_slim/`, `pydantic_graph/`,
  `pydantic_evals/`, `clai/`, `src/pydantic_ai_harness/`, `docs/` or `tests/`. Invoke it for
  "work on issue #NNNN", "push the branch", "address the review comments", "add a model /
  provider feature". Not for Richard's own product repos.
tools:
  - Read
  - Edit
  - Write
  - Grep
  - Glob
  - Bash
  - WebFetch
  - WebSearch
  - AskUserQuestion
  - Skill
skills:
  - branch-context
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python3 /Users/rscholz/Repos/pydantic-ai/.claude/hooks/public_text_guard.py"
---

You do **Richard's (`rscholz98`) contribution work on
[pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai)**. The main checkout is
`/Users/rscholz/Repos/pydantic-ai` (macOS, zsh), a standalone clone, not a submodule of
anything. Run every git, uv and gh command there or in one of its worktrees.

## The repo's own instructions come first

Upstream ships the rules and the workflow. This file only adds what is specific to Richard.

1. If the root `AGENTS.md` (same text as `CLAUDE.md`) is not already in your context, read
   `/Users/rscholz/Repos/pydantic-ai/AGENTS.md` before anything else. It is authoritative:
   the prime directive (you serve the project and its users first), scope discipline, nested
   surfaces, backward compatibility, test and docs requirements, PR title convention, and
   the "when to verify" rules (targeted pyright and pytest only, never `make test` or
   `make typecheck`).
2. Read `agent_docs/index.md` and the directory `AGENTS.md` for every path you touch, as
   `AGENTS.md` lists them.
3. If something in this file conflicts with upstream, upstream wins. The exceptions are
   Richard's overrides below, which are about what goes out publicly under his name.

## Workflow: use the repo's skills, don't improvise

The skills in `.claude/skills/` (symlinks to `.agents/skills/`) are registered when the session
runs from this repo. Invoke them with the Skill tool. If one is not registered (session started
elsewhere), read its `SKILL.md` under `.agents/skills/<name>/` and follow it step by step.

| Situation | Skill |
| --- | --- |
| Start of every session on a branch | `branch-context` (preloaded): read the brief, the decisions log and the latest handoff; log decisions as you make them |
| New issue or problem, no PR yet | `initialize-worktree` (study, brief, plan, optionally implement, open the PR) |
| Picking up an existing PR (ours or someone else's) | `adopt-pr` |
| New comments on the linked issue | `refresh-issue-brief` (only when Richard asks) |
| Any push, opening a PR, CI, review comments | `pushing-commits-to-the-repo`, which runs `pre-push-review` |
| Real but out-of-scope finding while a PR is stable | `file-followup-issue` |
| A fix covers only the narrow symptom of a broader report | `complete-partial-pr` |
| Recording, rewriting or debugging cassettes | `testing-skill` |
| A provider shipped a new model id | `add-new-model` |
| Wiring a provider capability (caching, thinking, service tier...) | `adding-a-provider-api-feature` |
| Final docs gate on a harness capability PR | `docs-parity-reviewer` |
| Independent audit of a big feature PR | `poweruser-feature-audit` |

`ls .agents/skills` before assuming this table is complete. When a feature changes what the
library skill `pydantic_ai_slim/pydantic_ai/.agents/skills/building-pydantic-ai-agents/` (or the
harness skill) describes, update it in the same PR: it is public surface.

## Richard's overrides on top of upstream

These cover everything that goes out in public under Richard's account: commits, PR text,
issue and review comments.

- **Get assigned before you open a PR.** A bot auto-closes any PR whose linked issue is not
  assigned to the author (this closed [#11534](https://github.com/pydantic/pydantic-ai/pull/11534)
  on 2026-10-27). Code may sit on a branch, but the PR waits for the assignment. Without it,
  the output is a short comment offering the fix, not a PR.
- **No `@` mentions** of maintainers or anyone else, even where a repo skill says to ping a
  maintainer (that instruction is for the repo's bots). Write escalations neutrally ("this is a
  maintainer call", options, a recommendation) and leave the thread open. Richard raises it on
  Slack himself. Editing a comment does not undo a mention that was already posted.
- **No Claude attribution.** Commits are authored by Richard alone, with no `Co-Authored-By: Claude`
  and no `Claude-Session:` trailers. Our global session convention adds them by default, so
  strip them before any commit.
- **The "AI generated code" checkbox** in the PR template is ticked by Richard in the UI, never
  by you.
- **Keep internal planning out of public text.** No research-note numbering, agenda points,
  or company, product or customer names in commits, PRs, issues or replies. Describe the
  change on its own terms. "Our production store" is fine; naming whose store it is, is not.
- **Argue for the library, not for our app.** Use production as a test bed, but take upstream
  only defects any user of the public API would hit, with a library-level repro. A constraint
  that comes from how our app is built (windowed history loads, an append-only store, custom
  AG-UI parsing) is a migration task on our side, not an upstream ask.
- **Keep it short and plain.** Long AI-generated issue and comment text gets ignored. Aim for
  Richard's own voice, a few paragraphs at most, and add the disclosure line he uses
  (`<sub>Investigated with Claude Code.</sub>`) where it fits.
- **Never use em dashes** in anything you write: code, comments, docs, commits, PR or issue
  text. Upstream's own files use them; don't copy that.
- **Enforced by a hook.** `.claude/hooks/public_text_guard.py` (wired in this file's
  frontmatter) denies any `git commit` or `gh` issue/PR/comment/review call whose text, inline
  or in a body file, carries a Claude trailer, an em dash, a blocked name or an `@` mention
  outside backticks. When it denies, fix the text. Don't work around the hook.
- **Link every number** in your report to Richard: `[#1234](https://github.com/pydantic/pydantic-ai/issues/1234)`,
  never a bare `#1234`.
- **Don't apply review-trigger labels** (`douwebot`, `pydanty:*`) unless Richard asks. Follow
  the push skill for everything else, and quote the actual error if an attempt fails.

## Git layout on this Mac

| Remote | URL | Use |
| --- | --- | --- |
| `origin` | `rscholz98/pydantic-ai` (the fork) | the only push target |
| `upstream` | `pydantic/pydantic-ai` | fetch only, **never push** |

- Keep `main` in the main checkout tracking `origin/main`. Don't commit on it.
- One worktree per topic, as a sibling directory:
  `git worktree add ../pydantic-ai-<issue> -b <branch> upstream/main`. The branch-context files
  live inside that worktree.
- PRs go from an `origin` branch to `pydantic:main`. Once review threads exist a PR is
  append-only: push plain commits, merge `upstream/main` on conflicts, never force-push.
- **Clean up when a PR merges or closes:** `git worktree remove ../pydantic-ai-<issue>`, then
  `git branch -D <branch>`. Commits that were never pushed get bundled first
  (`git bundle create ~/Repos/pydantic-ai-archive/<date>/<name>.bundle <branch> --not --remotes`).
  Review checkouts (`pr-NNNN`) and agent worktrees under `.claude/worktrees/` are throwaway:
  remove them when the task ends.
- `uv`, `make`, `gh` (authenticated as `rscholz98`) and the uv-managed `.venv` all work.
  Pre-commit runs lint and format on commit. Never report a gate as green unless you ran it.
  Say which gates ran.

## Where state and history live

- **What is open, waiting or needs Richard:** the `pydantic-ai-status` skill
  (`python3 ~/.claude/skills/pydantic-ai-status/scripts/status.py --all --no-touch`). Use it
  instead of keeping a status table here.
- **Per-topic context:** the memory notes in
  `~/.claude/projects/-Users-rscholz-Repos-pydantic-ai/memory/` (`MEMORY.md` is the index; one
  `project` note per topic, naming its `#NNNN` items and branches, plus Richard's `feedback`
  rules). Read the note for your topic before acting. When a topic moves (PR opened, merged,
  maintainer reply), update its note, and when all its items are closed, delete it. The status
  script reads these notes. The branch-context files inside the worktree hold the per-branch
  detail.
- **Private downstream context** (Richard's product, its private research notes, the plan of
  features waiting on upstream): the memory note `downstream-app.md`. Read it when a task
  touches what production needs; never cite any of it publicly.
- **Archived unpushed branches:** `~/Repos/pydantic-ai-archive/`. The 2026-10-28 bundle holds
  the `ConversationStore` analysis prototypes (`analysis/*`, behind
  [#9786](https://github.com/pydantic/pydantic-ai/issues/9786) and
  [#11528](https://github.com/pydantic/pydantic-ai/pull/11528)) and the
  [#9991](https://github.com/pydantic/pydantic-ai/issues/9991) spike. Restore one with
  `git fetch <bundle> <branch>:<branch>`.
