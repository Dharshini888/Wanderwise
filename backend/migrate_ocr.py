import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, inspect, text
from app.database.connection import DATABASE_URL

def run_migration():
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    if not inspector.has_table("documents"):
        print("Documents table does not exist. Migration skipped.")
        return
        
    columns = [col['name'] for col in inspector.get_columns("documents")]
    
    queries = []
    
    if "ocr_status" not in columns:
        queries.append("ALTER TABLE documents ADD COLUMN ocr_status VARCHAR;")
    if "ocr_confidence" not in columns:
        queries.append("ALTER TABLE documents ADD COLUMN ocr_confidence FLOAT;")
    if "extraction_source" not in columns:
        queries.append("ALTER TABLE documents ADD COLUMN extraction_source VARCHAR;")
    if "document_type_confidence" not in columns:
        queries.append("ALTER TABLE documents ADD COLUMN document_type_confidence FLOAT;")
    if "extracted_metadata" not in columns:
        # We're using SQLite for most of WanderWise by default, or Postgres. 
        queries.append("ALTER TABLE documents ADD COLUMN extracted_metadata JSON;")
        
    if queries:
        with engine.connect() as conn:
            for query in queries:
                print(f"Executing: {query}")
                try:
                    conn.execute(text(query))
                except Exception as e:
                    if "JSON" in query and "sqlite" in DATABASE_URL.lower():
                        print("Falling back to TEXT for JSON column in SQLite")
                        conn.execute(text(query.replace("JSON", "TEXT")))
                    else:
                        print(f"Error executing {query}: {e}")
            conn.commit()
        print("Migration completed successfully.")
    else:
        print("All OCR columns already exist. Nothing to do.")

if __name__ == "__main__":
    run_migration()
