#!/usr/bin/env python3
from app.core.config import get_settings
from app.core.database import initialize_database

settings = get_settings()
client, database = initialize_database(settings.mongodb_uri, settings.mongodb_database)

# Check if BEH_CHANGE_MANAGEMENT competency exists
comp = database.competencies.find_one({'code': 'BEH_CHANGE_MANAGEMENT'})
if comp:
    print(f'Competency BEH_CHANGE_MANAGEMENT EXISTS')
    print(f'  ID: {comp.get("_id")}')
    print(f'  Title: {comp.get("title")}')
else:
    print('Competency BEH_CHANGE_MANAGEMENT does NOT exist in competencies collection')
    
# List all competencies with 'BEH' prefix
beh_comps = list(database.competencies.find({'code': {'$regex': '^BEH'}}))
print(f'\nAll BEH competencies in DB: {len(beh_comps)}')
for c in beh_comps:
    print(f'  - {c.get("code")}')

client.close()
