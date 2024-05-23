import base64
import json
import os
import time
from neo4j import GraphDatabase
from collections import defaultdict
from neo_db import NEO
import numpy as np
from flask import Flask, request, jsonify
from PY.data import dump_json_file, extract_commit_data
from flask_cors import CORS



class App:
    neo_instance = NEO()
    neo_instance.run()
    def __init__(self):
        self._uri = "bolt://localhost:7687"
        self._user = "neo4j"
        self._password = "password"
        self._driver = GraphDatabase.driver(self._uri, auth=(self._user, self._password))

    def run(self):
        data_base_connection = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "password"))
        session = data_base_connection.session()
        delete_all_command = "MATCH (n) DETACH DELETE n"
        session.run(delete_all_command)

    def close(self):
        self._driver.close()

    def execute_query(self, query):
        with self._driver.session() as session:
            session.run(query)

    def get_developer_names(self):
        with self._driver.session() as session:
            result = session.run("MATCH (d:Developer) RETURN d.developer_name AS developer_name")
            developer_names = [record["developer_name"] for record in result]
            return developer_names

    def get_developers(self):
        with self._driver.session() as session:
            result = session.run("MATCH (d:Developer) RETURN d.developer_id AS developer_id")
            developers = [record["developer_id"] for record in result]
            return developers


    def get_files_for_developer(self, developer_id):
        with self._driver.session() as session:
            result = session.run(
                "MATCH (d:Developer {developer_id: $developer_id})-[:DEVELOPED_BY]->(c:Commit)-[:MODIFIED]->(f:Files) RETURN f",
                developer_id=developer_id,
            )
            files = [record['f'] for record in result]
            return files

    def dfs(self, start_node, visited=None, reachable_files=None):
        if visited is None:
            visited = set()
        if reachable_files is None:
            reachable_files = set()

        visited.add(start_node)
        files = self.get_files_for_developer(start_node)
        reachable_files.update(files)

        with self._driver.session() as session:
            result = session.run(
                "MATCH (d:Developer {developer_id: $developer_id})-[:DEVELOPED_BY]->(:Commit)-[:MODIFIED]->(f:Files) "
                "RETURN f",
                developer_id=start_node,
            )
            files_from_commits = [record['f'] for record in result]
            reachable_files.update(files_from_commits)

            result = session.run(
                "MATCH (d:Developer {developer_id: $developer_id})<-[:DEVELOPED_BY]-(:Commit)<-[:MODIFIED_BY]-(f:Files) "
                "RETURN f",
                developer_id=start_node,
            )
            files_to_commits = [record['f'] for record in result]
            reachable_files.update(files_to_commits)

        for file in files_from_commits + files_to_commits:
            file_name = file['file_name']
            if file_name not in visited:
                self.dfs(file_name, visited, reachable_files)

        return reachable_files

    def dev_to_files(self):
        developers = self.get_developers()
        dev_to_reachable_files = {}

        for dev_id in developers:
            reachable_files = self.dfs(dev_id)
            dev_to_reachable_files[dev_id] = reachable_files

        return dev_to_reachable_files

    def get_num_files(self):
        all_files = set()
        with self._driver.session() as session:
                result = session.run("MATCH (f:Files) RETURN f.file_name")
                all_files.update(record["f.file_name"] for record in result)

        return len(all_files)

    def find_jacks(self):
        dev_to_files = self.dev_to_files()
        dev_to_file_coverage = {}
        num_files = self.get_num_files()

        for dev, files in dev_to_files.items():
            num_dev_files = len(files)
            file_coverage = num_dev_files / num_files if num_files > 0 else 0
            dev_to_file_coverage[dev] = file_coverage

        sorted_dev_to_file_coverage = self.sort_by_value(dev_to_file_coverage)
        return sorted_dev_to_file_coverage

    @staticmethod
    def sort_by_value(dictionary):
        sorted_items = sorted(dictionary.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_items)

    def is_jack(self, dev_to_file_coverage, developer):
        treshold = 0.19
        return dev_to_file_coverage.get(developer, 0) > treshold


    def dev_to_rare_files(self):
        dev_to_files = self.dev_to_files()
        dev_to_rare_files = defaultdict(list)

        for dev, files in dev_to_files.items():
            for file in files:
                if self.is_file_rare(file, dev_to_files):
                    dev_to_rare_files[dev].append(file)

        return dict(dev_to_rare_files)

    def is_file_rare(self, file, dev_to_files):
        count = 0
        for devs in dev_to_files.values():
            if file in devs:
                count += 1
        return count == 1

    def find_mavens(self, threshold):
        dev_to_rare_files = self.dev_to_rare_files()
        dev_to_mavenness = {}

        # Get the total number of rare files across all developers
        num_rare_files = sum(len(files) for files in dev_to_rare_files.values())

        for dev, files in dev_to_rare_files.items():
            num_dev_files = len(files)
            mavenness = num_dev_files / num_rare_files if num_rare_files > 0 else 0
            dev_to_mavenness[dev] = mavenness

        sorted_dev_to_mavenness = self.sort_by_value(dev_to_mavenness)
        return sorted_dev_to_mavenness


    def find_replacements_for_all(self):
        dev_to_files = self.dev_to_files()
        all_devs = set(dev_to_files.keys())

        all_replacements = {}

        for leaving_dev in all_devs:
            leaving_dev_files = dev_to_files.get(leaving_dev, set())
            other_devs = all_devs - {leaving_dev}

            dev_to_overlapping_knowledge = defaultdict(float)

            for dev in other_devs:
                dev_files = dev_to_files.get(dev, set())
                common_elements=0
                for file in leaving_dev_files:
                    for file2 in dev_files:
                        if(file['file_id']==file2['file_id']):
                            common_elements= common_elements+1
                overlapping_knowledge = common_elements / len(leaving_dev_files) if len(leaving_dev_files) > 0 else 0
                dev_to_overlapping_knowledge[dev] = overlapping_knowledge

            sorted_dev_to_overlapping_knowledge = self.sort_by_value(dev_to_overlapping_knowledge)
            all_replacements[leaving_dev] = sorted_dev_to_overlapping_knowledge

        return all_replacements

    def get_top_similar_developers(self, all_replacements_result, top_n=3):
        top_n_replacements_result = defaultdict(dict)

        for leaving_dev, replacements in all_replacements_result.items():
            top_n_replacements_result[leaving_dev] = {k: v for k, v in sorted(replacements.items(), key=lambda item: item[1], reverse=True)[:top_n]}

        return top_n_replacements_result





    def get_developer_lines_modified(self):
        developer_lines_modified = defaultdict(int)

        with self._driver.session() as session:
            result = session.run(
                "MATCH (d:Developer)-[:DEVELOPED]->(c:Commit)-[r:MODIFIED]->(f:Files) "
                "RETURN d.developer_id AS developer_id, SUM(r.inserted_lines + r.deleted_lines) AS total_lines_modified"
            )

            for record in result:
                developer_id = record['developer_id']
                total_lines_modified = record['total_lines_modified']

                # Increment lines modified for the developer
                developer_lines_modified[developer_id] += total_lines_modified

        return dict(developer_lines_modified)

    def calculate_commits_per_developer(self):
        commits_per_developer = {}

        with self._driver.session() as session:
            result = session.run(
                "MATCH (d:Developer)-[:DEVELOPED]->(c:Commit) "
                "RETURN d.developer_name AS developer_name, COUNT(c) AS commit_count"
            )

            for record in result:
                developer_name = record['developer_name']
                commit_count = record['commit_count']

                commits_per_developer[developer_name] = commit_count

        return commits_per_developer

    def calculate_files_per_developer(self):
        files_per_developer = {}

        with self._driver.session() as session:
            result = session.run(
                "MATCH (d:Developer)-[:DEVELOPED]->(c:Commit)-[:MODIFIED]->(f:Files) "
                "RETURN d.developer_name AS developer_name, COUNT(DISTINCT f) AS files_count"
            )

            for record in result:
                developer_name = record['developer_name']
                files_count = record['files_count']

                files_per_developer[developer_name] = files_count

        return files_per_developer

    def calculate_lines_per_developer(self):
        total_lines_modified = {}

        with self._driver.session() as session:
            result = session.run(
                "MATCH (d:Developer)-[:DEVELOPED]->(c:Commit)-[r:MODIFIED]->(f:Files) "
                "RETURN d.developer_name AS developer_name, "
                "SUM(r.inserted_lines + r.deleted_lines) AS total_lines_modified"
            )

            for record in result:
                developer_name = record['developer_name']
                total_lines_modified[developer_name] = record['total_lines_modified']

        return total_lines_modified


    def list_files_modified_per_developer(self):
        files_modified_per_developer = defaultdict(int)

        with self._driver.session() as session:
            result = session.run(
                "MATCH (d:Developer)-[:DEVELOPED]->(c:Commit)-[:MODIFIED]->(f:Files) "
                "RETURN c.commit_hash AS commit_hash, "
                "d.developer_id AS developer_id, COUNT(DISTINCT f) AS modified_file_count"
            )

            for record in result:
                commit_hash = record['commit_hash']
                developer_id = record['developer_id']
                modified_file_count = record['modified_file_count']
                files_modified_per_developer[(commit_hash, developer_id)] = modified_file_count

        return dict(files_modified_per_developer)

    def list_lines_modified_per_commit(self):
        lines_modified_per_commit = defaultdict(int)

        with self._driver.session() as session:
            result = session.run(
                "MATCH (d:Developer)-[:DEVELOPED]->(c:Commit)-[r:MODIFIED]->(f:Files) "
                "RETURN c.commit_hash AS commit_hash, d.developer_id AS developer_id, "
                "SUM(r.inserted_lines + r.deleted_lines) AS total_lines_modified"
            )

            for record in result:
                commit_hash = record['commit_hash']
                developer_id = record['developer_id']
                total_lines_modified = record['total_lines_modified']

                # Increment lines modified for the commit and developer
                lines_modified_per_commit[(commit_hash, developer_id)] += total_lines_modified

        return dict(lines_modified_per_commit)

    def list_lines_modified_per_developer(self):
        lines_modified_per_developer = defaultdict(int)

        with self._driver.session() as session:
            result = session.run(
                "MATCH (d:Developer)-[:DEVELOPED]->(c:Commit)-[r:MODIFIED]->(f:Files) "
                "RETURN d.developer_id AS developer_id, "
                "SUM(r.inserted_lines + r.deleted_lines) AS total_lines_modified"
            )

            for record in result:
                developer_id = record['developer_id']
                total_lines_modified = record['total_lines_modified']
                lines_modified_per_developer[developer_id] += total_lines_modified

        return dict(lines_modified_per_developer)




# Define excluded extensions for various file types
excluded_extensions = {
    'compiled': ['.class', '.pyc'],
    'system': ['.dll', '.exe', '.so']
}

app = Flask(__name__)
CORS(app)  # Enable CORS support for all resources

@app.route('/submit-github-link', methods=['POST'])
def submit_github_link():
    try:
        data = request.get_json()
        github_link = data.get('github_link')


        # Check if the GitHub link is provided
        if not github_link:
            return jsonify({'error': 'Please enter a GitHub link.'}), 400

        dt1 = None
        dt2 = None

        commit_data = extract_commit_data(github_link, dt1, dt2)
        output_file_path = 'commit_data.json'
        dump_json_file(output_file_path, commit_data)


        # Return success response
        return jsonify({'success': True}), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500



@app.route('/get-developer-info', methods=['GET'])
def get_developer_info():
    try:
        # Wait until commit_data.json is created
        output_file_path = 'commit_data.json'
        while not os.path.exists(output_file_path):
            time.sleep(1)

        app_instance = App()

        # Load commit data from the temporary JSON file
        with open(output_file_path, 'r') as infile:
            loaded_commit_data = json.load(infile)

        # Extract developer info

        developer_ids = app_instance.get_developers()  # Geliştirici ID'lerini alın
        developer_names = app_instance.get_developer_names()  # Geliştirici isimlerini alın

        developer_info = {
            'developerIDs': developer_ids,
            'developerNames': developer_names
        }
        print("get info 1")
        return jsonify(developer_info), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@app.route('/get-developer-info2', methods=['GET'])
def get_developer_info2():
    try:
        # Wait until commit_data.json is created
        output_file_path = 'commit_data.json'
        while not os.path.exists(output_file_path):
            time.sleep(1)

        app_instance = App()

        # Load commit data from the temporary JSON file
        with open(output_file_path, 'r') as infile:
            loaded_commit_data = json.load(infile)

        # Extract developer info
        developer_ids = app_instance.get_developers()
        developer_names = app_instance.get_developer_names()

        # Calculate JACK ratios for each developer
        developer_jack_ratios = app_instance.find_jacks()

        developer_info = {
            'developerIDs': developer_ids,
            'developerNames': developer_names,
            'JackRatios': developer_jack_ratios
        }
        #print(developer_jack_ratios)

        return jsonify(developer_info), 200

    except Exception as e:
        print("Error in get_developer_info2:", e)
        return jsonify({'error': 'Internal Server Error'}), 500



@app.route('/get-developer-info3', methods=['GET'])
def get_developer_info3():
    try:
        app_instance = App()

        # Extract developer info
        developer_ids = app_instance.get_developers()
        developer_names = app_instance.get_developer_names()

        # Calculate mavenness for each developer
        developer_maven = app_instance.find_mavens(0.8)

        developer_info = {
            'developerIDs': developer_ids,
            'developerNames': developer_names,
            'Maven': developer_maven
        }
        print("get info 3")
        #print(developer_maven)

        return jsonify(developer_info), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/get-developer-info4', methods=['GET'])
def get_developer_info4():
    try:
        app_instance = App()

        total_commit_count = sum(app_instance.calculate_commits_per_developer().values())
        total_file_count = app_instance.get_num_files()
        total_developer_count = len(app_instance.get_developers())
        developer_names = app_instance.get_developer_names()

        developer_info = {
                'total_commit_count': total_commit_count,
                'total_file_count': total_file_count,
                'total_developer_count': total_developer_count,
                'developer_names': developer_names
        }
        #print(total_commit_count)

        return jsonify(developer_info), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@app.route('/get-similarity', methods=['GET'])
def get_similarity():
    try:
        app_instance = App()

        # Calculate replacements for all developers
        all_replacements_result = app_instance.find_replacements_for_all()

        # Get top similar developers
        developer_similarity = app_instance.get_top_similar_developers(all_replacements_result)

        # Extract developer info
        developer_ids = app_instance.get_developers()
        #print(developer_ids)
        developer_names = app_instance.get_developer_names()

        developer_info = {
            'developerIDs': developer_ids,
            'developerNames': developer_names,
            'Similarity': developer_similarity
        }
        return jsonify(developer_info), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500




from flask import jsonify

@app.route('/get-chart-data', methods=['GET'])
def get_chart_data():
    try:
        app_instance = App()

        # Extract developer info
        developer_commits = app_instance.calculate_commits_per_developer()

        # Extracting developer names and commits count
        developer_names = list(developer_commits.keys())
        developer_counts = list(developer_commits.values())

        # Combine labels and data points into a dictionary
        chart_data = {
            'labels': developer_names,  # x axis labels
            'datapoints': developer_counts,
        }

        # Return the chart data
        return jsonify(chart_data), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@app.route('/get-chart-data2', methods=['GET'])
def get_chart_data2():
    try:
        app_instance = App()

        # Extract developer info
        developer_files = app_instance.calculate_files_per_developer()

        # Extracting developer names and commits count
        developer_names = list(developer_files.keys())
        developer_files_ = list(developer_files.values())

        # Combine labels and data points into a dictionary
        chart_data = {
            'labels': developer_names,  # x axis labels
            'datapoints': developer_files_,
        }

        # Return the chart data
        return jsonify(chart_data), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@app.route('/get-chart-data3', methods=['GET'])
def get_chart_data3():
    try:
        app_instance = App()

        # Extract lines modified per commit by each developer
        developer_lines = app_instance.calculate_lines_per_developer()

        # Extracting developer names and lines modified count
        developer_names = list(developer_lines.keys())
        developer_lines_ = list(developer_lines.values())

        # Combine labels and data points into a dictionary
        chart_data = {
            'labels': developer_names,  # x axis labels
            'datapoints': developer_lines_,
        }

        # Return the chart data
        return jsonify(chart_data), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/get-chart-data4', methods=['GET'])
def get_chart_data4():
    try:
        app_instance = App()

        all_replacements_result = app_instance.find_replacements_for_all()

        # Get all developers
        all_devs = list(all_replacements_result.keys())

        # Initialize similarity matrix
        similarity_matrix = []

        # Iterate through developers to populate similarity matrix
        for dev1 in all_devs:
            row = []
            for dev2 in all_devs:
                # If dev1 is the same as dev2, similarity is 1
                if dev1 == dev2:
                    similarity = 1.0
                else:
                    # Get similarity between dev1 and dev2
                    similarity = all_replacements_result[dev1].get(dev2, 0.0)  # Default to 0 if no similarity found
                row.append(similarity)
            similarity_matrix.append(row)

        # Return the similarity matrix
        return jsonify(similarity_matrix), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500



@app.route('/get_balanced', methods=['GET'])
def get_balanced():
    try:
        app_instance = App()

        # Assuming you have a function list_lines_modified_per_developer implemented somewhere
        lines_modified_per_developer = app_instance.list_lines_modified_per_developer()
        lines_modified_values = list(lines_modified_per_developer.values())

        # Calculate the average lines modified
        average_lines_modified = sum(lines_modified_values) / len(lines_modified_values)
        print(lines_modified_values)
        print(average_lines_modified)

        # Calculate the bin width for the histogram
        iqr = np.percentile(lines_modified_values, 75) - np.percentile(lines_modified_values, 25)
        bin_width = 2 * iqr / (len(lines_modified_values) ** (1 / 3))
        bin_width /= 4

        # Define the bins for the histogram
        min_value = min(lines_modified_values)
        max_value = max(lines_modified_values)
        bins = np.arange(min_value, max_value + bin_width, bin_width)

        developer_names = app_instance.get_developer_names()


        # Create data in Chart.js format
        chart_data = {
            'developerNames': developer_names,
            'lines_modified_values': lines_modified_values,
            'average_lines_modified': average_lines_modified,
            'bins': bins.tolist()  # Convert numpy array to list
        }

        return jsonify(chart_data), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5002)
