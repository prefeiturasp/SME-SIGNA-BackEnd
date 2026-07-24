Designação
==========

Visão geral
-----------

O domínio de **Designação** (``apps.designacao``) implementa o fluxo
administrativo de nomeação temporária ou excepcional de servidores para
cargos de gestão escolar da SME-SP — Diretor de Escola, Assistente de
Diretor de Escola, Coordenador Pedagógico, Secretário de Escola e
Supervisor Escolar.

O domínio cobre quatro tipos de ato administrativo que se relacionam entre
si em uma hierarquia (**Designação**, **Cessação**, **Apostila** e
**Insubsistência**), o cálculo do **módulo** (quantidade de vagas
permitidas) por cargo e unidade, o registro de **impedimentos de
substituição** do titular, e a integração com o SGP/EOL para obtenção de
dados cadastrais de servidores e unidades escolares.

.. important::
   O código convive com dois "mundos" de modelos:

   - **Modelo atual**, baseado em :class:`~apps.designacao.models.ato_administrativo.AtoAdministrativo`
     e nas classes ``*Detalhe`` — é o que toda a API (views, services,
     serializers) utiliza hoje e o que esta documentação descreve em
     detalhe.
   - **Modelos legados** (``Designacao``, ``Cessacao``, ``Apostila``,
     ``Insubsistencia`` "de topo", em módulos homônimos), mantidos por
     compatibilidade histórica, mas não utilizados pelas rotas de API
     atuais, que serão removidos em breve.

Conceitos de domínio
---------------------

Designação
~~~~~~~~~~

Ato administrativo **raiz** (``tipo=DESIGNACAO``, sem ato pai) que
formaliza a nomeação de um servidor **indicado** para exercer, temporária
ou excepcionalmente, um cargo de gestão escolar — eventualmente em
substituição a um **titular** afastado por algum
:ref:`impedimento <impedimentos>`. É publicada por meio de uma
:ref:`Portaria <portaria>` e registrada no processo SEI e no Diário
Oficial.

.. _portaria:

Portaria
~~~~~~~~

Não é uma entidade própria: é o conjunto de campos (``numero_portaria``,
``ano_vigente``, ``sei_numero``, ``doc``) presente em todo
``AtoAdministrativo`` — exceto Apostila, que não usa numeração de
portaria própria. O endpoint ``portarias/`` lista todos os atos
administrativos sob a ótica desses campos, para a gestão da publicação no
Diário Oficial.

Ato administrativo
~~~~~~~~~~~~~~~~~~~

Entidade genérica (:class:`~apps.designacao.models.ato_administrativo.AtoAdministrativo`)
que unifica Designação, Cessação, Apostila e Insubsistência em uma única
tabela organizada em árvore (``ato_pai`` / ``ato_raiz``), com um
``status`` calculado dinamicamente (``ativo``, ``cessada`` ou
``insubsistente``).

Apostila
~~~~~~~~

Ato que **altera campos** de uma designação ou cessação já existente, sem
revogá-la — uma retificação administrativa. Cada campo alterado é
registrado individualmente (valor anterior e novo), o que permite reverter
a alteração posteriormente caso a apostila seja insubsistida.

Cessação
~~~~~~~~

Ato que encerra uma designação (equivalente a uma exoneração da função
designada), por um dos motivos: a pedido, remoção ou aposentadoria. Uma
designação só pode ter **uma cessação ativa por vez**.

Insubsistência
~~~~~~~~~~~~~~

Mecanismo geral de **cancelamento** do domínio: torna sem efeito qualquer
outro ato (designação, cessação, apostila ou mesmo outra insubsistência),
desativando-o. É o único tipo de ato que pode ter qualquer um dos outros
três tipos como pai — inclusive a si mesmo.

.. _impedimentos:

Impedimento de substituição
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Motivo legal/administrativo pelo qual o titular do cargo está impedido de
exercer a função, justificando a designação de um substituto (ex.: licença
médica, férias, licença gestante). Ver :ref:`seção dedicada <impedimentos-detalhe>`.

Modelo de dados
----------------

Hierarquia de atos administrativos
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cada ato é uma linha em :class:`~apps.designacao.models.ato_administrativo.AtoAdministrativo`,
acompanhada de uma tabela de detalhe específica do tipo, ligada por
``OneToOneField`` cuja chave primária é o próprio ``ato`` (padrão
*detail table*):

======================  ================================================
Tipo do ato              Tabela de detalhe
======================  ================================================
``DESIGNACAO``           ``DesignacaoDetalhe``
``CESSACAO``             ``CessacaoDetalhe``
``APOSTILA``              ``ApostilaDetalhe`` (+ ``ApostilaAlteracao`` para o histórico de campos)
``INSUBSISTENCIA``        ``InsubsistenciaDetalhe`` (+ ``InsubsistenciaApostilaDetalhe`` quando o ato pai é uma apostila)
======================  ================================================

Somente as seguintes combinações de ``tipo`` → ``ato_pai.tipo`` são
válidas (validado em ``AtoAdministrativo.clean()``):

.. code-block:: text

    CESSACAO         → DESIGNACAO
    APOSTILA         → DESIGNACAO | CESSACAO
    INSUBSISTENCIA   → DESIGNACAO | CESSACAO | APOSTILA | INSUBSISTENCIA
    DESIGNACAO       → (sem ato pai — é sempre raiz)

O campo ``ato_raiz`` é preenchido automaticamente em ``save()``: herda a
raiz do pai, ou é o próprio ato quando ele não tem pai (isto é, quando é
uma designação). Isso permite localizar rapidamente, a partir de qualquer
apostila ou insubsistência, a designação que originou a árvore.

O ``status`` do ato é uma *property* calculada, não um campo persistido:

- ``insubsistente`` — se ``ativo=False``;
- ``cessada`` — se o ato é uma ``DESIGNACAO`` e possui uma ``CESSACAO``
  filha com ``ativo=True``;
- ``ativo`` — caso contrário.

Exemplo de árvore típica:

.. code-block:: text

    Designação (raiz)
    ├── Apostila #1 (altera campos da designação)
    ├── Cessação
    │   └── Apostila #2 (altera campos da cessação)
    └── Insubsistência (torna a designação sem efeito)

Modelos legados
~~~~~~~~~~~~~~~~

Os modelos ``Designacao``, ``Cessacao``, ``Apostila`` e ``Insubsistencia``
(módulos ``apps/designacao/models/{designacao,cessacao,apostila,insubsistencia}.py``,
sem sufixo ``_detalhe``) representam o desenho original do domínio, com
relacionamentos diretos entre si e *soft delete* próprio (``is_deleted`` /
``deleted_at`` / ``delete()`` sobrescrito).

A camada de API que os expunha (``designacao_legado.py`` e respectivos
filter/serializer) foi removida no commit ``refactor: remove código legado
de atos administrativos`` (2026-07-17). Não há mais nenhuma view, filtro
ou serializer ativo apontando para esses quatro modelos — hoje eles
existem apenas para preservar o histórico de migrations, sem uso em tempo
de execução. Novas funcionalidades devem ser construídas sobre
``AtoAdministrativo``.

.. note::
   O módulo ``apps/designacao/models/designacao.py`` também define
   :class:`~apps.designacao.models.designacao.ImpedimentoSubstituicao`, que
   **não** é legado: é uma tabela de domínio (lookup) ainda usada
   ativamente pelo filtro e pelo serializer de designações do fluxo atual
   (ver :ref:`impedimentos-detalhe`).

Regras de negócio
------------------

Fluxo de vida de um ato
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    Designação criada
        │
        ├─► pode ser Apostilada (retificação de campos, reversível)
        │
        ├─► pode ser Cessada (uma única cessação ativa por vez)
        │        └─► a cessação também pode ser Apostilada
        │
        └─► Designação, Cessação ou Apostila podem ser Insubsistidas
                 └─► uma Insubsistência pode ela mesma ser "tornada sem
                     efeito" por uma nova Insubsistência, restaurando o
                     ato original

Criação de apostila (``ApostilaService``)
"""""""""""""""""""""""""""""""""""""""""

- o ato pai precisa estar ``eh_valido`` (``ativo=True``);
- não é possível apostilar uma designação **já cessada**;
- não é possível apostilar uma designação com prazo **já finalizado**
  (``data_fim`` no passado);
- campos protegidos não podem ser alterados via apostila: ``id``,
  ``tipo``, ``ato_pai``, ``ato_pai_id``, ``ato_raiz``, ``ato_raiz_id``,
  ``criado_em``;
- cada alteração de campo é registrada em ``ApostilaAlteracao`` (campo,
  valor anterior, valor novo), permitindo reversão futura.

.. warning::
   **Comportamento atual (a ser corrigido em breve):** hoje o
   ``ApostilaService`` permite criar múltiplas apostilas ativas
   simultaneamente sobre o mesmo ato pai — não há validação equivalente à
   de cessação (uma ativa por vez). O correto é **não permitir** criar uma
   nova apostila quando o ato pai já possuir uma apostila ativa; a
   apostila existente deveria ser insubsistida antes de uma nova ser
   criada. Essa regra ainda não está implementada e será adicionada em
   uma próxima alteração.

Criação de cessação (``CessacaoService``)
"""""""""""""""""""""""""""""""""""""""""

- o ato pai precisa ser uma ``DESIGNACAO`` válida;
- uma designação **não pode** ter mais de uma cessação ativa
  simultaneamente (regra reforçada tanto no ``clean()`` do modelo quanto
  no service).

Criação de insubsistência (``InsubsistenciaService``)
"""""""""""""""""""""""""""""""""""""""""""""""""""""

- o ato pai não pode já estar insubsistente;
- o ato pai não pode já ter uma insubsistência ativa;
- ao criar, o ato pai é desativado (``ativo=False``);
- os **efeitos em cascata** dependem do tipo do ato pai insubsistido:

  - **pai é outra Insubsistência** ("Tornar Sem Efeito" / TSE) — reativa
    o ato "avô" que a insubsistência original havia anulado;
  - **pai é uma Apostila** — reverte os campos que aquela apostila havia
    alterado no ato avô, restaurando o ``valor_anterior`` de cada
    ``ApostilaAlteracao``;
  - **pai é Designação ou Cessação** — reverte **todas** as apostilas
    ativas filhas daquele ato (restaurando os campos alterados por cada
    uma) e desativa cada uma dessas apostilas.

- excluir uma insubsistência (``InsubsistenciaService.excluir``) reverte o
  efeito: reativa o ``ato_pai`` e remove fisicamente o registro de
  insubsistência (não há soft delete em ``AtoAdministrativo``).

Cálculo de módulo de cargos
-----------------------------

O **módulo** é a quantidade de vagas permitidas para um cargo de gestão
escolar em uma unidade, calculada por regras específicas por cargo
(``apps/designacao/modulos/``, padrão *Strategy* via
:class:`~apps.designacao.modulos.base.ModuloCalculator`). O código do
cargo determina qual calculadora é usada:

============  ============================  ============================================
Código cargo   Cargo                          Calculadora
============  ============================  ============================================
``3360``       Diretor de Escola              ``ModuloLotacaoCalculator``
``3182``       Secretário de Escola           ``ModuloLotacaoCalculator``
``3085``       Assistente de Diretor          ``ModuloLotacaoCalculator``
``3379``       Coordenador Pedagógico         ``ModuloCoordenadorPedagogicoCalculator``
``3352``       Supervisor Escolar             ``ModuloSupervisorEscolarCalculator``
============  ============================  ============================================

``ModuloLotacaoCalculator``
    - Diretor: módulo fixo ``1``.
    - Secretário: ``1`` se o tipo de escola é EMEBS, EMEF, EMEFM ou CIEJA;
      caso contrário ``0``.
    - Assistente de Diretor: ``1`` em CEI; em CEMEI/EMEI/EMEBS/EMEF/EMEFM
      depende da quantidade de classes (``<= 20`` → ``1``, senão ``2``);
      demais tipos → ``0``.

``ModuloCoordenadorPedagogicoCalculator``
    - CEI → ``1``; CEMEI → ``2``.
    - EMEI: ``<= 20`` classes → ``1``, senão ``2``.
    - EMEF/EMEBS: ``<=14`` → ``1``; ``<=35`` → ``2`` (ou ``3`` com turno
      noturno com ``>=5`` turmas noturnas); ``<=50`` → ``3``; acima → ``4``.
    - Demais tipos → ``0``.

``ModuloSupervisorEscolarCalculator``
    Módulo definido **por DRE** (não por unidade), a partir de um mapa
    fixo de 13 DREs para o respectivo módulo. DRE ausente ou não mapeada
    resulta em ``0`` (com aviso registrado em log).

.. _impedimentos-detalhe:

Impedimentos de substituição
------------------------------

Um :class:`~apps.designacao.models.designacao.ImpedimentoSubstituicao` é um
registro de domínio (tabela ``impedimento_substituicao``) que descreve o
motivo pelo qual o titular do cargo está impedido de exercer a função. É
referenciado opcionalmente por ``Designacao`` / ``DesignacaoDetalhe``
através do campo ``impedimento_substituicao``.

São 23 impedimentos pré-cadastrados via migration (``0003_populate_impedimentos.py``),
entre eles: licença gestante, licença médica, licença paternidade, férias,
licença adoção, mandato eletivo (Portaria 20/SEGES/2024), afastamento por
cursos/congressos/competições, readaptação funcional (Art. 39 Lei
8.979/79), exercício de cargo em comissão (Art. 45 Lei 8.989/79),
transferência temporária (Decreto 57.444/16), entre outros.

O endpoint ``GET /designacoes/impedimentos/`` retorna a lista completa no
formato ``{"value": id, "label": descricao}`` para uso em componentes de
seleção na interface. Designações também podem ser filtradas por
impedimento (``impedimento_substituicao`` por id, ou ``impedimento_codigo``
pelo código).

API
---

Todas as rotas do domínio estão registradas sob ``app_name = "designacao"``
(``apps/designacao/urls.py``).

Utilitários e integração com SGP/EOL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

===========  ==========================  ================================================================
Método        Rota                        Descrição
===========  ==========================  ================================================================
``POST``      ``servidor``                Recebe ``{rf}`` e retorna dados do servidor a partir do SGP.
``GET``       ``unidade/``                Recebe ``?codigo_ue=`` e retorna cargos, funcionários, turmas e módulo calculado da unidade.
``GET``       ``unidade/cargos/``         Lista os cargos de vaga disponíveis para designação.
===========  ==========================  ================================================================

Designações
~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 12 30 58

   * - Método
     - Rota
     - Descrição
   * - ``GET``/``POST``
     - ``designacoes/``
     - Lista (com filtros/busca/ordenação, ou ``no_pagination=true``) ou cria uma designação.
   * - ``GET``
     - ``designacoes/impedimentos/``
     - Lista os impedimentos de substituição.
   * - ``GET``
     - ``designacoes/<id>/``
     - Detalha uma designação, incluindo cessação, apostilas e insubsistência associadas.
   * - ``PATCH``
     - ``designacoes/<id>/``
     - Atualiza parcialmente uma designação.
   * - ``DELETE``
     - ``designacoes/<id>/``
     - Remove uma designação (exclusão física do ato).
   * - ``GET``
     - ``designacoes/cargos-base-pareados/``
     - Cargos base combinados (indicado + titular), sem repetição.
   * - ``GET``
     - ``designacoes/cargos-sobrepostos-pareados/``
     - Idem para cargo sobreposto.
   * - ``GET``
     - ``designacoes/buscar-por-portaria/?portaria=``
     - Busca uma designação pelo número exato da portaria.

Filtros disponíveis (``DesignacaoFilter``): ``rf``, ``nome``,
``cargo_base``, ``periodo`` (intervalo de datas), ``cargo_sobreposto``,
``dre``, ``unidade``, ``ano``, ``impedimento_substituicao``,
``impedimento_codigo``.

Cessações, apostilas e insubsistências
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 12 33 55

   * - Método
     - Rota
     - Descrição
   * - ``GET``/``POST``
     - ``cessacoes/``
     - Lista ou cria uma cessação (``ato_pai`` deve ser uma designação).
   * - ``GET``
     - ``cessacoes/<id>/``
     - Detalha uma cessação, com dados da designação associada.
   * - ``DELETE``
     - ``cessacoes/<id>/``
     - Remove uma cessação.
   * - ``GET``
     - ``cessacoes/buscar-por-portaria/?portaria=``
     - Busca cessação pelo número da portaria.
   * - ``GET``/``POST``
     - ``apostilas/``
     - Lista ou cria uma apostila (``ato_pai`` é designação ou cessação; corpo inclui ``alteracoes``).
   * - ``GET``
     - ``apostilas/<id>/``
     - Detalha uma apostila, incluindo histórico de alterações.
   * - ``DELETE``
     - ``apostilas/<id>/``
     - Remove uma apostila.
   * - ``GET``/``POST``
     - ``insubsistencias/``
     - Lista ou cria uma insubsistência (``ato_pai`` pode ser qualquer tipo de ato).
   * - ``GET``
     - ``insubsistencias/<id>/``
     - Detalha uma insubsistência.
   * - ``DELETE``
     - ``insubsistencias/<id>/``
     - Remove a insubsistência e **reativa** o ato pai (ver regras acima).
   * - ``GET``
     - ``insubsistencias/buscar-por-portaria/?portaria=``
     - Busca insubsistência pelo número da portaria.

Portarias e atos administrativos (visão consolidada)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

===========  ===========================================  ================================================================
Método        Rota                                          Descrição
===========  ===========================================  ================================================================
``GET``       ``portarias/``                                Lista todos os tipos de ato administrativo formatados para a tela de publicação no Diário Oficial (sem paginação).
``POST``      ``portarias/atualizar-data-publicacao/``      Atualiza em massa ``doc`` e ``status_publicacao=PUBLICADO`` para os ``ids`` informados.
``GET``       ``atos-administrativos/``                     Visão paginada e mais detalhada dos atos, com filtros adicionais (tipo de ato composto, ``ato_id`` que casa id/ato_pai/ato_raiz, ``status_publicacao``, etc.).
===========  ===========================================  ================================================================

Integrações externas
----------------------

O domínio não se comunica diretamente com sistemas externos: toda
integração passa por serviços centralizados de outras apps:

- :class:`apps.usuarios.services.sme_integracao_service.SmeIntegracaoService`
  — cliente do SGP/EOL, usado para obter dados cadastrais e cargos do
  servidor (``informacao_usuario_sgp``, ``consulta_cargos_funcionario``),
  funcionários e informações de unidades escolares
  (``buscar_funcionarios_escolares``, ``consulta_informacoes_unidades_escolares``),
  e dados de turmas para cálculo de módulo e identificação de SP Integral
  (``buscar_turmas_ue_ano``, ``buscar_dados_turma``, ``buscar_disciplinas_turma``).
  Falhas de integração são sinalizadas por ``apps.helpers.exceptions.SmeIntegracaoError``.
  Endpoints e métodos completos estão documentados em
  :doc:`Usuários — Integração com a SME/CoreSSO </dominios/usuarios/index>`.
- :class:`apps.unidades.services.unidades_service.UnidadeIntegracaoService`
  — usado para obter o código hierárquico/de integração da unidade a
  partir do código da DRE (ver :doc:`Unidades </dominios/unidades/index>`).
- ``AUTH_USER_MODEL`` (``apps.usuarios``) — todo ato administrativo
  registra o usuário do sistema que o criou (``criado_por``).
