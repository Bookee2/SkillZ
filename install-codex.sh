#!/usr/bin/env bash
# Install Codex-compatible SkillZ skills for use from any project.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${CODEX_HOME:-$HOME/.codex}/skills"
DRY_RUN=0
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=1

if [[ ! -f "$SRC/skills/tg-render/SKILL.md" ]]; then
  printf 'Missing tg-render skill source\n' >&2
  exit 1
fi
if (( DRY_RUN )); then
  printf 'Would install %s at %s\n' "$SRC/skills/tg-render" "$DEST/tg-render"
  exit 0
fi
mkdir -p "$DEST"
if [[ -e "$DEST/tg-render" ]]; then
  n=1
  while [[ -e "$DEST/tg-render.bak.$n" ]]; do n=$((n+1)); done
  mv "$DEST/tg-render" "$DEST/tg-render.bak.$n"
  printf 'Backed up previous tg-render to %s\n' "$DEST/tg-render.bak.$n"
fi
cp -R "$SRC/skills/tg-render" "$DEST/tg-render"
printf 'Installed tg-render at %s\n' "$DEST/tg-render"
