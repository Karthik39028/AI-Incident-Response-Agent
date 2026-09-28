from app.services.database import get_connection

connection = get_connection()

print("DATABASE CONNECTION SUCCESSFUL")

connection.close()