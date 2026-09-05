#!/usr/bin/env bash
set -Eeuo pipefail

search_root="${1:-.}"
pattern="(BEGIN ([A-Z0-9][A-Z0-9 -]{0,63} )?PRIVATE KEY|[\"']?Authorization[\"']?[[:space:]]*:[[:space:]]*[\"']?[[:space:]]*Bearer[[:space:]]+[-A-Za-z0-9._~+/]{16,}=*|[\"']?[A-Za-z0-9_-]*client[_-]?secret[\"']?[[:space:]]*[:=][[:space:]]*[^[:space:]<]+|[\"']?(REDIS_PASSWORD|REDIS_EXPORTER_BASIC_AUTH_PASSWORD)[\"']?[[:space:]]*[:=][[:space:]]*[\"']?[^[:space:]<\"'\${}]{4,})"
path_list="$(mktemp)"
trap 'rm -f -- "$path_list"' EXIT

set +e
find "$search_root" \
  \( -path "$search_root/.git" -o -path "$search_root/upstream" \) -prune -o \
  \( -type f -o -type l \) -print0 > "$path_list"
find_status=$?
set -e
if (( find_status != 0 )); then
  echo "Secret scan traversal failed (find status ${find_status})." >&2
  exit "$find_status"
fi

while IFS= read -r -d '' path; do
  if [[ -L "$path" ]]; then
    echo "Secret scan refuses symbolic link: ${path}" >&2
    exit 2
  fi
done < "$path_list"

while IFS= read -r -d '' path; do
  set +e
  LC_ALL=C grep -aEiqz "$pattern" -- "$path"
  scan_status=$?
  if (( scan_status == 1 )); then
    # Parse Redis values separately: length and leading metacharacters do not
    # make a password safe. Only a complete braced environment reference is
    # a placeholder (and single quotes make that reference a literal).
    python3 - "$path" <<'PY'
import pathlib
import re
import sys

try:
    text = pathlib.Path(sys.argv[1]).read_bytes().decode("latin-1")
except OSError:
    raise SystemExit(2)
assignment = re.compile(
    r'''(?i)(?<![A-Za-z0-9_])["']?(?:REDIS_PASSWORD|REDIS_EXPORTER_BASIC_AUTH_PASSWORD)["']?[ \t]*[:=][ \t]*'''
)
quoted = re.compile(r'''(?s)(?:"(?:\\.|[^"\\])*"|'(?:''|[^'])*')''')
for match in assignment.finditer(text):
    tail = text[match.end():]
    if not tail or tail[0] in "\r\n":
        continue
    quote = tail[0] if tail[0] in "\"'" else ""
    if quote:
        token = quoted.match(tail)
        if token is None:
            raise SystemExit(0)
        value = token.group()[1:-1]
        remainder = tail[token.end():]
        if remainder and remainder[0] not in " \t\r\n,]}#":
            raise SystemExit(0)
    else:
        token = re.match(r"[^\r\n \t,]+", tail)
        if token is None:
            continue
        value = token.group()
    if not value:
        continue
    if quote != "'" and re.fullmatch(r"\$\{[A-Z_][A-Z0-9_]*\}", value):
        continue
    raise SystemExit(0)
raise SystemExit(1)
PY
    scan_status=$?
  fi
  set -e
  case "$scan_status" in
    0)
      echo 'Control-plane secret pattern detected.' >&2
      exit 1
      ;;
    1)
      ;;
    *)
      echo "Secret scan failed before completing (scanner status ${scan_status})." >&2
      exit "$scan_status"
      ;;
  esac
done < "$path_list"
