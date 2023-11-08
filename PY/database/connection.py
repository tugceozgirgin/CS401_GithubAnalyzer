import json
import psycopg2

class CONNECTION:
    def __init__(self):
        # You can initialize connection parameters here if needed
        self.db_params = {
            "database": "gui_analyzer",
            "user": "postgres",
            "password": "pass123",
            "host": "localhost",
            "port": "5432",
        }

    def run(self):
        # Read data from the JSON file
        with open('O:\proje\CS401_GithubAnalyzer\PY\commit_data.json', 'r') as json_file:
            data = json.load(json_file)

        # Connect to the PostgreSQL database
        conn = psycopg2.connect(**self.db_params)
        cursor = conn.cursor()

        # Clear existing data by deleting all records in the tables
        cursor.execute('DELETE FROM commit_file;')
        cursor.execute('DELETE FROM commit_developer;')
        cursor.execute('DELETE FROM commits;')
        cursor.execute('DELETE FROM files;')
        cursor.execute('DELETE FROM developer;')

        # Commit the deletions
        conn.commit()

        # Create the Developer table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS developer (
                developer_id SERIAL PRIMARY KEY,
                developer_name TEXT
            );
        ''')

        # Create the Commits table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commits (
                commit_id SERIAL PRIMARY KEY,
                commit_hash TEXT,
                commit_message TEXT,
                author_id INTEGER REFERENCES developer(developer_id)
            );
        ''')

        # Create the Files table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                file_id SERIAL PRIMARY KEY,
                file_name TEXT
            );
        ''')

        # Create the CommitDeveloper relation table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commit_developer (
                commit_id INTEGER REFERENCES commits(commit_id),
                developer_id INTEGER REFERENCES developer(developer_id)
            );
        ''')

        # Create the CommitFile relation table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commit_file (
                commit_id INTEGER REFERENCES commits(commit_id),
                file_id INTEGER REFERENCES files(file_id)
            );
        ''')

        # Dictionary to store developer IDs by name
        developer_ids = {}

        for commit_data in data:
            # Insert the developer if not already in the database
            developer_name = commit_data["author"]

            if developer_name not in developer_ids:
                cursor.execute(
                    "INSERT INTO developer (developer_name) VALUES (%s) RETURNING developer_id",
                    (developer_name,)
                )
                developer_id = cursor.fetchone()[0]
                developer_ids[developer_name] = developer_id
            else:
                developer_id = developer_ids[developer_name]

            # Insert the commit into the commits table
            cursor.execute(
                "INSERT INTO commits (commit_hash, commit_message, author_id) VALUES (%s, %s, %s) RETURNING commit_id",
                (commit_data["hash"], commit_data["message"], developer_id)
            )
            commit_id = cursor.fetchone()[0]

            # Insert modified files into the files table and create relations
            for file_name in commit_data["modified_files"]:
                cursor.execute(
                    "INSERT INTO files (file_name) VALUES (%s) RETURNING file_id",
                    (file_name,)
                )
                file_id = cursor.fetchone()[0]

                # Create a relation between the commit and developer
                cursor.execute(
                    "INSERT INTO commit_developer (commit_id, developer_id) VALUES (%s, %s)",
                    (commit_id, developer_id)
                )

                # Create a relation between the commit and file
                cursor.execute(
                    "INSERT INTO commit_file (commit_id, file_id) VALUES (%s, %s)",
                    (commit_id, file_id)
                )

        # Commit changes and close the connection
        conn.commit()
        conn.close()
