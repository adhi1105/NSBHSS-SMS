import os
import sys

# 1. Add your project directory to the sys.path
path = '/home/yourusername/mysite'  # <--- UPDATE THIS to your actual path
if path not in sys.path:
    sys.path.append(path)

# 2. Point to your settings.py file
os.environ['DJANGO_SETTINGS_MODULE'] = 'school_system.settings'

# 3. Create the application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()