"""
from typing import Dict, List
from neo4j import GraphDatabase

class GraphAlgorithms:
    def __init__(self, uri, username, password):
        self.uri = uri
        self.username = username
        self.password = password

    def dev_to_files(self, threshold):
        devs = self.get_developers()
        dev_to_file_reachable_files = {}

        for dev in devs:
            reachable_files = self.dfs(dev, threshold)
            dev_to_file_reachable_files[dev] = reachable_files

        return dev_to_file_reachable_files

    def dfs(self, start_node, threshold):
        with GraphDatabase.driver(self.uri, auth=(self.username, self.password)) as driver:
            with driver.session() as session:
                visited = set()
                stack = [start_node]
                reachable_files = set()

                while stack:
                    current_node = stack.pop()
                    if current_node not in visited:
                        visited.add(current_node)
                        reachable_files.add(current_node)

                        result = session.run(
                            f"MATCH (n:Developer)-[:MODIFIED]->(f:Files) WHERE n.developer_name = $developer AND f.file_name >= $threshold RETURN f.file_name",
                            developer=current_node, threshold=threshold
                        )
                        neighbors = [record["f.file_name"] for record in result]

                        for neighbor in neighbors:
                            if neighbor not in visited:
                                stack.append(neighbor)

        return reachable_files

    def find_jacks(self, threshold):
        dev_to_files = self.dev_to_files(threshold)
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

    def get_developers(self):
        with GraphDatabase.driver(self.uri, auth=(self.username, self.password)) as driver:
            with driver.session() as session:
                result = session.run("MATCH (d:Developer) RETURN d.developer_name AS developer_name")
                developers = [record["developer_name"] for record in result]

        return developers

    def get_num_files(self):
        all_files = set()
        with GraphDatabase.driver(self.uri, auth=(self.username, self.password)) as driver:
            with driver.session() as session:
                result = session.run("MATCH (f:Files) RETURN f.file_name")
                all_files.update(record["f.file_name"] for record in result)

        return len(all_files)

    def is_jack(self, dev_to_file_coverage, developer):
        return dev_to_file_coverage.get(developer, 0) > 0

# Usage
uri = "bolt://localhost:7687"
username = "neo4j"
password = "password"
threshold = 0.19  # You can adjust the threshold as needed

# Create an instance of GraphAlgorithms
graph_algorithms = GraphAlgorithms(uri, username, password)

# Call the FindJacks method with a threshold using the instance
result = graph_algorithms.find_jacks(threshold)

# Print the result to the console
print("Developer Classification:")
for developer, file_coverage in result.items():
    print(f"{developer}: {file_coverage:.2%} (Jack: {graph_algorithms.is_jack(result, developer)})")
"""