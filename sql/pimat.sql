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
         start_time TIME,
         stop_time TIME,
         enabled BIT
       );


