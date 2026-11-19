"""Testes do endpoint ``POST /api/designacao/portarias/lauda/``.

Valida autenticação, validação do payload, cabeçalhos da resposta binária
e a propagação dos erros de regra de negócio do serviço.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.designacao.__tests__.factories import criar_ato_designacao

User = get_user_model()

URL = "/api/designacao/portarias/lauda/"
PAYLOAD = {"ordenacao": "DRE"}


@pytest.fixture
def auth_client(db):
    """Cliente de API autenticado."""
    user = User.objects.create_user(username="lauda", password="senha123")
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def ato(db):
    return criar_ato_designacao(
        numero_portaria=1,
        ano_vigente="2026",
        sei_numero="6018.2026/0000001-0",
    )


@pytest.fixture
def publicado(db):
    return criar_ato_designacao(
        numero_portaria=2,
        ano_vigente="2026",
        sei_numero="6018.2026/0000002-0",
        doc="2026-02-01",
    )


class TestLaudaEndpoint:
    """Comportamento HTTP do endpoint de lauda."""

    def test_exige_autenticacao(self, db):
        response = APIClient().post(URL, {"ids": [1]}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retorna_pdf_como_anexo(self, auth_client, ato):
        response = auth_client.post(
            URL, {**PAYLOAD, "ids": [ato.pk], "formato": "PDF"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/pdf"
        disposition = response["Content-Disposition"]
        assert disposition.startswith('attachment; filename="lauda-')
        assert disposition.endswith('.pdf"')
        assert response.content.startswith(b"%PDF-")

    def test_retorna_word_como_anexo(self, auth_client, ato):
        response = auth_client.post(
            URL, {**PAYLOAD, "ids": [ato.pk], "formato": "WORD"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        )
        disposition = response["Content-Disposition"]
        assert disposition.startswith('attachment; filename="lauda-')
        assert disposition.endswith('.docx"')
        assert response.content.startswith(b"PK")

    def test_retorna_csv_como_anexo(self, auth_client, ato):
        response = auth_client.post(
            URL, {**PAYLOAD, "ids": [ato.pk], "formato": "CSV"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv; charset=utf-8"
        assert response["Content-Disposition"].endswith('.csv"')
        assert response.content.startswith(b"\xef\xbb\xbf")

    def test_formato_padrao_eh_pdf(self, auth_client, ato):
        response = auth_client.post(
            URL, {**PAYLOAD, "ids": [ato.pk]}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/pdf"

    def test_ids_repetidos_sao_aceitos(self, auth_client, ato):
        response = auth_client.post(
            URL, {**PAYLOAD, "ids": [ato.pk, ato.pk]}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK

    def test_erro_sem_ids(self, auth_client):
        response = auth_client.post(URL, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "ids" in response.json()

    def test_erro_ids_vazio(self, auth_client):
        response = auth_client.post(URL, {"ids": []}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_erro_id_nao_inteiro(self, auth_client):
        response = auth_client.post(URL, {"ids": ["abc"]}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_erro_formato_nao_suportado(self, auth_client, ato):
        response = auth_client.post(
            URL, {**PAYLOAD, "ids": [ato.pk], "formato": "ODT"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "formato" in response.json()

    def test_erro_sem_ordenacao(self, auth_client, ato):
        response = auth_client.post(URL, {"ids": [ato.pk]}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "ordenacao" in response.json()

    def test_erro_ordenacao_invalida(self, auth_client, ato):
        response = auth_client.post(
            URL, {"ids": [ato.pk], "ordenacao": "NOME"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "ordenacao" in response.json()

    @pytest.mark.parametrize("ordenacao", ["NUMERO_PORTARIA", "DRE", "TITULO"])
    def test_aceita_cada_ordenacao(self, auth_client, ato, ordenacao):
        response = auth_client.post(
            URL, {"ids": [ato.pk], "ordenacao": ordenacao}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK

    def test_erro_id_inexistente(self, auth_client):
        response = auth_client.post(
            URL, {**PAYLOAD, "ids": [99999]}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Sem prefixo "ids:" — o erro é do lote, não do campo.
        assert response.json()["detail"] == "Atos não encontrados: 99999."

    def test_ato_publicado_entra_na_lauda(self, auth_client, ato, publicado):
        # Sem trava por status_publicacao por enquanto (ver TODO no
        # LaudaService.buscar_atos).
        response = auth_client.post(
            URL, {**PAYLOAD, "ids": [ato.pk, publicado.pk]}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
