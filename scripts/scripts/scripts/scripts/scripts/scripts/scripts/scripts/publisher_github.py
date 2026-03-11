# scripts/publisher_github.py
import os, glob
from github import Github
from pathlib import Path

def commit_file(local_path, repo_name, commit_message="Auto publish"):
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN required")
    g = Github(token)
    repo = g.get_repo(repo_name)
    rel_path = Path(local_path).as_posix()
    with open(local_path, "r", encoding="utf8") as f:
        content = f.read()
    try:
        existing = repo.get_contents(rel_path)
        repo.update_file(existing.path, commit_message, content, existing.sha, branch="main")
    except Exception:
        repo.create_file(rel_path, commit_message, content, branch="main")

def commit_all():
    repo = os.getenv("GITHUB_REPOSITORY")
    for f in glob.glob("content/posts/*.md"):
        print("Committing", f)
        commit_file(f, repo, f"chore: publish {Path(f).name}")

if __name__ == "__main__":
    commit_all()
