# Automated Jira Ticket Creator

This project provides a simple tool to automate the creation of Jira tickets from a formatted Microsoft Word document (`.docx`).

It includes both a command-line interface (CLI) for technical users and a simple graphical user interface (GUI) for non-technical team members.

## Features

-   **AI-Powered Document Analysis** - Uses OpenAI GPT to intelligently extract tasks from any document format
-   **Enhanced Extraction** - Extracts images and structured content from Word documents
-   **Image Attachment** - Automatically attaches images from Word documents to Jira tickets
-   **Status Control** - Choose initial status for created tickets (To Do, In Progress, Done, etc.)
-   **Basic Text Parsing** - Simple text extraction for basic use cases
-   **Smart Task Recognition** - Identifies numbered lists, bullet points, and action items
-   **Automatic Project Fetching** - Loads available Jira projects automatically
-   **Epic Linking** - Automatically links tickets to selected epics
-   **Multiple Issue Types** - Supports Task, Story, Bug, and Epic creation
-   **Credential Storage** - Securely stores Jira credentials for convenience
-   **Dual Interface** - Both GUI and CLI options available

## Setup and Installation

### 1. Prerequisites

-   Python 3
-   A Jira account with API token permissions

### 2. Clone the Repository

Clone this repository to your local machine:

`git clone <repository-url>`
`cd <repository-directory>`

### 3. Create a Virtual Environment

It is highly recommended to use a virtual environment to manage dependencies.

`python3 -m venv venv`

### 4. Activate the Environment

-   **On macOS/Linux:** `source venv/bin/activate`
-   **On Windows:** `.\\venv\\Scripts\\activate`

### 5. Install Dependencies

Install the required Python libraries from the `requirements.txt` file.

`pip install -r requirements.txt`

### 6. Configure Credentials (Optional but Recommended)

To avoid entering your Jira credentials every time:

1. **Copy the configuration template:**
   `cp config.template.py config.py`

2. **Edit the config.py file:**
   - Replace `YOUR_API_TOKEN_HERE` with your actual Jira API token
   - Update the server URL and username if different
   - Save the file

3. **Generate a Jira API Token:**
   - Go to https://id.atlassian.com/manage-profile/security/api-tokens
   - Click "Create API token"
   - Give it a label (e.g., "Jira Automation Tool")
   - Copy the generated token and paste it in `config.py`

4. **Configure OpenAI API (Optional - for AI-powered analysis):**
   - Go to https://platform.openai.com/api-keys
   - Click "Create new secret key"
   - Copy the API key and add it to `config.py` under `OPENAI_CONFIG["api_key"]`
   - This enables AI-powered document analysis for better task extraction

**Note:** The `config.py` file is automatically ignored by git to keep your credentials secure.

## How to Use

You can create Jira tickets using either the Graphical User Interface (GUI) or the Command-Line Interface (CLI).

### Option 1: Using the Graphical User Interface (GUI)

The GUI is the easiest way to use this tool, especially for non-technical users.

1.  **Launch the application:**
    `python3 jira_ticket_gui.py`

2.  **Auto-populated fields:**
    -   If you've configured `config.py`, your Jira credentials will be automatically filled in
    -   The application will automatically fetch available projects on startup

3.  **Fill in any missing details:**
    -   **Jira Server URL:** Your Jira instance URL (auto-filled if configured)
    -   **Jira Username:** Your email address (auto-filled if configured)
    -   **API Token:** Your Jira API token (auto-filled if configured)
    -   **Project Key:** Select from the dropdown (auto-populated if credentials are configured)
    -   **Issue Type:** Select the type of issues to create (Task, Story, Bug, or Epic)
    -   **Epic:** Optionally select an epic to link the tickets to

4.  **Fetch Projects (if needed):**
    -   If projects aren't auto-loaded, click **🔄 Fetch Projects** to load available projects
    -   Select your target project from the dropdown

5.  **Fetch Epics (Optional):**
    -   After selecting a project, click the **🔄 Fetch Epics** button to load available epics
    -   Select an epic from the dropdown if you want to link all created tickets to that epic

6.  **Choose Initial Status:**
    -   Select the initial status for created tickets from the **Initial Status** dropdown
    -   Click **🔄 Fetch Statuses** to load project-specific statuses from Jira
    -   Common statuses include: To Do, In Progress, Done, Backlog, etc.

7.  **Choose Analysis Mode:**
    -   **AI-Powered**: Uses OpenAI to intelligently extract tasks from any document format (requires OpenAI API key)
    -   **Enhanced**: Extracts text and images from Word documents with improved parsing
    -   **Basic**: Simple text parsing for basic use cases

8.  **Preview Tickets:**
    -   Click **1️⃣ Preview Tickets** to see what tickets will be created from your document
    -   Review the preview in the console to ensure the parsing is correct
    -   AI-Powered mode will show priority, complexity, and category analysis

9.  **Select the Word Document:**
    -   Click the **Browse for Word Doc** button and choose the `.docx` file containing the issues

10. **Create Tickets:**
    -   Click the **2️⃣ Create in Jira** button. The progress will be displayed in the output console at the bottom

### Option 2: Using the Command-Line Interface (CLI)

The CLI is ideal for technical users or for integrating into other scripts.

1.  **Run the script with the following command:**

    `python3 create_jira_tickets.py <server_url> <username> <api_token> <project_key>`

2.  **Replace the placeholders:**
    -   `<server_url>`: Your Jira instance URL.
    -   `<username>`: Your Jira email.
    -   `<api_token>`: Your Jira API token.
    -   `<project_key>`: The target Jira project key.

    **Example:**
    `python3 create_jira_tickets.py https://example.atlassian.net user@example.com YOUR_API_TOKEN MYPROJ`

## Word Document Formatting

For the script to parse issues correctly, your `.docx` file must follow a simple format:

-   Each issue must be separated by at least one empty line (a double newline).
-   The first line of an issue block will become the **ticket title (Summary)**.
-   All subsequent lines in that block will become the **ticket Description**.

### Example:

```
This is the title for the first issue.
This is the first line of the description.
This is the second line of the description.

This is the title for the second issue.
This description only has one line.
``` 

## AI-Powered Document Analysis

The AI-powered mode uses OpenAI's GPT models to intelligently analyze your documents and extract actionable tasks. This mode offers several advantages:

### **Capabilities:**
- **Smart Task Recognition**: Identifies tasks from various formats (numbered lists, bullet points, paragraphs)
- **Context Understanding**: Understands the context and relationships between tasks
- **Automatic Categorization**: Classifies tasks as Bug, Feature, Improvement, or Task
- **Priority Assessment**: Analyzes and assigns priority levels (High, Medium, Low)
- **Complexity Estimation**: Estimates task complexity (Simple, Medium, Complex)
- **Flexible Format Support**: Works with various document structures and formats

### **Supported Document Formats:**
- Numbered lists (1., 2., 3., etc.)
- Bullet points with action items
- Paragraph descriptions of issues
- Mixed formats within the same document
- Tables with task information
- Unstructured text with embedded tasks

### **AI Analysis Output:**
Each extracted task includes:
- **Clear Title**: Suitable for Jira ticket summary
- **Detailed Description**: Context and requirements
- **Priority Level**: High, Medium, or Low
- **Complexity**: Simple, Medium, or Complex
- **Category**: Bug, Feature, Improvement, or Task

### **Cost Considerations:**
- Uses OpenAI API (small cost per document)
- Recommended model: `gpt-4o-mini` (cost-effective)
- Upgrade to `gpt-4o` for better accuracy if needed
- Typical cost: $0.01-0.05 per document analysis

## Document Format Requirements

### **For AI-Powered Analysis:**
No specific format required! The AI can understand various document structures including:
- Mixed numbered and bulleted lists
- Paragraph descriptions
- Tables with task information
- Unstructured text with embedded action items

### **For Enhanced/Basic Analysis:** 

For the script to parse issues correctly, your `.docx` file must follow a simple format:

-   Each issue must be separated by at least one empty line (a double newline).
-   The first line of an issue block will become the **ticket title (Summary)**.
-   All subsequent lines in that block will become the **ticket Description**.

### Example:

```
This is the title for the first issue.
This is the first line of the description.
This is the second line of the description.

This is the title for the second issue.
This description only has one line.
``` 

## Image Attachment Functionality

The tool automatically extracts and attaches images from Word documents to Jira tickets, making your tickets more comprehensive and visual.

### **How It Works:**

#### **Enhanced Mode:**
- Images are extracted and linked to specific content sections
- Each image is associated with the text content it appears near
- Images are automatically attached to the relevant Jira tickets

#### **AI-Powered Mode:**
- All images are extracted from the document
- Images are intelligently distributed across AI-analyzed tasks
- Each task receives a fair share of the available images
- Images are automatically attached to Jira tickets during creation

### **Image Processing:**
- **Supported Formats**: PNG, JPEG, GIF (automatically detected)
- **Storage**: Images are saved to `extracted_images/` folder
- **Naming**: Sequential naming (image_1.png, image_2.png, etc.)
- **Attachment**: Automatically uploaded to Jira with original filenames

### **Example Output:**
```
📸 Extracted image: image_1.png (316919 bytes)
📸 Extracted image: image_2.png (49820 bytes)
📸 Extracted image: image_3.png (625032 bytes)

Task 1: Fix Duplicate Arrows (2 images attached)
Task 2: Optimize Image Quality (1 image attached)
Task 3: Improve Mobile Layout (1 image attached)
```

### **Benefits:**
- **Visual Context**: Images provide visual context for issues
- **Better Communication**: Team members can see exactly what needs fixing
- **Reduced Back-and-forth**: No need to ask "which button?" or "where exactly?"
- **Automatic Process**: No manual image handling required

## Status Control Functionality

The tool allows you to control the initial status of created Jira tickets, giving you flexibility in your workflow management.

### **How It Works:**

#### **Default Statuses:**
- **To Do**: Default status for new tickets
- **In Progress**: For tickets ready to be worked on
- **Done**: For completed items (useful for documentation)
- **Backlog**: For future planning

#### **Project-Specific Statuses:**
- Click **🔄 Fetch Statuses** to load all available statuses from your Jira instance
- The tool retrieves all statuses configured in your Jira system
- Statuses are project-independent and work across all projects

### **Status Examples from Your System:**
Based on your Jira configuration, available statuses include:
- **Development**: To Do, In Progress, Done, In Dev, Dev Review
- **Testing**: Testing, QA, UAT, Tested
- **Planning**: Backlog, Selected for Development, Ready for Development
- **Review**: Code Review, Dev Review, UX/UI Complete
- **Deployment**: Ready for Rollout, Deployed on Stage, Ready for Release

### **Benefits:**
- **Workflow Control**: Start tickets in the right status for your process
- **Team Coordination**: Clearly indicate ticket readiness
- **Process Automation**: Skip manual status updates after creation
- **Flexibility**: Works with any Jira workflow configuration

### **Usage Tips:**
- Use **"Backlog"** for future planning sessions
- Use **"To Do"** for immediate work items
- Use **"In Progress"** for tickets being actively worked on
- Use **"Done"** for completed documentation or reference tickets

## Enhanced Success Messaging

The tool provides comprehensive feedback when tickets are successfully created, showing detailed information about each ticket.

### **Success Message Features:**

#### **Individual Ticket Details:**
Each created ticket shows:
- **Ticket Number**: Direct Jira ticket key (e.g., FKM-123)
- **Title**: Truncated title for easy identification
- **Type**: Issue type (Task, Story, Bug, Epic)
- **Status**: Final status after creation
- **Epic Link**: Connected epic (if configured)
- **Image Count**: Number of attached images
- **Direct URL**: Clickable link to the ticket

#### **Example Success Output:**
```
🎉 Successfully created 3 tickets:
================================================================================

✅ FKM-123: Fix Duplicate Arrows on HC Website
   📋 Type: Task
   🔄 Status: To Do
   🔗 Epic: FKM-100
   📸 Images: 2 attached
   🌐 URL: https://comwrapuk.atlassian.net/browse/FKM-123

✅ FKM-124: Optimize Image Sizes on HC Website
   📋 Type: Task
   🔄 Status: In Progress
   📸 Images: 1 attached
   🌐 URL: https://comwrapuk.atlassian.net/browse/FKM-124

✅ FKM-125: Improve Mobile Layout
   📋 Type: Task
   🔄 Status: To Do
   🌐 URL: https://comwrapuk.atlassian.net/browse/FKM-125

📍 All tickets created in project 'FKM'
🌐 View project: https://comwrapuk.atlassian.net/projects/FKM
```

#### **GUI Color Coding:**
- **Green**: Successful ticket creation details
- **Dark Green**: Major success messages and summaries
- **Blue**: Project and URL information
- **Red**: Error messages and warnings

### **Benefits:**
- **Immediate Verification**: See exactly what was created
- **Easy Navigation**: Direct links to tickets and project
- **Complete Overview**: All ticket details in one place
- **Progress Tracking**: Clear status and epic associations 