import json
import os
import time
from flask import Flask, request, jsonify
from PY.data import dump_json_file, extract_commit_data
from flask_cors import CORS
from app import App

app_instance = App()

# Define excluded extensions for various file types
excluded_extensions = {
    'compiled': ['.class', '.pyc'],
    'system': ['.dll', '.exe', '.so']
}

app = Flask(__name__)
CORS(app)  # Enable CORS support for all resources

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




        # Return success response
        return jsonify({'success': True}), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500




@app.route('/get-developer-info', methods=['GET'])
def get_developer_info():
    try:
        # Wait until commit_data.json is created
        output_file_path = 'commit_data.json'
        while not os.path.exists(output_file_path):
            time.sleep(1)


        # Load commit data from the temporary JSON file
        with open(output_file_path, 'r') as infile:
            loaded_commit_data = json.load(infile)


        # Extract developer info

        developer_ids = app_instance.get_developers()  # Geliştirici ID'lerini alın
        developer_names = app_instance.get_developer_names()  # Geliştirici isimlerini alın

        developer_info = {
            'developerIDs': developer_ids,
            'developerNames': developer_names
        }
        return jsonify(developer_info), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)