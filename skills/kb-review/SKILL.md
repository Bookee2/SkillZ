---
name: kb-review
description: Review open PRs against their linked Linear issues and required GitHub checks, then post a three-group verdict with loop labels. Use when asked to run the loop's reviewer or review its PR queue. Designed for /loop; never merges or pushes code.
---

# Loop reviewer

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

One pass = one PR reviewed. Under `/loop`, each iteration runs this skill once.

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

## 1. Find a PR needing review

```bash
gh pr list --state open --json number,title,labels,isDraft,headRefOid,updatedAt,url
```

Skip drafts. For each PR, find the latest comment whose first line is
`Loop review of COMMIT_SHA`.

Accept **either** marker when reading an existing verdict — `Loop review of
COMMIT_SHA` or the legacy `Finn-loop review of COMMIT_SHA` — so a verdict posted
before the rename is still found. Always **post** the new form.

Skip a PR when that recorded SHA equals its current `headRefOid` and it already
has `loop-approved`, `loop-changes-requested`, or `needs-human-review`. Review
it again when new commits landed after the recorded SHA. If nothing needs
review, say so and end the pass.

## 2. Read the contract and code

- Parse the linked issue identifier from `Closes <KEY>-NNN` in the PR body and
  fetch the full Linear issue, including comments and relations. No linked
  issue is a must-fix finding. Confirm the issue sits on the resolved team —
  identifiers are unique workspace-wide, so an issue on another team means this
  PR belongs to another product's repo and the pass is in the wrong checkout.
  Stop there rather than reviewing it. A *prefix* that is not the resolved key
  is not by itself a mismatch: per the resolver's identifier hygiene, try the
  same number under the resolved key first, since a rekeyed team or a moved
  issue leaves stale identifiers in older PR bodies.
- Read the full diff and every changed file in context.
- Review only against the linked issue: acceptance-criteria gaps, defects,
  broken data flow, unnecessary scope expansion, security problems, missing
  loading/error states, and code future agents will struggle to modify.
- Do not suggest unrelated improvements unless they are severe.

Every must-fix code finding starts with one of:

- `[AC-N]` — the PR does not satisfy that acceptance criterion
- `[DEFECT]` — the implementation is broken while staying inside scope
- `[SECURITY]` — a severe security issue blocks shipping
- `[CI]` — a required GitHub check failed

Non-goals are binding. If fixing a finding would require behavior excluded by
an `NG-N`, do not prescribe code. Record
`[SCOPE-CONFLICT AC-N ↔ NG-N]` with the exact contradiction and mark the PR for
human escalation.

## 3. Check merge evidence

Inspect the current PR head, mergeability, and checks:

```bash
gh pr view NUMBER --json headRefOid,mergeable,mergeStateStatus
gh pr checks NUMBER --json bucket,name,state,link
```

- If any check is still pending, or mergeability is still unknown, report that
  the PR is waiting and end without posting a verdict or changing labels. A
  later loop pass will retry it.
- Failed checks are `[CI]` must-fix findings.
- A merge conflict is a `[DEFECT]` must-fix finding.
- A check does **not** have to be marked required in branch protection to count
  as evidence. A workflow that ran against the reviewed head and passed is the
  evidence; branch protection is a repository policy, not a fact about whether
  this commit was tested. Some repositories deliberately have none — this one
  deploys `main` on push, so a required check would gate the deploy path and be
  bypassed by an admin anyway.
- If **no** checks ran against this head at all, mark the PR for human
  escalation; do not apply `loop-approved`. The loop does not treat absent CI
  as green — an untested commit is untested however the repository is
  configured.

Review the exact `headRefOid` used for this evidence. Re-fetch it immediately
before posting. If it changed, discard the review and start again on a future
pass.

## 4. Post one verdict

Post one comment in this structure:

```md
Loop review of COMMIT_SHA

CI: checks passed | failed | none ran
Mergeability: clean | conflicting

## Review

Summary: one or two plain-language sentences on what this PR does.

## 1. Must fix before merge

None.

## 2. Should fix soon

None.

## 3. Safe to merge

Yes — automated review evidence is complete. A human still makes the merge decision.
```

Then set labels based on the verdict, checking existing labels before removing
them so an absent label does not fail the command:

- No must-fix and no new escalation: add `loop-approved`; remove
  `loop-changes-requested`. Preserve a pre-existing `needs-human-review` label
  because it may represent a separate high-risk human gate.
- Must-fix present: add `loop-changes-requested`; remove `loop-approved`.
- Scope conflict, or no checks ran at all: add `needs-human-review`; remove both
  `loop-approved` and `loop-changes-requested`; set "Safe to merge" to
  `No — human decision required.`

The escalation path deliberately leaves the automated repair queue. A human
must resolve the reason, change the issue or repository configuration as
needed, and remove `needs-human-review` before the reviewer reviews that unchanged
commit again.

### Writing up a resolved escalation

When a human has answered an escalation and you are posting the verdict that
records it, say so unambiguously, and do not file the remaining work under a
heading that reads like a precondition. "Still to fix before merge" placed
directly under a decision reads as *the decision is conditional on these*, and
a builder acting on that will send the question back to the human who has
already answered it.

Say plainly that the escalation is resolved and the answer stands, then list
what is left as ordinary must-fix items under their own heading. If the
decision is not yet written into the issue, say that too and name it as the
fix — the issue is the record, and a decision living only in a PR comment is
one the next agent will not find.

Before escalating anything, check the issue for a Decision section and read the
PR's own history: a question the issue already answers is not an open question,
and re-raising it costs a human round trip for nothing.

## 5. Hard limits

- Never merge or enable auto-merge.
- Never push commits to the PR branch.
- Never approve or request changes through a formal GitHub review. Use one
  comment plus labels because the loop may run on the PR author's token and
  GitHub rejects self-reviews.
- `loop-approved` is evidence for a human, not merge authorization.
