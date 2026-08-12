from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)

# JWT configuration
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
jwt = JWTManager(app)

# MySQL database connection
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# User model
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    current_plan = db.Column(db.String(50), default="Free")
    created_at = db.Column(db.DateTime, server_default=db.func.now())

# Plan model
class Plan(db.Model):
    __tablename__ = "plans"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    features = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

# Subscription model
class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey("plans.id"), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default="active")
# Home
@app.route("/")
def home():
    return "SaaS Backend is running!"


# Signup
@app.route("/signup", methods=["POST"])
def signup():

    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({
            "message": "Name, email and password are required"
        }), 400

    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        return jsonify({
            "message": "Email already registered"
        }), 409

    hashed_password = generate_password_hash(password)

    new_user = User(
        name=name,
        email=email,
        password=hashed_password,
        current_plan="Free"
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "User registered successfully",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "current_plan": new_user.current_plan
        }
    }), 201


# Login
@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "message": "Email and password are required"
        }), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({
            "message": "Invalid email or password"
        }), 401

    if not check_password_hash(user.password, password):
        return jsonify({
            "message": "Invalid email or password"
        }), 401

    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "current_plan": user.current_plan
        }
    }), 200


@app.route("/profile", methods=["GET"])
@jwt_required()
def profile():

    user_id = get_jwt_identity()

    user = User.query.get(int(user_id))

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "current_plan": user.current_plan
    }), 200

@app.route("/plans", methods=["GET"])
def get_plans():

    plans = Plan.query.all()

    result = []

    for plan in plans:
        result.append({
            "id": plan.id,
            "name": plan.name,
            "price": float(plan.price),
            "features": plan.features
        })

    return jsonify({
        "plans": result
    }), 200

from datetime import datetime, timedelta


@app.route("/subscribe", methods=["POST"])
@jwt_required()
def subscribe():

    user_id = get_jwt_identity()

    data = request.get_json()

    plan_id = data.get("plan_id")

    if not plan_id:
        return jsonify({
            "message": "plan_id is required"
        }), 400

    user = User.query.get(int(user_id))

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    plan = Plan.query.get(plan_id)

    if not plan:
        return jsonify({
            "message": "Plan not found"
        }), 404

    # Check for an existing active subscription
    existing_subscription = Subscription.query.filter_by(
        user_id=user.id,
        status="active"
    ).first()

    if existing_subscription:
        return jsonify({
            "message": "You already have an active subscription"
        }), 400

    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=30)

    new_subscription = Subscription(
        user_id=user.id,
        plan_id=plan.id,
        start_date=start_date,
        end_date=end_date,
        status="active"
    )

    db.session.add(new_subscription)

    user.current_plan = plan.name

    db.session.commit()

    return jsonify({
        "message": "Subscription created successfully",
        "subscription": {
            "id": new_subscription.id,
            "plan": plan.name,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "status": "active"
        }
    }), 201

@app.route("/subscription", methods=["GET"])
@jwt_required()
def get_subscription():

    user_id = get_jwt_identity()

    subscription = Subscription.query.filter_by(
        user_id=int(user_id),
        status="active"
    ).first()

    if not subscription:
        return jsonify({
            "message": "No active subscription found"
        }), 404

    plan = Plan.query.get(subscription.plan_id)

    return jsonify({
        "subscription": {
            "id": subscription.id,
            "plan": plan.name,
            "price": float(plan.price),
            "start_date": subscription.start_date.isoformat(),
            "end_date": subscription.end_date.isoformat()
            if subscription.end_date else None,
            "status": subscription.status
        }
    }), 200

@app.route("/subscription", methods=["PUT"])
@jwt_required()
def change_subscription():

    user_id = get_jwt_identity()

    data = request.get_json()
    new_plan_id = data.get("plan_id")

    if not new_plan_id:
        return jsonify({
            "message": "plan_id is required"
        }), 400

    user = User.query.get(int(user_id))

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    subscription = Subscription.query.filter_by(
        user_id=user.id,
        status="active"
    ).first()

    if not subscription:
        return jsonify({
            "message": "No active subscription found"
        }), 404

    new_plan = Plan.query.get(new_plan_id)

    if not new_plan:
        return jsonify({
            "message": "Plan not found"
        }), 404

    # Update subscription
    subscription.plan_id = new_plan.id

    # Update user's current plan
    user.current_plan = new_plan.name

    db.session.commit()

    return jsonify({
        "message": "Subscription updated successfully",
        "subscription": {
            "id": subscription.id,
            "plan": new_plan.name,
            "price": float(new_plan.price),
            "status": subscription.status
        }
    }), 200

@app.route("/subscription", methods=["DELETE"])
@jwt_required()
def cancel_subscription():

    user_id = get_jwt_identity()

    user = User.query.get(int(user_id))

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    subscription = Subscription.query.filter_by(
        user_id=user.id,
        status="active"
    ).first()

    if not subscription:
        return jsonify({
            "message": "No active subscription found"
        }), 404

    subscription.status = "cancelled"

    # Return the user to the Free plan
    user.current_plan = "Free"

    db.session.commit()

    return jsonify({
        "message": "Subscription cancelled successfully",
        "current_plan": user.current_plan,
        "status": subscription.status
    }), 200

@app.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard():

    user_id = get_jwt_identity()

    user = User.query.get(int(user_id))

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    return jsonify({
        "message": "Welcome to your dashboard",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "current_plan": user.current_plan
        }
    }), 200

@app.route("/premium-content", methods=["GET"])
@jwt_required()
def premium_content():

    user_id = get_jwt_identity()

    user = User.query.get(int(user_id))

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    if user.current_plan != "Premium":
        return jsonify({
            "message": "Premium subscription required"
        }), 403

    return jsonify({
        "message": "Welcome to Premium content!",
        "content": "This content is available only to Premium subscribers."
    }), 200

if __name__ == "__main__":
    app.run(debug=True)
