---
name: kb-build
description: Claim the next safe agent-ready issue from Linear, implement it, and open a PR. Use when asked to run the loop's builder, work the approved queue, or fix the loop review feedback. Designed for /loop; one pass does one unit of work.
---

# Loop builder

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

One pass = one unit of work: fix review feedback on one existing PR, or build
one issue end to end. Under `/loop`, each iteration runs this skill once.

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

## 0. Stop check

If `.claude/loop.stop` exists, the merge loop has halted the loop —
either the queue is drained or something needs Kris. Report the file's contents
and end the pass immediately. Do not claim, build, review, or label anything.
A human removes that file to resume.

## 1. Preflight

Before changing Linear, GitHub, branches, or files:

- Confirm this is the intended GitHub repository and `origin` is reachable.
- Detect the repository's default branch with
  `gh repo view --json defaultBranchRef --jq .defaultBranchRef.name`; never
  assume it is `main`.
- Require a clean working tree (`git status --porcelain` must be empty). If it
  is dirty, report the paths and end the pass. Never stash, reset, overwrite,
  or commit unrelated work.

## 2. Review feedback first

List open PRs labeled `loop-changes-requested`, including their labels:

```bash
gh pr list --state open --label loop-changes-requested --json number,title,headRefName,headRefOid,labels,updatedAt,url
```

Skip every PR carrying `needs-human-review`; it has left the automated repair
queue until a human resolves the escalation.

If any PR remains, choose the least recently updated one. Read its linked
Linear issue and latest `Loop review of COMMIT_SHA` verdict.
Accept **either** marker when reading an existing verdict — `Loop review of
COMMIT_SHA` or the legacy `Finn-loop review of COMMIT_SHA` — so a verdict posted
before the rename is still found. Always **post** the new form. Check out its
branch, fix only the "Must fix before merge" items, run the relevant checks,
push, remove `loop-changes-requested`, and comment with what changed. End this
pass.

If a proposed fix would cross an issue non-goal or requires a product decision,
do not implement it. Comment the exact conflict, add `needs-human-review`,
remove `loop-changes-requested`, and end the pass. This prevents the next loop
iteration from retrying a decision only a human can make.

## 3. Pick

Using the Linear connector, list issues on the resolved team that meet every
condition:

- **on the resolved team** — filter on it explicitly; an unfiltered workspace
  query returns another product's queue, and this step is where that mistake
  gets built. When the binding names a `project`, filter on that too
- **still open** — its status type is `backlog`, `unstarted` or `started`.
  Never `completed`, `canceled` or `duplicate`: a closed issue can keep the
  `agent-ready` label forever, and building one means shipping work that was
  already done, abandoned, or superseded
- labeled `agent-ready`
- unassigned
- not labeled `blocked`
- no unresolved blocker relation

Sort by priority, then oldest first. If the queue is empty, say so and end the
pass. Do not invent work and do not pick a blocked issue.

## 4. Claim (the cooperative lock)

Assign yourself and move the issue to the team's started workflow state
(prefer `In Progress` when available). Claim before reading deeply or writing
code. Re-fetch the issue immediately after the update; if it is blocked,
assigned to somebody else, or no longer `agent-ready`, do not work it and
return to step 3.

The assignee prevents different people from taking the same issue. It is not
an atomic lock between simultaneous sessions authenticated as the same Linear
user, so only one builder loop may run per team — one per product, which is
what the team boundary now buys.

## 5. Read

Fetch the full issue including comments and relations. Implement only its
acceptance criteria. Non-goals are binding. Compare every `AC-N` against every
`NG-N` before editing. No unrelated changes and no opportunistic refactors.

If an acceptance criterion is ambiguous, conflicts with a non-goal, or depends
on an unresolved blocker, go to step 9. Never guess.

## 6. Build

- Fetch the latest default branch from `origin` and create or resume a branch
  named `<KEY>-NNN-short-slug`, using the issue's real identifier as Linear
  returned it.
- Implement the acceptance criteria using the repository's existing style,
  architecture, and naming.
- Add or update tests when the change affects logic, data flow, permissions,
  integrations, or user-visible behavior.
- Preserve behavior outside the issue contract.

## 6b. The changelog entry

The repo's binding may name a user-facing changelog — a `changelog` key in
`.claude/linear.json`, holding a repo-relative path (`static/changelog.html`,
`CHANGELOG.md`, whatever that product publishes). **When the key is absent,
skip this step entirely.** When it is present, `kb-merge` will not merge this
PR until one of the two outcomes below is true, so settle it here rather than
taking a bounce.

Decide which of three this change is:

| The change is | Do this |
|---|---|
| User-visible and live once merged | Write the entry into the declared file, in the same commit as the work |
| Not user-visible | Put `Changelog: none — <reason>` on its own line in the PR body |
| User-visible but behind a flag | Put `Changelog: deferred — <gate>` on its own line in the PR body |

"Not user-visible" means a person using the product could not tell the
difference: CI, refactors, test-harness changes, dependency bumps, internal
error-handling that no reachable path surfaces. Not a synonym for "small" — a
one-word button label is user-visible; a thousand-line refactor is not.

`deferred` is for work that is real but not yet reachable — anything behind a
feature flag or an unflipped environment switch. Name the gate exactly
(`Changelog: deferred — ships dark behind BILLING_ENFORCED`), because
`kb-merge` re-reports every outstanding deferral each pass and flags it as
overdue once its gate flips. A public log listing features nobody can reach is
worse than one that lags.

Writing the entry:

- **Read the file first and match what is already there** — its format, its
  voice, its ordering, its date convention. An HTML log has a markup shape to
  copy; a Markdown one has a heading convention. Never invent a new format in a
  file that has one, and never restructure the file to suit your entry.
- **Curate.** One entry per user-visible outcome, not one per commit. Where a
  chain of issues adds up to a single thing a person would notice, the last one
  writes the entry and the rest declare `Changelog: none — covered by
  <KEY>-NNN`.
- **Write what changed for the person using it**, not what changed in the
  code. The issue title is usually the wrong sentence: it names the task, and
  the entry names the result.
- Respect the product's own writing rules where the repo states them (a
  CLAUDE.md, a brand doc, the file's own header comment).

Append the entry to the same branch and commit as the work. It is part of the
change, not a follow-up.

## 7. Verify

Run the project's relevant lint, typecheck, build, and narrowest useful tests.
All checks attributable to this change must pass before opening a PR. If a
broad check has a pre-existing unrelated failure, run the relevant targeted
check, preserve the evidence, and disclose both results in the PR.

Review `git diff` and `git status` before shipping. Stop if the diff contains
unrelated work or generated secrets.

## 8. Ship

Push and open a PR with `gh pr create`. Its description must include:

- What changed and why
- `Closes <KEY>-NNN`, using the real Linear issue identifier
- A scope ledger: one evidence line per `AC-N`, one preservation line per
  `NG-N`, and `Other behavior changes: None`
- Numbered manual test steps matching what was actually built
- Automated checks run and their results
- Risk: Low / Medium / High
- The changelog outcome from step 6b, when the repo declares a `changelog`:
  either the entry is in the diff, or the body carries exactly one
  `Changelog: none — <reason>` or `Changelog: deferred — <gate>` line

If `Other behavior changes: None` is not true, stop and get the Linear issue
amended before opening the PR.

Comment the PR URL on the Linear issue. Move it to the team's review state if
one exists; otherwise leave it in the started state for the Linear-GitHub
integration to manage. Never merge and never enable auto-merge. End the pass.

## 9. Blocked

Comment one specific question a human can answer asynchronously, apply the
`blocked` label, and unassign yourself. Leave `agent-ready` in place: the pick
query explicitly excludes `blocked`, so the issue safely reappears only after
a human answers and removes that label.

Never use "this is unclear" as the question. State the exact decision, the
available options, and which acceptance criterion it affects. End the pass so
the next iteration can pick different work.
