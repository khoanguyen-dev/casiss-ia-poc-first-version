import psycopg2

# Connect to your PostgreSQL database
conn = psycopg2.connect(
    dbname="casiss_ia",
    user="khoa",
    password="k123",
    host="localhost",  # Change to your database host
    port="5432"        # Change to your database port if different
)

# Create a cursor object
cur = conn.cursor()

# SQL command to create the table
create_table_query = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE navisante (
    content TEXT,
    embedding VECTOR(3584),
    source TEXT PRIMARY KEY,
    keywords TEXT[]
);
"""

try:
    # Execute the create table command
    cur.execute(create_table_query)
    conn.commit()
    print("Table 'navisante' created successfully!")
except Exception as e:
    print(f"Error creating table: {e}")
finally:
    # Close the cursor and connection
    cur.close()
    conn.close()
