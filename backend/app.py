# app.py
import os
import logging
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from models import db, User, Signal, SignalLot

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

from auth import generate_token, login_required, admin_required
from mailer import mail


load_dotenv()


def create_app():
    app = Flask(__name__)

    # ---------------- BASIC CONFIG ----------------
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev_secret")
    app.config["JWT_EXP_SECONDS"] = int(os.getenv("JWT_EXP_SECONDS", "86400"))

    # ---------------- DATABASE ----------------
# ---------------- DATABASE ----------------
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ---------------- MAIL ----------------
    app.config["MAIL_SERVER"] = os.getenv("SMTP_HOST")
    app.config["MAIL_PORT"] = int(os.getenv("SMTP_PORT", "587"))
    app.config["MAIL_USERNAME"] = os.getenv("SMTP_USER")
    app.config["MAIL_PASSWORD"] = os.getenv("SMTP_PASS")
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_FROM")

    # ---------------- INIT ----------------
    
    db.init_app(app)

    with app.app_context():
        db.create_all()

    mail.init_app(app)
    logging.basicConfig(level=logging.INFO)
  

    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "https://narii.netlify.app"
            ]
        }
    })

    # ---------------- HEALTH ----------------
    @app.get("/api/ping")
    def ping():
        return jsonify({"ok": True})

    # ---------------- REGISTER ----------------
    @app.post("/api/register")
    def register():
        data = request.get_json() or {}

        required = ["name", "surname", "email", "password"]
        if not all(k in data for k in required):
            return jsonify({"message": "Missing fields"}), 400

        if User.query.filter_by(email=data["email"]).first():
            return jsonify({"message": "Email already registered"}), 400

        user = User(
            name=data["name"],
            surname=data["surname"],
            email=data["email"],
            password_hash=generate_password_hash(data["password"]),
            approved=False,
            role="client"
        )

        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "Registered. Await admin approval"}), 201
    


    @app.post("/api/login")
    def login():
        data = request.get_json() or {}

        email = data.get("email")
        password = data.get("password")
        role = data.get("role")

        if not email or not password:
            return jsonify({"message": "Missing credentials"}), 400

        user = User.query.filter_by(email=email).first()

        if not user:
            return jsonify({"message": "Invalid credentials"}), 401

        if not check_password_hash(user.password_hash, password):
            return jsonify({"message": "Invalid credentials"}), 401

        # 🔐 ADMIN LOGIN
        if role == "admin":
            if user.role != "admin":
                return jsonify({"message": "Not an admin account"}), 403

            token = generate_token(user.id, "admin")
            return jsonify({
                "token": token,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": "admin"
                }
            }), 200

        # 👤 CLIENT LOGIN
        if not user.approved:
            return jsonify({"message": "Account pending approval"}), 403

        token = generate_token(user.id, "client")

        return jsonify({
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": "client",
                "plan": user.plan,
                "subscription_end": user.subscription_end.isoformat() if user.subscription_end else None
            }
        }), 200



    # ---------------- CURRENT USER ----------------
    @app.get("/api/me")
    @login_required
    def me():
        user = request.current_user
        return jsonify({
            "id": user.id,
            "email": user.email,
            "plan": user.plan,
            "subscription_end": user.subscription_end.isoformat() if user.subscription_end else None
        })

    # ---------------- SUBSCRIBE ----------------
    @app.post("/api/subscribe")
    @login_required
    def subscribe():
        user = request.current_user
        plan = request.json.get("plan")

        if not plan:
            return jsonify({"message": "Plan required"}), 400

        user.plan = plan
        user.subscription_start = datetime.utcnow()
        user.subscription_end = datetime.utcnow() + timedelta(days=30)

        db.session.commit()
        return jsonify({"message": "Subscribed"}), 200

    # ---------------- USER SIGNALS ----------------

    @app.get("/api/admin/signals")
    @admin_required
    def get_admin_signals():
        signals = Signal.query.order_by(Signal.created_at.desc()).all()

        return jsonify([
            {
                "id": s.id,
                "pair": s.pair,
                "entry": s.entry,
                "tp": s.tp,
                "sl": s.sl,
                "plan": s.plan
            }
            for s in signals
        ]), 200


    @app.get("/api/admin/signals/<int:id>")
    @admin_required
    def get_admin_signal(id):
            signal = Signal.query.get_or_404(id)

            return jsonify({
                "id": signal.id,
                "pair": signal.pair,
                "entry": signal.entry,
                "tp": signal.tp,
                "sl": signal.sl,
                "plan": signal.plan,
                "lots": [
                    {
                        "id": lot.id,
                        "lot_size": lot.lot_size,
                        "win_amount": lot.win_amount,
                        "loss_amount": lot.loss_amount
                    }
                    for lot in signal.lots
                ]
            }), 200
    # ================= ADMIN USERS =================
    @app.get("/api/admin/users/pending")
    @admin_required
    def pending_users():
        users = User.query.filter_by(approved=False, role="client").all()
        return jsonify([{
            "id": u.id,
            "name": u.name,
            "surname": u.surname,
            "email": u.email
        } for u in users]), 200

    @app.get("/api/admin/users/active")
    @admin_required
    def active_users():
        users = User.query.filter_by(approved=True, role="client").all()
        return jsonify([{
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "plan": u.plan,
            "expiry": u.subscription_end.isoformat() if u.subscription_end else None
        } for u in users]), 200

    @app.put("/api/admin/users/<int:user_id>/approve")
    @admin_required
    def approve_user(user_id):
        user = User.query.get_or_404(user_id)
        user.approved = True
        db.session.commit()
        return jsonify({"message": "Approved"}), 200

    @app.delete("/api/admin/users/<int:user_id>/reject")
    @admin_required
    def reject_user(user_id):
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "Rejected"}), 200

    # ================= ADMIN SIGNALS =================
    @app.put("/api/admin/signals/<int:id>")
    @admin_required
    def update_signal(id):
        signal = Signal.query.get_or_404(id)
        data = request.get_json() or {}

        # ---------------- UPDATE SIGNAL FIELDS ----------------
        allowed_fields = ["pair", "entry", "tp", "sl", "plan"]

        for field in allowed_fields:
            if field in data:
                setattr(signal, field, data[field])

        # ---------------- UPDATE LOT OPTIONS ----------------
        lots = data.get("lots")

        if lots is not None:
            if not isinstance(lots, list):
                return jsonify({"message": "Lots must be a list"}), 400

            if len(lots) < 1 or len(lots) > 3:
                return jsonify({"message": "You must provide 1–3 lot options"}), 400

            # Clear existing lots
            SignalLot.query.filter_by(signal_id=signal.id).delete()

            # Add new lots
            for lot in lots:
                required = ["lot_size", "win_amount", "loss_amount"]
                if not all(k in lot for k in required):
                    return jsonify({"message": "Invalid lot structure"}), 400

                new_lot = SignalLot(
                    signal_id=signal.id,
                    lot_size=float(lot["lot_size"]),
                    win_amount=float(lot["win_amount"]),
                    loss_amount=float(lot["loss_amount"]),
                )
                db.session.add(new_lot)

        db.session.commit()

        return jsonify({
            "message": "Signal updated successfully",
            "signal_id": signal.id
        }), 200

    @app.post("/api/admin/signals")
    @admin_required
    def create_signal():
        data = request.get_json() or {}

        required = ["pair", "entry", "tp", "sl", "plan"]
        if not all(k in data for k in required):
            return jsonify({"message": "Missing fields"}), 400

        signal = Signal(
            pair=data["pair"],
            entry=data["entry"],
            tp=data["tp"],
            sl=data["sl"],
            plan=data["plan"],
        )

        db.session.add(signal)
        db.session.flush()  # IMPORTANT — get signal.id before commit

        # ---------------- LOT SIZES ----------------
        lots = data.get("lots", [])

        if lots:
            if not isinstance(lots, list):
                return jsonify({"message": "Lots must be a list"}), 400

            if len(lots) > 3:
                return jsonify({"message": "Maximum 3 lot sizes allowed"}), 400

            for lot in lots:
                required_lot = ["lot_size", "win_amount", "loss_amount"]
                if not all(k in lot for k in required_lot):
                    return jsonify({"message": "Invalid lot structure"}), 400

                db.session.add(SignalLot(
                    signal_id=signal.id,
                    lot_size=float(lot["lot_size"]),
                    win_amount=float(lot["win_amount"]),
                    loss_amount=float(lot["loss_amount"])
                ))

        db.session.commit()

        return jsonify({"message": "Signal created", "id": signal.id}), 201

    @app.get("/api/signals")
    @login_required
    def client_signals():
        user = request.current_user

        signals = Signal.query.filter_by(plan=user.plan).order_by(Signal.created_at.desc()).all()

        return jsonify([
            {
                "id": s.id,
                "pair": s.pair,
                "entry": s.entry,
                "tp": s.tp,
                "sl": s.sl,
                "plan": s.plan,
                "lots": [
                    {
                        "lot_size": lot.lot_size,
                        "win_amount": lot.win_amount,
                        "loss_amount": lot.loss_amount
                    }
                    for lot in s.lots
                ]
            }
            for s in signals
        ])


    @app.delete("/api/admin/signals/<int:id>")
    @admin_required
    def delete_signal(id):
        signal = Signal.query.get_or_404(id)

        # IMPORTANT: delete lots first if relationship exists
        for lot in signal.lots:
            db.session.delete(lot)

        db.session.delete(signal)
        db.session.commit()

        return jsonify({"message": "Deleted"}), 200
    
    @app.put("/api/admin/users/<int:user_id>/deactivate")
    @admin_required
    def deactivate_user(user_id):
            user = User.query.get_or_404(user_id)

            user.is_active = False
            user.subscription_end = None
            user.plan = None

            db.session.commit()

            return jsonify({"message": "User deactivated"})

    return app


# ---------------- ADMIN BOOTSTRAP ----------------
def ensure_admin_user(app):
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")

    if not email or not password:
        return

    with app.app_context():
        admin = User.query.filter_by(email=email).first()
        hashed = generate_password_hash(password)

        if admin:
            admin.role = "admin"
            admin.approved = True
            admin.password_hash = hashed
        else:
            admin = User(
                name="Admin",
                surname="",
                email=email,
                password_hash=hashed,
                approved=True,
                role="admin"
            )
            db.session.add(admin)

        db.session.commit()



# ---------------- RUN ----------------

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

