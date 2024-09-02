import os
import requests
import json    
        
def format_jira_table():
    tests_ran = os.getenv('TOTAL_TESTS')
    tests_passed = os.getenv('PASSED_TESTS')
    tests_skipped = os.getenv('SKIPPED_TESTS')
    tests_failed = os.getenv('FAILED_TESTS')

    jira_table = f"|Tests |Passed ✅ |Skipped ⏭️ |Failed ❌ ||\n|Test Report |{tests_ran} ran |{tests_passed} passed |{tests_skipped} skipped |{tests_failed} failed |"
    
    return jira_table
    
def extract_keys_from_branch():
    branch_name = os.getenv('ISSUE')

    if branch_name is None:
        raise ValueError("ISSUE environment variable is not set.")
    
    if '/' not in branch_name or '-' not in branch_name:
        raise ValueError("Invalid branch name format. Expected format 'prefix/PROJECT-123'.")
    
    issue_key = branch_name.split('/')[1]
    project_key = issue_key.split('-')[0]

    os.environ["PROJECT_KEY"] = project_key
    os.environ["ISSUE_KEY"] = issue_key

    with open(os.getenv("GITHUB_ENV"), "a") as env_file:
        env_file.write(f"PROJECT_KEY={project_key}\n")
        env_file.write(f"ISSUE_KEY={issue_key}\n")
  
def comment_jira_table():
    extract_keys_from_branch()

    jira_endpoint = os.getenv('JIRA_ENDPOINT')
    jira_token = os.getenv('JIRA_AUTHORIZATION')
    author = os.getenv('AUTHOR')
    repository = os.getenv('REPOSITORY')
    issue_key = os.getenv('ISSUE_KEY')
    
    jira_table = format_jira_table()

    url = f"{jira_endpoint}/issue/{issue_key}/comment"
    
    headers = {
        "Authorization": f"Bearer {jira_token}",
        "Content-Type": "application/json"
    }

    COMMENT_BODY = f"Triggered by {author} for [repository|https://github.com/{repository}/actions].\n\n | {jira_table}"

    data = {
        "body": COMMENT_BODY,
        "public": True
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()

def create_issue(issue_summary):
    extract_keys_from_branch()
    
    jira_endpoint = os.getenv('JIRA_ENDPOINT')
    jira_token = os.getenv('JIRA_AUTHORIZATION')
    project_key = os.getenv('PROJECT_KEY')
    repository = os.getenv('REPOSITORY')
    
    url = f"{jira_endpoint}/issue"
    
    headers = {
        "Authorization": f"Bearer {jira_token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "fields": {
            "project": {
                "key": f"{project_key}"
            },
            "summary": f"{issue_summary}",
            "description": f"This bug was automatically created on Pull Request for [repository|https://github.com/{repository}]",
            "issuetype": {
                "name": "Story"
            }
        }
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()
    
def create_bug(bug_summary):
    jira_endpoint = os.getenv('JIRA_ENDPOINT')
    jira_token = os.getenv('JIRA_AUTHORIZATION')
    project_key = os.getenv('PROJECT_KEY')
    author = os.getenv('AUTHOR')
    repository = os.getenv('REPOSITORY')

    url = f"{jira_endpoint}/issue"
    
    headers = {
        "Authorization": f"Bearer {jira_token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "fields": {
            "project": {
                "key": f"{project_key}"
            },
            "summary": f"{bug_summary}",
            "description": f"This bug was automatically created because automated test triggered by {author} failed on [repository|https://github.com/{repository}/actions]",
            "issuetype": {
                "name": "Bug"
            }
        }
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()
    
    bug_key = response.json()['key'] # TEST THIS
    
    with open(os.getenv("GITHUB_ENV"), "a") as env_file:
        env_file.write(f"BUG_KEY={bug_key}\n") # TEST

def change_bug_priority():
    jira_endpoint = os.getenv('JIRA_ENDPOINT')
    jira_token = os.getenv('JIRA_AUTHORIZATION')
    bug_key = os.getenv('BUG_KEY')
    priority = "Blocker"

    url = f"{jira_endpoint}/issue/{bug_key}"
    
    headers = {
        "Authorization": f"Bearer {jira_token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "fields": {
            "priority": {
                "name": f"{priority}"
            }
        }
    }
    
    response = requests.put(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()

def assign_bug_to_issue():
    jira_endpoint = os.getenv('JIRA_ENDPOINT')
    jira_token = os.getenv('JIRA_AUTHORIZATION')
    bug_key = os.getenv('BUG_KEY')
    issue_key = os.getenv('ISSUE_KEY')
    
    url = f"{jira_endpoint}/issueLink"
    
    headers = {
        "Authorization": f"Bearer {jira_token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "type": {
            "name": "Blocks"
        },
        "inwardIssue": {
            "key": f"{bug_key}"
        },
        "outwardIssue": {
            "key": f"{issue_key}"
        }
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()

def get_transition_options(transition_name):
    jira_endpoint = os.getenv('JIRA_ENDPOINT')
    jira_token = os.getenv('JIRA_AUTHORIZATION')
    issue_key = os.getenv('ISSUE_KEY')

    url = f"{jira_endpoint}/issue/{issue_key}/transitions"
    
    headers = {
        "Authorization": f"Bearer {jira_token}",
        "Accept": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    transitions = response.json()
    
    for transition in transitions['transitions']:
        if transition['name'] == transition_name:
            transition_id = transition['id']
            with open(os.getenv("GITHUB_ENV"), "a") as env_file:
                env_file.write(f"TRANSITION_ID={transition_id}\n") # TEST
        else:
            raise ValueError("Transition name not found.")

def transition_issue():
    jira_endpoint = os.getenv('JIRA_ENDPOINT')
    jira_token = os.getenv('JIRA_AUTHORIZATION')
    issue_key = os.getenv('ISSUE_KEY')
    transition_id = os.getenv('TRANSITION_ID')

    url = f"{jira_endpoint}/issue/{issue_key}/transitions"
    
    headers = {
        "Authorization": f"Bearer {jira_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    data = {
        "transition": {
            "id": f"{transition_id}"
        }
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()
    
def main():
    comment_jira_table()

if __name__ == "__main__":
    main()
