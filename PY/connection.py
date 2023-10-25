import json
import psycopg2

# Read data from the JSON file
with open('O:\proje\CS401_GithubAnalyzer\commit_data.json', 'r') as json_file:
    data = json.load(json_file)

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    database="gui_analyzer",
    user="postgres",
    password="pass123",
    host="localhost",
    port="5432",
)
cursor = conn.cursor()

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

for commit_data in data:
    # Insert the developer if not already in the database
    cursor.execute(
        "INSERT INTO developer (developer_name) VALUES (%s)",
        (commit_data["author"],),
    )

    # Get the developer ID
    cursor.execute("SELECT developer_id FROM developer WHERE developer_name = %s", (commit_data["author"],))
    developer_id = cursor.fetchone()[0]

    # Insert the commit into the commits table
    cursor.execute(
        "INSERT INTO commits (commit_hash, commit_message, author_id) VALUES (%s, %s, %s) RETURNING commit_id",
        (commit_data["hash"], commit_data["message"], developer_id),
    )
    commit_id = cursor.fetchone()[0]

    # Insert modified files into the files table and create relations
    for file_name in commit_data["modified_files"]:
        cursor.execute(
            "INSERT INTO files (file_name) VALUES (%s)",
            (file_name,),
        )

        cursor.execute("SELECT file_id FROM files WHERE file_name = %s", (file_name,))
        file_id = cursor.fetchone()[0]

        # Create a relation between the commit and developer
        cursor.execute(
            "INSERT INTO commit_developer (commit_id, developer_id) VALUES (%s, %s)",
            (commit_id, developer_id),
        )

        # Create a relation between the commit and file
        cursor.execute(
            "INSERT INTO commit_file (commit_id, file_id) VALUES (%s, %s)",
            (commit_id, file_id),
        )

# List tables in the public schema
cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")

tables = cursor.fetchall()
for table in tables:
    print(table[0])

# List developer names from the "developer" table
cursor.execute("SELECT developer_name FROM developer;")
developer_names = cursor.fetchall()

# Print developer names
for developer_name in developer_names:
    print(developer_name[0])

# Commit changes and close the connection
conn.commit()
conn.close()
