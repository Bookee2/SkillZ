#!/usr/bin/env bash
#
# Install the SkillZ skills into ~/.claude so Claude Code picks them up
# in every project.
#
#   ./install.sh                  install everything (backs up anything it replaces)
#   ./install.sh tg-render        install only the named skills
#   ./install.sh --dry-run [...]  show what would happen, write nothing
#
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${CLAUDE_HOME:-$HOME/.claude}"
SKILLS=(kb-spec kb-build kb-review kb-merge tg-render kb-motion kb-secbrain)

DRY_RUN=0
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=1 && shift
(( $# )) && SKILLS=("$@")

say()  { printf '%s\n' "$*"; }
run()  { if (( DRY_RUN )); then say "  would: $*"; else "$@"; fi; }

# Move an existing path to $DEST/skillz-backups/<name>.bak.<n>, keeping
# earlier backups. Backups must live outside skills/: Claude Code loads every
# folder there that has a SKILL.md, so a backup beside the skill shows up as a
# duplicate skill.
BACKUPS="$DEST/skillz-backups"
backup() {
  local path="$1" n=1 name
  [[ -e "$path" ]] || return 0
  name="$(basename "$path")"
  while [[ -e "$BACKUPS/$name.bak.$n" ]]; do n=$(( n + 1 )); done
  say "  backing up existing $path -> skillz-backups/$name.bak.$n"
  run mkdir -p "$BACKUPS"
  run mv "$path" "$BACKUPS/$name.bak.$n"
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

# The kb loop's shared resolver, whenever a kb-* skill is being installed.
if [[ " ${SKILLS[*]} " == *" kb-"* ]]; then
  say ""
  say "Shared resolver:"
  backup "$DEST/kb-loop/resolve-target.md"
  run mkdir -p "$DEST/kb-loop"
  run cp "$SRC/kb-loop/resolve-target.md" "$DEST/kb-loop/resolve-target.md"
  say "  kb-loop/resolve-target.md"
fi

say ""
if (( DRY_RUN )); then
  say "Dry run complete. Re-run without --dry-run to install."
else
  say "Done. Start a new Claude Code session, then bind a repo by adding"
  say ".claude/linear.json to it — see the README."
fi
