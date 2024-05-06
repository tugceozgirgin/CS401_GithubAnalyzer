import numpy as np
from neo4j import GraphDatabase
from collections import defaultdict
import plotly.graph_objs as go



from PY.neo_db import NEO


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

