CREATE TABLE IF NOT EXISTS departments (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS customers (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(160) NOT NULL,
  email VARCHAR(180) NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS agents (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(160) NOT NULL,
  email VARCHAR(180) NOT NULL UNIQUE,
  department_id BIGINT NOT NULL REFERENCES departments(id) ON DELETE RESTRICT
);
CREATE TABLE IF NOT EXISTS tickets (
  id BIGSERIAL PRIMARY KEY,
  subject VARCHAR(220) NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  status VARCHAR(20) NOT NULL DEFAULT 'open' CHECK (status IN ('open','in_progress','waiting','resolved','closed')),
  priority VARCHAR(20) NOT NULL DEFAULT 'normal' CHECK (priority IN ('low','normal','high','urgent')),
  customer_id BIGINT NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
  agent_id BIGINT REFERENCES agents(id) ON DELETE SET NULL,
  department_id BIGINT NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_tickets_customer_id ON tickets(customer_id);
CREATE INDEX IF NOT EXISTS ix_tickets_status_created ON tickets(status, created_at DESC);
CREATE TABLE IF NOT EXISTS outbox_events (
  id BIGSERIAL PRIMARY KEY,
  event_type VARCHAR(80) NOT NULL,
  aggregate_id BIGINT NOT NULL,
  payload JSONB NOT NULL,
  processed BOOLEAN NOT NULL DEFAULT FALSE,
  attempts INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  processed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_outbox_pending ON outbox_events(processed, id) WHERE processed = FALSE;

CREATE OR REPLACE VIEW vw_ticket_overview AS
SELECT t.id AS ticket_id, t.subject, t.status, t.priority, t.created_at,
       c.name AS customer_name, a.name AS agent_name, d.name AS department_name
FROM tickets t JOIN customers c ON c.id=t.customer_id
LEFT JOIN agents a ON a.id=t.agent_id JOIN departments d ON d.id=t.department_id;

CREATE OR REPLACE FUNCTION set_ticket_updated_at() RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS trg_ticket_updated_at ON tickets;
CREATE TRIGGER trg_ticket_updated_at BEFORE UPDATE ON tickets
FOR EACH ROW EXECUTE FUNCTION set_ticket_updated_at();

INSERT INTO departments(name) VALUES ('Comercial'),('Suporte'),('Financeiro'),('Implantação'),('Relacionamento')
ON CONFLICT (name) DO NOTHING;
