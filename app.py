from fastapi import FastAPI, HTTPException
import redis
import mysql.connector
from mysql.connector import Error

app = FastAPI()

cache = redis.Redis(host="redis", port=6379, decode_responses=True)

def create_db_connection():
    try:
        connection = mysql.connector.connect(
            host="mysql",  
            user="root",
            password="root",
            database="test_db"
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def get_item_from_db(item_id):
    cached_item = cache.get(item_id)
    if cached_item:
        return eval(cached_item)  

    connection = create_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE id = %s", (item_id,))
        item = cursor.fetchone()
        connection.close()

       
        if item:
            cache.set(item_id, str(item), ex=60)  
        return item
    return None

def update_item_in_db(item_id, new_data):
    connection = create_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE products SET name = %s, price = %s WHERE id = %s",
            (new_data["name"], new_data["price"], item_id)
        )
        connection.commit()
        connection.close()

        cache.delete(item_id)
        return True
    return False

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    item = get_item_from_db(item_id)
    if item:
        return {"item": item}
    raise HTTPException(status_code=404, detail="Item not found")

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: dict):
    success = update_item_in_db(item_id, item)
    if success:
        return {"message": "Item updated successfully"}
    raise HTTPException(status_code=500, detail="Failed to update item")

@app.get("/items")
async def get_all_items():
    connection = create_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products")
        items = cursor.fetchall()
        connection.close()
        return {"items": items}
    raise HTTPException(status_code=500, detail="Failed to fetch items")
