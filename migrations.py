from flask_migrate import (
    Migrate, init, migrate as create_migration, 
    upgrade, downgrade
)
from app import create_app
from app.models import db

# Create app instance
app = create_app()

# Initialize migrate
migrate = Migrate(app, db)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) <= 1:
        print("Usage: python migrations.py [command]")
        print("Available commands:")
        print("  init - Initialize migrations repository")
        print("  migrate - Generate migration script")
        print("  upgrade - Apply migrations")
        print("  downgrade - Revert migrations")
        sys.exit(1)
    
    # Get the command from the first argument
    command = sys.argv[1]
    
    with app.app_context():
        if command == "init":
            init(directory="migrations")
            print("Migrations initialized")
        elif command == "migrate":
            message = ""
            if len(sys.argv) > 2:
                message = sys.argv[2]
            create_migration(
                directory="migrations", 
                message=message
            )
            print("Migration script created")
        elif command == "upgrade":
            revision = "head"
            if len(sys.argv) > 2:
                revision = sys.argv[2]
            upgrade(directory="migrations", revision=revision)
            print(f"Database upgraded to {revision}")
        elif command == "downgrade":
            if len(sys.argv) <= 2:
                print("Error: Please specify revision to downgrade to")
                sys.exit(1)
            revision = sys.argv[2]
            downgrade(directory="migrations", revision=revision)
            print(f"Database downgraded to {revision}")
        else:
            print(f"Unknown command: {command}")
            sys.exit(1) 