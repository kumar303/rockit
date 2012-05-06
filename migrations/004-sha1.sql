DELETE FROM music_audiofile;
ALTER TABLE music_audiofile ADD COLUMN `sha1` varchar(40) NOT NULL;
CREATE INDEX `music_audiofile_9408048c` ON `music_audiofile` (`sha1`);
