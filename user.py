from flask_login import UserMixin
from db import get_db

class User(UserMixin):
    def __init__(self, id_, name, email, profile_pic):
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic

    @staticmethod
    def get(user_id):
        db = get_db()
        user_data = db.users.find_one({"_id": user_id})
        if not user_data:
            return None

        user = User(
            id_=user_data["_id"], name=user_data["name"], 
            email=user_data["email"], profile_pic=user_data["profile_pic"]
        )
        return user

    @staticmethod
    def create(id_, name, email, profile_pic):
        db = get_db()
        db.users.insert_one({
            "_id": id_, "name": name, 
            "email": email, "profile_pic": profile_pic
        })

    @staticmethod
    def update(id_, name, email, profile_pic):
        db = get_db()
        db.users.update_one({
            "_id": id_, "name": name, 
            "email": email, "profile_pic": profile_pic
        })

    @staticmethod
    def delete(user_id):
        db = get_db()
        db.users.delete_one({"_id": user_id})
