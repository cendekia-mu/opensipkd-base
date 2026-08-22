create user apps identified by aa;
create user webr identified by aa;
ALTER USER apps QUOTA UNLIMITED ON USERS;
GRANT DBA TO webr;
BEGIN
   -- Loop through every existing table in the APPS schema
   FOR t IN (SELECT table_name FROM all_tables WHERE owner = 'APPS') LOOP
      -- Execute explicit object-level grants safely
      EXECUTE IMMEDIATE 'GRANT REFERENCES ON apps."' || t.table_name || '" TO webr';
   END LOOP;
END;
BEGIN
   -- Loop through every existing table in the APPS schema
   FOR t IN (SELECT table_name FROM all_tables WHERE owner = 'APPS') LOOP
      -- Execute explicit object-level grants safely
      EXECUTE IMMEDIATE 'GRANT REFERENCES ON apps."' || t.table_name || '" TO webr';
   END LOOP;
END;
BEGIN
   FOR t IN (SELECT table_name FROM user_tables) LOOP
      EXECUTE IMMEDIATE 'DROP TABLE "' || t.table_name || '" CASCADE CONSTRAINTS PURGE';
   END LOOP;
END;
/

CREATE TABLE apps.external_identities (
        external_id VARCHAR2(255 CHAR) NOT NULL, 
        external_user_name VARCHAR2(255 CHAR), 
        local_user_id INTEGER NOT NULL, 
        provider_name VARCHAR2(50 CHAR) NOT NULL, 
        access_token VARCHAR2(512 CHAR), 
        alt_token VARCHAR2(512 CHAR), 
        token_secret VARCHAR2(512 CHAR), 
        CONSTRAINT pk_external_identities PRIMARY KEY (external_id, local_user_id, provider_name), 
        -- FIX: Add the parent table's schema prefix here
        FOREIGN KEY(local_user_id) REFERENCES APPS.users (id) ON DELETE CASCADE
);