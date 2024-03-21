import json

import pandas as pd
from neo4j import GraphDatabase

data_base_connection = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "password"))
session = data_base_connection.session()
delete_all_command = "MATCH (n) DETACH DELETE n"
session.run(delete_all_command)
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

def get_file_name(file_path):
    last_slash_index = file_path.rfind('/')
    if 0 <= last_slash_index < len(file_path) - 1:
        file_name = file_path[last_slash_index + 1:]
        if file_name.endswith('.java'):
            return file_name
    return None

df_change_set = pd.read_json("O:\proje\CS401_GithubAnalyzer\PY\json_files_for_validation\change_set_pig.json")#("../change_set.json")
df_change_set.columns = ['commit_hash', 'committed_date', 'committed_date_zoned', 'message', 'author', 'author_email', 'is_merged']
df_code_change = pd.read_csv("O:\proje\CS401_GithubAnalyzer\PY\json_files_for_validation\code_change_pig.csv")#("../code_change.csv")
df_code_change.columns = ['commit_hash', 'file_path', 'old_file_path', 'change_type', 'is_deleted', 'sum_added_lines', 'sum_removed_lines']

# print(len(df_change_set))
# print(len(df_code_change))

# Filter .java extennsions
java_changes = df_code_change[df_code_change['file_path'].str.endswith('.java')]

merged_df = pd.merge(java_changes, df_change_set, on='commit_hash', how='inner')

change_counts = merged_df.groupby('commit_hash').size()
valid_commits = change_counts.index[change_counts > 0]
final_df = merged_df[merged_df['commit_hash'].isin(valid_commits)]
pd.set_option('display.max_columns', None)  # Show all columns
pd.set_option('display.max_rows', 150)
pd.set_option('display.width', None)
print(len(final_df))

# remove duplicate commits with different commit hash
final_df.drop_duplicates(subset=['committed_date', 'committed_date_zoned', 'message', 'author', 'author_email', 'is_merged', 'file_path', 'old_file_path', 'change_type', 'is_deleted', 'sum_added_lines', 'sum_removed_lines'], inplace=True)
print(len(final_df))

# Filter out rows where is_merged column is equal to 1
final_df = final_df[final_df['is_merged'] != 1]
print(len(final_df))

# Count the number of unique authors
unique_authors_count = final_df['author'].nunique()
print("Number of unique authors:", unique_authors_count)

# Group by author email and collect unique author names for each email
author_groups = final_df.groupby('author_email')['author'].unique()

# Create a dictionary to store email to standardized author name mappings
lookup_table = {}

# Iterate through author groups to identify different names for the same email
for email, names in author_groups.items():
    # Check if there are different names for the same email
    if len(names) > 1:
        # Choose a standardized name (you can choose the first one for simplicity)
        standard_name = names[0]
        # Update the lookup table with email to standardized name mappings
        for name in names:
            lookup_table[name] = standard_name

# Use the lookup table to correct author names in the DataFrame
final_df['author'] = final_df['author'].map(lookup_table).fillna(final_df['author'])
print(len(final_df))
unique_authors_count = final_df['author'].nunique()
print("Number of unique authors:", unique_authors_count)
unique_commits_count = final_df['commit_hash'].nunique()
print("Number of unique commits:", unique_commits_count)


#Filter out rows where change_type column is equal to "DELETE"
final_df = final_df[final_df['change_type'] != 'DELETE']
print(len(final_df))
unique_authors_count = final_df['author'].nunique()
print("Number of unique authors:", unique_authors_count)
unique_commits_count = final_df['commit_hash'].nunique()
print("Number of unique commits:", unique_commits_count)

#Developer Nodes
unique_developers = final_df['author'].unique()
developer_data = {
    "id": range(1, len(unique_developers) + 1),
    "name": unique_developers
}
developer_list = pd.DataFrame(developer_data)
developer_execution_commands = []

for index, row in developer_list.iterrows():
    standardized_name = standardize_name(row['name'])  # Assuming standardize_name function is defined
    neo4j_create_statement = (
        f"CREATE (d:Developer {{developer_id: {row['id']}, developer_name: '{standardized_name}'}})"
    )
    developer_execution_commands.append(neo4j_create_statement)
execute_nodes(developer_execution_commands)

#File Nodes
file_names = final_df['file_path'].apply(get_file_name).unique()
print("Number of files:", len(file_names))

file_id = [i for i in range(1, len(file_names) + 1)]
file_data = {
    "id": file_id,
    "name": file_names
}
file_list = pd.DataFrame(file_data).values.tolist()
file_execution_commands = []
for i in file_list:
    neo4j_create_statement = "CREATE (f:Files {file_id:" + str(i[0]) + ", file_name:  '" + str(i[1]) + "'})"
    file_execution_commands.append(neo4j_create_statement)

execute_nodes(file_execution_commands)

#Create Commit Nodes' Cypher code and connect with Neo4j
commit_execution_commands = []

# Iterate over unique commit hashes
for commit_hash in final_df['commit_hash'].unique():
    commit_data = final_df[final_df['commit_hash'] == commit_hash]


    # Create Cypher statement for creating Commit Node
    neo4j_create_statement = (
        f"CREATE (c:Commit {{"
        f"commit_hash: '{commit_hash}', "
        # f"standardized_author: '{standardized_author}', "
        # f"commit_date: '{commit_date}', "
        # f"modified_files: {modified_files}, "
        f"lines_inserted: {commit_data['sum_added_lines'].sum()}, "
        f"lines_deleted: {commit_data['sum_removed_lines'].sum()} "
        # f"modified_file_names: {modified_file_names}"
        f"}})"
    )
    commit_execution_commands.append(neo4j_create_statement)


execute_nodes(commit_execution_commands)



relationship_commands1 = []

# Iterate through the DataFrame
for index, row in final_df.iterrows():
    commit_hash = row['commit_hash']
    author = standardize_name(row['author'])  # Assuming standardize_name function is defined

    commit_developer_relationship = (
        f"MATCH (c:Commit {{commit_hash: '{commit_hash}'}}), "
        f"(d:Developer {{developer_name: '{author}'}}) "
        "MERGE (c)-[:DEVELOPED_BY]->(d)"
    )
    relationship_commands1.append(commit_developer_relationship)

    # Create relationship between Developer-Commit
    developer_commit_relationship = (
        f"MATCH (c:Commit {{commit_hash: '{commit_hash}'}}), "
        f"(d:Developer {{developer_name: '{author}'}}) "
        "MERGE (d)-[:DEVELOPED]->(c)"
    )

    relationship_commands1.append(developer_commit_relationship)

execute_nodes(relationship_commands1)

relationship_commands2 = []

# Iterate through the DataFrame
for index, row in final_df.iterrows():
    commit_hash = row['commit_hash']
    file_name = get_file_name(row['file_path'])  # Assuming get_file_name function is defined

    # Create relationship between Commit-File
    commit_file_relationship = (
        f"MATCH (c:Commit {{commit_hash: '{commit_hash}'}}), "
        f"(f:Files {{file_name: '{file_name}'}}) "
        "MERGE (c)-[:MODIFIED]->(f)"
    )
    relationship_commands2.append(commit_file_relationship)

    # Create relationship between File-Commit
    file_commit_relationship = (
        f"MATCH (c:Commit {{commit_hash: '{commit_hash}'}}), "
        f"(f:Files {{file_name: '{file_name}'}}) "
        "MERGE (f)-[:MODIFIED_BY]->(c)"
    )
    relationship_commands2.append(file_commit_relationship)

execute_nodes(relationship_commands2)














# # keep only files with .java extension
# df_code_change['file_name'] = df_code_change['file_path'].apply(get_file_name)
# df_code_change = df_code_change[df_code_change['file_name'].isnull()]
# df_code_change.drop(columns=['file_name'], inplace=True)
# print()
# print(len(df_code_change))
# print(len(df_change_set))
#
# # remove duplicate row with different commit hash
# df_change_set = df_change_set.drop_duplicates(subset=df_change_set.columns.difference(['commit_hash']))
# print()
# print(len(df_code_change))
# print(len(df_change_set))
#
#
#
# #ignore is_merged=1 rows
# df_change_set = df_change_set[df_change_set['is_merged'] != 1]
# print()
# print(len(df_code_change))
# print(len(df_change_set))


# Developer Nodes
# df = pd.read_json("../change_set.json")
#
# # Group authors by their email addresses
# author_groups = df.groupby('author_email')['author'].unique()
#
# # Create a lookup table to map email addresses to standardized author names
# lookup_table = {}
# for email, authors in author_groups.items():
#     standardized_name = ' '.join(sorted(authors))
#     lookup_table[email] = standardized_name
#
# # Apply the lookup table to correct author names
# df['standardized_author'] = df['author_email'].map(lookup_table)
# unique_authors = df['standardized_author'].unique()
#
# print(unique_authors)

# df_developers.columns = ['commit_hash', 'committed_date', 'committed_date_zoned', 'message', 'author', 'author_email', 'is_merged']
#
# unique_developers = df_developers['author'].unique()
#
# developer_data = {
#     "id": range(1, len(unique_developers) + 1),
#     "name": unique_developers
# }
# developer_list = pd.DataFrame(developer_data)
# developer_execution_commands = []
# for index, row in developer_list.iterrows():
#     standardized_name = standardize_name(row['name'])  # Assuming standardize_name() function is defined
#     neo4j_create_statement = (
#         f"CREATE (d:Developer {{developer_id: {row['id']}, developer_name: '{standardized_name}'}})"
#     )
#     developer_execution_commands.append(neo4j_create_statement)
# execute_nodes(developer_execution_commands)


#File Nodes
# def get_file_name(file_path):
#     last_slash_index = file_path.rfind('/')
#     if 0 <= last_slash_index < len(file_path) - 1:
#         file_name = file_path[last_slash_index + 1:]
#         if file_name.endswith('.java'):
#             return file_name
#     return None
#
# df_files = pd.read_csv("../code_change.csv")
# df_files.columns = ['commit_hash', 'file_path', 'old_file_path', 'change_type', 'is_deleted', 'sum_added_lines', 'sum_removed_lines']
# file_names = df_files['file_path'].apply(get_file_name).unique()
# print(len(file_names))
# file_id = [i for i in range(1, len(file_names) + 1)]
# file_data = {
#     "id": file_id,
#     "name": file_names
# }
# file_list = pd.DataFrame(file_data).values.tolist()
# file_execution_commands = []
# for i in file_list:
#     neo4j_create_statement = "CREATE (f:Files {file_id:" + str(i[0]) + ", file_name:  '" + str(i[1]) + "'})"
#     file_execution_commands.append(neo4j_create_statement)
# execute_nodes(file_execution_commands)

# #Commit Node
# df_change_set = pd.read_json("../change_set.json")
# df_change_set.columns = ['commit_hash', 'committed_date', 'committed_date_zoned', 'message', 'author', 'author_email', 'is_merged']
# df_change_set = df_change_set[df_change_set['is_merged'] != 1]
# df_change_set = df_change_set.drop_duplicates(subset=df_change_set.columns.difference(['commit_hash']))
# print(df_change_set)

