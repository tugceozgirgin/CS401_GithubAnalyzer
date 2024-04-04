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

df_change_set = pd.read_json("../change_set.json")
df_change_set.columns = ['commit_hash', 'committed_date', 'committed_date_zoned', 'message', 'author', 'author_email', 'is_merged']
df_code_change = pd.read_csv("../code_change.csv")
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

# remove duplicate commits with different commit hash
final_df.drop_duplicates(subset=['committed_date', 'committed_date_zoned', 'message', 'author', 'author_email', 'is_merged', 'file_path', 'old_file_path', 'change_type', 'is_deleted', 'sum_added_lines', 'sum_removed_lines'], inplace=True)


# Filter out rows where is_merged column is equal to 1
final_df = final_df[final_df['is_merged'] != 1]

# Count the number of unique authors
unique_authors_count = final_df['author'].nunique()

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


#Filter out rows where change_type column is equal to "DELETE"
final_df = final_df[final_df['change_type'] != 'DELETE']
print(final_df.head(50))
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

#Create Commit node
commit_df = pd.DataFrame(columns=['commit_id', 'commit_hash', 'commit_author', 'commit_date', 'modified_files', 'lines_inserted', 'lines_deleted'])
unique_commit_hashes = final_df['commit_hash'].unique()
commit_df = pd.DataFrame({'commit_hash': unique_commit_hashes})
commit_df['commit_id'] = commit_df.reset_index().index + 1
commit_author_mapping = final_df.set_index('commit_hash')['author'].to_dict()
commit_df['commit_author'] = commit_df['commit_hash'].map(commit_author_mapping)
commit_date_mapping = final_df.set_index('commit_hash')['committed_date'].to_dict()
commit_df['commit_date'] = commit_df['commit_hash'].map(commit_date_mapping)
def get_modified_files(commit_group):
    modified_files = commit_group['file_path'].apply(get_file_name).dropna().tolist()
    return modified_files

modified_files_df = final_df.groupby('commit_hash').apply(get_modified_files).reset_index(name='modified_files')
commit_df = pd.merge(commit_df, modified_files_df, on='commit_hash', how='left')

def get_lines_inserted(commit_group):
    lines_inserted = commit_group['sum_added_lines'].dropna().tolist()
    return lines_inserted

lines_inserted = final_df.groupby('commit_hash').apply(get_lines_inserted).reset_index(name='lines_inserted')
commit_df = pd.merge(commit_df, lines_inserted, on='commit_hash', how='left')

def get_lines_deleted(commit_group):
    lines_deleted = commit_group['sum_removed_lines'].dropna().tolist()
    return lines_deleted

lines_deleted = final_df.groupby('commit_hash').apply(get_lines_deleted).reset_index(name='lines_deleted')
commit_df = pd.merge(commit_df, lines_deleted, on='commit_hash', how='left')
commit_execution_commands = []
for index, row in commit_df.iterrows():
    commit_id = row['commit_id']
    commit_hash = row['commit_hash']
    commit_author = row['commit_author']
    commit_date = row['commit_date']
    modified_files = row['modified_files']
    lines_inserted = row['lines_inserted']
    lines_deleted = row['lines_deleted']
    standardized_author = standardize_name(commit_author)

    neo4j_create_statement = (
        f"CREATE (c:Commit {{commit_id: {commit_id}, commit_hash: '{commit_hash}', "
        f"commit_author: '{standardized_author}', commit_date: '{commit_date}', "
        f"modified_files: {modified_files}, lines_inserted: {lines_inserted}, "
        f"lines_deleted: {lines_deleted}}})"
    )

    commit_execution_commands.append(neo4j_create_statement)

neo4j_create_relation_dev_statement_commit = (
            "MATCH (c:Commit), (d:Developer) "
            "WHERE c.commit_author = d.developer_name "
            "MERGE (c)-[:DEVELOPED_BY]->(d)"
        )
commit_execution_commands.append(neo4j_create_relation_dev_statement_commit)
bidirectional_dev_commit_relation = (
            "MATCH (c:Commit), (d:Developer) "
            "WHERE c.commit_author = d.developer_name "
            "MERGE (d)-[:DEVELOPED]->(c)"
        )
commit_execution_commands.append(bidirectional_dev_commit_relation)
execute_nodes(commit_execution_commands)
