import os
from github import Github


def create_issue(title, body):
    try:
        github_client = Github(os.getenv("GITHUB_ACCESS_TOKEN"))
        repo = github_client.get_repo(os.getenv("GITHUB_REPO"))
        label = repo.get_label("bug")

        repo.create_issue(title=title, body=body, labels=[label])
    except Exception as e:
        print("Error when creating GitHub issue (check your token): {}".format(e))
