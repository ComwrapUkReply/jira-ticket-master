## Relevant Files

- `create_jira_tickets.py` - Contains the core logic for parsing the Word document and creating Jira tickets. This script also serves as the command-line interface (CLI).
- `jira_ticket_gui.py` - Provides a graphical user interface (GUI) using Tkinter, allowing non-terminal users to run the tool.
- `requirements.txt` - Lists the necessary Python dependencies (`python-docx`, `jira`) for the project.
- `README.md` - Instructions for setting up the environment, installing dependencies, and running both the CLI and GUI applications.

### Notes

- The project should be run within a Python virtual environment to manage dependencies correctly.
- To run the command-line tool: `python create_jira_tickets.py <server_url> <username> <api_token> <project_key>`
- To run the GUI application: `python jira_ticket_gui.py`

## Tasks

- [x] **1.0 Setup Project Environment and Core Dependencies**
  - [x] 1.1 Create a virtual environment using `python3 -m venv venv`.
  - [x] 1.2 Activate the virtual environment: `source venv/bin/activate`.
  - [x] 1.3 Install the `python-docx` library for reading `.docx` files.
  - [x] 1.4 Install the `jira` library for interacting with the Jira API.
  - [x] 1.5 Generate a `requirements.txt` file using `pip freeze > requirements.txt`.

- [x] **2.0 Develop Word Document Parsing Logic**
  - [x] 2.1 Implement a function `get_text(filename)` that opens a `.docx` file and returns its complete text content.
  - [x] 2.2 Implement a function `parse_issues(text)` that splits the text into blocks based on double newlines.
  - [x] 2.3 In `parse_issues`, iterate through text blocks and extract the first line as the issue's "title".
  - [x] 2.4 Extract the remaining lines of the block as the issue's "description".
  - [x] 2.5 Ensure the function returns a list of dictionaries, with each dictionary representing an issue (e.g., `{'title': '...', 'description': '...'}`).

- [x] **3.0 Implement Jira Integration and Ticket Creation**
  - [x] 3.1 Create a function `create_jira_tickets` that takes Jira connection details and the list of parsed issues as arguments.
  - [x] 3.2 Authenticate with the Jira API using the provided server URL, username, and API token.
  - [x] 3.3 Loop through the list of issues and, for each one, create a new Jira issue.
  - [x] 3.4 Map the issue's "title" to the Jira 'Summary' field.
  - [x] 3.5 Map the issue's "description" to the Jira 'Description' field.
  - [x] 3.6 Set the `issuetype` to 'Task' and specify the `project_key`.
  - [x] 3.7 Print the key of each newly created ticket (e.g., "Successfully created issue: PROJ-123").

- [x] **4.0 Build the Command-Line Interface (CLI)**
  - [x] 4.1 In `create_jira_tickets.py`, implement the main execution block (`if __name__ == "__main__":`).
  - [x] 4.2 Use `sys.argv` to capture the four required command-line arguments.
  - [x] 4.3 Add a check to ensure the correct number of arguments is provided; if not, print a usage guide and exit.
  - [x] 4.4 Pass the arguments to the functions that handle document parsing and ticket creation.

- [x] **5.0 Develop the Graphical User Interface (GUI)**
  - [x] 5.1 In `jira_ticket_gui.py`, build the main window using `tkinter`.
  - [x] 5.2 Add input fields for the Jira server, username, API token, and project key.
  - [x] 5.3 Add a "Browse" button that allows users to select the `.docx` file.
  - [x] 5.4 Implement a "Create Tickets" button that triggers the main logic.
  - [x] 5.5 Add a text area to log progress and display success or error messages from the backend functions.
  - [x] 5.6 Run the ticket creation process in a separate thread to keep the GUI responsive.

- [x] **6.0 Finalize Documentation and Error Handling**
  - [x] 6.1 Add clear, user-friendly error handling for common issues (e.g., wrong file path, invalid credentials, network problems).
  - [x] 6.2 Write a comprehensive `README.md` file detailing the project's purpose, setup instructions, and usage for both the CLI and GUI.
  - [x] 6.3 Add comments to the code to clarify key functions and logic. 