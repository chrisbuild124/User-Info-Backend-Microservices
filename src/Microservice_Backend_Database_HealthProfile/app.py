from flask import Flask, request, jsonify
from datetime import date
from db import *

app = Flask(__name__)
PORT = 7003

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:8000'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    return jsonify({}), 200

# =====================
# USERS
# =====================

@app.route('/create_user', methods=['POST'])
def create_user_route():
    data = request.json

    create_user((
        data['id'],  # Redis ID
        data['name'],
        data['age'],
        data['weight'],
        data['height'],
        data['gender'],
        data['activity']
    ))

    return jsonify({"success": True})


@app.route('/get_user', methods=['GET'])
def get_user_route():
    user_id = request.args.get('user_id')

    user = get_user(user_id)
    return jsonify(user)

# =====================
# CALORIES
# =====================

@app.route('/add_calorie', methods=['POST'])
def add_calorie():
    data = request.json

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO calories (user_id, date, food_name, calories) VALUES (%s, %s, %s, %s)",
        (data['user_id'], data['date'], data['food_name'], data['calories'])
    )

    conn.commit()
    new_id = cursor.lastrowid

    cursor.close()
    conn.close()

    return jsonify({"id": new_id})


@app.route('/get_calories', methods=['GET'])
def get_calories_route():
    user_id = request.args.get('user_id')
    date = request.args.get('date')

    data = get_calories(user_id, date)
    return jsonify(data)


@app.route('/delete_calorie/<int:id>', methods=['DELETE'])
def delete_calorie(id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM calories WHERE id=%s", (id,))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"success": True})


if __name__ == '__main__':
    app.run(debug=True, port=PORT)