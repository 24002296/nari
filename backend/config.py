# config.py
class Config:
    SECRET_KEY = "dev_secret"

    SQLALCHEMY_DATABASE_URI = (
    "mysql+pymysql://root:B%40rlin%2312%24%26@127.0.0.1:3306/nari"
)

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = "jwt_secret"
