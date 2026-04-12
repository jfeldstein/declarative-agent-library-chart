#!/usr/bin/env bash
# Fail if two ADR files share the same NNNN prefix (docs/adrs/NNNN-slug.md).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ADR_DIR="${ROOT}/docs/adrs"

if [[ ! -d "$ADR_DIR" ]]; then
  echo "error: missing ${ADR_DIR}" >&2
  exit 1
fi

(
  cd "$ADR_DIR"
  shopt -s nullglob
  files=( [0-9][0-9][0-9][0-9]-*.md )
  if [[ ${#files[@]} -eq 0 ]]; then
    echo "error: no ADR files matching NNNN-*.md in docs/adrs" >&2
    exit 1
  fi

  seen_nums=()
  seen_files=()
  for f in "${files[@]}"; do
    num="${f:0:4}"
    if [[ ! "$num" =~ ^[0-9]{4}$ ]]; then
      echo "error: invalid ADR filename (expected NNNN-slug.md): $f" >&2
      exit 1
    fi
    for ((i = 0; i < ${#seen_nums[@]}; i++)); do
      if [[ "${seen_nums[$i]}" == "$num" ]]; then
        echo "error: duplicate ADR number ${num}: ${seen_files[$i]} and $f" >&2
        exit 1
      fi
    done
    seen_nums+=("$num")
    seen_files+=("$f")
  done
)

echo "ADR numbering OK (${ADR_DIR})"
