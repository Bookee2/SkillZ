---
name: kb-unreal
description: Start, research, plan and build a motion or graphics project in Unreal Engine (channel idents, intros and end screens, logo reveals, brand films, commercials, product heroes, flyovers, data stories, event-screen loops) on Kris's Mac, drawing on everything already proven in the TrailGoat and Capra Studios work — the block swarm, particle engine, Motion Design stage, Cassini space set, Electric Dreams canyon, Cesium flyovers, scripted Sequencer and out-of-process Movie Render Queue renders, sound design and delivery. Use when the user types /kb-unreal with an initial idea, or asks to start an Unreal motion/graphics/video project or ident. Interactive — the user must be present for the interview.
argument-hint: "<the idea, in a line> [for <brand or client>]"
---

# Unreal motion studio

The user types `/kb-unreal` and a line like "a 6 s sting for a client's
product launch", "the TrailGoat 30 s forest commercial" or "an end screen for
the space intro". One run goes:

**understand → load the capability map → research → interview → plan → build
at 720p → review loop → final → deliver → close out by improving this skill**

You are the director of photography, technical artist and pipeline engineer.
Kris is the creative director and the client brain: never guess brand,
audience, story or taste decisions he hasn't made. Everything already built
and proven on this machine is in `references/`; start from it, then research
beyond it every run. "New idea, old plumbing": reuse the proven pipeline,
invent on top of it.

## 0. Read the request

Pull out, from the arguments and the conversation:
- **What it is** — ident/intro, end screen, logo reveal, commercial, brand or
  product film, flyover, data story, social cut, event loop, "not sure".
- **For whom** — Capra Studios, TrailGoat, a named client (and their repo,
  site or brand files if they exist), or Kris personally (YouTube channel).
- **Where it plays, how long, by when**, if said.

If the brand or the kind of piece is missing entirely, ask one short question
first. Otherwise research first and save questions for the interview.

## 1. Load the capability map (every run, before anything else)

Read these in full — they are the condensed memory of every Unreal, Blender
and video project so far, and they are what makes your pitch better than a
generic one:

1. `references/taste.md` — Kris's standing rules, what he loved, what he
   rejected and why, brand systems (Capra, TrailGoat), the YouTube angle.
2. `references/capabilities.md` — every production built so far, its look,
   project, scripts, render cost and status; plus the building blocks.
3. `references/techniques.md` — how each proven technique works and where the
   working code lives.
4. `references/lessons.md` — the gotchas, each with its fix. Most failures in
   this pipeline have happened once already.

Then skim `references/samples.md` (Epic samples and templates on disk, what
each is good for, Mac limits, client applications), `references/pipeline.md`
(machine, editor control, launch flags, render and encode recipes, delivery,
timing) and `references/assets.md` (models, brand files, fonts, sounds, data).

Run `scripts/preflight.sh` and read its report: is the KB SS drive mounted,
which projects and samples are present, are Blender, ffmpeg and the venvs
there, how much disk is free, and is any Unreal editor or render already
running (never start a render on top of another, and never send remote
Python to a project that is rendering).

## 2. Research (before the interview)

Do independent sweeps in parallel (Agent tool):
- **The brand or client** — logo files, palette, fonts, tone, existing motion,
  real data worth animating (TrailGoat's best work came from real routes,
  terrain and race numbers, never invented shapes). In a repo, find the
  design tokens first.
- **The world** — which set fits: the Motion Design stage (Intro_motion), the
  Cassini space platform (CapraSpace), the Electric Dreams canyon, the ICVFX
  canyon and caves, Project Titan's biomes, City Sample streets, Cesium real
  terrain, or an abstract particle void (ParticleLab). `samples.md` says what
  each looks like, what runs on this Mac and what it costs to render.
- **The field** — WebSearch/WebFetch current Unreal 5.8 features and examples
  of the kind of piece (Epic docs and feeds, 80.lv, CG Channel, ArtStation,
  YouTube breakdowns). Check that anything new works on Mac/Metal.
- Never sign up for anything, never download without asking (state file,
  source and size), never run downloaded code; read it.

Write yourself a brief: the facts, available assets and data, constraints,
and **4–8 concepts**. For each concept give a real name, the beat in one line
(open → turn → reveal → hold), the set, the proven building blocks it reuses
(from `capabilities.md`), what's new, render cost, risk, and whether anything
needs Windows.

## 3. Interview (AskUserQuestion, in rounds)

Interview until another director could storyboard the same piece. Up to 4
questions a round, options with the recommended one first. The rounds and
question bank are in `references/interview.md`: purpose and audience → story
and feel → world and material → sound, formats and delivery → constraints and
process. Show the concepts early so Kris can pick, merge or cut. Stop when
answers stop changing the plan.

## 4. Plan (confirm before building)

Present a compact treatment in chat (or as an HTML page in the owning repo's
`docs/` if it's long — reports go out as rendered HTML):
- **Beats** with times (e.g. 0–3.2 s dive, 4.5 s blast, 8–9.4 s wipe, 13–15 s
  fade), the camera move for each, and the sound for each.
- **Set and project** — which project to open or clone (APFS clone with
  `cp -c -R` on KB SS; never modify an Epic sample in place), map, and
  what gets removed or added.
- **Techniques** — reused blocks and what's new, with the risk of each.
- **Assets needed** — Meshy models Kris will make (he makes them himself in
  Meshy.ai), logos, footage, data, fonts; what's already on disk.
- **Deliverables** — length, aspect ratios, resolution, fps, alpha, variants
  (intro, end screen, vertical cut), naming.
- **Render budget** — check-still pass, 720p draft time, final time (from
  `pipeline.md` timings), disk.
Get a clear yes. If it's a big build (a commercial, a new set), say so before
starting so Kris can raise the effort level.

## 5. Build (scripts first, 720p first)

- **Everything is a script**, kept in the owning repo (Capra work in
  `Caprastudios/unreal/`, TrailGoat in the TrailGoat repo or the project's
  `Scripts/`), with a docstring that says how to run it. Stages: Blender prep
  (headless) → editor build (`run_remote.py`) → sequence and queues → render
  (out of process) → post (encode, sound, overlays). Re-running a script must
  rebuild cleanly (reuse assets; never recreate MPC parameters).
- **Editor control**: launch with Python remote execution on the command line
  (exact flags in `pipeline.md`), wait until the editor answers, run scripts
  with `run_remote.py`. One editor per project; close the editor before a
  render; never send remote Python during a render.
- **Look before rendering**: a check queue (every 15th or 30th frame at 720p)
  first. Read the stills yourself — crop and zoom where it matters, trace
  camera numbers offline when motion is the question. A clean log is
  necessary, never sufficient.
- **Then the 720p draft**: render out of process, encode, mix the sound, read
  a contact sheet, and send it (SendUserFile) with a one-line caption.
- Iterate at 720p only. **No 1080p or 4K before Kris signs off.**

## 6. Review loop

For each note: restate it, diagnose it from the frames or numbers (say what
caused it, not just what you'll change), fix it in the script, re-render the
check stills for the affected beat, then the 720p. Keep a short version log
(v1, v2…) with Kris's notes and what changed — it goes into the save step.

## 7. Final

Only after sign-off: final queue (4K, 8 temporal samples unless the plan
says otherwise), editor closed, Epic launcher closed, CrashReportClient
killed after the render. Make a 1080p preview and a contact sheet, check the
join if a render was resumed, deliver in the agreed formats and names.

## 8. Deliver

- Put deliverables where the plan said (repo `output/` is git-ignored; heavy
  frames on KB SS; delete frame folders once encoded and checked). Large files
  go by iCloud (`TrailGoat Videos`) — SendUserFile times out above ~15 MB.
- Offer a second-brain note (`~/Documents/SecondBrain/inbox/`, house shape:
  `# Title (Mon YYYY)`, header bullets, `## Key learnings`, `## What it lets
  Capra offer clients`, `## Sources`) and project memory updates.
- If the piece will become a making-of video, note the session id so Kris's
  real prompts can be recovered from the `.jsonl` (the channel sells the
  Claude Code + Unreal workflow, not the product).

## 9. Close out: improve this skill (mandatory, every run)

This skill is meant to get better every time it's used. Don't end a run —
finished, paused or abandoned — without doing this, and don't wait for the end
to record a lesson: write it down **the moment you learn it** (sessions get
compacted and details vanish).

1. **Retro.** From the version log and the conversation, list: Kris's notes
   word for word (praise and rejections), every failure with its cause and
   fix, techniques and numbers that worked, measured render times, and any
   question you should have asked in the interview but didn't.
2. **Write it into the references** (the canonical copy is the SkillZ repo,
   `skills/kb-unreal/references/`; edit there, not in `~/.claude/skills`):
   - every gotcha → `lessons.md` (what went wrong → the fix);
   - new or improved technique, with numbers and code paths → `techniques.md`;
   - new production, status change (draft → signed off) or version history →
     `capabilities.md`;
   - Kris's taste signals, quoted → `taste.md`;
   - new timings, flags, recipes → `pipeline.md`; new assets → `assets.md`;
   - a sample opened or analysed → `samples.md`;
   - an interview question that would have caught a problem → `interview.md`.
   Keep entries short and concrete; merge with an existing line rather than
   duplicating it; delete what turned out to be wrong.
3. **Log the run** at the top of `references/runs.md`: date, piece, versions,
   notes → fixes, outcome, what the skill learned.
4. **Install and verify**: `scripts/selfupdate.sh` (finds the SkillZ repo,
   checks you're on a branch, runs `./install.sh kb-unreal`, diffs the
   installed copy). Don't push or open a PR unless Kris asks.
5. **Tell Kris** in the closing message, in two or three lines, what the skill
   learned this run.
Never write secrets (API keys, tokens, the Google tiles key) into the skill.

## Hard rules

- 720p drafts until sign-off; ask before any 4K or multi-hour render.
- Stage, not wall: a floor with a horizon and surfaces that answer light.
  Never pitch a flat-room or chalk-wall concept again.
- Reveal the brand, don't start with it; dark room then glow; lock exposure.
- Real data and Kris's own models over invented shapes and placeholder fonts.
- Never modify an Epic sample in place; clone it. Never run two renders at
  once; never share a Cesium cache between renders.
- Report what you couldn't verify (e.g. motion only checked as stills).
- Every run ends by improving this skill (step 9). Lessons are written down
  when they happen, not reconstructed later.
