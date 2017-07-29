USE pimat;

CREATE TABLE pimat;

CREATE TABLE sensors (
         id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
         timestamp DATETIME,
         temperature1 FLOAT,
         temperature2 FLOAT,
         humidity FLOAT,
         light1 FLOAT,
         pressure FLOAT,
         altitude FLOAT,
         source VARCHAR(100)
       );

CREATE TABLE schedules (
         id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
         relay VARCHAR(10),
         switch VARCHAR(50),
         start_time VARCHAR(10),
         stop_time VARCHAR(10),
         enabled VARCHAR(10)
       );


CREATE TABLE users (
         id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
         first_name VARCHAR(100),
         last_name VARCHAR(100),
         username VARCHAR(80) UNIQUE,
         password VARCHAR(64),
         email VARCHAR(120)
       );