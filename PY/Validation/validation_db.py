import json

import pandas as pd
from neo4j import GraphDatabase
def execute_nodes(commands):
    data_base_connection = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "password"))
    session = data_base_connection.session()
    for i in commands:
        session.run(i)

def standardize_name(name):
    # Replace Turkish characters with their English counterparts
    name = name.replace('ş', 's').replace('ı', 'i').replace('ğ', 'g').replace('Ğ', 'G').replace('ü', 'u').replace('Ü',
                                                                                                                  'U').replace(
        'ö', 'o').replace('Ö', 'O').replace('İ', 'I').replace('Ş', 'S').replace('Ç', 'C').replace('ç', 'c')
    # Remove non-alphanumeric characters, spaces, and convert to lowercase
    standardized_name = ''.join(e for e in name if e.isalnum() or e.isspace()).lower().replace(" ", "")
    return standardized_name
def get_developers_from_json(json_file_path='change_set.json'):
    with open(json_file_path, 'r', encoding='utf-8') as infile:
        commit_data = json.load(infile)

    developers = set()
    for commit in commit_data:
        developers.add(commit['author'])
    return list(developers)


developers = get_developers_from_json(json_file_path="../change_set.json")
developer_id = [i for i in range(1, len(developers) + 1)]
developer_data = {
            "id": developer_id,
            "name": developers
        }
developer_list = pd.DataFrame(developer_data).values.tolist()
developer_execution_commands = []
for i in developer_list:
    standardized_name = standardize_name(i[1])
    neo4j_create_statement = (
    f"CREATE (d:Developer {{developer_id: {i[0]}, developer_name: '{standardized_name}'}})"
    )
    developer_execution_commands.append(neo4j_create_statement)
execute_nodes(developer_execution_commands)