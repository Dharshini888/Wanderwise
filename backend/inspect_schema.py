from app.database.connection import get_db, engine
from sqlalchemy import text

db = next(get_db())

result = db.execute(text(
    'SELECT column_name, data_type FROM information_schema.columns WHERE table_name = :t ORDER BY ordinal_position'
), {'t': 'destination_knowledge'})

print('destination_knowledge columns:')
for row in result:
    print(' -', row[0], ':', row[1])

for t in ['user_travel_profiles', 'trip_preference_history', 'recommendation_history']:
    r2 = db.execute(text('SELECT column_name FROM information_schema.columns WHERE table_name = :t ORDER BY ordinal_position'), {'t': t})
    cols = [x[0] for x in r2.fetchall()]
    status = str(cols) if cols else 'TABLE MISSING / EMPTY'
    print(t + ': ' + status)
db.close()
