#!/usr/bin/env python
"""Get test user credentials."""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv('MONGODB_URI')
db_name = os.getenv('MONGODB_DATABASE')

client = MongoClient(uri)
db = client[db_name]

# Get first user
user = db.users.find_one()
if user:
    print(f'Email: {user.get("email")}')
    print(f'Full Name: {user.get("full_name")}')
    print(f'Role: {user.get("role_id")}')
    print(f'Status: {user.get("status")}')
else:
    print('No users found in database')
    print('Please register a user first via API or UI')
