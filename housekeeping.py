import requests
import json
from requests.auth import HTTPBasicAuth

# Artifactory configuration
ARTIFACTORY_URL = "https://your-artifactory-instance/artifactory"
REPO_NAME = "your-docker-repo"
USERNAME = "your-username"
PASSWORD = "your-password"
KEEP_LATEST = 10  # Number of latest images to keep


def list_docker_tags():
    url = f"{ARTIFACTORY_URL}/api/docker/{REPO_NAME}/v2/_catalog"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    if response.status_code == 200:
        repositories = response.json().get("repositories", [])
        for repo in repositories:
            tag_url = f"{ARTIFACTORY_URL}/api/docker/{REPO_NAME}/v2/{repo}/tags/list"
            tag_response = requests.get(tag_url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
            if tag_response.status_code == 200:
                tags = tag_response.json().get("tags", [])
                print(f"Repository: {repo}, Tags: {tags}")
            else:
                print(f"Failed to fetch tags for {repo}: {tag_response.text}")
    else:
        print(f"Failed to list repositories: {response.text}")


def delete_old_images():
    url = f"{ARTIFACTORY_URL}/api/docker/{REPO_NAME}/v2/_catalog"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    if response.status_code == 200:
        repositories = response.json().get("repositories", [])
        for repo in repositories:
            tag_url = f"{ARTIFACTORY_URL}/api/docker/{REPO_NAME}/v2/{repo}/tags/list"
            tag_response = requests.get(tag_url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
            if tag_response.status_code == 200:
                tags = sorted(tag_response.json().get("tags", []))
                if len(tags) > KEEP_LATEST:
                    tags_to_delete = tags[:-KEEP_LATEST]
                    for tag in tags_to_delete:
                        delete_url = f"{ARTIFACTORY_URL}/{REPO_NAME}/{repo}/{tag}"
                        delete_response = requests.delete(delete_url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
                        if delete_response.status_code == 204:
                            print(f"Deleted: {repo}:{tag}")
                        else:
                            print(f"Failed to delete {repo}:{tag}: {delete_response.text}")
            else:
                print(f"Failed to fetch tags for {repo}: {tag_response.text}")
    else:
        print(f"Failed to list repositories: {response.text}")


if __name__ == "__main__":
    print("Listing all docker tags:")
    list_docker_tags()
    print("Deleting old images:")
    delete_old_images()

