import boto3, os

session = boto3.Session(profile_name="boto3-lab")  # or drop profile_name if using default
s3 = session.client("s3")

resp = s3.list_buckets()
print("Buckets:")
for b in resp.get("Buckets", []):
    print(" -", b["Name"])

bucket = os.environ.get("LAB_BUCKET", "YOUR-LAB-BUCKET")
key = os.environ.get("LAB_KEY", "hello.txt")

try:
    obj = s3.get_object(Bucket=bucket, Key=key)
    print(f"\nContents of s3://{bucket}/{key}:\n{obj['Body'].read().decode('utf-8')}")
except s3.exceptions.NoSuchKey:
    print(f"Object not found: s3://{bucket}/{key}")
