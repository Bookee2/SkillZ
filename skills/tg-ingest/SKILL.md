---
name: tg-ingest
description: Run one crawl-and-ingest pass for the TrailGoat race catalog — sweep UltraSignup (once a day), hunt course GPX files (scripted, then by web search in this session), import, enrich and audit, then print a digest. Use when asked to grow the race catalog, run ingestion, or hunt course files. Designed for /loop; one invocation does exactly one pass.
---

# One ingest pass

Grows the race catalog by one pass and stops. `/loop 3h /tg-ingest` supplies the
cadence — **this skill never loops itself**, never schedules a wake-up, and ends
its turn after printing the digest.

Run from the repo root (`running-backend`). Every command below uses
`.venv/bin/python`; the system `python` is not the project's.

**Where to run.** This skill is installed user-wide (SkillZ), so it can be
invoked from any project. Every command below is relative to the TrailGoat
checkout. If the current directory has no `sweep_gate.py`, `cd` to
`~/Desktop/Projects/TrailGoat` first (on another machine, ask where the
TrailGoat checkout lives) and run the whole pass from there.

> **This pass writes to the PRODUCTION database.** Local `.env` points at prod
> Turso. That is intended here — ingestion's whole job is to add real courses —
> but it means a half-understood command is a live mistake. Run the steps as
> written.

> **Race ingestion never bills the Anthropic API. This is settled.** Kris,
> 2026-09-10: *"I'm never going to use an API call for it — I want to use my
> Claude Code plan usage, and I'm never going back to API for this kind of
> ingestion."* The hunt in step 4 is **your own web search**, on plan usage.
>
> There is no paid hunter to avoid any more: `gpx_agent.py` (Haiku +
> web_search) was **deleted** that day rather than left switched off, and the
> `race-sweep` GitHub Actions workflow that invoked it was retired with it —
> ingestion runs from Claude Code only. If you find yourself reaching for a
> model API to widen the hunt, the answer is more of your own searching, or
> the long-haul run below. Do not reintroduce one.

## The pass

Run these in order. Record the numbers as you go — the digest at the end is the
only output the user reads, and it must reflect what actually happened, not what
was supposed to.

### 0. Preflight — free on a machine that is already set up

```bash
scripts/bootstrap.sh
```

Creates `.venv` if it is missing, installs `requirements.txt`, and prints
whether the credentials the pass needs are present. On this laptop it is a
couple of seconds and prints `INGEST ENV: ready`; on a fresh cloud checkout it
is the difference between the pass running and every step failing on a missing
`.venv/bin/python`.

If it prints `INGEST ENV: not ready`, **stop the pass and say what is missing.**
The blocker is always a credential only Kris can supply — `TURSO_DATABASE_URL`
and `TURSO_AUTH_TOKEN` are the two that matter, and without them the pass would
happily write a whole crawl into a throwaway local file and report success.
`STRAVA_*` missing is a warning, not a blocker: the pass runs, but Strava route
candidates land in the manual queue instead of importing.

### 1. Sweep, at most once a day

```bash
.venv/bin/python sweep_gate.py --check
```

Exit 0 means due; exit 1 means today is already swept — **skip to step 3** and
say so in the digest. When due:

```bash
.venv/bin/python sweep.py --max-new 300
```

Two discovery sources run inside that, and the digest names both. The sitemap
is the cheap one and is currently **contributing nothing**: UltraSignup still
regenerates `sitemap-0.xml.gz`, but it took on no new id after 2026-07-27, so
`new: 0` on that line is expected rather than a fault. The one that finds races
now is the `frontier_*` walk, which probes the did space forward from a
high-water mark — `frontier_from`/`frontier_to` are the ids it covered. A pass
where `staged` is 0 **and** `frontier_probed` is 0 is the signal something is
actually wrong; say so rather than reporting a quiet zero.

Then, **only if it completed without a hard stop**:

```bash
.venv/bin/python sweep_gate.py --claim
```

Claiming after the fact is deliberate: a sweep aborted by a 403 leaves the day
unclaimed so the next pass can retry, rather than costing a day of growth.

### 2. Hard stops are the end of the pass

If the sweep prints `HARD STOP` or reports HTTP 403/429 from UltraSignup, **do
not retry and do not work around it**. Stop the pass here, skip to the digest,
and say which step stopped and why. UltraSignup blocking us is a signal to back
off for the day, not an obstacle to route around.

### 2b. Organizer websites

```bash
.venv/bin/python backfill_org_sites.py --all --commit --limit 25
```

Revisits one UltraSignup source page per event and fills a missing organizer
website before either downstream crawler needs it. Upcoming races sort first;
once they are covered, the same capped pass works through historical events
whose public course pages still lack the link. Every completed look is stamped,
including pages with no usable external link, so repeated passes advance rather
than fetching the same first 25 misses forever. Note its `DONE` line.

This step only fills blanks. It never replaces a hand-curated or previously
captured website. A 403/429 is the same hard stop as the sweep: end the pass and
do not retry around it.

### 3. Scripted hunt

```bash
.venv/bin/python gpx_hunt.py --all --limit 150
```

Note its `TALLY` line. This crawls organizer sites; it is the cheap hunt and it
runs every pass.

### 4. In-session hunt — the part only you can do

Take the batch — up to **40** editions worth searching for, upcoming races
first (soonest first), then past ones (most recent first). Past races are in
on purpose (Kris, 2026-10-12): nearly every race is annual, so last year's
official course is worth filing, and the importer takes it. A race whose
distance already has a course from any year is not offered again, and a race
searched in session in the last 180 days is not re-served under another
distance or year:

```bash
.venv/bin/python hunt_queue.py
```

40 is the size of one loop pass, not a rule about how much hunting is allowed.
Since the hunt runs on plan usage rather than a metered API, the only reason to
stop is the session, so `--limit` it up freely when you are catching up a
backlog or the user asks for volume — `hunt_queue.py --limit 200`. Work down it
soonest-race-first and record as you go, so a session that ends early still
banks everything it found.

Note its `QUEUE` line: it reports the batch size, how many events are huntable,
and what each filter removed. Quote it in the digest (step 8).

The selector drops what cannot pay off (TG-259): timed and last-one-standing
formats have no fixed course, distances outside the importer's 15–700 km are
rejected even when found, `Kids Run`-style rows are not races, UltraSignup's
demo events are not either — and it takes **one edition per event**, the
longest distance, so a batch of 40 is 40 races rather than the ~16 the old
query managed.

For each edition, search the web for its **official course map file**. Aim at
the organizer's own site and its course/map page.

**These eight shapes import on their own.** They are what `gpx_import.py`
resolves unaided, and they are what your searches should be aiming at — the
organizer's own site and its course/map page is where they live:

<!-- tg-ingest:auto -->
- a direct GPX file — `https://races.example.org/files/course.gpx`
- a GPX download endpoint — `https://races.example.org/routes/160km/download-gpx?variant=official`
- a zipped course — `https://races.example.org/files/courses.zip`
- CalTopo — `https://caltopo.com/m/AB12CD`
- Google Drive — `https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQr/view`
- Dropbox — `https://www.dropbox.com/s/abc123/course.gpx?dl=0`
- Strava **route** — `https://www.strava.com/routes/3139930042447530202`
- a GPX download whose URL never says so — record the bare link; the recorder asks the server, and only if its headers say GPX stores it as `https://races.example.org/courses/stillhouse-100k#gpx`
<!-- /tg-ingest:auto -->

Strava goes through the sanctioned API (`strava_route_gpx()`), which needs
`STRAVA_CLIENT_ID`/`SECRET`/`REFRESH_TOKEN` in `.env` — they are there, and it
resolves. Two limits: it is **`/routes/` only** — a `strava.com/activities/…`
link is somebody's recorded run, not a course, and is not a candidate; and if
the credentials are ever pulled, the importer degrades the URL to `manual`
rather than failing, so a run of Strava rows landing in the manual queue is the
signal to check `config.strava_configured()`.

**These do NOT import — they are manual-queue material only.** Each is blocked
by the site itself, not by missing code: RideWithGPS's robots.txt closes the
export path, plotaroute answers a bot challenge, and Footpath and HelloDrifter
draw their course pages in the browser, so an anonymous fetch gets an app shell
instead of a track. Recording one puts a link in /admin/ingest for a person to
fetch by hand, which is worth something — but it is **not** a found course:

<!-- tg-ingest:manual -->
- RideWithGPS — `https://ridewithgps.com/routes/15084161`
- plotaroute — `https://www.plotaroute.com/route/3138393`
- HelloDrifter — `https://www.hellodrifter.com/events/example-50k-2027/races/10209/gpx_download`
- Footpath — `https://footpathapp.com/routes/bulldog-ultra-25k/e4c4ee99-8622-446c-9add-564115ace7d3`
<!-- /tg-ingest:manual -->

So: **search for an auto shape first, and only record a manual one if that
search came up empty** — at most one, and never in place of continuing to look.
This is the pass's main leak. Over 2026-09-02/03 the hunt recorded 16
candidates and 13 were on manual platforms, because this list used to present
them as importable; exactly one edition imported. (Strava was on that manual
list until 2026-09-03 and is now an auto shape, which narrowed the leak.)

The list above is kept deliberately short for the same reason: a platform earns
a line only when it is often the **only** course link a race publishes. That is
why Footpath is on it — Footpath is the official mapping partner for a cluster
of SoCal races, and for several of them `footpathapp.com` is the entire website.
So the list is **not** the full set of manual shapes. `app/course_sources.py`
names more of them (ultrapacer, Gaia, AllTrails, Garmin and the rest) so that
the scripted hunt can still record a link for /admin/ingest instead of dropping
it — that table is the wider net, not a menu for this step.

Anything not in either list is not a candidate. Take **at most 3** per edition,
best first — and **order matters**: the importer tries them in the order you
record them and takes the first that resolves, so put the file for *this
edition's distance* ahead of a longer or shorter one. A page that merely
*describes* the course is not a candidate. Guessing a URL is worse than finding
nothing: an edition with no row gets re-hunted later, but a wrong candidate is
tried, fails, and looks like a dead end.

Record everything you looked at — including the editions where you found
nothing, so the next pass does not ask again:

```bash
cat <<'JSON' | .venv/bin/python record_candidates.py --stdin
[{"edition_id": 4211, "candidates": [{"url": "https://…/course.gpx", "distance_label": "50K"}]},
 {"edition_id": 4212, "candidates": []}]
JSON
```

The helper merges rather than replaces, drops URL shapes the importer can't use,
**checks that each URL actually resolves before recording it**, and never
erases what an earlier pass found. Note its `RECORDED` line — it reports both
kinds of drop, wrong-shape and did-not-resolve.

### 5. Organizer emails

```bash
.venv/bin/python backfill_org_emails.py --all --commit --limit 25
```

Reads the organizer sites we already hold and records one contact address —
and, where the page labels one plainly, a contact NAME — per event. Capped at
25 because it fetches other people's sites; it converges across passes like the
surface pass does. Note its `DONE` line.

`--all` at the same cap is strictly more coverage for the same cost: it sorts
upcoming races first, so the urgent work still happens first, and only the
leftover budget reaches events whose next edition hasn't been announced yet or
that have an address but no name. Those become pitchable the moment the sweeper
files their next edition, and the contact is already in hand.

Collection only — nothing in this pass emails anybody.

### 6. Import and build previews

```bash
.venv/bin/python gpx_import.py --commit --no-surface
.venv/bin/python backfill_route_preview.py
```

`--no-surface` on purpose: surfacing happens under its own cap in step 7.

### 7. Capped surface pass

```bash
.venv/bin/python backfill_surface.py --max-minutes 30
```

The cap is the point — it converges across passes instead of needing one long
run.

### 8. Audit

```bash
.venv/bin/python audit_course_distances.py
.venv/bin/python audit_course_quality.py
```

A green sweep is not the same as a good import — the 2026-08-03 sweep landed
seven wrong courses and these audits are how that was caught. Report their
counts even when they are zero.

### 9. Race results

```bash
.venv/bin/python results_fetch.py --max 150
```

Reads UltraSignup's per-edition results for races that have already happened
and stores the aggregates — finishers, DNF, DNS and the shape of the finish
times. Gated to once a day on its own `sync_state` key, so running the pass
again in the afternoon reports the skip rather than re-reading the same races.

Politeness is the sweep's: same UA, 2 s between requests, hard stop on 403/429.
A stopped run leaves the day unclaimed so the next pass can pick it up.

### 10. Outreach queue — report only

```bash
.venv/bin/python outreach_status.py
```

Prints how many race directors are waiting to be pitched and how many
follow-ups have come due, straight off `app/outreach.py` — the same function
`/admin/outreach` renders, so the digest can't disagree with the page. Add
`--detail` when the counts look surprising and you want the races behind them.

This step reports state; it never changes any. The pass never logs an outreach
touch and never emails a race director — sending stays one-to-one from Kris's
own mailbox.

## The digest

Print exactly one block, last thing in the turn:

```
## Ingest pass — <date>

Sweep      : <N new events staged> from did <frontier_from>-<frontier_to> · or "skipped — already ran today (<date>)"
Sites      : <N organizer sites resolved> · <N rows written> · <N misses checked>
Hunt       : <N editions crawled> → <N with candidates>   (scripted)
             <N editions searched> → <N with candidates>  (in session)
Emails     : <N emails> · <N names> found · <N rows written>   (organizer contacts)
Import     : <N imported> · <N manual> · <N failed> · <N distance-mismatch>
Previews   : <N built>
Surface    : <N courses profiled> (30 min cap)
Audits     : <N distance mismatches> · <N quality flags>
Results    : <N fetched> · <N with finishers> · <N empty> · or "skipped — already ran today (<date>)"
Outreach   : <N never contacted> · <N follow-ups due>   (RDs waiting)
```

Rules for it:

- **Numbers come from the commands' own output.** If a step was skipped or
  stopped, say so on its line rather than printing a zero — a zero and a
  never-ran look identical, and only one of them is fine.
- If nothing needed doing anywhere, say **"nothing to do"** and keep it short.
- If the pass stopped early, lead with why, then show the lines that did run.

Then end the turn. Do not schedule anything; do not start another pass.

## The other shape: a long-haul catch-up

When the ask is a **backlog** rather than a pass — "hunt everything we missed",
"grab as many races as possible" — do not try to do it in one turn of this
runbook. Start the unattended driver and let it grind:

```bash
.venv/bin/python scripts/longhaul_ingest.py
```

It sweeps the did space to exhaustion, then crawls organizer sites for every
un-hunted edition (upcoming first, then past), then imports, previews and audits — strictly
sequentially, because `sweep.py` and `gpx_hunt.py` both fetch ultrasignup.com
and running them together doubles our rate there and earns the 403 that stops
both. It claims the daily sweep gate on the way in and writes
`data/longhaul_progress.json`; `--status` reads that without running anything.

Two things follow from it being unattended:

- **Do not run a normal `/tg-ingest` pass while it is going.** The gate claim
  makes a concurrent pass skip *its* sweep, but step 3's scripted hunt would
  still put a second crawler on UltraSignup.
- **Your own hunting is still the valuable leg**, and it composes with the
  driver: candidates you record go into the same `gpx_hunt` table, so the
  driver's import phase picks them up. Pull big `hunt_queue.py --limit` batches
  and work soonest-race-first while it crawls.
