#!/bin/bash\n\
    service postgresql start\n\
    su postgres -c "psql -c \"ALTER USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';\"\n\
    su postgres -c "psql -c \"CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};\"\n\
    ollama serve &\n\
    sleep 10\n\
    ollama pull llama3.1\n\
    python app.py\n\
    
