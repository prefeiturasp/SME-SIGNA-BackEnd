import logging
import environ
import requests

from apps.helpers.exceptions import (
    AuthenticationError,
    InternalError,
    SmeIntegracaoException
)
from apps.designacao.constants.cargos_gestao_escolar import (
    CARGOS_GESTAO_ESCOLAR
)

from rest_framework import status

MSG_RF_OBRIGATORIO = "Registro funcional é obrigatório"
MSG_ERRO_COMUNICACAO_SME = "Erro de comunicação com SME"
MSG_ERRO_COMUNICACAO_CORESSO = "Erro de comunicação com CoreSSO"
MSG_ERRO_CARGOS = "Erro ao consultar cargos do servidor"

env = environ.Env()
logger = logging.getLogger(__name__)

class SmeIntegracaoService:
    """ Serviço responsável por autenticar usuário no CoreSSO (SME) """

    DEFAULT_HEADERS = {
        "accept": "application/json",
        "x-api-eol-key": env("SME_INTEGRACAO_TOKEN", default=""),
    }
    TIMEOUT = 30

    @classmethod
    def autentica(cls, login: str, senha: str) -> dict:
        payload = {
            "usuario": login,
            "senha": senha,
            "codigoSistema": env('CODIGO_SISTEMA_SIGNA', default='')
        }

        url = f"{env('SME_INTEGRACAO_URL', default='')}/v1/autenticacao/externa"

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
    def informacao_usuario_sgp(cls, username):
        logger.info(f"Consultando dados na API externa para: {username}")
        try:
            url = f"{env('SME_INTEGRACAO_URL', default='')}/AutenticacaoSgp/{username}/dados"  
            response = requests.get(url, headers=cls.DEFAULT_HEADERS, timeout=10)

            if response.status_code == status.HTTP_200_OK:
                return response.json()

            else:
                logger.info(f"Dados não encontrados: {response}")
                raise SmeIntegracaoException('Dados não encontrados.')

        except requests.RequestException:
            logger.exception("Erro de conexão com a API externa")
            raise requests.RequestException("Erro ao conectar-se à API externa.")


    @classmethod
    def redefine_senha(cls, registro_funcional, senha):
        """
        Redefine a senha de um usuário no sistema SME.
        
        IMPORTANTE: Se a nova senha for uma das senhas padrões, a API do SME 
        não permite a atualização. Para resetar para senha padrão, use o endpoint ReiniciarSenha.
        
        Args:
            registro_funcional: Username/registro funcional do usuário
            senha: Nova senha
            
        Returns:
            Dict[str, Any]: Resposta da API ou confirmação de sucesso
            
        Raises:
            SmeIntegracaoException: Em caso de erro na operação
        """

        if not registro_funcional or not senha:
            raise SmeIntegracaoException("Registro funcional e senha são obrigatórios")
        
        logger.info(
            "Iniciando redefinição de senha no CoreSSO para usuário: %s", 
            registro_funcional
        )
        
        data = {
            'Usuario': registro_funcional,
            'Senha': senha
        }

        try:

            url = f"{env('SME_INTEGRACAO_URL', default='')}/AutenticacaoSgp/AlterarSenha"  

            response = requests.post(url, data=data, headers=cls.DEFAULT_HEADERS)

            if response.status_code == status.HTTP_200_OK:
                result = "OK"
                return result
            else:
                texto = response.content.decode('utf-8')
                mensagem = texto.strip("{}'\"")
                logger.info("Erro ao redefinir senha: %s", mensagem)
                raise SmeIntegracaoException(mensagem)
        except Exception as err:
            raise SmeIntegracaoException(str(err))
        

    @classmethod
    def altera_email(cls, registro_funcional, email):
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
            raise SmeIntegracaoException("Registro funcional e email são obrigatórios")
        
        logger.info(
            "Iniciando alteração de email no CoreSSO para usuário: %s", 
            registro_funcional
        )
        
        data = {
            'Usuario': registro_funcional,
            'Email': email
        }

        try:

            url = f"{env('SME_INTEGRACAO_URL', default='')}/AutenticacaoSgp/AlterarEmail"

            response = requests.post(url, data=data, headers=cls.DEFAULT_HEADERS)

            if response.status_code == status.HTTP_200_OK:
                result = "OK"
                return result
            else:
                texto = response.content.decode('utf-8')
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
            "Consultando cargos do servidor no SME. RF: %s",
            registro_funcional
        )

        try:
            url = (
                f"{env('SME_INTEGRACAO_URL', default='')}/funcionarios/cargo/{registro_funcional}"
            )

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

            cargos = response.json()

            for cargo in cargos:
                cd_ue_base = cargo.get("cdUeCargoBase")
                if cd_ue_base:
                    info_base = cls.consulta_informacoes_unidades_escolares(cd_ue_base)
                    sigla_base = info_base.get("siglaTipoEscola")

                    if sigla_base:
                        cargo["ueCargoBase"] = f"{sigla_base} - {cargo.get('ueCargoBase')}"

                cd_ue_sobreposto = cargo.get("cdUeCargoSobreposto")
                if cd_ue_sobreposto:
                    info_sobreposto = cls.consulta_informacoes_unidades_escolares(cd_ue_sobreposto)
                    sigla_sobreposto = info_sobreposto.get("siglaTipoEscola")

                    if sigla_sobreposto:
                        cargo["ueCargoSobreposto"] = f"{sigla_sobreposto} - {cargo.get('ueCargoSobreposto')}"

            return cargos

        except requests.exceptions.RequestException as e:
            logger.exception("Erro de comunicação com API de cargos")
            raise SmeIntegracaoException(MSG_ERRO_COMUNICACAO_SME) from e


    @classmethod
    def buscar_funcionarios_escolares(cls, codigo_ue: str) -> list:
        """
        Busca os servidores de cargos de gestão escolar vinculados a uma UE.
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
                codigo_cargo
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
                        "Erro ao buscar cargo %s da UE %s | Status: %s | Body: %s",
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
                            "Resposta inválida da SME | UE %s | Cargo %s | Body: %s",
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

                funcionarios.append({
                    "codigo_cargo": codigo_cargo,
                    "nome_cargo": cargo["nomeCargo"],
                    "servidores": servidores_normalizados,
                })


            except requests.exceptions.RequestException as e:
                logger.exception(
                    "Erro de comunicação com SME | UE %s | Cargo %s",
                    codigo_ue,
                    codigo_cargo,
                )
                raise SmeIntegracaoException(
                    MSG_ERRO_COMUNICACAO_SME
                ) from e

        return funcionarios


    @classmethod
    def buscar_turmas_ue_ano(cls, codigo_ue: str, ano_letivo: int) -> list:
        """
        Busca todas as turmas de uma UE em um determinado ano letivo.
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
            logger.exception("Erro de comunicação com API de turmas de um ano letivo")
            raise SmeIntegracaoException(MSG_ERRO_COMUNICACAO_SME) from e


    @classmethod
    def buscar_dados_turma(cls, codigo_turma: int) -> dict:
        """
        Busca dados detalhados de uma turma.
        """
        if not codigo_turma:
            raise SmeIntegracaoException(
                "Código da turma é obrigatório"
            )

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
        """
        Consulta informacoes de unidades escolares pelo código.
        """
        if not codigo_ue:
            raise SmeIntegracaoException(MSG_RF_OBRIGATORIO)

        logger.info(
            "Consultando informações da unidade escolar em SME. código: %s",
            codigo_ue
        )

        try:
            url = (
                f"{env('SME_INTEGRACAO_URL', default='')}/escolas/dados/{codigo_ue}"
            )

            response = requests.get(
                url,
                headers=cls.DEFAULT_HEADERS,
                timeout=cls.TIMEOUT,
            )

            if response.status_code == status.HTTP_200_OK:
                return response.json()

            logger.error(
                "Erro ao consultar informações da unidade escolar. Status: %s | Body: %s",
                response.status_code,
                response.text,
            )
            raise SmeIntegracaoException("Erro ao consultar informações da unidade escolar")

        except requests.exceptions.RequestException as e:
            logger.exception("Erro de comunicação com API de informações da unidade escolar")
            raise SmeIntegracaoException(MSG_ERRO_COMUNICACAO_SME) from e
