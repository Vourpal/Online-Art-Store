import pandas as pd
import psycopg2

# Connect to PostgreSQL
try:
    conn = psycopg2.connect(
        dbname="learning",
        user="postgres",
        password="Eurekasan2478!",
        host="localhost",
    )
    print("Connected to the database!")
except Exception as e:
    print(f"Error connecting to database: {e}")

cur = conn.cursor()

# Function to create the table if it doesn't exist
def create_table():
    cur.execute("""
        CREATE TABLE IF NOT EXISTS store (
            item_id SERIAL PRIMARY KEY,
            item VARCHAR(150) NOT NULL,
            item_description VARCHAR(500),
            availability BOOLEAN DEFAULT FALSE,
            price NUMERIC(10,2) NOT NULL
        )
    """)
    conn.commit()
    print("Table created (if it didn't exist).")

# Function to insert a DataFrame into the store table
def insert_dataframe(df: pd.DataFrame, n_rows: int = None):
    """
    Inserts rows from a DataFrame into the store table.

    Parameters:
    - df: pandas DataFrame containing CSV data
    - n_rows: how many rows to insert (None = all rows)
    """
    rows_to_insert = df.head(n_rows) if n_rows else df

    for _, row in rows_to_insert.iterrows():
        # Map columns from CSV to table
        item_name = f"{row['brand']} {row['product_name']}"[:150]
        item_description = str(row['product_description'])[:500]
        availability = True if str(row['stock_info']).lower() == "in stock online" else False
        price = float(row['price'])

        cur.execute(
            "INSERT INTO store (item, item_description, availability, price) VALUES (%s, %s, %s, %s)",
            (item_name, item_description, availability, price)
        )

    conn.commit()
    print(f"Inserted {len(rows_to_insert)} rows successfully!")


def obtain_100_rows():
    cur.execute("SELECT * FROM store LIMIT 100")
    rows = cur.fetchall()
    return rows

# Example usage
if __name__ == "__main__":
    create_table()
    df = pd.read_csv("./Art_Materials.csv")  # adjust path if needed
    insert_dataframe(df) #only run once for now
