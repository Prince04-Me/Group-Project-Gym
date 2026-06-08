"""SQLAlchemy ORM models for the Peak Pulse Fitness application.

Maps the three existing database tables to Python classes:
  - Customer  →  Customer_data
  - Employee  →  Employees_data
  - Order     →  Order_data
"""
from db import db


class Customer(db.Model):
    """Represents a gym customer (Table A — primary entity).

    Attributes:
        CustomerID: Primary key.
        FirstName:  Customer's first name.
        LastName:   Customer's last name.
        Age:        Age in years.
        BirthDate:  Date of birth stored as ISO string (YYYY-MM-DD).
        Country:    Country of residence.
        orders:     All orders placed by this customer (One-to-Many).
    """

    __tablename__ = 'Customer_data'

    CustomerID = db.Column(db.Integer, primary_key=True)
    FirstName  = db.Column(db.String, nullable=False)
    LastName   = db.Column(db.String, nullable=False)
    Age        = db.Column(db.Integer, nullable=False)
    BirthDate  = db.Column(db.String, nullable=False)
    Country    = db.Column(db.String, nullable=False)

    orders = db.relationship('Order', back_populates='customer')


class Employee(db.Model):
    """Represents a gym employee (Table C — resource data).

    Attributes:
        EmployeeID:   Primary key.
        Name:         First name.
        LastName:     Last name.
        Email:        Work e-mail address.
        Age:          Age in years.
        Country:      Country of residence.
        HireDate:     Start date stored as ISO string (YYYY-MM-DD).
        JobID:        Job role identifier.
        Salary:       Monthly gross salary.
        ManagerID:    Self-referencing FK — EmployeeID of direct supervisor (nullable).
        DepartmentID: Department identifier.
        manager:      Employee object of the direct supervisor.
        orders:       All orders handled by this employee (One-to-Many).
    """

    __tablename__ = 'Employees_data'

    EmployeeID   = db.Column(db.Integer, primary_key=True, unique=True)
    FirstName    = db.Column(db.String, nullable=False)
    LastName     = db.Column(db.String, nullable=False)
    Email        = db.Column(db.String, nullable=False)
    Age          = db.Column(db.Integer, nullable=False)
    Country      = db.Column(db.String, nullable=False)
    HireDate     = db.Column(db.String, nullable=False)
    JobID        = db.Column(db.String, nullable=False)
    Salary       = db.Column(db.Float, nullable=False)
    ManagerID    = db.Column(db.Integer, db.ForeignKey('Employees_data.EmployeeID'), nullable=True)
    DepartmentID = db.Column(db.Integer, nullable=False)

    # Self-referencing relationship: points to the supervising Employee
    manager = db.relationship('Employee', remote_side='Employee.EmployeeID', foreign_keys=[ManagerID])
    orders  = db.relationship('Order', back_populates='employee')


class Order(db.Model):
    """Represents a gym service order (Table B — transaction data).

    Links a Customer to an Employee for a specific service purchase.

    Attributes:
        OrderID:     Primary key.
        CustomerID:  FK to Customer_data.CustomerID.
        EmployeeID:  FK to Employees_data.EmployeeID.
        Description: Description of the service or product ordered.
        Price:       Unit price in local currency.
        Amount:      Quantity ordered.
        Date:        Order date stored as ISO string (YYYY-MM-DD).
        customer:    Related Customer object.
        employee:    Related Employee object.
    """

    __tablename__ = 'Order_data'

    OrderID     = db.Column(db.Integer, primary_key=True)
    CustomerID  = db.Column(db.Integer, db.ForeignKey('Customer_data.CustomerID'), nullable=False)
    EmployeeID  = db.Column(db.Integer, db.ForeignKey('Employees_data.EmployeeID'), nullable=False)
    Description = db.Column(db.String, nullable=False)
    Price       = db.Column(db.Float, nullable=False)
    Amount      = db.Column(db.Integer, nullable=False)
    Date        = db.Column(db.String, nullable=False)

    customer = db.relationship('Customer', back_populates='orders')
    employee = db.relationship('Employee', back_populates='orders')
