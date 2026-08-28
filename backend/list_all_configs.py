#!/usr/bin/env python3
from app.core.config import get_settings
from app.core.database import initialize_database

settings = get_settings()
client, database = initialize_database(settings.mongodb_uri, settings.mongodb_database)

configs = list(database.assessment_configurations.find())
print(f'Assessment configurations: {len(configs)}')
for c in configs:
    print(f'  - {c.get("competency_code")}')

client.close()
