"""Assemble round two of the motion proposal: round one's page (src.html) plus the v2 lab and the toolbox.
Writes src2.html; run build.py afterwards to inline data and assets."""
import re, pathlib
here = pathlib.Path(__file__).parent
src = (here / "src.html").read_text()
v2css = (here / "v2/styles.css").read_text() + (here / "v2/toolbox.css").read_text()
v2js = (here / "v2/modules.js").read_text() + "\n" + (here / "v2/toolbox.js").read_text()
S = {}
for f in ("v2/sections.html", "v2/toolbox.html"):
    for m in re.finditer(r"<!-- @([\w-]+) -->\n(.*?)(?=<!-- @|\Z)", (here / f).read_text(), re.S):
        S[m.group(1)] = m.group(2).rstrip() + "\n"

def rep(s, old, new, n=1):
    assert s.count(old) == n, (s.count(old), old[:90]); return s.replace(old, new)

src = rep(src, '<meta name="description" content="Eight motion ideas for the trailgoat.run landing page, each running live on real course data.">',
               '<meta name="description" content="Motion ideas for trailgoat.run plus a live toolbox of thirteen techniques, from particle morphing to WebGPU, each running on real course data.">')
# fonts: the variable axis, so letters can take any weight from 300 to 900
src = rep(src, "family=Red+Hat+Display:wght@500;700;800;900", "family=Red+Hat+Display:wght@300..900")
src = rep(src, "\n@media (prefers-reduced-motion: reduce) {\n    .hud-read div.flash", v2css + "\n@media (prefers-reduced-motion: reduce) {\n    .hud-read div.flash")
# GSAP and its three plugins, free since 3.13, only for the GSAP demo
src = rep(src, "<script>", """<script src="https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/SplitText.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/DrawSVGPlugin.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/MorphSVGPlugin.min.js"></script>
<script>""")

# ---------- split <main> into its top-level blocks ----------
a = src.index("<main>\n") + len("<main>\n"); b = src.index("</main>")
blocks = re.split(r"\n(?=<(?:header|section|footer)\b)", src[a:b])
def key(bl):
    m = re.match(r'<(\w+)[^>]*?(?:id="([^"]+)"|aria-labelledby="([^"]+)")', bl)
    return (m.group(2) or m.group(3)) if m else bl[:20]
B = {key(bl): bl.rstrip() + "\n" for bl in blocks}

# ---------- edits inside kept blocks ----------
mast_key = next(k for k, v in B.items() if v.startswith("<header"))
mast = B[mast_key]
mast = rep(mast, '<p class="label">Motion proposal · trailgoat.run landing page · 24 Sep 2026</p>',
                 '<p class="label">Motion proposal · round two · trailgoat.run landing page · 24 Sep 2026</p>')
mast = re.sub(r'<p class="dek">.*?</p>', '<p class="dek">Round two. The living hero stays exactly as you liked it. The lab goes deep on particle systems: one field of dots that becomes the wordmark, the goat, a race profile or a map, and the Run Planner\'s whole plan told as a particle story on Leadville. Then the toolbox: all thirteen techniques from the research, each with its own live demo, so you can compare them before choosing. Everything is built from real data: <strong>506 race courses, their profiles and routes, and the terrain around Hope Pass.</strong></p>', mast, flags=re.S)
mast = rep(mast, '<p class="calm-note" id="calm-note">', '<a class="btn" href="#research">Jump to the toolbox</a>\n        <p class="calm-note" id="calm-note">')
B[mast_key] = mast
B["idea-hero"] = rep(B["idea-hero"], "<h2>A living hero</h2>", '<h2>A living hero <span class="tag keep">Keeper</span></h2>')
B["idea-ridge"] = rep(B["idea-ridge"], 'data-pm="cta"', 'data-pm="parked"')
B["idea-board"] = rep(B["idea-board"], 'data-pm="crew"', 'data-pm="parked"')
B["idea-offline"] = rep(B["idea-offline"], 'data-pm="offline"', 'data-pm="parked"')
mp = B["map-h"]
mp = rep(mp, '<td><a href="#idea-build">The plan builds itself</a>: the four "how it works" cards become one scrubbed sequence.</td>',
             '<td><a href="#idea-build">The plan builds itself, round two</a>: one particle story on Leadville replaces the four "how it works" cards, and <a href="#idea-scrolly">scrolled</a> it runs off the page\'s own scroll.</td>')
mp = rep(mp, '<td><a href="#idea-hero">A living hero</a> and <a href="#idea-ridge">A goat on the ridge</a>.</td>',
             '<td><a href="#idea-hero">A living hero</a>, the keeper, and <a href="#idea-topo">Living topo</a> for the closing band.</td>')
mp = rep(mp, '<td><a href="#idea-board">Arrival board</a> demos the paid Crew Sheet; the sting gets a three-note chime.</td>',
             '<td>The <a href="#parked">parked</a> arrival board; the summit sting keeps its three-note chime.</td>')
mp = rep(mp, '<td><a href="#idea-sigs">506 course signatures</a>, and a sting per race. Built from data we own, so no scraped logos and no trademark questions.</td>',
             '<td><a href="#idea-sigs">Course signatures, five ways</a>, and <a href="#idea-field">one field</a> that can take any course\'s shape. Built from data we own, so no scraped logos and no trademark questions.</td>')
B["map-h"] = mp
pl = B["plan-h"]
pl = re.sub(r"<tbody>.*?</tbody>", """<tbody>
                    <tr class="group"><td colspan="3">Before launch</td></tr>
                    <tr><td><a href="#idea-hero">A living hero</a></td><td>Hero</td><td class="e">~½ day</td></tr>
                    <tr><td><a href="#idea-field">One field, many shapes</a>, recorded as reels</td><td>Launch-week posts</td><td class="e">~1 day</td></tr>
                    <tr class="group after"><td colspan="3">After launch</td></tr>
                    <tr><td><a href="#idea-build">The plan builds itself, round two</a>, <a href="#idea-scrolly">scrolled</a></td><td>How it works</td><td class="e">~2 days</td></tr>
                    <tr><td><a href="#idea-topo">Living topo</a></td><td>Closing band, course pages</td><td class="e">~1½ days</td></tr>
                    <tr><td><a href="#idea-sigs">Course signatures</a>, one style plus the ridgeline</td><td>Course library</td><td class="e">~1 day</td></tr>
                    <tr><td><a href="#idea-field">One field</a> on the site</td><td>Loader, 404, /courses</td><td class="e">~1½ days</td></tr>
                    <tr><td><a href="#idea-type">Type that climbs</a></td><td>Course pages, titles</td><td class="e">~½ day</td></tr>
                    <tr class="group after"><td colspan="3">From the toolbox, if you pick them</td></tr>
                    <tr><td><a href="#idea-cssd">Scroll-driven reveals</a></td><td>Every section</td><td class="e">~½ day</td></tr>
                    <tr><td><a href="#idea-gsap">GSAP pieces</a>, per piece</td><td>Launch-week social</td><td class="e">~½ day</td></tr>
                    <tr><td><a href="#idea-vt">A card that becomes the page</a></td><td>Course library</td><td class="e">~1 day</td></tr>
                    <tr><td><a href="#idea-contours">Contours that rise</a></td><td>Course pages, print</td><td class="e">~1 day</td></tr>
                    <tr><td><a href="#idea-gpgpu">Dots with momentum</a></td><td>Hero alternative, loader</td><td class="e">~1½ days</td></tr>
                    <tr><td><a href="#idea-webgpu">A quarter of a million on Hope Pass</a></td><td>Closing band, desktop</td><td class="e">~2 days</td></tr>
                    <tr><td><a href="#idea-sm">A goat with moods</a>, with Rive art</td><td>Loader, empty states</td><td class="e">~2–3 days</td></tr>
                    <tr class="group after"><td colspan="3">Parked</td></tr>
                    <tr><td><a href="#parked">Arrival board, Signal drop, A goat on the ridge</a></td><td>Crew Sheet, offline, footer</td><td class="e">—</td></tr>
                </tbody>""", pl, flags=re.S)
pl = re.sub(r'<p class="caption">Estimates are mine.*?</p>', '<p class="caption">Estimates are mine, for one developer, including a phone and First Light check. Before launch is about a day and a half, and none of it touches the Planner. Scroll-driven reveals are the one toolbox item small enough to add before launch too. The summit sting and its sizes stay available if you prefer them to particle reels.</p>', pl, flags=re.S)
pl = rep(pl, """<li><b>Cheap to draw.</b><span>Transforms, opacity, stroke offsets and canvas. Nothing that forces a layout every frame.</span></li>""",
             """<li><b>Cheap to draw.</b><span>Transforms, opacity, stroke offsets and canvas. Each particle field is a single WebGL draw call. Nothing forces a layout every frame.</span></li>
                <li><b>Dots scale to the device.</b><span>About 9,000 on a desktop and 3,200 on a phone for the lab's fields. Without WebGL, a short note shows in their place.</span></li>
                <li><b>Newer APIs fall back quietly.</b><span>WebGPU, scroll-driven CSS and view transitions each have a fallback: a note and the 2D topo, the finished frame, or an instant switch.</span></li>""")
B["plan-h"] = pl

# ---------- the research cards become the toolbox index, one live demo per technique ----------
DEMOS = {
    "Particle morphing": ([("idea-field", "One field, many shapes"), ("idea-build", "The plan builds itself")], None),
    "GPU particle simulation": ([("idea-gpgpu", "Dots with momentum")], "65,536 dots with real momentum that swirl and settle between course shapes."),
    "WebGPU compute": ([("idea-webgpu", "A quarter of a million on Hope Pass")], "262,144 particles tracing the contours around Hope Pass, one compute pass per frame."),
    "Flow fields": ([("idea-topo", "Living topo")], None),
    "Open terrain data": ([("idea-topo", "Living topo"), ("idea-contours", "Contours that rise")], None),
    "Contours from a height grid": ([("idea-contours", "Contours that rise")], "100 m contours around Hope Pass that rise from the valley floor, with a live elevation readout."),
    "Scrollytelling": ([("idea-scrolly", "The Leadville story, scrolled")], "the lab's Leadville particle story, driven by scrolling this page."),
    "Scroll-driven CSS": ([("idea-cssd", "Scroll-driven, no script")], "a profile, a counter and bars animated by scroll with no script at all."),
    "View transitions": ([("idea-vt", "A card that becomes the page")], "course cards that grow into a course page header and back."),
    "GSAP, now free": ([("idea-gsap", "One timeline, three plugins")], "SplitText, DrawSVG and MorphSVG on one timeline, ending on the goat."),
    "Ridgeline plots": ([("idea-sigs", "Course signatures, five ways")], None),
    "Variable fonts": ([("idea-type", "Type that climbs")], None),
    "Rive and dotLottie": ([("idea-sm", "A goat with moods")], "a state-machine goat on Leadville, built as a plain JavaScript stand-in."),
}
res = S["research"]
res = rep(res, '<p class="label">Research · beyond the video</p>', '<p class="label">The toolbox · every technique, live</p>')
res = rep(res, '<h2 id="research-h">What else is out there, and what fits TrailGoat</h2>', '<h2 id="research-h">The toolbox: thirteen techniques, thirteen live demos</h2>')
res = re.sub(r'(<h2 id="research-h">.*?</h2>\s*)<p>.*?</p>', r'\1<p>The video was only the starting point. These are the techniques behind most of the motion work people ship now. Five were already in the lab above. You asked to see the rest before deciding, so each one now has a working demo right below, built on TrailGoat data. Every card links to its demo, and the sources are there for later.</p>', res, count=1, flags=re.S)
seen = set()
def card(m):
    art = m.group(0)
    title = re.search(r"<h3>([^<]+?)\s*(?:<span|</h3>)", art).group(1).strip()
    links, demo = DEMOS[title]; seen.add(title)
    if demo:
        art = re.sub(r"<h3>(.*?)</h3>", r'<h3>\1 <span class="tag new">New demo</span></h3>', art, count=1, flags=re.S)
        art = re.sub(r'<p class="fit">.*?</p>', f'<p class="fit"><b>Demo:</b> {demo}</p>', art, count=1, flags=re.S)
    else:
        art = art.replace('<span class="tag used">Used</span>', '<span class="tag used">In the lab</span>')
    go = " · ".join(f'<a href="#{a}">{t} ↓</a>' for a, t in links)
    return art.replace('<p class="src">', f'<p class="go">{go}</p>\n            <p class="src">', 1)
res = re.sub(r'<article class="tech">.*?</article>', card, res, flags=re.S)
assert seen == set(DEMOS), set(DEMOS) - seen
S["research"] = res

# ---------- new order ----------
foot_key = next(k for k, v in B.items() if v.startswith("<footer"))
out = [B[mast_key], B["idea-hero"]]
out += [S["lab"], S["field"], S["build"], S["topo"], S["sigs"], S["type"]]
out += [S["research"], S["gpgpu"], S["webgpu"], S["contours"], S["scrolly"], S["cssd"], S["vt"], S["gsap"], S["sm"]]
out += [B["idea-sting"], B["idea-sizes"]]
out += [B["rise-h"], B["map-h"], B["notes"], B["plan-h"]]
out += [S["parked-open"], B["idea-board"], B["idea-offline"], B["idea-ridge"], S["parked-close"]]
out += [B[foot_key]]
src = src[:a] + "\n".join(x.rstrip() + "\n" for x in out) + src[b:]

# ---------- script: drop round one's build and signature modules, add round two and the toolbox ----------
s0 = src.index("/* =================== B. Plan builds itself =================== */")
s1 = src.index("/* =================== D. Arrival board =================== */")
src = src[:s0] + src[s1:]
p0 = src.index("/* =================== Page map =================== */")
src = src[:p0] + v2js + "\n" + src[p0:]
src = rep(src, """    const SECS = [['hero', 'Hero', 856, 'A'], ['tools', 'How it works', 670, 'B'], ['courses', 'Course library', 660, 'C'],
        ['crew', 'Crew Sheet', 297, 'D'], ['offline', 'Offline', 380, 'E'], ['cta', 'Closing + footer', 480, 'F']];
    const OFF = [['sting', 'Summit sting', 150, 'G'], ['sizes', 'Every size', 150, 'H']];
    const ideaFor = { hero: 'idea-hero', tools: 'idea-build', courses: 'idea-sigs', crew: 'idea-board', offline: 'idea-offline', cta: 'idea-ridge', sting: 'idea-sting', sizes: 'idea-sizes' };""",
"""    const SECS = [['hero', 'Hero', 856], ['tools', 'How it works', 670], ['courses', 'Course library', 660],
        ['crew', 'Crew Sheet (parked)', 297], ['offline', 'Offline (parked)', 380], ['cta', 'Closing + footer', 480]];
    const OFF = [['field', 'Loader, 404, reels', 130], ['type', 'Titles, social', 110], ['sting', 'Summit sting', 110], ['sizes', 'Every size', 110]];
    const ideaFor = { hero: 'idea-hero', tools: 'idea-build', courses: 'idea-sigs', crew: 'parked', offline: 'parked', cta: 'idea-topo', field: 'idea-field', type: 'idea-type', sting: 'idea-sting', sizes: 'idea-sizes' };""")
src = rep(src, "<p class=\"pm-note\">Block heights are the live page's real section heights at 1440 px. The dashed box is launch-week media that lives off the page.</p>",
               "<p class=\"pm-note\">Block heights are the live page's real section heights at 1440 px. The dashed box holds ideas that live off the landing page.</p>")
(here / "src2.html").write_text(src)
print("src2 KB", len(src) // 1024)
