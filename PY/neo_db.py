
import numpy as np
import pandas as pd
from PY.api.data import extract_commit_data, dump_json_file, get_all_files, get_all_developers
from neo4j import GraphDatabase

data = extract_commit_data("https://github.com/Saeed-Muhaisen/PharmacyProject")
files = get_all_files(data)


# Create Developer Nodes' cypher code and connect with neo4j
developers = get_all_developers(data)
developer_id = [i for i in range(1, len(developers) + 1)]
developer_data = {}
developer_data = {
    "id": developer_id,
    "name": developers
}
developer_list = pd.DataFrame(developer_data).values.tolist()
developer_execution_commands = []
for i in developer_list:
    neo4j_create_statement = "CREATE (d:Developer {developer_id:" + str(i[0]) + ", developer_name:  '" + str(i[1])+ "'})"
    developer_execution_commands.append(neo4j_create_statement)
def execute_developers(commands):
    data_base_connection = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "password"))
    session = data_base_connection.session()
    for i in commands:
        session.run(i)
execute_developers(developer_execution_commands)

# Create File Nodes' cypher code and connect with neo4j
# Create Commit Nodes' cypher code and connect with neo4j