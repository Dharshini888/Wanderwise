import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(DATABASE_URL)

def migrate():
    print("Starting WanderWise Database Migration & Schema Synchronization...")
    
    # First, create all missing tables defined in Base metadata
    from app.database.connection import Base
    import app.models  # Ensures all models are registered
    Base.metadata.create_all(bind=engine)
    print("[OK] Base.metadata.create_all executed.")

    with engine.connect() as conn:
        def add_column_if_missing(table, col_name, col_type_def):
            sql = f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col_name} {col_type_def};"
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"[OK] Ensured column '{col_name}' on table '{table}'.")
            except Exception as e:
                conn.rollback()
                print(f"[ERROR] Error ensuring '{col_name}' on '{table}': {e}")

        # 1. Users Table Columns
        user_columns = [
            ("role", "VARCHAR DEFAULT 'USER' NOT NULL"),
            ("profile_completed", "BOOLEAN DEFAULT FALSE NOT NULL"),
            ("avatar_url", "VARCHAR"),
            ("profile_picture", "VARCHAR"),
            ("is_active", "BOOLEAN DEFAULT TRUE"),
            ("last_login_at", "TIMESTAMP WITH TIME ZONE"),
            ("phone_number", "VARCHAR"),
            ("travel_preference", "VARCHAR"),
            ("dietary_preferences", "VARCHAR"),
            ("allergies", "VARCHAR"),
            ("accessibility_needs", "VARCHAR"),
            ("nationality", "VARCHAR"),
            ("passport_expiry", "TIMESTAMP WITH TIME ZONE"),
            ("preferred_budget", "VARCHAR"),
            ("currency", "VARCHAR DEFAULT 'USD'"),
            ("travel_styles", "VARCHAR"),
            ("preferred_climate", "VARCHAR"),
            ("preferred_activities", "VARCHAR"),
            ("languages", "VARCHAR"),
        ]
        for col_name, col_def in user_columns:
            add_column_if_missing("users", col_name, col_def)

        # 2. Trips Table Columns
        trip_columns = [
            ("title", "VARCHAR"),
            ("country", "VARCHAR"),
            ("origin_city", "VARCHAR DEFAULT 'Coimbatore'"),
            ("origin_airport", "VARCHAR"),
            ("destination_airport", "VARCHAR"),
            ("currency", "VARCHAR DEFAULT 'USD'"),
            ("travel_type", "VARCHAR"),
            ("travel_style", "VARCHAR DEFAULT 'solo'"),
            ("transportation", "VARCHAR DEFAULT 'flight'"),
            ("accommodation_preference", "VARCHAR DEFAULT 'hotel'"),
            ("travel_companion", "VARCHAR"),
            ("group_size", "INTEGER DEFAULT 1"),
            ("interests", "VARCHAR"),
            ("visibility", "VARCHAR DEFAULT 'private'"),
            ("notes", "TEXT"),
            ("itinerary", "TEXT"),
            ("status", "VARCHAR DEFAULT 'Upcoming'"),
            ("is_favorite", "BOOLEAN DEFAULT FALSE"),
            ("is_archived", "BOOLEAN DEFAULT FALSE"),
            ("color_theme", "VARCHAR DEFAULT 'blue'"),
            ("image_url", "VARCHAR"),
            ("share_token", "VARCHAR UNIQUE"),
            ("carbon_footprint", "FLOAT DEFAULT 0.0"),
            ("sustainability_score", "FLOAT DEFAULT 0.0"),
            ("current_mood", "VARCHAR"),
            ("is_group_trip", "BOOLEAN DEFAULT FALSE"),
            ("trip_preferences", "JSONB"),
            ("created_at", "TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "TIMESTAMP WITH TIME ZONE"),
            ("last_opened_at", "TIMESTAMP WITH TIME ZONE"),
        ]
        for col_name, col_def in trip_columns:
            add_column_if_missing("trips", col_name, col_def)

        # 3. Itinerary Activities Columns
        activity_columns = [
            ("duration_minutes", "INTEGER DEFAULT 90"),
            ("activity_metadata", "JSONB"),
            ("is_completed", "BOOLEAN DEFAULT FALSE"),
            ("completed_at", "TIMESTAMP WITH TIME ZONE"),
        ]

        for col_name, col_def in activity_columns:
            add_column_if_missing("itinerary_activities", col_name, col_def)

        # 4. Expenses Table Columns
        try:
            conn.execute(text("ALTER TABLE expenses RENAME COLUMN date TO expense_date;"))
            conn.commit()
            print("[OK] Renamed 'date' to 'expense_date' on table 'expenses'.")
        except Exception:
            conn.rollback()

        expense_columns = [
            ("title", "VARCHAR DEFAULT 'Expense' NOT NULL"),
            ("merchant_normalized", "VARCHAR"),
            ("currency", "VARCHAR DEFAULT 'USD' NOT NULL"),
            ("base_currency", "VARCHAR DEFAULT 'USD' NOT NULL"),
            ("exchange_rate", "NUMERIC(12, 6) DEFAULT 1.0"),
            ("payment_method", "VARCHAR DEFAULT 'Cash'"),
            ("expense_date", "DATE DEFAULT CURRENT_DATE"),
            ("location_name", "VARCHAR"),
            ("receipt_metadata", "JSONB"),
            ("notes", "VARCHAR"),
            ("expense_source", "VARCHAR DEFAULT 'MANUAL'"),
            ("created_at", "TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "TIMESTAMP WITH TIME ZONE"),
        ]
        for col_name, col_def in expense_columns:
            add_column_if_missing("expenses", col_name, col_def)



        # 4. Places Columns
        place_columns = [
            ("google_place_id", "VARCHAR"),
            ("timezone", "VARCHAR"),
            ("phone", "VARCHAR"),
            ("website", "VARCHAR"),
            ("categories", "VARCHAR"),
        ]
        for col_name, col_def in place_columns:
            add_column_if_missing("places", col_name, col_def)

        # 5. Expenses Table Columns
        expense_columns = [
            ("description", "VARCHAR"),
            ("paid_by_user_id", "INTEGER REFERENCES users(id)"),
        ]
        for col_name, col_def in expense_columns:
            add_column_if_missing("expenses", col_name, col_def)


        # 4. Journal Entries Table Columns
        journal_columns = [
            ("title", "VARCHAR"),
            ("mood", "VARCHAR"),
        ]
        for col_name, col_def in journal_columns:
            add_column_if_missing("journal_entries", col_name, col_def)

        # 5. Wishlist Items Columns
        wishlist_columns = [
            ("country", "VARCHAR"),
            ("notes", "TEXT"),
            ("priority", "VARCHAR DEFAULT 'someday'"),
        ]
        for col_name, col_def in wishlist_columns:
            add_column_if_missing("wishlist_items", col_name, col_def)

        # 6. Documents Table Columns
        document_columns = [
            ("name", "VARCHAR DEFAULT 'Travel Document' NOT NULL"),
            ("category", "VARCHAR DEFAULT 'Other' NOT NULL"),
            ("document_type", "VARCHAR"),
            ("file_name", "VARCHAR"),
            ("storage_key", "VARCHAR"),
            ("encrypted_url", "VARCHAR"),
            ("mime_type", "VARCHAR DEFAULT 'application/pdf'"),
            ("file_size", "INTEGER DEFAULT 0"),
            ("expiry_date", "TIMESTAMP WITH TIME ZONE"),
            ("notes", "TEXT"),
            ("is_deleted", "BOOLEAN DEFAULT FALSE"),
            ("created_at", "TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "TIMESTAMP WITH TIME ZONE"),
        ]
        for col_name, col_def in document_columns:
            add_column_if_missing("documents", col_name, col_def)

        print("\nDatabase Schema Migration Completed Successfully! All tables synchronized.")

if __name__ == "__main__":
    migrate()

