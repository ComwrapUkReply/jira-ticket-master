#!/usr/bin/env python3
"""
List all Jira projects the user has access to
"""
from jira import JIRA, JIRAError

def list_accessible_projects(server, username, api_token):
    print(f"Connecting to: {server}")
    print(f"Username: {username}")
    print("-" * 50)
    
    try:
        jira = JIRA(server=server, basic_auth=(username, api_token))
        print("✅ Successfully connected to Jira")
        
        # Get all projects the user can see
        projects = jira.projects()
        
        if projects:
            print(f"\n📁 Found {len(projects)} accessible projects:")
            print("-" * 50)
            
            for project in projects:
                print(f"🔹 {project.key} - {project.name}")
                try:
                    # Test if we can create issues in this project
                    issue_types = jira.createmeta(projectKeys=project.key)
                    if issue_types['projects']:
                        available_types = [it['name'] for it in issue_types['projects'][0]['issuetypes']]
                        print(f"   ✅ Can create: {', '.join(available_types)}")
                    else:
                        print(f"   ❌ Cannot create issues")
                except:
                    print(f"   ❓ Unknown permissions")
                print()
        else:
            print("❌ No accessible projects found")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    server = "https://comwrapuk.atlassian.net"
    username = "s.sznajder@reply.com"
    
    print("Jira Projects List")
    print("=" * 50)
    
    api_token = input("Enter your API token: ").strip()
    list_accessible_projects(server, username, api_token) 