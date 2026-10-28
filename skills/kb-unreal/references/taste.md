# Taste, rules and brands (read first, keep adding)

Kris Brown runs Capra Studios (Atlanta: websites with motion and video
graphics including 3D brand films, software, practical AI) and makes
TrailGoat (trail-running planner, trailgoat.run). He makes YouTube videos about
building things with AI. Every rule below came from a real note on a real
render; the quote or incident is kept so you know how hard the rule is.

## Process rules (hard)

- **720p until sign-off.** Iterate at 1280×720, send the cut, wait. No 1080p,
  4K or multi-hour render until Kris says go. A 4K started early once had to be
  killed. (memory: no-final-renders-before-signoff; TrailGoat electric-dreams)
- **Tell him before a big build** (a 30 s commercial, a new set) so he can
  raise the effort level.
- **Close the editor during renders** (it halved speed: 27 s vs 14 s a frame at
  1080p). Close the Epic Games Launcher too. Never send remote Python while a
  render runs (a quit meant for the editor killed a 1080p render at frame 89).
- **Ask before downloading** anything (file, source, size). He approved the
  Mixkit sound library downloads; that approval doesn't carry to new sources.
- **Reports go out as designed, self-contained HTML** in the repo's `docs/`,
  shown rendered, with a short chat reply. Every analysis of a sample, tool or
  technique has a **"for future clients"** section tied to the real service
  lines, with licence and platform limits.
- **Don't flag Fab's "Allows usage with AI: No"** on Epic samples (scripting
  Unreal isn't AI training). Flag only unusual terms (non-commercial,
  editorial-only, attribution). Don't hand raw sample assets to clients
  outside Unreal.
- Don't push or open PRs unless asked. Commit only when asked. The exception
  is SkillZ itself: "I want to update our skillz after every learning session"
  (2026-10-26), so skill updates are committed, PR'd and merged at close-out.

## What he loved

- **The block swarm on the Motion Design stage**: "100x better" than the wall.
  Blocks fly in from a burst into his own Meshy models, solid lattice fill
  (blocks touch, real 3D depth), black-light glow, then dissolve back to the
  solid models. Signed off at 4K (sound mix R3 "neon power").
- **Particles morphing into words, profiles and maps** (TrailGoat openers) —
  the thing that excites him most.
- **The Saturn dive**: opening on the whole planet and rings, then falling
  through the rings onto the platform (space intro v2: "awesome").
- His own Meshy hero objects in the set: he swapped Cassini's monolith for a
  Meshy "Amethyst Unicorn" statue (white body, violet mane, lime horn — on
  brand) to be what explodes into the lockup ("this is going to be awesome!").
- **Real sound** over synthesis: he asked "can we not find a real sound
  library" — Mixkit recordings placed by their measured hit point.
- The end screen holding 20 s with the lit solid models, not a spinning sphere
  ("the sphere spinning loses the branding").
- Centred, eye-level end frames that keep creeping in so they breathe.

- The TrailGoat Films ident: "I'm not half assing this" (asked for 3D particles
  from Unreal over a 2D cut); on v2 with the drone under the lockup: "I like the
  second cut, let's keep building baby".
- Sound made of the world in the picture: night crickets, his footfalls, wind,
  a rock-impact hit (Films ident v2).

## What he rejected (never pitch again without a new answer)

- **The chalk wall ("Lights off" v1–v3)**: "this sucks", "first day in film
  school". Extruded logo plates on a matte wall give the renderer nothing;
  flat colour on flat geometry has no shading. → Stage, not wall.
- Letters ending "tilted back and to the left" — the camera must finish dead
  centre at eye level.
- Flat-looking 3D ("it's not 3D, it looks flat"), loose blocks ("compile much
  more loosely than TrailGoat") → solid volume fill, more depth.
- A logo glow so bright "you can't tell what it is" (space v1, glow 2.3 →
  0.75). Colours must read.
- An explosion that "doesn't look like it's actually exploding" (a slow peel
  in reading order). Explosions need a burst, a flash and camera recoil.
- A weak explosion sound → sub boom, suck-in, ducking.
- Stock sci-fi/magic sound effects for a TrailGoat piece: "The sounds are
  terrible" (Films ident v1: tube buzz, fairy shimmer, futuristic swoosh,
  trailer hit; Kris: cheesy). Use recordings of the world on screen.
- Anything that tips at the end: "the wordmark tilts down to the right" — a
  drain or exit must keep the lockup level.
- White-hot fragments that "turn into the colours" later → burst in colour.
- A platform that "appears out of nowhere" at the end of a dive → keep the
  set always loaded and give the last decade of the approach real time.
- An explosion that spreads as a flat ring instead of a sphere; a camera that
  "zooms to the side of the platform" — he wants to watch the explosion centred
  and natural (space v3 → v4).
- A camera "bump" when a move stops and restarts at a key → one continuous
  monotone curve per channel.
- Spinning-sphere outros that hide the brand; reversed intros as outros.
- TrailGoat: Unreal Western States render (Blender flyovers stay until Unreal
  matches them); a thin trail line; a particle zoom; smoke-formed shapes (smoke
  only as a transition); out-and-back elevation profiles (they mirror); many
  islands (one island); the Meshy Stand_and_Drink clip (head too big); a
  timing mat; the goat clipping rocks.

## Creative direction (from the ident post-mortem and brief)

- **Stage, not wall.** A floor with a horizon, something reflective, open dark
  space, a three-light rig; surfaces that answer light (chrome, plastic with
  micro-roughness and normals, rounded edges, many small facets). "A picture
  of a logo" vs "a place where a logo happens".
- **Orbit, don't dolly.** Parallax is free depth. Arrive from the side so the
  forms show depth, pan to dead centre at eye level, creep in through the hold.
- **Reveal the brand, don't start with it.** Cause and effect in beats:
  before → hit → reveal → sign-off.
- **Dark room, then glow.** The black-light switch is the studio's one trick;
  idents end in a dark room with a glowing mark. Fluorescence never switches
  on all at once (stagger by reading order or per mark).
- **Lock exposure** (manual / min = max EV) so renders don't drift; bloom
  modest.
- The intro ends on the wordmark and the outro starts on it. Outros keep room
  for YouTube end-screen elements and hold 5–20 s.
- Kris's own lettering/models, not fonts: the current lockup is three Meshy
  models (unicorn bust, one-line "capra studios", sprayed "with Kris").
  Sedgwick Ave and Rubik Spray Paint are stand-ins only.
- Reuse three diegetic sounds across idents (UV tube hum, switch click, low
  thud) where they fit; Kris adds music himself on many pieces — deliver
  silent masters plus SFX mixes.

## Capra land films (Petit Ridge, 2026-10-28)
- Kris picked: spec demo to pitch realtors/land brokers; all four cuts (film, 9:16, stills, sizzle); "The View
  Sells It" + "Read the Land" + "Leaf-Off" (not the block-swarm cabin); peak fall golden → blue hour; world sound
  with his music later; road but no neighbours; World Wakes reveal; **Capra-forward** branding; the lockup with
  "Your land, before it's built." He declined computer-use control of the Unreal window: script everything.
- v1 note, word for word: "The video is killer, the sounds are terrible." The v1 bed was game-sample loops
  (Electric Dreams' tropical canopy and crickets, a riverbed for a still lake, Game Animation Sample wind, the
  ED drone, a boulder "knock", a reversed gust). → Real places need real recordings of that place and season;
  no sample-project ambience, no designed hits or drones. He asked "What can we do with REAL sounds."
- Deliverables: Capra videos go to iCloud `Capra Studios/Videos`, never `TrailGoat Videos`.

## Capra Studios brand

- Palette (docs/BRAND.md): Chalk #f3f1ea, Ink #15141c, **Ribbon blue #7aa2f7
  (the logo, always)**, UV violet #7a2df5, Acid lime #b6ff3b, Koi orange
  #ff5c1a, Solar yellow #ffd23f, Hot magenta #ef388d, Lagoon #1ad7ce
  (TrailGoat). Flat fields only; one colour per section; gradients only
  inside artwork. Video cyc #0e0b16.
- Lockup colours in the block ident (dark → light): unicorn #5a1fd1 → #7aa2f7,
  capra studios #6fbf1c → #c8ff5a, with Kris #c2186f → #ff5aa5.
- Type: Red Hat Display 700–900 (headlines, wordmark), Red Hat Text 400–700.
  Fonts in `Caprastudios/marketing/brand/fonts/` (OFL).
- Motion tokens (web): --dur .45 s, ease-out cubic-bezier(.2,.8,.2,1). The
  brand feel is quick and settled, not bouncy.
- Voice: "Imagination. Made tangible." Studio "we" on the site; Kris's "I" in
  making-of videos. British spelling in docs. No invented awards or metrics.

## TrailGoat brand

- Tokyo Night (site default): canvas #1a1b26, panel #24283b, ink #c0caf5,
  bright #e6eafc, muted #9aa5ce, accent #7aa2f7. Data colours: fuel #ff9e64,
  pace #7aa2f7, crew #9ece6a, course #0db9d7, gear #bb9af7, weather #d98ae0,
  climb #f7768e, aid #7dcfff, gold #e0af68.
- Wordmark: TRAIL in #c0caf5, GOAT as a gradient #0db9d7 → #7aa2f7, Red Hat
  Display ExtraBold, always uppercase TRAILGOAT. Unreal emission calibrated to
  the navbar colours with `calib_nav.py`.
- Taglines: "Plan the climb. Nail the fuel. Send the trail." / "Greatness On
  All Trails." Pricing copy: "Free, no catch" (never "free forever").
- Mascot: the right-facing Tokyo Night goat; the Meshy "Running Goat biped"
  with 19 clips is the 3D goat.
- Music: Kris's own tracks (Breakbeat 20s, Tech House 20s, openers); house
  pick "A" = Breakbeat 20s from 17.65 s (drop lands at 3.35 s, bar 2.41 s).
  Loudness −14 LUFS for social, −16 for the Reddit demo.

## YouTube angle

- Making-of videos sell the **Claude Code + Unreal workflow**, not the product
  ("No one cares about trailgoat"). Show Kris's real prompts on screen, typos
  included, in his first person. Structure: the bridge (how Claude drives
  Unreal), the note-to-render loop, prompt/response pairs, what broke, "if you
  try this". Real prompts are recoverable from the session `.jsonl` files.
- Channel package: intro (10–15 s), end screen (20 s, room for end-screen
  elements), upload 4K so YouTube uses its better encoding ladder.
