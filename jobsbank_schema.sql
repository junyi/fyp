-- phpMyAdmin SQL Dump
-- version 4.0.10deb1
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: May 25, 2015 at 12:57 AM
-- Server version: 5.5.43-0ubuntu0.14.04.1
-- PHP Version: 5.5.9-1ubuntu4.9

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `jobsbank`
--

-- --------------------------------------------------------

--
-- Table structure for table `assoc_job_employment_type`
--

CREATE TABLE IF NOT EXISTS `assoc_job_employment_type` (
  `jobId` varchar(20) NOT NULL,
  `empId` smallint(4) NOT NULL,
  PRIMARY KEY (`jobId`,`empId`),
  KEY `jobId` (`jobId`,`empId`),
  KEY `empId` (`empId`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `assoc_job_industry`
--

CREATE TABLE IF NOT EXISTS `assoc_job_industry` (
  `jobId` varchar(20) NOT NULL,
  `industryId` smallint(6) NOT NULL,
  PRIMARY KEY (`jobId`,`industryId`),
  KEY `jobId` (`jobId`,`industryId`),
  KEY `industryId` (`industryId`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `assoc_job_job_category`
--

CREATE TABLE IF NOT EXISTS `assoc_job_job_category` (
  `jobId` varchar(20) NOT NULL,
  `categoryId` smallint(6) NOT NULL,
  PRIMARY KEY (`jobId`,`categoryId`),
  KEY `jobId` (`jobId`,`categoryId`),
  KEY `categoryId` (`categoryId`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `assoc_job_location`
--

CREATE TABLE IF NOT EXISTS `assoc_job_location` (
  `jobId` varchar(20) NOT NULL,
  `locationId` smallint(6) NOT NULL,
  PRIMARY KEY (`jobId`,`locationId`),
  KEY `jobId` (`jobId`,`locationId`),
  KEY `locationId` (`locationId`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `employment_type`
--

CREATE TABLE IF NOT EXISTS `employment_type` (
  `empId` smallint(4) NOT NULL AUTO_INCREMENT,
  `type` tinytext CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`empId`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Table structure for table `industry`
--

CREATE TABLE IF NOT EXISTS `industry` (
  `industryId` smallint(9) NOT NULL AUTO_INCREMENT,
  `description` tinytext CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`industryId`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Table structure for table `job`
--

CREATE TABLE IF NOT EXISTS `job` (
  `jobId` varchar(20) NOT NULL,
  `title` text CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `description` text CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `requirements` text CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `postingDate` date NOT NULL,
  `closingDate` date NOT NULL,
  `lastUpdated` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00' ON UPDATE CURRENT_TIMESTAMP,
  `url` text NOT NULL,
  `salary` tinytext CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `shiftPattern` tinytext CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `workingHours` tinytext CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `noOfVacancies` tinyint(4) NOT NULL,
  `yearsOfExp` tinytext CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`jobId`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `job_category`
--

CREATE TABLE IF NOT EXISTS `job_category` (
  `categoryId` smallint(6) NOT NULL AUTO_INCREMENT,
  `category` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`categoryId`),
  KEY `category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Table structure for table `location`
--

CREATE TABLE IF NOT EXISTS `location` (
  `locationId` smallint(6) NOT NULL AUTO_INCREMENT,
  `description` tinytext CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`locationId`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `assoc_job_employment_type`
--
ALTER TABLE `assoc_job_employment_type`
  ADD CONSTRAINT `assoc_job_employment_type_ibfk_2` FOREIGN KEY (`empId`) REFERENCES `employment_type` (`empId`) ON UPDATE CASCADE,
  ADD CONSTRAINT `assoc_job_employment_type_ibfk_1` FOREIGN KEY (`jobId`) REFERENCES `job` (`jobId`) ON UPDATE CASCADE;

--
-- Constraints for table `assoc_job_industry`
--
ALTER TABLE `assoc_job_industry`
  ADD CONSTRAINT `assoc_job_industry_ibfk_2` FOREIGN KEY (`industryId`) REFERENCES `industry` (`industryId`) ON UPDATE CASCADE,
  ADD CONSTRAINT `assoc_job_industry_ibfk_1` FOREIGN KEY (`jobId`) REFERENCES `job` (`jobId`) ON UPDATE CASCADE;

--
-- Constraints for table `assoc_job_job_category`
--
ALTER TABLE `assoc_job_job_category`
  ADD CONSTRAINT `assoc_job_job_category_ibfk_3` FOREIGN KEY (`categoryId`) REFERENCES `job_category` (`categoryId`) ON UPDATE CASCADE,
  ADD CONSTRAINT `assoc_job_job_category_ibfk_2` FOREIGN KEY (`jobId`) REFERENCES `job` (`jobId`) ON UPDATE CASCADE;

--
-- Constraints for table `assoc_job_location`
--
ALTER TABLE `assoc_job_location`
  ADD CONSTRAINT `assoc_job_location_ibfk_2` FOREIGN KEY (`locationId`) REFERENCES `location` (`locationId`) ON UPDATE CASCADE,
  ADD CONSTRAINT `assoc_job_location_ibfk_1` FOREIGN KEY (`jobId`) REFERENCES `job` (`jobId`) ON UPDATE CASCADE;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
