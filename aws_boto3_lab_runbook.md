# AWS Boto3 Lab Runbook

This runbook documents the setup of an AWS lab environment for experimenting with **boto3**, AWS CLI, and scheduled tasks on macOS. All sensitive information (account IDs, usernames, paths) has been masked for security.

---

## 1. AWS Account Setup

1. Create a new AWS account.
2. Configure root user MFA and billing alerts.
3. Create an **Admin IAM user** (e.g., `workstation-admin`) with programmatic and console access.
4. Configure AWS CLI profiles:
   ```bash
   aws configure --profile workstation-admin
   aws configure --profile boto3-lab
   ```

---

## 2. IAM Policies & Users

### 2.1 Create IAM Policy for S3 Read/Write
```bash
aws iam create-policy   --policy-name Boto3LabS3RW   --policy-document file://boto3lab-s3-rw.json   --profile workstation-admin
```

*Example `boto3lab-s3-rw.json`:*
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket", "s3:GetObject", "s3:PutObject"],
      "Resource": ["arn:aws:s3:::boto3-lab-*", "arn:aws:s3:::boto3-lab-*/*"]
    }
  ]
}
```

### 2.2 Attach Policy to IAM User
```bash
aws iam attach-user-policy   --user-name boto3-lab-RO   --policy-arn arn:aws:iam::<ACCOUNT_ID>:policy/Boto3LabS3RW   --profile workstation-admin
```

---

## 3. S3 Bucket Setup

### 3.1 Create S3 Bucket
```bash
aws s3 mb s3://boto3-lab-<unique-id> --profile boto3-lab
```

### 3.2 Upload Test File
```bash
echo "hello boto3 lab" > hello.txt
aws s3 cp hello.txt s3://boto3-lab-<unique-id>/hello.txt --profile boto3-lab
```

### 3.3 Verify Access
```bash
aws s3 cp s3://boto3-lab-<unique-id>/hello.txt - --profile boto3-lab
```

---

## 4. Local Lab Environment

### 4.1 Create Project Directory
```bash
mkdir -p $HOME/.boto3lab
```

### 4.2 Setup Virtual Environment
```bash
python3 -m venv $HOME/.boto3lab/venv
source $HOME/.boto3lab/venv/bin/activate
pip install boto3 botocore
```

### 4.3 Requirements File
`requirements.txt`:
```
boto3>=1.34.98
botocore>=1.34.98
```

---

## 5. Python Script for S3 Listing

### 5.1 Script: `s3_list_buckets.py`
```python
import boto3, os, sys
from datetime import datetime
from botocore.exceptions import NoCredentialsError, ClientError

def main():
    s3 = boto3.client("s3")
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
    out_dir = os.environ.get("BOTO3_LAB_LOG_DIR", os.path.expanduser("~/boto3_lab_logs"))
    os.makedirs(out_dir, exist_ok=True)
    log_path = os.path.join(out_dir, f"s3_buckets_{ts}.log")

    try:
        resp = s3.list_buckets()
        names = [b["Name"] for b in resp.get("Buckets", [])]
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(names) if names else "(no buckets found)")
        print(f"Wrote {len(names)} buckets to {log_path}")
    except NoCredentialsError:
        print("ERROR: No AWS credentials found. Run aws configure.", file=sys.stderr)
        sys.exit(2)
    except ClientError as e:
        print(f"AWS ClientError: {e}", file=sys.stderr)
        sys.exit(3)

if __name__ == "__main__":
    main()
```

Make it executable:
```bash
chmod +x $HOME/.boto3lab/s3_list_buckets.py
```

---

## 6. Scheduling with `launchd` (macOS)

### 6.1 Create Log Directory
```bash
mkdir -p $HOME/boto3_lab_logs
mkdir -p $HOME/Library/LaunchAgents
```

### 6.2 Create Launchd Plist
File: `$HOME/.boto3lab/com.boto3lab.example.plist`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.boto3lab.example</string>
  <key>ProgramArguments</key>
  <array>
    <string>$HOME/.boto3lab/venv/bin/python</string>
    <string>$HOME/.boto3lab/s3_list_buckets.py</string>
    <string>boto3lab</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key><string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    <key>BOTO3_LAB_LOG_DIR</key><string>$HOME/boto3_lab_logs</string>
  </dict>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/boto3lab.out.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/boto3lab.err.log</string>
  <key>RunAtLoad</key><true/>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key><integer>9</integer>
    <key>Minute</key><integer>0</integer>
  </dict>
</dict>
</plist>
```

### 6.3 Deploy and Start Service
```bash
cp $HOME/.boto3lab/com.boto3lab.example.plist $HOME/Library/LaunchAgents/com.boto3lab.example.plist
launchctl unload $HOME/Library/LaunchAgents/com.boto3lab.example.plist 2>/dev/null || true
launchctl load  $HOME/Library/LaunchAgents/com.boto3lab.example.plist
launchctl start com.boto3lab.example
```

---

## 7. Verification

Check logs:
```bash
tail -n 50 ~/Library/Logs/boto3lab.out.log
tail -n 50 ~/Library/Logs/boto3lab.err.log
```

Check S3 logs:
```bash
ls -lt ~/boto3_lab_logs
cat ~/boto3_lab_logs/s3_buckets_<timestamp>.log
```

---

## ✅ Completed Setup

- Secure AWS account created.
- IAM users, policies, and S3 bucket configured.
- Local boto3 environment built with virtualenv.
- Automated bucket logging scheduled with launchd.
- Logs verified for successful execution.
