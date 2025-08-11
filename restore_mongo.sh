#!/bin/bash

# Variables
ARCHIVE_FILE="jina4-2025-07-31T19-42-33.483Z-prod.archive"       # Path to your archive file
DB_NAME="jina4"            # Name of the target database
MONGO_HOST="localhost"          # MongoDB host
MONGO_PORT="27017"              # MongoDB port
USERNAME=""                     # Optional: MongoDB username
PASSWORD=""                     # Optional: MongoDB password
AUTH_DB="admin"                 # Optional: Authentication database

# Check if the archive file exists
if [ ! -f "$ARCHIVE_FILE" ]; then
  echo "Error: Archive file '$ARCHIVE_FILE' not found!"
  exit 1
fi

# Build the mongorestore command
RESTORE_CMD="mongorestore --host $MONGO_HOST --port $MONGO_PORT --archive=$ARCHIVE_FILE --nsFrom='$DB_NAME.*' --nsTo='$DB_NAME.*' --drop"
mongorestore --host "localhost" --port "27017" --archive="jina4-2025-07-31T19-42-33.483Z-prod.archive" --nsFrom="jina4.*" --nsTo="jina4.*" --drop
# If authentication is needed, add credentials
if [ -n "$USERNAME" ] && [ -n "$PASSWORD" ]; then
  RESTORE_CMD+=" --username $USERNAME --password $PASSWORD --authenticationDatabase $AUTH_DB"
fi

# Execute the command
echo "Running: $RESTORE_CMD"
eval $RESTORE_CMD
