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
print(len(df_code_change))
print(len(df_change_set))


# remove duplicate row with different commit hash
df_change_set = df_change_set.drop_duplicates(subset=df_change_set.columns.difference(['commit_hash']))
print()
print(len(df_code_change))
print(len(df_change_set))

# keep only files with .java extension
df_code_change['file_name'] = df_code_change['file_path'].apply(get_file_name)
df_code_change = df_code_change[df_code_change['file_name'].isnull()]
df_code_change.drop(columns=['file_name'], inplace=True)
print()
print(len(df_code_change))
print(len(df_change_set))

#ignore is_merged=1 rows
df_change_set = df_change_set[df_change_set['is_merged'] != 1]
print()
print(len(df_code_change))
print(len(df_change_set))


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

