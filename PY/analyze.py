import psycopg2

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    database="gui_analyzer",
    user="postgres",
    password="pass123",
    host="localhost",
    port="5432",
)
cursor = conn.cursor()

# Count the number of commits per developer
cursor.execute('''
    SELECT d.developer_name, COUNT(c.commit_id) as commit_count
    FROM developer d
    LEFT JOIN commits c ON d.developer_id = c.author_id
    GROUP BY d.developer_name
    ORDER BY commit_count DESC;
''')

commit_counts = cursor.fetchall()
print("Number of commits per developer:")
for developer, commit_count in commit_counts:
    print(f"{developer}: {commit_count} commits")

# Retrieve commit information
cursor.execute('''
    SELECT d.developer_name, c.commit_message, c.commit_hash
    FROM developer d
    LEFT JOIN commits c ON d.developer_id = c.author_id
''')

commit_info = cursor.fetchall()
print("\nCommit Information:")
for developer, commit_message, commit_hash in commit_info:
    print(f"Developer: {developer}")
    print(f"Commit Message: {commit_message}")
    print(f"Commit Hash: {commit_hash}\n")

# Close the connection
conn.close()
