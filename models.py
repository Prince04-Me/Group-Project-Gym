from db import db

class Customer(db.Model):
    __tablename__ = 'customer_data'
    Customer_ID = db.Column(db.Integer, primary_key=True)
    FirstName = db.Column(db.String(50))
    LastName = db.Column(db.String(50))
    Age = db.Column(db.Integer)
    BirthDate = db.Column(db.Date)
    Country = db.Column(db.String(50))
    

