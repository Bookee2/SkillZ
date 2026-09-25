#!/usr/bin/env bash
#
# Install the SkillZ skills into ~/.claude so Claude Code picks them up
# in every project.
#
#   ./install.sh            install (backs up anything it replaces)
#   ./install.sh --dry-run  show what would happen, write nothing
#
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${CLAUDE_HOME:-$HOME/.claude}"
SKILLS=(kb-spec kb-build kb-review kb-merge kb-motion)

DRY_RUN=0
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=1

say()  { printf '%s\n' "$*"; }
run()  { if (( DRY_RUN )); then say "  would: $*"; else "$@"; fi; }

# Back up an existing path to <path>.bak.<n>, keeping earlier backups.
backup() {
  local path="$1" n=1
  [[ -e "$path" ]] || return 0
  while [[ -e "$path.bak.$n" ]]; do n=$(( n + 1 )); done
  say "  backing up existing $path -> $(basename "$path").bak.$n"
  run mv "$path" "$path.bak.$n"
}

(( DRY_RUN )) && say "Dry run — nothing will be written." && say ""
say "Installing SkillZ into $DEST"
say ""

say "Skills:"
for skill in "${SKILLS[@]}"; do
  src="$SRC/skills/$skill"
  if [[ ! -f "$src/SKILL.md" ]]; then
    say "  ERROR: $src/SKILL.md not found" >&2
    exit 1
  fi
  backup "$DEST/skills/$skill"
  run mkdir -p "$DEST/skills"
  run cp -R "$src" "$DEST/skills/$skill"
  say "  /$skill"
done

say ""
say "Shared resolver:"
backup "$DEST/kb-loop/resolve-target.md"
run mkdir -p "$DEST/kb-loop"
run cp "$SRC/kb-loop/resolve-target.md" "$DEST/kb-loop/resolve-target.md"
say "  kb-loop/resolve-target.md"

say ""
if (( DRY_RUN )); then
  say "Dry run complete. Re-run without --dry-run to install."
else
  say "Done. Start a new Claude Code session, then bind a repo by adding"
  say ".claude/linear.json to it — see the README."
fi
