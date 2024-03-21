import json
from flask import Flask, request, jsonify
from PY.api.data import dump_json_file, extract_author_commit_counts, \
    extract_changed_classes, extract_commit_data, extract_issues
from datetime import datetime, timezone
from flask_cors import CORS


# Define excluded extensions for various file types
excluded_extensions = {
    'compiled': ['.class', '.pyc'],
    'system': ['.dll', '.exe', '.so']
}

app = Flask(__name__)
CORS(app)  # Tüm kaynaklar için CORS desteğini etkinleştirir

@app.route('/submit-github-link', methods=['POST'])

def submit_github_link():
    try:
        data = request.get_json()
        github_link = data.get('github_link')

        # Check if the GitHub link is provided
        if not github_link:
            return jsonify({'error': 'Please enter a GitHub link.'}), 400

        dt1 = None
        dt2 = None

        commit_data = extract_commit_data(github_link, dt1, dt2)
        output_file_path = 'commit_data.json'
        dump_json_file(output_file_path, commit_data)

        # issues_data = extract_issues(github_link,
        #                              "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")
        # output_file_path_issues = 'issue_data.json'
        # dump_json_file('issue_data.json', issues_data)

        # Load commit data from the temporary JSON file
        with open(output_file_path, 'r') as infile:
            loaded_commit_data = json.load(infile)

        # with open(output_file_path_issues, 'r') as infile:
        #     loaded_issue_data = json.load(infile)

        author_commit_counts = extract_author_commit_counts(loaded_commit_data)
        changed_classes = extract_changed_classes(loaded_commit_data)
        author_names = list(author_commit_counts.keys())
        commit_count = [author_commit_counts[author] for author in author_names]

        # Do other processing here if needed

        return jsonify({'success': True, 'data': {
            'commit_count': commit_count,
            'author_names': author_names,
            'changed_classes': changed_classes
        }}), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
