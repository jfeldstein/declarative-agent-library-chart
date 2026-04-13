#!/usr/bin/env python3
"""Validate OpenSpec promoted spec requirement IDs and traceability matrix consistency.

Traceability: [CFHA-VER-001]

Rules (see ``openspec/specs/cfha-requirement-verification/spec.md``, ``docs/adrs/0003-spec-test-traceability.md``,
and ``docs/spec-test-traceability.md``):

- Every ``### Requirement:`` heading under ``openspec/specs/*/spec.md`` must include a bracketed
  ``[CFHA-REQ-...]`` or ``[CFHA-VER-...]`` identifier **on the same line** as ``### Requirement:``.
- ``docs/spec-test-traceability.md`` must define a markdown table with one row per promoted ID.
- Active (non-waived) rows: evidence paths must exist. Waived rows: see ADR 0003 (approver + reason required;
  evidence may be ``-``).

Strict mode (default): for Python evidence, if the matrix uses ``file.py::function``, the ID must appear in
**that function's** docstring; if only ``file.py`` is listed, the ID must appear anywhere in the file. For Helm
unittest YAML, the ID must appear in a ``#`` comment in the file.

Environment:

- ``CFHA_TRACEABILITY_STRICT=0`` — skip content checks for Python/YAML evidence (paths must still exist for
  active rows). Use only temporarily while backfilling annotations.
"""

from __future__ import annotations

import ast
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPECS_DIR = ROOT / "openspec" / "specs"
MATRIX_PATH = ROOT / "docs" / "spec-test-traceability.md"

# ID must appear on the same line as ### Requirement:
ID_PATTERN = re.compile(r"\[(CFHA-REQ-[A-Z0-9-]+-\d{3}|CFHA-VER-\d{3})\]")
MATRIX_ID_CELL = re.compile(
    r"^\s*(\[(?:CFHA-REQ-[A-Z0-9-]+-\d{3}|CFHA-VER-\d{3})\])\s*$",
)
GITHUB_LOGIN = re.compile(
    r"^(?!-)(?!.*--)[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,37}[a-zA-Z0-9]$|^[a-zA-Z0-9]$",
)


def _strict() -> bool:
    return os.environ.get("CFHA_TRACEABILITY_STRICT", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _is_waiver_blank(cell: str) -> bool:
    t = cell.strip()
    return t == "" or t == "-"


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
                    f"error: requirement heading without ID on same line in "
                    f"{spec.relative_to(ROOT)}:\n  {line}",
                    file=sys.stderr,
                )
                sys.exit(1)
            rid = m.group(0)
            if rid in found:
                print(f"error: duplicate requirement ID {rid} in specs", file=sys.stderr)
                sys.exit(1)
            found[rid] = spec
    return found


def parse_matrix_table(text: str) -> dict[str, tuple[str, str, str, str, str]]:
    """Map ID (with brackets) -> (spec, evidence, tier, waiver_approver, waiver_reason)."""
    rows: dict[str, tuple[str, str, str, str, str]] = {}
    lines = text.splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("| ID |") and "Waiver approver" in line:
            header_idx = i
            break
    if header_idx is None:
        print(
            f"error: matrix table header not found in {MATRIX_PATH.relative_to(ROOT)} "
            "(expected '| ID |' row including 'Waiver approver')",
            file=sys.stderr,
        )
        sys.exit(1)

    for line in lines[header_idx + 2 :]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            break
        if re.match(r"^\|\s*-+", stripped):
            continue
        parts = [p.strip() for p in stripped.strip("|").split("|")]
        if len(parts) != 6:
            print(
                f"error: matrix row must have 6 columns (got {len(parts)}): {stripped!r}",
                file=sys.stderr,
            )
            sys.exit(1)
        rid_cell, spec_cell, ev_cell, tier_cell, wa_cell, wr_cell = parts
        m = MATRIX_ID_CELL.match(rid_cell.replace("`", "").strip())
        if not m:
            print(f"error: bad ID cell {rid_cell!r}", file=sys.stderr)
            sys.exit(1)
        rid = m.group(1)
        if rid in rows:
            print(f"error: duplicate matrix row for {rid}", file=sys.stderr)
            sys.exit(1)
        rows[rid] = (spec_cell, ev_cell, tier_cell, wa_cell, wr_cell)
    return rows


def split_evidence(cell: str) -> list[str]:
    raw = cell.replace("`", "")
    parts: list[str] = []
    for chunk in raw.split(","):
        t = chunk.strip()
        if t:
            parts.append(t)
    return parts


def evidence_path_for_token(token: str) -> tuple[Path, str | None]:
    """Return (path, pytest_function_or_none)."""
    func: str | None = None
    if "::" in token:
        path_part, func = token.split("::", 1)
        path_part = path_part.strip()
        func = func.strip()
    else:
        path_part = token.strip()
    p = (ROOT / path_part).resolve()
    try:
        p.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"evidence path escapes repo root: {token}") from exc
    return p, func


def is_examples_helm_test_yaml(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    parts = rel.parts
    return "tests" in parts and path.suffix in {".yaml", ".yml"} and (
        len(parts) > 0 and parts[0] == "examples"
    )


def is_runtime_pytest(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    parts = rel.parts
    return (
        len(parts) >= 2
        and parts[0] == "runtime"
        and parts[1] == "tests"
        and path.suffix == ".py"
    )


def strict_text_evidence(path: Path) -> bool:
    """Files that must contain the row's requirement ID when strict mode is on."""
    if path.suffix.lower() in {".md", ".json"}:
        return True
    if path.suffix in {".yaml", ".yml"}:
        return True
    if path.suffix == ".py":
        return True
    if path.name == "ci.yml" and "workflows" in path.parts:
        return True
    return False


def _pytest_function_docstring(path: Path, func_name: str) -> str | None:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
            return ast.get_docstring(node)
    return None


def id_in_pytest_evidence(path: Path, func_name: str | None, rid: str) -> bool:
    if func_name:
        doc = _pytest_function_docstring(path, func_name)
        return bool(doc and rid in doc)
    body = path.read_text(encoding="utf-8")
    return rid in body


def validate_waiver(approver: str, reason: str) -> None:
    if not GITHUB_LOGIN.match(approver):
        print(
            f"error: waiver approver {approver!r} must look like a GitHub username "
            "(letters, digits, hyphens; no placeholders)",
            file=sys.stderr,
        )
        sys.exit(1)
    if len(reason.strip()) < 10:
        print(
            "error: waiver reason must be at least 10 characters (explain deferral clearly)",
            file=sys.stderr,
        )
        sys.exit(1)
    low = approver.lower()
    for bad in ("pending", "todo", "tbd", "none", "unknown", "n-a"):
        if low == bad or low.replace("-", "") == bad.replace("-", ""):
            print(f"error: waiver approver cannot be a placeholder like {approver!r}", file=sys.stderr)
            sys.exit(1)


def main() -> None:
    spec_ids = collect_spec_ids()
    matrix_raw = MATRIX_PATH.read_text(encoding="utf-8")
    matrix = parse_matrix_table(matrix_raw)
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
    for rid, (spec_cell, ev_cell, tier_cell, wa_cell, wr_cell) in sorted(matrix.items()):
        spec_path = spec_ids[rid]
        rel_spec = spec_path.relative_to(ROOT).as_posix()
        if rel_spec not in spec_cell.replace("`", ""):
            print(
                f"error: matrix spec cell for {rid} must reference {rel_spec} (got {spec_cell!r})",
                file=sys.stderr,
            )
            sys.exit(1)

        wa = wa_cell.strip()
        wr = wr_cell.strip()
        waived = not (_is_waiver_blank(wa_cell) and _is_waiver_blank(wr_cell))
        if waived:
            if _is_waiver_blank(wa_cell) or _is_waiver_blank(wr_cell):
                print(
                    f"error: {rid} waiver row must set both approver and reason (or both empty/- for active)",
                    file=sys.stderr,
                )
                sys.exit(1)
            validate_waiver(wa, wr)

        tokens = split_evidence(ev_cell)
        if not waived and not tokens:
            print(f"error: {rid} has empty evidence in matrix", file=sys.stderr)
            sys.exit(1)
        if waived and not tokens:
            continue

        for token in tokens:
            if token.strip() == "-":
                continue
            try:
                p, py_func = evidence_path_for_token(token)
            except ValueError as e:
                print(f"error: {rid} evidence {token!r}: {e}", file=sys.stderr)
                sys.exit(1)
            if not p.is_file():
                print(
                    f"error: {rid} evidence file missing: {p.relative_to(ROOT)} (from {token!r})",
                    file=sys.stderr,
                )
                sys.exit(1)
            if waived:
                continue
            if strict and strict_text_evidence(p):
                if is_runtime_pytest(p):
                    if not id_in_pytest_evidence(p, py_func, rid):
                        hint = (
                            f"function {py_func!r} docstring"
                            if py_func
                            else "module/class/function docstring"
                        )
                        print(
                            f"error: {rid} not found in evidence {p.relative_to(ROOT)} ({hint}) "
                            f"— add docstring with the ID, narrow matrix to file.py::test_name, "
                            f"or set CFHA_TRACEABILITY_STRICT=0 temporarily.",
                            file=sys.stderr,
                        )
                        sys.exit(1)
                elif is_examples_helm_test_yaml(p):
                    body = p.read_text(encoding="utf-8")
                    if rid not in body:
                        print(
                            f"error: {rid} not found in evidence file "
                            f"{p.relative_to(ROOT)} — add a YAML # comment with the ID, "
                            f"or set CFHA_TRACEABILITY_STRICT=0 temporarily.",
                            file=sys.stderr,
                        )
                        sys.exit(1)
                else:
                    body = p.read_text(encoding="utf-8")
                    if rid not in body:
                        print(
                            f"error: {rid} not found in evidence file {p.relative_to(ROOT)} "
                            f"— add a comment or title field containing the ID, "
                            f"or set CFHA_TRACEABILITY_STRICT=0 temporarily.",
                            file=sys.stderr,
                        )
                        sys.exit(1)

        _ = tier_cell  # human-facing tier; not machine-validated

    print(
        f"ok: {len(spec_ids)} promoted requirements, matrix aligned "
        f"(strict={'on' if strict else 'off'})",
    )


if __name__ == "__main__":
    if not MATRIX_PATH.is_file():
        print(f"error: missing matrix {MATRIX_PATH}", file=sys.stderr)
        sys.exit(2)
    main()
