ADR 001 — Ausência de camada repository.py
==========================================

:Status: Aceito
:Data: 2026-06-11
:Contexto: Aderência ao Guia SME Django

Contexto
--------

O Guia SME Django recomenda uma camada ``repository.py`` separada dentro de
cada app, inspirada no padrão *Repository* do DDD (Domain-Driven Design) e
comum em microsserviços Java/C#. A motivação do guia é isolar o ORM do
restante da aplicação, permitindo trocar o banco de dados sem impacto nas
regras de negócio.

Decisão
-------

Este projeto **não adota** a camada ``repository.py``. O fluxo de dados segue:

.. code-block:: text

    view → service → ORM (Django)

Motivação
---------

**1. O Django ORM já é o repository**

O padrão Repository existe para abstrair o acesso a dados atrás de uma
interface. O ``Manager`` do Django (``objects``) já cumpre esse papel —
``Designacao.objects.filter(...)`` é exatamente a interface de repositório
que o padrão define. Criar um ``repository.py`` seria envolver o repository
em outro repository.

**2. O DRF é construído em torno de instâncias de modelo**

``ModelSerializer``, ``get_object()``, ``get_queryset()``, paginação e
filtros — tudo no DRF opera sobre instâncias e QuerySets. Um repository que
retorna ``dict`` (como recomenda o guia para microsserviços) quebra esse
fluxo e força a reescrever o que o framework já oferece gratuitamente.

**3. A separação real já está presente**

O que o padrão Repository realmente resolve — views sem lógica de negócio,
regras centralizadas, código testável — já está implementado com a camada
``services.py``. O único ajuste necessário é garantir que queries ORM não
apareçam diretamente nas views.

Consequências
-------------

- Views com acesso direto ao ORM devem ser corrigidas movendo as queries
  para o ``service`` correspondente.
- Testes de service podem usar ``pytest-django`` com banco SQLite em memória,
  sem necessidade de mockar um repository.
- O guia SME continua sendo seguido nos demais aspectos; esta é a única
  exceção justificada pelo tipo de aplicação (monolito DRF vs. microsserviço).
