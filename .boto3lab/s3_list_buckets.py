#!/usr/bin/env python3
"""List S3 buckets and write them to a timestamped log file."""
import os, sys
from datetime import datetime
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

def main():
    profile = sys.argv[1] if len(sys.argv) > 1 else None
    if profile:
        import boto3.session
        session = boto3.session.Session(profile_name=profile)
        s3 = session.client("s3")
    else:
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
        print("ERROR: No AWS credentials found. Run `aws configure`.", file=sys.stderr); sys.exit(2)
    except ClientError as e:
        print(f"AWS ClientError: {e}", file=sys.stderr); sys.exit(3)

if __name__ == "__main__":
    main()
