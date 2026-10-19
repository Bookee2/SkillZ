# SkillZ

A growing collection of [Claude Code](https://claude.com/claude-code) skills, and
the workflow they add up to.

`/tg-render` turns one or more TrailGoat catalogue course names into locally
rendered 3D flyovers, with a resumable sequential batch runner that checks each
encode against the reference bitrate budget. It works in Claude Code
(`./install.sh`) and in Codex (`./install-codex.sh`, then `$tg-render`). It
sets up a fresh machine itself: it finds or clones the TrailGoat checkout,
the encoder venv and Blender, and refuses to run on a stale flythrough engine.
Its output stays local; it does not publish videos to TrailGoat. Source:
[`skills/tg-render`](skills/tg-render/SKILL.md).

`/kb-motion` is a motion-graphics studio for any product. Type
`/kb-motion <what kind of motion> for <which product>` and it researches the
product (design tokens, real data, the live site) and current best practice,
interviews you, confirms a plan, then builds a page of live HTML examples. It
carries a catalog of everything built so far (particle fields that morph into
words, profiles and maps; GPU and WebGPU particle sims; data-driven hero
readouts; scroll stories; contours from terrain tiles; ridgelines and sand
signatures; view transitions; GSAP; state-machine mascots), the lessons behind
them, vetted sources, and the working code in
[`skills/kb-motion/assets`](skills/kb-motion/assets/README.md). Install just this
one with `./install.sh kb-motion`.

`/kb-secbrain` feeds the second brain (the claude-obsidian vault at
`~/Documents/SecondBrain`). One pass collects the week's research and
development learning (Claude Code sessions, memory updates, merged PRs and
review verdicts, commits and research docs across `~/Desktop/Projects`, and
Linear if it's connected) into a dated note in the vault inbox. It then
ingests un-ingested inbox material into the wiki through claude-obsidian's
reviewed transactions, in a bounded tranche per run, and skips anything
already ingested by hash. It's built to run unattended from a weekly
scheduled task in the Claude desktop app. Install just this one with
`./install.sh kb-secbrain`.

`/kb-ytvideo` makes motion graphics for YouTube videos and for Shorts, Reels
and TikTok: word-timed B-roll cutaways and panels over OBS screen takes or
talking-head footage, 9:16 reframes, word-by-word social captions, and
standalone intros, chapter cards, lower thirds and end cards, rendered
frame-accurately with motion blur in a brand (TrailGoat Tokyo Night by
default). Run `scripts/setup.sh` once per machine (it lives in the skill).
Built on motion-broll by Bart (MIT, `LICENSE-upstream`). Install just this one
with `./install.sh kb-ytvideo`.

`/tg-ingest` runs one crawl-and-ingest pass for the TrailGoat race catalog:
the UltraSignup sweep (once a day), the GPX hunt, import, enrichment and audit,
then a digest. It writes to the production database and runs from the
TrailGoat checkout (it changes there when started elsewhere). Use it with
`/loop 3h /tg-ingest`. Install just this one with `./install.sh tg-ingest`.

`/kb-unreal` is an Unreal Engine motion studio built on everything already
proven on Kris's Mac. Type `/kb-unreal <the idea> [for <brand or client>]` and
it loads a capability map of every Unreal, Blender and video production so far
(the block swarm, the 150k-particle engine, the Motion Design stage, the
Cassini space set, the Electric Dreams canyon run, Cesium flyovers, scripted
Sequencer, out-of-process Movie Render Queue renders, sound design, delivery),
checks the machine (`scripts/preflight.sh`), researches the brief and the Epic
samples on disk, interviews you, confirms a treatment, then builds with 720p
drafts and a note-to-render loop until sign-off. It closes out every run by
improving itself: lessons, techniques, taste notes and a run log go back into
its `references/` here, and `scripts/selfupdate.sh` reinstalls it. Install
just this one with `./install.sh kb-unreal`.

The first four are **the loop** — a spec-to-merge pipeline that runs across
Linear and GitHub. One human decision gates it; the rest is agents doing one
small, verifiable unit of work per pass. `/kb-design` is a different animal: it
builds things that have to look right.

## The loop

```
  /kb-spec  ──▶  Linear issue  ──▶  [ you apply `agent-ready` ]  ──┐
                                                                  │
  ┌───────────────────────────────────────────────────────────────┘
  │
  ▼
  /kb-build  ──▶  PR  ──▶  /kb-review  ──▶  verdict + label  ──▶  /kb-merge  ──▶  main
                            ▲                                          │
                            └────────  changes requested  ◀────────────┘
```

| Skill | What one pass does | Runs |
|---|---|---|
| **`/kb-spec`** | Interviews you about a raw idea until two engineers would ship the same thing, then files a build-ready Linear issue. | Interactive — you must be present |
| **`/kb-build`** | Claims the next safe `agent-ready` issue, implements it, opens a PR. Or fixes review feedback on one existing PR. | Unattended, under `/loop` |
| **`/kb-review`** | Reviews one PR against its linked issue and its CI evidence, posts a three-group verdict, sets labels. | Unattended, under `/loop` |
| **`/kb-merge`** | Merges every PR whose approval still describes its current head, in dependency order, and logs each merge in Linear. | Unattended, under `/loop 15m` |

The three unattended skills are designed to run as three concurrent `/loop`
sessions against one checkout. They never write each other's files and never
touch a branch another agent has checked out.

### The one gate

`/kb-spec` never applies the `agent-ready` label. You do, in Linear, after a
final read. That label is the entire boundary between "an idea I typed" and "an
agent is going to build this" — which is why a skill is not allowed to cross it.

### What holds it together

- **Stable ids.** Every acceptance criterion is `AC-N` and every non-goal is
  `NG-N`. Those ids are the contract: `/kb-build` implements against them,
  `/kb-review` cites them in findings, and neither is allowed to satisfy an
  `AC-N` by violating an `NG-N`.
- **Approval is about one commit.** `loop-approved` records a SHA. If commits
  land after it, the PR is no longer approved and `/kb-merge` skips it. No
  verdict silently outlives the code it described.
- **Absent CI is not green.** A PR with no checks against its head escalates to
  a human rather than merging.
- **Escalations skip, they don't stop.** `needs-human-review` takes one PR out
  of the automated queue. Independent work keeps landing.

## Beyond the loop

### `/kb-design` — build it in the product's design language

Hand it an idea — a report, a dashboard, a one-page tool, a marketing sheet, a
new page for the site — and it returns finished HTML that is indistinguishable
from the product it belongs to. It researches the subject first, interviews you
on the decisions a design system cannot make (who opens this, what the one
primary action is, where the data comes from), then builds, renders and checks
its own work at desktop and phone widths.

**This one is product-specific, and the other four are not.** It carries
TrailGoat's design language: the Tokyo Night palette, the Red Hat type, the
neutral interaction ladder, the terminal topbar, the cards and chips and tables,
the Leaflet and Chart.js recipes. Installed as-is it builds TrailGoat things.

What is portable is the shape:

```
skills/kb-design/
  SKILL.md                     the four phases, and the rules a build may not break
  references/design-system.md  the full reference — every token, with the file it came from
  assets/tokyo.css             a standalone distillation: tokens, themes, components
  assets/icons.js              the icon set
  assets/starter.html          a page rendering every component, to look at
```

Point those four files at your own product and the skill works the same way. The
reference is the *why* and the *exactly*; the stylesheet is the *paste this*; the
starter page is what stops an agent inventing a card that almost matches.

The rules it enforces are the ones a design system usually loses first: one solid
accent per view, feature hues on data and never on chrome, two radii, no emoji,
44px tap targets, and a `prefers-reduced-motion` path for every animation.

## Install

```bash
git clone https://github.com/Bookee2/SkillZ.git && cd SkillZ && ./install.sh           # Claude Code
install-codex.sh     # Codex (tg-render)
```

This copies the skills to `~/.claude/skills/` and the shared target resolver to
`~/.claude/kb-loop/`, so they're available in every project on that computer.
It backs up anything it would overwrite. Name skills to install only those
(`./install.sh tg-render`). To pick up changes on another computer,
`git pull && ./install.sh`. To preview without writing:

```bash
./install.sh --dry-run
```

## Bind a repo

Nothing here is specific to one product. A repo joins the loop by declaring its
Linear team in `.claude/linear.json` at its root:

```json
{
  "team": "TrailGoat",
  "project": "Race catalog",
  "site": "https://trailgoat.run",
  "changelog": "static/changelog.html"
}
```

| Key | Required | Meaning |
|---|---|---|
| `team` | yes | Linear team name or key. Every read is filtered to it; every write targets it. |
| `project` | no | Default Linear project for issues this repo files. |
| `site` | no | What a merge to the default branch deploys. `/kb-merge` names it before the first merge of a pass. |
| `changelog` | no | Repo-relative path to the user-facing changelog a merge must keep current. When set, `/kb-merge` won't merge a PR that neither touches it nor says why it doesn't. |

An unbound repo is never guessed at. `/kb-spec` can propose a team and write the
file with you present; the three unattended skills report the missing binding
and end the pass.

Full resolution rules — including how a checkout is found and what happens to
stale issue prefixes — live in [`kb-loop/resolve-target.md`](kb-loop/resolve-target.md).

## Requirements

The loop needs:

- Claude Code
- The [Linear](https://linear.app) connector, authorized
- [`gh`](https://cli.github.com), authenticated
- Labels in your Linear team: `agent-ready`, `blocked`
- Labels in your GitHub repo: `loop-approved`, `loop-changes-requested`,
  `needs-human-review`

`/kb-design` needs none of that — only Claude Code, and a browser to render with
if you want it to check its own output (it uses Playwright and Chromium when
they are there).

## Layout

```
skills/
  kb-spec/SKILL.md     kb-build/SKILL.md
  kb-review/SKILL.md   kb-merge/SKILL.md
  tg-render/SKILL.md   tg-render/scripts/batch_render.py
  kb-motion/           # SKILL.md, references/ (catalog, lessons, research), assets/ (code)
  kb-secbrain/         # SKILL.md, scripts/collect.py (weekly harvest), scripts/pending.py (un-ingested inbox)
  kb-ytvideo/          # SKILL.md, engine/ (motion.js, build.py, render.js), scripts/, brands/, reference/, examples/
  tg-ingest/SKILL.md   # one ingest pass; runs from the TrailGoat checkout
  kb-unreal/           # SKILL.md, references/ (taste, capabilities, techniques, lessons, pipeline, samples, assets, interview, research, runs), assets/ (runner, camera paths, render wrapper), scripts/ (preflight, selfupdate)
  kb-design/           # SKILL.md, references/design-system.md, assets/ (tokyo.css, shell, icons, starter)
kb-loop/
  resolve-target.md    # shared target resolution, referenced by the four loop skills
install.sh
```

The copies in this repo are the published source. `install.sh` puts them where
Claude Code looks; edit them here and re-run it.

## License

MIT — see [LICENSE](LICENSE).
