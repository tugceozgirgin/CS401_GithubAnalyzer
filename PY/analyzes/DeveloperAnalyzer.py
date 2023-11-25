import itertools
from collections import defaultdict

from PY.api.data import get_commits_from_json


class DeveloperAnalyzer:
    def __init__(self, commit_data, github_link):
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
