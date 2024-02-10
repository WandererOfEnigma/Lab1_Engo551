# Project 1

ENGO 551

How to run the application: 
Phyton 3.6 or higher needs to be installed 
Postgres SQL 16 needs to be installed 

Open terminal and on the terminal line copy paste your project path to the space after for example: cd [project path]

Set your database URL export DATABASE_URL='postgresql://ownername:yourpostgrespassword@localhost:5434/yourdatabasename'

ownername name = name of owner of your database 
yourpostgrespassword = password you used to connect to the postgres server
yourdatabasename = name of database viewed on pgadmin 4 

After url set enter echo $DATABASE_URL to check if its set correctly or not 

Type python3 import.py to import books into your database

Type python3 application.py to run application 

Copy and paste URL into browser to open web application 