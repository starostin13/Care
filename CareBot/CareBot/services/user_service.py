# services/user_service.py
from utils.database import execute_query  # Adjust as needed to import your database functions

async def set_user_name(user_id, name):
    # Prepare the SQL query and parameters
    query = "UPDATE warmasters SET nickname = ? WHERE telegram_id = ?"
    params = (name, user_id)
    
    # Use execute_query to interact with the database
    await execute_query(query, params)
