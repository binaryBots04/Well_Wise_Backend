from db import mongo
from bson.objectid import ObjectId

class UserData:
    @staticmethod
    def create(usersub, name, age, gender, mental_health_score):
        user = {
            "usersub": usersub,
            "name": name,
            "age": age,
            "gender": gender,
            "mental_health_score": mental_health_score
        }
        mongo.db.users.insert_one(user)
        return user

    @staticmethod
    def get(usersub):
        user_data = mongo.db.users.find_one({"usersub": usersub})
        return UserData.serialize(user_data)

    @staticmethod
    def update(usersub, data):
        mongo.db.users.update_one({"usersub": usersub}, {"$set": data})
        return UserData.get(usersub)

    @staticmethod
    def delete(usersub):
        return mongo.db.users.delete_one({"usersub": usersub})

    @staticmethod
    def serialize(user_data):
        if user_data is not None:
            user_data["_id"] = str(user_data["_id"])
        return user_data
