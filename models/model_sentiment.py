from bson import ObjectId 
from db import mongo

class Sentiment:
    @staticmethod
    def create(usersub, ml_s1, ml_s2, total_score, s1_text, s2_text, s1_score, s2_score):
        sentiment = {
            "usersub": usersub,
            "ml_s1": ml_s1,
            "ml_s2": ml_s2,
            "s1": {"text": s1_text, "score": s1_score},
            "s2": {"text": s2_text, "score": s2_score},
            "total_score": total_score
        }
        return mongo.db.sentiment.insert_one(sentiment)

    @staticmethod
    def get(usersub):
        sentiment = mongo.db.sentiment.find_one({"usersub": usersub})
        return Sentiment.serialize(sentiment)

    @staticmethod
    def update(usersub, data):
        return mongo.db.sentiment.update_one({"usersub": usersub}, {"$set": data})

    @staticmethod
    def delete(usersub):
        return mongo.db.sentiment.delete_one({"usersub": usersub})

    @staticmethod
    def serialize(sentiment):
        if sentiment is not None:
            sentiment["_id"] = str(sentiment["_id"])
        return sentiment
