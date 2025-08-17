# AWS Boto3 Lab – Step‑by‑Step Guide (with Commands)

> **Scope**: This guide documents what you completed to stand up AWS for your Boto3 lab on macOS—creating/secureing the account, setting up IAM (users, policies), configuring CLI profiles, testing S3 with Boto3, and automating a daily job with `launchctl`.
>
> **Masking**: All sensitive values are masked. Replace placeholders with your own values:
> - `<AWS_ACCOUNT_ID>` e.g., `111111111111`
> - `<REGION>` e.g., `us-east-1`
> - `<PROFILE_ADMIN>` e.g., `workstation-admin`
> - `<PROFILE_LAB>` e.g., `boto3-lab`
> - `<LAB_BUCKET>` e.g., `boto3-lab-yourname-1234`
> - `<HOME>` e.g., `/Users/your-username`

---

## 0) Prerequisites (macOS)
- Python 3.11+
- AWS CLI v2
- A terminal (zsh/bash)
- A text editor (VS Code, etc.)

Verify versions:
```bash
python3 -V
aws --version
```

---

## 1) Create & Secure Your AWS Account
1. **Create account** at aws.amazon.com and **verify email**.
2. **Secure the root user** (one-time):
   - Enable **MFA** on the root user.
   - **Do not** create access keys for the root user.
   - Set up billing alerts/thresholds.

> From this point forward, do **not** use root for daily work.

---

## 2) Create an Admin IAM User (for setup tasks)
This user will temporarily have admin-level rights to create policies/users.

1) Create an IAM user (console):
- Name: `workstation-admin` (or your choice)
- Console access: Enabled
- Programmatic access: Create an access key (store safely)
- Attach policy: `AdministratorAccess` (you can later swap to a tighter set)

2) Configure AWS CLI profile on your Mac:
```bash
aws configure --profile <PROFILE_ADMIN>
# Access Key ID:  ********************
# Secret Access Key: ********************
# Default region name: <REGION>
# Default output format: json
```

3) Verify:
```bash
aws sts get-caller-identity --profile <PROFILE_ADMIN>
# {
#   "UserId": "AIDAX...",
#   "Account": "<AWS_ACCOUNT_ID>",
#   "Arn": "arn:aws:iam::<AWS_ACCOUNT_ID>:user/workstation-admin"
# }
```

---

## 3) Create the Lab IAM User and Policies
You created a lab user and attached policies to allow S3 access to a specific bucket.

### 3.1 Create the lab user
- Name: `boto3-lab-RO` (name historical; you ended up granting RW to your bucket)
- Programmatic access only (Access key + secret key)

(Optional CLI example using admin profile):
```bash
aws iam create-user --user-name boto3-lab-RO --profile <PROFILE_ADMIN>
```

### 3.2 Create a **bucket-scoped** RW policy for your lab bucket
Prepare a file (mask `<LAB_BUCKET>`):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": "s3:ListAllMyBuckets", "Resource": "*" },
    { "Effect": "Allow", "Action": "s3:ListBucket", "Resource": "arn:aws:s3:::<LAB_BUCKET>" },
    { "Effect": "Allow", "Action": ["s3:GetObject","s3:PutObject","s3:DeleteObject"], "Resource": "arn:aws:s3:::<LAB_BUCKET>/*" }
  ]
}
```

Save as `/tmp/boto3-lab-s3-rw.json` then create the policy:
```bash
aws iam create-policy \
  --policy-name Boto3LabS3RW \
  --policy-document file:///tmp/boto3-lab-s3-rw.json \
  --profile <PROFILE_ADMIN>
```

Capture the ARN:
```bash
POLICY_ARN=$(aws iam list-policies --scope Local \
  --query "Policies[?PolicyName=='Boto3LabS3RW'].Arn | [0]" \
  --output text --profile <PROFILE_ADMIN>)
echo "$POLICY_ARN"
# arn:aws:iam::<AWS_ACCOUNT_ID>:policy/Boto3LabS3RW
```

### 3.3 Attach policies to the lab user
- Baseline read-only (optional): `arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess`
- Your bucket-scoped RW: `$POLICY_ARN`

```bash
aws iam attach-user-policy \
  --user-name boto3-lab-RO \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess \
  --profile <PROFILE_ADMIN>

aws iam attach-user-policy \
  --user-name boto3-lab-RO \
  --policy-arn "$POLICY_ARN" \
  --profile <PROFILE_ADMIN>

aws iam list-attached-user-policies \
  --user-name boto3-lab-RO \
  --profile <PROFILE_ADMIN>
```

> Result: the lab user can list your buckets and read/write objects **within `<LAB_BUCKET>` only**.

---

## 4) Create/Confirm the S3 Lab Bucket
Choose a globally-unique name (you used a pattern like `boto3-lab-yourname-1234`):
```bash
aws s3api create-bucket \
  --bucket <LAB_BUCKET> \
  --create-bucket-configuration LocationConstraint=<REGION> \
  --region <REGION> \
  --profile <PROFILE_ADMIN>
# (omit --create-bucket-configuration when region is us-east-1)
```

Verify:
```bash
aws s3api head-bucket --bucket <LAB_BUCKET> --profile <PROFILE_ADMIN>
aws s3 ls --profile <PROFILE_ADMIN>
```

---

## 5) Configure the **Lab** AWS CLI Profile
Set up the profile that uses the **lab user** credentials.

```bash
aws configure --profile <PROFILE_LAB>
# Paste Access Key ID for user boto3-lab-RO
# Paste Secret Access Key
# Default region: <REGION>
# Output: json
```

Verify identity and bucket access:
```bash
aws sts get-caller-identity --profile <PROFILE_LAB>
aws s3api head-bucket --bucket <LAB_BUCKET> --profile <PROFILE_LAB>
aws s3 ls s3://<LAB_BUCKET>/ --recursive --profile <PROFILE_LAB> || true
```

Test put/get:
```bash
echo "Hello from my boto3 lab!" > hello.txt

aws s3 cp hello.txt s3://<LAB_BUCKET>/hello.txt --profile <PROFILE_LAB>

aws s3 cp s3://<LAB_BUCKET>/hello.txt - --profile <PROFILE_LAB>
# Hello from my boto3 lab!
```

---

## 6) Local Lab Layout and Virtualenv
Create a dedicated folder for your project (you used `~/Projects/boto3-lab`).

```bash
mkdir -p "$HOME/Projects/boto3-lab"
cd "$HOME/Projects/boto3-lab"

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip boto3 botocore
printf "boto3>=1.34.98\nbotocore>=1.34.98\n" > requirements.txt
```

---

## 7) Boto3 Script (list buckets + safe logging)
Create `scripts/s3_list_buckets.py` (example):

```python
import boto3, os, sys
from datetime import datetime
from botocore.exceptions import NoCredentialsError, ClientError

def main():
    # Profile is picked up via environment (AWS_PROFILE) or ~/.aws/credentials
    s3 = boto3.client("s3")
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
    out_dir = os.environ.get("BOTO3_LAB_LOG_DIR", os.path.expanduser("~/boto3_lab_logs"))
    os.makedirs(out_dir, exist_ok=True)
    log_path = os.path.join(out_dir, f"s3_buckets_{ts}.log")

    try:
        resp = s3.list_buckets()
        names = [b["Name"] for b in resp.get("Buckets", [])]
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\\n".join(names) if names else "(no buckets found)")
        print(f"Wrote {len(names)} buckets to {log_path}")
    except NoCredentialsError:
        print("ERROR: No AWS credentials found. Run aws configure.", file=sys.stderr); sys.exit(2)
    except ClientError as e:
        print(f"AWS ClientError: {e}", file=sys.stderr); sys.exit(3)

if __name__ == "__main__":
    main()
```

```bash
mkdir -p scripts
# (write the file)
python scripts/s3_list_buckets.py  # with AWS_PROFILE exported or default profile set
```

> Logs are written to: `<HOME>/boto3_lab_logs/s3_buckets_<timestamp>.log`.

---

## 8) Automate Daily Run with `launchctl` (macOS)
Create `~/Library/LaunchAgents/com.boto3lab.example.plist` (mask `<HOME>` below or replace with `$HOME` via `sed`).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.boto3lab.example</string>
  <key>ProgramArguments</key>
  <array>
    <string><HOME>/Projects/boto3-lab/.venv/bin/python</string>
    <string><HOME>/Projects/boto3-lab/scripts/s3_list_buckets.py</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key><string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    <key>BOTO3_LAB_LOG_DIR</key><string><HOME>/boto3_lab_logs</string>
    <key>AWS_PROFILE</key><string><PROFILE_LAB></string>
  </dict>
  <key>StandardOutPath</key><string><HOME>/Library/Logs/boto3lab.out.log</string>
  <key>StandardErrorPath</key><string><HOME>/Library/Logs/boto3lab.err.log</string>
  <key>RunAtLoad</key><true/>
  <key>StartCalendarInterval</key><dict>
    <key>Hour</key><integer>9</integer>
    <key>Minute</key><integer>0</integer>
  </dict>
</dict></plist>
```

Install & start:
```bash
mkdir -p "$HOME/Library/LaunchAgents"
cp com.boto3lab.example.plist "$HOME/Library/LaunchAgents/com.boto3lab.example.plist"

launchctl unload "$HOME/Library/LaunchAgents/com.boto3lab.example.plist" 2>/dev/null || true
launchctl load  "$HOME/Library/LaunchAgents/com.boto3lab.example.plist"
launchctl start com.boto3lab.example

# Verify
launchctl list | grep com.boto3lab.example || true
tail -n 50 "$HOME/Library/Logs/boto3lab.out.log" || true
tail -n 50 "$HOME/Library/Logs/boto3lab.err.log" || true
ls -lt "$HOME/boto3_lab_logs" || true
```

> If you used literal `<HOME>` in the plist, replace with your path using macOS `sed`:
> ```bash
> sed -i '' "s|<HOME>|$HOME|g" "$HOME/Library/LaunchAgents/com.boto3lab.example.plist"
> ```

---

## 9) Verification Checklist
- ✅ `aws sts get-caller-identity --profile <PROFILE_LAB>` shows the lab user ARN
- ✅ `aws s3api head-bucket --bucket <LAB_BUCKET> --profile <PROFILE_LAB>` succeeds
- ✅ You can `aws s3 cp` to/from `s3://<LAB_BUCKET>/`
- ✅ A new log file appears at `<HOME>/boto3_lab_logs/` after manual start or at 09:00 daily
- ✅ `launchctl list | grep com.boto3lab.example` shows the job

---

## 10) Troubleshooting (based on your real logs)

### A) `AccessDenied` on `PutObject`
**Symptom:**
```
An error occurred (AccessDenied) when calling the PutObject operation:
User: arn:aws:iam::<AWS_ACCOUNT_ID>:user/boto3-lab-RO is not authorized to perform: s3:PutObject ...
```
**Fix:** Attach the bucket-scoped RW policy:
```bash
aws iam attach-user-policy \
  --user-name boto3-lab-RO \
  --policy-arn arn:aws:iam::<AWS_ACCOUNT_ID>:policy/Boto3LabS3RW \
  --profile <PROFILE_ADMIN>
```

### B) `HeadBucket` returns 403 vs 404
- **403 Forbidden**: Bucket exists but your principal lacks permission or is in a different AWS account without access.
- **404 Not Found**: Bucket does not exist.
Use `aws s3api head-bucket --bucket <LAB_BUCKET> --profile <PROFILE_LAB>` and verify region/permissions.

### C) “The config profile … could not be found”
You configured `boto3lab` but ran commands with `--profile boto3-lab` (dash vs no dash). Keep the name consistent or export:
```bash
export AWS_PROFILE=<PROFILE_LAB>
```

### D) `zsh: command not found: #` while pasting
You pasted commented lines directly at the prompt. Use a heredoc or run in a script file. Example:
```bash
cat > do_stuff.sh <<'SH'
# comments are fine inside scripts
echo "Hello"
SH
bash do_stuff.sh
```

### E) `sed -i` differences on macOS
Use the BSD syntax:
```bash
sed -i '' "s|FROM|TO|g" file.txt
```

### F) `zsh: command not found: s3api` / `s3`
Always prefix with `aws`:
```bash
aws s3api list-objects-v2 --bucket <LAB_BUCKET>
aws s3 cp file.txt s3://<LAB_BUCKET>/file.txt
```

### G) LaunchAgent unload error / label mismatch
Ensure:
- File is in `~/Library/LaunchAgents`
- `<key>Label</key>` matches the label you start: `com.boto3lab.example`
- Use full path to Python and script in `ProgramArguments`
- Consider `launchctl bootout gui/$(id -u) <plist>` for richer errors

---

## 11) Security Notes
- **Never commit** AWS keys to Git.
- Rotate lab access keys periodically.
- Keep the lab policy **bucket-scoped** and minimal.
- Prefer separate users for RO and RW if you want stricter separation.
- Mask IDs/paths when sharing logs externally.

---

## 12) Appendix – Quick Commands

Create the policy JSON quickly:
```bash
cat > /tmp/boto3-lab-s3-rw.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect": "Allow","Action":"s3:ListAllMyBuckets","Resource":"*"},
    {"Effect": "Allow","Action":"s3:ListBucket","Resource":"arn:aws:s3:::<LAB_BUCKET>"},
    {"Effect": "Allow","Action":["s3:GetObject","s3:PutObject","s3:DeleteObject"],"Resource":"arn:aws:s3:::<LAB_BUCKET>/*"}
  ]
}
EOF
```

List attached user policies:
```bash
aws iam list-attached-user-policies \
  --user-name boto3-lab-RO \
  --profile <PROFILE_ADMIN>
```

Bucket smoke test:
```bash
echo "hi" > /tmp/hi.txt
aws s3 cp /tmp/hi.txt s3://<LAB_BUCKET>/hi.txt --profile <PROFILE_LAB>
aws s3 cp s3://<LAB_BUCKET>/hi.txt - --profile <PROFILE_LAB>
```

---

**End of Guide** – You now have a reproducible, secure setup for your AWS Boto3 lab on macOS.
