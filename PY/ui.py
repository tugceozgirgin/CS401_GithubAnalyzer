import base64
import json
import os
import time
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

        # Calculate whether each developer is a "JACK"
        dev_to_file_coverage = app_instance.find_jacks()  # Calculate coverage
        developer_is_jack = {developer_id: app_instance.is_jack(dev_to_file_coverage, developer_id) for developer_id in developer_ids}

        developer_info = {
            'developerIDs': developer_ids,
            'developerNames': developer_names,
            'isJack': developer_is_jack
        }
        return jsonify(developer_info), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

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
        developer_names = app_instance.get_developer_names()

        developer_info = {
            'developerIDs': developer_ids,
            'developerNames': developer_names,
            'Similarity': developer_similarity
        }
        return jsonify(developer_info), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500




@app.route('/get-distribution', methods=['GET'])
def get_distribution():
    try:
        from app import App
        app_instance = App()

        # Generate the distribution plot
        fig_plotly = app_instance.plot_lines_modified_histogram2()

        if fig_plotly:
            # Convert Plotly figure to PNG image
            img_bytes = fig_plotly.to_image(format="png")
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')

            # Return the image data
            return f"data:image/png;base64,{img_base64}"
        else:
            return jsonify({'error': 'No data available for distribution plot'}), 404

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


from flask import jsonify

@app.route('/get-chart-data', methods=['GET'])
def get_chart_data():
    try:
        # Manually define x and y points for the chart
        labels = ['Elif', 'Ece', 'Tuğçe', 'Ed', 'Jana', 'Hasan', 'Ahmet', 'Mehmet', 'Eylül', 'Berra', 'Kasım', 'Can']
        data_points = [10, 20, 15, 25, 30, 20, 10, 15, 25, 20, 30, 25]

        # Combine labels and data points into a dictionary
        chart_data = {
            'labels': labels,  # x axis labels
            'datapoints': data_points
        }

        # Return the chart data
        return jsonify(chart_data), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500








if __name__ == "__main__":
    app.run(debug=True, port=5001)