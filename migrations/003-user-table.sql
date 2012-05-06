-- Making this way easier:
DELETE FROM music_audiofile;

CREATE TABLE `music_email` (
    `id` int(11) AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL,
    `email` varchar(255) NOT NULL UNIQUE,
    `upload_key` varchar(255) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

ALTER TABLE music_audiofile DROP COLUMN email;
ALTER TABLE music_audiofile ADD COLUMN `email_id` int(11) NOT NULL;
ALTER TABLE `music_audiofile` ADD CONSTRAINT `email_id_id_refs_id_1064e535`
    FOREIGN KEY (`email_id`) REFERENCES `music_email` (`id`)
    ON DELETE CASCADE;
CREATE INDEX `music_audiofile_6abdd435` ON `music_audiofile` (`email_id`);
