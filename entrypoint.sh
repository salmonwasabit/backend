#!/bin/bash

# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! python -c "import psycopg2; psycopg2.connect('$DATABASE_URL')" 2>/dev/null; do
  echo "Database not ready, waiting..."
  sleep 2
done

echo "Database is ready!"

# Run admin initialization
echo "Running admin initialization..."
python init_admin.py

# Check if we should populate data (only if POPULATE_DATA is set to true)
if [ "$POPULATE_DATA" = "true" ]; then
  echo "Populating categories..."
  python populate_categories.py

  echo "Populating products..."
  python populate_products.py
else
  echo "Skipping data population (POPULATE_DATA not set to true)"
fi

# Start the application
echo "Starting the application..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
