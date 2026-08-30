"""
Smart Travel Checklist DB Migration Script
Creates the `checklist_items` table safely if it does not exist.
Safe to run multiple times.
"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Ensure backend path is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import Base, engine
import app.models.checklist  # Ensures ChecklistItem model is registered


def migrate():
    print("Running Smart Travel Checklist database migration...")

    # 1. Create missing tables defined in Base metadata (including checklist_items)
    Base.metadata.create_all(bind=engine)
    print("[OK] Base.metadata.create_all executed.")

    # 2. Verify columns and ensure indexes if needed
    with engine.connect() as conn:
        def add_column_if_missing(table, col_name, col_type_def):
            sql = f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col_name} {col_type_def};"
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"  [OK] Column '{col_name}' verified on '{table}'.")
            except Exception as e:
                conn.rollback()
                print(f"  [SKIP] '{col_name}' on '{table}': {e}")

        checklist_columns = [
            ("title", "VARCHAR NOT NULL"),
            ("description", "TEXT"),
            ("category", "VARCHAR DEFAULT 'CUSTOM' NOT NULL"),
            ("priority", "VARCHAR DEFAULT 'MEDIUM' NOT NULL"),
            ("status", "VARCHAR DEFAULT 'PENDING' NOT NULL"),
            ("due_date", "TIMESTAMP WITH TIME ZONE"),
            ("source", "VARCHAR DEFAULT 'SYSTEM' NOT NULL"),
            ("action_type", "VARCHAR"),
            ("action_target", "VARCHAR"),
            ("is_auto_generated", "BOOLEAN DEFAULT TRUE NOT NULL"),
            ("created_at", "TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP"),
            ("completed_at", "TIMESTAMP WITH TIME ZONE"),
        ]

        for col_name, col_def in checklist_columns:
            add_column_if_missing("checklist_items", col_name, col_def)

    print("Smart Travel Checklist migration complete.")


if __name__ == "__main__":
    migrate()
