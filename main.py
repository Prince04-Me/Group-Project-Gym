from flask import Flask
from db import db
# Creating the web app
app = Flask(__name__)

# Connecting Flask to the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///5_gym_fitness/5_gym_fitness.db.sqlite3'
# Initialization of the app
db.init_app(app)

from models import Customer

# Defines a URL route with an intern function
@app.route('/')
def home():
    return 'Welcome to Peak Pulse Fitness!'



@app.route('/customers')
def customers():
    customers = Customer.query.limit(10).all()

    result = ''
    for c in customers:
        result += f'{c.FirstName} {c.LastName}<br>'

        return result

if __name__ == '__main__':
    app.run(debug=True)
