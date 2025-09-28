#!/usr/bin/env bash
set -euo pipefail
if [ $# -lt 4 ]; then
  echo "usage: new_bar_doc.sh <outline|flashcards|distinctions> <subject> <slug> <Title...>"
  exit 1
fi
type="$1"; subject="$2"; slug="$3"; shift 3
title="$*"
date=$(date +%F)

case "$type" in
  outline) tpl=templates/outline.md; subdir=outlines ;;
  flashcards|cards) tpl=templates/flashcards.md; subdir=questions ;;
  distinctions) tpl=templates/outline.md; subdir=distinctions ;;
  *) echo "type must be: outline|flashcards|distinctions"; exit 1 ;;
esac

out="docs/tn/bar/${subdir}/${subject}/tn-bar-${subject}-${slug}.md"
mkdir -p "$(dirname "$out")"

sed -e "s/{Subject}/$subject/g" \
    -e "s/{Topic}/$title/g" \
    -e "s/{subject}/$subject/g" \
    -e "s/{slug}/$slug/g" \
    -e "s/{DATE}/$date/g" "$tpl" > "$out"

echo "[ok] wrote $out"
tools/validate_meta.py
python3 tools/upsert_md.py "$out"
