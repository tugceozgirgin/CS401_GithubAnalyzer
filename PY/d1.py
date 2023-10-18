import json
import os
import tempfile
import tkinter as tk
from tkinter import messagebox, ttk
from pydriller import Repository

def open_new_page(commit_count, author_names, changed_classes):
    new_page = tk.Toplevel(root)
    new_page.title("Commit Information")

    canvas = tk.Canvas(new_page)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(new_page, orient=tk.VERTICAL, command=canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    frame = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=frame, anchor=tk.NW)

    for i, (label_text, data) in enumerate(zip(["Authors:", "Commits:", "Classes:"], [author_names, commit_count, changed_classes])):
        label = ttk.Label(frame, text=label_text)
        label.grid(row=0, column=i, padx=5, pady=5)

        if i == 0:  # Author names
            for j, author in enumerate(data):
                author_label = ttk.Label(frame, text=author)
                author_label.grid(row=j+1, column=i, padx=5, pady=2)
        elif i == 1:  # Commit count
            commit_count_label = ttk.Label(frame, text=data)
            commit_count_label.grid(row=1, column=i, padx=5, pady=2)
        elif i == 2:  # Changed classes
            for j, class_name in enumerate(data):
                class_label = ttk.Label(frame, text=class_name)
                class_label.grid(row=j+1, column=i, padx=5, pady=2)

    frame.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"), yscrollcommand=scrollbar.set)

def submit_button_clicked():
    github_link = entry.get()

    # Check if the GitHub link is provided
    if not github_link:
        messagebox.showinfo("Error", "Please enter a GitHub link.")
        return

    # Create a temporary directory to store the commit data
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, 'commit_data.json')

    try:
        # Write commit data to a temporary JSON file
        commit_data = []
        for commit in Repository(github_link).traverse_commits():
            commit_info = {
                'hash': commit.hash,
                'message': commit.msg,
                'author': commit.author.name,
                'modified_files': [file.filename for file in commit.modified_files]
            }
            commit_data.append(commit_info)

        with open(temp_file_path, 'w') as outfile:
            json.dump(commit_data, outfile, indent=4)

        print('Commit data written to', temp_file_path)

        # Load commit data from the temporary JSON file
        with open(temp_file_path, 'r') as infile:
            loaded_commit_data = json.load(infile)

        # Extract unique author names from the commit data
        author_names = set(commit['author'] for commit in loaded_commit_data)

        # Extract unique class names from the commit data
        changed_classes = set()
        for commit in loaded_commit_data:
            for modified_file in commit['modified_files']:
                if modified_file.endswith('.java'):  # Assuming the files are Java classes
                    changed_classes.add(modified_file)

        commit_count = len(loaded_commit_data)
        open_new_page(commit_count, author_names, changed_classes)

    except Exception as e:
        messagebox.showinfo("Error", f"An error occurred: {str(e)}")

    finally:
        # Clean up temporary files and directory
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)

# Create the main application window
root = tk.Tk()
root.title("GitHub Link Input")

# Create and configure the widgets
entry = tk.Entry(root, width=50)
entry.pack(pady=5, padx=10)  # Adding padding to the left and right

submit_button = tk.Button(root, text="Submit", command=submit_button_clicked)
submit_button.pack(pady=10)

# Run the GUI event loop
root.mainloop()
