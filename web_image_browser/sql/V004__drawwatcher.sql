CREATE OR REPLACE FUNCTION add_draw (
    drawpath text
)
RETURNS bool
VOLATILE
SECURITY DEFINER
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM true FROM newdraws WHERE name = drawpath;

    IF FOUND THEN
        RETURN false;
    END IF;

    INSERT INTO newdraws (name) VALUES (drawpath);
    RETURN true;
END;
$$;

DO
$$
BEGIN
IF NOT EXISTS (
    SELECT true
    FROM   pg_catalog.pg_user
    WHERE  usename = 'drawwatcher')
THEN
    CREATE USER drawwatcher LOGIN PASSWORD 'YOURPASSWORDHERE';
END IF;
END
$$;


GRANT EXECUTE ON FUNCTION add_draw(text) TO drawwatcher;
