"""Cria (ou remove) dados de demonstração do histórico de designações.

Uso:
    python manage.py seed_historico_demo
    python manage.py seed_historico_demo --apagar

Os atos criados usam o prefixo ``DEMO-`` em ``sei_numero``; designações
reais nunca são alteradas. O comando é idempotente: cada execução apaga
os dados de demonstração anteriores antes de recriá-los.
"""

from typing import Any

from django.core.management.base import BaseCommand

from apps.designacao.seed.historico_demo import (
    MARCADOR,
    UNIDADES,
    apagar_dados_demo,
    criar_dados_demo,
)


class Command(BaseCommand):
    """Popula o banco com cenários completos de designação por UE."""

    help = (
        "Cria designações, cessações, apostilas e insubsistências de "
        f"demonstração (prefixo {MARCADOR} no SEI) em 4 UEs."
    )

    def add_arguments(self, parser: Any) -> None:
        """Registra a opção de remoção dos dados."""
        parser.add_argument(
            "--apagar",
            action="store_true",
            help="Remove os dados de demonstração em vez de criá-los.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Executa a criação ou a remoção dos dados."""
        if options["apagar"]:
            removidos = apagar_dados_demo()
            self.stdout.write(
                self.style.SUCCESS(
                    f"{removidos} ato(s) de demonstração removido(s)."
                )
            )
            return

        dados = criar_dados_demo()
        self._imprimir_resumo(dados)

    def _imprimir_resumo(self, dados: dict[str, Any]) -> None:
        """Imprime o resumo do que foi criado e como testar.

        Args:
            dados: Resumo devolvido por ``criar_dados_demo``.

        """
        self.stdout.write(self.style.SUCCESS("Dados de demonstração:"))
        for tipo, quantidade in dados["por_tipo"].items():
            self.stdout.write(f"  {tipo:<16} {quantidade:>3}")

        self.stdout.write(f"  {'TOTAL':<16} {dados['total']:>3}")

        self.stdout.write("\nDesignações por UE:")
        for ue, quantidade in dados["por_ue"].items():
            nome = UNIDADES[ue]["unidade_proponente"]
            self.stdout.write(f"  {ue}  {quantidade:>2}  {nome}")

        self.stdout.write("\nEndpoints para testar:")
        for ue in UNIDADES:
            self.stdout.write(
                f"  /api/designacao/historico-de-designacoes/{ue}/"
            )
        self.stdout.write(
            "\n  Filtros de exemplo (UE 000108):\n"
            "  ?status_publicacao=NAO_PUBLICADO"
            "&periodo_after=2026-10-06&periodo_before=2026-11-10"
            "&observacao=ssss"
        )
