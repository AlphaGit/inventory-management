import math
import threading
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel, Field
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders, restock_orders, save_restock_orders

app = FastAPI(title="Factory Inventory Management System")

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

def filter_by_month(items: list, month: Optional[str]) -> list:
    """Filter items by month/quarter based on order_date field"""
    if not month or month == 'all':
        return items

    if month.startswith('Q'):
        # Handle quarters
        if month in QUARTER_MAP:
            months = QUARTER_MAP[month]
            return [item for item in items if any(m in item.get('order_date', '') for m in months)]
    else:
        # Direct month match
        return [item for item in items if month in item.get('order_date', '')]

    return items

def apply_filters(items: list, warehouse: Optional[str] = None, category: Optional[str] = None,
                 status: Optional[str] = None) -> list:
    """Apply common filters to a list of items"""
    filtered = items

    if warehouse and warehouse != 'all':
        filtered = [item for item in filtered if item.get('warehouse') == warehouse]

    if category and category != 'all':
        filtered = [item for item in filtered if item.get('category', '').lower() == category.lower()]

    if status and status != 'all':
        filtered = [item for item in filtered if item.get('status', '').lower() == status.lower()]

    return filtered

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class InventoryItem(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    reorder_point: int
    unit_cost: float
    location: str
    last_updated: str

class Order(BaseModel):
    id: str
    order_number: str
    customer: str
    items: List[dict]
    status: str
    order_date: str
    expected_delivery: str
    total_value: float
    actual_delivery: Optional[str] = None
    warehouse: Optional[str] = None
    category: Optional[str] = None

class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    period: str
    # Nullable: suppliers do not always provide cost or lead time
    unit_cost: Optional[float] = None
    lead_time_days: Optional[int] = None

class BacklogItem(BaseModel):
    id: str
    order_id: str
    item_sku: str
    item_name: str
    quantity_needed: int
    quantity_available: int
    days_delayed: int
    priority: str
    has_purchase_order: Optional[bool] = False

class PurchaseOrder(BaseModel):
    id: str
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    status: str
    created_date: str
    notes: Optional[str] = None

class CreatePurchaseOrderRequest(BaseModel):
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    notes: Optional[str] = None

class RestockLine(BaseModel):
    sku: str
    name: str
    trend: str
    current_demand: int
    forecasted_demand: int
    growth_pct: float
    on_hand: int
    need: int
    unit_cost: Optional[float] = None
    lead_time_days: Optional[int] = None
    recommended_qty: int = 0
    line_total: float = 0

class RestockRecommendation(BaseModel):
    budget: float
    max_budget: float
    default_budget: float
    lines: List[RestockLine]
    total: float
    remaining: float
    unpriced: List[RestockLine]

class RestockOrderLineIn(BaseModel):
    sku: str
    quantity: int = Field(ge=0)

class CreateRestockOrderRequest(BaseModel):
    budget: float = Field(ge=0)
    lines: List[RestockOrderLineIn]

class RestockOrderItem(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_cost: float
    line_total: float
    lead_time_days: int

class RestockOrder(BaseModel):
    id: str
    order_number: str
    status: str
    submitted_at: str
    budget: float
    items: List[RestockOrderItem]
    total_cost: float
    lead_time_days: int
    expected_delivery: str

# Restocking: growing demand is funded first, shrinking demand last
TREND_RANK = {'increasing': 0, 'stable': 1, 'decreasing': 2}
DEFAULT_LEAD_TIME_DAYS = 14
BUDGET_STEP = 500

# Serializes order-number assignment and the file write across concurrent POSTs
_restock_create_lock = threading.Lock()

def to_cents(amount: float) -> int:
    # Budget math runs in integer cents so floor division is exact (24.99 * 3 != 74.97 in floats)
    return int(round(amount * 100))

def compute_restock_lines():
    """Join forecasts with on-hand stock. Returns (priced lines in priority order, unpriced lines)."""
    on_hand_by_sku = {}
    for item in inventory_items:
        on_hand_by_sku[item['sku']] = on_hand_by_sku.get(item['sku'], 0) + item['quantity_on_hand']

    priced, unpriced = [], []
    for forecast in demand_forecasts:
        # Forecasts are company-wide, so subtract stock from all warehouses. SKUs missing
        # from inventory count as 0 on hand; need never goes below 0.
        on_hand = on_hand_by_sku.get(forecast['item_sku'], 0)
        current = forecast['current_demand']
        line = {
            'sku': forecast['item_sku'],
            'name': forecast['item_name'],
            'trend': forecast['trend'],
            'current_demand': current,
            'forecasted_demand': forecast['forecasted_demand'],
            'growth_pct': (forecast['forecasted_demand'] - current) / current * 100 if current else 0.0,
            'on_hand': on_hand,
            'need': max(0, forecast['forecasted_demand'] - on_hand),
            'unit_cost': forecast.get('unit_cost'),
            'lead_time_days': forecast.get('lead_time_days'),
        }
        (unpriced if line['unit_cost'] is None else priced).append(line)

    priced.sort(key=lambda l: (TREND_RANK.get(l['trend'], len(TREND_RANK)), -l['growth_pct']))
    for line in priced + unpriced:
        line['growth_pct'] = round(line['growth_pct'], 1)
    return priced, unpriced

def allocate_budget(lines: list, budget: float) -> list:
    """Fill lines in priority order: each gets as much of its need as the remaining budget buys."""
    remaining = to_cents(budget)
    allocated = []
    for line in lines:
        cost = to_cents(line['unit_cost'])
        qty = line['need'] if cost <= 0 else min(line['need'], remaining // cost)
        # No break when a line is only partly funded: leftover cents can still buy
        # cheaper items further down the list.
        remaining -= qty * cost
        allocated.append({**line, 'recommended_qty': qty, 'line_total': qty * cost / 100})
    return allocated

# API endpoints
@app.get("/")
def root():
    return {"message": "Factory Inventory Management System API", "version": "1.0.0"}

@app.get("/api/inventory", response_model=List[InventoryItem])
def get_inventory(
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Get all inventory items with optional filtering"""
    return apply_filters(inventory_items, warehouse, category)

@app.get("/api/inventory/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: str):
    """Get a specific inventory item"""
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/api/orders", response_model=List[Order])
def get_orders(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get all orders with optional filtering"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)
    return filtered_orders

@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    """Get a specific order"""
    order = next((order for order in orders if order["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/api/demand", response_model=List[DemandForecast])
def get_demand_forecasts():
    """Get demand forecasts"""
    return demand_forecasts

@app.get("/api/backlog", response_model=List[BacklogItem])
def get_backlog():
    """Get backlog items with purchase order status"""
    # Add has_purchase_order flag to each backlog item
    result = []
    for item in backlog_items:
        item_dict = dict(item)
        # Check if this backlog item has a purchase order
        has_po = any(po["backlog_item_id"] == item["id"] for po in purchase_orders)
        item_dict["has_purchase_order"] = has_po
        result.append(item_dict)
    return result

@app.get("/api/dashboard/summary")
def get_dashboard_summary(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get summary statistics for dashboard with optional filtering"""
    # Filter inventory
    filtered_inventory = apply_filters(inventory_items, warehouse, category)

    # Filter orders
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    total_inventory_value = sum(item["quantity_on_hand"] * item["unit_cost"] for item in filtered_inventory)
    low_stock_items = len([item for item in filtered_inventory if item["quantity_on_hand"] <= item["reorder_point"]])
    pending_orders = len([order for order in filtered_orders if order["status"] in ["Processing", "Backordered"]])
    total_backlog_items = len(backlog_items)

    return {
        "total_inventory_value": round(total_inventory_value, 2),
        "low_stock_items": low_stock_items,
        "pending_orders": pending_orders,
        "total_backlog_items": total_backlog_items,
        "total_orders_value": sum(order["total_value"] for order in filtered_orders)
    }

@app.get("/api/spending/summary")
def get_spending_summary():
    """Get spending summary statistics"""
    return spending_summary

@app.get("/api/spending/monthly")
def get_monthly_spending():
    """Get monthly spending breakdown"""
    return monthly_spending

@app.get("/api/spending/categories")
def get_category_spending():
    """Get spending by category"""
    return category_spending

@app.get("/api/spending/transactions")
def get_recent_transactions():
    """Get recent transactions"""
    return recent_transactions

@app.get("/api/reports/quarterly")
def get_quarterly_reports():
    """Get quarterly performance reports"""
    # Calculate quarterly statistics from orders
    quarters = {}

    for order in orders:
        order_date = order.get('order_date', '')
        # Determine quarter
        if '2025-01' in order_date or '2025-02' in order_date or '2025-03' in order_date:
            quarter = 'Q1-2025'
        elif '2025-04' in order_date or '2025-05' in order_date or '2025-06' in order_date:
            quarter = 'Q2-2025'
        elif '2025-07' in order_date or '2025-08' in order_date or '2025-09' in order_date:
            quarter = 'Q3-2025'
        elif '2025-10' in order_date or '2025-11' in order_date or '2025-12' in order_date:
            quarter = 'Q4-2025'
        else:
            continue

        if quarter not in quarters:
            quarters[quarter] = {
                'quarter': quarter,
                'total_orders': 0,
                'total_revenue': 0,
                'delivered_orders': 0,
                'avg_order_value': 0
            }

        quarters[quarter]['total_orders'] += 1
        quarters[quarter]['total_revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            quarters[quarter]['delivered_orders'] += 1

    # Calculate averages and fulfillment rate
    result = []
    for q, data in quarters.items():
        if data['total_orders'] > 0:
            data['avg_order_value'] = round(data['total_revenue'] / data['total_orders'], 2)
            data['fulfillment_rate'] = round((data['delivered_orders'] / data['total_orders']) * 100, 1)
        result.append(data)

    # Sort by quarter
    result.sort(key=lambda x: x['quarter'])
    return result

@app.get("/api/reports/monthly-trends")
def get_monthly_trends():
    """Get month-over-month trends"""
    months = {}

    for order in orders:
        order_date = order.get('order_date', '')
        if not order_date:
            continue

        # Extract month (format: YYYY-MM-DD)
        month = order_date[:7]  # Gets YYYY-MM

        if month not in months:
            months[month] = {
                'month': month,
                'order_count': 0,
                'revenue': 0,
                'delivered_count': 0
            }

        months[month]['order_count'] += 1
        months[month]['revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            months[month]['delivered_count'] += 1

    # Convert to list and sort
    result = list(months.values())
    result.sort(key=lambda x: x['month'])
    return result

@app.get("/api/restocking/recommendations", response_model=RestockRecommendation)
def get_restock_recommendations(budget: Optional[float] = Query(None, ge=0)):
    """Recommend restock quantities for forecast items within a budget"""
    priced, unpriced = compute_restock_lines()

    full_cost = sum(to_cents(l['unit_cost']) * l['need'] for l in priced) / 100
    max_budget = math.ceil(full_cost / 1000) * 1000
    default_budget = math.floor(max_budget / 2 / BUDGET_STEP) * BUDGET_STEP
    if budget is None:
        budget = default_budget

    lines = allocate_budget(priced, budget)
    total_cents = sum(to_cents(l['line_total']) for l in lines)
    return {
        'budget': budget,
        'max_budget': max_budget,
        'default_budget': default_budget,
        'lines': lines,
        'total': total_cents / 100,
        'remaining': (to_cents(budget) - total_cents) / 100,
        'unpriced': unpriced,
    }

@app.get("/api/restocking/orders", response_model=List[RestockOrder])
def get_restock_orders():
    """Get submitted restocking orders, newest first"""
    return list(reversed(restock_orders))

@app.post("/api/restocking/orders", response_model=RestockOrder, status_code=201)
def create_restock_order(request: CreateRestockOrderRequest):
    """Submit a restocking order"""
    forecasts_by_sku = {f['item_sku']: f for f in demand_forecasts}

    skus = [line.sku for line in request.lines]
    if len(skus) != len(set(skus)):
        raise HTTPException(status_code=422, detail="Duplicate SKU in order lines")

    items = []
    total_cents = 0
    for line in request.lines:
        forecast = forecasts_by_sku.get(line.sku)
        if not forecast:
            raise HTTPException(status_code=422, detail=f"Unknown SKU: {line.sku}")
        if forecast.get('unit_cost') is None:
            raise HTTPException(status_code=422, detail=f"SKU has no unit cost: {line.sku}")
        if line.quantity == 0:
            continue
        # Price from server data only; the request carries no cost, so the client cannot change it
        cost = to_cents(forecast['unit_cost'])
        total_cents += cost * line.quantity
        items.append({
            'sku': line.sku,
            'name': forecast['item_name'],
            'quantity': line.quantity,
            'unit_cost': forecast['unit_cost'],
            'line_total': cost * line.quantity / 100,
            'lead_time_days': forecast.get('lead_time_days') or DEFAULT_LEAD_TIME_DAYS,
        })

    if not items:
        raise HTTPException(status_code=422, detail="Order has no items")
    if total_cents > to_cents(request.budget):
        raise HTTPException(status_code=422, detail="Order total exceeds budget")

    # The order arrives when its slowest item arrives
    lead_time_days = max(item['lead_time_days'] for item in items)
    submitted_at = datetime.now(timezone.utc).replace(microsecond=0)

    with _restock_create_lock:
        next_number = max((int(o['order_number'].split('-')[1]) for o in restock_orders), default=0) + 1
        order = {
            'id': str(next_number),
            'order_number': f"RST-{next_number:04d}",
            'status': 'Submitted',
            'submitted_at': submitted_at.isoformat(),
            'budget': request.budget,
            'items': items,
            'total_cost': total_cents / 100,
            'lead_time_days': lead_time_days,
            'expected_delivery': (submitted_at + timedelta(days=lead_time_days)).isoformat(),
        }
        # Write the file before updating memory, so a failed write leaves both unchanged
        save_restock_orders(restock_orders + [order])
        restock_orders.append(order)

    return order

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
