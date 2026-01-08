# auth.py
import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from models import User
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

SECRET = os.getenv("SECRET_KEY", "dev_secret")
JWT_EXP = int(os.getenv("JWT_EXP_SECONDS", "86400"))


def generate_token(user_id, role):
    payload = {
        "id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXP)
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


def _get_token():
    auth = request.headers.get("Authorization")
    if not auth:
        return None
    if auth.startswith("Bearer "):
        return auth.split(" ", 1)[1]
    return auth


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _get_token()
        if not token:
            return jsonify({"message": "Missing token"}), 401

        try:
            data = jwt.decode(token, SECRET, algorithms=["HS256"])
            user = User.query.get(data["id"])
            if not user:
                return jsonify({"message": "User not found"}), 404

            request.current_user = user

        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401

        return fn(*args, **kwargs)
    return wrapper




def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            claims = get_jwt()

            if claims.get("role") != "admin":
                return jsonify({"message": "Admin access required"}), 401

            return fn(*args, **kwargs)

        except Exception:
            return jsonify({"message": "Invalid or missing token"}), 401

    return wrapper
