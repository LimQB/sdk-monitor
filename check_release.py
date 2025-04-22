import requests
import os
import sys
import traceback
import json
from packaging.version import parse as parse_version
import subprocess

def normalize_version(version):
    if version.startswith(('v', 'V')):
        version = version[1:]
    while version.endswith('.0'):
        version = version[:-2]
    return version

def fetch_remote_versions():
    """Fetch the remote versions.json from the main branch."""
    try:
        # Fetch the latest main branch
        subprocess.run(["git", "fetch", "origin", "main"], check=True)
        # Get the contents of versions.json from the remote main branch
        result = subprocess.run(
            ["git", "show", "origin/main:versions.json"],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError:
        # If the file doesn't exist or there's an error, return an empty dict
        print("⚠️ Could not fetch remote versions.json, assuming empty file")
        return {}
    except json.JSONDecodeError:
        print("⚠️ Remote versions.json is invalid, assuming empty file")
        return {}

def read_versions():
    """Read the local versions.json file."""
    version_file = "versions.json"
    if os.path.exists(version_file):
        with open(version_file, "r") as f:
            return json.load(f)
    return {}

def write_versions(versions):
    """Write the versions to versions.json."""
    with open("versions.json", "w") as f:
        json.dump(versions, f, indent=2)
    print("✅ 已更新 versions.json 文件")

def main():
    try:
        REPO = os.getenv("REPO")
        if not REPO:
            print("❌ 环境变量 REPO 未设置")
            sys.exit(2)

        API_URL = f"https://api.github.com/repos/{REPO}/releases"
        headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"token {github_token}"

        response = requests.get(API_URL, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            sys.exit(1)

        releases = response.json()
        if not releases:
            print("❌ 该仓库没有发布版本")
            sys.exit(0)

        non_prereleases = [r for r in releases if not r.get('prerelease', False)]
        if not non_prereleases:
            print("无正式发布版本")
            sys.exit(0)
        latest_release = sorted(non_prereleases, key=lambda x: x['published_at'], reverse=True)[0]
        latest_version = latest_release['tag_name']
        release_url = latest_release['html_url']

        # Fetch the remote versions.json to merge with local changes
        remote_versions = fetch_remote_versions()
        # Read the local versions.json (may have been modified by previous jobs)
        local_versions = read_versions()
        # Merge remote versions into local versions
        versions = remote_versions.copy()
        versions.update(local_versions)

        repo_key = REPO.replace("/", "_")
        saved_version = versions.get(repo_key)

        if not saved_version:
            print(f"📌 初次运行，记录最新版本: {latest_version}")
            versions[repo_key] = latest_version
            write_versions(versions)
            sys.exit(0)

        current_ver = parse_version(normalize_version(saved_version))
        latest_ver = parse_version(normalize_version(latest_version))
        print(f"✈️ 获取的最新版本: {latest_version}")
        print(f"🚘 本地记录的版本: {saved_version}")
        print(f"🔍 版本比较: {latest_ver} > {current_ver} = {latest_ver > current_ver}")

        if latest_ver > current_ver:
            print(f"🎉 发现新版本: {latest_version}")
            versions[repo_key] = latest_version
            write_versions(versions)

            with open(os.environ['GITHUB_ENV'], 'a') as env_file:
                env_file.write(f"NEW_VERSION={latest_version}\n")
                env_file.write(f"RELEASE_URL={release_url}\n")
                env_file.write(f"SDK={REPO}\n")
                env_file.write("VERSION_UPDATED=true\n")
        else:
            print(f"✅ 当前已是最新版本: {latest_version}")

    except Exception as e:
        print(f"❌ 发生错误: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
