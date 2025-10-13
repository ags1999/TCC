import psycopg2

# Connect to an existing database
conn = psycopg2.connect("dbname=ledgerBotDB user=alexandre")

# Open a cursor to perform database operations
cur = conn.cursor()

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

def register_transaction():
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