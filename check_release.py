import requests
import os
import sys
import traceback
from packaging.version import parse as parse_version
from datetime import datetime

def normalize_version(version):
    """标准化版本字符串：去除 v 前缀和末尾 .0"""
    if version.startswith(('v', 'V')):
        version = version[1:]
    while version.endswith('.0'):
        version = version[:-2]
    return version

def read_version_file(filepath):
    """读取版本记录文件，返回字典 {repo: version}"""
    versions = {}
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if "->" in line:
                    repo, version = line.split("->")
                    versions[repo.strip()] = version.strip()
    return versions

def update_version_file(filepath, repo, new_version):
    """更新 sdk_versions.txt 中某个 repo 的版本"""
    versions = read_version_file(filepath)
    versions[repo] = new_version
    with open(filepath, "w") as f:
        for r, v in versions.items():
            f.write(f"{r} -> {v}\n")

def append_version_history(history_file, repo, version):
    """追加一条历史记录"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(history_file, "a") as f:
        f.write(f"[{now}] {repo} -> {version}\n")

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

        # 文件路径
        version_file = "sdk_versions.txt"
        history_file = "sdk_versions_history.txt"

        # 读取旧版本
        versions = read_version_file(version_file)
        saved_version = versions.get(REPO)

        print(f"📂 当前 REPO: {REPO}")
        print(f"📦 最新版本: {latest_version}")
        print(f"🧾 本地记录版本: {saved_version or '无'}")

        # 如果无旧版本，初始化
        if not saved_version:
            print("📌 初次记录版本")
            update_version_file(version_file, REPO, latest_version)
            append_version_history(history_file, REPO, latest_version)
            print("✅ 初次写入完成")
            # Set environment variables even for initial run
            with open(os.environ['GITHUB_ENV'], 'a') as env_file:
                env_file.write(f"NEW_VERSION={latest_version}\n")
                env_file.write(f"RELEASE_URL={release_url}\n")
                env_file.write(f"SDK={REPO}\n")
            sys.exit(0)

        # 比较版本
        current_ver = parse_version(normalize_version(saved_version))
        latest_ver = parse_version(normalize_version(latest_version))

        if latest_ver > current_ver:
            print(f"🎉 发现新版本: {latest_version}")
            update_version_file(version_file, REPO, latest_version)
            append_version_history(history_file, REPO, latest_version)
            print("✅ 已写入版本更新记录")

            # 设置 GitHub Actions 环境变量
            with open(os.environ['GITHUB_ENV'], 'a') as env_file:
                env_file.write(f"NEW_VERSION={latest_version}\n")
                env_file.write(f"RELEASE_URL={release_url}\n")
                env_file.write(f"SDK={REPO}\n")
        else:
            print("✅ 当前已是最新版本，无需更新")

    except Exception as e:
        print(f"❌ 发生错误: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
