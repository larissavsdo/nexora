-- Auditoria SOMENTE LEITURA: execute com psql -f /app/sql/auditoria_requisitos.sql
\echo '===== TABELAS E QUANTIDADE DE CHAMADOS ====='
SELECT COUNT(*) AS total_tickets FROM tickets;
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY table_name;
\echo '===== CHAVES PRIMARIAS, ESTRANGEIRAS, UNIQUE, CHECK ====='
SELECT tc.table_name, tc.constraint_name, tc.constraint_type
FROM information_schema.table_constraints tc
WHERE tc.table_schema = 'public' ORDER BY tc.table_name, tc.constraint_type, tc.constraint_name;
\echo '===== RELACIONAMENTOS FK ====='
SELECT conrelid::regclass AS tabela, conname AS restricao, confrelid::regclass AS referencia
FROM pg_constraint WHERE contype = 'f' AND connamespace = 'public'::regnamespace
ORDER BY 1,2;
\echo '===== INDICES ====='
SELECT tablename, indexname, indexdef FROM pg_indexes WHERE schemaname = 'public' ORDER BY tablename,indexname;
\echo '===== VIEWS ====='
SELECT table_name AS view_name FROM information_schema.views WHERE table_schema = 'public' ORDER BY table_name;
\echo '===== FUNCOES E PROCEDIMENTOS ====='
SELECT p.proname AS nome, CASE p.prokind WHEN 'p' THEN 'PROCEDURE' WHEN 'f' THEN 'FUNCTION' ELSE p.prokind::text END AS tipo
FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname = 'public' ORDER BY 1;
\echo '===== TRIGGERS ====='
SELECT event_object_table AS tabela, trigger_name, event_manipulation AS evento, action_timing AS momento
FROM information_schema.triggers WHERE trigger_schema = 'public' ORDER BY 1,2;
\echo '===== VIEW - EXEMPLO ====='
SELECT * FROM vw_ticket_overview LIMIT 3;
\echo '===== OUTBOX - CONTAGENS ====='
SELECT processed, COUNT(*) AS quantidade FROM outbox_events GROUP BY processed ORDER BY processed;
