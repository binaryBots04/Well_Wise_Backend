from db import mongo
from bson.objectid import ObjectId

class OpenCV:
    @staticmethod
    def create(userID, happy, sad, fear, angry, surprise, disgust):
        opencv = {
            "userID": userID,
            "happy": happy,
            "sad": sad,
            "fear": fear,
            "angry": angry,
            "surprise": surprise,
            "disgust": disgust
        }
        mongo.db.opencv.insert_one(opencv)
        return opencv

    @staticmethod
    def get(userID):
        opencv_data = mongo.db.opencv.find_one({"userID": userID})
        return OpenCV.serialize(opencv_data)

    @staticmethod
    def update(userID, data):
        mongo.db.opencv.update_one({"userID": userID}, {"$set": data})
        return OpenCV.get(userID)

    @staticmethod
    def delete(userID):
        return mongo.db.opencv.delete_one({"userID": userID})

    @staticmethod
    def serialize(opencv_data):
        """Converts MongoDB document to a JSON-serializable dictionary."""
        if opencv_data is not None:
            opencv_data["_id"] = str(opencv_data["_id"])  # Convert ObjectId to string
        return opencv_data
