ALTER TABLE music_track ADD COLUMN `session_id` varchar(40) NULL;
ALTER TABLE `music_track` ADD CONSTRAINT `session_id_refs_session_key_eece831d`
  FOREIGN KEY (`session_id`) REFERENCES `sync_session` (`session_key`);
CREATE INDEX `music_track_6b4dc4c3` ON `music_track` (`session_id`);
