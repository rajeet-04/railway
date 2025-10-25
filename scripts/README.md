# Scripts — management utilities (planned)

This directory will contain management scripts used by the backend and maintainers.

Planned scripts
- `init_db.py` — Initialize the SQLite DB from `database/schema.sql` (optional) and seed initial admin from environment variables.
  - Reads `ADMIN_EMAIL` and `ADMIN_PASSWORD` (and optional `ADMIN_FULL_NAME`, `ADMIN_PHONE`) from environment or `.env`.
  - Supports `--init-schema` to apply schema, and `--force` to update admin credentials without deleting bookings/relations.
- `import_data.py` — Import `data/trains.json`, `data/stations.json`, and `data/schedules.json`.
  - Idempotent import with logs stored in `import_logs` table.

Example usage (PowerShell):
```powershell
# apply schema and seed admin from .env
python .\scripts\init_db.py --init-schema

# seed/admin update only
python .\scripts\init_db.py --force
```

Dependencies
- `python-dotenv` (optional) to load `.env` files
- `passlib[bcrypt]` for password hashing

Notes
- Scripts should be runnable from project root and use environment variables for automation/CI.
- Scripts must be idempotent where possible.
