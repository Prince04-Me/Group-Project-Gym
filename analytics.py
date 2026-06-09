import os
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd

#connecting to the database(ref. see test_connections.py)
basedir = os.path.abspath(os.path.dirname(__file__))
conn = sqlite3.connect(os.path.join(basedir, '', '5_gym_fitness', '5_gym_fitness.db'))
cursor = conn.cursor()
# Query the needed data from table, here product name(description) and price
# could aggregate the data in pandas directly
# but works better for large databases to let the db do the heavy lifting
df= pd.read_sql_query('''
    SELECT Description, SUM (Amount) as Total
    FROM Order_data
    GROUP BY Description
    ORDER BY Total DESC
    LIMIT 10;
    ''',conn)

# Setting the labels
# Use of barh(horizontal bars) b/c the names are long
# Could equally use the code on line 29 to just rotate the names
fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(df['Description'], df['Total'])
ax.set_xlabel('Total Units Sold')
ax.set_title('Top 10 Most Popular Products & Services')
# plt.xticks(rotation=45, ha='right')
plt.savefig(os.path.join(basedir, '', 'static', 'Top_10_Bestsellers.png'))
plt.tight_layout()


df1 = pd.read_sql('''
    SELECT 
        CASE DepartmentID
            WHEN 100 THEN 'Executive'
            WHEN 101 THEN 'Department 101'
            WHEN 102 THEN 'Department 102'
        END AS Department,
        COUNT(*) AS Total
    FROM Employees_data
    GROUP BY DepartmentID
''', conn)
conn.close()

fig1, ax1 = plt.subplots(figsize=(10, 6))
ax1.pie(df1['Total'], labels=df1['Department'], autopct='%1.1f%%')
ax1.set_title('Staff Distribution by Department')
plt.savefig(os.path.join(basedir, '', 'static', 'Staff_Distribution.png'))

plt.show()