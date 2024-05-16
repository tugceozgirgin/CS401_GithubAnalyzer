import json
from collections import defaultdict
from datetime import datetime

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


pd.set_option('display.max_columns', None)  # Show all columns
pd.set_option('display.max_rows', 150)
pd.set_option('display.width', None)

hadoop_author_mapping = {
    "=": "carlo curino",
    "aaron myers": "aaron twining myers",
    "aaron t. myers": "aaron twining myers",
    "alejandro abdelnur": "alejandro humberto abdelnur",
    "amareshwari sriramadasu": "amareshwari sri ramadasu",
    "arp": "arpit agarwal",
    "arun murthy": "arun c. murthy",
    "brandonli": "brandon li",
    "ccurino": "carlo curino",
    "clamb": "charles lamb",
    "chensammi": "sammi chen",
    "chris douglas": "christopher douglas",
    "chun-yang chen": "scott chun-yang chen",
    "cnauroth": "chris nauroth",
    "colin mccabe": "colin patrick mccabe",
    "colin p. mccabe": "colin patrick mccabe",
    "devaraj k": "devarajulu k",
    "doug cutting": "douglass cutting",
    "drankye": "kai zheng",
    "inigo": "inigo goiri",
    "jakob homan": "jakob glen homan",
    "jason lowe": "jason darrell lowe",
    "jian": "jian he",
    "jitendra pandey": "jitendra nath pandey",
    "jonathan eagles": "jonathan turner eagles",
    "junping_du": "junping du",
    "konstantin boudnik": "konstantin i boudnik",
    "konstantin shvachko": "konstantin v shvachko",
    "mattf": "matthew j. foley",
    "matthew foley": "matthew j. foley",
    "ravi  gummadi": "ravi gummadi",
    "rohithsharmaks": "rohith sharma k s",
    "sandy ryza": "sanford ryza",
    "stack": "michael stack",
    "subru": "subru krishnan",
    "sunil": "sunil g",
    "sunilg": "sunil g",
    "tgraves": "thomas graves",
    "tsz-wo sze": "tsz-wo nicholas sze",
    "uma mahesh": "uma maheswara rao g",
    "vinayakumarb": "vinayakumar b",
    "vinod kumar vavilapalli (i am also known as @tshooter.)": "vinod kumar vavilapalli",
    "vrushali": "vrushali channapattan",
    "vrushali c": "vrushali channapattan",
    "waltersu4549": "walter su",
    "wenxinhe": "wenxin he",
    "xuan": "xuan gong",
    "xuangong": "xuan gong",
    "yliu": "yi liu",
    "zhezhang": "zhe zhang",
}

pig_author_mapping = {
    "daijy": "jianyong dai",
    "rohini": "rohini palaniswamy",
}
hive_author_mapping = {
    "aihuaxu": "aihua xu",
    "amareshwari sriramadasu": "amareshwari sri ramadasu",
    "author: teddy choi": "teddy choi",
    "chao sun": "sun chao",
    "chengxiang": "chengxiang li",
    "chinnrao l": "chinna r lalam",
    "chinna rao l": "chinna r lalam",
    "ctang": "chaoyu tang",
    "daniel dai": "jianyong dai",
    "dapeng sun": "sun dapeng",
    "gopal v": "gopal vijayaraghavan",
    "haindrich zoltán (kirk)": "zoltan haindrich",
    "iilya yalovyy": "illya yalovyy",
    "ke jia": "jia ke",
    "jpullokk": "john pullokkaran",
    "mithun rk": "mithun radhakrishnan",
    "pengchengxiong": "pengcheng xiong",
    "prasanth j": "prasanth jayachandran",
    "ran gu": "ran wu",
    "sahil takir": "sahil takiar",
    "sankarh": "sankar hariappan",
    "sergey": "sergey shelukhin",
    "sergio peña": "sergio pena",
    "thejas nair": "thejas m nair",
    "vikram": "vikram dixit k",
    "wei": "wei zheng",
    "xzhang": "xuefu zhang",
}
zookeeper_author_mapping = {
    "andor molnár": "andor molnar",
    "flavio junqueira": "flavio paiva junqueira",
    "fpj": "flavio paiva junqueira",
    "patrick hunt": "patrick d. hunt",
    "raúl gutiérrez segalés": "raul gutierrez segales",
    "raúl gutierrez s": "raul gutierrez segales",
    "robert evans": "robert (bobby) evans",
}


def get_commits():
    # Load the data from a JSON file
    df_change_set = pd.read_json("../json_files_for_validation/change_set_hive.json")

    # Rename the columns to match the attributes you're interested in
    df_change_set.columns = ['commit_hash', 'committed_date', 'committed_date_zoned', 'message', 'author',
                             'author_email', 'is_merged']

    # Filter out merged commits and sort by the committed date
    filtered_commits = df_change_set[df_change_set['is_merged'] == 0].sort_values(by='committed_date')

    # Select the columns you need
    return filtered_commits[['commit_hash', 'author', 'committed_date']].values.tolist()


def get_commit_to_codechanges():
    df_code_change = pd.read_csv("../csv_files/code_change_hive.csv")
    df_code_change.columns = ['commit_hash', 'file_path', 'old_file_path', 'change_type', 'is_deleted',
                              'sum_added_lines', 'sum_removed_lines']

    # Filter the code changes to include only Java files
    df_code_change = df_code_change[df_code_change['file_path'].str.endswith('.java')]

    # Create a dictionary to map commit hashes to code changes
    commit_to_codechanges = defaultdict(list)
    for index, row in df_code_change.iterrows():
        fname = row['file_path'][row['file_path'].rfind("/") + 1:]
        commit_to_codechanges[row['commit_hash']].append(
            (row['file_path'], row['change_type'], fname, row['sum_added_lines'], row['sum_removed_lines'])
        )

    return commit_to_codechanges


# Get the mapping from commit hash to code changes
commit_to_codechanges = get_commit_to_codechanges()
commits = get_commits()

current_files = set()
change_set_jsons = []
prev_comparison_str = ""

developer_id = 0
unique_developers = set()
for commit_hash, author, date in commits:

    if commit_hash not in commit_to_codechanges:
        continue

    change_set_dict = {}
    change_set_dict["commit_hash"] = commit_hash
    author = author.lower()
    author = hive_author_mapping.get(author, author)
    change_set_dict["author"] = author

    unique_developers.add(author)
    change_set_dict["date"] = date

    fname_to_cchanges = defaultdict(list)

    for fpath, ctype, fname, num_added, num_deleted in commit_to_codechanges[
        commit_hash
    ]:
        fname_to_cchanges[fname].append(
            {
                "ctype": ctype,
                "fpath": fpath,
                "num_added": num_added,
                "num_deleted": num_deleted,
            }
        )

        # Find code changes in the commit
        extracted_changes = []
        for fname, cchanges_queue in fname_to_cchanges.items():
            while cchanges_queue:
                extracted_change = None

                # Pop one code change from the queue
                cchange = cchanges_queue.pop(0)

                # Check ADD and DELETE types for RENAME
                if cchange["ctype"] == "ADD":  # Possible RENAME
                    # Search for corresponding DELETE
                    for cc in cchanges_queue:
                        if (
                                cc["ctype"] == "DELETE"
                                and cc["num_deleted"] == cchange["num_added"]
                        ):  # RENAME
                            extracted_change = {
                                "file_path": cchange["fpath"],
                                "change_type": "RENAME",
                                "old_file_path": cc["fpath"],
                                "num_added": 0,
                                "num_deleted": 0

                            }
                            cchanges_queue.remove(cc)  # Remove corresponding DELETE
                            break
                elif cchange["ctype"] == "DELETE":  # Possible RENAME
                    # Search for corresponding ADD
                    for cc in cchanges_queue:
                        if (
                                cc["ctype"] == "ADD"
                                and cc["num_added"] == cchange["num_deleted"]
                        ):  # RENAME
                            extracted_change = {
                                "file_path": cc["fpath"],
                                "change_type": "RENAME",
                                "old_file_path": cchange["fpath"],
                                "num_added": 0,
                                "num_deleted": 0
                            }
                            cchanges_queue.remove(cc)  # Remove corresponding ADD
                            break

                if extracted_change == None:  # No RENAME situation detected
                    extracted_change = {
                        "file_path": cchange["fpath"],
                        "change_type": cchange["ctype"],
                        "num_added": cchange["num_added"],
                        "num_deleted": cchange["num_deleted"]
                    }

                extracted_changes.append(extracted_change)

                # This is for tracking the set of files after the commit
                ctype = extracted_change["change_type"]
                fpath = extracted_change["file_path"]

                if ctype == "DELETE" and fpath in current_files:
                    current_files.remove(fpath)
                elif ctype == "ADD":
                    current_files.add(fpath)
                elif ctype == "RENAME":
                    current_files.discard(extracted_change["old_file_path"])
                    current_files.add(fpath)

        if extracted_changes != []:
            change_set_dict["code_changes"] = extracted_changes
            change_set_dict["num_current_files"] = len(current_files)
            change_set_json = json.dumps(change_set_dict, ensure_ascii=False)

            # Prevent same commits (only hashes are different)
            comparison_str = change_set_json.split('"author":')[1]
            if comparison_str != prev_comparison_str:
                change_set_jsons.append(change_set_json)
            prev_comparison_str = comparison_str

start_date = datetime(2016, 11, 20)
end_date = datetime(2017, 11, 20)

filtered_change_set_jsons = []

for commit in change_set_jsons:
    commit_data = json.loads(commit)
    date_str = commit_data['date']
    commit_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")

    if start_date <= commit_date <= end_date:
        filtered_change_set_jsons.append(commit)

# NEO CREATION
# Developer Nodes

unique_authors = set()
developer_id = 0
for commit in filtered_change_set_jsons:
    commit_data = json.loads(commit)
    author = commit_data['author']

    if author not in unique_authors:
        unique_authors.add(author)
        neo4j_create_statement = (
            f"CREATE (d:Developer {{developer_id: {developer_id}, developer_name: '{standardize_name(author)}'}})"
        )

        session.run(neo4j_create_statement)
        developer_id += 1

# Create unique Commit Nodes
commit_details = {}

for commit in filtered_change_set_jsons:
    commit_data = json.loads(commit)
    commit_hash = commit_data['commit_hash']

    if commit_hash not in commit_details:
        commit_details[commit_hash] = {
            'modified_files': [],
            'lines_inserted': [],
            'lines_deleted': []
        }

    for code_change in commit_data.get('code_changes', []):
        commit_details[commit_hash]['modified_files'].append(code_change['file_path'])
        commit_details[commit_hash]['lines_inserted'].append(code_change['num_added'])
        commit_details[commit_hash]['lines_deleted'].append(code_change['num_deleted'])


unique_commit_hashes = set()
commit_id = 0
for commit in filtered_change_set_jsons:
    commit_data = json.loads(commit)
    commit_hash = commit_data['commit_hash']

    modified_files = commit_details[commit_hash]['modified_files']
    lines_inserted = commit_details[commit_hash]['lines_inserted']
    lines_deleted = commit_details[commit_hash]['lines_deleted']

    if commit_hash not in unique_commit_hashes and len(modified_files) < 50:
        unique_commit_hashes.add(commit_hash)
        author = standardize_name(commit_data['author'])
        date = commit_data['date']

        neo4j_create_statement = (
            f"CREATE (c:Commit {{commit_id: {commit_id}, commit_hash: '{commit_hash}', "
            f"commit_author: '{author}', commit_date: '{date}', "
            f"modified_files: {modified_files}, lines_inserted: {lines_inserted}, "
            f"lines_deleted: {lines_deleted}}})"
        )
        session.run(neo4j_create_statement)
        commit_id+1

        # Create relationships between commit and developer
        bidirectional_dev_commit_relation = (
            "MATCH (c:Commit), (d:Developer) "
            "WHERE c.commit_author = d.developer_name "
            "MERGE (d)-[:DEVELOPED]->(c)"
        )
        session.run(bidirectional_dev_commit_relation)

        neo4j_create_relation_commit_dev = (
            "MATCH (c:Commit), (d:Developer) "
            "WHERE c.commit_author = d.developer_name "
            "MERGE (c)-[:DEVELOPED_BY]->(d)"
        )
        session.run(neo4j_create_relation_commit_dev)

# Create File Nodes and Relationships
file_id = 0
file_paths = set()
for commit in filtered_change_set_jsons:
    commit_data = json.loads(commit)
    commit_hash = commit_data['commit_hash']

    for code_change in commit_data.get('code_changes', []):
        file_path = code_change['file_path']
        inserted_lines = code_change['num_added']
        deleted_lines = code_change['num_deleted']

        if file_path not in file_paths:
            file_paths.add(file_path)
            neo4j_create_statement = (
                f"CREATE (f:Files {{file_id: {file_id}, file_name: '{file_path}'}})"
            )
            session.run(neo4j_create_statement)
            file_id += 1

        commit_to_file_statement = (
            f"MATCH (c:Commit {{commit_hash: '{commit_hash}'}}), (f:Files {{file_name: '{file_path}'}}) "
            f"CREATE (c)-[:MODIFIED {{inserted_lines: {inserted_lines}, deleted_lines: {deleted_lines} }}]->(f)"
        )
        session.run(commit_to_file_statement)

        file_to_commit_statement = (
           f"MATCH (c:Commit {{commit_hash: '{commit_hash}'}}), (f:Files {{file_name: '{file_path}'}}) "
           f"CREATE (f)-[:MODIFIED_BY {{inserted_lines: {inserted_lines}, deleted_lines: {deleted_lines} }}]->(c)"
        )
        session.run(file_to_commit_statement)

session.close()
data_base_connection.close()
