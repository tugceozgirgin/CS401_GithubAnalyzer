import base64
import json
import os
import time

import numpy as np
from flask import Flask, request, jsonify
from PY.data import dump_json_file, extract_commit_data
from flask_cors import CORS
import plotly.graph_objs as go


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

        from app import App
        app_instance = App()

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
        print("get info 1")
        return jsonify(developer_info), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@app.route('/get-developer-info2', methods=['GET'])
def get_developer_info2():
    try:
        # Wait until commit_data.json is created
        output_file_path = 'commit_data.json'
        while not os.path.exists(output_file_path):
            time.sleep(1)

        from app import App
        app_instance = App()

        # Load commit data from the temporary JSON file
        with open(output_file_path, 'r') as infile:
            loaded_commit_data = json.load(infile)

        # Extract developer info
        developer_ids = app_instance.get_developers()
        developer_names = app_instance.get_developer_names()

        # Calculate JACK ratios for each developer
        developer_jack_ratios = app_instance.find_jacks()

        developer_info = {
            'developerIDs': developer_ids,
            'developerNames': developer_names,
            'JackRatios': developer_jack_ratios
        }
        #print(developer_jack_ratios)

        return jsonify(developer_info), 200

    except Exception as e:
        print("Error in get_developer_info2:", e)
        return jsonify({'error': 'Internal Server Error'}), 500



@app.route('/get-developer-info3', methods=['GET'])
def get_developer_info3():
    try:
        from app import App
        app_instance = App()

        # Extract developer info
        developer_ids = app_instance.get_developers()
        developer_names = app_instance.get_developer_names()

        # Calculate mavenness for each developer
        developer_maven = app_instance.find_mavens(0.8)

        developer_info = {
            'developerIDs': developer_ids,
            'developerNames': developer_names,
            'Maven': developer_maven
        }
        print("get info 3")
        #print(developer_maven)

        return jsonify(developer_info), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/get-developer-info4', methods=['GET'])
def get_developer_info4():
    try:
        from app import App
        app_instance = App()

        total_commit_count = sum(app_instance.calculate_commits_per_developer().values())
        total_file_count = app_instance.get_num_files()
        total_developer_count = len(app_instance.get_developers())
        developer_names = app_instance.get_developer_names()

        developer_info = {
                'total_commit_count': total_commit_count,
                'total_file_count': total_file_count,
                'total_developer_count': total_developer_count,
                'developer_names': developer_names
        }
        #print(total_commit_count)

        return jsonify(developer_info), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@app.route('/get-similarity', methods=['GET'])
def get_similarity():
    try:
        from app import App
        app_instance = App()

        # Calculate replacements for all developers
        all_replacements_result = app_instance.find_replacements_for_all()

        # Get top similar developers
        developer_similarity = app_instance.get_top_similar_developers(all_replacements_result)

        # Extract developer info
        developer_ids = app_instance.get_developers()
        #print(developer_ids)
        developer_names = app_instance.get_developer_names()

        developer_info = {
            'developerIDs': developer_ids,
            'developerNames': developer_names,
            'Similarity': developer_similarity
        }
        return jsonify(developer_info), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500




from flask import jsonify

@app.route('/get-chart-data', methods=['GET'])
def get_chart_data():
    try:
        from app import App
        app_instance = App()

        # Extract developer info
        developer_commits = app_instance.calculate_commits_per_developer()

        # Extracting developer names and commits count
        developer_names = list(developer_commits.keys())
        developer_counts = list(developer_commits.values())

        # Combine labels and data points into a dictionary
        chart_data = {
            'labels': developer_names,  # x axis labels
            'datapoints': developer_counts,
        }

        # Return the chart data
        return jsonify(chart_data), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@app.route('/get-chart-data2', methods=['GET'])
def get_chart_data2():
    try:
        from app import App
        app_instance = App()

        # Extract developer info
        developer_files = app_instance.calculate_files_per_developer()

        # Extracting developer names and commits count
        developer_names = list(developer_files.keys())
        developer_files_ = list(developer_files.values())

        # Combine labels and data points into a dictionary
        chart_data = {
            'labels': developer_names,  # x axis labels
            'datapoints': developer_files_,
        }

        # Return the chart data
        return jsonify(chart_data), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@app.route('/get-chart-data3', methods=['GET'])
def get_chart_data3():
    try:
        from app import App
        app_instance = App()

        # Extract lines modified per commit by each developer
        developer_lines = app_instance.calculate_lines_per_developer()

        # Extracting developer names and lines modified count
        developer_names = list(developer_lines.keys())
        developer_lines_ = list(developer_lines.values())

        # Combine labels and data points into a dictionary
        chart_data = {
            'labels': developer_names,  # x axis labels
            'datapoints': developer_lines_,
        }

        # Return the chart data
        return jsonify(chart_data), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/get-chart-data4', methods=['GET'])
def get_chart_data4():
    try:
        from app import App
        app_instance = App()

        all_replacements_result = app_instance.find_replacements_for_all()

        # Get all developers
        all_devs = list(all_replacements_result.keys())

        # Initialize similarity matrix
        similarity_matrix = []

        # Iterate through developers to populate similarity matrix
        for dev1 in all_devs:
            row = []
            for dev2 in all_devs:
                # If dev1 is the same as dev2, similarity is 1
                if dev1 == dev2:
                    similarity = 1.0
                else:
                    # Get similarity between dev1 and dev2
                    similarity = all_replacements_result[dev1].get(dev2, 0.0)  # Default to 0 if no similarity found
                row.append(similarity)
            similarity_matrix.append(row)

        # Return the similarity matrix
        return jsonify(similarity_matrix), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500



@app.route('/get_balanced', methods=['GET'])
def get_balanced():
    try:
        from app import App
        app_instance = App()

        # Assuming you have a function list_lines_modified_per_developer implemented somewhere
        lines_modified_per_developer = app_instance.list_lines_modified_per_developer()
        lines_modified_values = list(lines_modified_per_developer.values())

        # Calculate the average lines modified
        average_lines_modified = sum(lines_modified_values) / len(lines_modified_values)
        print(lines_modified_values)
        print(average_lines_modified)

        # Calculate the bin width for the histogram
        iqr = np.percentile(lines_modified_values, 75) - np.percentile(lines_modified_values, 25)
        bin_width = 2 * iqr / (len(lines_modified_values) ** (1 / 3))
        bin_width /= 4

        # Define the bins for the histogram
        min_value = min(lines_modified_values)
        max_value = max(lines_modified_values)
        bins = np.arange(min_value, max_value + bin_width, bin_width)

        developer_names = app_instance.get_developer_names()


        # Create data in Chart.js format
        chart_data = {
            'developerNames': developer_names,
            'lines_modified_values': lines_modified_values,
            'average_lines_modified': average_lines_modified,
            'bins': bins.tolist()  # Convert numpy array to list
        }

        return jsonify(chart_data), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)