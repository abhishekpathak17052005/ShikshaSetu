#!/usr/bin/env python3
"""Deep inspection of the upload route to find the source of 'scope' parameter"""

from app.ai.router import router
from app.auth.dependencies import get_current_user
import inspect

print("="*100)
print("DEEP ROUTE INSPECTION: Finding source of 'scope'")
print("="*100)

# Get the upload route
for route in router.routes:
    if hasattr(route, 'path') and '/upload' in route.path:
        print(f"\nRoute: {route.path} {route.methods}")
        
        # The endpoint function
        endpoint = route.endpoint
        print(f"\nEndpoint Function: {endpoint.__name__}")
        
        # Get original signature
        sig = inspect.signature(endpoint)
        print(f"\nOriginal Signature (from code):")
        print(f"  {endpoint.__name__}{sig}")
        
        # Get parameters from code
        print(f"\nParameters from inspect.signature():")
        for param_name, param in sig.parameters.items():
            print(f"  {param_name}:")
            print(f"    kind: {param.kind}")
            print(f"    annotation: {param.annotation}")
            print(f"    default: {param.default}")
            if hasattr(param.default, '__dict__'):
                print(f"    default.__dict__: {param.default.__dict__}")
        
        # Check the route's dependant (FastAPI's internal representation)
        if hasattr(route, 'dependant'):
            dependant = route.dependant
            print(f"\n\nRoute Dependant (FastAPI's processed version):")
            print(f"  name: {dependant.name}")
            print(f"  call: {dependant.call}")
            
            print(f"\n  body_params ({len(dependant.body_params)}):")
            for bp in dependant.body_params:
                print(f"    - name: {bp.name}")
                print(f"      annotation: {bp.annotation}")
                print(f"      field_info: {bp.field_info}")
            
            print(f"\n  dependencies ({len(dependant.dependencies)}):")
            for i, dep in enumerate(dependant.dependencies):
                print(f"    [{i}] name: {dep.name}")
                print(f"        call: {dep.call}")
                print(f"        body_params: {len(dep.body_params)} items")
                
                # If this dependency has body_params, inspect them
                if dep.body_params:
                    for bp in dep.body_params:
                        print(f"          - {bp.name}: {bp.annotation}")
                
                # Check if this is the 'request' dependency
                if dep.name == 'request':
                    print(f"        [FOUND 'request' dependency]")
                    print(f"        body_params in 'request' dependency:")
                    for bp in dep.body_params:
                        print(f"          NAME: {bp.name}")
                        print(f"          ANNOTATION: {bp.annotation}")
                        print(f"          FIELD_INFO: {bp.field_info}")
                        print(f"          ← THIS IS WHERE 'scope' COMES FROM")

print("\n" + "="*100)
print("INTERPRETATION")
print("="*100)
print("""
Key finding: If 'scope' appears in body_params of the 'request' dependency,
it means one of the following:

1. The Request class being used has 'scope' defined in its model
2. FastAPI is parsing Request attributes and treating them as body params
3. There's a mismatch between what Starlette.Request expects and what FastAPI sees

The critical question is: Which dependency is adding the 'scope' body param?
- Is it coming from get_current_user()?
- Is it coming from the Request = Depends() line?
- Is it coming from something else?

Check the output above for "FOUND 'request' dependency" to see where 'scope' originates.
""")
