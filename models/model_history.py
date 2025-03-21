from db import mongo
from bson.objectid import ObjectId

class History:
    @staticmethod
    def create(usersub, overall_score, q1, q2, q3, q4, q5):
        history = {
            "usersub": usersub,
            "history_score": overall_score,
            "q1": q1,
            "q2": q2,
            "q3": q3,
            "q4": q4,
            "q5": q5
        }
        mongo.db.history.insert_one(history)
        return history

    @staticmethod
    def get(usersub):
        history = mongo.db.history.find_one({"usersub": usersub})
        return History.serialize(history)

    @staticmethod
    def update(usersub, data):
        mongo.db.history.update_one({"usersub": usersub}, {"$set": data})
        return History.get(usersub)

    @staticmethod
    def delete(usersub):
        return mongo.db.history.delete_one({"usersub": usersub})

    @staticmethod
    def serialize(history_data):
        if history_data is not None:
            history_data["_id"] = str(history_data["_id"]) 
        return history_data
