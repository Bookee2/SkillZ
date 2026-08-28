---
name: kb-spec
description: Interview the user about a raw idea until confident, then file a build-ready issue in Linear. Use when asked to run the loop's spec interview, draft a queue-ready issue, or plan a feature. Interactive — requires the user present; never run unattended.
---

# Spec interview

> **Scope:** one target — the checkout the working directory resolves to, its
> GitHub repo, and its Linear team. Resolve it before anything else, following
> `~/.claude/kb-loop/resolve-target.md`. One pass serves exactly one target.
> Never run a pass across two, and never against a repo with no Linear binding.
>
> **Where these skills live.** The canonical copy of all four is user-wide at
> `~/.claude/skills/`, alongside the resolver they share at
> `~/.claude/kb-loop/resolve-target.md`. A repo may also carry a committed
> mirror under its own `.claude/skills/` so tablet and phone sessions — which
> see only what the repo carries — can run the loop. Edit the user-wide copy: a
> mirror is a published copy, never the source. Any repo can be a target; it
> names its Linear team in its own `.claude/linear.json`, so nothing here is
> specific to one product.

Turns a raw idea into a Linear issue so complete that a build agent needs
nothing beyond the issue. Works like plan mode: research the codebase,
interview the user in rounds until confident, draft, confirm, file. The user
is the product brain; you are the codebase brain. Never guess product
decisions.

## Resolve the target — before anything else

The full rule lives at `~/.claude/kb-loop/resolve-target.md`, or at
`<repo>/.claude/kb-loop/resolve-target.md` where a repo mirrors it. Read
whichever exists; it takes precedence. This summary is authoritative only when
neither does.

1. **Checkout** — `git rev-parse --show-toplevel` from the working directory.
   When the cwd is not itself a repo, search **three** levels down and accept
   exactly one repo *that carries `.claude/linear.json`* — unbound repos never
   count. Zero, or two or more bound ones, means stop and report. Record
   `origin`'s `owner/repo` slug.
2. **Team** — read `<repo root>/.claude/linear.json`:

   ```json
   { "team": "TrailGoat", "project": "optional", "site": "https://trailgoat.run" }
   ```

   `team` is required — a Linear team name or key. Resolve it through the Linear
   connector to get the team's real key. `project`, when set, is the default
   project for issues this repo files. `site`, when set, is what a merge to the
   default branch deploys.
3. **No binding** — never guess a team and never search Linear for something
   plausible. `kb-spec`, with the user present, may propose the closest team by
   repo slug, confirm it, and write the file. The three unattended skills report
   the repo slug and the missing file, and end the pass.

Then the whole pass is bound: `git` and `gh` against that checkout only, every
Linear read filtered to that team, every Linear write targeting it. An issue on
another team is a hard stop — report it and end the pass. Never act across the
boundary, and never renumber or re-file an issue to make it fit.

Say the resolved team, repo slug and checkout path in the first line of the pass
output, so a wrong answer is visible before anything is written.

`<KEY>-NNN` throughout this skill means the resolved team's real key as Linear
returns it — never a literal copied from here. When an older PR body or comment
carries a different prefix (a rekeyed team, or an issue moved between teams),
try the same *number* under the resolved key before calling it a mismatch, and
say in the output that you followed a stale identifier.

## 1. Research before asking

Read the relevant code first. Find which files are involved, what patterns
already exist, and what constraints apply. Never ask the user something the
codebase can answer.

## 2. Interview in rounds

Ask 1-4 questions per round, each with concrete options and your recommended
option first. Ask only genuine product decisions:

- Behavior forks: who sees it, what exactly happens, where does it live
- Scope boundaries: what is explicitly out of this issue
- Edge cases that change acceptance criteria: empty states, permissions,
  failure handling
- Data implications: existing records, migrations

After each round, fold the answers in and apply the confidence test:

> Could two different engineers read this spec and ship the same observable
> behavior?

If any fork remains, ask another round. There is NO cap on rounds: a small
fix might need two questions; a big feature legitimately needs 10-20+. Never
stop early because it feels like a lot of questions. Once the test passes,
stop — no filler questions.

## 3. Draft the issue

Use exactly this shape:

```md
## Problem

What user or business problem does this solve? One or two sentences.

## Acceptance Criteria

- [ ] AC-1 — Observable, testable outcome one
- [ ] AC-2 — Observable, testable outcome two

## Non-goals

- NG-1 — What must NOT change in this task
- NG-2 — What is explicitly excluded or saved for later

## Relevant files

- path/to/file.ts — why it matters

## Test expectations

- What should be tested, manually or automatically

## How to verify

1. Numbered manual steps anyone can follow to confirm the work: where to
   go, what to do, exactly what should happen. Cover every AC.
```

Rules for the draft:

- Every acceptance criterion is an observable outcome with a stable `AC-N`
  id. Every non-goal has a stable `NG-N` id. These ids are the contract the
  build and review skills enforce.
- No acceptance criterion may require a non-goal. If one does, resolve it
  with the user before filing.
- Size the issue to one day of agent work or less. Bigger work becomes a
  chain of small issues, ordered so each is buildable using only merged
  code from the ones before it.

## 4. Confirm and file

Show the full draft in chat and get the user's go-ahead. Then create the
issue on the resolved team (via the Linear connector) with the draft as the
body. When `.claude/linear.json` names a `project`, set that project on the
issue too — in a workspace where the team is subdivided by project, an issue
filed without one is invisible to a project-filtered queue. Report the exact
issue identifier and URL returned by Linear; later skills use that identifier
rather than guessing it.

## Hard rule

Never apply the `agent-ready` label. The user applies it in Linear after a
final read — that label is the approval gate between "idea" and "an agent
builds it".
