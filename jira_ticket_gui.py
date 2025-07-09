import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
import sys
from create_jira_tickets import parse_issues, create_jira_tickets, get_text, create_jira_tickets_with_type, get_enhanced_issues
from jira import JIRAError

# Import AI analyzer
try:
    from ai_document_analyzer import get_ai_enhanced_issues, is_ai_available
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("⚠️  AI document analyzer not available. Install OpenAI package: pip install openai")

# Import configuration
try:
    from config import JIRA_CONFIG
    DEFAULT_JIRA_SERVER = JIRA_CONFIG["server"]
    DEFAULT_JIRA_USERNAME = JIRA_CONFIG["username"]
    DEFAULT_JIRA_API_TOKEN = JIRA_CONFIG["api_token"]
except ImportError:
    # Fallback values if config.py doesn't exist
    DEFAULT_JIRA_SERVER = "https://comwrapuk.atlassian.net"
    DEFAULT_JIRA_USERNAME = "s.sznajder@reply.com"
    DEFAULT_JIRA_API_TOKEN = "YOUR_API_TOKEN_HERE"

class JiraApp:
    """A simple Tkinter GUI application for creating Jira tickets from a Word document."""
    def __init__(self, root):
        """Initializes the main application window and its widgets."""
        self.root = root
        self.root.title("Jira Ticket Creator")
        self.root.geometry("800x700")

        # --- GUI Layout ---

        # Frame for input fields
        input_frame = tk.Frame(root, padx=10, pady=10)
        input_frame.pack(fill="x", expand=False)

        # Labels and Entry widgets for user input
        labels = ["Jira Server URL:", "Jira Username:", "API Token:"]
        self.entries = {}
        
        # Default values for the fields
        default_values = [DEFAULT_JIRA_SERVER, DEFAULT_JIRA_USERNAME, DEFAULT_JIRA_API_TOKEN]

        for i, label_text in enumerate(labels):
            label = tk.Label(input_frame, text=label_text)
            label.grid(row=i, column=0, sticky="w", padx=5, pady=5)
            entry = tk.Entry(input_frame, width=50)
            # Hide text for the API token field
            if "token" in label_text.lower():
                entry.config(show="*")
            
            # Auto-populate with default values
            if i < len(default_values) and default_values[i]:
                entry.insert(0, default_values[i])
                
            entry.grid(row=i, column=1, sticky="ew", padx=5, pady=5)
            self.entries[label_text] = entry
        
        # Project Key dropdown
        project_label = tk.Label(input_frame, text="Project Key:")
        project_label.grid(row=len(labels), column=0, sticky="w", padx=5, pady=5)
        self.project_var = tk.StringVar(value="Select Project...")
        self.project_combo = ttk.Combobox(input_frame, textvariable=self.project_var, 
                                         values=["Select Project..."], state="readonly", width=47)
        self.project_combo.grid(row=len(labels), column=1, sticky="ew", padx=5, pady=5)
        
        # Button to fetch projects
        fetch_projects_button = tk.Button(input_frame, text="🔄 Fetch Projects", command=self.fetch_projects, bg="#e3f2fd")
        fetch_projects_button.grid(row=len(labels)+1, column=0, sticky="w", padx=5, pady=5)
        
        # Issue Type dropdown
        issue_type_label = tk.Label(input_frame, text="Issue Type:")
        issue_type_label.grid(row=len(labels)+2, column=0, sticky="w", padx=5, pady=5)
        self.issue_type_var = tk.StringVar(value="Task")
        issue_type_combo = ttk.Combobox(input_frame, textvariable=self.issue_type_var, 
                                       values=["Task", "Story", "Bug", "Epic"], state="readonly", width=47)
        issue_type_combo.grid(row=len(labels)+2, column=1, sticky="ew", padx=5, pady=5)
        
        # Epic dropdown
        epic_label = tk.Label(input_frame, text="Epic:")
        epic_label.grid(row=len(labels)+3, column=0, sticky="w", padx=5, pady=5)
        self.epic_var = tk.StringVar(value="None")
        self.epic_combo = ttk.Combobox(input_frame, textvariable=self.epic_var, 
                                      values=["None"], state="readonly", width=47)
        self.epic_combo.grid(row=len(labels)+3, column=1, sticky="ew", padx=5, pady=5)
        
        # Status dropdown
        status_label = tk.Label(input_frame, text="Initial Status:")
        status_label.grid(row=len(labels)+4, column=0, sticky="w", padx=5, pady=5)
        self.status_var = tk.StringVar(value="To Do")
        self.status_combo = ttk.Combobox(input_frame, textvariable=self.status_var, 
                                        values=["To Do", "In Progress", "Done", "Backlog"], state="readonly", width=47)
        self.status_combo.grid(row=len(labels)+4, column=1, sticky="ew", padx=5, pady=5)
        
        # Button to fetch statuses
        fetch_statuses_button = tk.Button(input_frame, text="🔄 Fetch Statuses", command=self.fetch_statuses, bg="#e8f5e8")
        fetch_statuses_button.grid(row=len(labels)+5, column=0, sticky="w", padx=5, pady=5)
        
        # Button to fetch epics
        fetch_epics_button = tk.Button(input_frame, text="🔄 Fetch Epics", command=self.fetch_epics, bg="#f0f0f0")
        fetch_epics_button.grid(row=len(labels)+6, column=0, sticky="w", padx=5, pady=5)
        
        # Analysis Mode selection
        analysis_label = tk.Label(input_frame, text="Analysis Mode:")
        analysis_label.grid(row=len(labels)+7, column=0, sticky="w", padx=5, pady=5)
        self.analysis_mode_var = tk.StringVar(value="Enhanced" if AI_AVAILABLE and is_ai_available() else "Basic")
        
        # Create analysis mode options based on availability
        analysis_options = ["Basic"]
        if AI_AVAILABLE:
            if is_ai_available():
                analysis_options.append("AI-Powered")
                analysis_options.append("Enhanced")  # Previous enhanced extraction
            else:
                analysis_options.append("AI-Powered (Configure API Key)")
        
        analysis_combo = ttk.Combobox(input_frame, textvariable=self.analysis_mode_var, 
                                     values=analysis_options, state="readonly", width=47)
        analysis_combo.grid(row=len(labels)+7, column=1, sticky="ew", padx=5, pady=5)
        
        # Add tooltip/help text
        analysis_help = tk.Label(input_frame, text="ℹ️ AI-Powered: Uses OpenAI to intelligently extract tasks | Enhanced: Extracts text + images | Basic: Simple text parsing", 
                               font=("Arial", 8), fg="gray", wraplength=400, justify="left")
        analysis_help.grid(row=len(labels)+8, column=0, columnspan=2, sticky="w", padx=5, pady=(0,5))
        
        # Make the entry column expandable
        input_frame.grid_columnconfigure(1, weight=1)

        # File selection widgets
        self.file_path_label = tk.Label(input_frame, text="No file selected.")
        self.file_path_label.grid(row=len(labels)+9, column=1, sticky="w", padx=5, pady=5)
        browse_button = tk.Button(input_frame, text="Browse for Word Doc", command=self.browse_file)
        browse_button.grid(row=len(labels)+9, column=0, sticky="w", padx=5, pady=5)
        self.selected_file = None

        # Button frame for actions
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)

        # Preview button
        self.preview_button = tk.Button(button_frame, text="1️⃣ Preview Tickets", command=self.preview_tickets, bg="#e0e0e0", width=15)
        self.preview_button.pack(side=tk.LEFT, padx=5)

        # Main action button
        self.create_button = tk.Button(button_frame, text="2️⃣ Create in Jira", command=self.start_ticket_creation, bg="#cccccc", fg="gray", width=15)
        self.create_button.pack(side=tk.LEFT, padx=5)
        self.create_button.config(state="disabled")  # Disabled until preview is done

        # Status label
        self.status_label = tk.Label(root, text="📁 Select a Word document and click 'Preview Tickets' to start", fg="blue")
        self.status_label.pack(pady=5)

        # Scrolled text widget to act as an output console
        console_label = tk.Label(root, text="Preview / Output Console:", anchor="w")
        console_label.pack(fill="x", padx=10, pady=(10,0))
        
        self.output_console = scrolledtext.ScrolledText(root, height=20, state="disabled")
        self.output_console.pack(padx=10, pady=5, fill="both", expand=True)
        
        # Store parsed issues for later use
        self.parsed_issues = []
        
        # Auto-fetch projects if credentials are available
        self.root.after(500, self.auto_fetch_projects)  # Delay to ensure GUI is fully loaded
    
    def auto_fetch_projects(self):
        """Automatically fetch projects if credentials are pre-filled."""
        server = self.entries["Jira Server URL:"].get().strip()
        username = self.entries["Jira Username:"].get().strip()
        api_token = self.entries["API Token:"].get().strip()
        
        # Only auto-fetch if all credentials are filled and API token is not the default placeholder
        if (all([server, username, api_token]) and 
            api_token != "YOUR_API_TOKEN_HERE" and 
            len(api_token) > 10):  # Basic validation for real API token
            self.log_message("🚀 Auto-fetching projects with stored credentials...")
            self.fetch_projects()
    
    def browse_file(self):
        """Opens a file dialog to select a .docx file and updates the label."""
        self.selected_file = filedialog.askopenfilename(
            title="Select a Word Document",
            filetypes=(("Word Documents", "*.docx"), ("All files", "*.*"))
        )
        if self.selected_file:
            # Display just the filename for cleanliness
            self.file_path_label.config(text=self.selected_file.split('/')[-1])
            # Reset the create button state when a new file is selected
            self.create_button.config(state="disabled", bg="#cccccc", fg="gray", text="2️⃣ Create in Jira")
            self.status_label.config(text="📄 Document selected! Click 'Preview Tickets' to see what will be created", fg="green")
            self.clear_console()
        else:
            self.file_path_label.config(text="No file selected.")
            self.status_label.config(text="📁 Select a Word document and click 'Preview Tickets' to start", fg="blue")

    def fetch_projects(self):
        """Fetch all projects from the specified Jira server."""
        # Get credentials
        server = self.entries["Jira Server URL:"].get().strip()
        username = self.entries["Jira Username:"].get().strip()
        api_token = self.entries["API Token:"].get().strip()
        
        if not all([server, username, api_token]):
            messagebox.showerror("Missing Information", "Please fill in all Jira credential fields before fetching projects.")
            return
        
        # Show loading state
        original_text = self.project_combo.get()
        self.project_combo.config(state="normal")
        self.project_combo.delete(0, tk.END)
        self.project_combo.insert(0, "🔄 Loading...")
        self.project_combo.config(state="readonly")
        self.root.update()
        
        try:
            from jira import JIRA, JIRAError
            
            # Connect to Jira
            jira = JIRA(server=server, basic_auth=(username, api_token))
            
            # Search for projects
            projects = jira.projects()
            
            project_options = ["Select Project..."]  # Default option
            for project in projects:
                project_options.append(project.key)
            
            # Update dropdown
            self.project_combo.config(values=project_options)
            self.project_var.set("Select Project...")
            
            if len(projects) > 0:
                self.log_message(f"✅ Found {len(projects)} projects.")
                self.status_label.config(text=f"✅ Loaded {len(projects)} projects.", fg="green")
            else:
                self.log_message(f"ℹ️  No projects found.")
                self.status_label.config(text=f"ℹ️  No projects found.", fg="blue")
                
        except JIRAError as e:
            error_msg = f"Failed to fetch projects: {e}"
            self.log_message(f"❌ {error_msg}")
            self.status_label.config(text="❌ Failed to fetch projects - check credentials", fg="red")
            messagebox.showerror("Project Fetch Error", f"Could not fetch projects from server {server}:\\n\\n{error_msg}")
            
        except Exception as e:
            error_msg = f"Unexpected error fetching projects: {e}"
            self.log_message(f"❌ {error_msg}")
            self.status_label.config(text="❌ Error fetching projects", fg="red")
            messagebox.showerror("Error", error_msg)
            
        finally:
            # Reset dropdown state
            self.project_combo.config(state="readonly")

    def fetch_epics(self):
        """Fetch all epics from the specified Jira project."""
        # Get credentials
        server = self.entries["Jira Server URL:"].get().strip()
        username = self.entries["Jira Username:"].get().strip()
        api_token = self.entries["API Token:"].get().strip()
        project_key = self.project_var.get()
        
        if not all([server, username, api_token, project_key]):
            messagebox.showerror("Missing Information", "Please fill in all Jira credential fields before fetching epics.")
            return
        
        # Validate project selection
        if project_key == "Select Project..." or not project_key:
            messagebox.showerror("Project Not Selected", "Please select a project from the dropdown first.")
            return
        
        # Show loading state
        original_text = self.epic_combo.get()
        self.epic_combo.config(state="normal")
        self.epic_combo.delete(0, tk.END)
        self.epic_combo.insert(0, "🔄 Loading...")
        self.epic_combo.config(state="readonly")
        self.root.update()
        
        try:
            from jira import JIRA, JIRAError
            
            # Connect to Jira
            jira = JIRA(server=server, basic_auth=(username, api_token))
            
            # Search for epics in the project
            jql = f'project = "{project_key}" AND issuetype = Epic ORDER BY summary ASC'
            epics = jira.search_issues(jql, maxResults=100)
            
            epic_options = ["None"]  # Default option
            for epic in epics:
                epic_display = f"{epic.key}: {epic.fields.summary}"
                epic_options.append(epic_display)
            
            # Update dropdown
            self.epic_combo.config(values=epic_options)
            self.epic_var.set("None")
            
            if len(epics) > 0:
                self.log_message(f"✅ Found {len(epics)} epics in project {project_key}")
                self.status_label.config(text=f"✅ Loaded {len(epics)} epics from project {project_key}", fg="green")
            else:
                self.log_message(f"ℹ️  No epics found in project {project_key}")
                self.status_label.config(text=f"ℹ️  No epics found in project {project_key}", fg="blue")
                
        except JIRAError as e:
            error_msg = f"Failed to fetch epics: {e}"
            self.log_message(f"❌ {error_msg}")
            self.status_label.config(text="❌ Failed to fetch epics - check credentials", fg="red")
            messagebox.showerror("Epic Fetch Error", f"Could not fetch epics from project {project_key}:\\n\\n{error_msg}")
            
        except Exception as e:
            error_msg = f"Unexpected error fetching epics: {e}"
            self.log_message(f"❌ {error_msg}")
            self.status_label.config(text="❌ Error fetching epics", fg="red")
            messagebox.showerror("Error", error_msg)
            
        finally:
            # Reset dropdown state
            self.epic_combo.config(state="readonly")

    def fetch_statuses(self):
        """Fetch all statuses from the specified Jira project."""
        # Get credentials
        server = self.entries["Jira Server URL:"].get().strip()
        username = self.entries["Jira Username:"].get().strip()
        api_token = self.entries["API Token:"].get().strip()
        project_key = self.project_var.get()
        
        if not all([server, username, api_token, project_key]):
            messagebox.showerror("Missing Information", "Please fill in all Jira credential fields before fetching statuses.")
            return
        
        # Validate project selection
        if project_key == "Select Project..." or not project_key:
            messagebox.showerror("Project Not Selected", "Please select a project from the dropdown first.")
            return
        
        # Show loading state
        original_text = self.status_combo.get()
        self.status_combo.config(state="normal")
        self.status_combo.delete(0, tk.END)
        self.status_combo.insert(0, "🔄 Loading...")
        self.status_combo.config(state="readonly")
        self.root.update()
        
        try:
            from jira import JIRA, JIRAError
            
            # Connect to Jira
            jira = JIRA(server=server, basic_auth=(username, api_token))
            
            # Get project information
            project = jira.project(project_key)
            
            # Get available statuses for the project
            statuses = jira.statuses()
            
            status_options = []
            for status in statuses:
                status_options.append(status.name)
            
            # Remove duplicates and sort
            status_options = sorted(list(set(status_options)))
            
            # Update dropdown
            self.status_combo.config(values=status_options)
            self.status_var.set("To Do" if "To Do" in status_options else status_options[0] if status_options else "To Do")
            
            if len(status_options) > 0:
                self.log_message(f"✅ Found {len(status_options)} statuses: {', '.join(status_options)}")
                self.status_label.config(text=f"✅ Loaded {len(status_options)} statuses from Jira", fg="green")
            else:
                self.log_message(f"ℹ️  No statuses found, using defaults")
                self.status_label.config(text=f"ℹ️  Using default statuses", fg="blue")
                
        except JIRAError as e:
            error_msg = f"Failed to fetch statuses: {e}"
            self.log_message(f"❌ {error_msg}")
            self.status_label.config(text="❌ Failed to fetch statuses - check credentials", fg="red")
            messagebox.showerror("Status Fetch Error", f"Could not fetch statuses from Jira:\\n\\n{error_msg}")
            
        except Exception as e:
            error_msg = f"Unexpected error fetching statuses: {e}"
            self.log_message(f"❌ {error_msg}")
            self.status_label.config(text="❌ Error fetching statuses", fg="red")
            messagebox.showerror("Error", error_msg)
            
        finally:
            # Reset dropdown state
            self.status_combo.config(state="readonly")

    def clear_console(self):
        """Clears the output console."""
        self.output_console.config(state="normal")
        self.output_console.delete(1.0, tk.END)
        self.output_console.config(state="disabled")

    def log_message(self, message):
        """Logs a message to the output console in a thread-safe way."""
        self.output_console.config(state="normal")
        self.output_console.insert(tk.END, message + "\\n")
        self.output_console.config(state="disabled")
        self.output_console.see(tk.END) # Auto-scroll to the bottom

    def flush(self):
        """A required method for the fake stdout interface."""
        pass

    def preview_tickets(self):
        """Parses the document and shows a preview of what tickets will be created."""
        if not self.selected_file:
            messagebox.showerror("Error", "Please select a Word document first.")
            return

        # Update button state during processing
        self.preview_button.config(state="disabled", text="🔄 Processing...")
        self.status_label.config(text="🔄 Parsing document and generating preview...", fg="orange")
        self.root.update()

        try:
            self.clear_console()
            self.log_message("📄 Parsing document...")
            
            # Get selected analysis mode
            analysis_mode = self.analysis_mode_var.get()
            self.log_message(f"🔍 Analysis Mode: {analysis_mode}")
            
            # Choose parsing method based on analysis mode
            if analysis_mode == "AI-Powered":
                if not AI_AVAILABLE or not is_ai_available():
                    self.log_message("❌ AI analysis not available. Please configure OpenAI API key in config.py")
                    messagebox.showerror("AI Not Available", "AI analysis requires OpenAI API key configuration.\n\nPlease update config.py with your OpenAI API key.")
                    return
                
                self.log_message("🤖 Using AI-powered analysis...")
                self.parsed_issues = get_ai_enhanced_issues(self.selected_file)
                
            elif analysis_mode == "Enhanced":
                self.log_message("🔧 Using enhanced extraction (with images)...")
                self.parsed_issues = get_enhanced_issues(self.selected_file)
                
            else:  # Basic mode
                self.log_message("📝 Using basic text extraction...")
                text = get_text(self.selected_file)
                self.parsed_issues = parse_issues(text)
            
            if not self.parsed_issues:
                self.log_message("❌ No issues found in the document. Please check the file content and formatting.")
                self.create_button.config(state="disabled", bg="#cccccc", fg="gray", text="2️⃣ Create in Jira")
                self.status_label.config(text="❌ No issues found. Check document format.", fg="red")
                return

            self.log_message(f"✅ Found {len(self.parsed_issues)} issues to create:\\n")
            
            # Display preview of each ticket
            for i, issue in enumerate(self.parsed_issues, 1):
                self.log_message(f"--- TICKET {i} ---")
                self.log_message(f"📝 Summary: {issue['title']}")
                
                # Show description preview (first 200 chars)
                desc_preview = issue['description'][:200] + ('...' if len(issue['description']) > 200 else '')
                self.log_message(f"📄 Description: {desc_preview}")
                
                # Show AI analysis metadata if available
                if analysis_mode == "AI-Powered":
                    if 'priority' in issue:
                        self.log_message(f"⚡ Priority: {issue['priority']}")
                    if 'complexity' in issue:
                        self.log_message(f"🔧 Complexity: {issue['complexity']}")
                    if 'category' in issue:
                        self.log_message(f"📂 Category: {issue['category']}")
                
                # Show image information if available (Enhanced mode)
                if 'images' in issue and issue['images']:
                    self.log_message(f"📸 Images: {len(issue['images'])} attached")
                    for img in issue['images']:
                        self.log_message(f"   • {img['filename']} ({img['size']} bytes)")
                
                # Show image information for AI mode too
                elif analysis_mode == "AI-Powered" and 'images' in issue and issue['images']:
                    self.log_message(f"📸 Images: {len(issue['images'])} will be attached")
                    for img in issue['images']:
                        self.log_message(f"   • {img['filename']} ({img['size']} bytes)")
                
                self.log_message("")
            
            self.log_message("=" * 60)
            self.log_message("✅ Preview complete! Review the tickets above.")
            self.log_message("🎯 Fill in your Jira credentials and click 'Create in Jira' to proceed.")
            
            # Enable the create button with clear styling
            self.create_button.config(state="normal", bg="#4CAF50", fg="white", text=f"2️⃣ Create {len(self.parsed_issues)} Tickets")
            self.status_label.config(text=f"✅ Ready to create {len(self.parsed_issues)} tickets! Fill in Jira credentials and click 'Create {len(self.parsed_issues)} Tickets'", fg="green")
            
        except FileNotFoundError:
            self.log_message(f"❌ Error: The file '{self.selected_file}' was not found.")
            self.create_button.config(state="disabled", bg="#cccccc", fg="gray", text="2️⃣ Create in Jira")
            self.status_label.config(text="❌ File not found error", fg="red")
        except Exception as e:
            self.log_message(f"❌ An error occurred while parsing: {e}")
            self.create_button.config(state="disabled", bg="#cccccc", fg="gray", text="2️⃣ Create in Jira")
            self.status_label.config(text="❌ Error during parsing", fg="red")
        finally:
            # Reset preview button
            self.preview_button.config(state="normal", text="1️⃣ Preview Tickets")

    def start_ticket_creation(self):
        """Validates inputs and starts the ticket creation process in a new thread."""
        # Get form data
        server = self.entries["Jira Server URL:"].get().strip()
        username = self.entries["Jira Username:"].get().strip()
        api_token = self.entries["API Token:"].get().strip()
        project_key = self.project_var.get()
        issue_type = self.issue_type_var.get()
        
        # Get selected epic
        selected_epic = self.epic_var.get()
        epic_key = None
        if selected_epic != "None" and ":" in selected_epic:
            epic_key = selected_epic.split(":")[0].strip()
        
        # Get selected status
        selected_status = self.status_var.get()
        
        if not all([server, username, api_token, project_key]):
            messagebox.showerror("Missing Information", "Please fill in all required fields.")
            return
        
        # Validate project selection
        if project_key == "Select Project..." or not project_key:
            messagebox.showerror("Project Not Selected", "Please select a project from the dropdown. Click '🔄 Fetch Projects' if the list is empty.")
            return

        if not self.parsed_issues:
            messagebox.showerror("No Preview", "Please click 'Preview Tickets' first to see what will be created.")
            return

        # Confirmation dialog with clear details
        epic_info = f"🔗 Epic: {epic_key}" if epic_key else "🔗 Epic: None"
        status_info = f"🔗 Status: {selected_status}" if selected_status else "🔗 Status: None"
        result = messagebox.askyesno(
            "⚠️ Confirm Ticket Creation", 
            f"You are about to create {len(self.parsed_issues)} tickets in Jira:\\n\\n"
            f"📍 Project: {project_key}\\n"
            f"🎫 Tickets: {len(self.parsed_issues)}\\n"
            f"📋 Type: {issue_type}\\n"
            f"{epic_info}\\n"
            f"{status_info}\\n"
            f"🔗 Server: {server}\\n\\n"
            f"This action cannot be undone.\\n\\n"
            f"Do you want to proceed?"
        )
        
        if not result:
            self.status_label.config(text="❌ Ticket creation cancelled by user", fg="orange")
            return

        # Update status
        self.status_label.config(text="🚀 Creating tickets in Jira... Please wait", fg="blue")

        # Run the core logic in a separate thread to prevent the GUI from freezing
        thread = threading.Thread(
            target=self.run_creation_logic, 
            args=(server, username, api_token, project_key, epic_key, selected_status)
        )
        thread.daemon = True # Allows main window to close even if thread is running
        thread.start()

    def run_creation_logic(self, server, username, api_token, project_key, epic_key=None, status_name=None):
        """The core logic that creates Jira tickets from the parsed issues."""
        # Disable buttons during processing to prevent multiple submissions
        self.create_button.config(state="disabled", text="🔄 Creating...", bg="#ff9800")
        self.preview_button.config(state="disabled")
        
        try:
            self.log_message("\n" + "=" * 60)
            self.log_message("🚀 Starting Jira ticket creation...")
            
            # Get the selected issue type
            issue_type = self.issue_type_var.get()
            self.log_message(f"📋 Issue Type: {issue_type}")
            
            # Log epic information
            if epic_key:
                self.log_message(f"🔗 Epic: {epic_key}")
            else:
                self.log_message(f"🔗 Epic: None (tickets will not be linked to an epic)")
            
            # Log status information
            if status_name:
                self.log_message(f"🔗 Initial Status: {status_name}")
            else:
                self.log_message(f"🔗 Initial Status: None (tickets will start as 'To Do')")
            
            # Temporarily redirect stdout to our GUI console to capture prints
            sys.stdout = self
            
            # Call the main ticket creation function with our pre-parsed issues
            created_tickets = create_jira_tickets_with_type(server, username, api_token, project_key, self.parsed_issues, issue_type, epic_key, status_name)
            
            if created_tickets:
                self.log_message("\n🎉 All tickets created successfully!")
                
                # Create a detailed status message with ticket count and project info
                project_key = self.project_var.get()
                server = self.entries["Jira Server URL:"].get().strip()
                
                # Show detailed success information
                success_msg = f"🎉 SUCCESS! Created {len(created_tickets)} tickets in project '{project_key}'"
                self.status_label.config(text=success_msg, fg="green")
                
                # Log additional success details
                self.log_message_colored(f"\n📊 SUMMARY:", "dark green")
                self.log_message_colored(f"   • Tickets Created: {len(created_tickets)}", "green")
                self.log_message_colored(f"   • Project: {project_key}", "green")
                self.log_message_colored(f"   • Server: {server}", "blue")
                self.log_message_colored(f"   • View Project: {server}/projects/{project_key}", "blue")
                
            else:
                self.log_message("\n❌ No tickets were created.")
                self.status_label.config(text="❌ No tickets were created", fg="red")

        except JIRAError as e:
            # Handle specific Jira errors
            if e.status_code == 401:
                error_msg = "Authentication failed. Please check your Jira username and API token."
                self.log_message(f"\n❌ Error: {error_msg}")
                self.status_label.config(text="❌ Authentication failed - check credentials", fg="red")
            elif e.status_code == 404:
                error_msg = f"Could not find project with key '{project_key}'. Please verify the project key."
                self.log_message(f"\n❌ Error: {error_msg}")
                self.status_label.config(text=f"❌ Project '{project_key}' not found", fg="red")
            else:
                self.log_message(f"\n❌ An error occurred with Jira: {e.text}")
                self.status_label.config(text="❌ Jira error occurred", fg="red")
        except Exception as e:
            # Handle any other unexpected errors
            self.log_message(f"\n❌ An unexpected error occurred: {e}")
            self.status_label.config(text="❌ Unexpected error occurred", fg="red")
        finally:
            # Restore standard output and re-enable buttons
            sys.stdout = sys.__stdout__
            self.create_button.config(state="normal", text=f"2️⃣ Create {len(self.parsed_issues)} Tickets", bg="#4CAF50")
            self.preview_button.config(state="normal")
    
    # --- Stdout Redirection ---
    
    def write(self, message):
        """A fake write method to redirect stdout from other modules to the GUI."""
        # Avoid printing empty lines
        if message.strip():
            # Check if this is a success summary line and format it nicely
            if message.strip().startswith("✅") and ":" in message:
                # This is a ticket creation success line - format it with green color
                self.log_message_colored(message.strip(), "green")
            elif message.strip().startswith("🎉") or "Successfully created" in message:
                # This is a major success message
                self.log_message_colored(message.strip(), "dark green")
            elif message.strip().startswith("📍") or message.strip().startswith("🌐"):
                # This is project/URL information
                self.log_message_colored(message.strip(), "blue")
            else:
                # Regular message
                self.log_message(message.strip())

    def log_message_colored(self, message, color="black"):
        """Logs a colored message to the output console."""
        self.output_console.config(state="normal")
        
        # Insert the message with color
        start_pos = self.output_console.index(tk.END)
        self.output_console.insert(tk.END, message + "\n")
        end_pos = self.output_console.index(tk.END)
        
        # Apply color tag
        color_tag = f"color_{color.replace(' ', '_')}"
        self.output_console.tag_add(color_tag, start_pos, end_pos)
        
        # Configure the color tag
        if color == "green":
            self.output_console.tag_config(color_tag, foreground="#2E7D32")
        elif color == "dark green":
            self.output_console.tag_config(color_tag, foreground="#1B5E20", font=("Arial", 9, "bold"))
        elif color == "blue":
            self.output_console.tag_config(color_tag, foreground="#1565C0")
        elif color == "red":
            self.output_console.tag_config(color_tag, foreground="#C62828")
        else:
            self.output_console.tag_config(color_tag, foreground="black")
        
        self.output_console.config(state="disabled")
        self.output_console.see(tk.END)  # Auto-scroll to the bottom

if __name__ == "__main__":
    root = tk.Tk()
    app = JiraApp(root)
    root.mainloop() 