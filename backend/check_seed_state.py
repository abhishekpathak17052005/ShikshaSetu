#!/usr/bin/env python3
from app.core.config import get_settings
from app.core.database import initialize_database

settings = get_settings()
client, database = initialize_database(settings.mongodb_uri, settings.mongodb_database)

count = database.assessment_configurations.count_documents({})
print(f'Assessment configurations in shikshasetu DB: {count}')

if count > 0:
    sample = list(database.assessment_configurations.find().limit(3))
    for s in sample:
        print(f'  - {s.get("competency_code")}')
else:
    print("  (none)")

client.close()
