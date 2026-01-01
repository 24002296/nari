import hashlib
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from models import db, User
from auth import login_required
import os

payments = Blueprint("payments", __name__)

PLAN_PRICES = {
    "Basic": 2000,
    "Standard": 3500,
    "Premium": 5000
}

@payments.route("/api/pay/ozow", methods=["POST"])
@login_required
def create_ozow_payment(current_user):

    data = request.json
    plan = data.get("plan")

    if plan not in PLAN_PRICES:
        return jsonify({"message": "Invalid plan"}), 400

    amount = PLAN_PRICES[plan]

    transaction_ref = f"NARI-{current_user.id}-{int(datetime.utcnow().timestamp())}"

    hash_string = (
        os.getenv("OZOW_SITE_CODE") +
        os.getenv("OZOW_API_KEY") +
        transaction_ref +
        str(amount) +
        os.getenv("OZOW_PRIVATE_KEY")
    )

    hash_check = hashlib.sha512(hash_string.encode()).hexdigest().lower()

    return jsonify({
        "redirectUrl": os.getenv("OZOW_BASE_URL"),
        "SiteCode": os.getenv("OZOW_SITE_CODE"),
        "Amount": amount,
        "TransactionReference": transaction_ref,
        "HashCheck": hash_check,
        "Plan": plan
    })
@payments.route("/api/pay/ozow/callback", methods=["POST"])
def ozow_callback():
    data = request.form

    status = data.get("Status")
    transaction_ref = data.get("TransactionReference")
    amount = float(data.get("Amount"))

    if status != "Complete":
        return "FAILED", 400

    user_id = int(transaction_ref.split("-")[1])
    user = User.query.get(user_id)

    if not user:
        return "USER NOT FOUND", 404

    plan = (
        "Basic" if amount == 2000 else
        "Standard" if amount == 3500 else
        "Premium"
    )

    user.subscription_plan = plan
    user.subscription_active = True
    user.subscription_start = datetime.utcnow()
    user.subscription_end = datetime.utcnow() + timedelta(days=30)

    db.session.commit()

    return "OK", 200
