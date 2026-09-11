"""Serviço de geração do texto SEI a partir de modelos de portaria.

Resolve o modelo de portaria vigente para um tipo de ato e monta o
texto final substituindo as variáveis do modelo pelos dados recebidos.
Não persiste nada — a persistência do texto gerado é responsabilidade
do fluxo de criação/apostilamento de cada ato.
"""

import re

from rest_framework.exceptions import ValidationError

from apps.gestao.models.modelo_portaria import ModeloPortaria
from apps.gestao.services.modelo_portaria_service import (
    ModeloPortariaService,
)

_PLACEHOLDER = re.compile(r"\[\[(\w+)\]\]")


class TextoSeiService:
    """Gera a prévia do texto SEI de um ato a partir do modelo vigente."""

    @staticmethod
    def gerar_preview(
        tipo_portaria: str,
        tipo_ato_pai: str,
        tipo_cargo: str,
        dados: dict[str, str],
    ) -> tuple[ModeloPortaria, str]:
        """Resolve o modelo vigente e monta o texto final.

        Args:
            tipo_portaria: Tipo do ato para o qual o texto está sendo
                gerado (designação, cessação, apostila ou
                insubsistência).
            tipo_ato_pai: Tipo do ato pai, quando aplicável.
            tipo_cargo: Se o cargo do ato é vago ou disponível —
                designação e cessação têm textos diferentes para
                cada caso.
            dados: Dicionário de variáveis (mesmas chaves de
                `ModeloPortaria.Variavel`) já resolvidas pelo
                requisitante, para substituição no texto do modelo.

        Returns:
            tuple[ModeloPortaria, str]: Modelo usado e texto já
            renderizado.

        Raises:
            ValidationError: Quando não há modelo ativo para a
            combinação de tipos informada.

        """
        modelo = ModeloPortariaService.resolver_ativo(
            tipo_portaria, tipo_ato_pai, tipo_cargo
        )
        if modelo is None:
            raise ValidationError(
                {
                    "modelo_portaria": (
                        "Não há modelo de portaria ativo cadastrado "
                        "para este tipo de ato."
                    )
                }
            )

        texto = TextoSeiService._renderizar(modelo.texto_portaria, dados)
        return modelo, texto

    @staticmethod
    def _renderizar(texto_portaria: str, dados: dict[str, str]) -> str:
        """Substitui as variáveis `[[CHAVE]]` do texto pelos dados.

        Args:
            texto_portaria: Texto do modelo, com placeholders no
                formato `[[CHAVE]]`.
            dados: Valores a substituir, indexados pela mesma chave
                usada no placeholder. Placeholders sem valor
                correspondente são substituídos por string vazia.

        Returns:
            str: Texto com todas as variáveis substituídas.

        """

        def _substituir(match: re.Match[str]) -> str:
            chave = match.group(1)
            valor = dados.get(chave, "")
            return str(valor) if valor is not None else ""

        return _PLACEHOLDER.sub(_substituir, texto_portaria)
