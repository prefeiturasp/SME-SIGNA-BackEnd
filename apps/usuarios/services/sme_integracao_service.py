"""Serviço de integração com a SME e CoreSSO.

Fornece autenticação, consulta de dados de usuário, alteração de senha,
consulta de cargos, turmas e outras informações relacionadas ao SME.
"""

import logging

import environ
import requests

from rest_framework import status

from apps.designacao.constants.cargos_gestao_escolar import (
    CARGOS_GESTAO_ESCOLAR,
)
from apps.helpers.exceptions import (
    AuthenticationError,
    InternalError,
    SmeIntegracaoException,
)

MSG_RF_OBRIGATORIO = "Registro funcional é obrigatório"
MSG_ERRO_COMUNICACAO_SME = "Erro de comunicação com SME"
MSG_ERRO_COMUNICACAO_CORESSO = "Erro de comunicação com CoreSSO"
MSG_ERRO_CARGOS = "Erro ao consultar cargos do servidor"

env = environ.Env()
logger = logging.getLogger(__name__)


class SmeIntegracaoService:
    """Serviço para autenticação e consulta de dados na SME.

    Expõe métodos de autenticação, consulta de dados do usuário, alteração de
    senha e busca de informações relacionadas a cargos, turmas e unidades.
    """

    DEFAULT_HEADERS = {
        "accept": "application/json",
        "x-api-eol-key": env("SME_INTEGRACAO_TOKEN", default=""),
    }
    TIMEOUT = 30

    @classmethod
    def autentica(cls, login: str, senha: str) -> dict:
        """Autentica usuário no CoreSSO da SME.

        Args:
            login (str): Registro funcional ou nome de usuário.
            senha (str): Senha do usuário.

        Returns:
            dict: Dados retornados pela SME após autenticação.

        Raises:
            AuthenticationError: Quando as credenciais são inválidas.
            SmeIntegracaoException: Em caso de falha na autenticação.
            InternalError: Em caso de erro interno não esperado.
        """
        payload = {
            "usuario": login,
            "senha": senha,
            "codigoSistema": env("CODIGO_SISTEMA_SIGNA", default=""),
        }

        url = (
            f"{env('SME_INTEGRACAO_URL', default='')}/v1/autenticacao/externa"
        )

        logger.info("Autenticando no CoreSSO: %s", login)

        try:
            response = requests.post(
                url,
                json=payload,
                headers=cls.DEFAULT_HEADERS,
                timeout=cls.TIMEOUT,
            )

            if response.status_code == 401:
                raise AuthenticationError("Credenciais inválidas")

            if response.status_code != 200:
                raise SmeIntegracaoException(
                    f"Erro ao autenticar no CoreSSO: {response.status_code}"
                )

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error("Erro de comunicação: %s", e)
            raise SmeIntegracaoException(MSG_ERRO_COMUNICACAO_CORESSO)

        except (AuthenticationError, SmeIntegracaoException):
            raise

        except Exception as e:
            logger.error("Erro interno na autenticação: %s", e)
            raise InternalError("Erro interno ao autenticar no CoreSSO")

    @classmethod
    def informacao_usuario_sgp(cls, username: str) -> dict:
        """Consulta os dados do usuário na SME pelo username.

        Args:
            username (str): Nome de usuário ou registro funcional.

        Returns:
            dict: Dados do usuário retornados pela SME.

        Raises:
            SmeIntegracaoException: Quando os dados não são encontrados.
            requests.RequestException: Em caso de falha de conexão.
        """
        logger.info(f"Consultando dados na API externa para: {username}")
        try:
            url = f"{env('SME_INTEGRACAO_URL', default='')}/AutenticacaoSgp/{username}/dados"  # noqa: E501
            response = requests.get(
                url, headers=cls.DEFAULT_HEADERS, timeout=10
            )

            if response.status_code == status.HTTP_200_OK:
                return response.json()

            else:
                logger.info(f"Dados não encontrados: {response}")
                raise SmeIntegracaoException("Dados não encontrados.")

        except requests.RequestException:
            logger.exception("Erro de conexão com a API externa")
            raise requests.RequestException(
                "Erro ao conectar-se à API externa."
            )

    @classmethod
    def redefine_senha(cls, registro_funcional: str, senha: str) -> str:
        """
        Redefine a senha de um usuário no sistema SME.

        IMPORTANTE: Se a nova senha for uma das senhas padrões, a API do SME
        não permite a atualização. Para resetar para senha padrão,
        use o endpoint ReiniciarSenha.

        Args:
            registro_funcional: Username/registro funcional do usuário
            senha: Nova senha

        Returns:
            Dict[str, Any]: Resposta da API ou confirmação de sucesso

        Raises:
            SmeIntegracaoException: Em caso de erro na operação
        """

        if not registro_funcional or not senha:
            raise SmeIntegracaoException(
                "Registro funcional e senha são obrigatórios"
            )

        logger.info(
            "Iniciando redefinição de senha no CoreSSO para usuário: %s",
            registro_funcional,
        )

        data = {"Usuario": registro_funcional, "Senha": senha}

        try:

            url = f"{env('SME_INTEGRACAO_URL', default='')}/AutenticacaoSgp/AlterarSenha"  # noqa: E501

            response = requests.post(
                url, data=data, headers=cls.DEFAULT_HEADERS
            )

            if response.status_code == status.HTTP_200_OK:
                result = "OK"
                return result
            else:
                texto = response.content.decode("utf-8")
                mensagem = texto.strip("{}'\"")
                logger.info("Erro ao redefinir senha: %s", mensagem)
                raise SmeIntegracaoException(mensagem)
        except Exception as err:
            raise SmeIntegracaoException(str(err))

    @classmethod
    def altera_email(cls, registro_funcional: str, email: str) -> str:
        """
        Altera o email de um usuário no sistema SME.

        Args:
            registro_funcional: Username/registro funcional do usuário
            email: Novo Email

        Returns:
            Dict[str, Any]: Resposta da API ou confirmação de sucesso

        Raises:
            SmeIntegracaoException: Em caso de erro na operação
        """

        if not registro_funcional or not email:
            raise SmeIntegracaoException(
                "Registro funcional e email são obrigatórios"
            )

        logger.info(
            "Iniciando alteração de email no CoreSSO para usuário: %s",
            registro_funcional,
        )

        data = {"Usuario": registro_funcional, "Email": email}

        try:

            url = f"{env('SME_INTEGRACAO_URL', default='')}/AutenticacaoSgp/AlterarEmail"  # noqa: E501

            response = requests.post(
                url, data=data, headers=cls.DEFAULT_HEADERS
            )

            if response.status_code == status.HTTP_200_OK:
                result = "OK"
                return result
            else:
                texto = response.content.decode("utf-8")
                mensagem = texto.strip("{}'\"")
                logger.info("Erro ao Alterar email: %s", mensagem)
                raise SmeIntegracaoException(mensagem)
        except Exception as err:
            raise SmeIntegracaoException(str(err))

    @classmethod
    def consulta_cargos_funcionario(cls, registro_funcional: str) -> list:
        """
        Consulta cargos (base e sobreposto) de um servidor pelo RF.
        """
        if not registro_funcional:
            raise SmeIntegracaoException(MSG_RF_OBRIGATORIO)

        logger.info(
            "Consultando cargos do servidor no SME. RF: %s", registro_funcional
        )

        try:
            cargos = cls._buscar_cargos(registro_funcional)
            return [cls._normalizar_cargo(cargo) for cargo in cargos]

        except requests.exceptions.RequestException as e:
            logger.exception("Erro de comunicação com API de cargos")
            raise SmeIntegracaoException(MSG_ERRO_COMUNICACAO_SME) from e

    @classmethod
    def _buscar_cargos(cls, registro_funcional: str) -> list:
        """Consulta cargos de um servidor na SME pelo RF.

        Args:
            registro_funcional (str): Registro funcional do servidor.

        Returns:
            list: Lista de cargos retornados pela API.

        Raises:
            SmeIntegracaoException: Quando a consulta falha.
        """
        url = f"{env('SME_INTEGRACAO_URL', default='')}/funcionarios/cargo/{registro_funcional}"  # noqa: E501

        response = requests.get(
            url,
            headers=cls.DEFAULT_HEADERS,
            timeout=cls.TIMEOUT,
        )

        if response.status_code != status.HTTP_200_OK:
            logger.error(
                "Erro ao consultar cargos. Status: %s | Body: %s",
                response.status_code,
                response.text,
            )
            raise SmeIntegracaoException(MSG_ERRO_CARGOS)

        return response.json()

    @classmethod
    def _normalizar_cargo(cls, cargo: dict) -> dict:
        """Normaliza os campos de cargo retornados pela SME.

        Converte nomes de cargos e monta as informações de unidade escolar.

        Args:
            cargo (dict): Dados do cargo retornado pela SME.

        Returns:
            dict: Dados de cargo normalizados.
        """
        if cargo.get("cargoBase"):
            cargo["cargoBase"] = cls.formatar_cargo(cargo["cargoBase"])

        if cargo.get("cargoSobreposto"):
            cargo["cargoSobreposto"] = cls.formatar_cargo(
                cargo["cargoSobreposto"]
            )

        cargo["ueCargoBase"] = cls._montar_ue(
            cargo.get("cdUeCargoBase"), cargo.get("ueCargoBase")
        )

        cargo["ueCargoSobreposto"] = cls._montar_ue(
            cargo.get("cdUeCargoSobreposto"), cargo.get("ueCargoSobreposto")
        )

        return cargo

    @classmethod
    def _montar_ue(
        cls, codigo_ue: str | int | None, nome_ue: str | None
    ) -> str | None:
        """Formata a descrição da unidade escolar para exibição.

        Args:
            codigo_ue (str|int): Código da unidade escolar.
            nome_ue (str): Nome da unidade escolar.

        Returns:
            str: Nome formatado da unidade ou o valor original quando não for
            possível.
        """
        if not codigo_ue:
            return nome_ue

        info = cls.consulta_informacoes_unidades_escolares(codigo_ue)
        sigla = info.get("siglaTipoEscola")

        if not sigla:
            return nome_ue

        nome_formatado = nome_ue
        return f"{sigla.upper()} - {nome_formatado}"

    @classmethod
    def buscar_funcionarios_escolares(cls, codigo_ue: str) -> list:
        """Busca servidores de gestão escolar para uma UE.

        Args:
            codigo_ue (str): Código da unidade escolar.

        Returns:
            list: Lista de cargos e servidores vinculados à UE.

        Raises:
            SmeIntegracaoException: Quando ocorre erro na consulta à SME.
        """

        if not codigo_ue:
            raise SmeIntegracaoException("Código da UE é obrigatório")

        funcionarios = []

        for cargo in CARGOS_GESTAO_ESCOLAR:
            codigo_cargo = cargo["codigoCargo"]

            url = (
                f"{env('SME_INTEGRACAO_URL', default='')}"
                f"/escolas/{codigo_ue}/funcionarios/cargos/{codigo_cargo}"
            )

            logger.info(
                "Consultando funcionários da UE %s para o cargo %s",
                codigo_ue,
                codigo_cargo,
            )

            try:
                response = requests.get(
                    url,
                    headers=cls.DEFAULT_HEADERS,
                    timeout=cls.TIMEOUT,
                )

                if response.status_code not in (
                    status.HTTP_200_OK,
                    status.HTTP_204_NO_CONTENT,
                ):
                    logger.error(
                        "Erro ao buscar cargo %s da UE %s | Status: %s | Body: %s",  # noqa: E501
                        codigo_cargo,
                        codigo_ue,
                        response.status_code,
                        response.text,
                    )
                    raise SmeIntegracaoException(
                        "Erro ao buscar funcionários da gestão escolar"
                    )

                if response.status_code == status.HTTP_204_NO_CONTENT:
                    servidores_api = []

                else:
                    try:
                        servidores_api = response.json()
                    except ValueError:
                        logger.error(
                            "Resposta inválida da SME | UE %s | Cargo %s | Body: %s",  # noqa: E501
                            codigo_ue,
                            codigo_cargo,
                            response.text,
                        )
                        servidores_api = []

                servidores_normalizados = [
                    {
                        "rf": servidor.get("codigoRF"),
                        "nome": servidor.get("nomeServidor"),
                        "esta_afastado": servidor.get("estaAfastado"),
                    }
                    for servidor in servidores_api
                ]

                funcionarios.append(
                    {
                        "codigo_cargo": codigo_cargo,
                        "nome_cargo": cargo["nomeCargo"],
                        "servidores": servidores_normalizados,
                    }
                )

            except requests.exceptions.RequestException as e:
                logger.exception(
                    "Erro de comunicação com SME | UE %s | Cargo %s",
                    codigo_ue,
                    codigo_cargo,
                )
                raise SmeIntegracaoException(MSG_ERRO_COMUNICACAO_SME) from e

        return funcionarios

    @classmethod
    def buscar_turmas_ue_ano(cls, codigo_ue: str, ano_letivo: int) -> list:
        """Busca todas as turmas de uma UE em um ano letivo.

        Args:
            codigo_ue (str): Código da unidade escolar.
            ano_letivo (int): Ano letivo.

        Returns:
            list: Lista de turmas encontradas.

        Raises:
            SmeIntegracaoException: Quando houver falha de comunicação
            ou dados inválidos.
        """
        if not codigo_ue or not ano_letivo:
            raise SmeIntegracaoException(
                "Código da UE e ano letivo são obrigatórios"
            )

        url = (
            f"{env('SME_INTEGRACAO_URL', default='')}"
            f"/escolas/{codigo_ue}/turmas/anos_letivos/{ano_letivo}"
        )

        try:
            response = requests.get(
                url,
                headers=cls.DEFAULT_HEADERS,
                timeout=cls.TIMEOUT,
            )

            if response.status_code == status.HTTP_200_OK:
                return response.json()

            raise SmeIntegracaoException(MSG_ERRO_CARGOS)

        except requests.exceptions.RequestException as e:
            logger.exception(
                "Erro de comunicação com API de turmas de um ano letivo"
            )
            raise SmeIntegracaoException(MSG_ERRO_COMUNICACAO_SME) from e

    @classmethod
    def buscar_dados_turma(cls, codigo_turma: int) -> dict:
        """Busca dados detalhados de uma turma.

        Args:
            codigo_turma (int): Identificador da turma.

        Returns:
            dict: Dados detalhados da turma.

        Raises:
            SmeIntegracaoException: Quando a turma não for encontrada ou a API
            falhar.
        """
        if not codigo_turma:
            raise SmeIntegracaoException("Código da turma é obrigatório")

        url = (
            f"{env('SME_INTEGRACAO_URL', default='')}"
            f"/turmas/{codigo_turma}/dados"
        )

        try:
            response = requests.get(
                url,
                headers=cls.DEFAULT_HEADERS,
                timeout=cls.TIMEOUT,
            )

            if response.status_code == status.HTTP_200_OK:
                return response.json()

            raise SmeIntegracaoException(MSG_ERRO_CARGOS)

        except requests.exceptions.RequestException as e:
            logger.exception("Erro de comunicação com API de dados da turma")
            raise SmeIntegracaoException(MSG_ERRO_COMUNICACAO_SME) from e

    @classmethod
    def consulta_informacoes_unidades_escolares(cls, codigo_ue: str) -> list:
        """Consulta informações de uma unidade escolar na SME.

        Args:
            codigo_ue (str): Código da unidade escolar.

        Returns:
            list: Dados detalhados da unidade escolar.

        Raises:
            SmeIntegracaoException: Quando houver problema de conexão
            ou retorno inválido.
        """
        if not codigo_ue:
            raise SmeIntegracaoException(MSG_RF_OBRIGATORIO)

        logger.info(
            "Consultando informações da unidade escolar em SME. código: %s",
            codigo_ue,
        )

        try:
            url = f"{env('SME_INTEGRACAO_URL', default='')}/escolas/dados/{codigo_ue}"  # noqa: E501

            response = requests.get(
                url,
                headers=cls.DEFAULT_HEADERS,
                timeout=cls.TIMEOUT,
            )

            if response.status_code == status.HTTP_200_OK:
                return response.json()

            logger.error(
                "Erro ao consultar informações da unidade escolar. Status: %s | Body: %s",  # noqa: E501
                response.status_code,
                response.text,
            )
            raise SmeIntegracaoException(
                "Erro ao consultar informações da unidade escolar"
            )

        except requests.exceptions.RequestException as e:
            logger.exception(
                "Erro de comunicação com API de informações da unidade escolar"
            )
            raise SmeIntegracaoException(MSG_ERRO_COMUNICACAO_SME) from e

    @classmethod
    def buscar_disciplinas_turma(cls, codigo_turma: int) -> list:
        """Busca disciplinas vinculadas a uma turma.

        Args:
            codigo_turma (int): Identificador da turma.

        Returns:
            list: Lista de disciplinas vinculadas.

        Raises:
            SmeIntegracaoException: Quando a API retornar erro ou
            houver falha de comunicação.
        """
        if not codigo_turma:
            raise SmeIntegracaoException("Código da turma é obrigatório")

        url = (
            f"{env('SME_INTEGRACAO_URL', default='')}"
            f"/funcionarios/turmas/{codigo_turma}/disciplinas"
        )

        logger.info(
            "Consultando disciplinas da turma no SME. Turma: %s", codigo_turma
        )

        try:
            response = requests.get(
                url,
                headers=cls.DEFAULT_HEADERS,
                timeout=cls.TIMEOUT,
            )

            if response.status_code == status.HTTP_200_OK:
                try:
                    return response.json()
                except ValueError:
                    logger.error(
                        "Resposta inválida ao consultar disciplinas da turma %s | Body: %s",  # noqa: E501
                        codigo_turma,
                        response.text,
                    )
                    return []

            if response.status_code == status.HTTP_204_NO_CONTENT:
                return []

            logger.error(
                "Erro ao consultar disciplinas da turma %s | Status: %s | Body: %s",  # noqa: E501
                codigo_turma,
                response.status_code,
                response.text,
            )
            raise SmeIntegracaoException(MSG_ERRO_COMUNICACAO_SME)

        except requests.exceptions.RequestException as e:
            logger.exception(
                "Erro de comunicação com API de disciplinas da turma %s",
                codigo_turma,
            )
            raise SmeIntegracaoException(MSG_ERRO_COMUNICACAO_SME) from e

    @staticmethod
    def formatar_cargo(texto: str) -> str:
        """Formata o nome de um cargo extraindo a parte principal.

        Args:
            texto (str): Texto do cargo retornado pela SME.

        Returns:
            str: Cargo formatado ou vazio quando o texto for inválido.
        """
        if not texto:
            return ""

        return texto.split("-")[0].strip()
