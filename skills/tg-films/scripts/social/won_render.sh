#!/bin/zsh
# "How it was won": the film's camera rendered at the full 16:9 width at the race Shorts' scale (2160x1920: the 9:16 window's
# 32 mm height across the film's 36 mm width, --portrait 1.0), under the studio's render lock (the batch chains wait on it).
#   won_render.sh <slug> dry              -> cam.json (the solved camera per frame) + hud-frames.json
#   won_render.sh <slug> <f0>-<f1>[,...]  -> frames/f_NNNN.png for those film frames
set -u
SLUG=$1; WHAT=$2; YEAR=${3:-2026}
Q="/Volumes/KB SS/TrailGoat-Studio/Films/queue"; LOCK="$Q/.render.lock"
FILM="/Volumes/KB SS/TrailGoat-Studio/Films/$SLUG/film.json"
OUTD=$(python3 -c "import json;print(json.load(open('$FILM'))['out_dir'])")
SHOTS=$(python3 -c "import json;print(json.load(open('$FILM'))['shots'])")
C=$(ls "$OUTD"/course-*.json | head -1)
OUT="/Volumes/KB SS/TrailGoat-Studio/Renders/flyovers/shorts/$SLUG/won-$YEAR"; mkdir -p "$OUT"
W=/Users/kb/Desktop/Projects/TrailGoat/.claude/worktrees/weekly-shorts   # render.py as on main, with the tile cache
B=/Applications/Blender.app/Contents/MacOS/Blender
WAITF="$Q/won.wait.$SLUG"; touch "$WAITF"; trap 'rm -f "$WAITF"' EXIT   # the batch masters let us in between films
while true; do
  if ! pgrep -f 'Blender.*-b' >/dev/null; then mkdir "$LOCK" 2>/dev/null && break; fi
  sleep 20
done
rm -f "$WAITF"
trap 'rmdir "$LOCK" 2>/dev/null' EXIT
echo "LOCK $SLUG $WHAT $(date +%H:%M)"
cd $W
if [[ $WHAT == dry ]]; then
  $B -b -P scripts/flythrough/render.py -- "$C" "$OUT" --shots "$SHOTS" --res 2160x1920 --portrait 1.0 --dry --export-cam "$OUT/cam.json" > "$OUT/dry.log" 2>&1
  tail -3 "$OUT/dry.log"; exit 0
fi
NEED=0; for r in ${(s:,:)WHAT}; do a=${r%-*}; b=${r#*-}; NEED=$((NEED + b - a + 1)); done
for i in 1 2 3 4 5; do
  for r in ${(s:,:)WHAT}; do
    $B -b -P scripts/flythrough/render.py -- "$C" "$OUT" --shots "$SHOTS" --res 2160x1920 --portrait 1.0 --samples 32 --frames $r >> "$OUT/render.log" 2>&1
  done
  n=0; for r in ${(s:,:)WHAT}; do a=${r%-*}; b=${r#*-}; for f in {$a..$b}; do [[ -f "$OUT/frames/$(printf 'f_%04d.png' $f)" ]] && n=$((n+1)); done; done
  echo "pass $i: $n of $NEED frames $(date +%H:%M)"
  (( n >= NEED )) && break
  sleep $((60*i))
done
echo "DONE $SLUG $(date +%H:%M)"
