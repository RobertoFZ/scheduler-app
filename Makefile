.PHONY: up down logs migrations-init migrations-create migrations-upgrade migrations-downgrade scheduler-once scheduler-loop scheduler-loop-custom db-shell db-backup rebuild restart help

# Docker compose commands
up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

restart:
	docker compose restart

rebuild:
	docker compose down
	docker compose build
	docker compose up -d

# Migration commands
migrations-init:
	docker compose exec web python migrations.py init

migrations-create:
	docker compose exec web python migrations.py migrate "$(message)"

migrations-upgrade:
	docker compose exec web python migrations.py upgrade

migrations-downgrade:
	docker compose exec web python migrations.py downgrade $(revision)

# Scheduler commands
scheduler-once:
	docker compose exec web python scheduler.py

scheduler-loop:
	docker compose exec web python scheduler.py --loop

scheduler-loop-custom:
	docker compose exec web python scheduler.py --loop --interval=$(interval)

# Database commands
db-shell:
	docker compose exec db psql -U postgres -d facebook_scheduler

db-backup:
	docker compose exec db pg_dump -U postgres facebook_scheduler > backup_$(shell date +%Y%m%d_%H%M%S).sql

# Default help command
help:
	@echo "Available commands:"
	@echo ""
	@echo "Docker commands:"
	@echo "  make up                    - Start all containers in detached mode"
	@echo "  make down                  - Stop and remove all containers"
	@echo "  make logs                  - View logs from all containers"
	@echo "  make restart               - Restart all containers"
	@echo "  make rebuild               - Rebuild and restart all containers"
	@echo ""
	@echo "Migration commands:"
	@echo "  make migrations-init                         - Initialize migration repository"
	@echo "  make migrations-create message=\"description\" - Create a new migration"
	@echo "  make migrations-upgrade                      - Apply all migrations"
	@echo "  make migrations-downgrade revision=rev       - Revert to specific revision"
	@echo ""
	@echo "Scheduler commands:"
	@echo "  make scheduler-once                       - Run scheduler once"
	@echo "  make scheduler-loop                       - Run scheduler in loop mode"
	@echo "  make scheduler-loop-custom interval=300   - Run with custom interval in seconds"
	@echo ""
	@echo "Database commands:"
	@echo "  make db-shell               - Access PostgreSQL shell"
	@echo "  make db-backup              - Create a database backup"
	@echo ""

# Default target
.DEFAULT_GOAL := help 