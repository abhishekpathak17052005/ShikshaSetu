#!/usr/bin/env python3
from app.main import app

print('Routes containing "assessments":')
for route in app.routes:
    path_str = str(route.path) if hasattr(route, 'path') else ''
    if 'assessments' in path_str:
        methods = route.methods if hasattr(route, 'methods') else 'N/A'
        print(f'  {methods} {path_str}')
