from unicodedata import category

import psycopg2
import psycopg2.extras
import uuid
# Connect to an existing database
conn = psycopg2.connect("dbname=ledgerBotDB user=alexandre")

# Open a cursor to perform database operations
cur = conn.cursor()
psycopg2.extras.register_uuid()
def register_user(id, name):
    query = f'''SELECT EXISTS(
    SELECT 1 
    FROM users 
    WHERE users.id = %s
    )'''
    cur.execute(query, (id,))
        
        # Fetch result
    exists = cur.fetchone()[0]
    if not exists:
        insert = '''INSERT INTO users VALUES (%s, %s)'''
        cur.execute(insert, (id, name))
        conn.commit()
    print(exists)

def register_transaction(transaction):
    # User Transactions : Transaction ID, User ID, Value
    value = transaction["value"]
    user_id = transaction["ID"]
    trs_category = transaction["category"]
    trs_id =uuid.uuid4()
    try:
        insert = '''INSERT INTO user_transactions \
                VALUES (%s, %s, %s, %s)'''
        cur.execute(insert, (trs_id, user_id, value, trs_category))
        conn.commit()
        print("Successfully inserted transaction")
    except Exception as e:
        print(f"Error: {e}")
    pass

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