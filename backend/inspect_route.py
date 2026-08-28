#!/usr/bin/env python3
from app.main import app

# Find the /configs route and inspect it
for route in app.routes:
    if hasattr(route, 'path') and route.path == '/api/v1/assessments/configs':
        print(f"Route: {route.path}")
        print(f"Endpoint: {route.endpoint.__name__}")
        print(f"Endpoint signature:")
        import inspect
        sig = inspect.signature(route.endpoint)
        for param_name, param in sig.parameters.items():
            print(f"  {param_name}: {param.annotation}")
        
        print(f"\nDependant object:")
        if hasattr(route, 'dependant'):
            dep = route.dependant
            print(f"  Dependencies: {dep.dependencies}")
            print(f"  Params: {dep.params}")
            print(f"  Security: {dep.security}")
            
            if dep.params:
                for param in dep.params:
                    print(f"    - {param.name}: {param}")
        
        print(f"\nBody field: {route.body_field}")
