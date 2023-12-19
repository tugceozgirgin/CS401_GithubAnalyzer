import datetime as dt
import json
from typing import Dict, List

import pandas as pd
from PY.api.data import get_files_from_json, \
    get_developers_from_json, read_from_json, get_all_files, \
    calculate_file_change_coverage, calculate_file_change_coverage_ratio, get_first_last_commit_dates
from neo4j import GraphDatabase

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
    print(days_in_graph)
    days_passed = days_in_graph - calculate_date_difference_in_days(first_date, targetdate)
    print(days_passed)
    return 1 - (days_passed / days_in_graph)


def calculate_date_difference_in_days(first_date_str, last_date_str):
    first_date = dt.datetime.strptime(first_date_str, '%Y-%m-%d %H:%M:%S')
    last_date = dt.datetime.strptime(last_date_str, '%Y-%m-%d %H:%M:%S')
    difference = last_date - first_date
    return difference.days


class NEO:
    def __init__(self, github_link):
        self.github_link = github_link

    def run(self):
        # Add this section to delete all existing nodes
        data_base_connection = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "password"))
        session = data_base_connection.session()
        delete_all_command = "MATCH (n) DETACH DELETE n"
        session.run(delete_all_command)

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

        # Create Issue Nodes
        issues_data = read_from_json("issue_data.json")
        issue_execution_commands = []
        for issue in issues_data:
            neo4j_create_statement = (
                    "CREATE (i:Issue {"
                    "issue_id: " + str(issue['id']) + ", "
                                                      "title: '" + issue['title'].replace("'", "\\'") + "', "
                                                                                                        "description: '" +
                    issue['description'].replace("'", "\\'") + "', "
                                                               "state: '" + issue['state'] + "', "
                                                                                             "created_at: '" + issue[
                        'created_at'] + "', "
                                        "closed_at: " + (
                        f"'{issue['closed_at']}'" if issue['closed_at'] is not None else "null") + ", "
                                                                                                   "closed_by: " + (
                        f"'{issue['closed_by']}'" if issue['closed_by'] is not None else "null") + ", "
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

        # Create relationships between Commit-Developer
        neo4j_create_relation_dev_statement = (
            "MATCH (c:Commit), (d:Developer) "
            "WHERE c.commit_author = d.developer_name "
            "MERGE (d)-[:DEVELOPED_BY]->(c)"
        )
        commit_execution_commands.append(neo4j_create_relation_dev_statement)
        execute_nodes(commit_execution_commands)

        # Create relationships between Commit-File based on modified_files
        commit_file_relation_commands = []

        for commit in commit_data:
            commit_hash = commit['hash']
            modified_files = commit['modified_files']
            lines_inserted = commit['lines_inserted']
            lines_deleted = commit['lines_deleted']
            recency = calculate_recency(commit['commit_date'])
            distance = calculate_date_difference_in_days(first_date,last_date) if recency == 0 else 1 / recency

            for idx, file_name in enumerate(modified_files):
                inserted = lines_inserted[idx]
                deleted = lines_deleted[idx]

                neo4j_create_relation_file_statement = (
                    f"MATCH (c:Commit {{commit_hash: '{commit_hash}'}}), "
                    f"(f:Files {{file_name: '{file_name}'}}) "
                    f"CREATE (c)-[:MODIFIED {{inserted_lines: {inserted}, deleted_lines: {deleted},distance: {distance}}}]->(f)"
                )
                commit_file_relation_commands.append(neo4j_create_relation_file_statement)

        execute_nodes(commit_file_relation_commands)

    def analyze_developers1(self):
        all_files = get_all_files(commit_data)

        file_counts = calculate_file_change_coverage(commit_data)
        coverage_ratios = calculate_file_change_coverage_ratio(file_counts, all_files)

        self.classify_developers_and_update_neo4j(coverage_ratios, file_counts)

    def calculate_developers_per_file(self, loaded_commit_data):
        developers_per_file = {}
        for commit in loaded_commit_data:
            author = commit['author']
            modified_files = commit['modified_files']
            for file in modified_files:
                developers_per_file[file] = developers_per_file.get(file, set()).union({author})

        return developers_per_file

    def find_files_modified_by_fewest_developers(self, developers_per_file):
        min_developers = float('inf')
        files_modified_by_fewest = set()

        for file, developers in developers_per_file.items():
            num_developers = len(developers)
            if num_developers < min_developers:
                min_developers = num_developers
                files_modified_by_fewest = {file}
            elif num_developers == min_developers:
                files_modified_by_fewest.add(file)

        return files_modified_by_fewest

    def calculate_mavenness(self, file_counts, developers_per_file, threshold=2) -> Dict[str, float]:
        rarely_reached_files = set()

        # Step 1: Identify rarely reached files based on the threshold
        for file, developers in developers_per_file.items():
            if developers <= threshold:
                rarely_reached_files.add(file)

        mavenness_per_developer = {}

        # Step 2: Calculate mavenness for each developer
        for developer, files in file_counts.items():
            developers = developers_per_file.get(developer, 0)  # Ensure developers is an integer
            rarely_reached_files_for_developer = rarely_reached_files.intersection(files)
            mavenness = len(rarely_reached_files_for_developer) / len(
                rarely_reached_files) if rarely_reached_files else 0
            mavenness_per_developer[developer] = mavenness

        return mavenness_per_developer

    def calculate_developers_per_file_count(self, commit_data) -> Dict[str, int]:
        developers_per_file_count = {}
        for commit in commit_data:
            author = commit['author']
            modified_files = commit['modified_files']

            for modified_file in modified_files:
                developers_per_file_count[modified_file] = developers_per_file_count.get(modified_file, 0) + 1

        return developers_per_file_count

    # Inside your analyze_developers method
    # Inside your analyze_developers2 method
    def analyze_developers2(self):
        all_files = get_all_files(commit_data)

        file_counts = calculate_file_change_coverage(commit_data)
        coverage_ratios = calculate_file_change_coverage_ratio(file_counts, all_files)

        developers_per_file_count = self.calculate_developers_per_file_count(commit_data)
        mavenness_per_developer = self.calculate_mavenness(file_counts, developers_per_file_count)

        # Classify developers and update Neo4j
        self.classify_developers_and_update_neo4j(coverage_ratios, file_counts, mavenness_per_developer)

        all_files = get_all_files(commit_data)

        file_counts = calculate_file_change_coverage(commit_data)
        coverage_ratios = calculate_file_change_coverage_ratio(file_counts, all_files)

        developers_per_file = self.calculate_developers_per_file(commit_data)
        files_modified_by_fewest = self.find_files_modified_by_fewest_developers(developers_per_file)

        # Print or store information about Mavenness for each developer
        with open('mavenness_classification.txt', 'w') as mavenness_output_file:
            total_rarely_reached_files = sum(1 for mavenness in mavenness_per_developer.values() if mavenness > 0)
            mavenness_output_file.write(f"Total Rarely Reached Files: {total_rarely_reached_files}\n\n")

            mavenness_output_file.write("Mavenness for each Developer:\n")
            for developer, mavenness in mavenness_per_developer.items():
                mavenness_output_file.write(f"{developer}: {mavenness:.2%}\n")

            mavenness_output_file.write("\nFiles modified by the fewest developers:\n")
            for modified_file in files_modified_by_fewest:
                mavenness_output_file.write(f"{modified_file}: {len(developers_per_file[modified_file])} developers\n")

    # Inside your NEO class
    def classify_developers_and_update_neo4j(self, coverage_ratios, file_counts, mavenness_per_developer,
                                             threshold=0.19):
        classified_developers = {}
        total_files_changed = {}

        for author, ratio in coverage_ratios.items():
            classification = 'Jack' if ratio > threshold else 'Not Jack'
            classified_developers[author] = classification
            total_files_changed[author] = len(file_counts[author])

        # Update Neo4j with developer classification
        neo4j_update_commands = []
        for author, classification in classified_developers.items():
            # Add classification based on Mavenness
            mavenness_classification = mavenness_per_developer.get(author, 0.0)
            neo4j_update_commands.append(
                f"MATCH (d:Developer {{developer_name: '{author}'}}) "
                f"SET d.classification = '{classification}', d.mavenness_classification = {mavenness_classification}"
            )

        execute_nodes(neo4j_update_commands)

        # Write classification and file information to a file
        with open('developer_classifications.txt', 'w') as file:
            file.write("Developer Classifications:\n")
            for author, classification in classified_developers.items():
                file.write(f"{author}: {classification}\n")

            total_files = sum(total_files_changed.values())
            file.write("\nDeveloper File Information:\n")
            file.write(f"Threshold: {threshold}\n")
            file.write(f"Total files: {total_files}\n\n")

            for author, files_changed in total_files_changed.items():
                ratio = (files_changed / total_files) * 100
                file.write(f"{author}: Files Changed - {files_changed}, Ratio - {ratio:.2f}%\n")
