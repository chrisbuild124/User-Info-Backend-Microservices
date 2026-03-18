-- ===============================
-- Schema: calorie_tracker
-- ===============================
CREATE DATABASE IF NOT EXISTS calorie_tracker;
USE calorie_tracker;

-- ===============================
-- Table: users
-- ID comes from Redis (no auto-increment)
-- ===============================
CREATE TABLE users (
    id INT PRIMARY KEY,            -- Matches Redis user ID
    name VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    weight FLOAT NOT NULL,
    height FLOAT NOT NULL,
    gender VARCHAR(10) NOT NULL,
    activity VARCHAR(50) NOT NULL
);

-- ===============================
-- Table: calories
-- Each entry belongs to a user
-- ===============================
CREATE TABLE calories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,          -- References users.id
    date DATE NOT NULL,
    food_name VARCHAR(100) NOT NULL,
    calories INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);