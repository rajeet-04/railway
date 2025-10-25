#!/usr/bin/env python3
"""
scripts/init_db.py

Initialize SQLite DB from schema (optional) and seed an admin user.
Reads credentials from environment variables (or .env).

Behavior:
- If DB doesn't exist and --init-schema provided, runs database/schema.sql.
- Inserts admin user if not present.
- If --force, updates the existing admin user's password and full_name, sets is_admin=1.
- Does NOT delete bookings or other relations.
"""

import argparse
import os
import sqlite3
import sys
from pathlib import Path
from passlib.context import CryptContext

# support bcrypt and pbkdf2_sha256 for environments where bcrypt C backend may be missing
# Prefer pbkdf2_sha256 to avoid relying on bcrypt C-extension during initial setup
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], default="pbkdf2_sha256", deprecated="auto")

# Optional: loads .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

DEFAULT_DB_PATH = os.environ.get("DB_PATH", "database/railway.db")
DEFAULT_SCHEMA_PATH = os.environ.get("SCHEMA_PATH", "database/schema.sql")


def run_schema(db_path: str, schema_path: str):
    schema_file = Path(schema_path)
    if not schema_file.exists():
        print(f"Schema file not found at {schema_path}. Skipping schema init.")
        return
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        # Try UTF-16 first (as the file may be in UTF-16), fallback to UTF-8
        try:
            with open(schema_file, "r", encoding="utf-16") as f:
                schema_sql = f.read()
        except UnicodeError:
            with open(schema_file, "r", encoding="utf-8") as f:
                schema_sql = f.read()
        conn.executescript(schema_sql)
        conn.commit()
        print(f"Schema executed from {schema_path} -> {db_path}")
    finally:
        conn.close()


def ensure_admin(db_path: str, email: str, password: str, full_name: str, phone: str, force: bool):
    if not email or not password:
        print("ADMIN_EMAIL and ADMIN_PASSWORD must be set in environment or .env.")
        sys.exit(2)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cur.fetchone():
            print("Warning: `users` table not found. Did you initialize schema?")
            conn.close()
            sys.exit(3)

        cur.execute("SELECT id, email, is_admin FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        hashed = pwd_context.hash(password)

        if row:
            user_id = row["id"]
            if not force:
                print(f"Admin user with email '{email}' already exists (id={user_id}). Use --force to update credentials.")
                return
            cur.execute("""
                UPDATE users
                SET password_hash = ?, full_name = ?, phone = ?, is_admin = 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (hashed, full_name or "Admin", phone, user_id))
            conn.commit()
            print(f"Updated existing admin user (id={user_id}, email={email}). Bookings/relations preserved.")
            return
        else:
            cur.execute("""
                INSERT INTO users (email, password_hash, full_name, phone, is_admin, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (email, hashed, full_name or "Admin", phone))
            conn.commit()
            new_id = cur.lastrowid
            print(f"Created admin user (id={new_id}, email={email}).")
            return
    finally:
        conn.close()


def parse_args():
    p = argparse.ArgumentParser(description="Initialize DB and seed an admin user.")
    p.add_argument("--db-path", default=DEFAULT_DB_PATH, help="Path to SQLite DB (default from DB_PATH env).")
    p.add_argument("--schema", default=DEFAULT_SCHEMA_PATH, help="Path to schema.sql to execute if DB empty.")
    p.add_argument("--init-schema", action="store_true", help="Run schema.sql before seeding admin.")
    p.add_argument("--force", action="store_true", help="If admin exists, force-update credentials (don't delete bookings).")
    return p.parse_args()


def main():
    args = parse_args()
    db_path = args.db_path
    schema_path = args.schema

    admin_email = os.environ.get("ADMIN_EMAIL")
    admin_password = os.environ.get("ADMIN_PASSWORD")
    admin_full_name = os.environ.get("ADMIN_FULL_NAME", "Admin User")
    admin_phone = os.environ.get("ADMIN_PHONE", "")

    db_parent = Path(db_path).parent
    db_parent.mkdir(parents=True, exist_ok=True)

    if args.init_schema:
        print("Running schema initialization...")
        run_schema(db_path, schema_path)

    if not Path(db_path).exists():
        print(f"Database not found at {db_path}. Creating empty SQLite file.")
        sqlite3.connect(db_path).close()
        print("Created empty database file. If schema is not applied, run with --init-schema to apply schema.sql.")

    ensure_admin(db_path, admin_email, admin_password, admin_full_name, admin_phone, args.force)
    print("Init script completed.")


if __name__ == "__main__":
    main()
