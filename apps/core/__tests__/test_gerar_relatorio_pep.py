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
    _aggregate_flake8_codes,
    _app_dir,
    _build_meta,
    _build_payload_args,
    _estimar_horas_ajuste,
    _get_git_commit,
    _hint_level,
    _mypy_code_from_line,
    _parse_requirement_line,
    _pct,
    _pct_float,
    _repo_root,
    _status_emoji,
    _status_palavra,
    _walk_symbols,
    _write_app_outputs,
    aggregate,
    analyze_file,
    analyze_pep440,
    build_json_payload,
    consolidate,
    discover_app_python_files,
    discover_django_apps,
    render_markdown,
    render_simplified_markdown,
    render_simplified_txt,
    run_flake8,
    run_for_app,
    run_mypy,
)


class TestAddArguments:
    """Testes de Command.add_arguments."""

    def test_deve_definir_argumentos_padrao(self):
        command = Command()
        parser = command.create_parser("manage.py", "gerar_relatorio_pep")

        options = parser.parse_args([])

        assert options.app == "core"
        assert options.all is False
        assert options.only is None
        assert options.output_dir is None
        assert options.max_line_length == 79
        assert options.service_name == "SME-SIGNA-BACKEND"

    def test_deve_aceitar_argumentos_customizados(self):
        command = Command()
        parser = command.create_parser("manage.py", "gerar_relatorio_pep")

        options = parser.parse_args(
            [
                "--only",
                "core",
                "usuarios",
                "--output-dir",
                "saida",
                "--max-line-length",
                "100",
                "--service-name",
                "MEU-SERVICO",
            ]
        )

        assert options.only == ["core", "usuarios"]
        assert options.output_dir == "saida"
        assert options.max_line_length == 100
        assert options.service_name == "MEU-SERVICO"


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
    def test_deve_resolver_output_dir_relativo(
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
        mock_discover.return_value = []
        mock_aggregate.return_value = {
            "files_count": 0,
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
        mock_json.return_value = {"summary": {}}

        run_for_app(
            "usuarios",
            repo_root=tmp_path,
            max_line_length=79,
            output_dir=Path("saida_relativa"),
            service_name="TESTE",
        )

        out_dir_usado = mock_write.call_args[0][0]

        assert out_dir_usado == tmp_path / "saida_relativa"


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

    @patch("apps.core.management.commands.gerar_relatorio_pep.consolidate")
    def test_deve_avisar_quando_nenhum_app_encontrado(
        self,
        mock_consolidate,
    ):
        command = Command()

        command._run_many(
            [],
            {
                "output_dir": None,
                "max_line_length": 79,
                "service_name": "TESTE",
            },
            Path("/tmp"),
        )

        mock_consolidate.assert_not_called()

    @patch("apps.core.management.commands.gerar_relatorio_pep.consolidate")
    @patch("apps.core.management.commands.gerar_relatorio_pep.run_for_app")
    def test_deve_avisar_quando_nenhum_dado_coletado(
        self,
        mock_run_for_app,
        mock_consolidate,
    ):
        command = Command()

        mock_run_for_app.side_effect = [
            Exception("erro1"),
            Exception("erro2"),
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

        mock_consolidate.assert_not_called()


class TestHintLevel:
    """Testes de _hint_level."""

    def test_hint_level_completo(self):
        tree = ast.parse("""
def soma(a: int, b: int) -> int:
    return a + b
""")

        node = tree.body[0]

        assert _hint_level(node) == "completo"

    def test_hint_level_parcial(self):
        tree = ast.parse("""
def soma(a, b) -> int:
    return a + b
""")

        node = tree.body[0]

        assert _hint_level(node) == "parcial"

    def test_hint_level_sem(self):
        tree = ast.parse("""
def soma(a, b):
    return a + b
""")

        node = tree.body[0]

        assert _hint_level(node) == "sem"

    def test_hint_level_no_funcao(self):
        tree = ast.parse("x = 1")

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


class TestAppDir:
    """Testes de _app_dir."""

    def test_deve_montar_caminho_do_app(self):
        result = _app_dir("core")

        assert result == _repo_root() / "apps" / "core"


class TestDiscoverDjangoApps:
    """Testes de discover_django_apps."""

    @patch("apps.core.management.commands.gerar_relatorio_pep._repo_root")
    def test_deve_retornar_lista_vazia_sem_diretorio_apps(
        self, mock_repo_root, tmp_path
    ):
        mock_repo_root.return_value = tmp_path

        assert discover_django_apps() == []


class TestDiscoverAppPythonFiles:
    """Testes de discover_app_python_files."""

    def test_deve_ignorar_diretorios_e_arquivos_excluidos(self, tmp_path):
        app_dir = tmp_path / "usuarios"
        app_dir.mkdir()

        (app_dir / "models.py").write_text("x = 1")

        subdir = app_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.py").write_text("x = 1")

        migrations = app_dir / "migrations"
        migrations.mkdir()
        (migrations / "0001_initial.py").write_text("x = 1")

        testes = app_dir / "__tests__"
        testes.mkdir()
        (testes / "test_models.py").write_text("x = 1")

        tests_dir = app_dir / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_bar.py").write_text("x = 1")

        pycache = app_dir / "__pycache__"
        pycache.mkdir()
        (pycache / "models.cpython-312.pyc.py").write_text("x = 1")

        (app_dir / "gerar_relatorio_pep.py").write_text("x = 1")

        result = discover_app_python_files(app_dir)
        names = sorted(str(p.relative_to(app_dir)) for p in result)

        assert names == ["models.py", "subdir/nested.py"]


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

    def test_analyze_pep440_ignora_include(self, tmp_path):
        requirements = tmp_path / "requirements"
        requirements.mkdir()

        (requirements / "local.txt").write_text(
            "\n".join(["-r base.txt", "django==4.2.0"])
        )

        result = analyze_pep440(requirements)

        assert result["total_dependency_lines"] == 1


class TestPercentuais:
    """Testes de _pct_float."""

    def test_pct_float_zero(self):
        assert _pct_float(0, 0) == pytest.approx(100.0)

    def test_pct_float_normal(self):
        assert _pct_float(5, 10) == pytest.approx(50.0)

    def test_pct_zero(self):
        assert _pct(0, 0) == "—"

    def test_pct_normal(self):
        assert _pct(5, 10) == "50.0%"


class TestGetGitCommit:
    """Testes de _get_git_commit."""

    @patch("apps.core.management.commands.gerar_relatorio_pep.subprocess.run")
    def test_deve_retornar_hash_do_commit(self, mock_run, tmp_path):
        result = Mock()
        result.stdout = "abc1234\n"
        mock_run.return_value = result

        assert _get_git_commit(tmp_path) == "abc1234"

    @patch("apps.core.management.commands.gerar_relatorio_pep.subprocess.run")
    def test_deve_retornar_none_quando_git_falha(self, mock_run, tmp_path):
        mock_run.side_effect = FileNotFoundError

        assert _get_git_commit(tmp_path) is None


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

    def test_aggregate_modulo_sem_docstring(self):
        file_metric = FileMetrics(
            path="service.py",
            loc=10,
            module_has_docstring=False,
        )

        result = aggregate([file_metric])

        assert result["modules_without_docstring"] == 1
        assert result["modules_with_docstring"] == 0


class TestWalkSymbols:
    """Testes de _walk_symbols."""

    def test_walk_symbols(self):
        tree = ast.parse('''
class Usuario:
    """doc"""

    def salvar(self):
        """doc"""
        pass

def processar(a: int) -> int:
    """doc"""
    return a
''')

        symbols = _walk_symbols(tree)

        names = [s.name for s in symbols]

        assert "Usuario" in names
        assert "Usuario.salvar" in names
        assert "processar" in names

    def test_walk_symbols_async_function(self):
        tree = ast.parse('''
async def buscar(a: int) -> int:
    """doc"""
    return a
''')

        symbols = _walk_symbols(tree)

        assert any(
            s.kind == "async_function" and s.name == "buscar" for s in symbols
        )


class TestAnalyzeFile:
    """Testes de analyze_file."""

    def test_analyze_file(self, tmp_path):
        arquivo = tmp_path / "service.py"

        arquivo.write_text('''
"""modulo"""


def processar(a: int) -> int:
    """doc"""
    return a
''')

        result = analyze_file(
            arquivo,
            tmp_path,
            79,
        )

        assert result.loc > 0
        assert result.module_has_docstring is True
        assert len(result.symbols) > 0

    def test_analyze_file_linha_acima_do_limite(self, tmp_path):
        arquivo = tmp_path / "service.py"

        arquivo.write_text("x = " + "1" * 100 + "\n")

        result = analyze_file(arquivo, tmp_path, 79)

        assert result.lines_over_max == 1

    def test_analyze_file_com_erro_de_sintaxe(self, tmp_path):
        arquivo = tmp_path / "service.py"

        arquivo.write_text("def (:\n    pass\n")

        result = analyze_file(arquivo, tmp_path, 79)

        assert result.symbols == []
        assert result.module_has_docstring is False


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


class TestRenderMarkdown:
    """Testes de render_markdown."""

    def test_render_markdown_com_todos_os_blocos(self):
        summary = {
            "files_count": 2,
            "loc_total": 200,
            "lines_over_79": 3,
            "lines_length_eligible": 180,
            "functions_methods_total": 2,
            "functions_methods_with_docstring": 1,
            "classes_total": 1,
            "classes_with_docstring": 1,
            "hints_completo": 1,
            "missing_docstrings_top": [
                {
                    "path": "service.py",
                    "lineno": 10,
                    "name": "processar",
                    "kind": "function",
                }
            ],
        }

        fm_com_funcoes = FileMetrics(
            path="service.py",
            loc=100,
            lines_over_max=2,
            module_has_docstring=True,
            symbols=[
                SymbolMetrics(
                    kind="function",
                    name="processar",
                    lineno=10,
                    has_docstring=False,
                    hint_level="completo",
                ),
            ],
        )
        fm_sem_funcoes = FileMetrics(
            path="vazio.py",
            loc=5,
            module_has_docstring=False,
        )

        meta = {
            "generated_at": "agora",
            "command": "teste",
            "git_commit": "abc123",
        }

        md = render_markdown(
            summary,
            [fm_com_funcoes, fm_sem_funcoes],
            Counter({"E501": 3, "W293": 1}),
            ["apps/core/service.py:1:1: E501 line too long"],
            {"error": 2, "warning": 1},
            ["a.py:1: error: erro [arg-type]"],
            {"PEP 484": 2},
            {
                "files_analyzed": ["base.txt"],
                "total_dependency_lines": 3,
                "pypi_valid": 2,
                "git_pins": 1,
                "pinned_with_eq": 1,
                "invalid_lines": [],
            },
            meta,
            79,
            "core",
        )

        assert "Top flake8" in md
        assert "Primeiras 30 linhas flake8" in md
        assert "## MyPy" in md
        assert "Primeiras 30 linhas mypy" in md
        assert "Símbolos sem docstring" in md
        assert "`processar`" in md
        assert "base.txt" in md
        assert "`service.py`" in md
        assert "`vazio.py`" in md

    def test_render_markdown_sem_blocos_opcionais(self):
        summary = {
            "files_count": 0,
            "loc_total": 0,
            "lines_over_79": 0,
            "lines_length_eligible": 0,
            "functions_methods_total": 0,
            "functions_methods_with_docstring": 0,
            "classes_total": 0,
            "classes_with_docstring": 0,
            "hints_completo": 0,
            "missing_docstrings_top": [],
        }

        meta = {"generated_at": "agora", "command": "teste"}

        md = render_markdown(
            summary,
            [],
            Counter(),
            [],
            {},
            [],
            {},
            {
                "files_analyzed": [],
                "total_dependency_lines": 0,
                "invalid_lines": [],
            },
            meta,
            79,
            "core",
        )

        assert "Top flake8" not in md
        assert "## MyPy" not in md


class TestBuildMeta:
    """Testes de _build_meta."""

    @patch("apps.core.management.commands.gerar_relatorio_pep._get_git_commit")
    def test_deve_montar_meta(self, mock_git_commit, tmp_path):
        mock_git_commit.return_value = "abc1234"

        meta = _build_meta(tmp_path, "core")

        assert (
            meta["command"]
            == "python manage.py gerar_relatorio_pep --app core"
        )
        assert meta["git_commit"] == "abc1234"
        assert "generated_at" in meta


class TestWriteAppOutputs:
    """Testes de _write_app_outputs."""

    def test_deve_gravar_todos_os_arquivos(self, tmp_path):
        summary = {
            "files_count": 1,
            "loc_total": 10,
            "lines_over_79": 0,
            "lines_length_eligible": 10,
            "modules_with_docstring": 1,
            "modules_without_docstring": 0,
            "functions_methods_total": 1,
            "functions_methods_with_docstring": 1,
            "functions_methods_without_docstring": 0,
            "classes_total": 0,
            "classes_with_docstring": 0,
            "classes_without_docstring": 0,
            "symbols_with_docstring": 1,
            "symbols_without_docstring": 0,
            "hints_completo": 1,
            "hints_parcial": 0,
            "hints_sem": 0,
            "missing_docstrings_top": [],
        }
        fm = FileMetrics(path="service.py", loc=10, module_has_docstring=True)
        meta = {
            "generated_at": "agora",
            "command": "teste",
            "git_commit": "abc123",
        }
        pep440 = {"total_dependency_lines": 0, "invalid_lines": []}

        payload_args = _build_payload_args(
            summary,
            [fm],
            Counter(),
            [],
            {},
            [],
            {},
            pep440,
            meta,
            79,
            "usuarios",
            0,
        )

        paths = _write_app_outputs(tmp_path, payload_args, "TESTE")

        assert paths["md"].exists()
        assert paths["md_simple"].exists()
        assert paths["txt_simple"].exists()
        assert paths["json"].exists()
        assert "Relatório PEP" in paths["md"].read_text()


class TestAggregateFlake8Codes:
    """Testes de _aggregate_flake8_codes."""

    def test_deve_somar_ocorrencias_por_codigo(self):
        per_app = [
            {"payload": {"flake8": {"E501": 2}}},
            {"payload": {"flake8": {"E501": 1, "W293": 1}}},
        ]

        result = _aggregate_flake8_codes(per_app)

        assert result == {"E501": 3, "W293": 1}


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

    def test_consolidate_com_codigos_flake8(self, tmp_path):
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
            "mypy": {"errors": 0, "warnings": 0},
            "pep440": {"total_dependency_lines": 1, "invalid_lines": []},
            "flake8": {"E501": 5, "W293": 1},
        }

        result = consolidate(
            [
                {
                    "app": "usuarios",
                    "payload": payload,
                    "flake8_total": 6,
                }
            ],
            tmp_path,
            79,
        )

        md_content = result["md"].read_text()

        assert "Top códigos flake8" in md_content
        assert "E501" in md_content


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

    def test_run_flake8_app_nao_existe(self, tmp_path):
        codes, lines = run_flake8("inexistente", tmp_path)

        assert codes == Counter()
        assert lines == []


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
            "a.py:3: note: informação adicional\n"
        )

        mock_run.return_value = result

        codes, _, peps = run_mypy(
            "usuarios",
            tmp_path,
        )

        assert codes["error"] == 1
        assert codes["warning"] == 1
        assert codes["note"] == 1

        assert peps["PEP 484"] == 1
        assert peps["PEP 526"] == 1

    def test_run_mypy_app_nao_existe(self, tmp_path):
        codes, lines, peps = run_mypy("inexistente", tmp_path)

        assert codes == Counter()
        assert lines == []
        assert peps == {}

    @patch("apps.core.management.commands.gerar_relatorio_pep.subprocess.run")
    def test_run_mypy_sem_mypy(self, mock_run, tmp_path):
        app_dir = tmp_path / "apps" / "usuarios"
        app_dir.mkdir(parents=True)

        mock_run.side_effect = FileNotFoundError

        codes, lines, peps = run_mypy("usuarios", tmp_path)

        assert codes == Counter()
        assert "mypy" in lines[0]
        assert peps == {}


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
