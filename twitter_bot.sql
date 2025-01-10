-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jan 10, 2025 at 03:15 PM
-- Server version: 10.4.24-MariaDB
-- PHP Version: 8.1.6

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `twitter_bot`
--

-- --------------------------------------------------------

--
-- Table structure for table `tweet_record`
--

CREATE TABLE `tweet_record` (
  `id` int(11) NOT NULL,
  `tagged_tweet_id` varchar(255) DEFAULT NULL,
  `author_id` varchar(255) DEFAULT NULL,
  `tagged_tweet` longtext DEFAULT NULL,
  `replied_comments` longtext DEFAULT NULL,
  `post_status` enum('pending','failed','successful') DEFAULT 'pending'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `tweet_record`
--

INSERT INTO `tweet_record` (`id`, `tagged_tweet_id`, `author_id`, `tagged_tweet`, `replied_comments`, `post_status`) VALUES
(7, '1877705579054907581', '1877288764516741121', 'twitter bot tweet testing 2....\n\n@zaid_works515', 'Bot tweet auto replying test...', 'successful'),
(8, '1877331038600339635', '1877288764516741121', 'twitter bot tweet testing....\n\n@zaid_works515', 'Bot tweet auto replying test...', 'successful'),
(9, '1877708287006712004', '1877288764516741121', 'twitter bot tweet testing....\n\n@zaid_works515', 'Bot tweet auto replying test (will only reply to unanswered/uncommented ones..).', 'successful');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `tweet_record`
--
ALTER TABLE `tweet_record`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `tagged_tweet_id` (`tagged_tweet_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `tweet_record`
--
ALTER TABLE `tweet_record`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
