# Relatório PEP — app `designacao`

Gerado em: **2026-05-21 13:04:45 UTC**  
Commit: `e050c33`  
Limite linha (PEP 8): **79**

## Resumo
| Métrica | Valor | % |
| --- | ---: | ---: |
| Arquivos | 85 | — |
| LOC | 8910 | — |
| Linhas > 79 | 51 | 0.6% |
| Funções/métodos | 498 | — |
| Com docstring | 14 | 2.8% |
| Classes c/ docstring | 6/98 | 6.1% |
| Hints completos | 39 | 7.8% |
| flake8 | 92 | — |

### Top flake8

| Código | Ocorrências |
| --- | ---: |
| `E501` | 91 |
| `F841` | 1 |

<details><summary>Primeiras 30 linhas flake8</summary>

```
apps/designacao/__tests__/test_apostila_service.py:28:80: E501 line too long (80 > 79 characters)
apps/designacao/__tests__/test_apostila_service.py:43:80: E501 line too long (80 > 79 characters)
apps/designacao/__tests__/test_apostila_service.py:60:80: E501 line too long (80 > 79 characters)
apps/designacao/__tests__/test_apostila_service.py:102:80: E501 line too long (80 > 79 characters)
apps/designacao/__tests__/test_designacao_serializer.py:115:80: E501 line too long (81 > 79 characters)
apps/designacao/__tests__/test_designacao_unidade_service.py:33:80: E501 line too long (125 > 79 characters)
apps/designacao/__tests__/test_designacao_unidade_service.py:38:80: E501 line too long (102 > 79 characters)
apps/designacao/__tests__/test_designacao_unidade_service.py:41:80: E501 line too long (108 > 79 characters)
apps/designacao/__tests__/test_designacao_unidade_service.py:44:80: E501 line too long (104 > 79 characters)
apps/designacao/__tests__/test_designacao_unidade_service.py:47:80: E501 line too long (123 > 79 characters)
apps/designacao/__tests__/test_designacao_unidade_service.py:50:80: E501 line too long (111 > 79 characters)
apps/designacao/__tests__/test_designacao_unidade_service.py:53:80: E501 line too long (113 > 79 characters)
apps/designacao/__tests__/test_designacao_unidade_service.py:56:80: E501 line too long (106 > 79 characters)
apps/designacao/__tests__/test_designacao_unidade_service.py:121:80: E501 line too long (125 > 79 characters)
apps/designacao/__tests__/test_designacao_unidade_service.py:126:80: E501 line too long (102 > 79 characters)
apps/designacao/__tests__/test_designacao_unidade_service.py:129:80: E501 line too long (108 > 79 characters)
apps/designacao/__tests__/test_designacao_unidade_service.py:132:80: E501 line too long (104 > 79 characters)
apps/designacao/__tests__/test_designacao_unidade_service.py:135:80: E501 line too long (123 > 79 characters)
apps/designacao/__tests__/test_designacao_unidade_service.py:138:80: E501 line too long (111 > 79 characters)
apps/designacao/__tests__/test_designacao_unidade_service.py:141:80: E501 line too long (113 > 79 characters)
apps/designacao/__tests__/test_designacao_unidade_service.py:144:80: E501 line too long (106 > 79 characters)
apps/designacao/__tests__/test_designacao_unidade_service.py:192:80: E501 line too long (80 > 79 characters)
apps/designacao/__tests__/test_designacao_unidade_service.py:203:80: E501 line too long (102 > 79 characters)
apps/designacao/__tests__/test_designacao_unidade_service.py:206:80: E501 line too long (108 > 79 characters)
apps/designacao/__tests__/test_designacao_unidade_service.py:209:80: E501 line too long (104 > 79 characters)
apps/designacao/__tests__/test_designacao_unidade_service.py:238:80: E501 line too long (93 > 79 characters)
apps/designacao/__tests__/test_designacao_unidade_service.py:241:80: E501 line too long (102 > 79 characters)
apps/designacao/__tests__/test_designacao_unidade_service.py:244:80: E501 line too long (108 > 79 characters)
apps/designacao/__tests__/test_designacao_unidade_service.py:247:80: E501 line too long (104 > 79 characters)
apps/designacao/__tests__/test_designacao_unidade_service.py:276:80: E501 line too long (102 > 79 characters)
```
<​/details>

## Símbolos sem docstring (top)

| Arquivo | Linha | Símbolo | Tipo |
| --- | ---: | --- | --- |
| `__tests__/factories.py` | 13 | `criar_ato_designacao` | function |
| `__tests__/factories.py` | 45 | `criar_designacao` | function |
| `__tests__/factories.py` | 49 | `criar_designacao_legado` | function |
| `__tests__/factories.py` | 73 | `criar_ato_cessacao` | function |
| `__tests__/factories.py` | 97 | `criar_ato_apostila` | function |
| `__tests__/factories.py` | 110 | `criar_ato_insubsistencia` | function |
| `__tests__/test_apostila_serializers.py` | 14 | `TestApostilaSerializer` | class |
| `__tests__/test_apostila_serializers.py` | 17 | `TestApostilaSerializer.designacao` | function |
| `__tests__/test_apostila_serializers.py` | 37 | `TestApostilaSerializer.apostila` | function |
| `__tests__/test_apostila_serializers.py` | 46 | `TestApostilaSerializer.test_serialization_campos_reais` | function |
| `__tests__/test_apostila_serializers.py` | 53 | `TestApostilaSerializer.test_deserialization_e_validacao` | function |
| `__tests__/test_apostila_serializers.py` | 65 | `TestApostilaSerializer.test_to_representation_com_cessacao` | function |
| `__tests__/test_apostila_serializers.py` | 81 | `TestApostilaSerializer.test_validacao_erro_vazio` | function |
| `__tests__/test_apostila_serializers.py` | 86 | `TestApostilaSerializer.test_apostila_anulacao` | function |
| `__tests__/test_apostila_service.py` | 16 | `TestApostilaService` | class |
| `__tests__/test_apostila_service.py` | 18 | `TestApostilaService._data` | function |
| `__tests__/test_apostila_service.py` | 30 | `TestApostilaService.test_criar_apostila_designacao_sucesso` | function |
| `__tests__/test_apostila_service.py` | 36 | `TestApostilaService.test_criar_apostila_cessacao_sucesso` | function |
| `__tests__/test_apostila_service.py` | 45 | `TestApostilaService.test_permite_criar_segunda_apostila_sem_anular_primeira` | function |
| `__tests__/test_apostila_service.py` | 51 | `TestApostilaService.test_permite_criar_apostila_apos_insubsistencia_da_anterior` | function |
| `__tests__/test_apostila_service.py` | 62 | `TestApostilaService.test_erro_designacao_cessada` | function |
| `__tests__/test_apostila_service.py` | 68 | `TestApostilaService.test_erro_designacao_prazo_finalizado` | function |
| `__tests__/test_apostila_service.py` | 76 | `TestApostilaService.test_permite_apostila_designacao_com_data_fim_futura` | function |
| `__tests__/test_apostila_service.py` | 84 | `TestApostilaService.test_permite_apostila_cessacao_mesmo_com_data_fim` | function |
| `__tests__/test_apostila_service.py` | 94 | `TestApostilaService.test_erro_ato_pai_insubsistente` | function |

## PEP 440
- Arquivos: base.txt, local.txt, production.txt, test.txt
- Linhas: **26**
- PyPI válidas: **26**
- git+: **0**
- ==: **5**
- Inválidas: **0**

## Por arquivo
| Arquivo | LOC | >max | Funções | Doc % | Hints completos % |
| --- | ---: | ---: | ---: | ---: | ---: |
| `__init__.py` | 0 | 0 | 0 | — | — |
| `__tests__/factories.py` | 124 | 0 | 6 | 0.0% | 0.0% |
| `__tests__/test_apostila_serializers.py` | 94 | 0 | 7 | 0.0% | 0.0% |
| `__tests__/test_apostila_service.py` | 147 | 0 | 13 | 0.0% | 0.0% |
| `__tests__/test_apostila_v2_view.py` | 165 | 0 | 12 | 0.0% | 0.0% |
| `__tests__/test_apostila_view.py` | 92 | 0 | 8 | 0.0% | 0.0% |
| `__tests__/test_ato_administrativo_model.py` | 201 | 0 | 26 | 0.0% | 0.0% |
| `__tests__/test_cessacao_serializer.py` | 89 | 0 | 7 | 0.0% | 0.0% |
| `__tests__/test_cessacao_v2_view.py` | 110 | 0 | 8 | 0.0% | 0.0% |
| `__tests__/test_cessacao_view.py` | 129 | 0 | 9 | 33.3% | 0.0% |
| `__tests__/test_designacao_filters.py` | 110 | 0 | 12 | 0.0% | 0.0% |
| `__tests__/test_designacao_impedimentos.py` | 40 | 0 | 1 | 0.0% | 0.0% |
| `__tests__/test_designacao_legado_filters.py` | 108 | 0 | 12 | 0.0% | 0.0% |
| `__tests__/test_designacao_legado_view.py` | 102 | 0 | 8 | 0.0% | 0.0% |
| `__tests__/test_designacao_serializer.py` | 162 | 1 | 6 | 16.7% | 0.0% |
| `__tests__/test_designacao_service.py` | 83 | 0 | 3 | 0.0% | 0.0% |
| `__tests__/test_designacao_servidor_service.py` | 105 | 0 | 3 | 0.0% | 0.0% |
| `__tests__/test_designacao_servidor_view.py` | 127 | 0 | 9 | 0.0% | 0.0% |
| `__tests__/test_designacao_unidade_service.py` | 480 | 34 | 31 | 0.0% | 0.0% |
| `__tests__/test_designacao_unidade_view.py` | 153 | 4 | 10 | 30.0% | 0.0% |
| `__tests__/test_designacao_view.py` | 143 | 0 | 9 | 0.0% | 0.0% |
| `__tests__/test_insubsistencia_serializer.py` | 275 | 0 | 11 | 0.0% | 0.0% |
| `__tests__/test_insubsistencia_service.py` | 206 | 0 | 12 | 0.0% | 0.0% |
| `__tests__/test_insubsistencia_v2_view.py` | 133 | 0 | 11 | 0.0% | 0.0% |
| `__tests__/test_insubsistencia_view.py` | 157 | 0 | 12 | 0.0% | 0.0% |
| `__tests__/test_portaria_filter.py` | 178 | 0 | 13 | 0.0% | 0.0% |
| `__tests__/test_portaria_serializer.py` | 363 | 0 | 35 | 0.0% | 0.0% |
| `__tests__/test_portaria_viewset.py` | 426 | 0 | 39 | 0.0% | 0.0% |
| `admin.py` | 2 | 0 | 0 | — | — |
| `api/filters/designacao_filter.py` | 77 | 0 | 3 | 0.0% | 0.0% |
| `api/filters/designacao_legado_filter.py` | 66 | 0 | 3 | 0.0% | 0.0% |
| `api/filters/portaria_filter.py` | 84 | 0 | 1 | 0.0% | 0.0% |
| `api/serializers/apostila_serializer.py` | 30 | 0 | 1 | 0.0% | 0.0% |
| `api/serializers/cessacao_serializer.py` | 43 | 0 | 4 | 0.0% | 0.0% |
| `api/serializers/designacao_legado_serializer.py` | 99 | 0 | 5 | 0.0% | 0.0% |
| `api/serializers/designacao_serializer.py` | 495 | 0 | 9 | 0.0% | 0.0% |
| `api/serializers/designacao_servidor_request_serializer.py` | 5 | 0 | 0 | — | — |
| `api/serializers/insubsistencia_serializer.py` | 77 | 1 | 4 | 0.0% | 0.0% |
| `api/serializers/portaria_serializer.py` | 98 | 0 | 7 | 28.6% | 0.0% |
| `api/serializers/utils.py` | 21 | 0 | 2 | 50.0% | 0.0% |
| `api/serializers/v2/__init__.py` | 0 | 0 | 0 | — | — |
| `api/serializers/v2/apostila_serializer.py` | 91 | 0 | 3 | 0.0% | 0.0% |
| `api/serializers/v2/cessacao_serializer.py` | 84 | 0 | 3 | 0.0% | 0.0% |
| `api/serializers/v2/insubsistencia_serializer.py` | 48 | 0 | 3 | 0.0% | 0.0% |
| `api/views/apostila_view.py` | 51 | 0 | 2 | 0.0% | 0.0% |
| `api/views/cessacao_view.py` | 31 | 0 | 1 | 0.0% | 0.0% |
| `api/views/designacao.py` | 167 | 0 | 10 | 0.0% | 0.0% |
| `api/views/designacao_impedimentos_view.py` | 14 | 0 | 1 | 0.0% | 0.0% |
| `api/views/designacao_legado.py` | 122 | 0 | 8 | 0.0% | 0.0% |
| `api/views/designacao_servidor_view.py` | 51 | 1 | 1 | 0.0% | 0.0% |
| `api/views/designacao_unidades_view.py` | 64 | 0 | 2 | 0.0% | 0.0% |
| `api/views/insubsistencia_view.py` | 61 | 0 | 2 | 0.0% | 0.0% |
| `api/views/portaria.py` | 101 | 0 | 2 | 50.0% | 0.0% |
| `api/views/v2/__init__.py` | 0 | 0 | 0 | — | — |
| `api/views/v2/apostila_view.py` | 52 | 0 | 2 | 0.0% | 0.0% |
| `api/views/v2/cessacao_view.py` | 47 | 0 | 2 | 0.0% | 0.0% |
| `api/views/v2/insubsistencia_view.py` | 58 | 0 | 3 | 0.0% | 0.0% |
| `apps.py` | 6 | 0 | 0 | — | — |
| `constants/cargos_gestao_escolar.py` | 16 | 0 | 0 | — | — |
| `models/__init__.py` | 8 | 0 | 0 | — | — |
| `models/apostila.py` | 61 | 0 | 1 | 0.0% | 0.0% |
| `models/apostila_detalhe.py` | 36 | 0 | 0 | — | — |
| `models/ato_administrativo.py` | 102 | 2 | 4 | 0.0% | 0.0% |
| `models/cessacao.py` | 31 | 0 | 1 | 0.0% | 0.0% |
| `models/cessacao_detalhe.py` | 21 | 0 | 0 | — | — |
| `models/designacao.py` | 136 | 0 | 3 | 33.3% | 0.0% |
| `models/designacao_detalhe.py` | 121 | 0 | 1 | 0.0% | 0.0% |
| `models/insubsistencia.py` | 45 | 0 | 1 | 0.0% | 0.0% |
| `models/insubsistencia_detalhe.py` | 17 | 0 | 0 | — | — |
| `modulos/__init__.py` | 15 | 0 | 0 | — | — |
| `modulos/__tests__/test_modulo_coordenador_pedagogico.py` | 114 | 0 | 8 | 0.0% | 0.0% |
| `modulos/__tests__/test_modulo_lotacao.py` | 118 | 0 | 9 | 0.0% | 0.0% |
| `modulos/__tests__/test_modulo_supervisor_escolar.py` | 64 | 0 | 4 | 0.0% | 0.0% |
| `modulos/base.py` | 8 | 0 | 1 | 0.0% | 100.0% |
| `modulos/coordenador_pedagogico.py` | 81 | 0 | 6 | 0.0% | 83.3% |
| `modulos/lotacao.py` | 61 | 0 | 6 | 0.0% | 100.0% |
| `modulos/supervisor_escolar.py` | 53 | 1 | 1 | 0.0% | 100.0% |
| `services/apostila_service.py` | 230 | 4 | 6 | 16.7% | 50.0% |
| `services/cessacao_service.py` | 46 | 0 | 1 | 0.0% | 100.0% |
| `services/designacao_service.py` | 72 | 0 | 3 | 0.0% | 66.7% |
| `services/designacao_servidor_service.py` | 75 | 3 | 2 | 50.0% | 100.0% |
| `services/designacao_unidades_service.py` | 315 | 0 | 16 | 0.0% | 93.8% |
| `services/insubsistencia_service.py` | 199 | 0 | 7 | 0.0% | 42.9% |
| `urls.py` | 107 | 0 | 0 | — | — |
| `urls_v2.py` | 111 | 0 | 0 | — | — |

*Gerado por `python manage.py gerar_relatorio_pep --app designacao`*
