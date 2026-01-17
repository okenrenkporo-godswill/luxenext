from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not found in .env")
    exit(1)

engine = create_engine(DATABASE_URL)

sql = """
INSERT INTO payment_options (name, provider, account_name, account_number, is_active)
VALUES ('Paystack', 'paystack', NULL, NULL, True)
ON CONFLICT DO NOTHING;
"""

try:
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    print("Successfully added Paystack payment option")
except Exception as e:
    # If ON CONFLICT DO NOTHING fails because of no unique constraint, try checking existence first
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT id FROM payment_options WHERE provider = 'paystack'")).fetchone()
            if not result:
                conn.execute(text("INSERT INTO payment_options (name, provider, is_active) VALUES ('Paystack', 'paystack', True)"))
                conn.commit()
                print("Successfully added Paystack payment option (manual check)")
            else:
                print("Paystack payment option already exists")
    except Exception as e2:
        print(f"Error updating database: {str(e2)}")
