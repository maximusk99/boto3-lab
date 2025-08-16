import boto3
import os

# Use your named profile
session = boto3.Session(profile_name="boto3-lab")  # remove profile_name if using default

s3 = session.client("s3")

# 1) List buckets (proves auth)
resp = s3.list_buckets()
print("Buckets:")
for b in resp.get("Buckets", []):
    print(" -", b["Name"])

# 2) Read a small object
bucket = os.environ.get("LAB_BUCKET", "YOUR-LAB-BUCKET")
key = os.environ.get("LAB_KEY", "hello.txt")

try:
    obj = s3.get_object(Bucket=bucket, Key=key)
    body = obj["Body"].read().decode("utf-8")
    print(f"\nContents of s3://{bucket}/{key}:\n{body}")
except s3.exceptions.NoSuchKey:
    print(f"Object not found: s3://{bucket}/{key}")
