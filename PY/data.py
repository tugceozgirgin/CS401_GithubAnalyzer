# data.py

import json
from github import Github
from pydriller import Repository


excluded_extensions = {
    'compiled': ['.class', '.pyc', '.jar', '.iml', '.name', '.gitignore'],
    'system': ['.dll', '.exe', '.so']
}


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


def get_files_from_json(json_file_path='commit_data.json'):
    with open(json_file_path, 'r') as infile:
        commit_data = json.load(infile)

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


def get_developers_from_json(json_file_path='commit_data.json'):
    with open(json_file_path, 'r') as infile:
        commit_data = json.load(infile)

    developers = set()
    for commit in commit_data:
        developers.add(commit['author'])
    return list(developers)

def read_from_json(json_file_path):
    with open(json_file_path, 'r') as infile:
        data = json.load(infile)
    return data


def calculate_file_change_coverage(loaded_commit_data):
    file_counts = {}
    for commit in loaded_commit_data:
        author = commit['author']
        modified_files = commit['modified_files']
        file_counts[author] = file_counts.get(author, set()).union(set(modified_files))

    return file_counts


def calculate_file_change_coverage_ratio(file_counts, all_files):
    coverage_ratios = {}
    for author, changed_files in file_counts.items():
        coverage_ratio = len(changed_files) / len(all_files)
        coverage_ratios[author] = coverage_ratio

    return coverage_ratios



def extract_commit_data(github_link, dt1, dt2):
    commit_data = []
    for commit in Repository(github_link, since=dt1, to=dt2).traverse_commits():
        commit_date = commit.committer_date
        formatted_date = commit_date.strftime('%Y-%m-%d %H:%M:%S')
        commit_info = {
            'hash': commit.hash,
            'message': commit.msg,
            'author': commit.author.name,
            'author_mail': commit.author.email,
            'commit_date': formatted_date,
            'modified_files': [],
            'lines_inserted': [],
            'lines_deleted': []
        }
        for modified_file in commit.modified_files:
            file_name = modified_file.filename

            # Check if the file has an excluded extension
            excluded = any(file_name.endswith(ext) for ext in sum(excluded_extensions.values(), []))

            if not excluded:
                commit_info['modified_files'].append(file_name)

                lines_inserted = 0
                lines_deleted = 0
                for diff in modified_file.diff_parsed['added']:
                    lines_inserted += 1
                for diff in modified_file.diff_parsed['deleted']:
                    lines_deleted += 1

                commit_info['lines_inserted'].append(lines_inserted)
                commit_info['lines_deleted'].append(lines_deleted)

        commit_data.append(commit_info)
    return commit_data

def extract_issues(repo_url, access_token):
    try:
        g = Github("")

        # Extract username and repository name from the URL
        repo_url_parts = repo_url.strip('/').split('/')
        username, repo_name = repo_url_parts[-2:]

        repo = g.get_repo(f"{username}/{repo_name}")

        issues_data = []
        for issue in repo.get_issues(state='all'):
            issue_comments = issue.get_comments()

            opened_by = issue.user.name if issue.user.name else issue.user.login
            # opened_by_email = None
            # if issue.user:
            #     user = g.get_user(issue.user.login)
            #     opened_by_email = user.email

            if issue.closed_by:
                closed_by = issue.closed_by.name if issue.closed_by.name else issue.closed_by.login
            else:
                closed_by = None

            issue_data = {
                'id': issue.number,
                'title': issue.title,
                'description': issue.body,
                'state': issue.state,
                'created_at': issue.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'closed_at': issue.closed_at.strftime('%Y-%m-%d %H:%M:%S') if issue.closed_at else None,
                'closed_by': closed_by,
                'opened_by': opened_by,
                #'opener_mail': opened_by_email,
                'comments': [{'author': comment.user.login,
                              'comment_date': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                              'comment_text': comment.body} for comment in issue_comments]
            }
            issues_data.append(issue_data)

        return issues_data
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

def get_first_last_commit_dates(commit_data):
    return commit_data[0]["commit_date"], commit_data[-1]["commit_date"]

