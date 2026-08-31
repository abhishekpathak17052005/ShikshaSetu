"""Check roles in database."""
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGODB_URI'))
db = client[os.getenv('MONGODB_DATABASE')]

roles = list(db.roles.find().limit(3))
for role in roles:
    print(f"Role ID: {role.get('_id')}")
    print(f"  Fields: {list(role.keys())}")
    print(f"  Content: {role}")
    print()
