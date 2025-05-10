import os
import sys

# Get the absolute path of the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.app import create_app

app = create_app()

if __name__ == '__main__':
    app.run() 