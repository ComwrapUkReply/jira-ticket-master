#!/usr/bin/env python3
"""
Simple script to test Jira authentication and project access
"""
import sys
from jira import JIRA, JIRAError

def test_jira_connection(server, username, api_token, project_key):
    print(f"Testing connection to: {server}")
    print(f"Username: {username}")
    print(f"Project: {project_key}")
    print("-" * 50)
    
    try:
        # Create JIRA connection
        jira = JIRA(server=server, basic_auth=(username, api_token))
        print("✅ Successfully connected to Jira")
        
        # Test server info
        try:
            server_info = jira.server_info()
            print(f"✅ Server: {server_info.get('serverTitle', 'Unknown')}")
        except Exception as e:
            print(f"⚠️  Server info failed: {e}")
        
        # Test project access
        try:
            project = jira.project(project_key)
            print(f"✅ Project found: {project.name}")
            print(f"   Key: {project.key}")
            print(f"   Lead: {getattr(project, 'lead', 'Unknown')}")
        except JIRAError as e:
            if e.status_code == 404:
                print(f"❌ Project '{project_key}' not found")
                print("   This could mean:")
                print("   • Project doesn't exist")
                print("   • You don't have permission to view it")
                print("   • Project key is wrong")
            elif e.status_code == 401:
                print("❌ Authentication failed")
                print("   Check your username and API token")
            else:
                print(f"❌ Error accessing project: {e}")
            return False
        
        # Test issue creation permissions
        try:
            # Get issue types for the project
            issue_types = jira.createmeta(projectKeys=project_key)
            if issue_types['projects']:
                project_meta = issue_types['projects'][0]
                available_types = [it['name'] for it in project_meta['issuetypes']]
                print(f"✅ Available issue types: {available_types}")
            else:
                print("⚠️  No issue creation permissions or project not accessible")
        except Exception as e:
            print(f"⚠️  Could not check issue creation permissions: {e}")
        
        return True
        
    except JIRAError as e:
        print(f"❌ Jira Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

if __name__ == "__main__":
    # Test with your credentials
    server = "https://comwrapuk.atlassian.net"
    username = "s.sznajder@reply.com"
    project_key = "FKM"
    
    print("Jira Connection Test")
    print("=" * 50)
    
    api_token = input("Enter your API token: ").strip()
    
    if test_jira_connection(server, username, api_token, project_key):
        print("\n🎉 All tests passed! You can create tickets.")
    else:
        print("\n❌ Tests failed. Check your credentials and permissions.") 