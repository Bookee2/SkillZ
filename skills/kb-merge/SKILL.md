---
name: kb-merge
description: Merge every review-approved PR to main in dependency order and log each merge in Linear. Use when asked to run the loop's merger or drain the approved PR queue. Designed for /loop; never reviews code, and never halts the loops — Kris stops them himself.
---

# Loop merger

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

One pass = merge everything that is genuinely ready, report the rest, and end.
Under `/loop 15m`, each iteration runs this skill once.

**This skill never halts the loops.** It does not write `.claude/loop.stop`, and
it does not tell peer sessions to stop. Anything it cannot merge — an
escalation, a failing check, a conflict — is skipped, reported, and left for the
next pass. Kris starts and stops the loops himself.

**Merging deploys to production.** Assume every push to the default branch
ships the target's live site; when `.claude/linear.json` names a `site`, say
which one before the first merge of the pass. Kris has explicitly
authorised merging without his review until human testing begins, but that
authorisation is exactly as wide as what is written here: a PR that carries
review evidence which is still valid. It is not authorisation to merge past a
failing check, past an escalation, or past a red `main`.

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
   { "team": "TrailGoat", "project": "optional", "site": "https://trailgoat.run",
     "changelog": "static/changelog.html" }
   ```

   `team` is required — a Linear team name or key. Resolve it through the Linear
   connector to get the team's real key. `project`, when set, is the default
   project for issues this repo files. `site`, when set, is what a merge to the
   default branch deploys. `changelog`, when set, is the repo-relative path to
   the user-facing changelog that step 4's gate enforces.
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

## 0. Preflight — the shared working tree

All loop agents run in **one** checkout. A builder is very likely to have
a feature branch checked out with uncommitted work in it right now.

- **Never** run `git checkout`, `git switch`, `git pull`, `git rebase`,
  `git reset`, `git stash`, or `git merge` in the primary working tree.
  `git fetch`, `git log`, `git show` and `git worktree list` are safe.
- Do all merging through the GitHub API (`gh pr merge`, `gh api`), which is
  server-side and touches nothing local.
- The only local git writes allowed are inside a throwaway worktree created
  under the scratchpad directory (step 6), which never changes the primary
  checkout's HEAD or index.
- Before touching any branch, run `git worktree list`. If the branch is checked
  out anywhere, leave it entirely alone and report it — a builder is on it.

If `.claude/loop.stop` exists, Kris has halted the loops by hand. Report its
contents and end the pass without merging. This skill never creates that file —
only a human does, and only a human removes it to resume.

## 1. Survey the board

Take both readings before acting on either.

```bash
gh pr list --state open --json number,title,labels,isDraft,headRefName,headRefOid,mergeable,mergeStateStatus,body,url
```

From the Linear connector, list every issue **on the resolved team** that is
not `Done`, `Canceled` or `Duplicate`, with labels, status and blocking
relations. Filter on the team explicitly — an unfiltered workspace query mixes
another product's issues into the dependency order.

Classify every open PR:

| Bucket | Test |
|---|---|
| **escalated** | labeled `needs-human-review` |
| **ready** | labeled `loop-approved`, not escalated, not draft |
| **in repair** | labeled `loop-changes-requested` |
| **awaiting review** | no loop label yet, or new commits since the recorded review |

## 2. Escalations are skipped, not merged — the pass continues

A PR labeled `needs-human-review`, and any PR whose linked Linear issue carries
the `blocked` label, is **skipped**. Only Kris can clear those, so never merge
one and never overturn the reviewer's call.

Skipping is all that happens. Keep going and merge everything else that is
ready, then report each skipped item with its PR/issue URL and the one question
or decision that unblocks it.

What stops later work from jumping a stuck earlier issue is step 3's chain rule,
not a full stop: a PR whose linked issue is still `blockedBy` an issue that is
not `Done` is never merged. Independent work is free to land meanwhile.

## 3. Order the merge queue

Sort **ready** PRs by their linked issue's blocker relations — an issue that is
`blockedBy` another merges after it. Break ties by oldest PR first.

Never merge a PR whose linked issue is still blocked by an issue that is not yet
`Done`. The issue chain is the contract; GitHub's mergeability is not a
substitute for it.

## 4. Re-verify the evidence, per PR

Accept **either** marker when reading an existing verdict — `Loop review of
COMMIT_SHA` or the legacy `Finn-loop review of COMMIT_SHA` — so a verdict posted
before the rename is still found. Always **post** the new form.

`loop-approved` is a verdict about **one commit**. Confirm it still describes
reality before merging:

```bash
gh pr view NUMBER --json headRefOid,mergeable,mergeStateStatus,body,labels
gh pr checks NUMBER --json bucket,name,state,link
```

Merge only when all of these hold:

- The `Loop review of COMMIT_SHA` comment's SHA equals the current
  `headRefOid`. If commits landed after the review, this PR is **awaiting
  review** — skip it, it is not approved.
- Checks ran against this head and passed. Pending → skip, retry next pass.
  Failed → remove `loop-approved`, add `loop-changes-requested`, comment why,
  and skip.
- `mergeable` is `MERGEABLE`. `CONFLICTING` → go to step 6. `UNKNOWN` → GitHub
  is still computing; skip and retry next pass.
- The body contains `Closes <KEY>-NNN` and that issue exists on the resolved
  team (following the resolver's stale-prefix rule before calling it a miss).
- The changelog gate below passes.

This is evidence-checking, not review. Do not read the diff for defects — that
is `kb-review`'s job and it already ran.

### The changelog gate

**Standing rule from Kris (2026-08-27): a merge keeps the user-facing changelog
current, in the same change.** TrailGoat's public log went silent for a week
while roughly twenty PRs shipped, on a page whose own hero promises the product
ships nearly every day — days before a launch push. Nothing caught it, because
nothing was watching.

Skip this gate entirely when the resolved `.claude/linear.json` has no
`changelog` key. Otherwise, for each PR about to merge:

```bash
gh pr diff NUMBER --name-only        # does it touch the declared path?
```

Merge only when **one** of these holds:

1. **The diff touches the declared changelog file.** Nothing further to check —
   the entry's wording is `kb-review`'s business, not this skill's.
2. **The body carries an explicit `Changelog:` declaration** on its own line,
   in one of exactly two forms:

   | Form | Means | Example |
   |---|---|---|
   | `Changelog: none — <reason>` | Genuinely not user-visible | `Changelog: none — CI workflow only, no runtime change` |
   | `Changelog: deferred — <gate>` | User-visible, but not live yet | `Changelog: deferred — ships dark behind BILLING_ENFORCED` |

Neither present → **skip the PR**: remove `loop-approved`, add
`loop-changes-requested`, and comment naming the declared path, the two
declaration forms verbatim, and the three curation rules below. Then continue
the pass. This is the one case where this skill bounces a PR over something
other than code, and it is deliberate: the entry belongs in the feature PR, not
in a cleanup sweep a week later that has to reconstruct a week from `git log`.

Three rules govern what an entry should say, quoted into the bounce comment so
the builder does not have to guess:

- **Curate, don't transcribe.** Only user-visible work earns an entry. CI,
  refactors, test-harness pins, internal 500-fixes and dependency bumps take
  `Changelog: none`. Several PRs in a chain may collapse into one entry.
- **Nothing that isn't live.** Work behind a feature flag takes
  `Changelog: deferred` and gets its entry when the flag flips — a public log
  that lists unreachable features is worse than one that lags.
- **Match the file's existing voice and format.** Read the entries already
  there and write the next one like them. Never invent a new format in a file
  that has one.

A `deferred` declaration is a debt, not a dismissal, and the thing that makes
it real is step 7 reporting it every pass until someone clears it.

## 5. Merge, then log it

Per PR, in queue order:

1. Comment on the Linear issue **before** merging — the working agreement is
   that Linear records the work before `main` does. State the PR number, the
   head SHA, that CI passed on it, and anything the review flagged as
   "should fix soon" so it is not lost.
2. Squash-merge with a message whose subject is the PR title and whose body
   carries `Closes <KEY>-NNN` plus the PR URL:

   ```bash
   gh pr merge NUMBER --squash --delete-branch --subject "..." --body "..."
   ```

   `--delete-branch` matters: this repo does not delete on merge, and stale
   branches make the next survey ambiguous.
3. Move the Linear issue to `Done`. Do this explicitly even if the GitHub
   integration also does it; an explicit write is idempotent and a missing
   integration is silent.
4. **Wait for `main` to go green.** The push triggers CI on `main`. Two PRs can
   each be green alone and broken together, and this repo deploys the result.

   ```bash
   gh run list --branch main --limit 1 --json databaseId,status,conclusion,url
   ```

   If it fails: stop merging immediately and do not merge anything else this
   pass — a red `main` is a live production problem and outranks draining the
   queue. Report the failing run URL prominently so Kris sees it. Do not halt
   the loops; end the pass and let the next one re-check.
5. Re-fetch the next PR's mergeability before merging it — the merge you just
   made usually invalidates it.

## 6. CHANGELOG conflicts — resolve, don't bounce

Every issue in a chain appends to `CHANGELOG.md` under the same date heading, so
merging one PR reliably conflicts the next. That conflict is bookkeeping, not a
code disagreement, so resolve it here rather than waking the build loop.

Only when the conflict is confined to `CHANGELOG.md`:

Create the worktree under **your session's scratchpad directory** (the absolute
path given in your system prompt), never anywhere inside the repository — a
worktree inside the repo would show up in the other agents' `git status`.

```bash
SCRATCH="<your-scratchpad>/merge-<KEY>-NNN"    # scratchpad, never the repo
git fetch origin
git worktree add --detach "$SCRATCH" "origin/BRANCH"
git -C "$SCRATCH" merge origin/main
git -C "$SCRATCH" diff --name-only --diff-filter=U
```

- If that last command lists **anything other than `CHANGELOG.md`**, abort:
  `git -C "$SCRATCH" merge --abort`, remove the worktree, then label the PR
  `loop-changes-requested` with a comment naming the conflicting files. A code
  conflict is a builder's decision.
- Otherwise resolve by **keeping both sides in full**, under one date heading:
  `main`'s entries first (they landed first), then the branch's, no dedup beyond
  removing an identical repeated line. Never rewrite somebody's entry prose.

```bash
git -C "$SCRATCH" add CHANGELOG.md
git -C "$SCRATCH" commit -m "Merge main into <KEY>-NNN: keep both changelog entries

Refs <KEY>-NNN"
git -C "$SCRATCH" push origin HEAD:BRANCH
git worktree remove "$SCRATCH"
```

The push moves the head, so the PR's `loop-approved` no longer describes it. It
returns to **awaiting review** by design — `kb-review` re-reviews the new head
and a later merge pass picks it up. Resolve at most one conflicted PR per pass
and say plainly in the report that it now needs re-review; do not merge it on
this pass on the strength of the old verdict.

Always remove the worktree, including on every failure path. A leaked worktree
holds a lock that will confuse the next pass.

## 7. Close the pass

Always end the pass here, whether the board is full or completely drained.
Never write a stop file and never message peers to stop.

Report, in this order:

1. What merged, with PR numbers and issue ids.
2. What was skipped and why — escalations first, each with its PR/issue URL and
   the single decision that unblocks it, then failing checks, conflicts, and
   PRs still awaiting review.
3. Anything a review flagged as "should fix soon" on a PR merged this pass, so
   it survives outside the PR thread.
4. **Outstanding changelog debt.** Every `Changelog: deferred — <gate>` merged
   this pass, and every one still outstanding from earlier passes, each with its
   gate and issue id. Gather them with:

   ```bash
   gh pr list --state merged --limit 100 --json number,title,body,url \
     --jq '.[] | select(.body | test("(?im)^[[:space:]]*Changelog:[[:space:]]*deferred")) | "#\(.number) \(.title) \(.url)"'
   ```

   Filter on the body client-side as shown. Do **not** reach for
   `gh pr list --search "Changelog: deferred"`: GitHub's search is full-text and
   fuzzy, and returns PRs that merely mention a changelog somewhere — verified
   against this repo, where it matched a PR carrying no declaration at all. A
   fuzzy match here reports debts that do not exist and buries the ones that do.

   Report this list every pass, even when nothing merged. It is the only thing
   standing between "we'll add it when the flag flips" and a second silent week —
   the deferral is a debt, and a debt nobody reads is a debt nobody pays. When
   the gate named in a deferral has since flipped, say so plainly: that entry is
   now overdue and its feature is live and undocumented.
5. Whether `main` is green after the merges.

If the board is drained — nothing merged, nothing skipped, nothing left to
review — say exactly that in one line. A quiet pass is a normal outcome, not a
reason to stop anything.

## 8. Hard limits

- Never merge a PR labeled `needs-human-review`, or one whose linked issue is
  `blocked`.
- Never merge with a failing or absent check, and never with `--admin`.
- Never write to the primary working tree, and never touch a branch that
  `git worktree list` shows as checked out.
- Never edit source files. The one file this skill may write is `CHANGELOG.md`
  inside a scratchpad worktree, to keep both sides of a conflict. It never
  writes the declared `changelog` file itself — a merger that authors the entry
  it is checking for is not a gate, and the entry belongs to whoever wrote the
  feature.
- Never merge a PR that fails the changelog gate, and never satisfy that gate on
  a PR's behalf by adding a `Changelog:` line to its body. Bounce it and let the
  builder decide which of the two declarations is true.
- Never re-review code or overturn a `kb-review` verdict. If a verdict looks
  wrong, skip the PR and report it instead of merging.
- Never force-push, and never rewrite an existing commit.
- Never halt the loops: no `.claude/loop.stop`, no stop messages to peers. Skip
  what cannot be merged, report it, and end the pass.
