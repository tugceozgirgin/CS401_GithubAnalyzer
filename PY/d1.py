import json
from pydriller import Repository

# Write commit data to a JSON file
commit_data = []

for commit in Repository('https://github.com/Saeed-Muhaisen/PharmacyProject').traverse_commits():
    commit_info = {
        'hash': commit.hash,
        'message': commit.msg,
        'author': commit.author.name,
        'modified_files': [file.filename for file in commit.modified_files]
    }
    commit_data.append(commit_info)

output_file_path = 'commit_data.json'
with open(output_file_path, 'w') as outfile:
    json.dump(commit_data, outfile, indent=4)

print('Commit data written to', output_file_path)

# Load commit data from the JSON file
with open(output_file_path, 'r') as infile:
    loaded_commit_data = json.load(infile)

# Extract the author names from the commit data
author_names = [commit['author'] for commit in loaded_commit_data]

# Print the author names
print('Author names:')
for author in author_names:
    print(author)
