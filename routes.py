"""Route handlers for the Peak Pulse Fitness web application.

Defines all URL endpoints and WTForms for the CRUD management UI.
Imports the shared Flask app instance from __init__.py to register routes.
"""
from pip._internal.commands import search

from __init__ import app, db
from flask import render_template, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, FloatField, IntegerField
from wtforms.validators import DataRequired

from models import Customer, Employee, Order


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
    """Render the home page."""
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
