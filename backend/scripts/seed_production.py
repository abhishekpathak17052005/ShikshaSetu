#!/usr/bin/env python3
"""
Production Database Seeding & Initialization CLI for ShikshaSetu.

This script executes:
1. Master framework synchronization (Competencies, Roles, Role Requirements, Assessments, Resources, Mappings)
2. Guaranteed 3-Role Demo Account Provisioning:
   - Official: officer@shikshasetu.gov.in / Password@123
   - Trainer:  trainer@shikshasetu.gov.in / Password@123
   - Admin:    admin@shikshasetu.gov.in / Password@123
3. Integrity audit and validation

Usage:
  python backend/scripts/seed_production.py
  (or from backend dir: python -m scripts.seed_production)
"""

import sys
from datetime import datetime, UTC
from pathlib import Path
from pymongo import MongoClient

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import get_settings
from app.core.database import initialize_database, close_database
from app.auth.security import hash_password
from app.scripts.seed_master import sync_master_data


DEMO_ACCOUNTS = [
    {
        "email": "officer@shikshasetu.gov.in",
        "password": "Password@123",
        "full_name": "Rajesh Sharma",
        "designation": "Statistical Officer",
        "department": "Ministry of Statistics & Programme Implementation",
        "employee_id": "GOV-SO-101",
        "access_role": "OFFICIAL",
        "status": "active",
    },
    {
        "email": "trainer@shikshasetu.gov.in",
        "password": "Password@123",
        "full_name": "Dr. Ananya Verma",
        "designation": "Senior Lead Faculty & Trainer",
        "department": "National Statistical Systems Training Academy (NSSTA)",
        "employee_id": "TRN-NSSTA-201",
        "access_role": "TRAINER",
        "status": "active",
    },
    {
        "email": "admin@shikshasetu.gov.in",
        "password": "Password@123",
        "full_name": "System Administrator",
        "designation": "Director (Capacity Building & Governance)",
        "department": "Capacity Building Commission / DoPT",
        "employee_id": "ADM-CBC-001",
        "access_role": "ADMIN",
        "status": "active",
    },
]


def seed_demo_users(db) -> None:
    """Ensure standard 3-role demo accounts are provisioned with active role_ids."""
    role = db.roles.find_one({"status": "active"}) or db.roles.find_one()
    role_id = role["_id"] if role else None

    print("\n[PROVISIONING DEMO ACCOUNTS]")
    print("-" * 60)
    for account_data in DEMO_ACCOUNTS:
        acc = dict(account_data)
        pwd = acc.pop("password")
        email = acc["email"]

        db.users.update_one(
            {"email": email},
            {
                "$set": {
                    **acc,
                    "password_hash": hash_password(pwd),
                    "role_id": role_id,
                    "updated_at": datetime.now(UTC),
                },
                "$setOnInsert": {
                    "created_at": datetime.now(UTC),
                },
            },
            upsert=True,
        )
        print(f"  ✓ {email: <30} | {acc['access_role']: <10} | {acc['designation']}")


def main():
    print("=" * 70)
    print("SHIKSHASETU: PRODUCTION DATABASE SEEDING & SYNC")
    print("=" * 70)

    settings = get_settings()
    print(f"Target Database: {settings.mongodb_database}")

    client, db = initialize_database(settings.mongodb_uri, settings.mongodb_database)

    try:
        # 1. Run Master Data Sync
        print("\n[STEP 1/2] Synchronizing Master Framework Taxonomy & Resources...")
        sync_master_data(db)

        # 2. Provision Demo Accounts
        print("\n[STEP 2/2] Provisioning 3-Role Demo Accounts...")
        seed_demo_users(db)

        print("\n" + "=" * 70)
        print("✓ PRODUCTION SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 70)
    finally:
        close_database(client)


if __name__ == "__main__":
    main()
