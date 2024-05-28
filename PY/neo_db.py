import datetime as dt
import json
import os
from typing import Dict

import pandas as pd
#from ..PY.data import get_files_from_json, \
#get_developers_from_json, read_from_json, get_all_files, \
#calculate_file_change_coverage, calculate_file_change_coverage_ratio, get_first_last_commit_dates
from neo4j import GraphDatabase

from data import get_developers_from_json, read_from_json, get_all_files, \
    calculate_file_change_coverage, calculate_file_change_coverage_ratio, get_first_last_commit_dates, \
    get_files_from_json

commit_data = read_from_json('commit_data.json')
first_date, last_date = get_first_last_commit_dates(commit_data)


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


def calculate_recency(targetdate):
    days_in_graph = calculate_date_difference_in_days(first_date, last_date)
    days_passed = days_in_graph - calculate_date_difference_in_days(first_date, targetdate)
    return 1 - (days_passed / days_in_graph)


def calculate_date_difference_in_days(first_date_str, last_date_str):
    first_date = dt.datetime.strptime(first_date_str, '%Y-%m-%d %H:%M:%S')
    last_date = dt.datetime.strptime(last_date_str, '%Y-%m-%d %H:%M:%S')
    difference = last_date - first_date
    return difference.days


class NEO:
    def __init__(self):
        pass

    def run(self):
        # Add this section to delete all existing nodes
        data_base_connection = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "password"))
        session = data_base_connection.session()
        delete_all_command = "MATCH (n) DETACH DELETE n"
        session.run(delete_all_command)
        print("neo giriş")
        # Create Developer Nodes' Cypher code and connect with Neo4j
        developers = get_developers_from_json()
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

        # Create File Nodes' Cypher code and connect with Neo4j
        files = get_files_from_json()
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

        # Create Commit Nodes' Cypher code and connect with Neo4j

        commit_execution_commands = []

        for i, commit in enumerate(commit_data, start=1):
            commit_id = i
            commit_hash = commit['hash']
            commit_author = commit['author']
            standardized_author = standardize_name(commit_author)
            commit_date = commit['commit_date']
            modified_files = commit['modified_files']
            lines_inserted = commit['lines_inserted']
            lines_deleted = commit['lines_deleted']

            neo4j_create_statement = (
                f"CREATE (c:Commit {{commit_id: {commit_id}, commit_hash: '{commit_hash}', "
                f"commit_author: '{standardized_author}', "
                f"commit_date: '{commit_date}', modified_files: {json.dumps(modified_files)}, "
                f"lines_inserted: {json.dumps(lines_inserted)}, lines_deleted: {json.dumps(lines_deleted)}}})"
            )

            commit_execution_commands.append(neo4j_create_statement)



        # Create relationships between Commit-Developer
        # Create relationships between Developer-Commit
        neo4j_create_relation_dev_statement_commit = (
            "MATCH (c:Commit), (d:Developer) "
            "WHERE c.commit_author = d.developer_name "
            "MERGE (c)-[:DEVELOPED_BY]->(d)"
        )
        commit_execution_commands.append(neo4j_create_relation_dev_statement_commit)

        # Create bidirectional relationships between Commit and Developer nodes
        bidirectional_dev_commit_relation = (
            "MATCH (c:Commit), (d:Developer) "
            "WHERE c.commit_author = d.developer_name "
            "MERGE (d)-[:DEVELOPED]->(c)"
        )
        commit_execution_commands.append(bidirectional_dev_commit_relation)

        execute_nodes(commit_execution_commands)

        # Create relationships between Commit-File based on modified_files
        commit_file_relation_commands = []
        file_commit_relation_commands = []  # New list for file->commit relationship commands

        for commit in commit_data:
            commit_hash = commit['hash']
            modified_files = commit['modified_files']
            lines_inserted = commit['lines_inserted']
            lines_deleted = commit['lines_deleted']
            recency = calculate_recency(commit['commit_date'])
            distance = calculate_date_difference_in_days(first_date, last_date) if recency == 0 else 1 / recency

            for idx, file_name in enumerate(modified_files):
                inserted = lines_inserted[idx]
                deleted = lines_deleted[idx]

                neo4j_create_relation_file_statement = (
                    f"MATCH (c:Commit {{commit_hash: '{commit_hash}'}}), "
                    f"(f:Files {{file_name: '{file_name}'}}) "
                    f"CREATE (c)-[:MODIFIED {{inserted_lines: {inserted}, deleted_lines: {deleted}, distance: {distance}}}]->(f)"
                )
                commit_file_relation_commands.append(neo4j_create_relation_file_statement)

                # New relationship creation from File to Commit
                file_to_commit_statement = (
                    f"MATCH (c:Commit {{commit_hash: '{commit_hash}'}}), "
                    f"(f:Files {{file_name: '{file_name}'}}) "
                    f"CREATE (f)-[:MODIFIED_BY {{inserted_lines: {inserted}, deleted_lines: {deleted}, distance: {distance}}}]->(c)"
                )
                file_commit_relation_commands.append(file_to_commit_statement)

        # Execute both types of relationship commands
        execute_nodes(commit_file_relation_commands)
        execute_nodes(file_commit_relation_commands)

        # Create Issue Nodes
        issues_data = read_from_json("issue_data.json")
        issue_execution_commands = []
        for issue in issues_data:
            neo4j_create_statement = (
                    "CREATE (i:Issue {"
                    "issue_id: " + str(issue['id']) + ", "
                                                      "title: '" + issue['title'].replace("'", "\\'") + "', "
                                                                                                        "description: '" + (
                        issue['description'].replace("'", "\\'") if issue['description'] is not None else "") + "', "
                                                                                                                "state: '" +
                    issue['state'] + "', "
                                     "created_at: '" + issue['created_at'] + "', "
                                                                             "closed_at: " + (
                        f"'{issue['closed_at']}'" if issue['closed_at'] is not None else "null") + ", "
                                                                                                   "closed_by: " + (
                        f"'{issue['closed_by']}'" if issue['closed_by'] is not None else "null") + ", "
                    # "opened_by: " + (f"'{issue['opened_by']}'" if issue['opened_by'] is not None else "null") + "'})"
                                                                                                   "opened_by: '" +
                    issue['opened_by'] + "'})"
            )

            issue_execution_commands.append(neo4j_create_statement)
        execute_nodes(issue_execution_commands)

        # Create relationships between Developer and Issue nodes based on opened_by and closed_by fields
        developer_issue_relation_commands = []

        for issue in issues_data:
            opened_by = issue['opened_by']
            closed_by = issue['closed_by']

            if opened_by:
                opened_by_standardized = standardize_name(opened_by)
                neo4j_create_relation_dev_issue_statement = (
                    f"MATCH (d1:Developer {{developer_name: '{opened_by_standardized}'}}), "
                    f"(i:Issue {{issue_id: {issue['id']}}}) "
                    f"CREATE (d1)-[:OPENED]->(i)"
                )
                developer_issue_relation_commands.append(neo4j_create_relation_dev_issue_statement)

            if closed_by:
                closed_by_standardized = standardize_name(closed_by)
                neo4j_create_relation_dev_issue_statement = (
                    f"MATCH (d2:Developer {{developer_name: '{closed_by_standardized}'}}), "
                    f"(i:Issue {{issue_id: {issue['id']}}}) "
                    f"CREATE (i)-[:CLOSED_BY]->(d2)"
                )
                developer_issue_relation_commands.append(neo4j_create_relation_dev_issue_statement)

        execute_nodes(developer_issue_relation_commands)