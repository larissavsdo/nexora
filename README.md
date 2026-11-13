# NEXORA — Sistema Omnichannel de Gestão de Atendimentos

## Sobre o projeto

O NEXORA é um projeto acadêmico desenvolvido para a disciplina de Banco de Dados II. Seu objetivo é demonstrar a integração de diferentes modelos de persistência em uma aplicação de gestão de atendimentos. A solução combina PostgreSQL, MongoDB e Redis, disponibiliza uma API REST construída com FastAPI e apresenta uma interface web para consulta e acompanhamento de chamados.

O sistema é um protótipo funcional para fins de estudo e demonstração. Não realiza integrações oficiais com WhatsApp ou outras plataformas de mensagens e não está preparado para operação em produção.

## Tecnologias e responsabilidades

| Tecnologia | Utilização |
| --- | --- |
| Python e FastAPI | API REST e regras de aplicação |
| PostgreSQL | Clientes, colaboradores, departamentos, chamados e eventos da Outbox |
| MongoDB | Armazenamento documental do histórico de mensagens |
| Redis | Cache de consultas a chamados, com estratégia Cache-Aside |
| Docker Compose | Inicialização e integração dos serviços |
| SQLAlchemy | Acesso aos dados relacionais |

## Organização dos dados

O banco relacional possui as tabelas `customers`, `agents`, `departments`, `tickets` e `outbox_events`. Os chamados referenciam clientes, departamentos e, quando atribuído, um colaborador. O modelo utiliza chaves primárias, estrangeiras e restrições de integridade. A estrutura relacional foi organizada para reduzir redundância e permitir a discussão da normalização até a terceira forma normal (3FN).

As mensagens são armazenadas no MongoDB. O Redis funciona como armazenamento temporário para acelerar consultas, sem substituir o PostgreSQL como fonte dos dados dos chamados.

### Sincronização de mensagens

O cadastro de uma mensagem produz um evento na tabela `outbox_events` durante a operação no PostgreSQL. Um worker independente consulta os eventos pendentes e realiza a gravação correspondente no MongoDB. A API retorna HTTP `202 Accepted` para indicar que a solicitação foi aceita para processamento assíncrono. Esse fluxo demonstra o padrão Transactional Outbox e consistência eventual; não equivale a uma transação distribuída entre PostgreSQL e MongoDB.

## Requisitos para execução

- Docker Desktop instalado e em execução.
- Virtualização habilitada no computador.
- Terminal PowerShell ou equivalente.
- VS Code é opcional.

## Como executar

1. Abra a pasta do projeto no terminal.
2. Se ainda não existir, crie o arquivo `.env` a partir de `.env.example` e revise as configurações locais. Não publique senhas ou arquivos `.env`.
3. Inicie os serviços:

```powershell
docker compose up --build -d
```

4. Confira o estado dos contêineres:

```powershell
docker compose ps
```

5. Acesse:

- Interface web: http://localhost:8000/app
- Documentação interativa da API: http://localhost:8000/docs
- Verificação da API: http://localhost:8000/health

**Atenção:** os arquivos de inicialização do PostgreSQL em `sql/` são executados automaticamente apenas na criação de um volume de dados vazio. A inclusão posterior de um arquivo SQL não o executa novamente em um banco existente.

## Carga de dados de demonstração

O script de carga cadastra clientes, colaboradores e completa o banco até pelo menos 100.000 chamados. Os 30 nomes de colaboradores foram definidos no arquivo `scripts/seed.py`; outros dados de teste são gerados com Faker.

Execute a carga apenas quando necessário, em ambiente de demonstração:

```powershell
docker compose exec api python -m scripts.seed
```

Confira a quantidade de chamados:

```powershell
docker compose exec postgres psql -U nexora -d nexora -c "SELECT COUNT(*) FROM tickets;"
```

O script consulta a quantidade existente antes de completar a carga. Não é necessário executá-lo novamente em um banco já populado com 100 mil chamados.

## Endpoints principais

| Método e rota | Finalidade |
| --- | --- |
| `GET /health` | Verificar a disponibilidade da API |
| `POST /tickets` | Criar chamado |
| `GET /tickets` | Listar chamados |
| `GET /tickets/{id}` | Consultar chamado com Cache-Aside |
| `PATCH /tickets/{id}/status` | Atualizar status e invalidar cache |
| `POST /tickets/{id}/messages` | Registrar solicitação de mensagem na Outbox |
| `GET /tickets/{id}/messages` | Consultar histórico de mensagens no MongoDB |

Exemplo de corpo para `POST /tickets`:

```json
{
  "subject": "Dúvida sobre emissão de nota",
  "description": "Cliente precisa de orientação.",
  "customer_id": 1,
  "department_id": 2,
  "agent_id": 1,
  "priority": "normal"
}
```

Os identificadores de cliente, departamento e colaborador precisam existir no banco.

Exemplo de mensagem aceito nos testes realizados:

```json
{
  "sender_type": "customer",
  "sender_id": 1,
  "content": "Preciso de ajuda com meu atendimento.",
  "message_type": "text"
}
```

## Recursos de banco de dados

O projeto inclui índices, restrições, a view `vw_ticket_overview`, o trigger `trg_ticket_updated_at`, a função `set_ticket_updated_at` e a procedure `sp_close_ticket`. Esta última foi testada em uma transação com `ROLLBACK`, confirmando a reversão da alteração de status. O trigger de atualização de data também foi verificado em transação reversível.

Os arquivos `sql/init.sql` e `sql/procedures.sql` fazem parte da inicialização do PostgreSQL em novos volumes. Para auditoria do esquema, consulte `sql/auditoria_requisitos.sql`.

## Testes de desempenho

Os resultados abaixo foram obtidos no ambiente local do projeto e não representam garantias de desempenho em outros computadores.

| Experimento | Mediana | p95 |
| --- | ---: | ---: |
| Consulta SQL com índice | 0,886 ms | 1,151 ms |
| Consulta SQL sem uso do índice | 18,616 ms | 23,461 ms |
| Consulta de chamado sem cache (MISS) | 7,763 ms | 15,475 ms |
| Consulta de chamado com cache (HIT) | 3,702 ms | 37,810 ms |

Foram realizadas 20 amostras por cenário. O ganho mediano observado foi de aproximadamente **21 vezes** na comparação SQL e **2,10 vezes** no experimento de cache. No cache, o p95 do cenário HIT foi superior ao do MISS, portanto a melhoria não foi uniforme em todas as medições.

Para repetir os testes:

```powershell
docker compose exec api python -m scripts.benchmark_rigoroso --samples 20 --warmup 3
docker compose exec api python -m scripts.benchmark_cache --samples 20 --ticket-id 2
```

O benchmark SQL rigoroso utiliza configurações de sessão para comparar planos de execução, sem remover índices. Evite executar o script legado `scripts/benchmark_sql.py` sem revisar seu comportamento, pois ele remove e recria um índice.

## Estrutura resumida

```text
Nexora/
├── app/                  API, modelos, serviços, worker e interface
├── scripts/              carga de dados e benchmarks
├── sql/                  estrutura SQL, procedure e auditoria
├── docs/                 arquitetura e registros de validação
├── docker-compose.yml    orquestração dos serviços
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Limitações e evolução

O NEXORA não possui autenticação e autorização completas, integrações externas oficiais, nem mecanismos de segurança e observabilidade suficientes para produção. A atribuição de colaboradores aos departamentos no script de carga é aleatória. O worker utiliza consulta periódica dos eventos e pode ser aprimorado com métricas, política de tentativas, tratamento de falhas e reprocessamento administrativo.

Os resultados dos testes validam os cenários executados, mas não substituem testes de carga concorrente, recuperação de falhas ou uma validação integral de instalação em ambiente novo.

## Encerramento

O projeto demonstra, em um mesmo fluxo de atendimento, o uso complementar de persistência relacional, documental e chave-valor, além de transações SQL, processamento assíncrono e avaliação de desempenho. A interface web facilita a apresentação dos conceitos, enquanto a API e os scripts permitem reproduzir os principais experimentos.
