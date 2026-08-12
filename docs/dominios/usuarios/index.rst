Usuários
========

Visão geral
-----------

O domínio de **Usuários** (``apps.usuarios``) é responsável pela
**autenticação, identidade e gestão de credenciais** de todo o SIGNA.
Concentra três responsabilidades:

- o modelo de usuário customizado (``User``), configurado como
  ``AUTH_USER_MODEL`` do projeto;
- o fluxo de **login, recuperação e alteração de senha**, integrado ao
  **CoreSSO/SME** (sistema de autenticação centralizado da Secretaria
  Municipal de Educação de São Paulo), com emissão de tokens **JWT**
  (Simple JWT) para as demais chamadas de API;
- o :class:`~apps.usuarios.services.sme_integracao_service.SmeIntegracaoService`,
  cliente HTTP central para a API de integração da SME (autenticação,
  dados de servidor, cargos, unidades escolares, turmas e disciplinas),
  reaproveitado por outros domínios do sistema (Designação, Alteração de
  E-mail).

.. important::
   O SIGNA **não valida senha localmente**. O CoreSSO/SME é a fonte da
   verdade de credenciais: todo login, redefinição e alteração de senha é
   validado contra a SME primeiro. O banco de dados local é um espelho
   *best-effort* — sincronizado a cada login e a cada troca de senha bem
   sucedida, mas sua falha isolada não impede a operação, já que a SME
   já confirmou a mudança.

Modelo de usuário
-------------------

``User`` (``apps/usuarios/models.py``) estende
``django.contrib.auth.models.AbstractUser`` e é o ``AUTH_USER_MODEL``
global do projeto (``config/settings/base.py``: ``AUTH_USER_MODEL =
"usuarios.User"``).

Campos adicionados aos herdados de ``AbstractUser``:

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Campo
     - Tipo
     - Descrição
   * - ``uuid``
     - ``UUIDField``
     - Gerado automaticamente (``uuid4``), único, não editável.
   * - ``name``
     - ``CharField(150)``
     - Nome completo, pode ser vazio.
   * - ``cpf``
     - ``CharField(11)``
     - Único, opcional — espelha o ``numeroDocumento`` retornado pela SME.
   * - ``email``
     - ``EmailField``
     - Sobrescreve o campo padrão do ``AbstractUser`` para ser único.

Os campos herdados relevantes seguem o padrão do Django: ``username``
(único, é o **Registro Funcional — RF**, não um login livre — ver
:ref:`fluxo-login`), ``password``, ``is_staff``, ``is_superuser``,
``is_active``, ``last_login``, ``groups``, ``user_permissions``.

``User.save()`` é sobrescrito para garantir que a senha nunca seja
persistida em texto plano: se ``self.password`` estiver preenchido e não
começar com um prefixo de hash conhecido (``pbkdf2_``, ``bcrypt``,
``argon2``), chama ``self.set_password(self.password)`` antes de salvar —
proteção contra atribuição direta acidental do atributo ``password``.

Não há sistema de perfis/papéis modelado dentro do app — ver
:ref:`perfis-de-acesso`.

Autenticação
-------------

O SIGNA não define ``AUTHENTICATION_BACKENDS`` nem middleware de
autenticação customizado — usa o ``ModelBackend`` padrão do Django apenas
como suporte ao admin. A autenticação real de API é 100% via
``rest_framework_simplejwt.authentication.JWTAuthentication``, configurada
globalmente:

.. code-block:: python

    REST_FRAMEWORK = {
        "DEFAULT_AUTHENTICATION_CLASSES": (
            "rest_framework_simplejwt.authentication.JWTAuthentication",
        ),
        "DEFAULT_PERMISSION_CLASSES": (
            "rest_framework.permissions.IsAuthenticated",
        ),
    }

    SIMPLE_JWT = {
        "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
        "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
        "ROTATE_REFRESH_TOKENS": False,
        "BLACKLIST_AFTER_ROTATION": False,
        "AUTH_HEADER_TYPES": ("Bearer",),
    }

Ou seja, **toda view exige ``Authorization: Bearer <token>`` por padrão**,
a menos que declare explicitamente ``permission_classes = (AllowAny,)``
(caso de login e dos endpoints de recuperação de senha).

.. _fluxo-login:

Fluxo de login
~~~~~~~~~~~~~~~

``POST /api/usuario/login`` (``LoginView``, que herda de
``TokenObtainPairView`` mas sobrescreve completamente o ``post``):

.. code-block:: text

    1. LoginSerializer valida o payload:
       - username: normalizado removendo tudo que não é dígito,
         precisa resultar em 7 ou 8 dígitos (Registro Funcional)
       - password
    2. SmeIntegracaoService.autentica(login, senha)
       → POST {SME_INTEGRACAO_URL}/v1/autenticacao/externa (CoreSSO)
    3. Valida se o perfil SIGNA (env GUIDE_PERFIL_SIGNA) está entre os
       perfis retornados pelo CoreSSO — senão, PerfilNaoAutorizadoError
    4. SmeIntegracaoService.sincronizar_usuario_local(...)
       → cria/atualiza o User local (nome, email, cpf, senha, last_login)
    5. Gera tokens JWT (access + refresh) com claims extras
       (username, name, email)
    6. Responde 200: {"token": <access>, "name", "email", "cpf"}
       (o refresh token não é devolvido no corpo)

O login **sempre re-sincroniza** os dados do usuário local a cada
autenticação bem-sucedida — nome, e-mail e senha locais são sobrescritos
com os dados vindos da SME, mesmo que já existam localmente com valores
diferentes.

Tratamento de erros: ``AuthenticationError`` → 401 (credenciais
inválidas); ``SmeIntegracaoError`` → 400 (instabilidade da integração);
``PerfilNaoAutorizadoError`` → 401 (usuário autenticado na SME, mas sem o
perfil de acesso ao SIGNA); exceção genérica → 500.

.. _perfis-de-acesso:

Perfis de acesso
~~~~~~~~~~~~~~~~~~

Não existe um sistema de perfis/papéis granular dentro do SIGNA (não há
model ``Perfil`` nem uso de ``Group``/``Permission`` nas rotas de API). O
controle de acesso é **binário** e delegado ao CoreSSO:

- o CoreSSO retorna, na resposta de autenticação, uma lista ``perfis``
  com os códigos de perfil que o servidor possui nos diversos sistemas
  municipais;
- ``LoginView`` compara essa lista (normalizada para uppercase) contra a
  variável de ambiente ``GUIDE_PERFIL_SIGNA``: só quem possui esse
  código de perfil cadastrado na SME consegue autenticar no SIGNA.

Permissões Django padrão (``is_staff``, ``is_superuser``, ``groups``,
``user_permissions``) seguem disponíveis apenas para o **admin do
Django** — não são usadas para controle de acesso na API.

Recuperação e alteração de senha
-----------------------------------

Três fluxos distintos, todos delegando a alteração real de senha à SME
via ``SmeIntegracaoService.redefine_senha`` e só então tentando espelhar
localmente:

.. list-table::
   :header-rows: 1
   :widths: 15 25 15 45

   * - Método
     - Rota
     - Permissão
     - Descrição
   * - ``POST``
     - ``esqueci-senha``
     - ``AllowAny``
     - Recebe ``username``, consulta a SME (``informacao_usuario_sgp``), obtém o e-mail cadastrado, gera token de reset (``django.contrib.auth.tokens.default_token_generator``) e envia e-mail com o link de redefinição.
   * - ``POST``
     - ``redefinir-senha``
     - ``AllowAny``
     - Recebe ``uid``/``token`` (gerados no passo anterior) + nova senha; valida o token, redefine a senha na SME e tenta espelhar localmente.
   * - ``POST``
     - ``atualizar-senha``
     - ``IsAuthenticated``
     - Troca de senha por um usuário já autenticado: valida a senha atual (``check_password``), redefine na SME e espelha localmente.

Fluxo "esqueci minha senha" (``EsqueciMinhaSenhaViewSet``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Busca o usuário local (``SenhaService.buscar_usuario_local``).
2. Consulta a SME (``informacao_usuario_sgp``); se a consulta falhar e o
   usuário também não existir localmente → ``UserNotFoundError``. Se
   existir localmente, segue com os dados da SME ausentes (fallback
   silencioso).
3. Determina o e-mail de destino priorizando o retornado pela SME sobre o
   local; se nenhum dos dois tiver e-mail → ``EmailNaoCadastradoError``.
4. Se a SME retornou dados com ``nome``, sincroniza o usuário local
   (``SenhaService.sincronizar_usuario_local`` — não sobrescreve nada se
   ``nome`` estiver ausente, para não gravar dados vazios).
5. Gera ``uid``/``token`` (``SenhaService.gerar_token_para_reset``), monta
   o link ``{AMBIENTE_URL}/recuperar-senha/{uid}/{token}`` e envia e-mail
   HTML (template ``emails/reset_senha.html``) via ``EnviaEmailService``.
6. Responde com o e-mail de destino **anonimizado**
   (``apps.helpers.utils.anonimizar_email``, ex.:
   ``joaosilva@email.com`` → ``joa****@email.com``), para não expor o
   e-mail completo de terceiros na resposta.

``IntegrityError`` na sincronização (ex.: e-mail já usado por outro RF)
vira ``EmailNaoCadastradoError`` amigável.

Redefinição via token (``RedefinirSenhaViewSet``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``RedefinirSenhaSerializer`` decodifica o ``uid`` (base64 urlsafe),
localiza o ``User``, valida o ``token`` com
``default_token_generator.check_token`` e confere a confirmação de senha.
Em seguida:

- ``SmeIntegracaoService.redefine_senha`` é **crítico** — se falhar,
  responde 400 com a mensagem de erro da SME;
- ``SenhaService.atualizar_senha_local`` é **best-effort** — se falhar
  (ex.: erro de banco), a exceção é apenas logada e a resposta ainda é
  **200 de sucesso**, já que a SME já confirmou a alteração (fonte da
  verdade).

Atualização de senha autenticada (``AtualizarSenhaViewSet``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Exige um ``request.user`` autenticado; ``AtualizarSenhaSerializer`` valida
a senha atual (``check_password``) e a confirmação da nova senha antes de
repetir a mesma sequência crítico (SME) → best-effort (local) descrita
acima.

.. note::
   Redefinir uma senha para um valor considerado "padrão" pelo sistema da
   SME é recusado pela própria API externa — o endpoint usado
   (``AlterarSenha``) não deve ser confundido com ``ReiniciarSenha``
   (reset para senha padrão), que não é implementado neste domínio.

Integração com a SME/CoreSSO
-------------------------------

``SmeIntegracaoService`` (``apps/usuarios/services/sme_integracao_service.py``)
é uma classe utilitária (métodos de classe/estáticos, não instanciada) que
concentra toda a comunicação HTTP com a API de integração da SME/EOL. As
chamadas usam o header ``x-api-eol-key`` (token estático, variável de
ambiente ``SME_INTEGRACAO_TOKEN``) contra a base ``SME_INTEGRACAO_URL``,
com timeout padrão de 30s (10s apenas em ``informacao_usuario_sgp``).

.. list-table::
   :header-rows: 1
   :widths: 26 40 34

   * - Método
     - Endpoint externo
     - Descrição
   * - ``autentica(login, senha)``
     - ``POST /v1/autenticacao/externa``
     - Autentica no CoreSSO com ``{usuario, senha, codigoSistema}``. Levanta ``AuthenticationError`` (credenciais inválidas) ou ``SmeIntegracaoError``.
   * - ``informacao_usuario_sgp(username)``
     - ``GET /AutenticacaoSgp/{username}/dados``
     - Dados cadastrais do servidor no SGP (nome, e-mail, ``numeroDocumento``, perfis).
   * - ``redefine_senha(rf, senha)``
     - ``POST /AutenticacaoSgp/AlterarSenha``
     - Redefine a senha do servidor no CoreSSO/SME.
   * - ``altera_email(rf, email)``
     - ``POST /AutenticacaoSgp/AlterarEmail``
     - Altera o e-mail cadastrado no CoreSSO/SME (usado pelo domínio de Alteração de E-mail).
   * - ``consulta_cargos_funcionario(rf)``
     - ``GET /funcionarios/cargo/{rf}``
     - Cargo base e cargo sobreposto do servidor, com nome da UE enriquecido pela sigla do tipo de escola.
   * - ``buscar_funcionarios_escolares(codigo_ue)``
     - ``GET /escolas/{codigo_ue}/funcionarios/cargos/{codigo_cargo}`` *(uma chamada por cargo)*
     - Servidores lotados na UE, por cargo de gestão escolar (Diretor, Assistente de Diretor, Coordenador Pedagógico, Secretário, Supervisor Escolar).
   * - ``buscar_turmas_ue_ano(codigo_ue, ano)``
     - ``GET /escolas/{codigo_ue}/turmas/anos_letivos/{ano}``
     - Turmas de uma unidade em um ano letivo.
   * - ``buscar_dados_turma(codigo_turma)``
     - ``GET /turmas/{codigo_turma}/dados``
     - Detalhes de uma turma (ex.: turno).
   * - ``buscar_disciplinas_turma(codigo_turma)``
     - ``GET /funcionarios/turmas/{codigo_turma}/disciplinas``
     - Disciplinas de uma turma.
   * - ``consulta_informacoes_unidades_escolares(codigo_ue)``
     - ``GET /escolas/dados/{codigo_ue}``
     - Dados da unidade escolar (sigla do tipo de escola, endereço, nome).
   * - ``formatar_cargo(texto)``
     - —
     - Utilitário local: extrai o nome do cargo antes do primeiro ``"-"`` (ex.: ``"DIRETOR - ESCOLA"`` → ``"DIRETOR"``).

Chamadas ``GET`` sem corpo esperado tratam ``204`` e JSON inválido na
resposta como lista vazia (não levantam exceção), para não quebrar telas
agregadoras que dependem de múltiplas chamadas. Erros de status
inesperado ou falha de conexão (``requests.RequestException``) são
convertidos em ``apps.helpers.exceptions.SmeIntegracaoError`` na maioria
dos métodos.

.. important::
   ``SmeIntegracaoService`` é reaproveitado por outros domínios:

   - **Designação** — ``DesignacaoServidorService`` e
     ``DesignacaoUnidadeService`` usam praticamente todos os métodos de
     consulta (servidor, cargos, unidades, turmas, disciplinas) para
     montar dados de designação e calcular módulo de cargos.
   - **Alteração de E-mail** — usa ``altera_email`` para propagar a
     alteração confirmada de volta ao CoreSSO/SME.

   O domínio de **Unidades** não reutiliza esta classe: replica o mesmo
   padrão de integração (mesmo header, mesma URL base) de forma
   independente em ``apps.unidades.services.unidades_service``.

Envio de e-mail
-----------------

``EnviaEmailService`` (``apps/usuarios/services/envia_email_service.py``)
é um wrapper fino sobre o backend de e-mail padrão do Django
(``django.core.mail.EmailMessage``), usado no fluxo de "esqueci minha
senha":

- ``validar(destinatario, assunto)`` — levanta ``ValidationError`` se
  destinatário ou assunto estiverem vazios.
- ``renderizar_corpo(template_html, contexto)`` — ``render_to_string``.
- ``enviar(destinatario, assunto, template_html, contexto)`` — monta e
  envia um ``EmailMessage`` com ``content_subtype = "html"``; erros de
  validação são repropagados, qualquer outra falha vira
  ``RuntimeError("Erro inesperado ao enviar e-mail.")``.

API
---

Todas as rotas estão sob o prefixo ``api/usuario/``
(``config/urls.py: path("api/usuario/", include("apps.usuarios.urls"))``).

.. list-table::
   :header-rows: 1
   :widths: 10 22 16 52

   * - Método
     - Rota
     - Permissão
     - Descrição
   * - ``POST``
     - ``login``
     - ``AllowAny``
     - Autentica via CoreSSO, valida perfil SIGNA, sincroniza usuário local, retorna JWT access token e dados básicos.
   * - ``POST``
     - ``esqueci-senha``
     - ``AllowAny``
     - Inicia o fluxo de recuperação de senha (envio de e-mail com link de redefinição).
   * - ``POST``
     - ``redefinir-senha``
     - ``AllowAny``
     - Redefine a senha a partir de ``uid``/``token`` recebidos por e-mail.
   * - ``POST``
     - ``atualizar-senha``
     - ``IsAuthenticated``
     - Troca de senha de um usuário já autenticado.
   * - ``GET``
     - ``me``
     - ``IsAuthenticated``
     - Retorna ``username``, ``name``, ``email`` e ``cpf`` do usuário autenticado.

``config/urls.py`` também expõe as rotas JWT genéricas do
``simplejwt`` (``api/token/`` e ``api/token/refresh/``) — não usadas pelo
fluxo de login do SIGNA, que tem sua própria ``LoginView``.

Configuração (variáveis de ambiente)
---------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Variável
     - Uso
   * - ``SME_INTEGRACAO_URL``
     - URL base da API de integração da SME/EOL, usada por todos os métodos de ``SmeIntegracaoService``.
   * - ``SME_INTEGRACAO_TOKEN``
     - Token enviado no header ``x-api-eol-key`` em toda chamada à API de integração.
   * - ``CODIGO_SISTEMA_SIGNA``
     - Identifica o SIGNA como sistema consumidor perante o CoreSSO, enviado no payload de ``autentica``.
   * - ``GUIDE_PERFIL_SIGNA``
     - Código de perfil exigido no CoreSSO para autorizar o login no SIGNA.
   * - ``AMBIENTE_URL``
     - URL base do frontend, usada para montar o link de redefinição de senha (``{AMBIENTE_URL}/recuperar-senha/{uid}/{token}``).

Integrações externas ao domínio
----------------------------------

Apps que dependem de ``apps.usuarios``:

- **Designação** (``apps.designacao``) — usa
  ``SmeIntegracaoService`` extensivamente (ver seção acima) e referencia
  ``User`` via ``AtoAdministrativo.criado_por`` (FK para o autor do ato).
- **Alteração de E-mail** (``apps.alteracao_email``) — usa
  ``SmeIntegracaoService.altera_email`` e possui FK para ``User``
  (solicitante da alteração).
- **Unidades** (``apps.unidades``) — não depende de ``apps.usuarios``
  diretamente, mas integra com a mesma API externa de forma paralela.

Exceções de domínio compartilhadas (``apps.helpers.exceptions``) usadas
por este app: ``AuthenticationError``, ``InternalError``,
``EmailNaoCadastradoError``, ``SmeIntegracaoError``, ``UserNotFoundError``,
``PerfilNaoAutorizadoError``.

O mesmo módulo compartilhado também define ``CargaUsuarioError`` ("Erro ao
cadastrar usuário no CoreSSO"), mas ela não é levantada nem importada em
nenhum ponto do projeto atualmente — é código morto, sem fluxo associado.
Já ``TokenJaUtilizadoError``/``TokenExpiradoError`` são usadas, mas não
por este domínio: pertencem ao fluxo de confirmação por token do
:doc:`Alteração de E-mail </dominios/alteracao_email/index>`.

.. todo:: Confirmar se ``CargaUsuarioError`` é realmente código morto (sem
   nenhum uso em todo o projeto) e, se sim, avaliar removê-la de
   ``apps.helpers.exceptions``.
