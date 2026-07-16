"""Testes do management command gerar_relatorio_pep."""

import ast
from collections import Counter
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from django.core.management import CommandError

from apps.core.management.commands.gerar_relatorio_pep import (
    Command,
    FileMetrics,
    SymbolMetrics,
    _build_payload_args,
    _estimar_horas_ajuste,
    _hint_level,
    _mypy_code_from_line,
    _parse_requirement_line,
    _pct_float,
    _status_emoji,
    _status_palavra,
    _walk_symbols,
    aggregate,
    analyze_file,
    analyze_pep440,
    build_json_payload,
    consolidate,
    render_simplified_markdown,
    render_simplified_txt,
    run_flake8,
    run_for_app,
    run_mypy,
)


class TestResolveApps:
    """Testes de Command._resolve_apps."""

    def test_deve_retornar_app_unico(self):
        command = Command()

        apps, consolidated = command._resolve_apps(
            {
                "app": "usuarios",
                "all": False,
                "only": None,
            }
        )

        assert apps == ["usuarios"]
        assert consolidated is False

    def test_deve_retornar_only(self):
        command = Command()

        apps, consolidated = command._resolve_apps(
            {
                "app": "core",
                "all": False,
                "only": ["usuarios", "autenticacao"],
            }
        )

        assert apps == ["usuarios", "autenticacao"]
        assert consolidated is True


class TestHandle:
    """Testes do fluxo Command.handle para um único app."""

    @patch(
        "apps.core.management.commands.gerar_relatorio_pep.Command._run_single"
    )
    def test_deve_executar_run_single(self, mock_run_single):
        command = Command()

        command.handle(
            app="usuarios",
            all=False,
            only=None,
            output_dir=None,
            max_line_length=79,
            service_name="TESTE",
        )

        mock_run_single.assert_called_once()


class TestHandleConsolidado:
    """Testes do fluxo Command.handle consolidado (--all)."""

    @patch(
        "apps.core.management.commands.gerar_relatorio_pep.Command._run_many"
    )
    def test_deve_executar_run_many(self, mock_run_many):
        command = Command()

        command.handle(
            app="core",
            all=True,
            only=None,
            output_dir=None,
            max_line_length=79,
            service_name="TESTE",
        )

        mock_run_many.assert_called_once()


class TestRunForApp:
    """Testes de run_for_app."""

    @patch("apps.core.management.commands.gerar_relatorio_pep._app_dir")
    def test_deve_lancar_erro_quando_app_nao_existe(
        self,
        mock_app_dir,
    ):
        mock_app_dir.return_value = Path("/tmp/app_inexistente")

        with pytest.raises(CommandError):
            run_for_app(
                "inexistente",
                repo_root=Path("/tmp"),
                max_line_length=79,
                output_dir=None,
                service_name="TESTE",
            )

    @patch(
        "apps.core.management.commands.gerar_relatorio_pep._write_app_outputs"
    )
    @patch(
        "apps.core.management.commands.gerar_relatorio_pep.build_json_payload"
    )
    @patch("apps.core.management.commands.gerar_relatorio_pep._build_meta")
    @patch("apps.core.management.commands.gerar_relatorio_pep.analyze_pep440")
    @patch("apps.core.management.commands.gerar_relatorio_pep.run_mypy")
    @patch("apps.core.management.commands.gerar_relatorio_pep.run_flake8")
    @patch("apps.core.management.commands.gerar_relatorio_pep.aggregate")
    @patch("apps.core.management.commands.gerar_relatorio_pep.analyze_file")
    @patch(
        "apps.core.management.commands.gerar_relatorio_pep.discover_app_python_files"
    )
    @patch("apps.core.management.commands.gerar_relatorio_pep._app_dir")
    def test_deve_gerar_relatorio(
        self,
        mock_app_dir,
        mock_discover,
        mock_analyze_file,
        mock_aggregate,
        mock_flake8,
        mock_mypy,
        mock_pep440,
        mock_meta,
        mock_json,
        mock_write,
        tmp_path,
    ):
        app_dir = tmp_path / "usuarios"
        app_dir.mkdir()

        mock_app_dir.return_value = app_dir

        mock_discover.return_value = [
            Path("arquivo.py"),
        ]

        mock_analyze_file.return_value = Mock()

        mock_aggregate.return_value = {
            "files_count": 1,
            "functions_methods_total": 0,
            "functions_methods_without_docstring": 0,
            "lines_over_79": 0,
            "lines_length_eligible": 0,
        }

        mock_flake8.return_value = ({}, [])
        mock_mypy.return_value = ({}, [], {})
        mock_pep440.return_value = {}
        mock_meta.return_value = {"generated_at": "agora"}

        mock_write.return_value = {
            "md": Path("relatorio.md"),
            "json": Path("relatorio.json"),
        }

        mock_json.return_value = {
            "summary": {},
        }

        result = run_for_app(
            "usuarios",
            repo_root=tmp_path,
            max_line_length=79,
            output_dir=None,
            service_name="TESTE",
        )

        assert result["app"] == "usuarios"

        mock_discover.assert_called_once()
        mock_aggregate.assert_called_once()
        mock_flake8.assert_called_once()
        mock_mypy.assert_called_once()
        mock_write.assert_called_once()


class TestRunMany:
    """Testes de Command._run_many."""

    @patch("apps.core.management.commands.gerar_relatorio_pep.consolidate")
    @patch("apps.core.management.commands.gerar_relatorio_pep.run_for_app")
    def test_deve_ignorar_apps_com_erro(
        self,
        mock_run_for_app,
        mock_consolidate,
    ):
        command = Command()

        mock_run_for_app.side_effect = [
            {"app": "app1", "payload": {}, "flake8_total": 0},
            Exception("erro"),
        ]

        command._run_many(
            ["app1", "app2"],
            {
                "output_dir": None,
                "max_line_length": 79,
                "service_name": "TESTE",
            },
            Path("/tmp"),
        )

        mock_consolidate.assert_called_once()


class TestHintLevel:
    """Testes de _hint_level."""

    def test_hint_level_completo(self):
        tree = ast.parse(
            """
def soma(a: int, b: int) -> int:
    return a + b
"""
        )

        node = tree.body[0]

        assert _hint_level(node) == "completo"

    def test_hint_level_parcial(self):
        tree = ast.parse(
            """
def soma(a, b) -> int:
    return a + b
"""
        )

        node = tree.body[0]

        assert _hint_level(node) == "parcial"

    def test_hint_level_sem(self):
        tree = ast.parse(
            """
def soma(a, b):
    return a + b
"""
        )

        node = tree.body[0]

        assert _hint_level(node) == "sem"


class TestMypyCode:
    """Testes de _mypy_code_from_line."""

    def test_deve_extrair_codigo(self):
        line = "arquivo.py:10: error: incompatibilidade [arg-type]"

        assert _mypy_code_from_line(line) == "arg-type"

    def test_deve_retornar_none(self):
        assert _mypy_code_from_line("erro qualquer") is None


class TestParseRequirementLine:
    """Testes de _parse_requirement_line."""

    def test_git_dependency(self):
        invalid = []

        result, is_git, pinned = _parse_requirement_line(
            "git+https://github.com/test/repo.git",
            "base.txt",
            invalid,
        )

        assert result["type"] == "git"
        assert is_git is True
        assert pinned is False

    def test_requirement_valido(self):
        invalid = []

        result, is_git, pinned = _parse_requirement_line(
            "django==4.2.0",
            "base.txt",
            invalid,
        )

        assert result["type"] == "pypi"
        assert result["name"] == "django"
        assert is_git is False
        assert pinned is True

    def test_requirement_invalido(self):
        invalid = []

        result, is_git, pinned = _parse_requirement_line(
            "????",
            "base.txt",
            invalid,
        )

        assert result["type"] == "invalid"
        assert is_git is False
        assert pinned is False
        assert len(invalid) == 1


class TestAnalyzePep440:
    """Testes de analyze_pep440."""

    def test_analyze_pep440(self, tmp_path):
        requirements = tmp_path / "requirements"
        requirements.mkdir()

        (requirements / "base.txt").write_text(
            "\n".join(
                [
                    "django==4.2.0",
                    "requests>=2.0",
                    "git+https://github.com/test/repo.git",
                ]
            )
        )

        result = analyze_pep440(requirements)

        assert result["total_dependency_lines"] == 3
        assert result["git_pins"] == 1
        assert result["pypi_valid"] == 2

    def test_analyze_pep440_sem_diretorio(self, tmp_path):
        result = analyze_pep440(tmp_path / "nao_existe")

        assert result["total_dependency_lines"] == 0


class TestPercentuais:
    """Testes de _pct_float."""

    def test_pct_float_zero(self):
        assert _pct_float(0, 0) == pytest.approx(100.0)

    def test_pct_float_normal(self):
        assert _pct_float(5, 10) == pytest.approx(50.0)


class TestStatus:
    """Testes de _status_palavra e _status_emoji."""

    def test_status_palavra_bom(self):
        assert _status_palavra(90) == "Bom"

    def test_status_palavra_regular(self):
        assert _status_palavra(70) == "Regular"

    def test_status_palavra_ruim(self):
        assert _status_palavra(50) == "Precisa melhorar"

    def test_status_emoji_bom(self):
        assert _status_emoji(90) == "🟢 Bom"

    def test_status_emoji_regular(self):
        assert _status_emoji(70) == "🟡 Regular"

    def test_status_emoji_ruim(self):
        assert _status_emoji(50) == "🔴 Precisa melhorar"


class TestEstimativaHoras:
    """Testes de _estimar_horas_ajuste."""

    def test_estimar_horas(self):
        summary = {
            "functions_methods_without_docstring": 10,
            "hints_sem": 5,
            "lines_over_79": 20,
        }

        result = _estimar_horas_ajuste(
            summary,
            flake8_total=10,
            mypy_errors=2,
        )

        assert result >= 1


class TestAggregate:
    """Testes de aggregate."""

    def test_aggregate(self):
        file_metric = FileMetrics(
            path="service.py",
            loc=100,
            lines_over_max=2,
            module_has_docstring=True,
            symbols=[
                SymbolMetrics(
                    kind="function",
                    name="funcao",
                    lineno=10,
                    has_docstring=True,
                    hint_level="completo",
                ),
                SymbolMetrics(
                    kind="class",
                    name="Classe",
                    lineno=20,
                    has_docstring=False,
                    hint_level="sem",
                ),
            ],
        )

        result = aggregate([file_metric])

        assert result["files_count"] == 1
        assert result["loc_total"] == 100
        assert result["functions_methods_total"] == 1
        assert result["classes_total"] == 1
        assert result["symbols_with_docstring"] == 1


class TestWalkSymbols:
    """Testes de _walk_symbols."""

    def test_walk_symbols(self):
        tree = ast.parse(
            '''
class Usuario:
    """doc"""

    def salvar(self):
        """doc"""
        pass

def processar(a: int) -> int:
    """doc"""
    return a
'''
        )

        symbols = _walk_symbols(tree)

        names = [s.name for s in symbols]

        assert "Usuario" in names
        assert "Usuario.salvar" in names
        assert "processar" in names


class TestAnalyzeFile:
    """Testes de analyze_file."""

    def test_analyze_file(self, tmp_path):
        arquivo = tmp_path / "service.py"

        arquivo.write_text(
            '''
"""modulo"""


def processar(a: int) -> int:
    """doc"""
    return a
'''
        )

        result = analyze_file(
            arquivo,
            tmp_path,
            79,
        )

        assert result.loc > 0
        assert result.module_has_docstring is True
        assert len(result.symbols) > 0


class TestRenderizadores:
    """Testes dos renderizadores e da montagem do payload JSON."""

    def test_renderizadores_e_payload(self):
        summary = {
            "files_count": 1,
            "loc_total": 100,
            "lines_over_79": 0,
            "lines_length_eligible": 100,
            "modules_with_docstring": 1,
            "modules_without_docstring": 0,
            "functions_methods_total": 1,
            "functions_methods_with_docstring": 1,
            "functions_methods_without_docstring": 0,
            "classes_total": 1,
            "classes_with_docstring": 1,
            "classes_without_docstring": 0,
            "symbols_with_docstring": 2,
            "symbols_without_docstring": 0,
            "hints_completo": 1,
            "hints_parcial": 0,
            "hints_sem": 0,
            "missing_docstrings_top": [],
        }

        fm = FileMetrics(
            path="service.py",
            loc=100,
            module_has_docstring=True,
            symbols=[
                SymbolMetrics(
                    kind="function",
                    name="processar",
                    lineno=1,
                    has_docstring=True,
                    hint_level="completo",
                )
            ],
        )

        meta = {
            "generated_at": "agora",
            "command": "teste",
            "git_commit": "abc123",
        }

        md = render_simplified_markdown(
            summary,
            0,
            {},
            {},
            {
                "total_dependency_lines": 1,
                "invalid_lines": [],
            },
            meta,
            "usuarios",
        )

        assert "PEP 8" in md

        txt = render_simplified_txt(
            summary,
            0,
            {},
            {},
            {
                "total_dependency_lines": 1,
                "invalid_lines": [],
            },
            meta,
            79,
            service_name="TESTE",
        )

        assert "RESUMO DE BOAS PRÁTICAS" in txt

        payload = build_json_payload(
            summary=summary,
            file_metrics=[fm],
            flake8_codes=Counter(),
            mypy_codes={},
            mypy_pep_summary={},
            pep440={
                "total_dependency_lines": 1,
                "invalid_lines": [],
            },
            meta=meta,
            max_line_length=79,
            app_name="usuarios",
        )

        assert payload["app"] == "usuarios"

        args = _build_payload_args(
            summary,
            [fm],
            Counter(),
            [],
            {},
            [],
            {},
            {
                "total_dependency_lines": 1,
                "invalid_lines": [],
            },
            meta,
            79,
            "usuarios",
            0,
        )

        assert "render_md" in args
        assert "json" in args


class TestConsolidate:
    """Testes de consolidate."""

    def test_consolidate(self, tmp_path):

        payload = {
            "summary": {
                "files_count": 1,
                "loc_total": 10,
                "lines_over_79": 0,
                "lines_length_eligible": 10,
                "functions_methods_total": 1,
                "functions_methods_with_docstring": 1,
                "functions_methods_without_docstring": 0,
                "classes_total": 0,
                "classes_with_docstring": 0,
                "symbols_with_docstring": 1,
                "hints_completo": 1,
                "hints_parcial": 0,
                "hints_sem": 0,
            },
            "simple": {
                "pep8_line_width_compliance_pct": 100,
                "pep8_flake8_compliance_pct": 100,
                "pep257_docstring_compliance_pct": 100,
                "pep484_full_hints_pct": 100,
                "mypy_compliance_pct": 100,
            },
            "mypy": {
                "errors": 0,
                "warnings": 0,
            },
            "pep440": {
                "total_dependency_lines": 1,
                "invalid_lines": [],
            },
            "flake8": {},
        }

        result = consolidate(
            [
                {
                    "app": "usuarios",
                    "payload": payload,
                    "flake8_total": 0,
                }
            ],
            tmp_path,
            79,
        )

        assert result["md"].exists()
        assert result["json"].exists()


class TestRunFlake8:
    """Testes de run_flake8."""

    @patch("apps.core.management.commands.gerar_relatorio_pep.subprocess.run")
    def test_run_flake8(self, mock_run, tmp_path):

        app_dir = tmp_path / "apps" / "usuarios"
        app_dir.mkdir(parents=True)

        result = Mock()
        result.stdout = (
            "apps/usuarios/test.py:1:1: E501 line too long\n"
            "apps/usuarios/test.py:2:1: W293 blank line\n"
        )

        mock_run.return_value = result

        codes, lines = run_flake8(
            "usuarios",
            tmp_path,
        )

        assert codes["E501"] == 1
        assert codes["W293"] == 1
        assert len(lines) == 2

    @patch("apps.core.management.commands.gerar_relatorio_pep.subprocess.run")
    def test_run_flake8_sem_flake8(
        self,
        mock_run,
        tmp_path,
    ):
        app_dir = tmp_path / "apps" / "usuarios"
        app_dir.mkdir(parents=True)

        mock_run.side_effect = FileNotFoundError

        codes, lines = run_flake8(
            "usuarios",
            tmp_path,
        )

        assert codes == Counter()
        assert "flake8" in lines[0]


class TestRunMypy:
    """Testes de run_mypy."""

    @patch("apps.core.management.commands.gerar_relatorio_pep.subprocess.run")
    def test_run_mypy(
        self,
        mock_run,
        tmp_path,
    ):
        app_dir = tmp_path / "apps" / "usuarios"
        app_dir.mkdir(parents=True)

        result = Mock()

        result.stdout = (
            "a.py:1: error: erro [arg-type]\n"
            "a.py:2: warning: aviso [var-annotated]\n"
        )

        mock_run.return_value = result

        codes, _, peps = run_mypy(
            "usuarios",
            tmp_path,
        )

        assert codes["error"] == 1
        assert codes["warning"] == 1

        assert peps["PEP 484"] == 1
        assert peps["PEP 526"] == 1


class TestRunSingle:
    """Testes de Command._run_single."""

    @patch("apps.core.management.commands.gerar_relatorio_pep.run_for_app")
    def test_run_single(
        self,
        mock_run_for_app,
    ):
        command = Command()

        mock_run_for_app.return_value = {
            "paths": {
                "md": Path("a"),
                "md_simple": Path("b"),
                "txt_simple": Path("c"),
                "json": Path("d"),
            },
            "summary": {
                "files_count": 1,
                "functions_methods_total": 1,
                "functions_methods_without_docstring": 0,
                "lines_over_79": 0,
            },
            "flake8_total": 0,
            "mypy_codes": {},
        }

        command._run_single(
            "usuarios",
            {
                "output_dir": None,
                "max_line_length": 79,
                "service_name": "TESTE",
            },
            Path("/tmp"),
        )

        mock_run_for_app.assert_called_once()


class TestHandleExtra:
    """Testes adicionais de Command.handle cobrindo os dois fluxos."""

    @patch.object(Command, "_run_single")
    def test_handle_single(
        self,
        mock_single,
    ):
        Command().handle(
            app="usuarios",
            all=False,
            only=None,
            output_dir=None,
            max_line_length=79,
            service_name="TESTE",
        )

        mock_single.assert_called_once()

    @patch.object(Command, "_run_many")
    def test_handle_many(
        self,
        mock_many,
    ):
        Command().handle(
            app="usuarios",
            all=True,
            only=None,
            output_dir=None,
            max_line_length=79,
            service_name="TESTE",
        )

        mock_many.assert_called_once()
