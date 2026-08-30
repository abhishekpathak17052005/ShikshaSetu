#!/usr/bin/env python3
"""Document active seeded data for SIH submission."""

from pymongo import MongoClient
from app.core.config import get_settings

settings = get_settings()
client = MongoClient(settings.mongodb_uri)
db = client[settings.mongodb_database]

# Active competencies
competencies = list(db.competencies.find({}, {"code": 1, "name": 1, "domain": 1}).sort("code", 1))
print("=" * 80)
print("ACTIVE COMPETENCIES (33)")
print("=" * 80)
for i, c in enumerate(competencies, 1):
    print(f"{i:2}. {c['code']:40} {c['name']:30} ({c.get('domain', 'unknown')})")

# Active iGOT mappings
igot_mappings = list(db.competency_resource_mappings.find(
    {"provider": "IGOT"}, 
    {"resource_id": 1, "competency_code": 1}
).sort("competency_code", 1))

igot_by_comp = {}
for m in igot_mappings:
    comp = m.get("competency_code")
    if comp not in igot_by_comp:
        igot_by_comp[comp] = []
    igot_by_comp[comp].append(m)

print("\n" + "=" * 80)
print("ACTIVE iGOT MAPPINGS (42)")
print("=" * 80)
for comp in sorted(igot_by_comp.keys()):
    count = len(igot_by_comp[comp])
    print(f"{comp:40} {count:3} mappings")

# Active NSSTA mappings
nssta_mappings = list(db.competency_resource_mappings.find(
    {"provider": "NSSTA"}, 
    {"resource_id": 1, "competency_code": 1}
).sort("competency_code", 1))

nssta_by_comp = {}
for m in nssta_mappings:
    comp = m.get("competency_code")
    if comp not in nssta_by_comp:
        nssta_by_comp[comp] = []
    nssta_by_comp[comp].append(m)

print("\n" + "=" * 80)
print("ACTIVE NSSTA MAPPINGS (46)")
print("=" * 80)
for comp in sorted(nssta_by_comp.keys()):
    count = len(nssta_by_comp[comp])
    print(f"{comp:40} {count:3} mappings")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total Competencies:     {len(competencies)}")
print(f"iGOT Mappings:          {len(igot_mappings)}")
print(f"NSSTA Mappings:         {len(nssta_mappings)}")
print(f"Total Mappings:         {len(igot_mappings) + len(nssta_mappings)}")

client.close()
