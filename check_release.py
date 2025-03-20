import requests
import os
import sys
import traceback

try:
    REPO = os.getenv("REPO")
    if not REPO:
        print("❌ 环境变量 REPO 未设置")
        sys.exit(2)

    API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
    print(f"正在检查 {REPO} 的最新版本，API URL: {API_URL}")

    # 添加 GitHub API 认证（如果有 GITHUB_TOKEN）
    headers = {}
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"token {github_token}"
        print("使用 GITHUB_TOKEN 进行认证")

    response = requests.get(API_URL, headers=headers)
    print(f"API 请求状态码: {response.status_code}")

    if response.status_code != 200:
        print(f"❌ 无法获取 {REPO} 的最新版本，状态码: {response.status_code}")
        print(f"错误信息: {response.text}")
        sys.exit(1)

    latest_version = response.json()['tag_name']
    release_url = response.json()['html_url']
    print(f"最新版本: {latest_version}, 发布链接: {release_url}")

    # 文件命名为仓库名，防止冲突
    version_file = REPO.replace("/", "_") + "_latest_version.txt"

    # 读取已保存的版本号
    try:
        with open(version_file, "r") as f:
            saved_version = f.read().strip()
        print(f"已保存的版本: {saved_version}")
    except FileNotFoundError:
        saved_version = None
        print("版本文件不存在，将创建新文件")

    if latest_version != saved_version:
        with open(version_file, "w") as f:
            f.write(latest_version)
        print(f"🎉 新版本发布: {latest_version} - {release_url}")

        # 设置输出，供下一个步骤使用
        with open(os.environ['GITHUB_ENV'], 'a') as env_file:
            env_file.write(f"NEW_VERSION={latest_version}\n")
            env_file.write(f"RELEASE_URL={release_url}\n")
            env_file.write(f"SDK={REPO}\n")
    else:
        print(f"✅ {REPO} 已是最新版本")

except Exception as e:
    print(f"❌ 脚本执行失败: {str(e)}")
    print("详细错误信息:")
    traceback.print_exc()
    sys.exit(2)
