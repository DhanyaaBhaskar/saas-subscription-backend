# SaaS Subscription Backend

A Flask-based SaaS subscription backend with JWT authentication and subscription management.

## Features

- User signup and login
- Password hashing
- JWT authentication
- User profile
- Dashboard
- Free, Basic and Premium plans
- Create subscription
- View subscription
- Upgrade and downgrade subscription
- Cancel subscription
- Premium-only content
- MySQL database

## Technologies

- Python
- Flask
- MySQL
- Flask-SQLAlchemy
- Flask-JWT-Extended
- PyMySQL
- python-dotenv

## API Endpoints

| Method | Endpoint | Authentication |
|---|---|---|
| POST | /signup | No |
| POST | /login | No |
| GET | /plans | No |
| GET | /profile | JWT |
| GET | /dashboard | JWT |
| POST | /subscribe | JWT |
| GET | /subscription | JWT |
| PUT | /subscription | JWT |
| DELETE | /subscription | JWT |
| GET | /premium-content | JWT |

## How to Run

Install the required packages:

```bash
pip install -r requirements.txt