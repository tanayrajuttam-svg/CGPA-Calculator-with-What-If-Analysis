import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="qwer1234",
        database="cgpa_db"
    )