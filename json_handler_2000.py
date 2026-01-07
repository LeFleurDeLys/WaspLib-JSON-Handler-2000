import os
import json
import shutil
import zipfile
import tempfile
import urllib.request
import ssl
import tkinter as tk
from tkinter import filedialog, messagebox

class CoordinateUpdaterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JSON Handler 2000")
        self.root.geometry("600x700")

        # Header
        header = tk.Label(root, text="JSON Handler 2000 by Fini Le Niaisage", font=("Helvetica", 16, "bold"))
        header.pack(pady=10)

        # Target Selection
        tk.Label(root, text="Target /Data/Assets/map/npcs.zip ").pack(anchor=tk.W, padx=20)
        self.dir_frame = tk.Frame(root)
        self.dir_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.dir_entry = tk.Entry(self.dir_frame)
        # Default path based on user context
        default_path = os.path.abspath(os.path.join("Data", "Assets", "map", "npcs.zip"))
        self.dir_entry.insert(0, default_path)
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.browse_file_btn = tk.Button(self.dir_frame, text="Browse File...", command=self.browse_file)
        self.browse_file_btn.pack(side=tk.RIGHT, padx=(5, 0))


        # Keyword Search Group
        self.search_group = tk.LabelFrame(root, text="Keyword Search", padx=10, pady=10)
        self.search_group.pack(padx=20, pady=10, fill=tk.X)

        tk.Label(self.search_group, text="Keyword:").pack(side=tk.LEFT, padx=5)
        self.keyword_entry = tk.Entry(self.search_group)
        self.keyword_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.keyword_entry.bind('<Return>', lambda event: self.run_search())
        
        self.search_btn = tk.Button(self.search_group, text="Search", command=self.run_search, bg="#9C27B0", fg="white")
        self.search_btn.pack(side=tk.RIGHT, padx=5)

        # Action Button
        self.run_btn = tk.Button(root, text="1. Install New JSONs", command=self.run_update,
                                 bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold"), height=2)
        self.run_btn.pack(fill=tk.X, padx=40, pady=20)

        # Allow Custom JSONs Button
        self.custom_json_btn = tk.Button(root, text="2. Disable WaspLib Updates (Allows Custom JSONs)", command=self.allow_custom_jsons,
                                         bg="#2196F3", fg="white", font=("Helvetica", 10, "bold"), height=2)
        self.custom_json_btn.pack(fill=tk.X, padx=40, pady=(0, 20))

        # Update Chunk Translator Button
        self.update_chunk_btn = tk.Button(root, text="3. Update Chunk Translator", command=self.update_chunk_translator,
                                          bg="#673AB7", fg="white", font=("Helvetica", 10, "bold"), height=2)
        self.update_chunk_btn.pack(fill=tk.X, padx=40, pady=(0, 20))

        # Delete Old NPCs from Cache Button
        self.delete_npc_cache_btn = tk.Button(root, text="4. Delete Old NPCs from Cache", command=self.delete_npc_cache,
                                              bg="#FF9800", fg="white", font=("Helvetica", 10, "bold"), height=2)
        self.delete_npc_cache_btn.pack(fill=tk.X, padx=40, pady=(0, 20))

        # Spacer for 50px vertical gap between first three and last two buttons
        spacer = tk.Frame(root, height=50)
        spacer.pack(fill=tk.X, padx=40)

        # Restore Default JSONs Button
        self.restore_json_btn = tk.Button(root, text="Restore WaspLib Updates (Downloads old JSONs on next script run)", command=self.restore_default_jsons,
                                          bg="#f44336", fg="white", font=("Helvetica", 10, "bold"), height=2)
        self.restore_json_btn.pack(fill=tk.X, padx=40, pady=(0, 20))

        # Restore Old Chunk Translator Button
        self.restore_chunk_btn = tk.Button(root, text="Restore Old Chunk Translator", command=self.restore_old_chunk_translator,
                                           bg="#f44336", fg="white", font=("Helvetica", 10, "bold"), height=2)
        self.restore_chunk_btn.pack(fill=tk.X, padx=40, pady=(0, 20))

        # Status Label
        self.status_label = tk.Label(root, text="Ready", fg="gray")
        self.status_label.pack(side=tk.BOTTOM, pady=10)

        self.preview_window = None
        self.current_editing_context = None

    def browse_file(self):
        current_path = self.dir_entry.get().strip().strip('"').strip("'")
        initial_dir = os.getcwd()

        if current_path:
            abs_path = os.path.abspath(current_path)
            if os.path.isfile(abs_path):
                abs_path = os.path.dirname(abs_path)
            
            if os.path.exists(abs_path):
                initial_dir = abs_path

        file_path = filedialog.askopenfilename(
            initialdir=initial_dir,
            filetypes=[("Supported Files", "*.json;*.zip"), ("JSON Files", "*.json"), ("ZIP Files", "*.zip"), ("All Files", "*.*")]
        )
        if file_path:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, file_path)

    def _get_suggested_includes_dir(self):
        """Attempts to determine the Includes/WaspLib/utils directory based on current context."""
        current_path = self.dir_entry.get().strip().strip('"').strip("'")
        
        # Try to deduce from current selection in dir_entry
        if current_path:
            try:
                abs_path = os.path.abspath(current_path)
                parts = abs_path.split(os.sep)
                
                # Search for 'Data' to switch to 'Includes' branch
                # Iterate backwards to find the relevant 'Data' folder
                for i in range(len(parts) - 1, -1, -1):
                    if parts[i].lower() == 'data':
                        # Construct candidate path: .../Includes/WaspLib/utils
                        base_path = os.sep.join(parts[:i])
                        candidate = os.path.join(base_path, "Includes", "WaspLib", "utils")
                        if os.path.exists(candidate):
                            return candidate
            except Exception:
                pass

        # Fallback: Check relative to script location (Standard Simba Structure)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Check ../../Includes/WaspLib/utils (Sibling of Scripts folder's parent)
        candidate_rel = os.path.normpath(os.path.join(script_dir, "../../Includes/WaspLib/utils"))
        if os.path.exists(candidate_rel):
            return candidate_rel
            
        # Check existing hardcoded path logic just in case
        candidate_old = os.path.normpath(os.path.join(script_dir, "Includes/WaspLib/utils"))
        if os.path.exists(candidate_old):
            return candidate_old
            
        return os.getcwd()

    def allow_custom_jsons(self):
        initial_dir = self._get_suggested_includes_dir()
        
        target_path = filedialog.askopenfilename(
            title="Select assets.simba",
            initialdir=initial_dir,
            initialfile="assets.simba",
            filetypes=[("Simba Files", "*.simba"), ("All Files", "*.*")]
        )

        if not target_path:
            return

        target_path = os.path.normpath(target_path)

        # Modify File
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            new_lines = []
            skipping = False
            processed = False
            
            replacement = [
                "procedure TWLAssets.Update();\n",
                "begin\n",
                "  WriteLn(GetDebugLn('WLAssets', 'Custom JSONs allowed. Skipping online update check. Everything is okay.'));\n",
                "  Self.JSON := Self.LoadJSON();\n",
                "end;\n"
            ]
            
            for line in lines:
                if line.strip().startswith("procedure TWLAssets.Update();"):
                    new_lines.extend(replacement)
                    skipping = True
                    processed = True
                    continue
                
                if skipping:
                    if line.startswith("end;"):
                        skipping = False
                    continue
                
                new_lines.append(line)
                    
            if not processed:
                messagebox.showwarning("Warning", "Could not find procedure TWLAssets.Update() to replace.")
                return

            with open(target_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
                
            messagebox.showinfo("Success", "Successfully updated assets.simba to allow custom JSONs.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to modify file:\n{e}")

    def restore_default_jsons(self):
        initial_dir = self._get_suggested_includes_dir()
        
        target_path = filedialog.askopenfilename(
            title="Select assets.simba to Restore",
            initialdir=initial_dir,
            initialfile="assets.simba",
            filetypes=[("Simba Files", "*.simba"), ("All Files", "*.*")]
        )

        if not target_path:
            return

        target_path = os.path.normpath(target_path)
        url = "https://raw.githubusercontent.com/WaspScripts/WaspLib/main/utils/assets.simba"

        try:
            # Create a default SSL context
            context = ssl.create_default_context()
            
            # Download the file content
            with urllib.request.urlopen(url, context=context) as response:
                content = response.read().decode('utf-8')
            
            # Write the content to the selected file
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)

            messagebox.showinfo("Success", "Restored successfully.\nOriginal assets.simba has been restored from GitHub.")
        except Exception as e:
            messagebox.showerror("Restore Error", f"Failed to restore file from GitHub:\n{e}")

    def update_chunk_translator(self):
        initial_dir = self._get_suggested_includes_dir()
        suggested_path = os.path.join(initial_dir, "math", "rstranslator.simba")
        suggested_path = os.path.normpath(suggested_path)
        
        target_path = filedialog.askopenfilename(
            title="Select rstranslator.simba to Update",
            initialdir=os.path.dirname(suggested_path),
            initialfile=os.path.basename(suggested_path),
            filetypes=[("Simba Files", "*.simba"), ("All Files", "*.*")]
        )
        
        if not target_path:
            return
        
        target_path = os.path.normpath(target_path)
        
        # Ensure directory exists just in case
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        url = "https://raw.githubusercontent.com/LeFleurDeLys/WaspLib/main/utils/math/rstranslator.simba"

        try:
            # Create a default SSL context
            context = ssl.create_default_context()
            
            # Download the file content
            with urllib.request.urlopen(url, context=context) as response:
                content = response.read().decode('utf-8')
            
            # Write the content to the selected file
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            messagebox.showinfo("Success", f"Updated Chunk Translator successfully at:\n{target_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update Chunk Translator:\n{e}")

    def restore_old_chunk_translator(self):
        initial_dir = self._get_suggested_includes_dir()
        suggested_path = os.path.join(initial_dir, "math", "rstranslator.simba")
        suggested_path = os.path.normpath(suggested_path)
        
        target_path = filedialog.askopenfilename(
            title="Select rstranslator.simba to Restore",
            initialdir=os.path.dirname(suggested_path),
            initialfile=os.path.basename(suggested_path),
            filetypes=[("Simba Files", "*.simba"), ("All Files", "*.*")]
        )
        
        if not target_path:
            return
        
        target_path = os.path.normpath(target_path)
        
        url = "https://raw.githubusercontent.com/WaspScripts/WaspLib/main/utils/math/rstranslator.simba"

        try:
            context = ssl.create_default_context()
            with urllib.request.urlopen(url, context=context) as response:
                content = response.read().decode('utf-8')
            
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)

            messagebox.showinfo("Success", "Restored Old Chunk Translator successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore Chunk Translator:\n{e}")

    def delete_npc_cache(self):
        suggested_path = os.path.abspath(os.path.join("Data", "Cache", "map", "npcs"))
        suggested_path = os.path.normpath(suggested_path)
        
        target_path = filedialog.askdirectory(
            title="Select NPC Cache Folder to Delete",
            initialdir=os.path.dirname(suggested_path),
            mustexist=True
        )
        
        if not target_path:
            return
        
        target_path = os.path.normpath(target_path)
        
        # Confirm deletion
        if not messagebox.askyesno("Confirm Deletion",
                                   f"Are you sure you want to delete the following folder and all its contents?\n\n{target_path}\n\nThis action cannot be undone."):
            return
        
        try:
            # Delete the directory and all its contents
            if os.path.exists(target_path):
                shutil.rmtree(target_path)
                messagebox.showinfo("Success", f"Successfully deleted:\n{target_path}")
            else:
                messagebox.showwarning("Warning", "The selected folder does not exist.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete folder:\n{e}")

    def run_update(self):
        target_path = self.dir_entry.get().strip().strip('"').strip("'")
        # Hardcoded offsets
        x_off = 4096
        y_off = 0

        if not os.path.exists(target_path):
            messagebox.showerror("Path Error", "The specified path does not exist.")
            return

        files_processed = 0
        files_modified = 0
        errors = 0
        total_files = 0

        # First pass: count total files for progress tracking
        if os.path.isfile(target_path):
            if target_path.endswith(".json"):
                total_files = 1
            elif target_path.endswith(".zip"):
                with zipfile.ZipFile(target_path, 'r') as zip_ref:
                    total_files = sum(1 for f in zip_ref.namelist() if f.endswith(".json"))
        else:
            for root_dir, _, files in os.walk(target_path):
                for file in files:
                    if file.endswith(".json"):
                        total_files += 1
                    elif file.endswith(".zip"):
                        zip_path = os.path.join(root_dir, file)
                        try:
                            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                                total_files += sum(1 for f in zip_ref.namelist() if f.endswith(".json"))
                        except:
                            pass

        self.status_label.config(text=f"Processing 0/{total_files} files...", fg="blue")
        self.root.update()

        if os.path.isfile(target_path):
            # Process single file
            if target_path.endswith(".json"):
                files_processed += 1
                try:
                    if self.process_file(target_path, x_off, y_off):
                        files_modified += 1
                except Exception as e:
                    print(f"Failed to process {target_path}: {e}")
                    errors += 1
            elif target_path.endswith(".zip"):
                self.status_label.config(text=f"Processing zip: {os.path.basename(target_path)}...", fg="blue")
                self.root.update()
                z_processed, z_modified, z_errors = self.process_zip(target_path, x_off, y_off)
                files_processed += z_processed
                files_modified += z_modified
                errors += z_errors
            else:
                messagebox.showerror("Error", "Target must be a directory, .json, or .zip file.")
                self.status_label.config(text="Ready", fg="gray")
                return
        else:
            # Process directory (recursive) - process zips one at a time sequentially
            for root_dir, _, files in os.walk(target_path):
                for file in files:
                    if file.endswith(".json"):
                        file_path = os.path.join(root_dir, file)
                        files_processed += 1
                        self.status_label.config(text=f"Processing {files_processed}/{total_files}: {os.path.basename(file_path)}", fg="blue")
                        self.root.update()
                        try:
                            if self.process_file(file_path, x_off, y_off):
                                files_modified += 1
                        except Exception as e:
                            print(f"Failed to process {file_path}: {e}")
                            errors += 1
                    elif file.endswith(".zip"):
                        zip_path = os.path.join(root_dir, file)
                        self.status_label.config(text=f"Processing zip: {os.path.basename(zip_path)}...", fg="blue")
                        self.root.update()
                        z_processed, z_modified, z_errors = self.process_zip(zip_path, x_off, y_off)
                        files_processed += z_processed
                        files_modified += z_modified
                        errors += z_errors

        result_msg = (f"Processing Complete!\n\n"
                      f"Files Scanned: {files_processed}\n"
                      f"Files Updated: {files_modified}\n"
                      f"Errors: {errors}")
        
        self.status_label.config(text=f"Finished. Updated {files_modified} files.", fg="green")
        messagebox.showinfo("Summary", result_msg)

    def process_zip(self, zip_path, x_off, y_off):
        processed = 0
        modified = 0
        errors = 0
        modified_files = {}  # filename -> modified content
        original_files = {}  # filename -> original content (bytes)

        try:
            # First pass: read all files and process JSONs
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Read all files into memory
                for info in zip_ref.infolist():
                    if not info.filename.endswith("/"):  # Skip directory entries
                        with zip_ref.open(info.filename) as f:
                            original_files[info.filename] = f.read()
                
                # Process JSON files
                for filename in original_files.keys():
                    if filename.endswith(".json"):
                        processed += 1
                        try:
                            content = original_files[filename].decode('utf-8')
                            
                            # Parse and process
                            try:
                                data = json.loads(content)
                                
                                # Determine Floor from parent directory
                                try:
                                    parent_dir = os.path.basename(os.path.dirname(filename))
                                    floor = int(parent_dir)
                                except ValueError:
                                    floor = 0
                                
                                if floor < 0:
                                    floor = 0
                                
                                # Check if modification is needed
                                if self.recursive_update(data, x_off, y_off, floor):
                                    # Format modified content
                                    if isinstance(data, list):
                                        formatted = "[\n"
                                        for i, item in enumerate(data):
                                            line = json.dumps(item, separators=(',', ':'), ensure_ascii=False)
                                            if i < len(data) - 1:
                                                formatted += f"  {line},\n"
                                            else:
                                                formatted += f"  {line}\n"
                                        formatted += "]"
                                    else:
                                        formatted = json.dumps(data, indent=4, ensure_ascii=False)
                                    
                                    modified_files[filename] = formatted.encode('utf-8')
                                    modified += 1
                            except json.JSONDecodeError:
                                pass
                        except Exception as e:
                            print(f"Failed to process {filename} inside zip: {e}")
                            errors += 1

            # Only re-zip if there were modifications
            if modified_files:
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
                    for filename, content in original_files.items():
                        if filename in modified_files:
                            # Use modified content
                            zip_ref.writestr(filename, modified_files[filename])
                        else:
                            # Use original content
                            zip_ref.writestr(filename, content)
                                
        except Exception as e:
            print(f"Failed to process zip {zip_path}: {e}")
            errors += 1
            
        return processed, modified, errors

    def process_file(self, file_path, x_off, y_off):
        # Determine Floor from parent directory
        try:
            parent_dir = os.path.basename(os.path.dirname(file_path))
            floor = int(parent_dir)
        except ValueError:
            floor = 0
        
        # If floor <= 0, we treat it as 0
        if floor < 0:
            floor = 0

        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return False

        if self.recursive_update(data, x_off, y_off, floor):
            with open(file_path, 'w', encoding='utf-8') as f:
                if isinstance(data, list):
                    f.write("[\n")
                    for i, item in enumerate(data):
                        line = json.dumps(item, separators=(',', ':'), ensure_ascii=False)
                        if i < len(data) - 1:
                            f.write(f"  {line},\n")
                        else:
                            f.write(f"  {line}\n")
                    f.write("]")
                else:
                    json.dump(data, f, indent=4)
            return True
        return False

    def recursive_update(self, data, x_off, y_off, floor):
        """Recursively traverse JSON structure to find 'coordinates' keys."""
        modified = False
        
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "coordinates" and isinstance(value, list):
                    # Found coordinates list, update it
                    changed, new_coords = self.update_coords_list(value, x_off, y_off, floor)
                    if changed:
                        data[key] = new_coords
                        modified = True
                elif isinstance(value, (dict, list)):
                    # Recurse deeper
                    if self.recursive_update(value, x_off, y_off, floor):
                        modified = True
                        
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    if self.recursive_update(item, x_off, y_off, floor):
                        modified = True
                        
        return modified

    def update_coords_list(self, coords_list, x_off, y_off, floor):
        """Updates a list of coordinate pairs: [[x, y], [x2, y2]]"""
        changed = False
        new_list = []

        for item in coords_list:
            if isinstance(item, list) and len(item) >= 2:
                if isinstance(item[0], (int, float)) and isinstance(item[1], (int, float)):
                    original_x, original_y = item[0], item[1]
                    new_x, new_y = original_x, original_y

                    floor_val = 0
                    if floor > 0:
                        floor_val = 12800 * floor * 2
                    
                    # Apply floor offset first
                    if floor > 0:
                        new_x += floor_val
                        new_y += floor_val

                    # Apply offsets only if they are non-zero
                    if x_off != 0:
                        new_x += x_off
                    
                    new_y = original_y # Y should never be modified

                    new_list.append([new_x, new_y])
                    
                    if new_x != original_x or new_y != original_y:
                        changed = True
                else:
                    new_list.append(item)
            else:
                new_list.append(item)
                
        return changed, new_list

    def run_search(self):
        target_path = self.dir_entry.get().strip().strip('"').strip("'")
        keyword = self.keyword_entry.get().strip()

        if not keyword:
            messagebox.showerror("Input Error", "Please enter a keyword to search.")
            return

        if not os.path.exists(target_path):
            messagebox.showerror("Path Error", "The specified path does not exist.")
            return

        self.status_label.config(text="Searching...", fg="blue")
        self.root.update()

        matches = []
        try:
            matches = self.perform_search(target_path, keyword)
        except Exception as e:
            messagebox.showerror("Search Error", f"An error occurred during search: {e}")
            self.status_label.config(text="Error", fg="red")
            return

        self.status_label.config(text=f"Search Complete. Found {len(matches)} matches.", fg="green")
        self.show_results(matches, keyword)

    def perform_search(self, path, keyword):
        matches = []
        
        if os.path.isfile(path):
            if path.endswith(".json"):
                if self.check_file_content(path, keyword):
                    matches.append(path)
            elif path.endswith(".zip"):
                matches.extend(self.search_zip(path, keyword))
        else:
            for root_dir, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root_dir, file)
                    if file.endswith(".json"):
                        if self.check_file_content(file_path, keyword):
                            matches.append(file_path)
                    elif file.endswith(".zip"):
                        matches.extend(self.search_zip(file_path, keyword))
        return matches

    def check_file_content(self, file_path, keyword):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if keyword.lower() in content.lower():
                    return True
        except Exception:
            pass
        return False

    def search_zip(self, zip_path, keyword):
        matches = []
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                for filename in z.namelist():
                    if filename.endswith(".json"):
                        try:
                            with z.open(filename) as f:
                                content = f.read().decode('utf-8', errors='ignore')
                                if keyword.lower() in content.lower():
                                    matches.append(f"{zip_path} -> {filename}")
                        except Exception:
                            pass
        except Exception:
            pass
        return matches

    def open_selected_file(self, event):
        widget = event.widget
        selection = widget.curselection()
        if not selection:
            return
        
        item = widget.get(selection[0])
        
        try:
            if " -> " in item:
                zip_path, inner_file = item.split(" -> ")
                self.open_zip_entry(zip_path, inner_file)
            else:
                if os.path.exists(item):
                    os.startfile(item)
                else:
                    messagebox.showerror("Error", f"File not found: {item}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}")

    def open_zip_entry(self, zip_path, inner_file):
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                content = z.read(inner_file)
            
            base_name = os.path.basename(inner_file)
            name_part, ext_part = os.path.splitext(base_name)
            
            # Create a temporary file
            fd, path = tempfile.mkstemp(suffix=ext_part, prefix=f"{name_part}_")
            
            with os.fdopen(fd, 'wb') as tmp:
                tmp.write(content)
            
            os.startfile(path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not extract/open file from zip:\n{e}")

    def get_json_content(self, item):
        try:
            if " -> " in item:
                zip_path, inner_file = item.split(" -> ")
                with zipfile.ZipFile(zip_path, 'r') as z:
                    content = z.read(inner_file)
                    return json.loads(content)
            else:
                with open(item, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            return None

    def find_keyword_in_json(self, data, keyword, path=None):
        if path is None:
            path = []
        results = []
        
        kw_lower = keyword.lower()
        
        if isinstance(data, dict):
            is_match = False
            # Check current dict for immediate match
            for k, v in data.items():
                if kw_lower in str(k).lower():
                    is_match = True
                    break
                if isinstance(v, (str, int, float, bool, type(None))) and kw_lower in str(v).lower():
                    is_match = True
                    break
            
            if is_match:
                results.append((data, path))
            
            # Recurse
            for k, v in data.items():
                if isinstance(v, (dict, list)):
                    results.extend(self.find_keyword_in_json(v, keyword, path + [k]))
                    
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    results.extend(self.find_keyword_in_json(item, keyword, path + [i]))
                elif isinstance(item, (str, int, float, bool, type(None))) and kw_lower in str(item).lower():
                    results.append((item, path + [i]))
                    
        return results

    def update_preview(self, match_data, title, match_path, file_path):
        if self.preview_window is None or not self.preview_window.winfo_exists():
            self.preview_window = tk.Toplevel(self.root)
            self.preview_window.title("Edit JSON Match")
            self.preview_window.geometry("600x600")
            
            # Text Editor Area
            frame = tk.Frame(self.preview_window)
            frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            ysb = tk.Scrollbar(frame, orient=tk.VERTICAL)
            ysb.pack(side=tk.RIGHT, fill=tk.Y)
            
            xsb = tk.Scrollbar(frame, orient=tk.HORIZONTAL)
            xsb.pack(side=tk.BOTTOM, fill=tk.X)
            
            self.preview_text = tk.Text(frame, wrap=tk.NONE, yscrollcommand=ysb.set, xscrollcommand=xsb.set, font=("Consolas", 10), undo=True)
            self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Undo/Redo bindings
            self.preview_text.bind("<Control-z>", lambda e: self.preview_text.edit_undo())
            self.preview_text.bind("<Control-y>", lambda e: self.preview_text.edit_redo())
            self.preview_text.bind("<Control-Shift-Z>", lambda e: self.preview_text.edit_redo())
            
            ysb.config(command=self.preview_text.yview)
            xsb.config(command=self.preview_text.xview)

            # Button Bar
            btn_frame = tk.Frame(self.preview_window)
            btn_frame.pack(fill=tk.X, padx=5, pady=5)

            tk.Button(btn_frame, text="Overwrite File", command=self.save_changes, bg="#d9534f", fg="white", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text="Cancel", command=self.preview_window.destroy).pack(side=tk.RIGHT, padx=5)
        else:
            self.preview_window.lift()

        # Update Context
        self.current_editing_context = {
            "file_path": file_path,
            "match_path": match_path
        }

        self.preview_window.title(f"Editing: {title}")
        self.preview_text.delete(1.0, tk.END)
        
        try:
            formatted = json.dumps(match_data, indent=4, ensure_ascii=False)
            self.preview_text.insert(tk.END, formatted)
        except Exception:
            self.preview_text.insert(tk.END, str(match_data))

    def on_result_select(self, event, keyword):
        widget = event.widget
        selection = widget.curselection()
        if not selection:
            return
        
        item = widget.get(selection[0])
        full_data = self.get_json_content(item)
        
        if full_data is not None:
            matches = self.find_keyword_in_json(full_data, keyword)
            if matches:
                # User Requirement: Edit first match
                first_match, path = matches[0]
                self.update_preview(first_match, item, path, item)
            else:
                messagebox.showinfo("Info", "No matches found in structure.")

    def save_changes(self):
        if not self.current_editing_context:
            return

        # 1. Confirm
        if not messagebox.askyesno("Confirm Overwrite", "Are you certain you want to overwrite the file?"):
            return

        # 2. Parse JSON
        content = self.preview_text.get(1.0, tk.END).strip()
        try:
            new_obj = json.loads(content)
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON Error", f"Invalid JSON:\n{e}")
            return

        file_item = self.current_editing_context["file_path"]
        match_path = self.current_editing_context["match_path"]

        try:
            if " -> " in file_item:
                # It's a zip file
                zip_path, inner_file = file_item.split(" -> ")
                self.update_zip_file(zip_path, inner_file, match_path, new_obj)
            else:
                # Regular file
                self.update_regular_file(file_item, match_path, new_obj)
            
            messagebox.showinfo("Success", "File updated successfully!")
            self.preview_window.destroy()
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save changes:\n{e}")

    def update_regular_file(self, file_path, match_path, new_obj):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not match_path:
            data = new_obj
        else:
            self.set_value_by_path(data, match_path, new_obj)
        
        with open(file_path, 'w', encoding='utf-8') as f:
             json.dump(data, f, indent=4)

    def update_zip_file(self, zip_path, inner_file, match_path, new_obj):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract all
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            target_path = os.path.join(temp_dir, inner_file)
            
            # Read, Modify, Write
            with open(target_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not match_path:
                data = new_obj
            else:
                self.set_value_by_path(data, match_path, new_obj)
            
            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
                
            # Re-zip
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zip_ref.write(file_path, arcname)

    def set_value_by_path(self, data, path, value):
        if not path:
             raise ValueError("Cannot set value for empty path.")

        current = data
        for i in range(len(path) - 1):
            key = path[i]
            current = current[key]
        
        last_key = path[-1]
        current[last_key] = value

    def show_results(self, matches, keyword):
        top = tk.Toplevel(self.root)
        top.title(f"Search Results: '{keyword}'")
        top.geometry("600x400")

        lbl = tk.Label(top, text=f"Found {len(matches)} files containing '{keyword}':", font=("Helvetica", 10, "bold"))
        lbl.pack(pady=10)

        # Scrollbar and Listbox
        frame = tk.Frame(top)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL)
        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, selectmode=tk.EXTENDED)
        scrollbar.config(command=listbox.yview)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for m in matches:
            listbox.insert(tk.END, m)
        
        listbox.bind('<Double-1>', self.open_selected_file)
        listbox.bind('<<ListboxSelect>>', lambda e: self.on_result_select(e, keyword))
        
        tk.Button(top, text="Close", command=top.destroy).pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = CoordinateUpdaterApp(root)
    root.mainloop()