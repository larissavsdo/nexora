
CREATE OR REPLACE PROCEDURE sp_close_ticket(
    IN p_ticket_id INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_status VARCHAR;
BEGIN
    SELECT status
    INTO v_status
    FROM tickets
    WHERE id = p_ticket_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Chamado % não encontrado.', p_ticket_id;
    END IF;

    IF v_status = 'closed' THEN
        RAISE EXCEPTION 'Chamado % já está encerrado.', p_ticket_id;
    END IF;

    UPDATE tickets
    SET status = 'closed'
    WHERE id = p_ticket_id;
END;
$$;
