from unicodedata import category

import psycopg2
from psycopg2 import sql
import psycopg2.extras
import uuid
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
# Connect to an existing database
conn = psycopg2.connect("dbname=ledgerBotDB user=alexandre")

# Open a cursor to perform database operations
cur = conn.cursor()
psycopg2.extras.register_uuid()
def register_user(id, name):
    query = f'''SELECT EXISTS(
    SELECT 1 
    FROM users 
    WHERE users.user_id = %s
    )'''
    cur.execute(query, (id,))
        
        # Fetch result
    exists = cur.fetchone()[0]
    if not exists:
        insert = '''INSERT INTO users(user_id, username) VALUES (%s, %s)'''
        cur.execute(insert, (id, name))
        conn.commit()
    print(exists)

#TODO register date
def register_transaction(transaction):
    # User Transactions : Transaction ID, User ID, Value, Category, Date, Description
    trs_id =uuid.uuid4()
    user_id = transaction["ID"]
    value = transaction["value"]
    trs_category = transaction["category"]
    trs_date = transaction["date"]
    if "description" in transaction:
        trs_description = transaction["description"]
    else:
        trs_description = None
    try:
        insert = '''INSERT INTO transactions(transactions_id, user_id, value, category, date, description) \
                VALUES (%s, %s, %s, %s, %s, %s)'''
        cur.execute(insert, (trs_id, user_id, value, trs_category, trs_date, trs_description))
        conn.commit()
        print("Successfully inserted transaction")
    except Exception as e:
        print(f"Error: {e}")
    pass

def retorna_consulta(user_id):
#def retorna_consulta(user_id, min_value, max_value, min_date, max_date, categories):
    query = '''SELECT * FROM transactions WHERE'''


    min_value = None
    max_value= None
    min_date = None
    max_date = None
    categories = ["Mercado", "Contas", "Outros"]
    conditions=[]
    conditions.append("user_id = %s")
    params=[]
    params.append(user_id)
    # Date range
    if min_date is not None:
        conditions.append("date >= %s")
        params.append(min_date)
    if max_date is not None:
        conditions.append("date <= %s")
        params.append(max_date)

    # Numeric range (price, score, etc.)
    if min_value is not None:
        conditions.append("value >= %s")
        params.append(min_price)
    if max_value is not None:
        conditions.append("value <= %s")
        params.append(max_price)

    # Categories
    if categories is not None:
        conditions.append("category in %s")
        params.append(tuple(categories))

    # Add other filters similarly...
    # if some_text:
    #     conditions.append("name ILIKE %s")
    #     params.append(f"%{some_text}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    print(query)
    cur.execute(query, params)
    results = cur.fetchall()
    print(results)
    return "test"

    '''
    df = pd.read_sql(query, conn)
    fig, ax = plt.subplots(figsize=(10,10))
    ax.axis('off')
    table = ax.table(cellText=df.values, colLabels=df.columns, loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.2)
    with PdfPages("transactions.pdf") as pdf:
        pdf.savefig(fig)
    plt.close(fig)
    '''
def consulta_ano_mes(user_id, ano, mes):
    sql_query = """
                SELECT * \
                FROM transactions
                WHERE user_id = %s \
                  AND EXTRACT(YEAR FROM date) = %s \
                  AND EXTRACT(MONTH FROM date) = %s; \
                """
    params = [user_id, int(ano), int(mes)]
    print(params)
'''
# Execute a command: this creates a new table
#cur.execute("CREATE TABLE test (id serial PRIMARY KEY, num integer, data varchar);")

# Pass data to fill a query placeholders and let Psycopg perform
# the correct conversion (no more SQL injections!)
#cur.execute("INSERT INTO test (num, data) VALUES (%s, %s)",(100, "abc'def"))


# Query the database and obtain data as Python objects
cur.execute("SELECT * FROM test;")
print(cur.fetchall())


# Make the changes to the database persistent
#conn.commit()

# Close communication with the database
cur.close()
conn.close()
'''