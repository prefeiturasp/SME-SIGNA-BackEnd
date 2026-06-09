#!/usr/bin/env python3
"""Verificador simples de PEP 440 para usar em pre-commit.

Lê arquivos em `requirements/*.txt`, ignora linhas vazias, comentários e `-r`,
tenta parsear cada linha com `packaging.Requirement` e reporta linhas
inválidas, git+ pins e pins com `==`.

Sai com código 1 se houver linhas inválidas, 0 caso contrário.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

from packaging.requirements import InvalidRequirement, Requirement


def _parse_requirement_line(
    line: str, file_name: str
) -> Tuple[Dict[str, Any], bool, bool]:
    """Parse requirement line and return metadata with git and pinned flags."""
    # `InvalidRequirement` and `Requirement` are imported at module level; if
    # `packaging` is missing the ImportError will propagate to the caller.
    entry: Dict[str, Any] = {"file": file_name, "line": line}
    if line.startswith("git+"):
        entry["type"] = "git"
        return entry, True, False

    try:
        req = Requirement(line)
    except InvalidRequirement:
        entry["type"] = "invalid"
        return entry, False, False

    entry["type"] = "pypi"
    entry["name"] = req.name
    pinned = any(str(s).startswith("==") for s in req.specifier)
    return entry, False, pinned


def analyze_pep440(requirements_dir: Path) -> Dict[str, Any]:
    """Analyze PEP 440 compliance across all requirements files."""
    if not requirements_dir.exists():
        return {
            "files_analyzed": [],
            "total_dependency_lines": 0,
            "pypi_valid": 0,
            "git_pins": 0,
            "pinned_with_eq": 0,
            "invalid_lines": [],
            "entries": [],
        }

    files = sorted(requirements_dir.glob("*.txt"))
    entries: List[Dict[str, Any]] = []
    invalid: List[str] = []
    git_pins = 0
    pinned_eq = 0
    total = 0

    for req_file in files:
        for raw_line in req_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith("-r"):
                continue
            total += 1
            entry, is_git, is_pinned = _parse_requirement_line(
                line, req_file.name
            )
            git_pins += int(is_git)
            pinned_eq += int(is_pinned)
            if entry.get("type") == "invalid":
                invalid.append(f"{req_file.name}: {line}")
            entries.append(entry)

    return {
        "files_analyzed": [f.name for f in files],
        "total_dependency_lines": total,
        "pypi_valid": sum(1 for e in entries if e.get("type") == "pypi"),
        "git_pins": git_pins,
        "pinned_with_eq": pinned_eq,
        "invalid_lines": invalid,
        "entries": entries,
    }


def main() -> int:
    """Run PEP 440 analysis and return exit code."""
    repo_root = Path(__file__).resolve().parent.parent
    req_dir = repo_root / "requirements"
    if not req_dir.exists():
        print("No requirements/ directory found; skipping PEP 440 check.")
        return 0

    res = analyze_pep440(req_dir)

    print("PEP 440 check summary:")
    print(f"  Files: {', '.join(res['files_analyzed'])}")
    print(f"  Total lines: {res['total_dependency_lines']}")
    print(f"  PyPI valid: {res['pypi_valid']}")
    print(f"  git+: {res['git_pins']}")
    print(f"  == pinned: {res['pinned_with_eq']}")
    print(f"  Invalid lines: {len(res['invalid_lines'])}")
    if res["invalid_lines"]:
        print("\nInvalid requirement lines:")
        for invalid_line in res["invalid_lines"]:
            print("  ", invalid_line)

    return 1 if res["invalid_lines"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
