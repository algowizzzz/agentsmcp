#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
KEEP_MANIFEST="$ROOT_DIR/scripts/keep_model_summary_manifest.txt"
DRY_RUN="${DRY_RUN:-1}"

if [[ ! -f "$KEEP_MANIFEST" ]]; then
  echo "Keep manifest not found: $KEEP_MANIFEST" >&2
  exit 1
fi

# Build keep set (normalize to absolute paths)
KEEP_ITEMS=()
while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in
    ''|'#'*) continue ;;
    *) KEEP_ITEMS+=("$line") ;;
  esac
done < "$KEEP_MANIFEST"

KEEP_PATHS=()
norm_path() {
  local p="$1"
  # strip trailing slashes
  while [[ "$p" != "/" && "$p" == */ ]]; do p="${p%/}"; done
  printf '%s' "$p"
}
for item in "${KEEP_ITEMS[@]}"; do
  abs=$(norm_path "$ROOT_DIR/$item")
  KEEP_PATHS+=("$abs")
  # Also keep parent dirs
  while true; do
    abs_dir="$(dirname "$abs")"
    [[ "$abs_dir" == "$ROOT_DIR" || "$abs_dir" == "/" ]] && break
    KEEP_PATHS+=("$abs_dir")
    abs="$abs_dir"
  done
done

is_kept() {
  local path="$1"
  path=$(norm_path "$path")
  for kp in "${KEEP_PATHS[@]}"; do
    kp=$(norm_path "$kp")
    case "$path/" in
      "$kp/"|$kp/*) return 0 ;;
    esac
  done
  return 1
}

# List top-level items (excluding venv and .git safety)
DELETE_LIST=()
while IFS= read -r -d '' p; do
  name="$(basename "$p")"
  case "$name" in
    .git|.gitignore|.cursorignore|.DS_Store|venv) continue ;;
  esac
  if ! is_kept "$p"; then
    DELETE_LIST+=("$p")
  fi
done < <(find "$ROOT_DIR" -mindepth 1 -maxdepth 1 -print0)

# Also scan subtrees to remove non-kept items under kept parents
while IFS= read -r -d '' p; do
  case "$p" in
    *"$ROOT_DIR/.git"*|*"$ROOT_DIR/venv"*) continue ;;
  esac
  if ! is_kept "$p"; then
    DELETE_LIST+=("$p")
  fi
done < <(find "$ROOT_DIR" -mindepth 2 -print0)

# De-duplicate and sort
DELETE_UNIQ=$(printf '%s\n' "${DELETE_LIST[@]}" | awk 'NF' | sort -u)

if [[ "$DRY_RUN" == "1" ]]; then
  echo "[DRY_RUN] Would delete the following paths:";
  printf ' - %s\n' $DELETE_UNIQ
  echo "Set DRY_RUN=0 to execute."
  exit 0
fi

read -r -p "This will delete files. Type YES to proceed: " ans || true
if [[ "$ans" != "YES" ]]; then
  echo "Aborted."
  exit 1
fi

# Delete (files first, then dirs)
FILES=()
DIRS=()
while IFS= read -r p; do
  [[ -z "$p" ]] && continue
  if [[ -d "$p" ]]; then DIRS+=("$p"); else FILES+=("$p"); fi
done <<< "$DELETE_UNIQ"

if ((${#FILES[@]})); then
  printf '%s\0' "${FILES[@]}" | xargs -0 rm -f -- 2>/dev/null || true
fi
if ((${#DIRS[@]})); then
  # delete deepest dirs first
  printf '%s\n' "${DIRS[@]}" | awk '{ print length, $0 }' | sort -rn | cut -d" " -f2- | while IFS= read -r d; do rm -rf -- "$d" 2>/dev/null || true; done
fi

echo "Prune complete."
