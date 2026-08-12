Alteração de E-mail
====================

Visão geral
-----------

O domínio de **Alteração de E-mail** (``apps.alteracao_email``) implementa
o fluxo de troca do e-mail institucional de um usuário autenticado do
SIGNA, por confirmação via link enviado ao **novo** endereço de e-mail.

Fluxo em alto nível: o usuário autenticado solicita a troca → o sistema
gera um token único, persiste a solicitação e envia um e-mail de
confirmação para o **novo** endereço → o usuário clica no link → o
sistema valida o token, efetiva a troca no **CoreSSO/SME** e só então
atualiza o ``User`` local, marcando o token como usado.

.. important::
   Assim como no fluxo de senha do domínio :doc:`Usuários
   </dominios/usuarios/index>`, o CoreSSO/SME é a fonte da verdade: a
   troca de e-mail só é considerada efetivada depois que
   ``SmeIntegracaoService.altera_email`` confirma a alteração no sistema
   externo. A atualização do ``User`` local acontece **depois**, dentro
   da mesma transação.

Modelo
------

Único modelo do domínio: ``AlteracaoEmail`` (``apps/alteracao_email/models/alteracao_email.py``).

.. list-table::
   :header-rows: 1
   :widths: 20 25 55

   * - Campo
     - Tipo
     - Descrição
   * - ``usuario``
     - ``ForeignKey(AUTH_USER_MODEL, on_delete=CASCADE)``
     - Usuário solicitante. Excluir o usuário exclui em cascata suas solicitações.
   * - ``novo_email``
     - ``EmailField``
     - Endereço para o qual o usuário deseja migrar.
   * - ``token``
     - ``UUIDField(default=uuid.uuid4, unique=True)``
     - Identificador da solicitação, usado na URL de confirmação. Único, mas não é a PK do modelo.
   * - ``criado_em``
     - ``DateTimeField(auto_now_add=True)``
     - Timestamp de criação, base do cálculo de expiração.
   * - ``ja_usado``
     - ``BooleanField(default=False)``
     - Flag de uso único do token, setada para ``True`` após confirmação bem-sucedida.

Não há choices/enums nem métodos de negócio no modelo — toda regra vive na
camada de serviço. Existe apenas uma migration (``0001_initial``), sem
evolução posterior de schema. **O modelo não está registrado no Django
Admin** — não há ``admin.py`` neste app.

Regras de negócio
------------------

Solicitação (``AlteracaoEmailService.solicitar``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Cria um registro ``AlteracaoEmail`` (token gerado automaticamente).
2. Monta o link de confirmação: ``{AMBIENTE_URL}/confirmar-email/{token}``.
3. Envia e-mail (template ``emails/alteracao_email.html``) para o
   **novo** endereço — não para o e-mail atual — via
   ``EnviaEmailService.enviar`` (domínio :doc:`Usuários </dominios/usuarios/index>`).
4. Retorna a instância criada.

Não há integração com a SME nesta etapa — a chamada ao CoreSSO só ocorre
na confirmação. Também **não há rate limiting**: nada impede múltiplas
solicitações simultâneas do mesmo usuário; cada uma gera um token
independente e as anteriores continuam válidas até expirarem ou serem
usadas.

A validação de que o e-mail é institucional, diferente do atual e não
duplicado acontece na camada de **serializer**, antes de chamar o
service (ver :ref:`alteracao-email-validacoes`).

Confirmação (``AlteracaoEmailService.validar``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def validar(token: str) -> tuple[User, AlteracaoEmail]:
        email_request = get_object_or_404(AlteracaoEmail, token=token)
        usuario = email_request.usuario

        if email_request.ja_usado:
            raise TokenJaUtilizadoError("Este token já foi utilizado.")

        if email_request.criado_em < now() - timedelta(minutes=30):
            raise TokenExpiradoError("Token expirado.")

        return usuario, email_request

- **Token inexistente** → ``Http404``.
- **Token já usado** → ``TokenJaUtilizadoError``.
- **Token expirado** — janela fixa de **30 minutos** desde ``criado_em``
  — → ``TokenExpiradoError``. Consistente com o aviso no e-mail enviado
  ("Este link é válido por 30 minutos.").
- Se válido, o método **apenas retorna** ``(usuario, email_request)`` —
  não marca ``ja_usado`` nem persiste nada. Essa responsabilidade é da
  view, que orquestra a efetivação completa (ver abaixo).

Efetivação da troca (orquestrada pela view, em transação atômica)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    1. AlteracaoEmailService.validar(token)          → valida token
    2. SmeIntegracaoService.altera_email(rf, email)  → efetiva no CoreSSO
    3. usuario.email = novo_email; usuario.save()    → persiste localmente
    4. email_request.ja_usado = True; save()         → invalida o token

Todo o bloco roda dentro de ``transaction.atomic()``: se a chamada à SME
falhar, nada é persistido no banco local. Note que a chamada HTTP externa
à SME, se ela chegar a ser efetuada, não é "desfeita" por um rollback de
banco — apenas os efeitos locais são revertidos.

.. _alteracao-email-validacoes:

Validações do novo e-mail (``AlteracaoEmailSerializer``)
------------------------------------------------------------

Executadas em ``validate_new_email``, nesta ordem:

1. **Igual ao atual** — ``usuario.email == value`` → "O novo e-mail não
   pode ser igual ao atual."
2. **Domínio institucional** — precisa terminar em
   ``@sme.prefeitura.sp.gov.br`` → "Utilize seu e-mail institucional."
3. **Duplicidade** — ``User.objects.filter(email=value).exists()`` →
   "Este e-mail já está cadastrado." (checa contra a tabela de usuários,
   não contra outras solicitações ``AlteracaoEmail`` pendentes).
4. **Formato** — ``django.core.validators.validate_email`` → "Digite um
   e-mail válido!"

.. note::
   Como a checagem de domínio (etapa 2) roda antes da checagem de
   formato (etapa 4), um e-mail malformado que ainda termine no domínio
   correto (ex.: ``invalido@@sme.prefeitura.sp.gov.br``) passa pela
   etapa 2 e só falha na 4. Já um e-mail malformado que não termina no
   domínio correto (ex.: ``novo@gmail.com@``) falha antes, na etapa 2,
   com a mensagem de "e-mail institucional" — mesmo sendo, na prática,
   um problema de formato.

Todos os erros de validação do serializer (não só deste campo) são
normalizados em um único formato de resposta ``{"detail": "<primeira
mensagem de erro>"}``, em vez do dicionário padrão por campo do DRF.

API
---

Roteado sob ``api/alteracao-email/`` (namespace ``alteracao_email``, via
``DefaultRouter`` do DRF).

.. list-table::
   :header-rows: 1
   :widths: 10 30 16 44

   * - Método
     - Rota
     - Permissão
     - Descrição
   * - ``POST``
     - ``solicitar/``
     - ``IsAuthenticated``
     - Recebe ``{"new_email": "..."}``, valida, cria a solicitação e envia o e-mail de confirmação. Sucesso: **201** ``{"message": "E-mail de confirmação enviado com sucesso."}``.
   * - ``PUT``
     - ``validar/<token>/``
     - ``IsAuthenticated``
     - Valida o token (via URL, como ``pk``) e efetiva a troca de e-mail. Sucesso: **200** ``{"message": "E-mail alterado com sucesso.", "email": "..."}``.

Tratamento de erros em ``validar/<token>/``:

.. list-table::
   :header-rows: 1
   :widths: 40 15 45

   * - Situação
     - Status
     - Corpo
   * - ``TokenJaUtilizadoError``
     - 400
     - ``{"detail": "Este token já foi utilizado."}``
   * - ``TokenExpiradoError``
     - 400
     - ``{"detail": "Token expirado."}``
   * - ``SmeIntegracaoError``
     - 400
     - ``{"detail": "<mensagem da SME>"}`` — logado como erro.
   * - Token inexistente (``Http404``)
     - 404
     - ``{"detail": "Token não encontrado."}``
   * - Exceção genérica
     - 500
     - ``{"detail": "Erro inesperado."}``

Template de e-mail
--------------------

``apps/templates/emails/alteracao_email.html`` — HTML simples com CSS
inline, sem herança de layout. Contexto esperado: ``usuario_nome`` (nome
do solicitante) e ``link`` (URL de confirmação). Conteúdo: saudação,
explicação do pedido de troca, link de confirmação, aviso de validade de
30 minutos e aviso de segurança orientando a ignorar o e-mail caso a
troca não tenha sido solicitada pelo próprio usuário.

Integrações
-----------

- :doc:`Usuários </dominios/usuarios/index>` — fornece
  ``SmeIntegracaoService.altera_email`` (efetivação da troca no
  CoreSSO/SME) e ``EnviaEmailService.enviar`` (envio do e-mail de
  confirmação); o modelo ``AlteracaoEmail`` tem FK para ``User``.
- ``AMBIENTE_URL`` (mesma variável de ambiente usada pelo fluxo de
  recuperação de senha) monta o link de confirmação.
- Exceções de domínio compartilhadas (``apps.helpers.exceptions``):
  ``TokenJaUtilizadoError``, ``TokenExpiradoError``, ``SmeIntegracaoError``.
