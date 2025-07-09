# Jira Configuration Template
# 
# INSTRUCTIONS:
# 1. Copy this file to 'config.py' in the same directory
# 2. Replace the placeholder values below with your actual Jira credentials
# 3. Keep config.py secure and never commit it to version control
#
# To copy this file:
# cp config.template.py config.py

JIRA_CONFIG = {
    # Your Jira server URL (e.g., https://yourcompany.atlassian.net)
    "server": "https://your-jira-server.atlassian.net",
    
    # Your Jira username (usually your email address)
    "username": "your-email@company.com",
    
    # Your Jira API token (generate from: https://id.atlassian.com/manage-profile/security/api-tokens)
    "api_token": "YOUR_JIRA_API_TOKEN_HERE"
}

# OpenAI Configuration for AI-powered document analysis
OPENAI_CONFIG = {
    # Your OpenAI API key (get from: https://platform.openai.com/api-keys)
    "api_key": "YOUR_OPENAI_API_KEY_HERE",
    
    # Model to use (gpt-4o-mini is cost-effective, gpt-4o for better results)
    "model": "gpt-4o-mini",
    
    # Maximum tokens for response
    "max_tokens": 4000,
    
    # Temperature (0.1 = more consistent, 0.7 = more creative)
    "temperature": 0.1
}

# How to get your API token:
# 1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
# 2. Click "Create API token"
# 3. Give it a label (e.g., "Jira Automation Tool")
# 4. Copy the generated token and paste it above
# 5. Save this file as 'config.py' 