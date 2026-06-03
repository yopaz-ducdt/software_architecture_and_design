import os
import re

services = [
    'analytics_service',
    'content_service',
    'interaction_service',
    'inventory_service',
    'marketing_service',
    'notification_service',
    'staff_service'
]

# We want to replace the hardcoded host.docker.internal in main.py
pattern = re.compile(r'from sqlalchemy\.engine import URL as _URL\nDATABASE_URL = _URL\.create\([^)]+\)')

for s in services:
    main_path = os.path.join(s, 'main.py')
    if os.path.exists(main_path):
        with open(main_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        db_name = s.replace('_service', '') + '_db'
        
        replacement = f'DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:Duyanh090%40@mysql:3306/{db_name}")'
        
        new_content = pattern.sub(replacement, content)
        
        if new_content != content:
            with open(main_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Patched {main_path}')
        else:
            print(f'No match found in {main_path}')
