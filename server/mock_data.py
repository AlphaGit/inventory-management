"""
Mock data for the Factory Inventory Management System
This module loads sample data from JSON files for inventory items, orders, demand forecasts, and backlog items.
All data is from September 2025 and includes warehouse, category, and date fields for filtering.
"""

import json
import os
import tempfile
import threading

# Get the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def load_json_file(filename):
    """Load data from a JSON file in the data directory"""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'r') as f:
        return json.load(f)

# Load all datasets from JSON files
inventory_items = load_json_file('inventory.json')
orders = load_json_file('orders.json')
demand_forecasts = load_json_file('demand_forecasts.json')
backlog_items = load_json_file('backlog_items.json')

# Load spending data
spending_data = load_json_file('spending.json')
spending_summary = spending_data['spending_summary']
monthly_spending = spending_data['monthly_spending']
category_spending = spending_data['category_spending']

# Load transactions
recent_transactions = load_json_file('transactions.json')

# Load purchase orders
purchase_orders = load_json_file('purchase_orders.json')

# Restocking orders are the only data the API writes. The file is gitignored and
# created on first write. RESTOCK_ORDERS_PATH lets tests redirect it to a temp file.
RESTOCK_ORDERS_PATH = os.environ.get('RESTOCK_ORDERS_PATH', os.path.join(DATA_DIR, 'restock_orders.json'))
_restock_orders_lock = threading.Lock()

def load_restock_orders(path=None):
    """Load submitted restocking orders, or an empty list when the file does not exist yet"""
    path = path or RESTOCK_ORDERS_PATH
    if not os.path.exists(path):
        return []
    with open(path, 'r') as f:
        return json.load(f)

def save_restock_orders(orders, path=None):
    """Write restocking orders to disk atomically"""
    path = path or RESTOCK_ORDERS_PATH
    # Sync FastAPI handlers run in a threadpool, so two submits can overlap. The lock
    # serializes writers, and temp file + os.replace means a reader never sees a
    # half-written file.
    with _restock_orders_lock:
        directory = os.path.dirname(path) or '.'
        fd, tmp_path = tempfile.mkstemp(dir=directory, suffix='.tmp')
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(orders, f, indent=2)
            os.replace(tmp_path, path)
        except Exception:
            os.remove(tmp_path)
            raise

restock_orders = load_restock_orders()

# All data is now loaded from JSON files in the data/ directory
# This allows for easier maintenance and updates of the sample data
