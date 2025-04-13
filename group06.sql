-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Feb 28, 2025 at 05:31 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `fixiit`
--

-- --------------------------------------------------------

--
-- Table structure for table `administrators`
--

CREATE TABLE `administrators` (
  `Admin_ID` int(11) NOT NULL,
  `Name` varchar(50) NOT NULL,
  `Email` varchar(100) NOT NULL,
  `Password_Hash` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `administrators`
--

INSERT INTO `administrators` (`Admin_ID`, `Name`, `Email`, `Password_Hash`) VALUES
(1, 'Admin One', 'admin1@iitgn.ac.in', 'hashedpassword1'),
(2, 'Admin Two', 'admin2@iitgn.ac.in', 'hashedpassword2');

-- --------------------------------------------------------

--
-- Table structure for table `feedback`
--

CREATE TABLE `feedback` (
  `Feedback_ID` int(11) NOT NULL,
  `Request_ID` int(11) NOT NULL,
  `Student_ID` int(11) NOT NULL,
  `Rating` int(11) DEFAULT NULL CHECK (`Rating` between 1 and 5),
  `Comments` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `feedback`
--

INSERT INTO `feedback` (`Feedback_ID`, `Request_ID`, `Student_ID`, `Rating`, `Comments`) VALUES
(4, 3, 22110292, 5, 'Quick service, very satisfied!'),
(5, 2, 22110057, 4, 'Took some time, but issue resolved.'),
(6, 1, 22110087, 3, 'Plumbing issue fixed, but took longer than expected.');

-- --------------------------------------------------------

--
-- Table structure for table `maintenance_logs`
--

CREATE TABLE `maintenance_logs` (
  `Log_ID` int(11) NOT NULL,
  `Request_ID` int(11) NOT NULL,
  `Technician_ID` int(11) NOT NULL,
  `Status_Update` text NOT NULL,
  `Updated_At` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `maintenance_logs`
--

INSERT INTO `maintenance_logs` (`Log_ID`, `Request_ID`, `Technician_ID`, `Status_Update`, `Updated_At`) VALUES
(1, 1, 2, 'Leak detected, fixing underway.', '2025-02-25 11:30:00'),
(2, 2, 3, 'Checked router, issue persists.', '2025-02-24 16:45:00'),
(3, 3, 1, 'Broken glass replaced.', '2025-02-23 12:00:00'),
(4, 4, 4, 'Socket repair in progress.', '2025-02-22 15:45:00');

-- --------------------------------------------------------

--
-- Table structure for table `maintenance_requests`
--

CREATE TABLE `maintenance_requests` (
  `Request_ID` int(11) NOT NULL,
  `Student_ID` int(11) NOT NULL,
  `Issue_Description` varchar(255) NOT NULL,
  `Location` varchar(100) NOT NULL,
  `Priority` enum('Low','Medium','High') NOT NULL DEFAULT 'Medium',
  `Submission_Date` datetime DEFAULT current_timestamp(),
  `Status` enum('submitted','in_progress','completed','rejected') NOT NULL DEFAULT 'submitted'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `maintenance_requests`
--

INSERT INTO `maintenance_requests` (`Request_ID`, `Student_ID`, `Issue_Description`, `Location`, `Priority`, `Submission_Date`, `Status`) VALUES
(1, 22110087, 'Leaking water pipe in hostel', 'Emiet, E 201', 'High', '2025-02-25 10:15:00', 'submitted'),
(2, 22110057, 'WiFi not working', 'Hiqom, H 202', 'Medium', '2025-02-24 15:30:00', 'in_progress'),
(3, 22110292, 'Broken window in classroom', 'Firpeal, F 203', 'High', '2025-02-23 09:45:00', 'completed'),
(4, 22110043, 'Electrical socket not working', 'Emiet, E 204', 'Low', '2025-02-22 14:20:00', 'submitted'),
(5, 22110072, 'AC not cooling properly', 'Hiqom, H 205', 'Medium', '2025-02-21 18:10:00', 'rejected');

-- --------------------------------------------------------

--
-- Table structure for table `notifications`
--

CREATE TABLE `notifications` (
  `Notification_ID` int(11) NOT NULL,
  `Student_ID` int(11) NOT NULL,
  `Message` text NOT NULL,
  `Sent_At` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `notifications`
--

INSERT INTO `notifications` (`Notification_ID`, `Student_ID`, `Message`, `Sent_At`) VALUES
(1, 22110087, 'Your maintenance request has been submitted.', '2025-02-25 10:16:00'),
(2, 22110057, 'A technician has been assigned to your WiFi issue.', '2025-02-24 16:05:00'),
(3, 22110292, 'Your broken window request has been completed.', '2025-02-23 12:15:00'),
(4, 22110043, 'Electrician assigned to fix your electrical socket.', '2025-02-22 15:10:00'),
(5, 22110072, 'Your AC request has been rejected.', '2025-02-21 18:20:00');

-- --------------------------------------------------------

--
-- Table structure for table `repair_categories`
--

CREATE TABLE `repair_categories` (
  `Category_ID` int(11) NOT NULL,
  `Category_Name` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `repair_categories`
--

INSERT INTO `repair_categories` (`Category_ID`, `Category_Name`) VALUES
(4, 'Carpentry'),
(2, 'Electrical'),
(5, 'HVAC'),
(3, 'Networking'),
(1, 'Plumbing');

-- --------------------------------------------------------

--
-- Table structure for table `students`
--

CREATE TABLE `students` (
  `Student_ID` int(11) NOT NULL,
  `Name` varchar(50) NOT NULL,
  `Email` varchar(100) NOT NULL,
  `Contact_Number` varchar(15) NOT NULL,
  `Age` int(11) DEFAULT NULL CHECK (`Age` >= 18),
  `Image` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `students`
--

INSERT INTO `students` (`Student_ID`, `Name`, `Email`, `Contact_Number`, `Age`, `Image`) VALUES
(22110043, 'Atharva Bodhale', 'atharva.bodhale@iitgn.ac.in', '9022508427', 20, 'Atharva.jpg'),
(22110057, 'Chandrabhan Patel', 'chandrabhan.patel@iitgn.ac.in', '6376471802', 21, 'Chandrabhan.jpg'),
(22110072, 'Dewansh Singh Chandel', 'dewanshsingh.chandel@iitgn.ac.in', '8085907445', 20, 'Dewansh.jpg'),
(22110087, 'Parth Govale', 'parth.govale@iitgn.ac.in', '9619869044', 20, 'Parth.jpg'),
(22110292, 'Vraj Shah', 'vraj.shah@iitgn.ac.in', '9484638348', 20, 'Vraj.jpg');

-- --------------------------------------------------------

--
-- Table structure for table `technicians`
--

CREATE TABLE `technicians` (
  `Technician_ID` int(11) NOT NULL,
  `Name` varchar(50) NOT NULL,
  `Email` varchar(100) NOT NULL,
  `Contact_Number` varchar(15) NOT NULL,
  `Specialization` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `technicians`
--

INSERT INTO `technicians` (`Technician_ID`, `Name`, `Email`, `Contact_Number`, `Specialization`) VALUES
(1, 'John Doe', 'john.technician@iitgn.ac.in', '8765432109', 'Plumbing'),
(2, 'Sarah Connor', 'sarah.technician@iitgn.ac.in', '8654321098', 'Electrical'),
(3, 'Mike Ross', 'mike.technician@iitgn.ac.in', '8543210987', 'Networking'),
(4, 'Anna White', 'anna.technician@iitgn.ac.in', '8432109876', 'Carpentry'),
(5, 'Robert Brown', 'robert.technician@iitgn.ac.in', '8321098765', 'HVAC');

-- --------------------------------------------------------

--
-- Table structure for table `technician_assignments`
--

CREATE TABLE `technician_assignments` (
  `Assignment_ID` int(11) NOT NULL,
  `Technician_ID` int(11) NOT NULL,
  `Request_ID` int(11) NOT NULL,
  `Assigned_Date` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `technician_assignments`
--

INSERT INTO `technician_assignments` (`Assignment_ID`, `Technician_ID`, `Request_ID`, `Assigned_Date`) VALUES
(1, 2, 1, '2025-02-25 11:05:00'),
(2, 3, 2, '2025-02-24 16:10:00'),
(3, 1, 3, '2025-02-23 10:05:00'),
(4, 4, 4, '2025-02-22 15:15:00');

-- --------------------------------------------------------

--
-- Table structure for table `work_orders`
--

CREATE TABLE `work_orders` (
  `Order_ID` int(11) NOT NULL,
  `Request_ID` int(11) NOT NULL,
  `Technician_ID` int(11) DEFAULT NULL,
  `Assigned_Date` datetime DEFAULT current_timestamp(),
  `Completion_Date` datetime DEFAULT NULL,
  `Remarks` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `work_orders`
--

INSERT INTO `work_orders` (`Order_ID`, `Request_ID`, `Technician_ID`, `Assigned_Date`, `Completion_Date`, `Remarks`) VALUES
(11, 1, 2, '2025-02-25 11:00:00', NULL, 'Assigned to plumber'),
(12, 2, 3, '2025-02-24 16:00:00', NULL, 'Network technician checking issue'),
(13, 3, 1, '2025-02-23 10:00:00', '2025-02-23 12:00:00', 'Glass replaced'),
(14, 4, 4, '2025-02-22 15:00:00', NULL, 'Electrician assigned'),
(15, 5, NULL, NULL, NULL, 'Request rejected due to duplicate entry');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `administrators`
--
ALTER TABLE `administrators`
  ADD PRIMARY KEY (`Admin_ID`),
  ADD UNIQUE KEY `Email` (`Email`);

--
-- Indexes for table `feedback`
--
ALTER TABLE `feedback`
  ADD PRIMARY KEY (`Feedback_ID`),
  ADD KEY `Request_ID` (`Request_ID`),
  ADD KEY `Student_ID` (`Student_ID`);

--
-- Indexes for table `maintenance_logs`
--
ALTER TABLE `maintenance_logs`
  ADD PRIMARY KEY (`Log_ID`),
  ADD KEY `Request_ID` (`Request_ID`),
  ADD KEY `Technician_ID` (`Technician_ID`);

--
-- Indexes for table `maintenance_requests`
--
ALTER TABLE `maintenance_requests`
  ADD PRIMARY KEY (`Request_ID`),
  ADD KEY `Student_ID` (`Student_ID`);

--
-- Indexes for table `notifications`
--
ALTER TABLE `notifications`
  ADD PRIMARY KEY (`Notification_ID`),
  ADD KEY `Student_ID` (`Student_ID`);

--
-- Indexes for table `repair_categories`
--
ALTER TABLE `repair_categories`
  ADD PRIMARY KEY (`Category_ID`),
  ADD UNIQUE KEY `Category_Name` (`Category_Name`);

--
-- Indexes for table `students`
--
ALTER TABLE `students`
  ADD PRIMARY KEY (`Student_ID`),
  ADD UNIQUE KEY `Email` (`Email`);

--
-- Indexes for table `technicians`
--
ALTER TABLE `technicians`
  ADD PRIMARY KEY (`Technician_ID`),
  ADD UNIQUE KEY `Email` (`Email`);

--
-- Indexes for table `technician_assignments`
--
ALTER TABLE `technician_assignments`
  ADD PRIMARY KEY (`Assignment_ID`),
  ADD KEY `Technician_ID` (`Technician_ID`),
  ADD KEY `Request_ID` (`Request_ID`);

--
-- Indexes for table `work_orders`
--
ALTER TABLE `work_orders`
  ADD PRIMARY KEY (`Order_ID`),
  ADD KEY `Request_ID` (`Request_ID`),
  ADD KEY `Technician_ID` (`Technician_ID`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `administrators`
--
ALTER TABLE `administrators`
  MODIFY `Admin_ID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `feedback`
--
ALTER TABLE `feedback`
  MODIFY `Feedback_ID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT for table `maintenance_logs`
--
ALTER TABLE `maintenance_logs`
  MODIFY `Log_ID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `maintenance_requests`
--
ALTER TABLE `maintenance_requests`
  MODIFY `Request_ID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `notifications`
--
ALTER TABLE `notifications`
  MODIFY `Notification_ID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `repair_categories`
--
ALTER TABLE `repair_categories`
  MODIFY `Category_ID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `students`
--
ALTER TABLE `students`
  MODIFY `Student_ID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=221100294;

--
-- AUTO_INCREMENT for table `technicians`
--
ALTER TABLE `technicians`
  MODIFY `Technician_ID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `technician_assignments`
--
ALTER TABLE `technician_assignments`
  MODIFY `Assignment_ID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `work_orders`
--
ALTER TABLE `work_orders`
  MODIFY `Order_ID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `feedback`
--
ALTER TABLE `feedback`
  ADD CONSTRAINT `feedback_ibfk_1` FOREIGN KEY (`Request_ID`) REFERENCES `maintenance_requests` (`Request_ID`) ON DELETE CASCADE,
  ADD CONSTRAINT `feedback_ibfk_2` FOREIGN KEY (`Student_ID`) REFERENCES `students` (`Student_ID`) ON DELETE CASCADE;

--
-- Constraints for table `maintenance_logs`
--
ALTER TABLE `maintenance_logs`
  ADD CONSTRAINT `maintenance_logs_ibfk_1` FOREIGN KEY (`Request_ID`) REFERENCES `maintenance_requests` (`Request_ID`) ON DELETE CASCADE,
  ADD CONSTRAINT `maintenance_logs_ibfk_2` FOREIGN KEY (`Technician_ID`) REFERENCES `technicians` (`Technician_ID`) ON DELETE CASCADE;

--
-- Constraints for table `maintenance_requests`
--
ALTER TABLE `maintenance_requests`
  ADD CONSTRAINT `maintenance_requests_ibfk_1` FOREIGN KEY (`Student_ID`) REFERENCES `students` (`Student_ID`) ON DELETE CASCADE;

--
-- Constraints for table `notifications`
--
ALTER TABLE `notifications`
  ADD CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`Student_ID`) REFERENCES `students` (`Student_ID`) ON DELETE CASCADE;

--
-- Constraints for table `technician_assignments`
--
ALTER TABLE `technician_assignments`
  ADD CONSTRAINT `technician_assignments_ibfk_1` FOREIGN KEY (`Technician_ID`) REFERENCES `technicians` (`Technician_ID`) ON DELETE CASCADE,
  ADD CONSTRAINT `technician_assignments_ibfk_2` FOREIGN KEY (`Request_ID`) REFERENCES `maintenance_requests` (`Request_ID`) ON DELETE CASCADE;

--
-- Constraints for table `work_orders`
--
ALTER TABLE `work_orders`
  ADD CONSTRAINT `work_orders_ibfk_1` FOREIGN KEY (`Request_ID`) REFERENCES `maintenance_requests` (`Request_ID`) ON DELETE CASCADE,
  ADD CONSTRAINT `work_orders_ibfk_2` FOREIGN KEY (`Technician_ID`) REFERENCES `technicians` (`Technician_ID`) ON DELETE SET NULL;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
