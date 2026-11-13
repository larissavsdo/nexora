# NEXORA — Validação Técnica e Análise de Desempenho

**Disciplina:** Banco de Dados II  
**Data dos testes iniciais:** 11/11/2026  
**Ambiente:** execução local com Docker Compose, FastAPI, PostgreSQL, MongoDB e Redis.

## 1. Objetivo

Este documento apresenta as verificações funcionais e os testes de desempenho realizados no NEXORA, um sistema de atendimento omnichannel desenvolvido como projeto acadêmico da disciplina de Banco de Dados II.

As validações tiveram como objetivo verificar o funcionamento dos componentes da aplicação, a integridade dos dados, a utilização de recursos avançados do PostgreSQL, a persistência documental no MongoDB, o mecanismo de cache com Redis e o processamento assíncrono de eventos.

Também foram realizados benchmarks para comparar consultas SQL com e sem utilização de índices e requisições com diferentes condições de cache.

Os resultados apresentados correspondem ao ambiente local de desenvolvimento e não representam garantias de desempenho em produção.

## 2. Ambiente de execução

O projeto utiliza Docker Compose para organizar os serviços necessários ao funcionamento da aplicação.

Os cinco serviços principais são:

| Serviço | Responsabilidade | Situação observada |
|---|---|---|
| `nexora-api` | Aplicação FastAPI | Em execução |
| `nexora-postgres` | Banco de dados relacional | Saudável |
| `nexora-mongo` | Banco de dados documental | Saudável |
| `nexora-redis` | Cache de consultas | Saudável |
| `nexora-worker` | Processamento assíncrono de eventos | Em execução |

A verificação dos serviços foi realizada por meio do Docker Compose.

O endpoint `GET /health` também foi testado por meio da documentação interativa da API.

A requisição retornou HTTP 200, com o seguinte conteúdo:

```json
{
  "system": "NEXORA",
  "status": "online"
}
```

Esse resultado confirmou que a API estava respondendo corretamente no momento da verificação.

## 3. Resumo das validações

A tabela abaixo reúne os principais requisitos e os resultados observados durante os testes.

| Componente ou requisito | Evidência obtida | Situação |
|---|---|---|
| PostgreSQL | Consulta retornou 100.001 registros em `tickets` | Validado |
| Integridade relacional | Identificadas 14 constraints e 11 índices na auditoria realizada | Validado |
| View SQL | `vw_ticket_overview` identificada e consultada | Validado |
| Trigger | `trg_ticket_updated_at` atualizou `updated_at` após um UPDATE | Validado |
| Função SQL | `set_ticket_updated_at` identificada | Identificada |
| Stored procedure | `sp_close_ticket` executada e testada com ROLLBACK | Validado |
| MongoDB | Documentos encontrados na coleção `messages` | Validado |
| Transactional Outbox | Eventos `message.created` e `ticket.status_updated` identificados como processados | Validado no fluxo de sucesso |
| Redis | `PING` retornou `PONG`; consultas retornaram MISS e HIT | Validado |
| Docker Compose | Cinco serviços em execução, com bancos e Redis saudáveis | Validado |
| Normalização até 3FN | Estrutura relacional separada por entidades e documentada | Justificativa documental |
| Recuperação de falhas da Outbox | Não foi realizado teste controlado de falha e reprocessamento | Não validado |
| Throughput concorrente | Não foi realizado teste com múltiplos clientes simultâneos | Não validado |

A carga inicial do banco foi composta por 100.000 chamados. Durante as verificações posteriores, foi identificado um chamado adicional, totalizando 100.001 registros.

## 4. Auditoria do PostgreSQL

O PostgreSQL foi utilizado para armazenar os dados relacionais e executar as operações transacionais do sistema.

A auditoria teve como objetivo verificar a presença de restrições de integridade, índices, views, triggers e stored procedures.

### 4.1. Verificação da quantidade de chamados

Foi executada a consulta:

```sql
SELECT COUNT(*) FROM tickets;
```

O resultado mais recente foi:

**100.001 chamados cadastrados.**

Esse volume permitiu realizar consultas sobre uma base de dados maior do que a utilizada em testes funcionais simples.

Entretanto, a quantidade de registros, isoladamente, não comprova a capacidade do sistema de atender múltiplas requisições simultâneas.

### 4.2. Restrições de integridade

A consulta ao catálogo `pg_constraint` identificou as seguintes restrições:

| Tipo de restrição | Quantidade |
|---|---:|
| CHECK | 2 |
| FOREIGN KEY | 4 |
| PRIMARY KEY | 5 |
| UNIQUE | 3 |
| **Total** | **14** |

As restrições contribuem para garantir a integridade dos dados e preservar os relacionamentos entre as entidades.

A contagem apresentada corresponde à auditoria mais recente das restrições identificadas nas tabelas do projeto.

### 4.3. Índices

Foram identificados 11 índices no PostgreSQL.

Entre os índices presentes estão:

- `ix_tickets_status_created`: utilizado para auxiliar consultas por status e data de criação.
- `ix_tickets_customer_id`: utilizado para consultas de chamados associados a um cliente.
- `ix_outbox_pending`: utilizado para localizar eventos pendentes de processamento.

A existência desses índices foi verificada por meio do catálogo `pg_indexes`.

Os índices contribuem para melhorar o desempenho de determinadas consultas, embora também impliquem custos de armazenamento e manutenção.

### 4.4. Comando de auditoria

A auditoria pode ser executada no PowerShell, dentro da pasta do projeto, com o seguinte comando:

```powershell
Get-Content .\sql\auditoria_requisitos.sql | docker compose exec -T postgres psql -U nexora -d nexora
```

Esse comando utiliza o script SQL de auditoria presente no projeto.

## 5. Validação da view SQL

O NEXORA utiliza a view `vw_ticket_overview`.

Ela reúne informações dos chamados com dados relacionados aos clientes, colaboradores e departamentos.

Durante os testes, foi realizada uma consulta à view e os registros foram retornados corretamente.

A utilização da view facilita a reutilização de consultas que envolvem diferentes tabelas e reduz a necessidade de repetir instruções SQL mais extensas.

A view convencional não armazena uma cópia independente dos resultados; sua definição é utilizada na execução das consultas.

## 6. Validação da trigger e da função SQL

O projeto possui a função `set_ticket_updated_at()` e a trigger `trg_ticket_updated_at`.

A trigger foi criada para atualizar automaticamente o campo `updated_at` quando um chamado é modificado.

### 6.1. Procedimento de teste

O teste foi realizado dentro de uma transação PostgreSQL.

1. Foi consultado o valor original de `updated_at`.
2. Foi executado um UPDATE no chamado.
3. O campo `updated_at` foi atualizado automaticamente.
4. Foi executado um ROLLBACK.
5. O valor anterior foi restaurado.

O resultado demonstrou o funcionamento da trigger no cenário testado.

A utilização do ROLLBACK permitiu verificar o comportamento sem manter a alteração de teste no banco.

## 7. Validação da stored procedure

O projeto utiliza a stored procedure `sp_close_ticket`, responsável pelo encerramento de chamados.

A procedure foi identificada no PostgreSQL por meio do catálogo `pg_proc`, com o valor `prokind = 'p'`.

Esse valor indica que o objeto corresponde a um procedimento.

### 7.1. Comando de verificação

```powershell
docker compose exec postgres psql -P pager=off -U nexora -d nexora -c "SELECT proname, prokind FROM pg_proc WHERE proname = 'sp_close_ticket';"
```

### 7.2. Teste transacional

A procedure foi executada dentro de uma transação explícita.

O chamado utilizado no teste apresentava inicialmente o status `in_progress`.

Após a execução da procedure, o status passou para `closed`.

Em seguida, foi executado ROLLBACK e o status retornou ao valor anterior.

Esse comportamento confirmou que a alteração realizada pela procedure participou da transação PostgreSQL e pôde ser revertida.

### 7.3. Disponibilização da procedure

O código está disponível no arquivo:

`sql/procedures.sql`

O script foi incluído na configuração de inicialização do PostgreSQL no Docker Compose.

É importante considerar que os scripts presentes em `/docker-entrypoint-initdb.d` são executados automaticamente quando o banco é inicializado com um diretório de dados vazio.

Por esse motivo, a procedure também foi instalada e verificada no banco de dados já existente durante os testes.

## 8. Validação do MongoDB

O MongoDB foi utilizado para armazenar documentos relacionados às mensagens dos atendimentos.

A coleção utilizada é `messages`.

Durante os testes, foram realizadas consultas para verificar a existência dos documentos.

### 8.1. Consulta utilizada

```javascript
db.messages.find(
  {},
  {
    _id: 0,
    ticket_id: 1,
    event_id: 1,
    content: 1
  }
).limit(5).toArray()
```

A consulta retornou documentos associados aos chamados cadastrados.

Entre os registros encontrados estava uma mensagem com os seguintes dados:

```json
{
  "event_id": 5,
  "ticket_id": 100001,
  "content": "oi, tudo bem?"
}
```

Esse resultado confirmou que o documento correspondente estava armazenado no MongoDB no momento da consulta.

## 9. Validação do Transactional Outbox

O NEXORA utiliza o padrão Transactional Outbox para organizar a sincronização assíncrona entre PostgreSQL e MongoDB.

Os eventos são registrados na tabela `outbox_events` e posteriormente processados pelo worker.

### 9.1. Consulta dos eventos

Foi utilizada a seguinte consulta:

```sql
SELECT
    id,
    event_type,
    processed,
    attempts,
    processed_at
FROM outbox_events
ORDER BY id DESC
LIMIT 5;
```

Na verificação realizada, foram identificados eventos dos tipos:

- `ticket.created`
- `message.created`
- `ticket.status_updated`

Os cinco eventos mais recentes apresentados na consulta estavam marcados com `processed = true`.

O campo `attempts` apresentava valor zero nesses registros.

Esse resultado demonstra que os eventos consultados estavam marcados como processados, mas não constitui, isoladamente, um teste de recuperação após falhas.

### 9.2. Correspondência entre PostgreSQL e MongoDB

Foi identificado no PostgreSQL o evento `message.created`, com identificador 5, marcado como processado.

Posteriormente, foi localizado no MongoDB um documento contendo:

- `event_id = 5`
- `ticket_id = 100001`
- `content = "oi, tudo bem?"`

A correspondência entre o identificador do evento e o documento armazenado no MongoDB representa uma evidência do funcionamento da sincronização assíncrona no cenário testado.

### 9.3. Limites da validação

O fluxo de sucesso foi verificado.

Entretanto, não foi realizado um teste controlado envolvendo a interrupção do worker após a gravação no MongoDB e antes da atualização do evento no PostgreSQL.

Portanto, o mecanismo de recuperação e a idempotência sob falhas ainda não foram comprovados experimentalmente.

## 10. Validação do Redis

O Redis foi utilizado como mecanismo de cache para consultas de chamados.

Inicialmente, foi executado o comando:

```redis
PING
```

O Redis retornou:

```text
PONG
```

Esse resultado confirmou que o serviço estava respondendo.

### 10.1. Verificação de Cache-Aside

Foi realizada uma consulta ao chamado de identificador 2.

Na primeira requisição, a API retornou:

`"cache": "MISS"`

Na segunda requisição, realizada após o preenchimento do cache, retornou:

`"cache": "HIT"`

Esses resultados demonstraram o funcionamento básico da estratégia Cache-Aside no cenário testado.

## 11. Benchmark de consultas SQL

O objetivo do benchmark foi comparar o desempenho de uma consulta utilizando índice com uma alternativa que realizava varredura sequencial.

### 11.1. Comando utilizado

```powershell
docker compose exec api python -m scripts.benchmark_rigoroso --samples 20 --warmup 3
```

O teste foi executado com:

- 20 amostras por cenário.
- 3 execuções de aquecimento.
- Base de aproximadamente 100.000 chamados.

O benchmark comparou os cenários sem exigir a remoção física dos índices.

### 11.2. Resultados

| Métrica | Com índice | Sem utilização de índice |
|---|---:|---:|
| Amostras | 20 | 20 |
| Mediana | 0,8865 ms | 18,6161 ms |
| P95 | 1,1507 ms | 23,4606 ms |

A mediana da consulta sem utilização do índice foi aproximadamente 21 vezes maior que a da consulta indexada.

O resultado demonstra uma diferença significativa de desempenho para a consulta e o conjunto de dados avaliados.

### 11.3. Planos de execução

Durante a análise, foram observadas estratégias distintas de execução.

No cenário indexado, o PostgreSQL utilizou uma operação do tipo `Index Scan`.

No cenário de varredura sequencial, foi utilizada uma operação do tipo `Seq Scan`.

Essas estratégias podem apresentar diferenças relevantes conforme a seletividade da consulta, a quantidade de registros e as condições do ambiente.

### 11.4. Observação sobre medições anteriores

Uma medição isolada anterior com `EXPLAIN (ANALYZE, BUFFERS)` apresentou aproximadamente 22,487 ms no cenário indexado e 1.172,838 ms com varredura sequencial forçada.

Esses resultados pertencem a outra execução e não foram utilizados para calcular as medianas do benchmark repetido.

Para a comparação principal, foram considerados os resultados das 20 amostras por cenário.

## 12. Benchmark do Cache-Aside com Redis

O segundo benchmark teve como objetivo comparar os tempos de resposta das requisições com cache MISS e cache HIT.

### 12.1. Comando utilizado

```powershell
docker compose exec api python -m scripts.benchmark_cache --samples 20 --ticket-id 2
```

A rotina executa consultas ao chamado 2 e controla a presença da entrada correspondente no Redis.

No cenário MISS, a aplicação precisa buscar as informações no PostgreSQL.

No cenário HIT, as informações podem ser recuperadas diretamente do Redis.

A remoção da chave de cache não exclui o chamado armazenado no PostgreSQL.

### 12.2. Resultados

| Métrica | Cache MISS | Cache HIT |
|---|---:|---:|
| Amostras | 20 | 20 |
| Média | 8,7360 ms | 8,4329 ms |
| Mediana | 7,7625 ms | 3,7023 ms |
| P95 | 15,4755 ms | 37,8096 ms |
| Mínimo | 4,7642 ms | 2,7878 ms |
| Máximo | 18,7090 ms | 41,4696 ms |

A mediana do cenário HIT foi aproximadamente 2,10 vezes menor que a do cenário MISS.

Entretanto, o P95 do cenário HIT foi superior ao observado no MISS.

Isso indica que, embora a latência mediana tenha sido menor com o cache, algumas requisições apresentaram tempos mais elevados.

Portanto, o benchmark demonstra uma melhoria na mediana, mas não permite afirmar que todas as consultas com cache foram mais rápidas.

### 12.3. Limitações do benchmark

As medições incluem o tempo das requisições HTTP locais.

O teste não representa a latência de acesso pela internet nem o comportamento da aplicação com múltiplos usuários simultâneos.

Os resultados podem variar conforme a carga da máquina, o sistema operacional e as condições de execução dos serviços.

## 13. Verificação das propriedades transacionais

Os testes da stored procedure e da trigger foram realizados com transações explícitas.

Nos dois casos, foi possível executar uma alteração, verificar seu efeito e utilizar ROLLBACK para restaurar o estado anterior.

Esses resultados demonstraram o comportamento de reversão das alterações no PostgreSQL.

A validação apresentada não equivale a uma comprovação experimental completa de todas as propriedades ACID sob diferentes condições de concorrência e falha.

## 14. Arquivos de evidência

Os resultados dos benchmarks estão disponíveis nos arquivos:

- `results/benchmark_sql.json`
- `results/benchmark_cache.json`

Além dos arquivos JSON, foram produzidas capturas de tela das consultas e verificações realizadas durante os testes.

Entre as evidências estão:

- Execução dos serviços Docker Compose.
- Dashboard com 100.001 chamados.
- Resposta do endpoint de saúde da API.
- Contagem de chamados no PostgreSQL.
- Auditoria de constraints e índices.
- Consulta à view SQL.
- Verificação da trigger e da stored procedure.
- Consulta aos eventos Outbox.
- Consulta aos documentos MongoDB.
- Teste de cache MISS e HIT.
- Resultados dos benchmarks SQL e Redis.

As capturas documentam os resultados observados no ambiente local.

## 15. Limitações dos testes

As verificações realizadas apresentam algumas limitações que devem ser consideradas na interpretação dos resultados.

1. Os testes foram executados em ambiente local de desenvolvimento.
2. Os benchmarks utilizaram 20 amostras por cenário.
3. Não foi realizado teste de throughput com múltiplos usuários simultâneos.
4. Não foi realizado teste controlado de falha e recuperação do worker.
5. A idempotência da Outbox não foi comprovada por um cenário de reprocessamento forçado.
6. Os tempos medidos podem variar conforme as condições da máquina.
7. A existência de 100.001 chamados não comprova, isoladamente, a capacidade de processamento sob alta concorrência.

Também é importante evitar a execução de comandos destrutivos no ambiente de testes.

O comando `docker compose down -v`, por exemplo, pode remover volumes persistentes e provocar perda dos dados armazenados.

O script `scripts/benchmark_rigoroso.py` deve ser priorizado em relação ao benchmark SQL legado quando o objetivo for repetir a comparação sem remover fisicamente índices.

## 16. Conclusão

Os testes realizados demonstraram o funcionamento dos principais componentes do NEXORA no ambiente local.

O PostgreSQL armazenou os registros relacionais e permitiu validar restrições de integridade, índices, view, trigger, função e stored procedure.

O MongoDB apresentou documentos de mensagens associados aos chamados, enquanto o Redis respondeu corretamente aos testes de conectividade e cache.

A consulta aos eventos Outbox e a correspondência com documentos no MongoDB demonstraram o funcionamento do fluxo de sincronização assíncrona no cenário de sucesso.

Os benchmarks permitiram comparar diferentes estratégias de acesso aos dados. A utilização de índice apresentou menor latência nas consultas SQL avaliadas, enquanto o cache Redis apresentou menor mediana de tempo de resposta, embora com maior variabilidade em parte das requisições.

Os resultados obtidos permitem analisar, de forma prática, conceitos de bancos de dados relacionais e não relacionais, transações, integridade, índices, cache e consistência eventual.

O NEXORA atende ao propósito de demonstrar esses conceitos em um protótipo acadêmico funcional, respeitando as limitações dos testes realizados.