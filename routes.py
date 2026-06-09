"""Route handlers for the Peak Pulse Fitness web application.

Defines all URL endpoints and WTForms for the CRUD management UI.
Imports the shared Flask app instance from __init__.py to register routes.
"""
from pip._internal.commands import search

from flask import render_template, redirect, url_for, flash, request
from db import db
from flask import render_template, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, FloatField, IntegerField
from wtforms.validators import DataRequired

from models import Customer, Employee, Order

from __init__ import app

# for Student 1 Focus:
import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from sqlalchemy import func


# ---------------------------------------------------------------------------
# Forms
# ---------------------------------------------------------------------------

class CustomerForm(FlaskForm):
    """WTForm for creating and editing a Customer record."""

    FirstName = StringField('First Name', validators=[DataRequired()])
    LastName  = StringField('Last Name',  validators=[DataRequired()])
    Age       = IntegerField('Age',       validators=[DataRequired()])
    BirthDate = StringField('Birth Date (YYYY-MM-DD)', validators=[DataRequired()])
    Country   = StringField('Country',   validators=[DataRequired()])
    submit    = SubmitField('Save')


class OrderForm(FlaskForm):
    """WTForm for creating and editing an Order record.

    SelectField choices for CustomerID and EmployeeID are populated
    dynamically from the database before each render.
    """

    CustomerID  = SelectField('Customer',    coerce=int, validators=[DataRequired()])
    EmployeeID  = SelectField('Employee',    coerce=int, validators=[DataRequired()])
    Description = StringField('Description', validators=[DataRequired()])
    Price       = FloatField('Price',        validators=[DataRequired()])
    Amount      = IntegerField('Amount',     validators=[DataRequired()])
    Date        = StringField('Date (YYYY-MM-DD)', validators=[DataRequired()])
    submit      = SubmitField('Save')


class DeleteForm(FlaskForm):
    """Minimal form used solely to provide CSRF protection for delete buttons."""

    submit = SubmitField('Delete')


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _populate_order_choices(form):
    """Fill SelectField choices for OrderForm from the database.

    Args:
        form: An OrderForm instance whose choices should be populated.
    """
    form.CustomerID.choices = [
        (c.CustomerID, f'{c.FirstName} {c.LastName}')
        for c in Customer.query.order_by(Customer.LastName).all()
    ]
    form.EmployeeID.choices = [
        (e.EmployeeID, f'{e.FirstName} {e.LastName}')
        for e in Employee.query.order_by(Employee.LastName).all()
    ]


# ---------------------------------------------------------------------------
# General
# ---------------------------------------------------------------------------

@app.route('/')
def home():
    """Render the home page.
    """
    return render_template('home.html')


# ---------------------------------------------------------------------------
# Customer CRUD
# ---------------------------------------------------------------------------

@app.route('/customers')
def customer_list():
    """
    Display all customers with dynamic sorting.

    Accepts optional query parameters:
        - sort (str): Column key to sort by. Defaults to 'last_name'.
        - dir  (str): Sort direction, either 'asc' or 'desc'. Defaults to 'asc'.
        - search (str): Optional search string filtered across all relevant columns.

    Returns:
        Rendered HTML template with the customer's list and active sort/search state.

    Whitelist of allowed sort keys mapped to the corresponding Customer model column.
    All columns belong to the Customer table, so no JOIN is required.
    """

    SORT_COLUMNS = {
        'id':         Customer.CustomerID,
        'first_name': Customer.FirstName,
        'last_name':  Customer.LastName,
        'age':        Customer.Age,
        'country':    Customer.Country,
    }
    VALID_DIRECTIONS = {'asc', 'desc'}

    # Read sort parameters from the URL query string
    sort_by  = request.args.get('sort', 'id')
    sort_dir = request.args.get('dir',  'asc')
    search = request.args.get('search', '').strip()

    # Fall back to safe defaults if an invalid value is provided
    if sort_by  not in SORT_COLUMNS:     sort_by  = 'id'
    if sort_dir not in VALID_DIRECTIONS: sort_dir = 'asc'

    column     = SORT_COLUMNS[sort_by]
    order_expr = column.asc() if sort_dir == 'asc' else column.desc()

    query   = Customer.query

    # Apply search filter across all customer columns
    if search:
        term = f"%{search}%"
        query = query.filter(
            db.or_(
                Customer.FirstName.ilike(term),
                Customer.LastName.ilike(term),
                Customer.Age.ilike(term),
                Customer.BirthDate.ilike(term),
                Customer.Country.ilike(term),
                db.cast(Customer.CustomerID, db.String).ilike(term),
            )
        )

    customers = query.order_by(order_expr).all()
    delete_form = DeleteForm()

    return render_template(
        'customers/list.html',
        customers=customers,
        delete_form=delete_form,
        sort_by=sort_by,
        sort_dir=sort_dir,
        search=search,
    )


@app.route('/customers/create', methods=['GET', 'POST'])
def customer_create():
    """Show and process the create-customer form."""
    form = CustomerForm()
    if form.validate_on_submit():
        customer = Customer(
            FirstName=form.FirstName.data,
            LastName=form.LastName.data,
            Age=form.Age.data,
            BirthDate=form.BirthDate.data,
            Country=form.Country.data,
        )
        db.session.add(customer)
        db.session.commit()
        flash('Customer created.', 'success')
        return redirect(url_for('customer_list'))
    return render_template('customers/form.html', form=form, title='New Customer')


@app.route('/customers/<int:customer_id>/edit', methods=['GET', 'POST'])
def customer_edit(customer_id):
    """Show and process the edit-customer form.

    Args:
        customer_id: Primary key of the customer to edit.
    """
    customer = Customer.query.get_or_404(customer_id)
    form     = CustomerForm(obj=customer)
    if form.validate_on_submit():
        customer.FirstName = form.FirstName.data
        customer.LastName  = form.LastName.data
        customer.Age       = form.Age.data
        customer.BirthDate = form.BirthDate.data
        customer.Country   = form.Country.data
        db.session.commit()
        flash('Customer updated.', 'success')
        return redirect(url_for('customer_list'))
    return render_template('customers/form.html', form=form, title='Edit Customer')


@app.route('/customers/<int:customer_id>/delete', methods=['POST'])
def customer_delete(customer_id):
    """Delete a customer record.

    Args:
        customer_id: Primary key of the customer to delete.
    """
    customer = Customer.query.get_or_404(customer_id)
    form     = DeleteForm()
    if form.validate_on_submit():
        db.session.delete(customer)
        db.session.commit()
        flash('Customer deleted.', 'success')
    return redirect(url_for('customer_list'))


# ---------------------------------------------------------------------------
# Order CRUD
# ---------------------------------------------------------------------------

@app.route('/orders')
def order_list():
    """
    Display all orders with dynamic sorting.

    Accepts optional query parameters:
        - sort (str): Column key to sort by. Defaults to 'id'.
        - dir  (str): Sort direction, either 'asc' or 'desc'. Defaults to 'asc'.
        - search (str): Optional search string filtered across all relevant columns.

    Returns:
        Rendered HTML template with the order list and active sort/search state.

    Whitelist of allowed sort keys mapped to (model column, join model).
    join model is None if the column belongs to the Order table itself.
    """
    SORT_COLUMNS = {
        'id':          (Order.OrderID,      None),
        'customer':    (Customer.LastName,  Customer),
        'employee':    (Employee.LastName,  Employee),
        'description': (Order.Description,  None),
        'price':       (Order.Price,        None),
        'amount':      (Order.Amount,       None),
        'date':        (Order.Date,         None),
    }
    VALID_DIRECTIONS = {'asc', 'desc'}

    # Read sort parameters from the URL query string
    sort_by  = request.args.get('sort', 'id')
    sort_dir = request.args.get('dir',  'asc')
    search   = request.args.get('search', '').strip()

    # Fall back to safe defaults if an invalid value is provided
    if sort_by  not in SORT_COLUMNS:     sort_by  = 'id'
    if sort_dir not in VALID_DIRECTIONS: sort_dir = 'asc'

    column, join_model = SORT_COLUMNS[sort_by]
    order_expr = column.asc() if sort_dir == 'asc' else column.desc()

    # Build the query; only JOIN a related table when sorting by its column
    query = (
        Order.query
        .join(Customer)
        .join(Employee)
    )
    '''Apply search filter across all relevant columns using a case-insensitive
    LIKE match. Each column is cast to String so numeric fields (price,
    amount) can also be matched against the search term.
    '''
    if search:
        term = f"%{search}%"
        query = query.filter(
            db.or_(
                Customer.FirstName.ilike(term),
                Customer.LastName.ilike(term),
                Employee.FirstName.ilike(term),
                Employee.LastName.ilike(term),
                Order.Description.ilike(term),
                db.cast(Order.Price, db.String).ilike(term),
                db.cast(Order.Amount, db.String).ilike(term),
                db.cast(Order.Date, db.String).ilike(term),
            )
        )

    orders      = query.order_by(order_expr).all()
    delete_form = DeleteForm()

    return render_template(
        'orders/list.html',
        orders=orders,
        delete_form=delete_form,
        sort_by=sort_by,
        sort_dir=sort_dir,
        search=search,
    )


@app.route('/orders/create', methods=['GET', 'POST'])
def order_create():
    """Show and process the create-order form."""
    form = OrderForm()
    _populate_order_choices(form)
    if form.validate_on_submit():
        order = Order(
            CustomerID=form.CustomerID.data,
            EmployeeID=form.EmployeeID.data,
            Description=form.Description.data,
            Price=form.Price.data,
            Amount=form.Amount.data,
            Date=form.Date.data,
        )
        db.session.add(order)
        db.session.commit()
        flash('Order created.', 'success')
        return redirect(url_for('order_list'))
    return render_template('orders/form.html', form=form, title='New Order')


@app.route('/orders/<int:order_id>/edit', methods=['GET', 'POST'])
def order_edit(order_id):
    """Show and process the edit-order form.

    Args:
        order_id: Primary key of the order to edit.
    """
    order = Order.query.get_or_404(order_id)
    form  = OrderForm(obj=order)
    _populate_order_choices(form)
    if form.validate_on_submit():
        order.CustomerID  = form.CustomerID.data
        order.EmployeeID  = form.EmployeeID.data
        order.Description = form.Description.data
        order.Price       = form.Price.data
        order.Amount      = form.Amount.data
        order.Date        = form.Date.data
        db.session.commit()
        flash('Order updated.', 'success')
        return redirect(url_for('order_list'))
    return render_template('orders/form.html', form=form, title='Edit Order')


@app.route('/orders/<int:order_id>/delete', methods=['POST'])
def order_delete(order_id):
    """Delete an order record.

    Args:
        order_id: Primary key of the order to delete.
    """
    order = Order.query.get_or_404(order_id)
    form  = DeleteForm()
    if form.validate_on_submit():
        db.session.delete(order)
        db.session.commit()
        flash('Order deleted.', 'success')
    return redirect(url_for('order_list'))

@app.route('/dashboard')
def dashboard():
    generate_dashboard_plots()

    return render_template('analytics_stud1/dashboard.html')


# for Student 1 Focus:
def generate_dashboard_plots():
    """
    Generate and save both dashboard plots as PNG files to static/plots/.

    Uses SQLAlchemy connection directly (compatible with Pandas 2.x+).
    Plot 1: Customer geographic distribution (bar chart by country).
    Plot 2: Age group vs. average spending (bar chart).
    """
    plots_dir = os.path.join(os.path.dirname(__file__),'Student1_Focus_plots', 'static', 'plots')
    os.makedirs(plots_dir, exist_ok=True)

    engine = db.get_engine()
    with engine.connect() as conn:
        customers = pd.read_sql_table('Customer_data', conn)
        orders = pd.read_sql_table('Order_data', conn)



    # Plot 1: Customer origin bar chart
    country_counts = customers['Country'].value_counts()

    fig, ax = plt.subplots(figsize=(8,4))
    country_counts.plot(kind='bar', ax=ax, color='#2d6a2d', edgecolor='white')
    ax.set_title('Customer Geographic Distribution', fontsize=14, fontweight='bold')
    ax.set_xlabel('Country')
    ax.set_ylabel('Number of Customers')
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    fig.savefig(os.path.join(plots_dir, 'customer_origin.png'), dpi=120)
    plt.close(fig)



    # Plot 2: Age Group vs. Average Spending
    merged = orders.merge(customers[['CustomerID', 'Age']], on='CustomerID', how='left')

    # Calculate total spending per order row (Price × Amount)
    merged['total'] = merged['Price'] * merged['Amount']

    # Group customers into age buckets
    bins   = [0, 18, 25, 35, 45, 55, 100]
    labels = ['<18', '18-25', '26-35', '36-45', '46-55', '55+']
    merged['age_group'] = pd.cut(merged['Age'], bins=bins, labels=labels, right=True)

    # Calculate average total spending per age group
    age_spending = merged.groupby('age_group', observed=True)['total'].mean()

    fig, ax = plt.subplots(figsize=(8, 4))
    age_spending.plot(kind='bar', ax=ax, color='#f0a500', edgecolor='white')
    ax.set_title('Average Spending by Age Group', fontsize=14, fontweight='bold')
    ax.set_xlabel('Age Group')
    ax.set_ylabel('Average Order Value (€)')
    ax.tick_params(axis='x', rotation=0)
    plt.tight_layout()
    fig.savefig(os.path.join(plots_dir, 'age_vs_spending.png'), dpi=120)
    plt.close(fig)

@app.route('/leaderboard')
def leaderboard():
    """
    Render the customer leaderboard page.

    Leaderboard A: Top customers by number of orders (frequency).
    Leaderboard B: Top customers by total revenue generated (spending).
    """
    # Leaderboard A: top 10 customers by transaction count
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

    # Leaderboard B: top 10 customers by total revenue (Price × Amount)
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

    return render_template(
        'analytics_stud1/leaderboard.html',
        top_frequency=top_frequency,
        top_revenue=top_revenue,
    )

@app.route('/campaigns')
def campaigns():
    """
    Render the automated customer campaigns page.

    Campaign 1: Birthday reminders — customers whose birth month
                matches the current calendar month.
    Campaign 2: Inactive accounts — customers with no orders
                in the past 6 months.
    """
    today         = datetime.today()
    current_month = today.month
    cutoff_date   = today - timedelta(days=182)  # ~6 months ago

    all_customers = Customer.query.all()
    all_orders    = Order.query.all()

    # Campaign 1: match birth month against current month using string slicing.
    # BirthDate format is 'YYYY-MM-DD', so [5:7] extracts the month as a string.
    birthday_customers = [
        c for c in all_customers
        if c.BirthDate and int(c.BirthDate[5:7]) == current_month
    ]

    # Build a set of CustomerIDs that have at least one recent order
    active_ids = {
        o.CustomerID for o in all_orders
        if o.Date and datetime.strptime(o.Date, '%Y-%m-%d') >= cutoff_date
    }

    # Campaign 2: customers NOT in the active set are considered inactive
    inactive_customers = [
        c for c in all_customers
        if c.CustomerID not in active_ids
    ]

    return render_template(
        'analytics_stud1/campaigns.html',
        birthday_customers=birthday_customers,
        inactive_customers=inactive_customers,
        current_month=today.strftime('%B'),   # e.g. "June"
    )