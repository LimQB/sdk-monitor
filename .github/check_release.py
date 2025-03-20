import requests
import os

REPO = os.getenv("REPO")
API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"

response = requests.get(API_URL)
if response.status_code != 200:
    print(f"❌ 无法获取 {REPO} 的最新版本")
    exit(1)

latest_version = response.json()['tag_name']
release_url = response.json()['html_url']

# 文件命名为仓库名，防止冲突
version_file = REPO.replace("/", "_") + "_latest_version.txt"

# 读取已保存的版本号
try:
    with open(version_file, "r") as f:
        saved_version = f.read().strip()
except FileNotFoundError:
    saved_version = None

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
