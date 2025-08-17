# Boto3 Lab Documentation

This document provides a complete step-by-step guide to setting up and running a Boto3 lab environment. 
All sensitive values (account IDs, usernames, bucket names) have been masked.

---

## 1. Prerequisites

- Python 3.11+ installed
- AWS CLI installed and configured with a profile (`workstation-admin` or equivalent)
- Basic understanding of IAM policies, roles, and S3

---

## 2. Lab Setup

### Create Lab Directory

```bash
mkdir -p "$HOME/.boto3lab"
```

Verify:

```bash
ls -al $HOME/.boto3lab
```

Example output:

```
-rw-r--r--   1 your-username  staff   140 Aug 15  requirements.txt
drwxr-xr-x   6 your-username  staff   192 Aug 15  venv
```

### Create Virtual Environment

```bash
python3 -m venv "$HOME/.boto3lab/venv"
source "$HOME/.boto3lab/venv/bin/activate"
```

### Requirements File

`requirements.txt` should include:

```
boto3>=1.34.98
botocore>=1.34.98
```

Install requirements:

```bash
pip install -r "$HOME/.boto3lab/requirements.txt"
```

---

## 3. IAM Policy and User

### Create IAM Policy

```bash
aws iam create-policy   --policy-name Boto3LabS3RW   --policy-document file://boto3lab-s3rw.json   --profile workstation-admin
```

### Attach Policy to User

```bash
aws iam attach-user-policy   --user-name boto3-lab-RO   --policy-arn arn:aws:iam::111111111111:policy/Boto3LabS3RW   --profile workstation-admin
```

---

## 4. S3 Test

### List Buckets via CLI

```bash
aws s3 ls --profile boto3lab
```

Example masked output:

```
2025-08-15 20:47:11 boto3-lab-<masked>
```

---

## 5. Python Script

Create `$HOME/.boto3lab/s3_list_buckets.py`:

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
        print("ERROR: No AWS credentials found. Run aws configure.", file=sys.stderr); sys.exit(2)
    except ClientError as e:
        print(f"AWS ClientError: {e}", file=sys.stderr); sys.exit(3)

if __name__ == "__main__":
    main()
```

Make executable:

```bash
chmod +x "$HOME/.boto3lab/s3_list_buckets.py"
```

Run test:

```bash
"$HOME/.boto3lab/venv/bin/python" "$HOME/.boto3lab/s3_list_buckets.py" boto3lab
```

Example masked output:

```
Wrote 1 buckets to $HOME/boto3_lab_logs/s3_buckets_2025-08-15T20-47-11Z.log
```

---

## 6. LaunchAgent Automation (macOS)

### Create PLIST

`$HOME/.boto3lab/com.boto3lab.example.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
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
  <key>StartCalendarInterval</key><dict>
    <key>Hour</key><integer>9</integer>
    <key>Minute</key><integer>0</integer>
  </dict>
</dict>
</plist>
```

### Load LaunchAgent

```bash
mkdir -p "$HOME/Library/LaunchAgents"
cp "$HOME/.boto3lab/com.boto3lab.example.plist" "$HOME/Library/LaunchAgents/com.boto3lab.example.plist"

launchctl unload "$HOME/Library/LaunchAgents/com.boto3lab.example.plist" 2>/dev/null || true
launchctl load  "$HOME/Library/LaunchAgents/com.boto3lab.example.plist"
launchctl start com.boto3lab.example
```

Check logs:

```bash
tail -n 50 ~/Library/Logs/boto3lab.out.log
tail -n 50 ~/Library/Logs/boto3lab.err.log
```

---

## 7. Verification

```bash
ls -lt ~/boto3_lab_logs
```

Example masked output:

```
-rw-r--r--  1 your-username  staff  25 Aug 15 15:55 s3_buckets_2025-08-15T20-55-22Z.log
-rw-r--r--  1 your-username  staff  25 Aug 15 15:47 s3_buckets_2025-08-15T20-47-11Z.log
```

---

## 8. Notes & Troubleshooting

- Always use a non-root AWS profile for the lab (`boto3lab` recommended).
- Ensure IAM policies are created **before** attaching.
- macOS `sed` requires `-i ''` syntax.
- Logs are rotated daily by timestamp.

---

## 9. Summary

You now have a complete Boto3 Lab environment that:
- Creates and uses a dedicated IAM policy and user
- Tests connectivity with S3
- Automates bucket listing with a Python script
- Schedules daily execution with LaunchAgent
- Writes logs to `$HOME/boto3_lab_logs`
