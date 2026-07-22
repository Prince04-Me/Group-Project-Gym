"""Sales, staff, leaderboard, and campaign analytics for Peak Pulse Fitness.

Several kinds of analytics live here:
  - Chart generation, saved as static PNG files (customer geography/spending,
    bestsellers, staff distribution by department).
  - Leaderboard queries (customers, staff, departments).
  - Marketing campaign data (birthdays, inactivity, product recommendations,
    low-performing products).

All return plain query results / lists / dicts for routes.py to pass
straight into render_template

Reuses the app's shared SQLAlchemy engine/session (see db.py) instead of
opening separate connections, so there is a single source of truth for the
database across the whole app.
"""
import os

from db import db

from models import Customer, Employee, Order

from collections import namedtuple, defaultdict
from datetime import datetime, timedelta
from itertools import combinations

from sqlalchemy import func

import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use('Agg')

# Identifying and mapping the departments
DEPARTMENT_NAMES = {
    100: 'Executive',
    101: 'Department 101',
    102: 'Department 102',
}

# All plots stored in one folder
PLOTS_DIR = os.path.join(os.path.dirname(__file__), 'statics', 'plots')


def generate_dashboard_plots():
    """Generate and save both customer dashboard plots as PNG files.

    Uses SQLAlchemy connection directly (compatible with Pandas 2.x+).
    Plot 1: Customer geographic distribution (bar chart by country).
    Plot 2: Age group vs. average spending (bar chart).
    """
    os.makedirs(PLOTS_DIR, exist_ok=True)

    engine = db.get_engine()
    with engine.connect() as conn:
        customers = pd.read_sql_table('Customer_data', conn)
        orders = pd.read_sql_table('Order_data', conn)

    # Plot 1: Customer origin bar chart
    country_counts = customers['Country'].value_counts()

    fig, ax = plt.subplots(figsize=(8, 4))
    country_counts.plot(kind='bar', ax=ax, color='#2d6a2d', edgecolor='white')
    ax.set_title('Customer Geographic Distribution', fontsize=14, fontweight='bold')
    ax.set_xlabel('Country')
    ax.set_ylabel('Number of Customers')
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, 'customer_origin.png'), dpi=120)
    plt.close(fig)

    # --- Plot 2: Age vs. spending (scatter plot) --------------------------

    # Merge orders with customer age so each order row carries the buyer's age.
    merged = orders.merge(
        customers[['CustomerID', 'Age']], on='CustomerID', how='left'
    )
    # Total value of a single order = unit price * quantity ordered.
    merged['OrderTotal'] = merged['Price'] * merged['Amount']

    # Aggregate to one point per customer: age vs. their total spending.
    customer_spending = (
        merged.groupby(['CustomerID', 'Age'], as_index=False)['OrderTotal']
        .sum()
        .rename(columns={'OrderTotal': 'TotalSpending'})
    )

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.scatter(
        customer_spending["Age"],
        customer_spending["TotalSpending"],
        color="#f0a500",
        edgecolor="black",
        alpha=0.7,
    )
    ax.set_title('Customer Age vs. Total Spending', fontsize=14, fontweight='bold')
    ax.set_xlabel('Customer Age')
    ax.set_ylabel('Total Spending')
    plt.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, 'age_vs_spending.png'), dpi=120)
    plt.close(fig)


def generate_sales_and_staff_plots():
    """Generate and save the bestsellers and staff distribution charts.

    Plot 1: Top 10 best-selling products/services by total units sold.
    Plot 2: Staff distribution by department.
    """
    os.makedirs(PLOTS_DIR, exist_ok=True)
    engine = db.get_engine()

    with engine.connect() as conn:
        bestsellers = pd.read_sql_query('''
            SELECT Description, SUM(Amount) AS Total
            FROM Order_data
            GROUP BY Description
            ORDER BY Total DESC
            LIMIT 10;
        ''', conn)

        staff = pd.read_sql_query('''
            SELECT DepartmentID, COUNT(*) AS Total
            FROM Employees_data
            GROUP BY DepartmentID;
        ''', conn)

    """Plot 1: Top 10 bestsellers. Horizontal bars suit long product names,
    invert the y-axis so the best seller appears at the top.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(bestsellers['Description'], bestsellers['Total'])
    ax.invert_yaxis()
    ax.set_xlabel('Total Units Sold')
    ax.set_title('Top 10 Most Popular Products & Services')
    plt.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, 'Top_10_Bestsellers.png'), dpi=120)
    plt.close(fig)

    # Plot 2: Staff distribution by department.
    staff['Department'] = staff['DepartmentID'].map(DEPARTMENT_NAMES)
    staff['Department'] = staff['Department'].fillna(
        staff['DepartmentID'].apply(lambda dept_id: f'Department {dept_id}')
    )

    fig1, ax1 = plt.subplots(figsize=(10, 6))
    ax1.pie(staff['Total'], labels=staff['Department'], autopct='%1.1f%%')
    ax1.set_title('Staff Distribution by Department')
    plt.tight_layout()
    fig1.savefig(os.path.join(PLOTS_DIR, 'Staff_Distribution.png'), dpi=120)
    plt.close(fig1)

# ---------------------------------------------------------------------------
# Leaderboard queries
# ---------------------------------------------------------------------------

def get_customer_leaderboards():
# Return the top 10 customers by order frequency and by total revenue.
    top_frequency = (
        db.session.query(
            Customer.FirstName,
            Customer.LastName,
            func.count(Order.OrderID).label('order_count')
        )
        .join(Order, Order.CustomerID == Customer.CustomerID)
        .group_by(Customer.CustomerID)
        .order_by(func.count(Order.OrderID).desc())
        .limit(10)
        .all()
    )

    top_revenue = (
        db.session.query(
            Customer.FirstName,
            Customer.LastName,
            func.sum(Order.Price * Order.Amount).label('total_spent')
        )
        .join(Order, Order.CustomerID == Customer.CustomerID)
        .group_by(Customer.CustomerID)
        .order_by(func.sum(Order.Price * Order.Amount).desc())
        .limit(10)
        .all()
    )

    return top_frequency, top_revenue


def get_staff_leaderboard():
# Return the top 10 employees ranked by number of transactions processed.
    return (
        db.session.query(
            Employee.FirstName,
            Employee.LastName,
            func.count(Order.OrderID).label('order_count')
        )
        .join(Order, Order.EmployeeID == Employee.EmployeeID)
        .group_by(Employee.EmployeeID)
        .order_by(func.count(Order.OrderID).desc())
        .limit(10)
        .all()
    )

DepartmentRevenue = namedtuple('DepartmentRevenue', ['department', 'total_revenue'])

def get_department_leaderboard():
    """Return departments ranked by total revenue generated.

    Revenue is attributed to a department through the employee who
    processed each order (Order.EmployeeID -> Employee.DepartmentID).
    Department names reuse the same DEPARTMENT_NAMES mapping as the staff
    distribution chart, so an unmapped DepartmentID still shows up as
    "Department <id>" instead of being dropped.
    """
    rows = (
        db.session.query(
            Employee.DepartmentID,
            func.sum(Order.Price * Order.Amount).label('total_revenue')
        )
        .join(Order, Order.EmployeeID == Employee.EmployeeID)
        .group_by(Employee.DepartmentID)
        .order_by(func.sum(Order.Price * Order.Amount).desc())
        .all()
    )

    return [
        DepartmentRevenue(
            DEPARTMENT_NAMES.get(department_id, f'Department {department_id}'),
            total_revenue,
        )
        for department_id, total_revenue in rows
    ]

# ---------------------------------------------------------------------------
# Campaign data
# ---------------------------------------------------------------------------

def get_campaign_data():
    """Return birthday-reminder and inactive-customer campaign data.

    Campaign 1: customers whose birth month matches the current calendar
                month.
    Campaign 2: customers with no orders in the past 6 months.
    """
    today         = datetime.today()
    current_month = today.month
    cutoff_date   = today - timedelta(days=182)  # ~6 months ago

    all_customers = Customer.query.all()
    all_orders    = Order.query.all()

    birthday_customers = [
        c for c in all_customers
        if c.BirthDate and int(c.BirthDate[5:7]) == current_month
    ]

    # Build a set of CustomerIDs that have at least one recent order
    active_ids = {
        o.CustomerID for o in all_orders
        if o.Date and datetime.strptime(o.Date, '%Y-%m-%d') >= cutoff_date
    }

    # Customers NOT in the active set are considered inactive
    inactive_customers = [
        c for c in all_customers
        if c.CustomerID not in active_ids
    ]

    return {
        'birthday_customers': birthday_customers,
        'inactive_customers': inactive_customers,
        'current_month': today.strftime('%B'),
    }


# ---------------------------------------------------------------------------
# Rule-based recommendation engine
# ---------------------------------------------------------------------------

# dot-access instead of indexing into a plain dict.
CustomerRecommendation = namedtuple('CustomerRecommendation', ['customer', 'recommendations'])
ProductPerformance     = namedtuple('ProductPerformance', ['description', 'total_units'])


def _bestseller_ranking(item_total_qty):
    # Rank items by total units sold: quantity descending, name ascending on ties.
    return [
        item for item, _ in sorted(
            item_total_qty.items(), key=lambda kv: (-kv[1], kv[0])
        )
    ]


def _build_co_occurrence_ranking(customer_item_qty):
    """Build a 'frequently bought together' ranking for every item.

    Treats each customer's full purchase history as one basket (there's no
    explicit per-transaction basket ID in the schema): for every pair of
    distinct items the same customer has ever bought, a counter is
    incremented. Each item then gets a ranked list of partner items, sorted
    by how often they co-occurred (descending), with ties broken
    alphabetically.

    Args:
        customer_item_qty: dict of {customer_id: {description: total_qty}}.

    Returns:
        dict of {description: [partner_description, ...]} ranked best-first.
    """
    co_occurrence = defaultdict(lambda: defaultdict(int))
    for items_qty in customer_item_qty.values():
        distinct_items = sorted(items_qty.keys())
        for item_a, item_b in combinations(distinct_items, 2):
            co_occurrence[item_a][item_b] += 1
            co_occurrence[item_b][item_a] += 1

    return {
        item: [
            partner for partner, _ in sorted(
                partners.items(), key=lambda kv: (-kv[1], kv[0])
            )
        ]
        for item, partners in co_occurrence.items()
    }


def get_product_recommendations():
    """Build rule-based, per-customer product recommendations.

    For every customer:
      - No orders yet: recommend the top 3 bestsellers.
      - Has orders: take their 3 most-purchased items (by quantity,
        ties broken alphabetically). For each one, walk down its
        "frequently bought together" ranking to find the first item they
        haven't already bought (and that isn't already recommended via
        another anchor item). Any slots still empty afterward — too few
        distinct purchases, or a co-occurrence list exhausted with nothing
        new to offer — are filled from the bestseller ranking, skipping
        anything already purchased or already recommended.

    Returns:
        A list of CustomerRecommendation(customer, recommendations) ordered
        by customer last name, where recommendations is a list of up to 3
        item-description strings.
    """
    orders    = Order.query.all()
    customers = Customer.query.order_by(Customer.LastName).all()

    # Per-customer quantity purchased per item, and global totals per item.
    customer_item_qty = defaultdict(lambda: defaultdict(int))
    item_total_qty    = defaultdict(int)
    for o in orders:
        customer_item_qty[o.CustomerID][o.Description] += o.Amount
        item_total_qty[o.Description] += o.Amount

    bestsellers        = _bestseller_ranking(item_total_qty)
    co_occurrence_rank = _build_co_occurrence_ranking(customer_item_qty)

    results = []
    for customer in customers:
        purchased_qty = customer_item_qty.get(customer.CustomerID, {})

        if not purchased_qty:
            results.append(CustomerRecommendation(customer, bestsellers[:3]))
            continue

        purchased_items = set(purchased_qty.keys())

        # Top 3 most-purchased items: quantity descending, name ascending on ties.
        top_items = [
            item for item, _ in sorted(
                purchased_qty.items(), key=lambda kv: (-kv[1], kv[0])
            )[:3]
        ]

        recommendations = []
        for anchor in top_items:
            for partner in co_occurrence_rank.get(anchor, []):
                if partner not in purchased_items and partner not in recommendations:
                    recommendations.append(partner)
                    break  # one suggestion per anchor item

        # Fill any remaining slots with bestsellers not already purchased/recommended.
        for item in bestsellers:
            if len(recommendations) >= 3:
                break
            if item not in purchased_items and item not in recommendations:
                recommendations.append(item)

        results.append(CustomerRecommendation(customer, recommendations[:3]))

    return results


def get_low_performing_products(limit=10):
    """Return the lowest-performing products/services by total units sold.

    The mirror image of the bestseller ranking — sorted ascending instead
    of descending — to flag items that may need marketing support.

    Args:
        limit: Maximum number of products to return (default 10).

    Returns:
        A list of ProductPerformance(description, total_units), ascending.
    """
    orders = Order.query.all()
    item_total_qty = defaultdict(int)
    for o in orders:
        item_total_qty[o.Description] += o.Amount

    ranked = sorted(item_total_qty.items(), key=lambda kv: (kv[1], kv[0]))
    return [ProductPerformance(description, total_units) for description, total_units in ranked[:limit]]