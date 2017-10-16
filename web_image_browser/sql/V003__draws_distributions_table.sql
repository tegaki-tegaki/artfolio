CREATE TABLE uploads (
    upload BIGSERIAL PRIMARY KEY,

    domain_name text,

    newdraw integer REFERENCES newdraws
);
