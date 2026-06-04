import sqlite3

# Step one: Connecting to the database
conn = sqlite3.connect('5_gym_fitness/5_gym_fitness.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_Master WHERE type = "table";')
# Testing if connection is successful
print(cursor.fetchall())
# Reading the data from a table
cursor.execute('SELECT * FROM Customer_data LIMIT 5;')
rows = cursor.fetchall()
for row in rows:
    print(row)