import pandas as pd
import psycopg2
from pydantic import BaseModel
import datetime


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
    order_id: int


class UserProductInteraction(BaseModel):
    customer_id: int
    order_id: int
    product_id: int
    order_status: str
    payment_method: str


def connect_db():
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
    try:
        df = pd.read_csv(path)
        cleaned_df = df.copy()
        cleaned_df['customer_id'] = cleaned_df['customer_id'].str[4:].astype(
            int)
        cleaned_df['order_id'] = cleaned_df['order_id'].str[3:].astype(int)
        cleaned_df['product_id'] = cleaned_df['product_id'].str[4:].astype(int)

        print(cleaned_df.dtypes)
        return cleaned_df
    except Exception as e:
        print(f"Error loading or cleaning CSV: {e}")
        return None, None

#TODO: probably split creating the tables and inserting the data into separate functions

#TODO: Figure out how to make the product and user id's connect to each other (also take into account your pydantic objects)

def csv_to_db(conn, df):
    try:
        cur = conn.cursor()

        # Create tables if they don't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id SERIAL PRIMARY KEY,
                product_name VARCHAR(255),
                category VARCHAR(100),
                quantity INT,
                price FLOAT
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
                order_id INT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_product_interactions (
                interaction_id SERIAL PRIMARY KEY,
                customer_id INT,
                order_id INT,
                product_id INT,
                order_status VARCHAR(50),
                payment_method VARCHAR(50)
            )
        """)

        # Insert data row by row
        for _, row in df.iterrows():
            try:
                # Validate and parse with Pydantic
                product = Product(
                    product_name=row['product_name'],
                    category=row['category'],
                    quantity=row['quantity'],
                    price=row['unit_price']
                )

                signup_date = row['signup_date']
                if isinstance(signup_date, str):
                    signup_date = datetime.datetime.strptime(signup_date, "%Y-%m-%d").date()

                user = User(
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    gender=row['gender'],
                    age_group=row['age_group'],
                    signup_date=signup_date,
                    country=row['country'],
                    order_id=row['order_id']
                )

                interaction = UserProductInteraction(
                    customer_id=row['customer_id'],
                    order_id=row['order_id'],
                    product_id=row['product_id'],
                    order_status=row['order_status'],
                    payment_method=row['payment_method']
                )

                # Insert into products
                cur.execute("""
                    INSERT INTO products (product_name, category, quantity, price)
                    VALUES (%s, %s, %s, %s)
                """, (
                    product.product_name,
                    product.category,
                    product.quantity,
                    product.price
                ))

                # Insert into users
                cur.execute("""
                    INSERT INTO users (first_name, last_name, gender, age_group, signup_date, country, order_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    user.first_name,
                    user.last_name,
                    user.gender,
                    user.age_group,
                    user.signup_date,
                    user.country,
                    user.order_id
                ))

                # Insert into interactions
                cur.execute("""
                    INSERT INTO user_product_interactions (customer_id, order_id, product_id, order_status, payment_method)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    interaction.customer_id,
                    interaction.order_id,
                    interaction.product_id,
                    interaction.order_status,
                    interaction.payment_method
                ))

            except Exception as row_error:
                print(f"Row failed: {row_error}")

        conn.commit()
        print("All data inserted successfully!")

    except Exception as e:
        print(f"Error inserting data into database: {e}")
        conn.rollback()


if __name__ == "__main__":
    conn = connect_db()
    if conn:
        cur = conn.cursor()
    cleaned_df = load_and_clean_csv(
        r"C:\Users\hollo\OneDrive\Documents\Practice\Lullia\Server\ecommerce_dataset_10000.csv")
    csv_to_db(conn, cleaned_df)
    print(cleaned_df.head())
