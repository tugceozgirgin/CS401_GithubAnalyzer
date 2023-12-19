import json
import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import DateEntry
from datetime import datetime, timedelta, timezone

from PY.analyzes.DeveloperAnalyzer import DeveloperAnalyzer
#from PY.analyzes.graph_algorithms import GraphAlgorithms
from PY.database.connection import CONNECTION
from PY.database.neo_db import NEO  # Import the NEO class

from PY.api.data import extract_commit_data_by_time, dump_json_file, extract_author_commit_counts, \
    extract_changed_classes, extract_commit_data, extract_issues

# Define excluded extensions for various file types
excluded_extensions = {
    'compiled': ['.class', '.pyc'],
    'system': ['.dll', '.exe', '.so']
}

class GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("GitHub Link Input")

        # Create and configure the widgets
        self.entry = tk.Entry(self.root, width=50)
        self.entry.pack(pady=5, padx=10)  # Adding padding to the left and right

        # Checkbox to enable/disable date selections
        self.date_checkbox_var = tk.BooleanVar()
        self.date_checkbox = ttk.Checkbutton(self.root, text="Enable Date Selection", variable=self.date_checkbox_var,
                                             command=self.toggle_date_entries)
        self.date_checkbox.pack(pady=5)

        # DateEntry widgets for selecting the time range
        self.date_label1 = tk.Label(self.root, text="Select start date:")
        self.date_label1.pack(pady=5)
        self.date_entry1 = DateEntry(self.root, width=12, background='darkblue', foreground='white', borderwidth=2,
                                     state="disabled")
        self.date_entry1.pack(pady=5, padx=(0, 10))  # Adding padding to the right

        self.date_label2 = tk.Label(self.root, text="Select end date:")
        self.date_label2.pack(pady=5)
        self.date_entry2 = DateEntry(self.root, width=12, background='darkblue', foreground='white', borderwidth=2,
                                     state="disabled")
        self.date_entry2.pack(pady=5)

        self.submit_button = tk.Button(self.root, text="Submit", command=self.submit_button_clicked)
        self.submit_button.pack(pady=10)

    def run(self):
        # Run the GUI event loop
        self.root.mainloop()

    def open_new_page(self, commit_count, author_names, changed_classes):
        new_page = tk.Toplevel(self.root)
        new_page.title("Commit Information")

        canvas = tk.Canvas(new_page)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(new_page, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=frame, anchor=tk.NW)

        ttk.Label(frame, text="Author").grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(frame, text="Total Commits").grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(frame, text="Changed Classes").grid(row=0, column=2, padx=5, pady=5)

        for i, (author, commit_count) in enumerate(zip(author_names, commit_count), start=1):
            ttk.Label(frame, text=author).grid(row=i, column=0, padx=5, pady=2)
            ttk.Label(frame, text=str(commit_count)).grid(row=i, column=1, padx=5, pady=2)

            changed_classes_text = "\n".join(changed_classes.get(author, []))
            ttk.Label(frame, text=changed_classes_text).grid(row=i, column=2, padx=5, pady=2, sticky="w")

        frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"), yscrollcommand=scrollbar.set)

    def toggle_date_entries(self):
        # Enable or disable the DateEntry widgets based on the checkbox state
        if self.date_checkbox_var.get():
            self.date_entry1.configure(state="normal")
            self.date_entry2.configure(state="normal")
        else:
            self.date_entry1.configure(state="disabled")
            self.date_entry2.configure(state="disabled")

    def submit_button_clicked(self):
        github_link = self.entry.get()

        # Check if the GitHub link is provided
        if not github_link:
            messagebox.showinfo("Error", "Please enter a GitHub link.")
            return

        # Check if the user wants to filter by date
        if self.date_checkbox_var.get():
            # Get the selected dates from the DateEntry widgets
            if self.date_entry1.get_date() and self.date_entry2.get_date():
                dt1 = datetime.combine(self.date_entry1.get_date(), datetime.min.time(), tzinfo=timezone.utc)
                dt2 = datetime.combine(self.date_entry2.get_date(), datetime.max.time(), tzinfo=timezone.utc)
            else:
                messagebox.showinfo("Error", "Please select both start and end dates.")
                return
        else:
            dt1 = None
            dt2 = None

        try:
            commit_data = extract_commit_data(github_link, dt1, dt2)
            output_file_path = 'commit_data.json'
            dump_json_file(output_file_path, commit_data)
            issues_data = extract_issues(github_link,
                                         "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")
            output_file_path_issues = 'issue_data.json'
            dump_json_file('issue_data.json', issues_data)

            # Load commit data from the temporary JSON file
            with open(output_file_path, 'r') as infile:
                loaded_commit_data = json.load(infile)

            with open(output_file_path_issues, 'r') as infile:
                loaded_issue_data = json.load(infile)



            author_commit_counts = extract_author_commit_counts(loaded_commit_data)
            changed_classes = extract_changed_classes(loaded_commit_data)
            author_names = list(author_commit_counts.keys())
            commit_count = [author_commit_counts[author] for author in author_names]

            self.open_new_page(commit_count, author_names, changed_classes)

        except Exception as e:
            messagebox.showinfo("Error", f"An error occurred: {str(e)}")

        # Run the NEO class with the provided GitHub link
        neo_instance = NEO(github_link)
        neo_instance.run()
        neo_instance.analyze_developers2()

        # Instantiate DeveloperAnalyzer after loading commit data
        developer_analyzer = DeveloperAnalyzer(loaded_commit_data, loaded_issue_data, github_link)
        developer_analyzer.show_similarity_ratios()
        developer_analyzer.run_analysis()
        developer_analyzer.plot_commits_per_developer()
        developer_analyzer.plot_file_counts_per_developer()
        developer_analyzer.plot_lines_per_developer()
        developer_analyzer.plot_all()
        #developer_analyzer.plot_combined_boxplot()

        developer_analyzer.plot_closed_issues_per_developer()

        #graph_algorithms = GraphAlgorithms("bolt://localhost:7687", "neo4j", "password")
        #graph_algorithms.run()


        # connection_instance = CONNECTION()
        # connection_instance.run()

    def get_github_link(self):
        github_link = self.entry.get()
        return str(github_link)


if __name__ == "__main__":
    gui_instance = GUI()
    gui_instance.run()
    github_link = gui_instance.get_github_link()  # Get the GitHub link from the GUI
