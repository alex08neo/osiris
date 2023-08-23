CREATE TABLE IF NOT EXISTS `guilds` (
  `guild_id` varchar(20) NOT NULL,
  `channels` text DEFAULT '',
  `model` varchar(20) DEFAULT 'gpt-4',
  `opt` int(1) DEFAULT 1,
  `temperature` float(2,1) DEFAULT 0.5,
  `instructions` text DEFAULT 'You are Osiris, an AI chatbot in a Discord server.',
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