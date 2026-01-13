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
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import secrets
from werkzeug.security import generate_password_hash
from mailer import send_email
from models import User, db
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



auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.json
    email = data.get("email")

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"message": "If email exists, a reset link was sent"}), 200

    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expiry = datetime.utcnow() + timedelta(minutes=30)

    db.session.commit()

    reset_link = f"https://yourfrontend.com/reset-password.html?token={token}"

    send_email(
        to=email,
        subject="Password Reset",
        body=f"""
Hello,

Click the link below to reset your password.
This link expires in 30 minutes.

{reset_link}

If you did not request this, ignore this email.
"""
    )

    return jsonify({"message": "Reset link sent"}), 200

@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.json
    token = data.get("token")
    new_password = data.get("password")

    user = User.query.filter_by(reset_token=token).first()

    if not user or user.reset_token_expiry < datetime.utcnow():
        return jsonify({"message": "Invalid or expired token"}), 400

    user.password = generate_password_hash(new_password)
    user.reset_token = None
    user.reset_token_expiry = None

    db.session.commit()

    return jsonify({"message": "Password reset successful"}), 200


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
