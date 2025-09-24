-- USERS
CREATE TABLE `user` (
   user_id                VARCHAR(36)  NOT NULL PRIMARY KEY,
   email                  VARCHAR(255) NOT NULL UNIQUE,
   first_name             VARCHAR(100),
   last_name              VARCHAR(100),
   avatar_url             VARCHAR(500),
   pin                    TEXT,
   public_key             TEXT,
   encrypted_private_key  TEXT
);


-- SHEETS
CREATE TABLE sheet (
   sheet_id     VARCHAR(36)  NOT NULL PRIMARY KEY,
   link         VARCHAR(1000) NOT NULL,
   creator_id   VARCHAR(36)  NOT NULL,
   created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
   FOREIGN KEY (creator_id) REFERENCES `user`(user_id)
       ON UPDATE CASCADE
       ON DELETE RESTRICT
);


CREATE INDEX idx_sheet_creator ON sheet (creator_id);


-- USER <-> SHEET (many-to-many)
CREATE TABLE user_sheet (
   user_id              VARCHAR(36) NOT NULL,
   sheet_id             VARCHAR(36) NOT NULL,
   role                 ENUM('owner','editor','viewer') NOT NULL DEFAULT 'viewer',
   encrypted_sheet_key  TEXT,              -- shared sheet key being encrypted by public key
   is_favorite          BOOLEAN DEFAULT FALSE,
   last_accessed_at     DATETIME NULL,
   PRIMARY KEY (user_id, sheet_id),
   FOREIGN KEY (user_id) REFERENCES `user`(user_id)
       ON UPDATE CASCADE
       ON DELETE CASCADE,
   FOREIGN KEY (sheet_id) REFERENCES sheet(sheet_id)
       ON UPDATE CASCADE
       ON DELETE CASCADE
);


CREATE INDEX idx_usersheet_sheet ON user_sheet (sheet_id);
CREATE INDEX idx_usersheet_user  ON user_sheet (user_id);

