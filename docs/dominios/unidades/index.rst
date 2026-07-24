Unidades
========

Visão geral
-----------

O domínio de **Unidades** (``apps.unidades``) é um domínio **stateless**:
não possui nenhum modelo persistido, admin ou migration real — é um
wrapper de integração HTTP com a API SME/EOL para consulta de **DREs**
(Diretorias Regionais de Educação) e **Unidades Escolares**, expondo um
único endpoint público usado principalmente para popular seletores de
DRE/UE em formulários do frontend.

.. important::
   ``apps.unidades`` **não está listado em** ``INSTALLED_APPS``
   (``config/settings/base.py``). Isso não quebra nada porque o app não
   define modelos nem depende do app registry do Django para funcionar —
   suas rotas são incluídas diretamente em ``config/urls.py``
   (``path("api/unidades/", include("apps.unidades.urls", ...))``), que
   não exige que o app esteja registrado. Ainda assim, é uma
   particularidade digna de atenção: qualquer funcionalidade futura que
   dependa do app registry (models, signals, checks do Django) exigirá
   adicionar o app a ``INSTALLED_APPS``.

Integração com a API SME/EOL
--------------------------------

Toda "unidade" e "DRE" é um ``dict`` volátil obtido a cada requisição —
não há cache local. A integração é implementada em
``apps/unidades/services/unidades_service.py``, por ``BaseEOLService`` e
suas duas subclasses, ``DREIntegracaoService`` e
``UnidadeIntegracaoService``.

``BaseEOLService`` centraliza o request GET (``_get(url, context)``) e o
tratamento de erros:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Condição
     - Comportamento
   * - HTTP 401
     - ``PermissionError("Não autorizado ao sistema EOL")``
   * - HTTP 404
     - ``LookupError(f"Recurso não encontrado: {context}")``
   * - Outro status != 200
     - ``EOLIntegrationError(f"Erro na integração com EOL: {status}")``
   * - ``requests.exceptions.Timeout``
     - ``EOLTimeoutError("Tempo limite excedido")``
   * - ``requests.exceptions.RequestException``
     - ``EOLCommunicationError(str(exc))``
   * - HTTP 200
     - retorna ``response.json()``

.. note::
   Diferente do :doc:`SmeIntegracaoService </dominios/usuarios/index>`
   (que trata explicitamente ``204`` e JSON inválido como lista vazia em
   alguns métodos), ``BaseEOLService._get`` **não trata 204** — cairia no
   branch de erro genérico (``EOLIntegrationError``) — nem captura
   explicitamente falha de decodificação do JSON de uma resposta 200.

``DREIntegracaoService``
~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``get_dres() -> list[dict]`` — ``GET /DREs``. Valida que a resposta é
  uma lista (senão ``EOLUnexpectedResponseError``).
- ``get_dre_by_codigo(codigo_dre) -> dict | None`` — chama ``get_dres()``
  e filtra em memória por ``codigoDRE``; retorna ``None`` se não
  encontrar. Não tem consumidor na API pública deste app (testado, mas
  sem endpoint dedicado).

``UnidadeIntegracaoService``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Timeout próprio de **50s** (``DEFAULT_TIMEOUT = 50``, maior que o padrão
de 30s de ``BaseEOLService``).

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Método
     - Endpoint externo
     - Uso
   * - ``get_unidades_by_dre(dre_codigo)``
     - ``GET /DREs/{dre}/unidades``
     - Sem consumidor mapeado fora dos testes.
   * - ``get_unidades_by_dre_com_tipo_unidade(dre_codigo)``
     - ``GET /DREs/{dre}/escola``
     - Usado pelo próprio ``UnidadeViewSet`` para listar UEs de uma DRE (inclui o tipo de unidade — EMEF, EMEI, CEI etc.).
   * - ``get_unidades_codigo_integracao_by_dre(dre_codigo)``
     - ``GET /DREs/{dre}/unidades/codigo-integracao``
     - **Único método consumido fora deste app** — usado pelo domínio :doc:`Designação </dominios/designacao/index>`.
   * - ``get_unidade_supervisao_by_dre(dre_codigo)``
     - ``GET /escolas/dados/{codigo_escola_eol}``
     - Usado pelo ``UnidadeViewSet`` para anexar a unidade de supervisão escolar de cada DRE à listagem de UEs.

Todos os métodos validam primeiro que ``dre_codigo`` não é vazio, senão
levantam ``ValueError`` **antes** de qualquer chamada HTTP.

``get_unidade_supervisao_by_dre`` resolve o código da DRE para o
``codigo_escola_eol`` da sua unidade de supervisão através do mapa fixo
``SUPERVISAO_ESCOLAR_DRES_MAP`` (``apps/unidades/constants/utils.py``,
13 DREs mapeadas); se a DRE não estiver no mapa, levanta ``ValueError("DRE
não possui unidade de supervisão configurada.")``. A resposta é
reformatada por ``_formatar_unidade_supervisao``, que fixa
``siglaTipoEscola="UA"`` e ``codigoSubprefeitura``/``nomeSubprefeitura``
como ``None`` — campos que a API de "dados de escola" não retorna para
uma unidade administrativa de supervisão.

.. important::
   ``UnidadeIntegracaoService`` **não reaproveita**
   ``SmeIntegracaoService`` (domínio :doc:`Usuários
   </dominios/usuarios/index>`), embora ambos consumam a mesma API
   externa com o mesmo header de autenticação (``x-api-eol-key``) e a
   mesma variável de ambiente (``SME_INTEGRACAO_URL``). São duas
   implementações paralelas e independentes do mesmo padrão de
   integração — o histórico de commits mostra que ``apps.unidades`` foi
   criado como um domínio isolado, sem reaproveitar o client já existente
   em ``apps.usuarios``. A única diferença funcional real é o timeout
   maior (50s), que poderia ter sido resolvido com um parâmetro em vez de
   duplicação de código.

API
---

Roteado sob ``api/unidades/`` (namespace ``unidades``, via
``DefaultRouter`` do DRF, com um único ``ViewSet`` registrado na raiz).

``UnidadeViewSet`` implementa apenas a action ``list`` — não há
``create``/``retrieve``/``update``/``destroy`` — e usa
**``permission_classes = [AllowAny]``**: é o único domínio documentado do
SIGNA cujo endpoint é público, sem exigir JWT.

.. list-table::
   :header-rows: 1
   :widths: 15 45 40

   * - Query params
     - Exemplo
     - Descrição
   * - ``tipo=DRE``
     - ``GET /api/unidades/?tipo=DRE``
     - Lista todas as DREs (``DREIntegracaoService.get_dres()``).
   * - ``tipo=UE&dre=<codigo>``
     - ``GET /api/unidades/?tipo=UE&dre=108200``
     - Lista as UEs da DRE informada, com a unidade de supervisão anexada ao final da lista, se disponível.

A filtragem não usa ``django-filter`` — é feita manualmente lendo
``request.query_params`` dentro do método ``list()``. O parâmetro
``tipo`` é **case-sensitive** (``"dre"`` minúsculo é inválido).

Regras de erro:

.. list-table::
   :header-rows: 1
   :widths: 40 15 45

   * - Situação
     - Status
     - Observação
   * - ``tipo`` ausente
     - 400
     - ``{"detail": "É necessário informar o parâmetro 'tipo' (DRE ou UE)."}``
   * - ``tipo`` inválido
     - 400
     - ``{"detail": "Parâmetro 'tipo' inválido. Use 'DRE' ou 'UE'."}``
   * - ``tipo=UE`` sem ``dre``
     - 400
     - ``{"detail": "É necessário informar o código da DRE no parâmetro 'dre'."}``
   * - ``ValueError`` do service
     - 400
     - —
   * - ``LookupError`` do service
     - 404
     - —
   * - ``PermissionError`` do service
     - 401
     - —
   * - Falha ao obter a unidade de supervisão
     - *(engolida)*
     - A listagem de UEs **não falha** se só a busca de supervisão der erro — o erro é logado e a supervisão simplesmente não é anexada à resposta.
   * - Exceção genérica
     - 500
     - ``{"detail": "Erro ao consultar DREs/unidades no sistema externo."}``

.. note::
   Existem ``DRESerializer`` e ``UnidadeSerializer``
   (``apps/unidades/api/serializers/``), testados isoladamente, mas
   **não são usados pelas views atuais** — ``UnidadeViewSet`` devolve os
   dicts crus retornados pelos services. Fica como pendência para quem
   for evoluir este domínio: ou conectar os serializers às views, ou
   removê-los caso permaneçam sem uso.

.. todo:: Avaliar unificar ``UnidadeIntegracaoService``/``DREIntegracaoService``
   com ``SmeIntegracaoService`` (domínio Usuários) para eliminar a
   duplicação de padrão de integração com a API SME/EOL.

Integrações
-----------

Único consumidor externo do domínio: :doc:`Designação
</dominios/designacao/index>`
(``DesignacaoUnidadeService.obter_informacoes_escolares``), que usa
``UnidadeIntegracaoService.get_unidades_codigo_integracao_by_dre(codigo_dre)``
para obter a lista de códigos de integração de todas as unidades de uma
DRE e, em seguida, filtra em memória pelo item cujo ``codigoUe`` bate com
a UE que está processando — não existe endpoint "por UE" direto para
código de integração, só "por DRE" com filtro posterior.
