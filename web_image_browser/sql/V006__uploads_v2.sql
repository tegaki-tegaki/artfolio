CREATE EXTENSION "citext";

CREATE TABLE upload_domains (
    upload_domain BIGSERIAL PRIMARY KEY,
    name citext UNIQUE
);

CREATE TYPE upload_state AS ENUM ('not_uploaded', 'uploading', 'uploaded', 'error');

ALTER TABLE uploads ADD COLUMN state upload_state DEFAULT 'not_uploaded';
ALTER TABLE uploads ALTER state SET NOT NULL;
ALTER TABLE uploads ADD COLUMN ctime timestamptz DEFAULT now();

ALTER TABLE uploads DROP COLUMN domain_name RESTRICT;
ALTER TABLE uploads ADD COLUMN upload_domain bigint;
ALTER TABLE uploads ADD CONSTRAINT uploads_domain_name_fkey FOREIGN KEY (upload_domain) REFERENCES upload_domains (upload_domain);

ALTER TABLE uploads ALTER ctime SET NOT NULL;

-- TRIGGER, when insert on newdraws, -> insert on uploads (one row for each row in upload_domains)
CREATE FUNCTION add_uploads() RETURNS trigger
VOLATILE
SECURITY DEFINER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO uploads (newdraw, upload_domain)
    SELECT
        NEW.newdraw,
        ud.upload_domain
    FROM upload_domains ud;

    RETURN NEW;
END;
$$;

CREATE TRIGGER newdraws_add_uploads AFTER INSERT ON newdraws
FOR EACH ROW EXECUTE PROCEDURE add_uploads();
