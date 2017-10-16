ALTER TABLE newdraws ADD COLUMN ctime timestamptz DEFAULT now();

UPDATE newdraws SET ctime = now();

ALTER TABLE newdraws ALTER ctime SET NOT NULL;
