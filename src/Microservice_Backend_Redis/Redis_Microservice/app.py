from flask import Flask, jsonify, request
from cryptography.hazmat.primitives import serialization
import jwt
import redis
import os
from dotenv import load_dotenv
import datetime

# -----------------------------
# A backend microservice to update the Redis database.
# It also verifies the JWT token before retrieving information. 
# -----------------------------
PORT = 7002
REDIS_PORT = 6379
DEBUG_MODE = True
TIME_UNTIL_EXPIRED = 30 * 60 # Seconds until token is considered expired 30 minutes

load_dotenv()
PASSWORD = os.getenv("REDIS_DATABASE_PASSWORD")

app = Flask(__name__)
redis_app = redis.Redis(
    host="localhost", 
    port=REDIS_PORT, 
    password=PASSWORD,
    db=0,
    decode_responses=True
    )

# -----------------------------
# Routes
# -----------------------------
@app.route("/create_session")
def create_session():
    """
    Given the user logs in from Auth0 microservice, when the JWT token is received by the microservice:
     - Verify the JWT is a valid JWT token
        - If the user ID already exists:
            - Value 1 as the new JWT
            - Value 2 as the new expiration date
        - If it does not exist, create a record in the Redis JWT database that contains:
            - Key as the user ID
            - Value 1 as the JWT 
            - Value 2 as the session expiration date
    """
    # Grab token from request header
    token = request.headers.get("Authorization", None)

    # Verify the token
    verify_jwt_status = verify_user(token)
    response = verify_jwt_status[0]
    response_dict = response.get_json()
    if not response_dict.get("success"):
        return verify_jwt_status

    # Get user id
    user_info = response_dict.get("user_info")
    user_id = user_info.get("sub")

    # Check if user id exists in the REDIS database
    # - If it does, update the record
    # - Else, create a new record
    redis_app.hset(user_id, mapping={"JWT": token, "last_updated": datetime.datetime.now().isoformat()})
    res = jsonify(response_dict), 201
    return res

@app.route("/update_session")
def update_session():
    """
    Given the user is logged in, when the user moves to another page, then
    - Verify the JWT is a valid JWT by checking expiration and decoding
    - If the JWT is valid:
        - Verify session expiration date
            - Return 
        - Updated the expiration in the Redis database
        - Return the user ID associated with the JWT in the response, 200
    - Else:
        - Return an error response 400
    """
    # Grab token from request header
    token = request.headers.get("Authorization", None)

    # Verify the token
    verify_jwt_status = verify_user(token)
    response = verify_jwt_status[0]
    response_dict = response.get_json()
    if not response_dict.get("success"):
        return verify_jwt_status
    
    # Get user id
    user_info = response_dict.get("user_info")
    user_id = user_info.get("sub")

    # Verify session hasn't expired, sends error if session expired
    if is_session_expired(user_id):
        return jsonify({"success": False, "error": "Session expired"}), 401

    # Checks if the user is in the latest session, sends error if not in latest session
    if not is_user_in_latest_session(user_id, token):
        return jsonify({"success": False, "error": "Invalid session. Please log in again."}), 401

    # Adds to Redis database as refreshed
    redis_app.hset(user_id, mapping={"JWT": token, "last_updated": datetime.datetime.now().isoformat()})

    # Because the JWT is valid and the session is updated, 
    # return the user ID associated with the JWT in the response, 200
    return jsonify({
        "success": True,
        "message": f"Hello, {user_info.get('name')}! Your session is updated.",
        "user_id": user_id
    }), 200
    
@app.route("/delete_session")
def delete_session():
    """
    When the user logs out
        - Verify the JWT is a valid JWT token
        - If userId is in database:
            - Invalidate the user ID by removing the user ID from the database
        - Else:
            - Send error saying user already logged out
    """
    # Grab token from request header
    token = request.headers.get("Authorization", None)

    # Verify the token
    verify_jwt_status = verify_user(token)
    response = verify_jwt_status[0]
    response_dict = response.get_json()
    if not response_dict.get("success"):
        return verify_jwt_status
    
    # Get user id
    user_info = response_dict.get("user_info")
    user_id = user_info.get("sub")

    # Check if user id exists in the REDIS database
    if redis_app.exists(user_id) and is_user_in_latest_session(user_id, token):
        redis_app.delete(user_id)
        return jsonify({"success": True, "message": "Session deleted successfully"}), 200
    else:
        return jsonify({"success": False, "error": "User already logged out"}), 400

# -----------------------------
# HELPERS
# -----------------------------
def verify_user(token):
    """
    Verifies the user's JWT and expiration
    """
    if not token:
        return jsonify({"success": False, "error": "Authorization header missing"}), 401

    with open("public.pem", "rb") as f:
        public_key = serialization.load_pem_public_key(f.read())

    # decode JWT
    try:
        user_info = jwt.decode(token, public_key, algorithms=["RS256"])
        print("User info success")
    except jwt.ExpiredSignatureError:
        print("Expired JWT")
        return jsonify({"success": False, "error": "JWT expired"}), 401
    except jwt.InvalidTokenError:
        print("Invalid JWT")
        return jsonify({"success": False, "error": "Invalid JWT"}), 401

    # returns successful message
    return jsonify({
        "success": True,
        "message": f"Hello, {user_info.get('name')}! You are authenticated.",
        "user_info": user_info
    }), 200

def is_session_expired(user_id: str) -> bool:
    """
    Given the user_id exists in the database:
    - Checks if now - user_id.last_updated is > TIME_UNTIL_EXPIRED
    """
    last_updated_str = redis_app.hget(user_id, "last_updated")
    if not last_updated_str:
        return True
    
    last_updated = datetime.datetime.fromisoformat(last_updated_str)
    now = datetime.datetime.now()
    elapsed_time = (now - last_updated).total_seconds()
    return elapsed_time > TIME_UNTIL_EXPIRED

def is_user_in_latest_session(user_id: str, token: str) -> bool:
    """
    Given the user_id exists in the database:
    - Checks if the JWT in the database matches the JWT provided by the user
    """
    last_updated_JWT = redis_app.hget(user_id, "JWT")
    if not last_updated_JWT:
        return True
    
    return last_updated_JWT == token

if __name__ == "__main__":
    app.run(port=PORT, debug=DEBUG_MODE)