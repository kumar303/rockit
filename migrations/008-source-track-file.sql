ALTER TABLE music_track ADD COLUMN source_track_file_id int(11) NULL;
ALTER TABLE `music_track`
    ADD CONSTRAINT `source_track_file_id_refs_id_7948bb65`
    FOREIGN KEY (`source_track_file_id`) REFERENCES `music_track_file` (`id`);
CREATE INDEX `music_track_e626bcd7` ON `music_track` (`source_track_file_id`);
