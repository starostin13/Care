#!/usr/bin/env python
import sys
sys.path.insert(0, '/app')

try:
    from CareBot import sqllite_helper
    print("✓ sqllite_helper imported")
    
    # Check for new functions
    funcs = [
        'is_warmaster_admin',
        'get_warmaster_info_by_id',
        'verify_admin_web_credentials'
    ]
    
    for func_name in funcs:
        exists = hasattr(sqllite_helper, func_name)
        status = "✓" if exists else "✗"
        print(f"{status} {func_name}: {exists}")
    
    # Check file modification time
    import os
    mtime = os.path.getmtime('/app/CareBot/sqllite_helper.py')
    from datetime import datetime
    print(f"\nFile modified: {datetime.fromtimestamp(mtime)}")
    
    # Check first 30 lines of sqllite_helper
    print("\n=== First 30 lines ===")
    with open('/app/CareBot/sqllite_helper.py', 'r') as f:
        for i, line in enumerate(f):
            if i >= 30:
                break
            print(f"{i+1}: {line.rstrip()}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
