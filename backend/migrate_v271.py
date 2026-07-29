"""
v2.7.1 schema migration script.
Run once to add missing columns to existing tables.
"""
from app.database.connection import get_db, engine
from sqlalchemy import text

db = next(get_db())

print("Running v2.7.1 schema migrations...")

migrations = [
    # Add popularity_score to destination_knowledge
    """ALTER TABLE destination_knowledge ADD COLUMN IF NOT EXISTS popularity_score INTEGER DEFAULT 85""",

    # Add missing interest score columns to user_travel_profiles
    """ALTER TABLE user_travel_profiles ADD COLUMN IF NOT EXISTS nature_score INTEGER DEFAULT 70""",
    """ALTER TABLE user_travel_profiles ADD COLUMN IF NOT EXISTS adventure_score INTEGER DEFAULT 65""",
    """ALTER TABLE user_travel_profiles ADD COLUMN IF NOT EXISTS culture_score INTEGER DEFAULT 60""",
    """ALTER TABLE user_travel_profiles ADD COLUMN IF NOT EXISTS food_score INTEGER DEFAULT 75""",
    """ALTER TABLE user_travel_profiles ADD COLUMN IF NOT EXISTS beach_score INTEGER DEFAULT 50""",
    """ALTER TABLE user_travel_profiles ADD COLUMN IF NOT EXISTS history_score INTEGER DEFAULT 55""",
    """ALTER TABLE user_travel_profiles ADD COLUMN IF NOT EXISTS nightlife_score INTEGER DEFAULT 40""",
    """ALTER TABLE user_travel_profiles ADD COLUMN IF NOT EXISTS shopping_score INTEGER DEFAULT 45""",

    # Add travel style scores
    """ALTER TABLE user_travel_profiles ADD COLUMN IF NOT EXISTS solo_score INTEGER DEFAULT 60""",
    """ALTER TABLE user_travel_profiles ADD COLUMN IF NOT EXISTS family_score INTEGER DEFAULT 40""",
    """ALTER TABLE user_travel_profiles ADD COLUMN IF NOT EXISTS friends_score INTEGER DEFAULT 50""",
    """ALTER TABLE user_travel_profiles ADD COLUMN IF NOT EXISTS luxury_score INTEGER DEFAULT 40""",
    """ALTER TABLE user_travel_profiles ADD COLUMN IF NOT EXISTS budget_score INTEGER DEFAULT 80""",

    # Rename/add columns for compatibility
    """ALTER TABLE user_travel_profiles ADD COLUMN IF NOT EXISTS average_trip_budget FLOAT DEFAULT 800.0""",
    """ALTER TABLE user_travel_profiles ADD COLUMN IF NOT EXISTS average_trip_duration INTEGER DEFAULT 5""",
    """ALTER TABLE user_travel_profiles ADD COLUMN IF NOT EXISTS preferred_months JSON""",
    """ALTER TABLE user_travel_profiles ADD COLUMN IF NOT EXISTS visited_countries JSON""",
    """ALTER TABLE user_travel_profiles ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()""",
]

for sql in migrations:
    try:
        db.execute(text(sql))
        db.commit()
        col = sql.split('ADD COLUMN IF NOT EXISTS ')[1].split(' ')[0] if 'ADD COLUMN' in sql else sql[:50]
        print(f"  OK: {col}")
    except Exception as e:
        db.rollback()
        print(f"  SKIP (already done or error): {e}")

db.close()
print("\nMigration complete.")
