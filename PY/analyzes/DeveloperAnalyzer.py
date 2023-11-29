import itertools
from collections import defaultdict, Counter
import matplotlib.pyplot as plt

from PY.api.data import read_from_json

class DeveloperAnalyzer:
    def __init__(self, commit_data, github_link=None):
        self.commit_data = commit_data
        self.developers = self.get_developers()
        self.github_link = github_link

    def get_developers(self):
        developers = set()
        for commit in self.commit_data:
            developers.add(commit['author'])
        return list(developers)

    def get_modified_files_by_developer(self, developer):
        modified_files = set()
        for commit in self.commit_data:
            if commit['author'] == developer:
                modified_files.update(commit['modified_files'])
        return modified_files

    def calculate_similarity_ratio(self, developer1, developer2):
        files_developer1 = self.get_modified_files_by_developer(developer1)
        files_developer2 = self.get_modified_files_by_developer(developer2)

        common_files = files_developer1.intersection(files_developer2)
        all_files = files_developer1.union(files_developer2)

        similarity_ratio = len(common_files) / len(all_files) if len(all_files) > 0 else 0
        return similarity_ratio

    def find_most_compatible_developer(self, target_developer):
        compatibility_scores = defaultdict(float)

        for developer in self.developers:
            if developer != target_developer:
                similarity_ratio = self.calculate_similarity_ratio(target_developer, developer)
                compatibility_scores[developer] = similarity_ratio

        most_compatible_developer = max(compatibility_scores, key=compatibility_scores.get)
        return most_compatible_developer, compatibility_scores[most_compatible_developer]

    def show_similarity_ratios(self):
        with open('similarity.txt', 'w') as outfile:
            for pair in itertools.combinations(self.developers, 2):
                developer1, developer2 = pair
                similarity_ratio = self.calculate_similarity_ratio(developer1, developer2)
                result = f"Similarity Ratio between {developer1} and {developer2}: {similarity_ratio:.2%}\n"
                outfile.write(result)

    def run_analysis(self):
        self.show_similarity_ratios()

        # İstediğiniz geliştirici için en uyumlu kişiyi bulmak için:
        target_developer = "hedef_gelistirici"
        compatible_developer, compatibility_score = self.find_most_compatible_developer(target_developer)
        result = f"The most compatible developer for {target_developer} is {compatible_developer} with a similarity ratio of {compatibility_score:.2%}\n"
        with open('similarity.txt', 'a') as outfile:
            outfile.write(result)

    def count_commits_per_developer(self):
        commits_per_developer = Counter(commit['author'] for commit in self.commit_data)
        return commits_per_developer

    def find_min_max_commit_developers(self):
        commits_per_developer = self.count_commits_per_developer()
        min_commit_developer = min(commits_per_developer, key=commits_per_developer.get)
        max_commit_developer = max(commits_per_developer, key=commits_per_developer.get)
        min_commit_count = commits_per_developer[min_commit_developer]
        max_commit_count = commits_per_developer[max_commit_developer]

        return min_commit_developer, max_commit_developer, min_commit_count, max_commit_count

    def check_commit_difference_threshold(self, threshold=0.1):
        min_commit_developer, max_commit_developer, min_commit_count, max_commit_count = self.find_min_max_commit_developers()

        difference_percentage = (max_commit_count - min_commit_count) / max_commit_count

        if difference_percentage > threshold:
            print(f"Commit difference between {min_commit_developer} and {max_commit_developer} exceeds the threshold.")
        else:
            print(f"Commit difference between {min_commit_developer} and {max_commit_developer} is within the threshold.")

    def plot_commits_per_developer(self):
        commits_per_developer = Counter(commit['author'] for commit in self.commit_data)
        developers = list(commits_per_developer.keys())
        commit_counts = list(commits_per_developer.values())

        plt.bar(developers, commit_counts, color='blue')
        plt.xlabel('Developers')
        plt.ylabel('Commit Counts')
        plt.title('Commit Counts per Developer')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        plt.show()

    def count_modified_files_by_developer(self):
        modified_files_per_developer = defaultdict(list)

        for commit in self.commit_data:
            developer = commit['author']
            new_modified_files = commit.get('modified_files', [])

            # Exclude files that were modified in previous commits
            new_files_to_count = [file for file in new_modified_files if file not in modified_files_per_developer[developer]]

            modified_files_per_developer[developer].extend(new_files_to_count)

        return {developer: len(files) for developer, files in modified_files_per_developer.items()}

    def compare_file_counts(self, threshold=0.1):
        modified_files_per_developer = self.count_modified_files_by_developer()

        for (developer1, count1), (developer2, count2) in itertools.combinations(modified_files_per_developer.items(), 2):
            file_difference_percentage = abs(count1 - count2) / max(count1, count2)

            if file_difference_percentage < threshold:
                print(
                    f"File count difference between {developer1} and {developer2} is below the threshold: {file_difference_percentage:.2%}")

    def plot_file_counts_per_developer(self):
        modified_files_per_developer = self.count_modified_files_by_developer()

        developers = list(modified_files_per_developer.keys())
        file_counts = [count for (_, count) in modified_files_per_developer.items()]

        plt.bar(developers, file_counts, color='green')
        plt.xlabel('Developers')
        plt.ylabel('Modified Files Counts')
        plt.title('Modified Files Counts per Developer')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        plt.show()

    def count_modified_lines_by_developer(self):
        modified_lines_per_developer = {}

        for commit in self.commit_data:
            developer = commit['author']
            lines_inserted = sum(lines for lines in commit.get('lines_inserted', []))
            lines_deleted = sum(lines for lines in commit.get('lines_deleted', []))

            modified_lines = lines_inserted - lines_deleted

            if developer in modified_lines_per_developer:
                modified_lines_per_developer[developer] += modified_lines
            else:
                modified_lines_per_developer[developer] = modified_lines

        return modified_lines_per_developer

    def compare_lines_modified_per_developer(self, threshold=0.1):
        modified_lines_per_developer = self.count_modified_lines_by_developer()

        for (developer1, count1), (developer2, count2) in itertools.combinations(modified_lines_per_developer.items(), 2):
            lines_difference_percentage = abs(count1 - count2) / max(count1, count2)

            if lines_difference_percentage > threshold:
                print(f"Lines modified difference between {developer1} and {developer2} exceeds the threshold.")

    def plot_lines_per_developer(self):
        modified_lines_per_developer = self.count_modified_lines_by_developer()

        developers = list(modified_lines_per_developer.keys())
        lines_counts = list(modified_lines_per_developer.values())

        plt.bar(developers, lines_counts, color='orange')
        plt.xlabel('Developers')
        plt.ylabel('Lines Modified')
        plt.title('Lines Modified per Developer')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        plt.show()