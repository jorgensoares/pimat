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

