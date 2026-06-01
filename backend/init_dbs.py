"""
init_dbs.py — Initialize unified app.db on startup.
Delegates to utils/app_db.py which owns the full schema.
"""

import sys
import os

# Ensure backend directory is in the Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


def init_dbs():
    from utils.app_db import init_db
    init_db()


if __name__ == "__main__":
    init_dbs()
    print("Database initialized successfully.")
