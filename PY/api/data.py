# data.py

import json
from pydriller import Repository
from datetime import datetime, timedelta, timezone
excluded_extensions = {
    'compiled': ['.class', '.pyc'],
    'system': ['.dll', '.exe', '.so']
}
def extract_commit_data(github_link):
    commit_data = []
    for commit in Repository(github_link).traverse_commits():
        commit_date = commit.committer_date
        formatted_date = commit_date.strftime('%Y-%m-%d %H:%M:%S')
        commit_info = {
            'hash': commit.hash,
            'message': commit.msg,
            'author': commit.author.name,
            'commit_date': formatted_date,
            'modified_files': [file.filename for file in commit.modified_files]
        }
        commit_data.append(commit_info)
    return commit_data

def dump_json_file(output_file_path, commit_data):
    with open(output_file_path, 'w') as outfile:
        json.dump(commit_data, outfile, indent=4)
    print('Commit data written to', output_file_path)

def get_all_files(commit_data):
    files = set()
    for commit in commit_data:
        for modified_file in commit['modified_files']:
            # Check if the file has an excluded extension
            skip_file = False
            for ext_type, extensions in excluded_extensions.items():
                if any(modified_file.endswith(ext) for ext in extensions):
                    skip_file = True
                    break

            if not skip_file:
                files.add(modified_file)

    return list(files)

def get_all_developers(commit_data):
    developers = set()
    for commit in commit_data:
        developers.add(commit['author'])
    return list(developers)


def extract_commit_data_by_time(github_link,dt1,dt2):
    commit_data = []
    for commit in Repository(github_link, since=dt1, to=dt2).traverse_commits():
        commit_date = commit.committer_date
        formatted_date = commit_date.strftime('%Y-%m-%d %H:%M:%S')
        commit_info = {
            'hash': commit.hash,
            'message': commit.msg,
            'author': commit.author.name,
            'commit_date': formatted_date,
            'modified_files': [file.filename for file in commit.modified_files]
        }
        commit_data.append(commit_info)
    return commit_data

def extract_author_commit_counts(loaded_commit_data):
    author_commit_counts = {}
    for commit in loaded_commit_data:
        author = commit['author']
        author_commit_counts[author] = author_commit_counts.get(author, 0) + 1
    return author_commit_counts

def extract_changed_classes(loaded_commit_data):
    changed_classes = {}

    for commit in loaded_commit_data:
        author = commit['author']
        for modified_file in commit['modified_files']:
            # Check if the file has an excluded extension
            skip_file = False
            for ext_type, extensions in excluded_extensions.items():
                if any(modified_file.endswith(ext) for ext in extensions):
                    skip_file = True
                    break
            if not skip_file:
                changed_classes.setdefault(author, []).append(modified_file)
    return changed_classes