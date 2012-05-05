ALTER TABLE music_audiofile ADD COLUMN `byte_size` int(11) UNSIGNED NOT NULL DEFAULT 0;
ALTER TABLE music_audiofile ALTER `byte_size` DROP DEFAULT;
