from dash import Dash, html, Output, Input, dcc
import pandas as pd
import numpy as np


from PY.analyzes.graph_algorithms import GraphAlgorithms, developers  # Replace with your graph module or class

graph = GraphAlgorithms()
closedissue_dict = graph.dev_to_closed_issues()
expertness_dict = graph.find_jacks()
savantness_dict = graph.find_mavens(0.8)
is_expert = graph.find_jacks()

data = {
    'Developer Id': graph.get_developers(),
    'Developer Name': graph.get_developer_names(),
}

df = pd.DataFrame(data)

df['Closed Issue'] = df['Developer Name'].map(closedissue_dict).fillna(0).astype(int)
df['Expertness Ratio %'] = (df['Developer Id'].map(expertness_dict).fillna(0).astype(float) * 100).round(2)
df['Savantness Ratio %'] = (df['Developer Id'].map(savantness_dict).fillna(0).astype(float) * 100).round(2)


def determine_expert(row):
    if row['Expertness Ratio %'] > 20:
        return 'Yes'
    else:
        return 'No'

df['Expert'] = df.apply(determine_expert, axis=1)
def determine_savant(row):
    if row['Savantness Ratio %'] > 20:
        return 'Yes'
    else:
        return 'No'

df['Savant'] = df.apply(determine_savant, axis=1)
def determine_solver(row):
    if row['Closed Issue'] > 2:
        return 'Yes'
    else:
        return 'No'

# Apply the function to create the 'Savant' column
df['Solver'] = df.apply(determine_solver, axis=1)

print(df)

def plot_files_modified_boxplot(graph):
    files_modified_per_developer = graph.list_files_modified_per_developer()
    data = {'Developer': [], 'Modified Files': []}

    for (commit_hash, developer_id), modified_files_count in files_modified_per_developer.items():
        data['Developer'].append(developer_id)
        data['Modified Files'].append(modified_files_count)

    df_files_modified = pd.DataFrame(data)

    mean = df_files_modified['Modified Files'].mean()
    std_dev = df_files_modified['Modified Files'].std()
    cutoff = 3 * std_dev

    df_filtered = df_files_modified[np.abs(df_files_modified['Modified Files'] - mean) < cutoff]

    # Create Plotly figure
    fig = go.Figure(data=[
        go.Box(x=df_files_modified['Developer'], y=df_files_modified['Modified Files'], marker_color='lightblue')])
    fig.update_layout(
        title='Files Modified per Commit (Outliers Removed)',
        xaxis=dict(title='Developers'),
        yaxis=dict(title='Modified Files')
    )
    return fig

def plot_lines_modified_boxplot(graph):
    # Call the method to get lines modified per commit
    lines_modified_per_commit = graph.list_lines_modified_per_commit()

    # Organize data into a DataFrame
    data = {
        'Developer': [],
        'Lines Modified': []
    }

    for (commit_hash, developer_id), lines_modified in lines_modified_per_commit.items():
        data['Developer'].append(developer_id)
        data['Lines Modified'].append(lines_modified)

    df = pd.DataFrame(data)

    mean = df['Lines Modified'].mean()
    std_dev = df['Lines Modified'].std()
    cutoff = 3 * std_dev

    df_filtered = df[np.abs(df['Lines Modified'] - mean) < cutoff]

    # Create Plotly figure
    fig = go.Figure(data=[go.Box(x=df['Developer'], y=df['Lines Modified'], marker_color='lightgreen')])
    fig.update_layout(
        title='Lines Modified per Commit (Outliers Removed)',
        xaxis=dict(title='Developers'),
        yaxis=dict(title='Lines Modified')
    )
    return fig
def plot_commits_per_developer_histogram(self):
    # Extract data for plotting
    calculate_commits_per_developer = graph.calculate_commits_per_developer()

    developers = list(calculate_commits_per_developer.keys())
    commit_counts = list(calculate_commits_per_developer.values())

    # Create a Plotly figure with a different color (e.g., red)
    fig = go.Figure(data=[go.Bar(x=developers, y=commit_counts, marker_color='purple')])
    fig.update_layout(
        title='Number of Commits for Each Developer',
        xaxis=dict(title='Developers'),
        yaxis=dict(title='Number of Commits')
    )

    return fig

import plotly.graph_objs as go

def plot_lines_modified_histogram(self):
    developer_lines_modified = graph.get_developer_lines_modified()

    developers = list(developer_lines_modified.keys())
    lines_modified = list(developer_lines_modified.values())

    # Create a Plotly figure
    fig = go.Figure(data=[go.Bar(x=developers, y=lines_modified, marker_color='orange')])
    fig.update_layout(
        title='Total Lines Modified for Each Developer',
        xaxis=dict(title='Developers'),
        yaxis=dict(title='Total Lines Modified')
    )
    return fig

import plotly.graph_objs as go

def plot_lines_modified_histogram2(self):
    lines_modified_per_developer = self.list_lines_modified_per_developer()

    # Extract lines modified values for each developer
    lines_modified_values = list(lines_modified_per_developer.values())

    # Create a histogram with Matplotlib
    if len(lines_modified_values) > 0:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(20, 12))  # Larger figure size

        average_lines_modified = sum(lines_modified_values) / len(lines_modified_values)
        iqr = np.percentile(lines_modified_values, 75) - np.percentile(lines_modified_values, 25)
        bin_width = 2 * iqr / (len(lines_modified_values) ** (1 / 3))
        bin_width /= 4

        # Calculate histogram bins dynamically
        min_value = min(lines_modified_values)
        max_value = max(lines_modified_values)
        bins = np.arange(min_value, max_value + bin_width, bin_width)

        # Create histogram with adjusted column width
        ax.hist(lines_modified_values, bins=bins, edgecolor='black', alpha=0.7, width=bin_width, align='mid')
        ax.axvline(x=average_lines_modified, color='red', linestyle='--', linewidth=2, label='Average')

        # Set labels and title
        ax.set_xlabel('Total Lines Modified')
        ax.set_ylabel('Number of Developers')
        ax.set_title('Lines Modified Distribution per Developer')

        # Convert Matplotlib figure to Plotly
        fig.canvas.draw()
        img = np.array(fig.canvas.renderer._renderer)
        plt.close(fig)

        # Create Plotly figure with a larger layout
        fig_plotly = go.Figure(go.Image(z=img))
        fig_plotly.update_layout(
            width=1500,  # Adjust the width
            height=900,  # Adjust the height
            margin=dict(l=20, r=20, t=20, b=20),  # Add margins if needed
        )
        return fig_plotly
    else:
        return None






from dash import Dash, html, Input, Output, dash_table
app = Dash(__name__, suppress_callback_exceptions=True)

app.layout = html.Div([
    html.H4('Github Repository Analysis Outcomes'),
    html.Div(id='table_out'),
    dash_table.DataTable(
            id='table',
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict('records'),
            style_cell=dict(textAlign='left'),
            style_header=dict(backgroundColor="paleturquoise"),
            style_data=dict(backgroundColor="lavender")
        ),
        dcc.Graph(
            id='bar_plot_issues',
            figure={
                'data': [
                    {'x': df['Developer Name'], 'y': df['Closed Issue'], 'type': 'bar', 'name': 'Closed Issues'}
                ],
                'layout': {
                    'title': 'Closed Issues per Developer',
                    'xaxis': {'title': 'Developer Name'},
                    'yaxis': {'title': '# Closed Issues'}
                }
            }
        ),
        dcc.Graph(
            id='bar_plot_experts',
            figure={
                'data': [
                    {'x': df['Developer Name'], 'y': df['Expertness Ratio %'], 'type': 'bar', 'name': 'Expert Percentage'}
                ],
                'layout': {
                    'title': 'Expert Percentage for Each Developer',
                    'xaxis': {'title': 'Developers'},
                    'yaxis': {'title': 'Expert Percentage'},
                    'shapes': [{
                        'type': 'line',
                        'x0': 0,
                        'y0': 20,
                        'x1': len(df['Developer Name']),
                        'y1': 20,
                        'line': {
                            'color': 'red',
                            'width': 2,
                            'dash': 'dash',
                        },
                    }],
                }
            }
        ),
    dcc.Graph(
        id='bar_plot_experts',
        figure={
            'data': [
                {'x': df['Developer Name'], 'y': df['Savantness Ratio %'], 'type': 'bar', 'name': 'Expert Percentage'}
            ],
            'layout': {
                'title': 'Savantness Percentage for Each Developer',
                'xaxis': {'title': 'Developers'},
                'yaxis': {'title': 'Savantness Percentage'},
                'shapes': [{
                    'type': 'line',
                    'x0': 0,
                    'y0': 20,
                    'x1': len(df['Developer Name']),
                    'y1': 20,
                    'line': {
                        'color': 'red',
                        'width': 2,
                        'dash': 'dash',
                    },
                }],
            }
        }
    ),
        dcc.Graph(
            id='boxplot_files_modified',
            figure=plot_files_modified_boxplot(graph)
        ),
        dcc.Graph(
            id='boxplot_lines_modified',
            figure=plot_lines_modified_boxplot(graph)
        ),
      dcc.Graph(
           id='commits_per_developer_histogram',
           figure=plot_commits_per_developer_histogram(graph)
      ),
    dcc.Graph(
        id='lines_modified_histogram',
        figure=plot_lines_modified_histogram(graph)
    ),
    dcc.Graph(
        id='lines_modified_histogram2',
        figure=plot_lines_modified_histogram2(graph)
    ),
    ])
@app.callback(
    Output('table_out', 'children'),
    Input('table', 'active_cell'))
def update_graphs(active_cell):
    if active_cell:
        cell_data = df.iloc[active_cell['row']][active_cell['column_id']]
        return f"Data: \"{cell_data}\" from table cell: {active_cell}"
    return "Click the table"
app.run_server(debug=True)

