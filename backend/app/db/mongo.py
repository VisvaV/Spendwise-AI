import os
from pymongo import MongoClient
from pymongo.collection import Collection
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)

db = client.spendwise

def get_receipt_metadata_collection() -> Collection:
    return db.receipt_metadata

def get_activity_logs_collection() -> Collection:
    return db.activity_logs

def get_notifications_collection() -> Collection:
    return db.notifications
