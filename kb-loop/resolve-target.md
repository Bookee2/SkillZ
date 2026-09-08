# Resolving the loop target

Every `kb-*` pass serves exactly **one target**: one local checkout, one GitHub
repo, and one Linear team. Resolve it before reading issues, touching git, or
writing anything. This file is the single source of truth for that resolution —
the four skills point here rather than each carrying their own copy.

There is no hardcoded project table. Any repo works as long as it declares its
Linear team.

## 1. Find the checkout

Stop at the first step that answers:

1. **The working directory's own repo** — `git rev-parse --show-toplevel`.
2. **Exactly one *bound* repo beneath the working directory** — when the cwd is
   not itself a repo, search **three** levels down (a checkout can easily sit
   three deep under `~`, and a shallower scan finds a neighbouring repo instead
   and answers confidently with the wrong one). Count only repo roots that carry
   `.claude/linear.json`; unbound repos — a scratch clone, a static site sitting
   next to the product — never count. Exactly one bound repo is the answer;
   zero, or two or more, means fall through. Counting bindings rather than repos
   is the whole point: `~/Desktop/TrailGoat` holds both `running-backend`
   and `personal_website`, and only the first is bound.
3. **Stop.** Report that no single checkout resolves and end the pass. Never
   guess, and never carry the target over from a previous pass.

Then read `git remote get-url origin` and record the `owner/repo` slug.

## 2. Read the binding

The repo declares its own Linear team in `<repo root>/.claude/linear.json`:

```json
{
  "team": "TrailGoat",
  "project": "Race catalog",
  "site": "https://trailgoat.run",
  "changelog": "changelog/"
}
```

| key | required | meaning |
|---|---|---|
| `team` | yes | Linear team name or key. The pass is bound to this team. |
| `project` | no | Default Linear project for issues this repo files. Omit when the team has no projects — the team alone is the boundary. |
| `site` | no | What a merge to the default branch deploys. `kb-merge` names it before merging; absent means assume a merge may reach production. |
| `changelog` | no | Repo-relative path to the **user-facing** changelog a merge must keep current — a single file (`CHANGELOG.md`) or a directory of one-file-per-entry fragments (`changelog/`, TrailGoat's shape since TG-266; touching any file under it counts). When set, `kb-merge` will not merge a PR that neither touches it nor declares why it doesn't. Omit only when the repo publishes no changelog at all. |

Resolve the team through the Linear connector to get its real **key** (`TG`,
`PS`, …). That key — never a literal from this file or a skill — is what
`<KEY>-NNN` means everywhere below.

## 3. When the binding is missing

An unbound repo is not an invitation to search Linear for something plausible.

- **`kb-spec`** (interactive, user present) may onboard the repo: list the
  Linear teams, propose the closest match to the repo slug, and ask. Only after
  the user confirms, write `.claude/linear.json` with their answer and continue.
  If no team fits, say so — the user creates the team in Linear first; these
  skills never create one.
- **`kb-build`, `kb-review`, `kb-merge`** (unattended under `/loop`) must not
  ask and must not guess. Report the repo slug and the missing file, say that
  `/kb-spec` or a hand-written `.claude/linear.json` binds it, and end the pass.

## 4. Bind the whole pass

Once resolved:

- `git` and `gh` run against that checkout only, never another.
- Every Linear read is filtered to that team.
- Every Linear write targets that team (and the configured project, when set).
- An issue on another team is a hard stop: report it and end the pass. Never
  act across the boundary, and never renumber or re-file an issue to make it
  fit.

Say the resolved **team, repo slug and checkout path** in the first line of the
pass output, so a wrong answer is visible before anything is written.

## 5. Identifier hygiene

- Issue identifiers are `<KEY>-NNN` using the resolved team's key. Build branch
  names, `Closes` lines, and commit trailers from the identifier Linear
  actually returned — never from a pattern hardcoded in a skill.
- **Reading a stale prefix.** A team's key can change, and an issue moved
  between teams is renumbered. When a PR body or comment carries an identifier
  whose prefix is not the resolved team's key, try the same *number* under the
  resolved key before calling it a mismatch, and say in the pass output that
  you followed a stale identifier. Only a number that resolves to nothing, or
  to an issue on another team, is a genuine cross-boundary stop.
- Identifiers are unique workspace-wide, so an identifier that resolves to
  another team means this pass is in the wrong checkout. Stop rather than
  working it.
