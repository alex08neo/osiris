CREATE TABLE IF NOT EXISTS `guilds` (
  `guild_id` varchar(20) NOT NULL,
  `channel_id` varchar(20),
  `model` varchar(20) DEFAULT 'gpt-3.5-turbo-16k',
  `opt` int(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`guild_id`)
);

CREATE TABLE IF NOT EXISTS `blacklist` (
  `user_id` varchar(20) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`)
);

CREATE TABLE IF NOT EXISTS `messages` (
  `guild_id` varchar(20) NOT NULL,
  `channel_id` varchar(20) NOT NULL,
  `author_id` varchar(20) NOT NULL,
  `content` text NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`guild_id`) REFERENCES `guilds` (`guild_id`)
);