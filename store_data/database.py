import psycopg2
from psycopg2.extras import RealDictCursor


class Database:
    def __init__(self, dbname, user, password, host='localhost', port='5432'):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.connection = None

    def connect(self):
        """Establishes a new database connection."""

        if not self.connection:
            try:
                self.connection = psycopg2.connect(
                    dbname=self.dbname,
                    user=self.user,
                    password=self.password,
                    host=self.host,
                    port=self.port
                )
                print("✅ Connected to the database successfully!")
            except Exception as e:
                print(f"❌ Failed to connect to the database: {e}")

    def execute_query(self, query, params=None):
        """Executes a query and commits changes."""

        try:
            self.connect()
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                self.connection.commit()
        except Exception as e:
            print(f"❌ Query execution failed: {e}")

    def fetch_all(self, query, params=None):
        """Fetches all rows from a query."""

        try:
            self.connect()
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            print(f"❌ Fetch failed: {e}")
            return []

    def fetch_one(self, query, params=None):
        """Fetches one row from a query."""

        try:
            self.connect()
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                return cursor.fetchone()
        except Exception as e:
            print(f"❌ Fetch failed: {e}")
            return None

    def close(self):
        """Closes the database connection."""

        if self.connection:
            self.connection.close()
            self.connection = None
            print("✅ Database connection closed.")
