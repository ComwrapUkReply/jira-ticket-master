import docx
import sys
from jira import JIRA, JIRAError

# Import enhanced extraction functions
try:
    from extract_word_content import get_enhanced_text_with_images, parse_enhanced_issues
    ENHANCED_EXTRACTION_AVAILABLE = True
except ImportError:
    ENHANCED_EXTRACTION_AVAILABLE = False

def get_text(filename):
    """
    Extracts all text from a .docx file.
    
    Args:
        filename (str): The path to the Word document.
        
    Returns:
        str: The full text content of the document, with paragraphs joined by newlines.
    """
    doc = docx.Document(filename)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\\n'.join(full_text)

def parse_issues(text):
    """
    Parses a block of text into a list of structured issues.
    
    Issues are expected to be separated by double newlines. The first line
    of each issue block is treated as the title, and the rest as the description.
    
    Args:
        text (str): The text content from the Word document.
        
    Returns:
        list: A list of dictionaries, where each dictionary represents an issue
              (e.g., {'title': '...', 'description': '...'}).
    """
    issues = []
    # Split by two or more newlines to handle variance in document formatting
    blocks = [b.strip() for b in text.split('\\n\\n') if b.strip()]
    
    for block in blocks:
        lines = [line.strip() for line in block.split('\\n') if line.strip()]
        if not lines:
            continue
        
        title = lines[0]
        description = '\\n'.join(lines[1:])
        
        if not description and len(lines) > 1:
            description = lines[-1]

        issues.append({"title": title, "description": description})
            
    return issues

def get_enhanced_issues(filename):
    """
    Get issues using enhanced extraction (with images) if available, 
    otherwise fall back to basic text extraction.
    """
    if ENHANCED_EXTRACTION_AVAILABLE:
        try:
            print("🔍 Using enhanced extraction (with images)...")
            content_blocks, extracted_images = get_enhanced_text_with_images(filename)
            issues = parse_enhanced_issues(content_blocks, extracted_images)
            print(f"📸 Found {len(extracted_images)} images in document")
            return issues
        except Exception as e:
            print(f"⚠️  Enhanced extraction failed: {e}")
            print("🔄 Falling back to basic text extraction...")
    
    # Fallback to basic extraction
    print("📄 Using basic text extraction...")
    text = get_text(filename)
    return parse_issues(text)

def create_jira_tickets_with_type(server, username, api_token, project_key, issues, issue_type="Task", epic_key=None, status_name=None):
    """
    Connects to Jira and creates tickets based on a list of parsed issues with specified issue type.
    
    Args:
        server (str): The URL of the Jira instance.
        username (str): The user's email for Jira authentication.
        api_token (str): The user's Jira API token.
        project_key (str): The key of the target Jira project.
        issues (list): A list of issue dictionaries to be created.
        issue_type (str): The type of issue to create (Task, Story, Bug, Epic).
        epic_key (str, optional): The key of the epic to assign tickets to.
        status_name (str, optional): The name of the status to set for created tickets.
    """
    try:
        print("🔍 Debugging connection details:")
        print(f"   Server URL: {server}")
        print(f"   Username: {username}")
        print(f"   Project Key: {project_key}")
        print(f"   Issue Type: {issue_type}")
        print("")
        
        # Validate server URL format
        if not server.startswith(('http://', 'https://')):
            raise ValueError("Jira Server URL must start with 'http://' or 'https://'")
        
        # Remove trailing slash if present
        server = server.rstrip('/')
        print(f"📍 Cleaned server URL: {server}")
        
        print("🔗 Attempting to connect to Jira...")
        
        # Try to establish a connection to the Jira server with more detailed error handling
        try:
            jira = JIRA(server=server, basic_auth=(username, api_token))
            print("✅ JIRA object created successfully")
        except Exception as jira_init_error:
            print(f"❌ Failed to create JIRA object: {jira_init_error}")
            if "Expecting value" in str(jira_init_error):
                print("\\n🔍 This error suggests the server URL is not returning valid JSON.")
                print("Common causes:")
                print(f"• '{server}' is not a valid Jira server")
                print("• The URL points to a login page instead of the API")
                print("• Network/firewall blocking the connection")
                print("• SSL certificate issues")
                print("\\n💡 Try these URLs instead:")
                if ".atlassian.net" in server:
                    print(f"• {server}")
                    print(f"• {server.replace('www.', '')}")
                else:
                    print(f"• {server}/jira")
                    print(f"• {server}:8080")
                return []
            raise jira_init_error
        
        # Test the connection by getting server info
        print("🧪 Testing connection with server info...")
        try:
            server_info = jira.server_info()
            print(f"✅ Connected to Jira server: {server_info.get('serverTitle', 'Unknown')}")
            print(f"   Version: {server_info.get('version', 'Unknown')}")
        except Exception as server_info_error:
            print(f"❌ Failed to get server info: {server_info_error}")
            if "Expecting value" in str(server_info_error):
                print("\\n🔍 The connection was made but server didn't return valid JSON.")
                print("This might mean:")
                print(f"• '{server}' redirects to a login page")
                print("• The API endpoint is different")
                print("• Authentication is required for server info")
                print("\\n💡 Let's try to continue anyway...")
            else:
                raise server_info_error
        
        print(f"\\n🎫 Creating {len(issues)} tickets in project '{project_key}'...")
        
        # First, let's get available issue types and statuses for better error handling
        print("🔍 Checking project access...")
        try:
            project = jira.project(project_key)
            print(f"✅ Project found: {project.name}")
        except Exception as project_error:
            print(f"❌ Cannot access project '{project_key}': {project_error}")
            if "404" in str(project_error) or "does not exist" in str(project_error).lower():
                print(f"\\n💡 Project '{project_key}' was not found. Common issues:")
                print("• Project key is case-sensitive (try uppercase)")
                print("• You don't have permission to view this project")
                print("• Project doesn't exist")
                return []
            else:
                print("\\n💡 Continuing anyway - project might exist but we can't verify...")
        
        created_tickets = []
        ticket_details = []  # Store detailed information about each ticket
        
        for i, issue in enumerate(issues, 1):
            try:
                issue_dict = {
                    'project': {'key': project_key},
                    'summary': issue['title'],
                    'description': issue['description'],
                    'issuetype': {'name': issue_type},
                }
                
                # Add epic link if specified and issue type is not Epic
                epic_linked = False
                if epic_key and issue_type.lower() != 'epic':
                    try:
                        # Different Jira instances use different field names for epic links
                        # Try the most common ones
                        issue_dict['parent'] = {'key': epic_key}  # For newer Jira instances
                        epic_linked = True
                        print(f"🔗 Linking to epic: {epic_key}")
                    except Exception as epic_error:
                        print(f"⚠️  Could not link to epic {epic_key}: {epic_error}")
                        # Continue creating the ticket without epic link
                
                print(f"\n🔨 Creating ticket {i}/{len(issues)}: {issue['title'][:50]}...")
                new_issue = jira.create_issue(fields=issue_dict)
                
                # Initialize ticket details
                ticket_info = {
                    'key': new_issue.key,
                    'title': issue['title'],
                    'type': issue_type,
                    'epic': epic_key if epic_linked else None,
                    'status': None,
                    'images': 0,
                    'url': f"{server}/browse/{new_issue.key}"
                }
                
                print(f"✅ Issue created: {new_issue.key}")
                
                # Attach images if available
                if 'images' in issue and issue['images']:
                    print(f"📸 Attaching {len(issue['images'])} images to {new_issue.key}...")
                    images_attached = 0
                    for img in issue['images']:
                        try:
                            # Attach image to the ticket
                            with open(img['path'], 'rb') as img_file:
                                attachment = jira.add_attachment(
                                    issue=new_issue,
                                    attachment=img_file,
                                    filename=img['filename']
                                )
                                print(f"   ✅ Attached: {img['filename']}")
                                images_attached += 1
                        except Exception as img_error:
                            print(f"   ❌ Failed to attach {img['filename']}: {img_error}")
                    
                    ticket_info['images'] = images_attached
                
                # Try to set the status if specified
                final_status = "Default"
                if status_name:
                    try:
                        # Get available transitions for this issue
                        transitions = jira.transitions(new_issue)
                        print(f"🔄 Available transitions: {[t['name'] for t in transitions]}")
                        
                        # Look for the specified status
                        target_transition = None
                        for transition in transitions:
                            if transition['name'].lower() == status_name.lower():
                                target_transition = transition['id']
                                print(f"🎯 Found target status transition: {transition['name']}")
                                break
                        
                        if target_transition:
                            jira.transition_issue(new_issue, target_transition)
                            print(f"✅ Issue {new_issue.key} moved to '{status_name}' status")
                            final_status = status_name
                        else:
                            print(f"⚠️  Status '{status_name}' not available for {new_issue.key}")
                            final_status = "Default (To Do)"
                            
                    except Exception as status_error:
                        print(f"⚠️  Issue {new_issue.key} created but couldn't set status: {status_error}")
                        final_status = "Default (To Do)"
                
                # Try to set the status to "To Do" explicitly (fallback)
                elif not status_name:
                    try:
                        # Get available transitions for this issue
                        transitions = jira.transitions(new_issue)
                        print(f"🔄 Available transitions: {[t['name'] for t in transitions]}")
                        
                        # Look for "To Do" status or similar
                        todo_transition = None
                        for transition in transitions:
                            transition_name = transition['name'].lower()
                            if any(keyword in transition_name for keyword in ['to do', 'todo', 'open', 'new']):
                                todo_transition = transition['id']
                                print(f"🎯 Found 'To Do' transition: {transition['name']}")
                                break
                        
                        if todo_transition:
                            jira.transition_issue(new_issue, todo_transition)
                            print(f"✅ Issue {new_issue.key} moved to 'To Do' status")
                            final_status = "To Do"
                        else:
                            print(f"ℹ️  Issue {new_issue.key} remains in default status")
                            final_status = "Default"
                            
                    except Exception as transition_error:
                        # If we can't set the status, at least the ticket was created
                        print(f"⚠️  Issue {new_issue.key} created but couldn't change status: {transition_error}")
                        final_status = "Default"
                
                ticket_info['status'] = final_status
                created_tickets.append(new_issue.key)
                ticket_details.append(ticket_info)
                
            except Exception as create_error:
                print(f"❌ Failed to create ticket {i}: {issue['title'][:50]}...")
                print(f"   Error: {create_error}")
                continue
        
        if created_tickets:
            print(f"\n🎉 Successfully created {len(created_tickets)} tickets:")
            print("=" * 80)
            
            for ticket in ticket_details:
                print(f"\n✅ {ticket['key']}: {ticket['title'][:60]}{'...' if len(ticket['title']) > 60 else ''}")
                print(f"   📋 Type: {ticket['type']}")
                print(f"   🔄 Status: {ticket['status']}")
                
                if ticket['epic']:
                    print(f"   🔗 Epic: {ticket['epic']}")
                
                if ticket['images'] > 0:
                    print(f"   📸 Images: {ticket['images']} attached")
                
                print(f"   🌐 URL: {ticket['url']}")
            
            print(f"\n📍 All tickets created in project '{project_key}'")
            print(f"🌐 View project: {server}/projects/{project_key}")
        else:
            print("\n❌ No tickets were created successfully.")
        
        return created_tickets

    except ValueError as e:
        print(f"\\n❌ Validation Error: {e}")
        return []
    except ConnectionError as e:
        print(f"\\n❌ Connection Error: {e}")
        return []
    except JIRAError as e:
        # Handle specific Jira-related errors for more helpful messages
        print(f"\\n❌ Jira Error (Status {e.status_code}):")
        if e.status_code == 401:
            print("Authentication failed. Please check:")
            print("• Username is your EMAIL address")
            print("• API token is correct (not your password)")
            print("• API token has proper permissions")
        elif e.status_code == 404:
            if "project" in str(e).lower():
                print(f"Project '{project_key}' not found. Please check:")
                print("• Project key is correct and case-sensitive")
                print("• You have access to this project")
                print("• Project exists")
            else:
                print(f"Resource not found. Check your Jira server URL: {server}")
        elif e.status_code == 403:
            print(f"Access denied. You don't have permission to:")
            print(f"• Create issues in project '{project_key}'")
            print(f"• Access the Jira server")
        else:
            print(f"Jira API error: {e.text}")
        return []
    except Exception as e:
        # Catch any other unexpected errors with more specific messages
        error_msg = str(e)
        print(f"\\n❌ Unexpected Error: {error_msg}")
        
        if "Expecting value" in error_msg:
            print("\\n🔍 JSON parsing error - this usually means:")
            print(f"• '{server}' is not a valid Jira API endpoint")
            print("• The server returned HTML instead of JSON (login page?)")
            print("• Network/proxy issues")
            print("• SSL/certificate problems")
            print("\\n💡 Troubleshooting steps:")
            print(f"1. Open '{server}' in your browser - does it show Jira?")
            print(f"2. Try '{server}/rest/api/2/serverInfo' - does it show JSON?")
            print("3. Check if you need VPN or special network access")
        elif "Connection" in error_msg or "timeout" in error_msg.lower():
            print(f"\\n🔍 Network connection failed:")
            print("• Check your internet connection")
            print("• Verify the server URL is correct")
            print("• Check if VPN is required")
            print("• Verify firewall/proxy settings")
        
        return []

def create_jira_tickets(server, username, api_token, project_key, issues):
    """
    Wrapper function for backward compatibility - creates tickets with default 'Task' type.
    """
    return create_jira_tickets_with_type(server, username, api_token, project_key, issues, "Task")

if __name__ == "__main__":
    # This block runs when the script is executed directly from the command line
    if len(sys.argv) != 5:
        print("Usage: python create_jira_tickets.py <server_url> <username> <api_token> <project_key>")
        sys.exit(1)

    # Capture credentials and project info from command-line arguments
    server_url = sys.argv[1]
    username = sys.argv[2]
    api_token = sys.argv[3]
    project_key = sys.argv[4]

    try:
        # Read the document and create the tickets
        doc_text = get_text('Changes to the HC website AT.docx')
        issues = parse_issues(doc_text)
        
        if not issues:
            print("No issues found in the document. Please check the file content and formatting.")
            sys.exit(0)
            
        create_jira_tickets(server_url, username, api_token, project_key, issues)
        
    except FileNotFoundError:
        print(f"Error: The file 'Changes to the HC website AT.docx' was not found.")
        sys.exit(1) 