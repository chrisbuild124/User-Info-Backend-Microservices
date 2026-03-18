import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )

# =====================
# USERS
# =====================

def create_user(user):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (id, name, age, weight, height, gender, activity)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, user)

    conn.commit()
    cursor.close()
    conn.close()


def get_user(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()
    return result

# =====================
# CALORIES
# =====================

def add_calorie(user_id, date, food_name, calories):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO calories (user_id, date, food_name, calories)
        VALUES (%s, %s, %s, %s)
    """, (user_id, date, food_name, calories))

    conn.commit()
    cursor.close()
    conn.close()


def get_calories(user_id, date=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if date:
        cursor.execute("""
            SELECT * FROM calories WHERE user_id = %s AND date = %s
            ORDER BY date DESC
        """, (user_id, date))
    else:
        cursor.execute("""
            SELECT * FROM calories WHERE user_id = %s
            ORDER BY date DESC
        """, (user_id,))

    results = cursor.fetchall()

    cursor.close()
    conn.close()
    return results


def delete_calorie(entry_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM calories WHERE id = %s", (entry_id,))

    conn.commit()
    cursor.close()
    conn.close()