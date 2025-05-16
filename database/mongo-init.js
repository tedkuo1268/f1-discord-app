db.createUser(
    {
      user: process.env.MONGODB_INITDB_ROOT_USERNAME,
      pwd: process.env.MONGODB_INITDB_ROOT_PASSWORD,
      roles: [
        { role: "userAdminAnyDatabase", db: "admin" },
        { role: "readWriteAnyDatabase", db: "admin" },
        { role: "dbAdminAnyDatabase", db: "admin" }
      ]
    }
  );