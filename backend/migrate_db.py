import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def migrate():
    with engine.connect() as conn:
        def try_execute(sql, success_msg, err_msg):
            try:
                conn.execute(text(sql))
                conn.commit()
                print(success_msg)
            except Exception as e:
                conn.rollback()
                print(f"{err_msg}: {e}")

        try_execute("ALTER TABLE trips ADD COLUMN currency VARCHAR DEFAULT 'USD'", "Added currency column.", "Error adding currency")
        try_execute("ALTER TABLE trips ADD COLUMN group_size INTEGER DEFAULT 1", "Added group_size column.", "Error adding group_size")
        try_execute("ALTER TABLE trips ADD COLUMN travel_style VARCHAR DEFAULT 'solo'", "Added travel_style column.", "Error adding travel_style")

        # v2 Columns - Trips
        v2_trip_cols = [
            "carbon_footprint FLOAT DEFAULT 0.0",
            "sustainability_score FLOAT DEFAULT 0.0",
            "current_mood VARCHAR",
            "is_group_trip BOOLEAN DEFAULT FALSE"
        ]
        for col in v2_trip_cols:
            col_name = col.split()[0]
            try_execute(f"ALTER TABLE trips ADD COLUMN {col}", f"Added {col_name} to trips.", f"Error adding {col_name}")

        # v2 Columns - Users
        v2_user_cols = [
            "dietary_preferences VARCHAR",
            "allergies VARCHAR",
            "accessibility_needs VARCHAR",
            "nationality VARCHAR",
            "passport_expiry TIMESTAMP WITH TIME ZONE"
        ]
        for col in v2_user_cols:
            col_name = col.split()[0]
            try_execute(f"ALTER TABLE users ADD COLUMN {col}", f"Added {col_name} to users.", f"Error adding {col_name}")

        # v2 Columns - Expenses
        try_execute("ALTER TABLE expenses ADD COLUMN paid_by_user_id INTEGER REFERENCES users(id)", "Added paid_by_user_id to expenses.", "Error adding paid_by_user_id")

if __name__ == "__main__":
    migrate()
