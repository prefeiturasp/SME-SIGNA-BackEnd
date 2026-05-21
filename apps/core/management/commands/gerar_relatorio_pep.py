"""
Gera relatório de conformidade PEP 8, 257, 484 e 440 para um app Django.
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

COMMAND_NAME = "gerar_relatorio_pep"
EXCLUDE_DIRS = {"tests", "migrations", "__pycache__"}
EXCLUDE_COMMAND_FILES = {"gerar_relatorio_pep.py"}
TOP_MISSING_DOCSTRINGS = 25
APPS_PARENT = "apps"  # pasta que contém os apps Django


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
    symbols: List[SymbolMetrics] = field(default_factory=list)

    @property
    def functions_and_methods(self) -> List[SymbolMetrics]:
        return [
            s for s in self.symbols if s.kind in ("function", "async_function")
        ]

    @property
    def classes(self) -> List[SymbolMetrics]:
        return [s for s in self.symbols if s.kind == "class"]


def _repo_root() -> Path:
    return Path(settings.BASE_DIR)


def _app_dir(app_name: str) -> Path:
    return _repo_root() / APPS_PARENT / app_name


def discover_app_python_files(app_dir: Path) -> List[Path]:
    files: List[Path] = []
    for path in sorted(app_dir.rglob("*.py")):
        parts = set(path.relative_to(app_dir).parts)
        if parts & EXCLUDE_DIRS:
            continue
        if path.name in EXCLUDE_COMMAND_FILES:
            continue
        files.append(path)
    return files


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


def _walk_symbols(tree: ast.AST, filepath: Path) -> List[SymbolMetrics]:
    symbols: List[SymbolMetrics] = []

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
        if len(line) > max_line_length:
            metrics.lines_over_max += 1

    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return metrics

    metrics.module_has_docstring = bool(ast.get_docstring(tree))
    metrics.symbols = _walk_symbols(tree, path)
    return metrics


def run_flake8(app_name: str, repo_root: Path) -> Tuple[Counter, List[str]]:
    app_rel = f"{APPS_PARENT}/{app_name}"
    if not (repo_root / app_rel).exists():
        return Counter(), []

    cmd = [
        sys.executable,
        "-m",
        "flake8",
        "--max-line-length=79",
        "--extend-exclude=migrations,tests,__pycache__",
        app_rel,
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
        return Counter(), ["flake8 não disponível no ambiente"]

    codes: Counter = Counter()
    raw_lines: List[str] = []
    for line in result.stdout.splitlines():
        raw_lines.append(line)
        msg = line.rsplit(":", 1)[-1].strip() if ":" in line else ""
        if msg:
            code = msg.split()[0]
            if len(code) >= 4 and code[0] in "EWFN":
                codes[code] += 1
    return codes, raw_lines


def analyze_pep440(requirements_dir: Path) -> Dict[str, Any]:
    from packaging.requirements import InvalidRequirement, Requirement

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
            entry = {"file": req_file.name, "line": line}
            if line.startswith("git+"):
                git_pins += 1
                entry["type"] = "git"
                entries.append(entry)
                continue
            try:
                req = Requirement(line)
                entry["type"] = "pypi"
                entry["name"] = req.name
                if any(str(s).startswith("==") for s in req.specifier):
                    pinned_eq += 1
                entries.append(entry)
            except InvalidRequirement:
                invalid.append(f"{req_file.name}: {line}")
                entry["type"] = "invalid"
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


def _estimar_horas_ajuste(summary: Dict[str, Any], flake8_total: int) -> int:
    horas = (
        flake8_total * 0.005
        + summary["functions_methods_without_docstring"] * 0.05
        + summary["hints_sem"] * 0.03
        + summary["lines_over_79"] * 0.005
    )
    return max(1, round(horas))


def aggregate(file_metrics: List[FileMetrics]) -> Dict[str, Any]:
    funcs: List[SymbolMetrics] = []
    classes: List[SymbolMetrics] = []
    modules_with_doc = 0
    modules_without_doc = 0
    lines_over = 0
    loc_total = 0
    missing_docstrings: List[Tuple[str, SymbolMetrics]] = []

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


def render_simplified_markdown(
    summary, flake8_total, pep440, meta, max_line_length, app_name
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

    return (
        f"# Resumo PEP — app `{app_name}`\n\n"
        f"Gerado em: **{meta['generated_at']}** · Commit: `{meta.get('git_commit','N/A')}`\n\n"
        f"## PEP 8\n**{pep8_lines:.1f}%** — {within}/{elig} linhas ≤ {max_line_length} chars; "
        f"flake8: {flake8_total} avisos.\n\n"
        f"## PEP 257\n**{pep257:.1f}%** — {agg['symbols_with_docstring']}/{sym_total} símbolos com docstring.\n\n"
        f"## PEP 484\nCompleto: **{pep484_full:.1f}%** · Completo+parcial: **{pep484_partial:.1f}%** "
        f"({ft} funções/métodos).\n\n"
        f"## PEP 440\n**{pep440_pct:.1f}%** — {dep_lines - inv_n}/{dep_lines} linhas parseáveis; inválidas: {inv_n}.\n"
    )


def render_simplified_txt(
    summary, flake8_total, pep440, meta, max_line_length, *, service_name
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
    horas = _estimar_horas_ajuste(agg, flake8_total)

    return (
        "================================================================\n"
        "  RESUMO DE BOAS PRÁTICAS DO CÓDIGO PYTHON (PEPs)\n"
        f"  {service_name}\n"
        "================================================================\n\n"
        f"Data: {meta['generated_at']}\n"
        f"Commit: {meta.get('git_commit', 'não informado')}\n\n"
        f"PEP 8  — {pep8_lines:.1f}% ({_status_palavra(pep8_lines)}) — "
        f"{over} linha(s) acima de {max_line_length} chars de {elig}.\n"
        f"PEP 257 — {pep257:.1f}% ({_status_palavra(pep257)}) — "
        f"{agg['symbols_with_docstring']}/{sym_total} documentados.\n"
        f"PEP 484 — completo {pep484_full:.1f}% / com parcial {pep484_partial:.1f}% "
        f"({_status_palavra(pep484_partial)}) — {agg['hints_completo']}/{ft} completos.\n"
        f"PEP 440 — {pep440_pct:.1f}% ({_status_palavra(pep440_pct)}) — "
        f"{dep_lines - inv_n}/{dep_lines} linhas válidas, {inv_n} inválidas.\n\n"
        f"Estimativa grosseira de ajuste: ~{horas}h\n"
    )


def render_markdown(
    summary,
    file_metrics,
    flake8_codes,
    flake8_lines,
    pep440,
    meta,
    max_line_length,
    app_name,
):
    agg = summary
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
        f"| Linhas > {max_line_length} | {agg['lines_over_79']} | {_pct(agg['lines_over_79'], agg['loc_total'])} |",
        f"| Funções/métodos | {agg['functions_methods_total']} | — |",
        f"| Com docstring | {agg['functions_methods_with_docstring']} | "
        f"{_pct(agg['functions_methods_with_docstring'], agg['functions_methods_total'])} |",
        f"| Classes c/ docstring | {agg['classes_with_docstring']}/{agg['classes_total']} | "
        f"{_pct(agg['classes_with_docstring'], agg['classes_total'])} |",
        f"| Hints completos | {agg['hints_completo']} | "
        f"{_pct(agg['hints_completo'], agg['functions_methods_total'])} |",
        f"| flake8 | {sum(flake8_codes.values())} | — |",
        "",
    ]
    if flake8_codes:
        lines += [
            "### Top flake8",
            "",
            "| Código | Ocorrências |",
            "| --- | ---: |",
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

    lines += [
        "## Símbolos sem docstring (top)",
        "",
        "| Arquivo | Linha | Símbolo | Tipo |",
        "| --- | ---: | --- | --- |",
    ]
    for item in agg["missing_docstrings_top"]:
        lines.append(
            f"| `{item['path']}` | {item['lineno']} | `{item['name']}` | {item['kind']} |"
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
            f"| `{fm.path}` | {fm.loc} | {fm.lines_over_max} | {n} | {doc_pct} | {hint_pct} |"
        )
    lines += [
        "",
        f"*Gerado por `python manage.py {COMMAND_NAME} --app {app_name}`*",
        "",
    ]
    return "\n".join(lines)


def build_simple_summary(summary, flake8_total, pep440, max_line_length):
    agg = summary
    elig = agg["lines_length_eligible"]
    over = agg["lines_over_79"]
    within = elig - over
    dep_lines = pep440.get("total_dependency_lines") or 0
    inv_n = len(pep440.get("invalid_lines") or [])
    sym_total = agg["functions_methods_total"] + agg["classes_total"]
    ft = agg["functions_methods_total"]
    return {
        "pep8_line_width_compliance_pct": round(_pct_float(within, elig), 2),
        "pep8_lines_over_max": over,
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
        "max_line_length": max_line_length,
    }


def build_json_payload(
    summary,
    file_metrics,
    flake8_codes,
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
    return {
        "generated_at": meta["generated_at"],
        "command": meta["command"],
        "git_commit": meta.get("git_commit"),
        "app": app_name,
        "max_line_length": max_line_length,
        "summary": summary,
        "simple": build_simple_summary(
            summary, sum(flake8_codes.values()), pep440, max_line_length
        ),
        "flake8": dict(flake8_codes.most_common()),
        "pep440": pep440,
        "by_file": by_file,
    }


class Command(BaseCommand):
    help = (
        "Gera relatório PEP 8/257/484/440 de um app Django (MD + JSON + TXT)"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--app",
            default="core",
            help="Nome do app dentro de apps/ (ex.: core, designacao, unidades, usuarios)",
        )
        parser.add_argument(
            "--output-dir",
            default=None,
            help="Diretório de saída (default: apps/<app>/docs)",
        )
        parser.add_argument("--max-line-length", type=int, default=79)
        parser.add_argument("--service-name", default="SME-SIGNA-BACKEND")

    def handle(self, *args, **options):
        repo_root = _repo_root()
        app_name = options["app"]
        app_dir = _app_dir(app_name)
        if not app_dir.exists():
            raise CommandError(f"App não encontrado: {app_dir}")

        output_dir = (
            Path(options["output_dir"])
            if options["output_dir"]
            else app_dir / "docs"
        )
        if not output_dir.is_absolute():
            output_dir = repo_root / output_dir
        max_len = options["max_line_length"]
        output_dir.mkdir(parents=True, exist_ok=True)

        py_files = discover_app_python_files(app_dir)
        file_metrics = [analyze_file(p, app_dir, max_len) for p in py_files]
        summary = aggregate(file_metrics)

        flake8_codes, flake8_lines = run_flake8(app_name, repo_root)
        flake8_total = sum(flake8_codes.values())
        pep440 = analyze_pep440(repo_root / "requirements")

        git_commit = None
        try:
            r = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=str(repo_root),
                capture_output=True,
                text=True,
                check=True,
            )
            git_commit = r.stdout.strip()
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

        meta = {
            "generated_at": datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            ),
            "command": f"python manage.py {COMMAND_NAME} --app {app_name}",
            "git_commit": git_commit,
        }

        md_path = output_dir / "RELATORIO_PEP.md"
        md_simple_path = output_dir / "RELATORIO_PEP_RESUMIDO.md"
        txt_simple_path = output_dir / "RELATORIO_PEP_RESUMIDO.txt"
        json_path = output_dir / "relatorio_pep.json"

        md_path.write_text(
            render_markdown(
                summary,
                file_metrics,
                flake8_codes,
                flake8_lines,
                pep440,
                meta,
                max_len,
                app_name,
            ),
            encoding="utf-8",
        )
        md_simple_path.write_text(
            render_simplified_markdown(
                summary, flake8_total, pep440, meta, max_len, app_name
            ),
            encoding="utf-8",
        )
        txt_simple_path.write_text(
            render_simplified_txt(
                summary,
                flake8_total,
                pep440,
                meta,
                max_len,
                service_name=options["service_name"],
            ),
            encoding="utf-8",
        )
        json_path.write_text(
            json.dumps(
                build_json_payload(
                    summary,
                    file_metrics,
                    flake8_codes,
                    pep440,
                    meta,
                    max_len,
                    app_name,
                ),
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        self.stdout.write(self.style.SUCCESS(f"MD:   {md_path}"))
        self.stdout.write(self.style.SUCCESS(f"MD resumido: {md_simple_path}"))
        self.stdout.write(
            self.style.SUCCESS(f"TXT resumido: {txt_simple_path}")
        )
        self.stdout.write(self.style.SUCCESS(f"JSON: {json_path}"))
        self.stdout.write(
            f"Arquivos: {summary['files_count']} | "
            f"Funções: {summary['functions_methods_total']} | "
            f"Sem doc: {summary['functions_methods_without_docstring']} | "
            f"Linhas >{max_len}: {summary['lines_over_79']} | flake8: {flake8_total}"
        )
