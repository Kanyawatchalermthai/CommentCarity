-- สร้างฐานข้อมูล
CREATE DATABASE IF NOT EXISTS comment_clarity_schema;

-- ใช้งานฐานข้อมูลที่สร้างขึ้น
USE comment_clarity_schema;

-- Create Administrator table
CREATE TABLE Users (
    userId INT PRIMARY KEY AUTO_INCREMENT,
    firstName VARCHAR(50) NOT NULL,
    lastName VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Products table
CREATE TABLE Products (
    productId INT PRIMARY KEY AUTO_INCREMENT,
    productName VARCHAR(100) NOT NULL,
startDate VARCHAR(7) NOT NULL,
    endDate VARCHAR(7) NOT NULL,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE UserProducts (
    userProductId INT PRIMARY KEY AUTO_INCREMENT,
    userId INT NOT NULL,
    productId INT NOT NULL,
    isCreator BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (userId) REFERENCES Users(userId) ON DELETE CASCADE,
    FOREIGN KEY (productId) REFERENCES Products(productId) ON DELETE CASCADE
);

-- Create SentimentAnalysis table

CREATE TABLE SentimentAnalysis (
    sentimentId INT PRIMARY KEY AUTO_INCREMENT,
    sentimentType ENUM('Positive', 'Negative', 'Neutral','None') NOT NULL
);

-- Create CommentCategory table
CREATE TABLE CommentCategory (
    commentCategoryId INT PRIMARY KEY AUTO_INCREMENT,
    commentCategoryName ENUM('Product', 'Delivery','Service','Other') NOT NULL
);

-- Create Keywords table
CREATE TABLE Keywords (
    keywordId INT PRIMARY KEY AUTO_INCREMENT,
    keywordText VARCHAR(50) NOT NULL
);

-- Create Comments table with foreign keys
CREATE TABLE Comments (
    commentId INT PRIMARY KEY AUTO_INCREMENT,
    ratings INT NOT NULL CHECK (ratings BETWEEN 1 AND 5),
    text VARCHAR(1000) NOT NULL,  -- ใช้ VARCHAR สำหรับข้อความ
    date DATE DEFAULT (CURRENT_TIMESTAMP),  -- ใช้ CURRENT_TIMESTAMP แต่เก็บแค่วันที่
    sentimentId INT,
    userId INT,
    productId INT,
    commentCategoryId INT,
    FOREIGN KEY (sentimentId) REFERENCES SentimentAnalysis(sentimentId),
    FOREIGN KEY (userId) REFERENCES Users(userId),
    FOREIGN KEY (productId) REFERENCES Products(productId),
    FOREIGN KEY (commentCategoryId) REFERENCES CommentCategory(commentCategoryId)
);

-- Create Comment-Keyword mapping table (many-to-many relationship)
CREATE TABLE Comment_Keyword_Mapping (
    ck_mapId INT PRIMARY KEY AUTO_INCREMENT,
    commentId INT,
    keywordId INT,
    FOREIGN KEY (commentId) REFERENCES Comments(commentId),
    FOREIGN KEY (keywordId) REFERENCES Keywords(keywordId)
);

-- Add indexes for better performance
CREATE INDEX idx_comments_sentiment ON Comments(sentimentId);
CREATE INDEX idx_comments_product ON Comments(productId);
CREATE INDEX idx_comments_category ON Comments(commentCategoryId);
CREATE INDEX idx_comment_keyword ON Comment_Keyword_Mapping(commentId, keywordId);