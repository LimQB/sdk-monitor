- name: Create Python script
  run: |
    cat <<EOF > check_release.py
import requests
import os

REPO = '${{ matrix.repo }}'
API_URL = f'https://api.github.com/repos/{REPO}/releases/latest'

response = requests.get(API_URL)
latest_version = response.json()['tag_name']
release_url = response.json()['html_url']

version_file = REPO.replace('/', '_') + '_latest_version.txt'

try:
    with open(version_file, 'r') as f:
        saved_version = f.read().strip()
except FileNotFoundError:
    saved_version = None

if latest_version != saved_version:
    with open(version_file, 'w') as f:
        f.write(latest_version)
    
    with open(os.environ['GITHUB_ENV'], 'a') as env_file:
        env_file.write(f'NEW_VERSION={latest_version}\n')
        env_file.write(f'RELEASE_URL={release_url}\n')
        env_file.write(f'SDK={REPO}\n')
else:
    print(f'✅ {REPO} 已是最新版本')
EOF

- name: Run Python script
  run: python check_release.py
