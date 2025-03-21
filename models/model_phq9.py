from db import mongo
from bson.objectid import ObjectId

class PHQ9:
    @staticmethod
    def create(usersub, responses, total_score, phq1, phq2, phq3, phq4, phq5, phq6, phq7, phq8, phq9):
        phq_9 = {
            "usersub": usersub,
            "responses": responses,
            "phq9_score": total_score,
            "phq1" : phq1,
            "phq2" : phq2,
            "phq3" : phq3,
            "phq4" : phq4,
            "phq5" : phq5,
            "phq6" : phq6,
            "phq7" : phq7,
            "phq8" : phq8,
            "phq9" : phq9
        }
        mongo.db.phq_9.insert_one(phq_9)
        return phq_9

    @staticmethod
    def get(usersub):
        phq_data = mongo.db.phq_9.find_one({"usersub": usersub})
        return PHQ9.serialize(phq_data)

    @staticmethod
    def update(usersub, data):
        mongo.db.phq_9.update_one({"usersub": usersub}, {"$set": data})
        return PHQ9.get(usersub)

    @staticmethod
    def delete(usersub):
        return mongo.db.phq_9.delete_one({"usersub": usersub})

    @staticmethod
    def serialize(phq_data):
        """Converts MongoDB document to a JSON-serializable dictionary."""
        if phq_data is not None:
            phq_data["_id"] = str(phq_data["_id"])  # Convert ObjectId to string
        return phq_data
