"""
Gera relatório de conformidade PEP 8, 257, 484 e 440 para apps Django.

Modos:
  - Um app:        python manage.py gerar_relatorio_pep --app core
  - Todos:         python manage.py gerar_relatorio_pep --all
  - Selecionados:  python manage.py gerar_relatorio_pep --only core usuarios
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

COMMAND_NAME = "gerar_relatorio_pep"
EXCLUDE_DIRS = {"tests", "__tests__", "migrations", "__pycache__"}
EXCLUDE_COMMAND_FILES = {"gerar_relatorio_pep.py"}
EXCLUDE_APPS = {"__pycache__"}
TOP_MISSING_DOCSTRINGS = 25
APPS_PARENT = "apps"

MD_TABLE_SEP_RIGHT = "| --- | ---: |"
MD_TABLE_SEP_STATUS = "| --- | ---: | :--- |"


# =========================================================================
# Dataclasses
# =========================================================================
@dataclass
class SymbolMetrics:
    kind: str
    name: str
    lineno: int
    has_docstring: bool
    hint_level: str  # completo | parcial | sem


@dataclass
class FileMetrics:
    path: str
    loc: int = 0
    lines_over_max: int = 0
    lines_length_eligible: int = 0
    module_has_docstring: bool = False
    symbols: list[SymbolMetrics] = field(default_factory=list)

    @property
    def functions_and_methods(self) -> list[SymbolMetrics]:
        return [
            s for s in self.symbols if s.kind in ("function", "async_function")
        ]

    @property
    def classes(self) -> list[SymbolMetrics]:
        return [s for s in self.symbols if s.kind == "class"]


# =========================================================================
# Caminhos / descoberta
# =========================================================================
def _repo_root() -> Path:
    return Path(cast(Any, settings).BASE_DIR)


def _app_dir(app_name: str) -> Path:
    return _repo_root() / APPS_PARENT / app_name


def discover_django_apps() -> list[str]:
    apps_dir = _repo_root() / APPS_PARENT
    if not apps_dir.exists():
        return []
    apps = []
    for p in sorted(apps_dir.iterdir()):
        if not p.is_dir() or p.name in EXCLUDE_APPS or p.name.startswith("."):
            continue
        if not (p / "__init__.py").exists():
            continue
        apps.append(p.name)
    return apps


def discover_app_python_files(app_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(app_dir.rglob("*.py")):
        parts = set(path.relative_to(app_dir).parts)
        if parts & EXCLUDE_DIRS:
            continue
        if path.name in EXCLUDE_COMMAND_FILES:
            continue
        files.append(path)
    return files


# =========================================================================
# AST / symbols
# =========================================================================
def _hint_level(node: ast.AST) -> str:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return "sem"
    args = [a for a in node.args.args if a.arg not in ("self", "cls")]
    kwonly = list(node.args.kwonlyargs)
    posonly = list(getattr(node.args, "posonlyargs", []))
    all_args = posonly + args + kwonly

    has_return = node.returns is not None
    if not all_args:
        return "completo" if has_return else "sem"

    annotated_args = sum(1 for a in all_args if a.annotation is not None)
    if annotated_args == len(all_args) and has_return:
        return "completo"
    if annotated_args > 0 or has_return:
        return "parcial"
    return "sem"


def _walk_symbols(tree: ast.AST) -> list[SymbolMetrics]:
    symbols: list[SymbolMetrics] = []

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            symbols.append(
                SymbolMetrics(
                    kind="function",
                    name=node.name,
                    lineno=node.lineno,
                    has_docstring=bool(ast.get_docstring(node)),
                    hint_level=_hint_level(node),
                )
            )
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node):
            symbols.append(
                SymbolMetrics(
                    kind="async_function",
                    name=node.name,
                    lineno=node.lineno,
                    has_docstring=bool(ast.get_docstring(node)),
                    hint_level=_hint_level(node),
                )
            )
            self.generic_visit(node)

        def visit_ClassDef(self, node):
            symbols.append(
                SymbolMetrics(
                    kind="class",
                    name=node.name,
                    lineno=node.lineno,
                    has_docstring=bool(ast.get_docstring(node)),
                    hint_level="sem",
                )
            )
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    kind = (
                        "function"
                        if isinstance(item, ast.FunctionDef)
                        else "async_function"
                    )
                    symbols.append(
                        SymbolMetrics(
                            kind=kind,
                            name=f"{node.name}.{item.name}",
                            lineno=item.lineno,
                            has_docstring=bool(ast.get_docstring(item)),
                            hint_level=_hint_level(item),
                        )
                    )

    Visitor().visit(tree)
    return symbols


def analyze_file(
    path: Path, app_dir: Path, max_line_length: int
) -> FileMetrics:
    rel = str(path.relative_to(app_dir))
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    metrics = FileMetrics(path=rel, loc=len(lines))

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        metrics.lines_length_eligible += 1
        if len(line) > max_line_length and "# noqa" not in line:
            metrics.lines_over_max += 1

    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return metrics

    metrics.module_has_docstring = bool(ast.get_docstring(tree))
    metrics.symbols = _walk_symbols(tree)
    return metrics


# =========================================================================
# flake8
# =========================================================================
def run_flake8(app_name: str, repo_root: Path) -> tuple[Counter, list[str]]:
    app_rel = f"{APPS_PARENT}/{app_name}"
    if not (repo_root / app_rel).exists():
        return Counter(), []

    cmd = [sys.executable, "-m", "flake8", app_rel]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return Counter(), ["flake8 não disponível no ambiente"]

    codes: Counter = Counter()
    raw_lines: list[str] = []
    for line in result.stdout.splitlines():
        raw_lines.append(line)
        msg = line.rsplit(":", 1)[-1].strip() if ":" in line else ""
        if msg:
            code = msg.split()[0]
            if len(code) >= 4 and code[0] in "EWFN":
                codes[code] += 1
    return codes, raw_lines


# =========================================================================
# mypy
# =========================================================================

PEP_484 = "PEP 484"
PEP_526 = "PEP 526"
PEP_544 = "PEP 544"
PEP_589 = "PEP 589"
PEP_591 = "PEP 591"
PEP_612 = "PEP 612"

MYPY_CODE_TO_PEP: dict[str, str] = {
    # PEP 484 — Type Hints
    "arg-type": PEP_484,
    "return-value": PEP_484,
    "return": PEP_484,
    "assignment": PEP_484,
    "attr-defined": PEP_484,
    "call-arg": PEP_484,
    "call-overload": PEP_484,
    "index": PEP_484,
    "operator": PEP_484,
    "type-arg": PEP_484,
    "valid-type": PEP_484,
    "override": PEP_484,
    "no-untyped-def": PEP_484,
    "no-untyped-call": PEP_484,
    "no-any-return": PEP_484,
    "no-any-explicit": PEP_484,
    "redundant-cast": PEP_484,
    "type-var": PEP_484,
    "union-attr": PEP_484,
    "has-type": PEP_484,
    "import": PEP_484,
    "import-untyped": PEP_484,
    "import-not-found": PEP_484,
    "name-defined": PEP_484,
    # PEP 526 — Anotações de variáveis
    "annotation-unchecked": PEP_526,
    "var-annotated": PEP_526,
    # PEP 544 — Protocols
    "misc": PEP_544,
    # PEP 589 — TypedDict
    "typeddict-item": PEP_589,
    "typeddict-unknown-key": PEP_589,
    # PEP 591 — Final
    "final-override": PEP_591,
    "cannot-redefine": PEP_591,
    # PEP 612 — ParamSpec
    "valid-newtype": PEP_612,
}

_MYPY_PEP_DESCRIPTIONS: dict[str, str] = {
    PEP_484: "Type Hints",
    PEP_526: "Anotações de variáveis",
    PEP_544: "Protocols",
    PEP_589: "TypedDict",
    PEP_591: "Final",
    PEP_612: "ParamSpec",
}


def _mypy_code_from_line(line: str) -> str | None:
    """Extrai o código entre colchetes no final da linha MyPy, ex: [arg-type]."""
    match = re.search(r"\[([a-z0-9\-]+)\]$", line.strip())
    return match.group(1) if match else None


def run_mypy(
    app_name: str, repo_root: Path
) -> tuple[Counter, list[str], dict[str, int]]:
    """Roda mypy no app.

    Retorna:
        codes       — Counter com 'error' / 'warning' / 'note'
        raw_lines   — linhas brutas do mypy
        pep_summary — dict { 'PEP 484': N, 'PEP 526': N, ... }
    """
    app_rel = f"{APPS_PARENT}/{app_name}"
    if not (repo_root / app_rel).exists():
        return Counter(), [], {}

    cmd = [
        sys.executable,
        "-m",
        "mypy",
        app_rel,
        "--ignore-missing-imports",
        "--no-error-summary",
    ]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return Counter(), ["mypy não disponível no ambiente"], {}

    codes: Counter = Counter()
    pep_counter: Counter = Counter()
    raw_lines: list[str] = []
    for line in result.stdout.splitlines():
        raw_lines.append(line)
        if ": error:" in line:
            codes["error"] += 1
        elif ": warning:" in line:
            codes["warning"] += 1
        elif ": note:" in line:
            codes["note"] += 1

        if ": error:" in line or ": warning:" in line:
            mypy_code = _mypy_code_from_line(line)
            if mypy_code:
                pep = MYPY_CODE_TO_PEP.get(mypy_code, PEP_484)
                pep_counter[pep] += 1

    return codes, raw_lines, dict(pep_counter)


# =========================================================================
# PEP 440
# =========================================================================
def _empty_pep440_result() -> dict[str, Any]:
    return {
        "files_analyzed": [],
        "total_dependency_lines": 0,
        "pypi_valid": 0,
        "git_pins": 0,
        "pinned_with_eq": 0,
        "invalid_lines": [],
        "entries": [],
    }


def _parse_requirement_line(
    line: str, file_name: str, invalid: list[str]
) -> tuple[dict[str, Any], bool, bool]:
    """Retorna (entry, is_git, is_pinned_eq)."""
    from packaging.requirements import InvalidRequirement, Requirement

    entry: dict[str, Any] = {"file": file_name, "line": line}

    if line.startswith("git+"):
        entry["type"] = "git"
        return entry, True, False

    try:
        req = Requirement(line)
        entry["type"] = "pypi"
        entry["name"] = req.name
        pinned = any(str(s).startswith("==") for s in req.specifier)
        return entry, False, pinned
    except InvalidRequirement:
        invalid.append(f"{file_name}: {line}")
        entry["type"] = "invalid"
        return entry, False, False


def analyze_pep440(requirements_dir: Path) -> dict[str, Any]:
    if not requirements_dir.exists():
        return _empty_pep440_result()

    files = sorted(requirements_dir.glob("*.txt"))
    entries: list[dict[str, Any]] = []
    invalid: list[str] = []
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
                line, req_file.name, invalid
            )
            git_pins += int(is_git)
            pinned_eq += int(is_pinned)
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


# =========================================================================
# Utilitários
# =========================================================================
def _pct_float(part: int, whole: int) -> float:
    if whole <= 0:
        return 100.0
    return 100.0 * part / whole


def _pct(part: int, whole: int) -> str:
    if whole == 0:
        return "—"
    return f"{100 * part / whole:.1f}%"


def _status_palavra(pct: float) -> str:
    if pct >= 80:
        return "Bom"
    if pct >= 60:
        return "Regular"
    return "Precisa melhorar"


def _status_emoji(pct: float) -> str:
    if pct >= 80:
        return "🟢 Bom"
    if pct >= 60:
        return "🟡 Regular"
    return "🔴 Precisa melhorar"


def _estimar_horas_ajuste(
    summary: dict[str, Any], flake8_total: int, mypy_errors: int = 0
) -> int:
    horas = (
        flake8_total * 0.005
        + summary["functions_methods_without_docstring"] * 0.05
        + summary["hints_sem"] * 0.03
        + summary["lines_over_79"] * 0.005
        + mypy_errors * 0.1
    )
    return max(1, round(horas))


def _get_git_commit(repo_root: Path) -> str | None:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=True,
        )
        return r.stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


# =========================================================================
# Agregação
# =========================================================================
def aggregate(file_metrics: list[FileMetrics]) -> dict[str, Any]:
    funcs: list[SymbolMetrics] = []
    classes: list[SymbolMetrics] = []
    modules_with_doc = 0
    modules_without_doc = 0
    lines_over = 0
    loc_total = 0
    missing_docstrings: list[tuple[str, SymbolMetrics]] = []

    for fm in file_metrics:
        loc_total += fm.loc
        lines_over += fm.lines_over_max
        if fm.module_has_docstring:
            modules_with_doc += 1
        else:
            modules_without_doc += 1
        funcs.extend(fm.functions_and_methods)
        classes.extend(fm.classes)
        for s in fm.symbols:
            if not s.has_docstring:
                missing_docstrings.append((fm.path, s))

    doc_with = sum(1 for s in funcs + classes if s.has_docstring)
    doc_without = len(funcs) + len(classes) - doc_with
    hints = Counter(s.hint_level for s in funcs)

    return {
        "files_count": len(file_metrics),
        "loc_total": loc_total,
        "lines_over_79": lines_over,
        "lines_length_eligible": sum(
            fm.lines_length_eligible for fm in file_metrics
        ),
        "modules_with_docstring": modules_with_doc,
        "modules_without_docstring": modules_without_doc,
        "functions_methods_total": len(funcs),
        "functions_methods_with_docstring": sum(
            1 for s in funcs if s.has_docstring
        ),
        "functions_methods_without_docstring": len(funcs)
        - sum(1 for s in funcs if s.has_docstring),
        "classes_total": len(classes),
        "classes_with_docstring": sum(1 for s in classes if s.has_docstring),
        "classes_without_docstring": len(classes)
        - sum(1 for s in classes if s.has_docstring),
        "symbols_with_docstring": doc_with,
        "symbols_without_docstring": doc_without,
        "hints_completo": hints.get("completo", 0),
        "hints_parcial": hints.get("parcial", 0),
        "hints_sem": hints.get("sem", 0),
        "missing_docstrings_top": [
            {"path": p, "lineno": s.lineno, "name": s.name, "kind": s.kind}
            for p, s in sorted(
                missing_docstrings, key=lambda x: (x[0], x[1].lineno)
            )[:TOP_MISSING_DOCSTRINGS]
        ],
    }


# =========================================================================
# Renderização (por app)
# =========================================================================
def render_simplified_markdown(
    summary,
    flake8_total,
    mypy_codes,
    mypy_pep_summary,
    pep440,
    meta,
    app_name,
):
    agg = summary
    elig = agg["lines_length_eligible"]
    over = agg["lines_over_79"]
    within = elig - over
    pep8_lines = _pct_float(within, elig)
    sym_total = agg["functions_methods_total"] + agg["classes_total"]
    pep257 = _pct_float(agg["symbols_with_docstring"], sym_total)
    ft = agg["functions_methods_total"]
    pep484_full = _pct_float(agg["hints_completo"], ft)
    pep484_partial = _pct_float(
        agg["hints_completo"] + agg["hints_parcial"], ft
    )
    dep_lines = pep440.get("total_dependency_lines") or 0
    inv_n = len(pep440.get("invalid_lines") or [])
    pep440_pct = _pct_float(dep_lines - inv_n, dep_lines)
    pep8_flake8 = _pct_float(max(elig - flake8_total, 0), elig)
    mypy_errors = mypy_codes.get("error", 0)
    mypy_warnings = mypy_codes.get("warning", 0)
    mypy_pct = _pct_float(max(elig - mypy_errors, 0), elig)

    # Todas as PEPs monitoradas, mesmo com 0 erros
    all_peps = {p: mypy_pep_summary.get(p, 0) for p in _MYPY_PEP_DESCRIPTIONS}
    rows = "\n".join(
        f"| `{pep}` | {_MYPY_PEP_DESCRIPTIONS[pep]} | {n} |"
        for pep, n in sorted(all_peps.items(), key=lambda x: -x[1])
    )
    pep_table = (
        "\n\n#### PEPs verificadas pelo MyPy\n\n"
        "| PEP | Descrição | Erros |\n"
        "| --- | --- | ---: |\n"
        f"{rows}"
    )

    return (
        f"# Resumo PEP — app `{app_name}`\n\n"
        f"Gerado em: **{meta['generated_at']}** · "
        f"Commit: `{meta.get('git_commit', 'N/A')}`\n\n"
        f"## PEP 8\n"
        f"Largura de linha: **{pep8_lines:.1f}%** ({over} violações).\n\n"
        f"Flake8 geral: **{pep8_flake8:.1f}%** ({flake8_total} violações).\n\n"
        f"## PEP 257\n**{pep257:.1f}%** — "
        f"{agg['symbols_with_docstring']}/{sym_total} símbolos com docstring.\n\n"
        f"## PEP 484\nCompleto: **{pep484_full:.1f}%** · "
        f"Completo+parcial: **{pep484_partial:.1f}%** ({ft} funções/métodos).\n\n"
        f"## PEP 440\n**{pep440_pct:.1f}%** — "
        f"{dep_lines - inv_n}/{dep_lines} linhas parseáveis; inválidas: {inv_n}.\n\n"
        f"## MyPy\n**{mypy_pct:.1f}%** — "
        f"{mypy_errors} erro(s), {mypy_warnings} aviso(s)."
        f"{pep_table}\n"
    )


def render_simplified_txt(
    summary,
    flake8_total,
    mypy_codes,
    mypy_pep_summary,
    pep440,
    meta,
    max_line_length,
    *,
    service_name,
):
    agg = summary
    elig = agg["lines_length_eligible"]
    over = agg["lines_over_79"]
    within = elig - over
    pep8_lines = _pct_float(within, elig)
    pep8_flake8 = _pct_float(max(elig - flake8_total, 0), elig)
    sym_total = agg["functions_methods_total"] + agg["classes_total"]
    pep257 = _pct_float(agg["symbols_with_docstring"], sym_total)
    ft = agg["functions_methods_total"]
    pep484_full = _pct_float(agg["hints_completo"], ft)
    pep484_partial = _pct_float(
        agg["hints_completo"] + agg["hints_parcial"], ft
    )
    dep_lines = pep440.get("total_dependency_lines") or 0
    inv_n = len(pep440.get("invalid_lines") or [])
    pep440_pct = _pct_float(dep_lines - inv_n, dep_lines)
    mypy_errors = mypy_codes.get("error", 0)
    mypy_warnings = mypy_codes.get("warning", 0)
    mypy_pct = _pct_float(max(elig - mypy_errors, 0), elig)
    horas = _estimar_horas_ajuste(agg, flake8_total, mypy_errors)

    # Todas as PEPs monitoradas, mesmo com 0 erros
    all_peps = {p: mypy_pep_summary.get(p, 0) for p in _MYPY_PEP_DESCRIPTIONS}
    pep_lines = "\n  PEPs verificadas pelo MyPy:\n"
    for pep, n in sorted(all_peps.items(), key=lambda x: -x[1]):
        desc = _MYPY_PEP_DESCRIPTIONS.get(pep, "—")
        pep_lines += f"    {pep} ({desc}): {n} erro(s)\n"

    return (
        "================================================================\n"
        "  RESUMO DE BOAS PRÁTICAS DO CÓDIGO PYTHON (PEPs)\n"
        f"  {service_name}\n"
        "================================================================\n\n"
        f"Data: {meta['generated_at']}\n"
        f"Commit: {meta.get('git_commit', 'não informado')}\n\n"
        f"PEP 8 (linhas)  — {pep8_lines:.1f}% ({_status_palavra(pep8_lines)}) — "
        f"{over} linha(s) acima de {max_line_length} chars.\n"
        f"PEP 8 (flake8)  — {pep8_flake8:.1f}% ({_status_palavra(pep8_flake8)}) — "
        f"{flake8_total} violações.\n"
        f"PEP 257 — {pep257:.1f}% ({_status_palavra(pep257)}) — "
        f"{agg['symbols_with_docstring']}/{sym_total} documentados.\n"
        f"PEP 484 — completo {pep484_full:.1f}% / com parcial {pep484_partial:.1f}% "
        f"({_status_palavra(pep484_partial)}) — {agg['hints_completo']}/{ft} completos.\n"
        f"PEP 440 — {pep440_pct:.1f}% ({_status_palavra(pep440_pct)}) — "
        f"{dep_lines - inv_n}/{dep_lines} linhas válidas, {inv_n} inválidas.\n"
        f"MyPy    — {mypy_pct:.1f}% ({_status_palavra(mypy_pct)}) — "
        f"{mypy_errors} erro(s), {mypy_warnings} aviso(s).\n"
        f"{pep_lines}\n"
        f"Estimativa grosseira de ajuste: ~{horas}h\n"
    )


def render_markdown(
    summary,
    file_metrics,
    flake8_codes,
    flake8_lines,
    mypy_codes,
    mypy_lines,
    mypy_pep_summary,
    pep440,
    meta,
    max_line_length,
    app_name,
):
    agg = summary
    mypy_errors = mypy_codes.get("error", 0)
    mypy_warnings = mypy_codes.get("warning", 0)
    elig = agg["lines_length_eligible"]
    mypy_pct = _pct_float(max(elig - mypy_errors, 0), elig)

    lines = [
        f"# Relatório PEP — app `{app_name}`",
        "",
        f"Gerado em: **{meta['generated_at']}**  ",
        f"Commit: `{meta.get('git_commit', 'N/A')}`  ",
        f"Limite linha (PEP 8): **{max_line_length}**",
        "",
        "## Resumo",
        "| Métrica | Valor | % |",
        "| --- | ---: | ---: |",
        f"| Arquivos | {agg['files_count']} | — |",
        f"| LOC | {agg['loc_total']} | — |",
        (
            f"| Linhas > {max_line_length} | {agg['lines_over_79']} | "
            f"{_pct(agg['lines_over_79'], agg['loc_total'])} |"
        ),
        f"| Funções/métodos | {agg['functions_methods_total']} | — |",
        (
            f"| Com docstring | {agg['functions_methods_with_docstring']} | "
            f"{_pct(agg['functions_methods_with_docstring'], agg['functions_methods_total'])} |"  # noqa: E501
        ),
        (
            f"| Classes c/ docstring | "
            f"{agg['classes_with_docstring']}/{agg['classes_total']} | "
            f"{_pct(agg['classes_with_docstring'], agg['classes_total'])} |"
        ),
        (
            f"| Hints completos | {agg['hints_completo']} | "
            f"{_pct(agg['hints_completo'], agg['functions_methods_total'])} |"
        ),
        f"| flake8 | {sum(flake8_codes.values())} | — |",
        f"| mypy erros | {mypy_errors} | — |",
        f"| mypy avisos | {mypy_warnings} | — |",
        "",
    ]

    if flake8_codes:
        lines += [
            "### Top flake8",
            "",
            "| Código | Ocorrências |",
            MD_TABLE_SEP_RIGHT,
        ]
        for code, count in flake8_codes.most_common(10):
            lines.append(f"| `{code}` | {count} |")
        lines.append("")

    if flake8_lines:
        lines += [
            "<details><summary>Primeiras 30 linhas flake8</summary>",
            "",
            "```",
        ]
        lines += flake8_lines[:30]
        lines += ["```", "<​/details>", ""]

    if mypy_codes:
        lines += [
            "### MyPy",
            "",
            f"Conformidade: **{mypy_pct:.1f}%** — "
            f"{mypy_errors} erro(s), {mypy_warnings} aviso(s).",
            "",
        ]

    # Sempre exibe todas as PEPs monitoradas, mesmo com 0 erros
    all_peps = {p: mypy_pep_summary.get(p, 0) for p in _MYPY_PEP_DESCRIPTIONS}
    lines += [
        "#### PEPs verificadas pelo MyPy",
        "",
        "| PEP | Descrição | Erros |",
        "| --- | --- | ---: |",
    ]
    for pep, count in sorted(all_peps.items(), key=lambda x: -x[1]):
        desc = _MYPY_PEP_DESCRIPTIONS.get(pep, "—")
        lines.append(f"| `{pep}` | {desc} | {count} |")
    lines.append("")

    if mypy_lines:
        lines += [
            "<details><summary>Primeiras 30 linhas mypy</summary>",
            "",
            "```",
        ]
        lines += mypy_lines[:30]
        lines += ["```", "<​/details>", ""]

    lines += [
        "## Símbolos sem docstring (top)",
        "",
        "| Arquivo | Linha | Símbolo | Tipo |",
        "| --- | ---: | --- | --- |",
    ]
    for item in agg["missing_docstrings_top"]:
        lines.append(
            f"| `{item['path']}` | {item['lineno']} | "
            f"`{item['name']}` | {item['kind']} |"
        )

    lines += [
        "",
        "## PEP 440",
        f"- Arquivos: {', '.join(pep440.get('files_analyzed', []))}",
        f"- Linhas: **{pep440.get('total_dependency_lines', 0)}**",
        f"- PyPI válidas: **{pep440.get('pypi_valid', 0)}**",
        f"- git+: **{pep440.get('git_pins', 0)}**",
        f"- ==: **{pep440.get('pinned_with_eq', 0)}**",
        f"- Inválidas: **{len(pep440.get('invalid_lines', []))}**",
        "",
        "## Por arquivo",
        "| Arquivo | LOC | >max | Funções | Doc % | Hints completos % |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for fm in sorted(file_metrics, key=lambda x: x.path):
        funcs = fm.functions_and_methods
        n = len(funcs)
        doc_pct = (
            _pct(sum(1 for s in funcs if s.has_docstring), n) if n else "—"
        )
        hint_pct = (
            _pct(sum(1 for s in funcs if s.hint_level == "completo"), n)
            if n
            else "—"
        )
        lines.append(
            f"| `{fm.path}` | {fm.loc} | {fm.lines_over_max} | "
            f"{n} | {doc_pct} | {hint_pct} |"
        )
    lines += [
        "",
        f"*Gerado por `python manage.py {COMMAND_NAME} --app {app_name}`*",
        "",
    ]
    return "\n".join(lines)


def build_simple_summary(
    summary, flake8_total, mypy_codes, pep440, max_line_length
):
    agg = summary
    elig = agg["lines_length_eligible"]
    over = agg["lines_over_79"]
    within = elig - over
    dep_lines = pep440.get("total_dependency_lines") or 0
    inv_n = len(pep440.get("invalid_lines") or [])
    sym_total = agg["functions_methods_total"] + agg["classes_total"]
    ft = agg["functions_methods_total"]
    flake8_pct = _pct_float(max(elig - flake8_total, 0), elig)
    mypy_errors = mypy_codes.get("error", 0)
    mypy_warnings = mypy_codes.get("warning", 0)
    mypy_pct = _pct_float(max(elig - mypy_errors, 0), elig)
    return {
        "pep8_line_width_compliance_pct": round(_pct_float(within, elig), 2),
        "pep8_lines_over_max": over,
        "pep8_flake8_compliance_pct": round(flake8_pct, 2),
        "pep8_flake8_violations": flake8_total,
        "pep257_docstring_compliance_pct": round(
            _pct_float(agg["symbols_with_docstring"], sym_total), 2
        ),
        "pep484_full_hints_pct": round(
            _pct_float(agg["hints_completo"], ft), 2
        ),
        "pep484_full_or_partial_pct": round(
            _pct_float(agg["hints_completo"] + agg["hints_parcial"], ft), 2
        ),
        "pep440_requirement_lines_parseable_pct": round(
            _pct_float(dep_lines - inv_n, dep_lines), 2
        ),
        "mypy_errors": mypy_errors,
        "mypy_warnings": mypy_warnings,
        "mypy_compliance_pct": round(mypy_pct, 2),
        "max_line_length": max_line_length,
    }


def build_json_payload(
    summary,
    file_metrics,
    flake8_codes,
    mypy_codes,
    mypy_pep_summary,
    pep440,
    meta,
    max_line_length,
    app_name,
):
    by_file = []

    for fm in file_metrics:
        funcs = fm.functions_and_methods
        by_file.append(
            {
                "path": fm.path,
                "loc": fm.loc,
                "lines_over_max": fm.lines_over_max,
                "module_has_docstring": fm.module_has_docstring,
                "functions_count": len(funcs),
                "functions_with_docstring": sum(
                    1 for s in funcs if s.has_docstring
                ),
                "hints_completo": sum(
                    1 for s in funcs if s.hint_level == "completo"
                ),
                "hints_parcial": sum(
                    1 for s in funcs if s.hint_level == "parcial"
                ),
                "hints_sem": sum(1 for s in funcs if s.hint_level == "sem"),
            }
        )

    flake8_total = sum(flake8_codes.values())
    mypy_errors = mypy_codes.get("error", 0)
    mypy_warnings = mypy_codes.get("warning", 0)

    elig = summary["lines_length_eligible"]
    over = summary["lines_over_79"]

    pep8_line_pct = _pct_float(elig - over, elig)
    pep8_flake8_pct = _pct_float(max(elig - flake8_total, 0), elig)
    mypy_pct = _pct_float(max(elig - mypy_errors, 0), elig)

    # Todas as PEPs monitoradas no JSON, mesmo com 0 erros
    all_peps = {p: mypy_pep_summary.get(p, 0) for p in _MYPY_PEP_DESCRIPTIONS}

    return {
        "generated_at": meta["generated_at"],
        "command": meta["command"],
        "git_commit": meta.get("git_commit"),
        "app": app_name,
        "max_line_length": max_line_length,
        "summary": summary,
        "simple": build_simple_summary(
            summary, flake8_total, mypy_codes, pep440, max_line_length
        ),
        "pep8": {
            "line_length": {
                "compliance_pct": round(pep8_line_pct, 2),
                "violations": over,
            },
            "flake8": {
                "compliance_pct": round(pep8_flake8_pct, 2),
                "violations": flake8_total,
                "breakdown": dict(flake8_codes.most_common()),
            },
        },
        "mypy": {
            "compliance_pct": round(mypy_pct, 2),
            "errors": mypy_errors,
            "warnings": mypy_warnings,
            "breakdown": dict(mypy_codes),
            "pep_breakdown": all_peps,
        },
        "flake8": dict(flake8_codes.most_common()),
        "pep440": pep440,
        "by_file": by_file,
    }


# =========================================================================
# Execução por app
# =========================================================================
def _build_meta(repo_root: Path, app_name: str) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "command": f"python manage.py {COMMAND_NAME} --app {app_name}",
        "git_commit": _get_git_commit(repo_root),
    }


def _write_app_outputs(
    output_dir: Path,
    payload_args: dict[str, Any],
    service_name: str,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    md_path = output_dir / "RELATORIO_PEP.md"
    md_simple_path = output_dir / "RELATORIO_PEP_RESUMIDO.md"
    txt_simple_path = output_dir / "RELATORIO_PEP_RESUMIDO.txt"
    json_path = output_dir / "relatorio_pep.json"

    md_path.write_text(
        render_markdown(**payload_args["render_md"]), encoding="utf-8"
    )
    md_simple_path.write_text(
        render_simplified_markdown(**payload_args["render_md_simple"]),
        encoding="utf-8",
    )
    txt_simple_path.write_text(
        render_simplified_txt(
            **payload_args["render_txt_simple"], service_name=service_name
        ),
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps(
            build_json_payload(**payload_args["json"]),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return {
        "md": md_path,
        "md_simple": md_simple_path,
        "txt_simple": txt_simple_path,
        "json": json_path,
    }


def _build_payload_args(
    summary,
    file_metrics,
    flake8_codes,
    flake8_lines,
    mypy_codes,
    mypy_lines,
    mypy_pep_summary,
    pep440,
    meta,
    max_line_length,
    app_name,
    flake8_total,
) -> dict[str, dict[str, Any]]:
    return {
        "render_md": {
            "summary": summary,
            "file_metrics": file_metrics,
            "flake8_codes": flake8_codes,
            "flake8_lines": flake8_lines,
            "mypy_codes": mypy_codes,
            "mypy_lines": mypy_lines,
            "mypy_pep_summary": mypy_pep_summary,
            "pep440": pep440,
            "meta": meta,
            "max_line_length": max_line_length,
            "app_name": app_name,
        },
        "render_md_simple": {
            "summary": summary,
            "flake8_total": flake8_total,
            "mypy_codes": mypy_codes,
            "mypy_pep_summary": mypy_pep_summary,
            "pep440": pep440,
            "meta": meta,
            "app_name": app_name,
        },
        "render_txt_simple": {
            "summary": summary,
            "flake8_total": flake8_total,
            "mypy_codes": mypy_codes,
            "mypy_pep_summary": mypy_pep_summary,
            "pep440": pep440,
            "meta": meta,
            "max_line_length": max_line_length,
        },
        "json": {
            "summary": summary,
            "file_metrics": file_metrics,
            "flake8_codes": flake8_codes,
            "mypy_codes": mypy_codes,
            "mypy_pep_summary": mypy_pep_summary,
            "pep440": pep440,
            "meta": meta,
            "max_line_length": max_line_length,
            "app_name": app_name,
        },
    }


def run_for_app(
    app_name: str,
    *,
    repo_root: Path,
    max_line_length: int,
    output_dir: Path | None,
    service_name: str,
) -> dict[str, Any]:
    """Executa análise completa de um app e grava arquivos."""
    app_dir = _app_dir(app_name)
    if not app_dir.exists():
        raise CommandError(f"App não encontrado: {app_dir}")

    out_dir = output_dir if output_dir else app_dir / "docs"
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir

    py_files = discover_app_python_files(app_dir)
    file_metrics = [
        analyze_file(p, app_dir, max_line_length) for p in py_files
    ]
    summary = aggregate(file_metrics)
    flake8_codes, flake8_lines = run_flake8(app_name, repo_root)
    mypy_codes, mypy_lines, mypy_pep_summary = run_mypy(app_name, repo_root)
    pep440 = analyze_pep440(repo_root / "requirements")
    meta = _build_meta(repo_root, app_name)
    flake8_total = sum(flake8_codes.values())

    payload_args = _build_payload_args(
        summary,
        file_metrics,
        flake8_codes,
        flake8_lines,
        mypy_codes,
        mypy_lines,
        mypy_pep_summary,
        pep440,
        meta,
        max_line_length,
        app_name,
        flake8_total,
    )

    paths = _write_app_outputs(out_dir, payload_args, service_name)
    json_payload = build_json_payload(**payload_args["json"])

    return {
        "app": app_name,
        "paths": paths,
        "payload": json_payload,
        "summary": summary,
        "flake8_total": flake8_total,
        "mypy_codes": mypy_codes,
    }


# =========================================================================
# Consolidação (geral)
# =========================================================================
def _sum_totals(per_app: list[dict[str, Any]]) -> dict[str, int]:
    totals = {
        "files": 0,
        "loc": 0,
        "lines_over": 0,
        "lines_eligible": 0,
        "funcs": 0,
        "funcs_doc": 0,
        "classes": 0,
        "classes_doc": 0,
        "symbols_doc": 0,
        "symbols_total": 0,
        "hints_completo": 0,
        "hints_parcial": 0,
        "hints_sem": 0,
        "flake8": 0,
        "mypy_errors": 0,
        "mypy_warnings": 0,
    }
    for d in per_app:
        s = d["payload"]["summary"]
        totals["files"] += s["files_count"]
        totals["loc"] += s["loc_total"]
        totals["lines_over"] += s["lines_over_79"]
        totals["lines_eligible"] += s["lines_length_eligible"]
        totals["funcs"] += s["functions_methods_total"]
        totals["funcs_doc"] += s["functions_methods_with_docstring"]
        totals["classes"] += s["classes_total"]
        totals["classes_doc"] += s["classes_with_docstring"]
        totals["symbols_doc"] += s["symbols_with_docstring"]
        totals["symbols_total"] += (
            s["functions_methods_total"] + s["classes_total"]
        )
        totals["hints_completo"] += s["hints_completo"]
        totals["hints_parcial"] += s["hints_parcial"]
        totals["hints_sem"] += s["hints_sem"]
        totals["flake8"] += d["flake8_total"]
        mypy = d["payload"].get("mypy", {})
        totals["mypy_errors"] += mypy.get("errors", 0)
        totals["mypy_warnings"] += mypy.get("warnings", 0)
    return totals


def _aggregate_flake8_codes(per_app: list[dict[str, Any]]) -> dict[str, int]:
    agg: dict[str, int] = {}
    for d in per_app:
        for code, n in d["payload"].get("flake8", {}).items():
            agg[code] = agg.get(code, 0) + n
    return agg


def _compute_compliance(
    totals: dict[str, int], pep440: dict[str, Any]
) -> dict[str, float]:
    elig = totals["lines_eligible"]
    within = elig - totals["lines_over"]
    flake8_total = totals["flake8"]
    mypy_errors = totals["mypy_errors"]

    dep_lines = pep440.get("total_dependency_lines") or 0
    inv_n = len(pep440.get("invalid_lines") or [])

    return {
        "pep8_line_length": _pct_float(within, elig),
        "pep8_flake8": _pct_float(max(elig - flake8_total, 0), elig),
        "pep257": _pct_float(totals["symbols_doc"], totals["symbols_total"]),
        "pep484_full": _pct_float(totals["hints_completo"], totals["funcs"]),
        "pep484_partial": _pct_float(
            totals["hints_completo"] + totals["hints_parcial"],
            totals["funcs"],
        ),
        "pep440": _pct_float(dep_lines - inv_n, dep_lines),
        "mypy": _pct_float(max(elig - mypy_errors, 0), elig),
    }


def _render_consolidated_md(
    per_app: list[dict[str, Any]],
    totals: dict[str, int],
    compliance: dict[str, float],
    agg_codes: dict[str, int],
    max_len: int,
    now: str,
) -> str:
    md = [
        "# Relatório PEP — Consolidado",
        "",
        f"Gerado em: **{now}**  ",
        f"Apps analisados: {', '.join(d['app'] for d in per_app)}  ",
        f"Limite linha (PEP 8): **{max_len}**",
        "",
        "## Aderência geral",
        "",
        "| PEP | Aderência | Situação |",
        MD_TABLE_SEP_STATUS,
        (
            f"| PEP 8 (largura linha) | "
            f"**{compliance['pep8_line_length']:.1f}%** | "
            f"{_status_emoji(compliance['pep8_line_length'])} |"
        ),
        (
            f"| PEP 8 (flake8 geral) | "
            f"**{compliance['pep8_flake8']:.1f}%** | "
            f"{_status_emoji(compliance['pep8_flake8'])} |"
        ),
        (
            f"| PEP 257 (docstrings) | "
            f"**{compliance['pep257']:.1f}%** | "
            f"{_status_emoji(compliance['pep257'])} |"
        ),
        (
            f"| PEP 484 (hints completos) | "
            f"**{compliance['pep484_full']:.1f}%** | "
            f"{_status_emoji(compliance['pep484_full'])} |"
        ),
        (
            f"| PEP 484 (completo+parcial) | "
            f"**{compliance['pep484_partial']:.1f}%** | "
            f"{_status_emoji(compliance['pep484_partial'])} |"
        ),
        (
            f"| PEP 440 (requirements) | "
            f"**{compliance['pep440']:.1f}%** | "
            f"{_status_emoji(compliance['pep440'])} |"
        ),
        (
            f"| MyPy (type errors) | "
            f"**{compliance['mypy']:.1f}%** | "
            f"{_status_emoji(compliance['mypy'])} |"
        ),
        "",
        "## Totais",
        "",
        "| Métrica | Valor |",
        MD_TABLE_SEP_RIGHT,
        f"| Arquivos | {totals['files']} |",
        f"| LOC | {totals['loc']} |",
        f"| Linhas > {max_len} | {totals['lines_over']} |",
        f"| Funções/métodos | {totals['funcs']} |",
        f"| Funções com docstring | {totals['funcs_doc']} |",
        f"| Classes | {totals['classes']} |",
        f"| Classes com docstring | {totals['classes_doc']} |",
        f"| Hints completos | {totals['hints_completo']} |",
        f"| Hints parciais | {totals['hints_parcial']} |",
        f"| Sem hints | {totals['hints_sem']} |",
        f"| flake8 (total) | {totals['flake8']} |",
        f"| mypy erros | {totals['mypy_errors']} |",
        f"| mypy avisos | {totals['mypy_warnings']} |",
        "",
        "## Por app",
        "",
        (
            "| App | Arquivos | Funções | Sem doc | "
            "Linhas >max | flake8 | MyPy erros | "
            "PEP8 Linhas % | PEP8 Flake8 % | "
            "PEP257 % | PEP484 % | MyPy % |"
        ),
        (
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | "
            "---: | ---: | ---: | ---: | ---: |"
        ),
    ]

    for d in per_app:
        s = d["payload"]["summary"]
        simple = d["payload"].get("simple", {})
        mypy = d["payload"].get("mypy", {})

        md.append(
            f"| `{d['app']}` | "
            f"{s['files_count']} | "
            f"{s['functions_methods_total']} | "
            f"{s['functions_methods_without_docstring']} | "
            f"{s['lines_over_79']} | "
            f"{d['flake8_total']} | "
            f"{mypy.get('errors', 0)} | "
            f"{simple.get('pep8_line_width_compliance_pct', 0):.1f}% | "
            f"{simple.get('pep8_flake8_compliance_pct', 0):.1f}% | "
            f"{simple.get('pep257_docstring_compliance_pct', 0):.1f}% | "
            f"{simple.get('pep484_full_hints_pct', 0):.1f}% | "
            f"{simple.get('mypy_compliance_pct', 0):.1f}% |"
        )

    md += [
        "",
        "## Top códigos flake8 (agregado)",
        "",
    ]

    if agg_codes:
        md += ["| Código | Ocorrências |", MD_TABLE_SEP_RIGHT]
        for code, n in sorted(agg_codes.items(), key=lambda x: -x[1])[:15]:
            md.append(f"| `{code}` | {n} |")

    md += [
        "",
        "_Relatórios detalhados por app em `apps/<app>/docs/`._",
    ]

    return "\n".join(md) + "\n"


def consolidate(
    per_app: list[dict[str, Any]],
    out_dir: Path,
    max_len: int,
) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    totals = _sum_totals(per_app)
    agg_codes = _aggregate_flake8_codes(per_app)
    pep440 = per_app[0]["payload"].get("pep440", {})
    compliance = _compute_compliance(totals, pep440)
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    md = _render_consolidated_md(
        per_app, totals, compliance, agg_codes, max_len, now
    )

    md_path = out_dir / "RELATORIO_PEP_GERAL.md"
    json_path = out_dir / "relatorio_pep_geral.json"
    md_path.write_text(md, encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "generated_at": now,
                "apps": [d["app"] for d in per_app],
                "totals": totals,
                "pep_compliance": {
                    k: round(v, 2) for k, v in compliance.items()
                },
                "flake8_top": dict(
                    sorted(agg_codes.items(), key=lambda x: -x[1])
                ),
                "per_app": [d["payload"] for d in per_app],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return {"md": md_path, "json": json_path}


# =========================================================================
# Django Command
# =========================================================================
class Command(BaseCommand):
    help = (
        "Gera relatório PEP 8/257/484/440 + MyPy de um app Django "
        "(MD + JSON + TXT). Suporta --all e --only para múltiplos apps."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--app",
            default="core",
            help="Nome do app dentro de apps/ (ignorado com --all/--only).",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Roda em todos os apps em apps/ e gera consolidado.",
        )
        parser.add_argument(
            "--only",
            nargs="*",
            default=None,
            help="Lista de apps específicos; gera consolidado.",
        )
        parser.add_argument(
            "--output-dir",
            default=None,
            help=(
                "Saída por-app (default: apps/<app>/docs). "
                "No modo consolidado, é o diretório do relatório geral "
                "(default: docs/)."
            ),
        )
        parser.add_argument("--max-line-length", type=int, default=79)
        parser.add_argument("--service-name", default="SME-SIGNA-BACKEND")

    def _resolve_apps(self, options) -> tuple[list[str], bool]:
        """Retorna (lista_de_apps, modo_consolidado)."""
        if options["only"]:
            return list(options["only"]), True
        if options["all"]:
            return discover_django_apps(), True
        return [options["app"]], False

    def _run_single(self, app_name: str, options, repo_root: Path) -> None:
        output_dir = (
            Path(options["output_dir"]) if options["output_dir"] else None
        )
        result = run_for_app(
            app_name,
            repo_root=repo_root,
            max_line_length=options["max_line_length"],
            output_dir=output_dir,
            service_name=options["service_name"],
        )
        paths = result["paths"]
        s = result["summary"]
        mypy = result["mypy_codes"]
        self.stdout.write(self.style.SUCCESS(f"MD:   {paths['md']}"))
        self.stdout.write(
            self.style.SUCCESS(f"MD resumido: {paths['md_simple']}")
        )
        self.stdout.write(
            self.style.SUCCESS(f"TXT resumido: {paths['txt_simple']}")
        )
        self.stdout.write(self.style.SUCCESS(f"JSON: {paths['json']}"))
        self.stdout.write(
            f"Arquivos: {s['files_count']} | "
            f"Funções: {s['functions_methods_total']} | "
            f"Sem doc: {s['functions_methods_without_docstring']} | "
            f"Linhas >{options['max_line_length']}: {s['lines_over_79']} | "
            f"flake8: {result['flake8_total']} | "
            f"mypy erros: {mypy.get('error', 0)}"
        )

    def _run_many(self, apps: list[str], options, repo_root: Path) -> None:
        if not apps:
            self.stdout.write(
                self.style.WARNING("Nenhum app encontrado em apps/")
            )
            return

        self.stdout.write(
            self.style.NOTICE(f"Apps a analisar: {', '.join(apps)}")
        )

        per_app: list[dict[str, Any]] = []
        for app in apps:
            self.stdout.write(f"\n→ Rodando para: {app}")
            try:
                result = run_for_app(
                    app,
                    repo_root=repo_root,
                    max_line_length=options["max_line_length"],
                    output_dir=None,
                    service_name=options["service_name"],
                )
            except Exception as exc:  # noqa: BLE001
                self.stdout.write(self.style.ERROR(f"  Falhou: {exc}"))
                continue
            per_app.append(result)

        if not per_app:
            self.stdout.write(self.style.ERROR("Nenhum dado coletado."))
            return

        out_dir = Path(options["output_dir"] or "docs")
        if not out_dir.is_absolute():
            out_dir = repo_root / out_dir

        paths = consolidate(per_app, out_dir, options["max_line_length"])
        self.stdout.write(
            self.style.SUCCESS(f"\nMD consolidado:   {paths['md']}")
        )
        self.stdout.write(
            self.style.SUCCESS(f"JSON consolidado: {paths['json']}")
        )

    def handle(self, *args, **options):
        repo_root = _repo_root()
        apps, consolidated = self._resolve_apps(options)
        if consolidated:
            self._run_many(apps, options, repo_root)
        else:
            self._run_single(apps[0], options, repo_root)
