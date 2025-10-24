"""
WSGI configuration for PythonAnywhere deployment
This file is used by PythonAnywhere to run your Flask application
"""
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/vineet2812/BidSystem'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Import the Flask app
from app import app as application

# This is required for PythonAnywhere
if __name__ == '__main__':
    application.run()
