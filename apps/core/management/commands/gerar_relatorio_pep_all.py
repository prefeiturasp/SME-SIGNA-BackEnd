"""
Gera relatório PEP consolidado de todos os apps em apps/.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

APPS_PARENT = "apps"
EXCLUDE_APPS = {"__pycache__"}


def _repo_root() -> Path:
    return Path(settings.BASE_DIR)


def _discover_apps() -> List[str]:
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


def _load_json(path: Path) -> Dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _status(pct: float) -> str:
    if pct >= 80:
        return "🟢 Bom"
    if pct >= 60:
        return "🟡 Regular"
    return "🔴 Precisa melhorar"


class Command(BaseCommand):
    help = "Roda gerar_relatorio_pep para todos os apps e gera consolidado."

    def add_arguments(self, parser):
        parser.add_argument("--max-line-length", type=int, default=79)
        parser.add_argument(
            "--output-dir",
            default="docs",
            help="Diretório de saída do relatório consolidado (rel. ao repo).",
        )
        parser.add_argument(
            "--only",
            nargs="*",
            default=None,
            help="Lista de apps específicos (default: todos).",
        )

    def handle(self, *args, **options):
        repo_root = _repo_root()
        max_len = options["max_line_length"]
        apps = options["only"] or _discover_apps()

        if not apps:
            self.stdout.write(
                self.style.WARNING("Nenhum app encontrado em apps/")
            )
            return

        self.stdout.write(
            self.style.NOTICE(f"Apps a analisar: {', '.join(apps)}")
        )

        per_app: List[Dict[str, Any]] = []
        for app in apps:
            self.stdout.write(f"\n→ Rodando para: {app}")
            try:
                call_command(
                    "gerar_relatorio_pep",
                    app=app,
                    max_line_length=max_len,
                    verbosity=0,
                )
            except Exception as exc:  # noqa: BLE001
                self.stdout.write(self.style.ERROR(f"  Falhou: {exc}"))
                continue

            json_path = (
                repo_root / APPS_PARENT / app / "docs" / "relatorio_pep.json"
            )
            data = _load_json(json_path)
            if data is None:
                self.stdout.write(
                    self.style.WARNING(f"  JSON não encontrado para {app}")
                )
                continue
            data["_app"] = app
            per_app.append(data)

        if not per_app:
            self.stdout.write(self.style.ERROR("Nenhum dado coletado."))
            return

        # Consolidação
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
        }
        for d in per_app:
            s = d["summary"]
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
            totals["flake8"] += sum(d.get("flake8", {}).values())

        def pct(part: int, whole: int) -> float:
            return 100.0 if whole <= 0 else 100.0 * part / whole

        elig = totals["lines_eligible"]
        within = elig - totals["lines_over"]
        pep8_pct = pct(within, elig)
        pep257_pct = pct(totals["symbols_doc"], totals["symbols_total"])
        pep484_full = pct(totals["hints_completo"], totals["funcs"])
        pep484_partial = pct(
            totals["hints_completo"] + totals["hints_parcial"], totals["funcs"]
        )

        # PEP 440 (lê de qualquer app, é o mesmo requirements/)
        pep440 = per_app[0].get("pep440", {})
        dep_lines = pep440.get("total_dependency_lines") or 0
        inv_n = len(pep440.get("invalid_lines") or [])
        pep440_pct = pct(dep_lines - inv_n, dep_lines)

        # Markdown consolidado
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        md = [
            "# Relatório PEP — Consolidado",
            "",
            f"Gerado em: **{now}**  ",
            f"Apps analisados: {', '.join(d['_app'] for d in per_app)}  ",
            f"Limite linha (PEP 8): **{max_len}**",
            "",
            "## Aderência geral",
            "",
            "| PEP | Aderência | Situação |",
            "| --- | ---: | :--- |",
            f"| PEP 8 (largura linha) | **{pep8_pct:.1f}%** | {_status(pep8_pct)} |",
            f"| PEP 257 (docstrings) | **{pep257_pct:.1f}%** | {_status(pep257_pct)} |",
            f"| PEP 484 (hints completos) | **{pep484_full:.1f}%** | {_status(pep484_full)} |",
            f"| PEP 484 (completo+parcial) | **{pep484_partial:.1f}%** | {_status(pep484_partial)} |",
            f"| PEP 440 (requirements) | **{pep440_pct:.1f}%** | {_status(pep440_pct)} |",
            "",
            "## Totais",
            "",
            "| Métrica | Valor |",
            "| --- | ---: |",
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
            "",
            "## Por app",
            "",
            "| App | Arquivos | Funções | Sem doc | Linhas >max | flake8 | PEP 8 % | PEP 257 % | PEP 484 % |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
        for d in per_app:
            s = d["summary"]
            simple = d.get("simple", {})
            md.append(
                f"| `{d['_app']}` | {s['files_count']} | {s['functions_methods_total']} | "
                f"{s['functions_methods_without_docstring']} | {s['lines_over_79']} | "
                f"{sum(d.get('flake8', {}).values())} | "
                f"{simple.get('pep8_line_width_compliance_pct', 0):.1f}% | "
                f"{simple.get('pep257_docstring_compliance_pct', 0):.1f}% | "
                f"{simple.get('pep484_full_hints_pct', 0):.1f}% |"
            )
        md += [
            "",
            "## Top códigos flake8 (agregado)",
            "",
        ]
        agg_codes: Dict[str, int] = {}
        for d in per_app:
            for code, n in d.get("flake8", {}).items():
                agg_codes[code] = agg_codes.get(code, 0) + n
        if agg_codes:
            md += ["| Código | Ocorrências |", "| --- | ---: |"]
            for code, n in sorted(agg_codes.items(), key=lambda x: -x[1])[:15]:
                md.append(f"| `{code}` | {n} |")
        md.append("")
        md.append("_Relatórios detalhados por app em `apps/<app>/docs/`._")

        out_dir = Path(options["output_dir"])
        if not out_dir.is_absolute():
            out_dir = repo_root / out_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        md_path = out_dir / "RELATORIO_PEP_GERAL.md"
        json_path = out_dir / "relatorio_pep_geral.json"

        md_path.write_text("\n".join(md) + "\n", encoding="utf-8")
        json_path.write_text(
            json.dumps(
                {
                    "generated_at": now,
                    "apps": [d["_app"] for d in per_app],
                    "totals": totals,
                    "pep_compliance": {
                        "pep8": round(pep8_pct, 2),
                        "pep257": round(pep257_pct, 2),
                        "pep484_full": round(pep484_full, 2),
                        "pep484_full_or_partial": round(pep484_partial, 2),
                        "pep440": round(pep440_pct, 2),
                    },
                    "flake8_top": dict(
                        sorted(agg_codes.items(), key=lambda x: -x[1])
                    ),
                    "per_app": per_app,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        self.stdout.write(self.style.SUCCESS(f"\nMD consolidado:   {md_path}"))
        self.stdout.write(self.style.SUCCESS(f"JSON consolidado: {json_path}"))
