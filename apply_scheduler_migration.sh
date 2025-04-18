#!/bin/bash
# This script runs the complete migration process for adding 
# the Facebook post scheduler fields to the database

set -e  # Exit on any error

echo "Starting Facebook scheduler migration process..."

# Check if migrations directory exists
if [ ! -d "migrations" ]; then
    echo "Initializing migrations repository..."
    docker compose exec -T web python migrations.py init
    echo "✅ Migrations repository initialized"
else
    echo "✅ Migrations repository already exists"
fi

# Create migration script
echo "Creating migration script for Facebook scheduler fields..."
docker compose exec -T web python migrations.py migrate "add_facebook_scheduler_fields"
echo "✅ Migration script created"

# Apply migrations
echo "Applying migrations to database..."
docker compose exec -T web python migrations.py upgrade
echo "✅ Migrations applied successfully"

# Restart services
echo "Restarting services..."
docker compose restart web scheduler
echo "✅ Services restarted"

echo ""
echo "🎉 Migration completed successfully! Your database has been updated with the new fields for Facebook post scheduling."
echo ""
echo "Next steps:"
echo "1. Schedule posts beyond Facebook's 28-day limit in the application"
echo "2. The scheduler service will automatically submit them to Facebook when they come within the limit"
echo "3. Check the logs with 'docker compose logs -f scheduler' to monitor the scheduling process"
echo "" 