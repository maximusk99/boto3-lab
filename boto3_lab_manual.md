# Boto3 Lab: Complete Step-by-Step Guide (macOS)

This lab manual consolidates and streamlines the instructions, troubleshooting, and notes gathered during setup of a **Python automation environment with Boto3**. It is designed so you can follow it end-to-end without needing any external references.

---

## 1. What You’ll Build
- A clean Python environment on macOS.
- AWS CLI configured with either IAM Identity Center (SSO) or IAM access keys.
- A lab S3 bucket with least-privilege access.
- A starter Boto3 script that lists buckets and retrieves an object.
- Optional automation using macOS LaunchAgent or AWS-native scheduling.

---

## 2. Prerequisites
- macOS with Terminal access.
- Python 3.9+ installed.
- Homebrew (optional, but recommended).
- An AWS account with ability to create IAM users or SSO permission sets.

### Install basics (if not already installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install pyenv direnv awscli
brew install --cask visual-studio-code
```

Add to your shell:
```bash
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
exec zsh
```

Verify:
```bash
python3 --version
```

---

## 3. Project Setup
```bash
cd ~
mkdir -p Projects/boto3-lab
cd Projects/boto3-lab

echo "layout python" > .envrc
direnv allow
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip boto3 botocore
```

---

## 4. Initialize Git & GitHub
```bash
git init -b main
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### Starter files
**README.md**
```markdown
# boto3-lab
First Python automation lab using Boto3. Set up on macOS.
```

**.gitignore**
```gitignore
# macOS
.DS_Store

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
*.pkl
*.log

# Virtual environments
.venv/

# Local environment variables
.env
.envrc

# Editors
.vscode/
.idea/

# Jupyter
.ipynb_checkpoints/

# AWS
.aws/
```

Commit:
```bash
git add .
git commit -m "Initial commit: boto3 lab setup"
```

### Connect to GitHub
- **Fine-grained token** (recommended): grant `Contents: Read and write` to only `boto3-lab` repo.
- Or use SSH:
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
pbcopy < ~/.ssh/id_ed25519.pub   # add to GitHub → Settings → SSH keys
git remote add origin git@github.com:MAXIMUSK99/boto3-lab.git
git push -u origin main
```

---

## 5. AWS Authentication

### Option A — AWS SSO (recommended)
```bash
aws configure sso --profile boto3-lab
aws sso login --profile boto3-lab
```

### Option B — IAM User with Access Keys
1. In the AWS Console, go to IAM → Users → Add user.
2. Enable **Programmatic access**.
3. Attach least-privilege policy (see below).
4. Configure locally:
```bash
aws configure --profile boto3-lab
```

---

## 6. IAM Policies

### Minimal read-only policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect": "Allow", "Action": ["s3:ListAllMyBuckets"], "Resource": "*"},
    {"Effect": "Allow", "Action": ["s3:ListBucket"], "Resource": "arn:aws:s3:::YOUR-LAB-BUCKET"},
    {"Effect": "Allow", "Action": ["s3:GetObject"], "Resource": "arn:aws:s3:::YOUR-LAB-BUCKET/*"}
  ]
}
```

### Add write access (if you want uploads/deletes)
```json
"s3:PutObject", "s3:DeleteObject"
```

Attach with an **admin-capable profile** (`workstation-admin` or SSO Admin).

---

## 7. Create the Lab Bucket
```bash
BUCKET=boto3-lab-<username>-$(date +%s)
aws s3api create-bucket --bucket "$BUCKET" --region us-east-1 --profile workstation-admin

echo "Hello from Boto3!" > hello.txt
aws s3 cp hello.txt s3://$BUCKET/hello.txt --profile workstation-admin
```

Export environment variables:
```bash
export LAB_BUCKET=$BUCKET
export LAB_KEY=hello.txt
```

---

## 8. First Boto3 Script
**s3_list_and_read.py**
```python
import boto3, os

session = boto3.Session(profile_name="boto3-lab")
s3 = session.client("s3")

# List buckets
resp = s3.list_buckets()
print("Buckets:")
for b in resp.get("Buckets", []):
    print(" -", b["Name"])

# Read object
bucket = os.environ.get("LAB_BUCKET")
key = os.environ.get("LAB_KEY", "hello.txt")

try:
    obj = s3.get_object(Bucket=bucket, Key=key)
    print(f"\nContents of s3://{bucket}/{key}:\n{obj['Body'].read().decode('utf-8')}")
except s3.exceptions.NoSuchKey:
    print(f"Object not found: s3://{bucket}/{key}")
```

Run:
```bash
python s3_list_and_read.py
```

---

## 9. Troubleshooting Notes
- **403 Forbidden**: bucket exists but you lack `s3:ListBucket`.
- **404 Not Found**: key doesn’t exist; check object name and path.
- **AccessDenied on PutObject**: policy missing `s3:PutObject`.
- **Invalid username/token for Git push**: must use PAT or SSH.
- **zsh EOF issues**: when writing files with `cat <<EOF`, paste JSON cleanly and close with `EOF` on its own line.

---

## 10. Automation Options

### macOS LaunchAgent (local)
- Install plist in `~/Library/LaunchAgents/`.
- Example schedule: run at login + daily 9am.
- Logs go to `~/Library/Logs/boto3lab.*.log`.

### AWS-native (recommended for production)
- **EventBridge Scheduler → Lambda**.
- Create a Lambda with `boto3` client calls.
- Schedule with cron/rate expressions (supports time zones).

---

## 11. Next Steps
- Add DynamoDB or RDS read operations.
- Implement retries and structured logging.
- Explore multipart uploads with progress callbacks.
- Replace static profile with env-based auth for CI/CD.
- Experiment with CloudWatch metrics in Boto3.

---

## ✅ Outcome
At this point, you have:
- A Python project on macOS with Git/GitHub integration.
- AWS CLI and credentials configured.
- A working S3 bucket with least-privilege access.
- A Boto3 script that lists and reads objects.
- The foundation to extend into automation and cloud-native scheduling.
