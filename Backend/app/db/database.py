from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["wdud_db"]
incidents_collection = db["incidents"]