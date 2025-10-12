import pandas as pd
from psycopg2 import sql
import psycopg2
from pydantic import BaseModel
import datetime
from typing import Literal, Union
# TODO: Figure out if there is even a point in cleaning the id's if we don't technically ever use them 
# Data models for validation using Pydantic.
# We struggled initially when invalid or missing fields slipped through,
# so these catch schema errors early in parse_row().
class Product(BaseModel):
    product_name: str
    category: str
    quantity: int
    price: float

class User(BaseModel):
    first_name: str
    last_name: str
    gender: str
    age_group: str
    signup_date: datetime.date
    country: str

class UserProductInteraction(BaseModel):
    customer_id: int
    order_id: int
    product_id: int
    order_status: str
    payment_method: str

def connect_db():
    """
    Connect to PostgreSQL.  
    We printed errors here to catch bad credentials or wrong host immediately.
    """
    try:
        conn = psycopg2.connect(
            dbname="ecommerce",
            user="postgres",
            password="Eurekasan2478!",
            host="localhost",
        )
        print("Connected to the database!")
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def load_and_clean_csv(path):
    """
    Load CSV into pandas and clean the ID strings.
    We had issues when NaNs or wrong formats appeared,
    so we log dtype info and catch errors here.
    """
    try:
        df = pd.read_csv(path)
        cleaned_df = df.copy()
        # Strip the prefix (e.g. 'CUST1001' → 1001) and convert to int.
        cleaned_df["customer_id"] = cleaned_df["customer_id"].str[4:].astype(int)
        cleaned_df["order_id"]    = cleaned_df["order_id"].str[3:].astype(int)
        cleaned_df["product_id"]  = cleaned_df["product_id"].str[4:].astype(int)

        print(cleaned_df.dtypes)  # Verify types before insertion
        return cleaned_df
    except Exception as e:
        print(f"Error loading or cleaning CSV: {e}")
        return None

def create_db_tables(cur):
    """
    Create the tables with UNIQUE constraints inline.
    We originally forgot these and got ON CONFLICT errors,
    because PostgreSQL didn't know how to detect duplicates.
    Also, we must commit DDL before inserting data
    or we'll see 'relation does not exist' in the same transaction.
    """
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id SERIAL PRIMARY KEY,
            product_name VARCHAR(255),
            category VARCHAR(100),
            quantity INT,
            price FLOAT,
            CONSTRAINT unique_product UNIQUE (product_name, category, price)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            gender VARCHAR(20),
            age_group VARCHAR(50),
            signup_date DATE,
            country VARCHAR(100),
            CONSTRAINT unique_user UNIQUE (first_name, last_name, signup_date, country)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_product_interactions (
            interaction_id SERIAL PRIMARY KEY,
            customer_id INT,
            order_id INT UNIQUE,  -- ensure no duplicate order IDs
            product_id INT,
            order_status VARCHAR(50),
            payment_method VARCHAR(50),
            FOREIGN KEY (customer_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (product_id)  REFERENCES products(product_id) ON DELETE CASCADE
        )
    """)

def parse_row(row):
    """
    Convert a DataFrame row into our Pydantic models.
    We handle string dates here because pandas may load dates as strings.
    Any validation error prints and returns None triples to skip the row.
    """
    try:
        signup_date = row["signup_date"]
        if isinstance(signup_date, str):
            signup_date = datetime.datetime.strptime(signup_date, "%Y-%m-%d").date()

        product = Product(
            product_name=row["product_name"],
            category=row["category"],
            quantity=row["quantity"],
            price=row["unit_price"],
        )
        user = User(
            first_name=row["first_name"],
            last_name=row["last_name"],
            gender=row["gender"],
            age_group=row["age_group"],
            signup_date=signup_date,
            country=row["country"],
        )
        interaction = UserProductInteraction(
            customer_id=row["customer_id"],
            order_id=row["order_id"],
            product_id=row["product_id"],
            order_status=row["order_status"],
            payment_method=row["payment_method"],
        )
        return product, user, interaction

    except Exception as e:
        print(f"Validation failed: {e}")
        # Returning None signals the caller to skip this row
        return None, None, None

def insert_row_to_db(cur, product, user, interaction):
    """
    Insert one parsed row.  
    We use ON CONFLICT DO NOTHING + RETURNING to deduplicate,
    then fallback to SELECT if nothing was returned.  
    The 'raise' ensures that errors bubble up,
    so the outer function can rollback or skip appropriately.
    """
    try:
        # Product insert / dedupe
        cur.execute(
            """
            INSERT INTO products (product_name, category, quantity, price)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (product_name, category, price) DO NOTHING
            RETURNING product_id
            """,
            (product.product_name, product.category, product.quantity, product.price),
        )
        res = cur.fetchone()
        if res:
            product_id = res[0]
        else:
            # fallback select to get existing ID
            cur.execute(
                "SELECT product_id FROM products WHERE product_name=%s AND category=%s AND price=%s",
                (product.product_name, product.category, product.price),
            )
            product_id = cur.fetchone()[0]

        # User insert / dedupe
        cur.execute(
            """
            INSERT INTO users (first_name, last_name, gender, age_group, signup_date, country)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (first_name, last_name, signup_date, country) DO NOTHING
            RETURNING user_id
            """,
            (
                user.first_name,
                user.last_name,
                user.gender,
                user.age_group,
                user.signup_date,
                user.country,
            ),
        )
        res = cur.fetchone()
        if res:
            user_id = res[0]
        else:
            cur.execute(
                "SELECT user_id FROM users WHERE first_name=%s AND last_name=%s AND signup_date=%s AND country=%s",
                (user.first_name, user.last_name, user.signup_date, user.country),
            )
            user_id = cur.fetchone()[0]

        # Interaction insert (no conflict clause; order_id is UNIQUE)
        cur.execute(
            """
            INSERT INTO user_product_interactions 
                (customer_id, order_id, product_id, order_status, payment_method)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                user_id,
                interaction.order_id,
                product_id,
                interaction.order_status,
                interaction.payment_method,
            ),
        )

    except Exception as e:
        print(f"Insert failed: {e}")
        # Re-raise so insert_data_to_tables can decide to rollback the transaction
        raise

def insert_data_to_tables(conn, df):
    """
    Create tables, commit schema changes, then insert each row.
    We commit DDL first to avoid 'relation does not exist' errors
    and handle any row-level error by rolling back the batch.
    """
    cur = conn.cursor()
    try:
        create_db_tables(cur)
        conn.commit()  # commit table creation before data inserts

        for _, row in df.iterrows():
            product, user, interaction = parse_row(row)
            if product and user and interaction:
                insert_row_to_db(cur, product, user, interaction)

        conn.commit()
        print("All data inserted successfully!")
    except Exception as e:
        print(f"Error inserting data into database: {e}")
        conn.rollback()
    finally:
        cur.close()

def single_lookup(lookup: Literal['products', 'users'], item_id: int, q: Union[str, None] = None):
    conn = connect_db()
    cur = conn.cursor()

    # choose column name based on table
    id_column = "product_id" if lookup == "products" else "user_id"

    # safely compose SQL with psycopg2.sql
    query = sql.SQL("SELECT * FROM {} WHERE {} = %s").format(
        sql.Identifier(lookup),    # table name
        sql.Identifier(id_column)  # column name
    )

    cur.execute(query, (item_id,))
    result = cur.fetchone()

    cur.close()
    conn.close()

    return {"item": result, "query": q}


if __name__ == "__main__":
    conn = connect_db()
    if conn:
        cleaned_df = load_and_clean_csv(
            r"C:\Users\hollo\OneDrive\Documents\Practice\Lullia\Server\ecommerce_dataset_10000.csv"
        )
        if cleaned_df is not None:
            print(cleaned_df.head())  # Optional: preview the cleaned data

            # Show all unique product names before inserting
            unique_products = cleaned_df["product_name"].unique().tolist()
            print(f"\nUnique product names ({len(unique_products)}):")
            for name in unique_products:
                print("-", name)

            insert_data_to_tables(conn, cleaned_df)
        else:
            print("Data cleaning failed. No data inserted.")
    else:
        print("Database connection failed.")