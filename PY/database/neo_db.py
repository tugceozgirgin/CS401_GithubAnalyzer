import json

import numpy as np
import pandas as pd
from PY.api.data import extract_commit_data, get_files_from_json, \
    get_developers_from_json, get_commits_from_json, get_all_developers, get_all_files
from neo4j import GraphDatabase


def execute_nodes(commands):
    data_base_connection = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "password"))
    session = data_base_connection.session()
    for i in commands:
        session.run(i)


class NEO:
    def __init__(self, github_link):
        self.github_link = github_link

    def run(self):
        # Add this section to delete all existing nodes
        data_base_connection = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "password"))
        session = data_base_connection.session()
        delete_all_command = "MATCH (n) DETACH DELETE n"
        session.run(delete_all_command)

        data = extract_commit_data(self.github_link)

        # Create Developer Nodes' Cypher code and connect with Neo4j
        developers = get_all_developers(data)
        developer_id = [i for i in range(1, len(developers) + 1)]
        developer_data = {
            "id": developer_id,
            "name": developers
        }
        developer_list = pd.DataFrame(developer_data).values.tolist()
        developer_execution_commands = []
        for i in developer_list:
            neo4j_create_statement = "CREATE (d:Developer {developer_id:" + str(i[0]) + ", developer_name:  '" + str(
                i[1]) + "'})"
            developer_execution_commands.append(neo4j_create_statement)
        execute_nodes(developer_execution_commands)

        # Create File Nodes' Cypher code and connect with Neo4j
        files = get_all_files(data)
        file_id = [i for i in range(1, len(files) + 1)]
        file_data = {
            "id": file_id,
            "name": files
        }
        file_list = pd.DataFrame(file_data).values.tolist()
        file_execution_commands = []
        for i in file_list:
            neo4j_create_statement = "CREATE (f:Files {file_id:" + str(i[0]) + ", file_name:  '" + str(i[1]) + "'})"
            file_execution_commands.append(neo4j_create_statement)
        execute_nodes(file_execution_commands)

       #Create Commit Nodes' Cypher code and connect with Neo4j
        commit_data = get_commits_from_json()
        commit_list = pd.DataFrame(commit_data).values.tolist()
        commit_execution_commands = []
        for i in commit_list:
            commit_id = i[0]
            commit_hash = i[1]
            commit_message = i[2]
            commit_author = i[3]  # Add the 'commit_author' attribute
            commit_date = i[4]  # Add the 'commit_date' attribute
            modified_files = i[5]  # Add the 'modified_files' attribute

            neo4j_create_statement = (
                    "CREATE (c:Commit {commit_id: " + str(commit_id) + ", "
                    "commit_hash: '" + commit_hash + "', "
                    "commit_message: '" + commit_message + "', "
                    "commit_author: '" + commit_author + "', "
                    "commit_date: '" + commit_date + "', "
                    "modified_files: " + json.dumps(modified_files) + "})"
            )

            commit_execution_commands.append(neo4j_create_statement)
        execute_nodes(commit_execution_commands)
