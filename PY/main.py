import json
import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import DateEntry
from pydriller import Repository
from datetime import datetime, timedelta, timezone

from PY.api.data import extract_commit_data_by_time, dump_json_file, extract_author_commit_counts, \
    extract_changed_classes

# Define excluded extensions for various file types
excluded_extensions = {
    'compiled': ['.class', '.pyc'],
    'system': ['.dll', '.exe', '.so']
}

def open_new_page(commit_count, author_names, changed_classes):
    new_page = tk.Toplevel(root)
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

def toggle_date_entries():
    # Enable or disable the DateEntry widgets based on the checkbox state
    if date_checkbox_var.get():
        date_entry1.configure(state="normal")
        date_entry2.configure(state="normal")
    else:
        date_entry1.configure(state="disabled")
        date_entry2.configure(state="disabled")

def submit_button_clicked():
    github_link = entry.get()

    # Check if the GitHub link is provided
    if not github_link:
        messagebox.showinfo("Error", "Please enter a GitHub link.")
        return

    # Check if the user wants to filter by date
    if date_checkbox_var.get():
        # Get the selected dates from the DateEntry widgets
        if date_entry1.get_date() and date_entry2.get_date():
            dt1 = datetime.combine(date_entry1.get_date(), datetime.min.time(), tzinfo=timezone.utc)
            dt2 = datetime.combine(date_entry2.get_date(), datetime.max.time(), tzinfo=timezone.utc)
        else:
            messagebox.showinfo("Error", "Please select both start and end dates.")
            return
    else:
        dt1 = None
        dt2 = None

    try:
        commit_data = extract_commit_data_by_time(github_link, dt1, dt2)
        output_file_path = 'commit_data.json'
        dump_json_file(output_file_path, commit_data)

        # Load commit data from the temporary JSON file
        with open(output_file_path, 'r') as infile:
            loaded_commit_data = json.load(infile)

        author_commit_counts = extract_author_commit_counts(loaded_commit_data)
        changed_classes = extract_changed_classes(loaded_commit_data)
        author_names = list(author_commit_counts.keys())
        commit_count = [author_commit_counts[author] for author in author_names]

        open_new_page(commit_count, author_names, changed_classes)

    except Exception as e:
        messagebox.showinfo("Error", f"An error occurred: {str(e)}")

# Create the main application window
root = tk.Tk()
root.title("GitHub Link Input")

# Create and configure the widgets
entry = tk.Entry(root, width=50)
entry.pack(pady=5, padx=10)  # Adding padding to the left and right

# Checkbox to enable/disable date selections
date_checkbox_var = tk.BooleanVar()
date_checkbox = ttk.Checkbutton(root, text="Enable Date Selection", variable=date_checkbox_var, command=toggle_date_entries)
date_checkbox.pack(pady=5)

# DateEntry widgets for selecting the time range
date_label1 = tk.Label(root, text="Select start date:")
date_label1.pack(pady=5)
date_entry1 = DateEntry(root, width=12, background='darkblue', foreground='white', borderwidth=2, state="disabled")
date_entry1.pack(pady=5, padx=(0, 10))  # Adding padding to the right

date_label2 = tk.Label(root, text="Select end date:")
date_label2.pack(pady=5)
date_entry2 = DateEntry(root, width=12, background='darkblue', foreground='white', borderwidth=2, state="disabled")
date_entry2.pack(pady=5)

submit_button = tk.Button(root, text="Submit", command=submit_button_clicked)
submit_button.pack(pady=10)

# Run the GUI event loop
root.mainloop()
