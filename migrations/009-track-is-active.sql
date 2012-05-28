ALTER TABLE music_track ADD COLUMN is_active bool NULL;
UPDATE music_track SET is_active=1;
ALTER TABLE music_track MODIFY is_active bool NOT NULL;

ALTER TABLE music_track_file ADD COLUMN is_active bool NULL;
UPDATE music_track_file SET is_active=1;
ALTER TABLE music_track_file MODIFY is_active bool NOT NULL;

CREATE INDEX `music_track_e01be369` ON `music_track` (`is_active`);
CREATE INDEX `music_track_file_e01be369` ON `music_track_file` (`is_active`);
