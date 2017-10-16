CREATE OR REPLACE FUNCTION not_uploaded()
RETURNS TABLE (
    upload_domain text,
    name text
)
STABLE
SECURITY DEFINER
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
        SELECT ud.name::text, n.name::text FROM uploads
        INNER JOIN newdraws n USING (newdraw)
        INNER JOIN upload_domains ud USING (upload_domain)
        WHERE state = 'not_uploaded';
END;
$$;

CREATE OR REPLACE FUNCTION set_uploading
(
    p_upload_domain citext,
    p_name text
)
RETURNS void
VOLATILE
SECURITY DEFINER
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE uploads AS u
    SET state = 'uploading'
    FROM uploads u2
    INNER JOIN newdraws n USING (newdraw)
    INNER JOIN upload_domains ud USING (upload_domain)
    WHERE u2.upload = u.upload
    AND u2.state = 'not_uploaded'
    AND n.name = p_name
    AND ud.name = p_upload_domain;
END;
$$;

CREATE OR REPLACE FUNCTION set_uploaded
(
    p_upload_domain citext,
    p_name text
)
RETURNS void
VOLATILE
SECURITY DEFINER
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE uploads AS u
    SET state = 'uploaded'
    FROM uploads u2
    INNER JOIN newdraws n USING (newdraw)
    INNER JOIN upload_domains ud USING (upload_domain)
    WHERE u2.upload = u.upload
    AND u2.state = 'uploading'
    AND n.name = p_name
    AND ud.name = p_upload_domain;
END;
$$;

CREATE OR REPLACE FUNCTION set_not_uploaded
(
    p_upload_domain citext,
    p_name text
)
RETURNS void
VOLATILE
SECURITY DEFINER
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE uploads AS u
    SET state = 'not_uploaded'
    FROM uploads u2
    INNER JOIN newdraws n USING (newdraw)
    INNER JOIN upload_domains ud USING (upload_domain)
    WHERE u2.upload = u.upload
    AND u2.state <> 'uploaded'
    AND n.name = p_name
    AND ud.name = p_upload_domain;
END;
$$;

GRANT EXECUTE ON FUNCTION not_uploaded() TO multibot;
GRANT EXECUTE ON FUNCTION set_uploading(citext, text) TO multibot;
GRANT EXECUTE ON FUNCTION set_uploaded(citext, text) TO multibot;
GRANT EXECUTE ON FUNCTION set_not_uploaded(citext, text) TO multibot;
