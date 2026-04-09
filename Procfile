# Railway reads Build Command and Start Command from Settings > Deploy.
# Build:  cd backend && python manage.py migrate --noinput && python manage.py seed_admin && python manage.py collectstatic --noinput
# Start:  cd backend && gunicorn servicetrack.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT

web: cd backend && gunicorn servicetrack.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
