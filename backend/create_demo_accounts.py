from pymongo import MongoClient
from app.auth.security import hash_password
from datetime import datetime, UTC

client = MongoClient('mongodb+srv://shikshasetu9_db_user:gpp88E8A3tH72JMs@cluster0.ai984wg.mongodb.net')
db = client['shikshasetu']

role = db.roles.find_one({'status': 'active'}) or db.roles.find_one()
role_id = role['_id'] if role else None

accounts = [
    {
        'email': 'officer@shikshasetu.gov.in',
        'password': 'Password@123',
        'full_name': 'Rajesh Sharma',
        'designation': 'Statistical Officer',
        'department': 'Ministry of Statistics',
        'employee_id': 'GOV-SO-101',
        'access_role': 'OFFICIAL',
        'status': 'active'
    },
    {
        'email': 'trainer@shikshasetu.gov.in',
        'password': 'Password@123',
        'full_name': 'Dr. Ananya Verma',
        'designation': 'Senior Lead Trainer',
        'department': 'Capacity Building Commission',
        'employee_id': 'TRN-CBC-201',
        'access_role': 'TRAINER',
        'status': 'active'
    },
    {
        'email': 'admin@shikshasetu.gov.in',
        'password': 'Password@123',
        'full_name': 'System Administrator',
        'designation': 'Director (Admin & Governance)',
        'department': 'DoPT',
        'employee_id': 'ADM-DOPT-001',
        'access_role': 'ADMIN',
        'status': 'active'
    }
]

for a in accounts:
    pwd = a.pop('password')
    db.users.update_one(
        {'email': a['email']},
        {
            '$set': {
                **a,
                'password_hash': hash_password(pwd),
                'role_id': role_id,
                'updated_at': datetime.now(UTC),
                'created_at': datetime.now(UTC)
            }
        },
        upsert=True
    )
    print(f"Provisioned account: {a['email']} ({a['access_role']})")

print("All demo accounts provisioned successfully!")
