DROP TABLE music_audiofile;

CREATE TABLE `music_track` (
    `id` int(11) AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL,
    `email_id` int(11) NOT NULL,
    `temp_path` varchar(255) NOT NULL,
    `artist` varchar(255) NOT NULL,
    `album` varchar(255) NOT NULL,
    `track` varchar(255) NOT NULL,
    `track_num` int(11),
    `large_art_url` varchar(255),
    `medium_art_url` varchar(255),
    `small_art_url` varchar(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

ALTER TABLE `music_track`
    ADD CONSTRAINT `email_id_refs_id_1c7e868`
    FOREIGN KEY (`email_id`) REFERENCES `music_email` (`id`);

CREATE TABLE `music_track_file` (
    `id` int(11) AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL,
    `sha1` varchar(40) NOT NULL,
    `byte_size` int(11) NOT NULL,
    `track_id` int(11) NOT NULL,
    `type` varchar(4) NOT NULL,
    `s3_url` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

ALTER TABLE `music_track_file` ADD
    CONSTRAINT `track_id_refs_id_53fe3d9b`
    FOREIGN KEY (`track_id`) REFERENCES `music_track` (`id`);

CREATE INDEX `music_track_6abdd435` ON `music_track` (`email_id`);
CREATE INDEX `music_track_738a9118` ON `music_track` (`artist`);
CREATE INDEX `music_track_be9cd983` ON `music_track` (`album`);
CREATE INDEX `music_track_file_9408048c` ON `music_track_file` (`sha1`);
CREATE INDEX `music_track_file_61144240` ON `music_track_file` (`track_id`);
CREATE INDEX `music_track_file_type` ON `music_track_file` (`type`);
