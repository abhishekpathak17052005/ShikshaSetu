#!/usr/bin/env python3
"""Deep inspection of the upload route - improved version"""

from app.ai.router import router
import inspect

print("="*100)
print("DEEP ROUTE INSPECTION V2: Finding source of 'scope'")
print("="*100)

# Get the upload route
for route in router.routes:
    if hasattr(route, 'path') and '/upload' in route.path:
        print(f"\nRoute: {route.path} {route.methods}")
        
        endpoint = route.endpoint
        print(f"Endpoint: {endpoint.__name__}")
        
        # Get original signature
        sig = inspect.signature(endpoint)
        print(f"\nSignature from code:")
        print(f"  {endpoint.__name__}{sig}")
        
        # Check the route's dependant
        if hasattr(route, 'dependant'):
            dependant = route.dependant
            
            print(f"\n[Route dependant] body_params:")
            for bp in dependant.body_params:
                print(f"  - {bp.name}")
            
            print(f"\n[Route dependant] dependencies ({len(dependant.dependencies)}):")
            for i, dep in enumerate(dependant.dependencies):
                print(f"\n  [{i}] {dep.name} (call={dep.call.__name__ if hasattr(dep.call, '__name__') else dep.call})")
                
                if dep.body_params:
                    print(f"      body_params:")
                    for bp in dep.body_params:
                        print(f"        - {bp.name}")
                        
                        # Check if this is 'scope'
                        if bp.name == 'scope':
                            print(f"          ^^^ FOUND SCOPE HERE ^^^")
                            print(f"          type: {type(bp)}")
                            print(f"          field_info: {bp.field_info}")
                            
                            # Trace back to see what created it
                            print(f"\n          Tracing back:")
                            print(f"            Parent dependency: {dep.name}")
                            print(f"            Dependency function: {dep.call}")
                            print(f"            This dependency's dependencies: {len(dep.dependencies)}")

print("\n" + "="*100)
print("SUMMARY")
print("="*100)

# Simpler summary
for route in router.routes:
    if hasattr(route, 'path') and '/upload' in route.path:
        if hasattr(route, 'dependant'):
            dependant = route.dependant
            
            print(f"\nRoute: {route.path}")
            print(f"Route-level body_params: {[bp.name for bp in dependant.body_params]}")
            
            print(f"\nDependencies and their body_params:")
            for dep in dependant.dependencies:
                dep_name = dep.call.__name__ if hasattr(dep.call, '__name__') else str(dep.call)
                bp_names = [bp.name for bp in dep.body_params]
                
                if bp_names:
                    print(f"  {dep.name or 'unnamed'} ({dep_name}): body_params = {bp_names}")
                    if 'scope' in bp_names:
                        print(f"    ⚠️  SCOPE FOUND IN THIS DEPENDENCY")
                else:
                    print(f"  {dep.name or 'unnamed'} ({dep_name}): (no body_params)")

print("\n" + "="*100)
print("CONCLUSION")
print("="*100)
print("""
If 'scope' does NOT appear in the dependencies above, then the issue is NOT
coming from the endpoint's declared dependencies.

Possible source:
1. The `request: Request = Depends()` line without a dependency function
2. FastAPI is auto-discovering the Request class and treating scope as a field
3. There's middleware or a global setting adding it

If 'scope' DOES appear, identify which dependency introduces it.
""")
