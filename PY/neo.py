from neo4j import GraphDatabase
import json

# Define the JSON file path
json_file = "O:\proje\CS401_GithubAnalyzer\commit_data.json"

# Connect to the Neo4j database
uri = "bolt://localhost:7687"  # Update with your Neo4j server information
username = "neo4j"
password = "12345678"

# Function to create nodes and relationships from JSON data
def create_nodes_and_relationships(tx, data):
    for developer in data['developers']:
        tx.run("CREATE (:developer {name: $name, email: $email})", name=developer['name'], email=developer['email'])

    for commit in data['commits']:
        tx.run("CREATE (:commit {id: $id, message: $message})", id=commit['id'], message=commit['message'])
        tx.run("MATCH (developer:developer {name: $developer_name}), (commit:commit {id: $commit_id}) CREATE (developer)-[:COMMITTED]->(commit)",
               developer_name=commit['developer'], commit_id=commit['id'])

    for file in data['files']:
        tx.run("CREATE (:file {name: $name, path: $path})", name=file['name'], path=file['path'])
        tx.run("MATCH (commit:commit {id: $commit_id}), (file:file {name: $file_name}) CREATE (commit)-[:AFFECTED]->(file)",
               commit_id=file['commit'], file_name=file['name'])

# Main script
with open(json_file, 'r') as f:
    data = json.load(f)

with GraphDatabase.driver(uri, auth=(username, password)) as driver:
    with driver.session() as session:
        session.write_transaction(create_nodes_and_relationships, data)

print("Nodes and relationships created in Neo4j.")
