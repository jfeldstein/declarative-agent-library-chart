#!/usr/bin/env python3
"""Validate OpenSpec promoted spec requirement IDs and traceability matrix consistency.

Traceability: [CFHA-VER-001]

Rules (see openspec/specs/cfha-requirement-verification/spec.md, docs/adrs/0003-spec-test-traceability.md, and docs/spec-test-traceability.md):

- Every ``### Requirement:`` heading under ``openspec/specs/*/spec.md`` must include a bracketed
  ``[CFHA-REQ-...]`` or ``[CFHA-VER-...]`` identifier on the same line.
- ``docs/spec-test-traceability.md`` must define a markdown table with one row per promoted ID.
- Evidence paths in the matrix must exist under the repository root.

Strict mode (default): for evidence tokens pointing at ``runtime/tests/**/*.py`` or
``examples/**/tests/**/*.yaml``, the file content must include the row's requirement ID string
(including brackets) so reviewers and automation can see the linkage.

Environment:

- ``CFHA_TRACEABILITY_STRICT=0`` — skip the content check for Python/YAML evidence files (paths must
  still exist). Use only temporarily while backfilling annotations; default PR CI should stay strict.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPECS_DIR = ROOT / "openspec" / "specs"
MATRIX_PATH = ROOT / "docs" / "spec-test-traceability.md"

REQ_HEADING = re.compile(r"^### Requirement:\s*(.*)$")
ID_PATTERN = re.compile(r"\[(CFHA-REQ-[A-Z0-9-]+-\d{3}|CFHA-VER-\d{3})\]")
MATRIX_ROW = re.compile(
    r"^\|\s*(\[(?:CFHA-REQ-[A-Z0-9-]+-\d{3}|CFHA-VER-\d{3})\])\s*\|"
    r"\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*$",
)


def _strict() -> bool:
    return os.environ.get("CFHA_TRACEABILITY_STRICT", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def collect_spec_ids() -> dict[str, Path]:
    found: dict[str, Path] = {}
    if not SPECS_DIR.is_dir():
        print(f"error: missing specs directory {SPECS_DIR}", file=sys.stderr)
        sys.exit(2)
    for spec in sorted(SPECS_DIR.glob("*/spec.md")):
        text = spec.read_text(encoding="utf-8")
        for line in text.splitlines():
            if not line.startswith("### Requirement:"):
                continue
            m = ID_PATTERN.search(line)
            if not m:
                print(
                    f"error: requirement heading without ID in {spec.relative_to(ROOT)}:\n  {line}",
                    file=sys.stderr,
                )
                sys.exit(1)
            rid = m.group(0)  # include brackets to match matrix column
            if rid in found:
                print(f"error: duplicate requirement ID {rid} in specs", file=sys.stderr)
                sys.exit(1)
            found[rid] = spec
    return found


def parse_matrix() -> dict[str, tuple[str, str, str]]:
    """Map ID (with brackets) -> (spec cell, evidence cell, tier cell)."""
    text = MATRIX_PATH.read_text(encoding="utf-8")
    rows: dict[str, tuple[str, str, str]] = {}
    in_table = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("| ID |"):
            in_table = True
            continue
        if not in_table or not stripped.startswith("|"):
            continue
        if re.match(r"^\|\s*-+", stripped):
            continue
        m = MATRIX_ROW.match(line.rstrip())
        if not m:
            continue
        rid, spec_cell, ev_cell, tier_cell = m.groups()
        rid = rid.strip()
        if rid in rows:
            print(f"error: duplicate matrix row for {rid}", file=sys.stderr)
            sys.exit(1)
        rows[rid] = (spec_cell.strip(), ev_cell.strip(), tier_cell.strip())
    return rows


def split_evidence(cell: str) -> list[str]:
    raw = cell.replace("`", "")
    parts: list[str] = []
    for chunk in raw.split(","):
        t = chunk.strip()
        if t:
            parts.append(t)
    return parts


def evidence_path_for_token(token: str) -> Path:
    if "::" in token:
        token = token.split("::", 1)[0].strip()
    p = (ROOT / token).resolve()
    try:
        p.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"evidence path escapes repo root: {token}") from exc
    return p


def needs_id_in_content(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    parts = rel.parts
    if len(parts) >= 2 and parts[0] == "runtime" and parts[1] == "tests" and path.suffix == ".py":
        return True
    if "tests" in parts and path.suffix in {".yaml", ".yml"} and parts[0] == "examples":
        return True
    return False


def main() -> None:
    spec_ids = collect_spec_ids()
    matrix = parse_matrix()
    spec_keys = set(spec_ids.keys())
    matrix_keys = set(matrix.keys())

    missing_rows = spec_keys - matrix_keys
    if missing_rows:
        for rid in sorted(missing_rows):
            print(
                f"error: promoted spec ID {rid} missing from {MATRIX_PATH.relative_to(ROOT)}",
                file=sys.stderr,
            )
        sys.exit(1)

    extra = matrix_keys - spec_keys
    if extra:
        for rid in sorted(extra):
            print(
                f"error: matrix ID {rid} not found under {SPECS_DIR.relative_to(ROOT)}",
                file=sys.stderr,
            )
        sys.exit(1)

    strict = _strict()
    for rid, (spec_cell, ev_cell, tier_cell) in sorted(matrix.items()):
        spec_path = spec_ids[rid]
        rel_spec = spec_path.relative_to(ROOT).as_posix()
        if rel_spec not in spec_cell.replace("`", ""):
            print(
                f"error: matrix spec cell for {rid} must reference {rel_spec} (got {spec_cell!r})",
                file=sys.stderr,
            )
            sys.exit(1)

        tokens = split_evidence(ev_cell)
        if not tokens:
            print(f"error: {rid} has empty evidence in matrix", file=sys.stderr)
            sys.exit(1)

        for token in tokens:
            try:
                p = evidence_path_for_token(token)
            except ValueError as e:
                print(f"error: {rid} evidence {token!r}: {e}", file=sys.stderr)
                sys.exit(1)
            if not p.is_file():
                print(
                    f"error: {rid} evidence file missing: {p.relative_to(ROOT)} (from {token!r})",
                    file=sys.stderr,
                )
                sys.exit(1)
            if strict and needs_id_in_content(p):
                body = p.read_text(encoding="utf-8")
                if rid not in body:
                    print(
                        f"error: {rid} not found in evidence file "
                        f"{p.relative_to(ROOT)} — add a docstring or YAML comment "
                        f"containing the ID, or set CFHA_TRACEABILITY_STRICT=0 temporarily.",
                        file=sys.stderr,
                    )
                    sys.exit(1)

        _ = tier_cell  # documented for humans; not machine-validated

    print(
        f"ok: {len(spec_ids)} promoted requirements, matrix aligned "
        f"(strict={'on' if strict else 'off'})",
    )


if __name__ == "__main__":
    if not MATRIX_PATH.is_file():
        print(f"error: missing matrix {MATRIX_PATH}", file=sys.stderr)
        sys.exit(2)
    main()
