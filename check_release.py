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

        # 获取最新正式发布版本
        non_prereleases = [r for r in releases if not r.get('prerelease', False)]
        if not non_prereleases:
            print("无正式发布版本")
            sys.exit(0)
        latest_release = sorted(non_prereleases, key=lambda x: x['published_at'], reverse=True)[0]
        latest_version = latest_release['tag_name']
        release_url = latest_release['html_url']

        # 版本存储目录
        version_dir = "versions"
        os.makedirs(version_dir, exist_ok=True)
        version_file = os.path.join(version_dir, REPO.replace("/", "_") + "_latest_version.txt")
        print(f"📂 版本文件路径: {version_file}")
        print(f"📂 当前工作目录: {os.getcwd()}")

        saved_version = None
        if os.path.exists(version_file):
            with open(version_file, "r") as f:
                saved_version = f.read().strip()
            print(f"📖 从文件读取的本地版本: {saved_version}")
        else:
            print("📖 本地版本文件不存在，将进行首次初始化")

        # 首次运行时记录最新版本，不触发通知
        if not saved_version:
            print(f"📌 初次运行，记录最新版本: {latest_version}")
            with open(version_file, "w") as f:
                f.write(latest_version)
            # 确认写入是否成功
            if os.path.exists(version_file):
                with open(version_file, "r") as f:
                    written_version = f.read().strip()
                print(f"✅ 首次写入成功，确认版本: {written_version}")
            else:
                print("❌ 首次写入失败，文件未创建")
            sys.exit(0)

        # 版本号比较
        current_ver = parse_version(saved_version)
        latest_ver = parse_version(latest_version)
        print(f"✈️ 获取的最新版本: {latest_version}")
        print(f"🚘 本地记录的版本: {saved_version}")
        print(f"🔍 版本比较: {latest_ver} > {current_ver} = {latest_ver > current_ver}")

        if latest_ver > current_ver:
            print(f"🎉 发现新版本: {latest_version}")
            # 更新本地版本文件
            try:
                with open(version_file, "w") as f:
                    f.write(latest_version)
                # 确认写入是否成功
                if os.path.exists(version_file):
                    with open(version_file, "r") as f:
                        written_version = f.read().strip()
                    print(f"✅ 更新本地版本成功，确认版本: {written_version}")
                else:
                    print("❌ 更新本地版本失败，文件未创建")
            except Exception as e:
                print(f"❌ 写入版本文件失败: {e}")
                traceback.print_exc()
                sys.exit(1)

            # 写入 GitHub Actions 环境变量
            with open(os.environ['GITHUB_ENV'], 'a') as env_file:
                env_file.write(f"NEW_VERSION={latest_version}\n")
                env_file.write(f"RELEASE_URL={release_url}\n")
                env_file.write(f"SDK={REPO}\n")
        else:
            print(f"✅ 当前已是最新版本: {latest_version}")

    except Exception as e:
        print(f"❌ 发生错误: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
