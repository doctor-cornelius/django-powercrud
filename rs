# quickly get the dev server up and running

# Set default port to 8000 if not provided
PORT=${1:-8001}

./src/manage.py runserver 0:$PORT
