from sqlalchemy import text; from app.database.connection import engine;
with engine.connect() as conn:
    conn.execute(text('ALTER TABLE packing_lists ADD COLUMN IF NOT EXISTS generation_source VARCHAR DEFAULT \'ai\''))
    conn.commit()

