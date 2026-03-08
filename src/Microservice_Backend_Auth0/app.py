from flask import Flask, make_response, jsonify, redirect, request
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
from datetime import timezone
import os
import requests
import jwt
import datetime

# -----------------------------
# A backend microservice to authenticate users with Auth0 and
# generate JWT tokens for frontend applications (CLI and Web)
# -----------------------------

PORT = 7001
DEBUG_MODE = True

app = Flask(__name__)
load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH_URL = f"https://{AUTH0_DOMAIN}/authorize"
TOKEN_URL = f"https://{AUTH0_DOMAIN}/oauth/token"
USERINFO_URL = f"https://{AUTH0_DOMAIN}/userinfo"
REDIS_MICROSERVICE_DOMAIN = os.getenv("REDIS_MICROSERVICE_DOMAIN")
CALLBACK_URL = os.getenv("CALLBACK_URL")
CLIENT_ID = os.getenv("CLIENT_ID") 
CLIENT_SECRET = os.getenv("CLIENT_SECRET") 

# App specific
FRONTEND_URL = os.getenv("FRONTEND_URL")

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def home():
    return "Auth0 Microservice Running"

@app.route("/login")
def login():
    """
    Redirects to Auth0 URL page for that specific client type
    """
    client_app = request.args.get("app-type", "invalid_entry") # URL parameters
    auth_request = create_authentication_request_for_target_app(client_app)
    return redirect(auth_request.url) # Redirect user to Auth0 login page

@app.route("/callback")
def callback():
    """
    'code' is unique 1 time code and provides access to exchange for token to auth0
        - Exchanged for access token
    Backend uses access token to retrieve user info
    Generates JWT token using user info & private key, sends to client
    """
    code = request.args.get("code", None)
    client_app = request.args.get("state", None)  # defined in login request parameters
    if not code:
        return jsonify({"success": False, "error": "No code returned"}), 400
    
    token_object = exchange_code_for_token(code)
    if not token_object["success"]:
        return token_object["error"]

    user_info = exchange_token_for_user_info(token_object["access_token"])
    if not user_info["success"]:
        return user_info["error"]

    private_jwt = create_private_jwt(user_info)
    return handle_redis_based_on_app(client_app, private_jwt)

# -----------------------------
# HELPERS
# -----------------------------

def create_authentication_request_for_target_app(client_app):
    """
    Sends request to Auth0 service to get the url for the user
    """
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": CALLBACK_URL, # Must match the callback URL client
        "scope": "openid profile email", # Tells what parameters we want back from Auth0
        "state": client_app, # Sent directly back in callback
        "prompt": "select_account"
    }
    auth_request = requests.Request("GET", AUTH_URL, params=params).prepare()
    return auth_request

def exchange_code_for_token(code):
    """
    Exchanges an authorization code for an access token
    Returns Python Dictionary
    """
    res = send_request_for_token_and_get_response(code)
    if res.status_code not in (200, 201, 204):
        return {"success": False, "error": f"Token exchange failed, status code: {res.status_code}"}
    
    access_token = get_access_token_from_response(res)
    if not isinstance(access_token, str): # looks if the token isn't a string, which means it's an error json
        return access_token

    return {"success": True, "access_token": access_token}

def send_request_for_token_and_get_response(code):
    """
    Returns response after POST with code to get the user token
    """
    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": CALLBACK_URL,
        "scope": "openid profile email"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    return requests.post(TOKEN_URL, data=data, headers=headers)

def get_access_token_from_response(response):
    """
    Takes response from code request for token and returns the token
    If the token isn't in the response, returns error json
    """
    tokens = response.json()
    access_token = tokens.get("access_token", None)
    if not access_token:
        return {"success": False, "error": "Invalid token response from Auth0"}
    return access_token

def exchange_token_for_user_info(access_token):
    """
    Exchanges an access token for user info from Auth0 using /userinfo
    Returns Python dictionary
    """
    headers = {"Authorization": f"Bearer {access_token}"} # Bearer is Auth 2.0 protocol standard
    res = requests.get(USERINFO_URL, headers=headers)
    if res.status_code not in (200, 201, 204):
        return {"success": False, "error": f"Failed to fetch user info, status code: {res.status_code}"}
    
    response = res.json()
    response["success"] = True
    return response

def handle_redis_based_on_app(client_app, jw_token):      
    """
    Depending on the client app, sends the JWT token to Redis microservice and then renders the appropriate response for the client
     - For CLI: Render JWT token in a webpage for user to copy and paste into CLI
     - For Flask: Set JWT token in cookie and redirect to frontend URL
     - For unknown client app: Return error JSON
    """
    if client_app not in ("CLI", "Flask"):
        return jsonify({"success": False, "error": "Unknown client app"}), 400
    
    res = send_redis_token(jw_token)
    if not res.json().get("success"):
        return res
    
    if client_app == "CLI":
        return handle_jwt_CLI(jw_token)
    elif client_app == "Flask":
        return handle_jwt_flask(jw_token) 

def handle_jwt_CLI(token):
    """
    Render the JWT token to give to the front end CLI app
    """
    return f"""
    <html>
        <body>
            <h1>CLI JWT</h1>
            <p>Copy this token into your CLI:</p>
            <textarea style="width:100%;height:200px;">{token}</textarea>
        </body>
    </html>
    """

def handle_jwt_flask(token):
    """
    Render front end URL page with JWT token inside cookie
    """
    response = make_response(redirect(FRONTEND_URL))
    response.set_cookie(
        "jwt_calorie_counter_profile", 
        token, 
        httponly=True, 
        secure=False  # secure=True in production (HTTPS)
    )
    return response

def create_private_jwt(user_info, expires_minutes=10):
    """
    Creates a signed JWT with user info using RS256 (private/public key)
    """
    with open("private.pem", "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    payload = {
        "sub": user_info["sub"],
        "email": user_info.get("email", None),
        "name": user_info.get("name", None),
        "exp": datetime.datetime.now(tz=timezone.utc) + datetime.timedelta(minutes=expires_minutes)
    }
    token = jwt.encode(payload, private_key, algorithm="RS256")
    return token

def send_redis_token(token):
    """
    Receives token, sends Redis_Microservice the token to add to database
    - Send GET request with token to the REDIS_MICROSERVCE_DOMAIN/create_session
        - Request header should have an "Authorization": JWT str
    - Response should be a success 200 if it worked, error 400 if it failed
    """
    headers = {"Authorization": token}
    res = requests.get(REDIS_MICROSERVICE_DOMAIN + '/create_session', headers=headers)
    return res
    
# Initialize application
if __name__ == "__main__":
    app.run(port=PORT, debug=DEBUG_MODE)
