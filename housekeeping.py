import requests
import json
import os
import argparse
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta

# Get configuration from environment variables or command-line arguments
def get_config():
    parser = argparse.ArgumentParser(description="Artifactory Docker Cleanup Script")
    parser.add_argument("--url", default=os.getenv("ARTIFACTORY_URL", "https://your-artifactory-instance/artifactory"), help="Artifactory base URL")
    parser.add_argument("--repo", default=os.getenv("REPO_NAME", "your-docker-repo"), help="Docker repository name")
    parser.add_argument("--user", default=os.getenv("USERNAME", "your-username"), help="Artifactory username")
    parser.add_argument("--password", default=os.getenv("PASSWORD", "your-password"), help="Artifactory password")
    parser.add_argument("--keep", type=int, default=int(os.getenv("KEEP_LATEST", 10)), help="Number of latest images to keep")
    parser.add_argument("--days", type=int, default=int(os.getenv("DELETE_OLDER_THAN_DAYS", 30)), help="Delete artifacts older than N days")
    parser.add_argument("--artifact", default=os.getenv("ARTIFACT_NAME", None), help="Specific artifact name (optional)")
    
    return parser.parse_args()

def list_old_tags(config):
    url = f"{config.url}/api/docker/{config.repo}/v2/_catalog"
    response = requests.get(url, auth=HTTPBasicAuth(config.user, config.password))
    if response.status_code == 200:
        repositories = response.json().get("repositories", [])
        if config.artifact:
            repositories = [config.artifact] if config.artifact in repositories else []
        
        for repo in repositories:
            tag_url = f"{config.url}/api/docker/{config.repo}/v2/{repo}/tags/list"
            tag_response = requests.get(tag_url, auth=HTTPBasicAuth(config.user, config.password))
            if tag_response.status_code == 200:
                tags = sorted(tag_response.json().get("tags", []))
                metadata_url = f"{config.url}/api/storage/{config.repo}/{repo}"
                metadata_response = requests.get(metadata_url, auth=HTTPBasicAuth(config.user, config.password))
                
                if metadata_response.status_code == 200:
                    items = metadata_response.json().get("children", [])
                    tag_dates = {}
                    for item in items:
                        item_url = f"{metadata_url}{item['uri']}?properties"
                        item_response = requests.get(item_url, auth=HTTPBasicAuth(config.user, config.password))
                        if item_response.status_code == 200:
                            properties = item_response.json().get("properties", {})
                            created = properties.get("created", [None])[0]
                            if created:
                                tag_dates[item['uri'].strip("/")] = datetime.strptime(created, "%Y-%m-%dT%H:%M:%S.%fZ")
                    
                    cutoff_date = datetime.utcnow() - timedelta(days=config.days)
                    tags_to_delete = [tag for tag in sorted(tag_dates, key=tag_dates.get)[:-config.keep] if tag_dates[tag] < cutoff_date]
                    print(f"Repository: {repo}, Tags to delete: {tags_to_delete}")
                else:
                    print(f"Failed to fetch metadata for {repo}: {metadata_response.text}")
            else:
                print(f"Failed to fetch tags for {repo}: {tag_response.text}")
    else:
        print(f"Failed to list repositories: {response.text}")

def delete_old_images(config):
    url = f"{config.url}/api/docker/{config.repo}/v2/_catalog"
    response = requests.get(url, auth=HTTPBasicAuth(config.user, config.password))
    if response.status_code == 200:
        repositories = response.json().get("repositories", [])
        if config.artifact:
            repositories = [config.artifact] if config.artifact in repositories else []
        
        for repo in repositories:
            tag_url = f"{config.url}/api/docker/{config.repo}/v2/{repo}/tags/list"
            tag_response = requests.get(tag_url, auth=HTTPBasicAuth(config.user, config.password))
            if tag_response.status_code == 200:
                tags = sorted(tag_response.json().get("tags", []))
                metadata_url = f"{config.url}/api/storage/{config.repo}/{repo}"
                metadata_response = requests.get(metadata_url, auth=HTTPBasicAuth(config.user, config.password))
                
                if metadata_response.status_code == 200:
                    items = metadata_response.json().get("children", [])
                    tag_dates = {}
                    for item in items:
                        item_url = f"{metadata_url}{item['uri']}?properties"
                        item_response = requests.get(item_url, auth=HTTPBasicAuth(config.user, config.password))
                        if item_response.status_code == 200:
                            properties = item_response.json().get("properties", {})
                            created = properties.get("created", [None])[0]
                            if created:
                                tag_dates[item['uri'].strip("/")] = datetime.strptime(created, "%Y-%m-%dT%H:%M:%S.%fZ")
                    
                    cutoff_date = datetime.utcnow() - timedelta(days=config.days)
                    tags_to_delete = [tag for tag in sorted(tag_dates, key=tag_dates.get)[:-config.keep] if tag_dates[tag] < cutoff_date]
                    
                    for tag in tags_to_delete:
                        delete_url = f"{config.url}/{config.repo}/{repo}/{tag}"
                        delete_response = requests.delete(delete_url, auth=HTTPBasicAuth(config.user, config.password))
                        if delete_response.status_code == 204:
                            print(f"Deleted: {repo}:{tag}")
                        else:
                            print(f"Failed to delete {repo}:{tag}: {delete_response.text}")
                else:
                    print(f"Failed to fetch metadata for {repo}: {metadata_response.text}")
            else:
                print(f"Failed to fetch tags for {repo}: {tag_response.text}")
    else:
        print(f"Failed to list repositories: {response.text}")

if __name__ == "__main__":
    config = get_config()
    print("Listing tags to delete:")
    list_old_tags(config)
    print("Deleting old images:")
    delete_old_images(config)
