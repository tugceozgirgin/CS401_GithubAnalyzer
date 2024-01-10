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

        # Create a style for themed widgets
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")  # Set background color
        self.style.configure("TLabel", background="#f0f0f0")  # Set background color
        self.style.configure("TButton", background="#4CAF50", foreground="white")  # Set button colors

        # Create and configure the widgets
        frame = ttk.Frame(self.root, style="TFrame")
        frame.pack(pady=10, padx=10)

        ttk.Label(frame, text="GitHub Link:", style="TLabel").grid(row=0, column=0, padx=5, pady=5)

        self.entry = ttk.Entry(frame, width=50)
        self.entry.grid(row=0, column=1, padx=5, pady=5)

        # Checkbox to enable/disable date selections
        self.date_checkbox_var = tk.BooleanVar()
        self.date_checkbox = ttk.Checkbutton(frame, text="Enable Date Selection", variable=self.date_checkbox_var,
                                             command=self.toggle_date_entries, style="TCheckbutton")
        self.date_checkbox.grid(row=1, columnspan=2, pady=5)

        # DateEntry widgets for selecting the time range
        ttk.Label(frame, text="Select start date:", style="TLabel").grid(row=2, column=0, padx=5, pady=5)
        self.date_entry1 = DateEntry(frame, width=12, background='darkblue', foreground='white', borderwidth=2,
                                     state="disabled")
        self.date_entry1.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Select end date:", style="TLabel").grid(row=3, column=0, padx=5, pady=5)
        self.date_entry2 = DateEntry(frame, width=12, background='darkblue', foreground='white', borderwidth=2,
                                     state="disabled")
        self.date_entry2.grid(row=3, column=1, padx=5, pady=5)

        self.submit_button = ttk.Button(frame, text="Submit", command=self.submit_button_clicked)
        self.submit_button.grid(row=4, columnspan=2, pady=10)

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
        #developer_analyzer.plot_commits_per_developer()
        #developer_analyzer.plot_file_counts_per_developer()
        #developer_analyzer.plot_lines_per_developer()
        #developer_analyzer.plot_all()
        #developer_analyzer.plot_custom_boxplot()

        #developer_analyzer.plot_closed_issues_per_developer()

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