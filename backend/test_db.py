from db import get_db_connection


try:
    connection = get_db_connection()
    print("DATABASE CONNECTION SUCCESSFUL!")

    cursor = connection.cursor()
    cursor.execute("SELECT current_database();")
    result = cursor.fetchone()

    print("Connected database:", result[0])

    cursor.close()
    connection.close()

except Exception as e:
    print("DATABASE CONNECTION FAILED!")
    print("Error:", e)