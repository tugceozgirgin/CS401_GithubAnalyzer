import numpy as np
import pandas as pd
from PY.api.data import extract_commit_data, get_all_files, get_all_developers
from neo4j import GraphDatabase

class NEO:
    def __init__(self, github_link):
        self.github_link = github_link

    def execute_nodes(self, commands):
        data_base_connection = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "password"))
        session = data_base_connection.session()
        for i in commands:
            session.run(i)

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
            neo4j_create_statement = "CREATE (d:Developer {developer_id:" + str(i[0]) + ", developer_name:  '" + str(i[1]) + "'})"
            developer_execution_commands.append(neo4j_create_statement)
        self.execute_nodes(developer_execution_commands)

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
        self.execute_nodes(file_execution_commands)
