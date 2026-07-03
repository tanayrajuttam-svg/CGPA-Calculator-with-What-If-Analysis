import mysql.connector
import os

def get_connection():
    return mysql.connector.connect(
        host=os.environ.get("MYSQLHOST", "localhost"),
        user=os.environ.get("MYSQLUSER", "root"),
        password=os.environ.get("MYSQLPASSWORD", "qwer1234"),
        database=os.environ.get("MYSQLDATABASE", "cgpa_db"),
        port=int(os.environ.get("MYSQLPORT", 3306))
    )
