#!/bin/zsh
# Install the kb-unreal skill from its canonical SkillZ copy and verify the
# installed copy matches. Run at the close-out of every /kb-unreal run, after
# editing skills/kb-unreal/ in the SkillZ repo.
#
#   ~/.claude/skills/kb-unreal/scripts/selfupdate.sh
#
# SKILLZ_REPO overrides the repo location (default ~/Desktop/Projects/SkillZ).
set -u
REPO="${SKILLZ_REPO:-$HOME/Desktop/Projects/SkillZ}"
DEST="${CLAUDE_HOME:-$HOME/.claude}/skills/kb-unreal"
[[ -f "$REPO/skills/kb-unreal/SKILL.md" ]] || { echo "SkillZ repo not found at $REPO (set SKILLZ_REPO)"; exit 1; }
BRANCH=$(git -C "$REPO" rev-parse --abbrev-ref HEAD)
if [[ "$BRANCH" == "main" ]]; then
  echo "SkillZ is on main: create a branch from origin/main before editing (git -C \"$REPO\" fetch && git -C \"$REPO\" checkout -b kb-unreal/<topic> origin/main)"
fi
echo "Changed in the skill since the branch point:"
git -C "$REPO" status --short -- skills/kb-unreal | sed 's/^/  /'
(cd "$REPO" && ./install.sh kb-unreal) || { echo "install failed"; exit 1; }
if diff -rq "$REPO/skills/kb-unreal" "$DEST" >/dev/null; then
  echo "OK: installed copy at $DEST matches $REPO/skills/kb-unreal (branch $BRANCH)"
else
  echo "MISMATCH between $REPO/skills/kb-unreal and $DEST:"; diff -rq "$REPO/skills/kb-unreal" "$DEST"; exit 1
fi
