from collections import defaultdict

from matplotlib import pyplot as plt
from neo4j import GraphDatabase

class GraphAlgorithms:
    def __init__(self):
        self._uri = "bolt://localhost:7687"
        self._user = "neo4j"
        self._password = "password"
        self._driver = GraphDatabase.driver(self._uri, auth=(self._user, self._password))

    def close(self):
        self._driver.close()

    def execute_query(self, query):
        with self._driver.session() as session:
            session.run(query)

    def get_all_nodes(self):
        query = "MATCH (n) RETURN n"
        with self._driver.session() as session:
            result = session.run(query)
            nodes = [record['n'] for record in result]
            return nodes

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
                print(dev_to_files)

            sorted_dev_to_overlapping_knowledge = self.sort_by_value(dev_to_overlapping_knowledge)
            all_replacements[leaving_dev] = sorted_dev_to_overlapping_knowledge

        return all_replacements



# Graph instance creation and function execution
graph = GraphAlgorithms()
# developers = graph.get_developers()
# print(developers)
# reachable_files = graph.dev_to_files()
# print(reachable_files)
#
# result = graph.find_jacks()
# # Print the result to the console
# print("Developer Classification:")
# for developer, file_coverage in result.items():
#     print(f"{developer}: {file_coverage:.2%} (Jack: {graph.is_jack(result, developer)})")
#
# # Extract developers and their corresponding Jack percentages
# developers = list(result.keys())
# jack_percentages = [result[developer] for developer in developers]
#
# # Plotting
# plt.figure(figsize=(10, 6))
# plt.bar(developers, jack_percentages, color='blue')
# plt.title('Jack Percentage for Each Developer')
# plt.xlabel('Developers')
# plt.ylabel('Jack Percentage')
# plt.ylim(0, 1)  # Set the y-axis limit to represent percentages (0% to 100%)
#
#
# plt.show()
#
# threshold_value = 0.5  # You can adjust the threshold as needed
# rare_files_result = graph.dev_to_rare_files()
# # print("Rarely Reached Files per Developer:")
# # for developer, files in rare_files_result.items():
# #     print(f"{developer}: {files}")
#
# mavens_result = graph.find_mavens(threshold_value)
# print("Mavenness per Developer:")
# for developer, mavenness in mavens_result.items():
#     print(f"{developer}: {mavenness:.2%}")
#
# developers_mavenness = list(mavens_result.keys())
# mavenness_values = [mavens_result[developer] for developer in developers_mavenness]
#
# # Plotting Mavenness
# plt.figure(figsize=(10, 6))
# plt.bar(developers_mavenness, mavenness_values, color='orange')
# plt.title('Mavenness per Developer')
# plt.xlabel('Developers')
# plt.ylabel('Mavenness')
#
#
# plt.show()


all_replacements_result = graph.find_replacements_for_all()


# # Print the result to the console
for leaving_dev, replacements in all_replacements_result.items():
    print(f"Potential Best Replacement for {leaving_dev}:")

    best_replacement, overlapping_knowledge = max(replacements.items(), key=lambda x: x[1])
    print(f"  {best_replacement}: Overlapping Knowledge - {overlapping_knowledge:.2%}")

graph.close()


