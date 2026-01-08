from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    surname = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    approved = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default="client")
    
    is_active = db.Column(db.Boolean, default=True)
    subscription_start = db.Column(db.DateTime)
    subscription_end = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Signal(db.Model):
    __tablename__ = "signals"

    id = db.Column(db.Integer, primary_key=True)
    pair = db.Column(db.String(120), nullable=False)
    entry = db.Column(db.String(120), nullable=False)
    tp = db.Column(db.String(120), nullable=False)
    sl = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    lots = db.relationship(
        "SignalLot",
        backref="signal",
        cascade="all, delete-orphan"
    )


class SignalLot(db.Model):
    __tablename__ = "signal_lots"

    id = db.Column(db.Integer, primary_key=True)
    signal_id = db.Column(
        db.Integer,
        db.ForeignKey("signals.id"),
        nullable=False
    )

    lot_size = db.Column(db.Float, nullable=False)
    win_amount = db.Column(db.Float, nullable=False)
    loss_amount = db.Column(db.Float, nullable=False)

