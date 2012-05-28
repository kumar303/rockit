CREATE TABLE `sync_session` (
    `session_key` varchar(40) NOT NULL PRIMARY KEY,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL,
    `is_active` bool NOT NULL,
    `email_id` integer NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

ALTER TABLE `sync_session` ADD CONSTRAINT `email_id_refs_id_beee339a`
  FOREIGN KEY (`email_id`) REFERENCES `music_email` (`id`);
CREATE INDEX `sync_session_e01be369` ON `sync_session` (`is_active`);
CREATE INDEX `sync_session_6abdd435` ON `sync_session` (`email_id`);

ALTER TABLE music_track_file ADD COLUMN `session_id` varchar(40) NULL;
ALTER TABLE `music_track_file` ADD CONSTRAINT `session_id_refs_session_key_39837d29`
  FOREIGN KEY (`session_id`) REFERENCES `sync_session` (`session_key`);
CREATE INDEX `music_track_file_6b4dc4c3` ON `music_track_file` (`session_id`);
