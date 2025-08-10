#!/usr/bin/env python3
"""
Convenience management script.

Usage:
  python manage.py create "Add flights & car rentals"
  python manage.py migrate
  python manage.py rollback head-1
  python manage.py status
  python manage.py history
  python manage.py seed
  python manage.py reset
"""

import sys

import manage_migrations as mm


def main() -> None:
    if len(sys.argv) < 2:
        mm.show_help()
        return

    command = sys.argv[1].lower()

    if command == "init":
        mm.init_alembic()
    elif command == "create":
        message = sys.argv[2] if len(sys.argv) > 2 else None
        mm.create_migration(message)
    elif command == "migrate":
        mm.migrate()
    elif command == "rollback":
        revision = sys.argv[2] if len(sys.argv) > 2 else None
        mm.rollback(revision)
    elif command == "status":
        mm.show_status()
    elif command == "history":
        mm.show_history()
    elif command == "stamp":
        mm.stamp_head()
    elif command == "reset":
        mm.reset_database()
    elif command == "seed":
        mm.seed_data()
    else:
        print(f"Unknown command: {command}\n")
        mm.show_help()


if __name__ == "__main__":
    main()


