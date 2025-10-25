# Database folder

This folder contains the canonical DB schema, sample queries, and optionally a pre-populated SQLite database.

Files
- `schema.sql` — canonical schema used to create tables (users, trains, stations, train_stops, seats, bookings, etc.).
- `queries.sql` — helpful sample queries for search, availability, booking, and admin reporting. Use as reference or for manual testing.
- `railway.db` — optional SQLite database file (may contain imported sample data). Use at your own risk — backups recommended.

How to (re)initialize the DB
1. Use `scripts/init_db.py --init-schema` to run `schema.sql` and optionally seed the admin user from env.
2. Alternatively, use sqlite3 CLI:

```powershell
# create DB and apply schema
sqlite3 database/railway.db ".read database/schema.sql"
```

Inspecting the DB
- Use the sqlite3 CLI or a GUI tool (DB Browser for SQLite) to inspect tables and run queries from `queries.sql`.

Notes
- `queries.sql` includes booking transaction examples and admin reports. Keep as a working reference.
- Prefer interacting with the DB via the backend API during normal development to keep business rules and constraints enforced.
