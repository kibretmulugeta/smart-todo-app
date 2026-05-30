import sys
import os

# Add your project directory to the path
path = '/home/YOURUSERNAME/smart_todo_app'
if path not in sys.path:
    sys.path.append(path)

# Import your Flask app
from app import app as application