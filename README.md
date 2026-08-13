<h1 align="center">steps-public</h1>

<p align="center">
  Catálogo <b>público</b> de steps da Dadosfera — componentes genéricos e reutilizáveis
  dos pipelines do Módulo de Inteligência.
</p>

> Submódulo de [`steps-fera`](https://github.com/dadosfera/steps-fera).
> **Documentação completa (o que é um step, como desenvolver, como testar):**
> [`steps-fera/docs`](https://github.com/dadosfera/steps-fera/tree/main/docs).

## O que entra aqui

Steps **genéricos**, utilizáveis por qualquer cliente: S3, Snowflake, operações da
plataforma, analytics.

❌ Não entra: credencial, token, nome de cliente ou regra de negócio específica de
cliente. Isso vai para [`steps-private`](https://github.com/dadosfera/steps-private).

## Anatomia de um step

Cada step é um diretório em `steps/` com **três** arquivos, com nomes casados
(*sidecar naming* — a plataforma descobre os schemas pelo nome do arquivo `.py`):

```
steps/get_objects_from_s3/
├── get_objects_from_s3.py                  # lógica + handlers
├── get_objects_from_s3.py.schema.json      # JSON Schema dos parâmetros
└── get_objects_from_s3.py.uischema.json    # UI Schema (JsonForms) do formulário
```

O `.py` roda em dois contextos, decidido por `ORCHEST_STEP_UUID`:

```python
if ORCHEST_STEP_UUID is not None:
    orchest_handler()    # na plataforma: orchest.get_step_param / orchest.output
else:
    script_handler()     # local: config JSON em sys.argv[1], saída em arquivo
```

## Estrutura

```
├── steps/                  # os steps publicados
├── templates/              # esqueletos: get_from_data_source, put_in_target_location, transformation
├── manual_tests/flow_*/    # smoke tests encadeados (.sh numerados)
├── Dockerfile              # imagem dadosfera_steps (python:3.8 + deps + libs internas)
├── docker-compose.yml
├── requirements.txt
└── local.example.env
```

## Catálogo

| Domínio | Steps |
|---|---|
| **S3 / arquivos** | `get_objects_from_s3`, `put_objects_in_s3`, `get_files_from_google_drive` |
| **Snowflake** | `get_table_from_snowflake`, `get_table_using_sql`, `save_data_in_snowflake`, `save_data_in_snowflake_using_copy`, `merge_tables_from_snowflake`, `standardize_tables_in_snowflake`, `standardized_tables_union_all` |
| **Transformações Snowflake** | `snowflake_flatten_column`, `snowflake_remove_columns`, `snowflake_rename_columns`, `snowflake_text_transformations`, `snowflake_unpivot_data` |
| **Plataforma** | `get_data_assets`, `get_pipelines`, `get_status_of_all_pipelines`, `trigger_job`, `bulk_delete_connections`, `bulk_delete_data_assets`, `delete_project_intelligence` |
| **Fontes** | `get_data_from_c2s`, `get_data_from_sponte` |
| **Analytics** | `rfm_analysis` |

## Desenvolvimento local

```bash
cp local.example.env local.env      # AWS_PROFILE, OPENAI_API_KEY, ENV=local
docker compose build

docker compose run dadosfera_steps \
  python /project-dir/steps/get_objects_from_s3/get_objects_from_s3.py \
  '{"bucket_name": "meu-bucket", "prefix": "htmls/", "output_filepath": "/project-dir/output/out.json"}'
```

`./steps` é montado em `/project-dir/steps` e `./output` em `/project-dir/output`; suas
credenciais AWS entram via `~/.aws/credentials` (read-only). O build faz login no AWS
CodeArtifact para instalar `dadosfera` e `dadosfera_logs` — sem credencial AWS válida, o
build falha.

### Smoke tests encadeados

```bash
bash manual_tests/flow_extract_text_from_html/0_get_objects_from_s3.sh
bash manual_tests/flow_extract_text_from_html/1_extract_text_from_html.sh
bash manual_tests/flow_extract_text_from_html/2_put_objects_in_s3.sh
```

Cada script grava em `output/` o arquivo que o próximo consome — é assim que se valida o
encadeamento sem subir na plataforma.

## Criando um step novo

```bash
cp -r templates/get_from_data_source steps/get_data_from_foo
cd steps/get_data_from_foo
# renomeie os 3 arquivos para get_data_from_foo.py[.schema.json|.uischema.json]
```

Passo a passo completo: [2. Desenvolvendo um Step](https://github.com/dadosfera/steps-fera/blob/main/docs/02-desenvolvendo-um-step.md).

### Checklist

- [ ] Três arquivos com o *sidecar naming* correto, no mesmo diretório
- [ ] Todo parâmetro lido no `.py` existe no `schema.json` e aparece no `uischema.json`
- [ ] Lógica de negócio em função pura, separada dos handlers, com type hints
- [ ] `logger` em vez de `print`; nenhum segredo no código
- [ ] Roda local via docker compose
- [ ] Validado em um ambiente `dadosfera-ai-oss`: formulário renderiza e execução passa
- [ ] `README.md` do step e este catálogo atualizados

## Convenções

- `snake_case` no diretório, no arquivo e na função principal — os três iguais
- Nome no formato verbo + objeto + origem/destino (`get_table_from_snowflake`)
- **Conventional Commits** — o release é automático via `semantic-release`
  (`feat:` → minor, `fix:` → patch, `feat!:`/`BREAKING CHANGE:` → major)
- `pre-commit install` após clonar
