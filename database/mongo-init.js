// mongo-init.js
db = db.getSiblingDB('f1_discord_app');

// Create collection
db.createCollection('locations');

// Create indexes
db.locations.createIndex({ meeting_key: 1 }, { unique: true });

