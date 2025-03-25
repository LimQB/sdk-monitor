import requests
import os
import sys
import traceback
from packaging.version import parse as parse_version

def main():
    try:
        REPO = os.getenv("REPO")
        if not REPO:
            print("❌ 环境变量 REPO 未设置")
            sys.exit(2)
        if len(REPO.split('/')) != 2:
            print("❌ 仓库名称格式错误，应为 'owner/repo'")
            sys.exit(1)

        API_URL = f"https://api.github.com/repos/{REPO}/releases"
        headers = {}
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

        # 获取最新正式发布
        non_prereleases = [r for r in releases if not r.get('prerelease', False)]
        if not non_prereleases:
            print("无正式发布版本")
            sys.exit(0)
        latest_release = sorted(non_prereleases, key=lambda x: x['published_at'], reverse=True)[0]
        latest_version = latest_release['tag_name']
        release_url = latest_release['html_url']

        # 版本文件存储
        version_dir = "versions"
        os.makedirs(version_dir, exist_ok=True)
        version_file = os.path.join(version_dir, REPO.replace("/", "_") + "_latest_version.txt")

        saved_version = None
        if os.path.exists(version_file):
            with open(version_file, "r") as f:
                saved_version = f.read().strip()

        if saved_version:
            current_ver = parse_version(saved_version.lstrip('v'))
            latest_ver = parse_version(latest_version.lstrip('v'))
            if latest_ver > current_ver:
                print(f"🎉 发现新版本: {latest_version}")
                with open(version_file, "w") as f:
                    f.write(latest_version)
                # 写入环境变量
                env_prefix = REPO.replace("/", "_").upper()
                with open(os.environ['GITHUB_ENV'], 'a') as env_file:
                    env_file.write(f"{env_prefix}_NEW_VERSION={
