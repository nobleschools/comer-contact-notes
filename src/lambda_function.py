"""
comer_contact_notes/src/lambda_function.py

Lambda wrapper for upload_contact_notes. Creates Contact Notes at Noble where
necessary, and saves the resulting match file to an S3 bucket.
"""

from base64 import urlsafe_b64decode
import os
import urllib

import boto3

from src import upload_contact_notes

BUCKET_NAME = os.environ["BUCKET_NAME"]
REPORTS_DIR = os.environ["REPORTS_DIR"]
TMP_DIR = "/tmp"

# decrypt env vars once here so they're available to subsequent lambda
# calls on same container
env_vars = (
    "PAPERTRAIL_HOST",
    "PAPERTRAIL_PORT",
    "SF_LIVE_PASSWORD",
    "SF_LIVE_TOKEN",
)

for var in env_vars:
    encrypted = os.environ[var]
    decrypted = boto3.client("kms").decrypt(
        CiphertextBlob=urlsafe_b64decode(encrypted)
    )["Plaintext"]
    os.environ[var] = decrypted.decode()


def lambda_handler(event, context):
    """Download the input file to the container, process the contact notes
    from the file, and then push the resulting match file to an S3 bucket.

    :param event: dict AWS event source dict
    :param context: LambdaContext object
    """
    local_upload_filepath = "/tmp/for_upload.csv"
    # file path will have been made URL-safe
    file_key = urllib.parse.unquote_plus(
        event["Records"][0]["s3"]["object"]["key"]
    )
    uploaded_file = boto3.resource("s3").Object(BUCKET_NAME, file_key)
    uploaded_file.download_file(local_upload_filepath)

    report_path = upload_contact_notes(local_upload_filepath, TMP_DIR)

    push_to_s3(report_path, BUCKET_NAME)


def push_to_s3(file_path, bucket_name):
    """Push the file at file_path to the s3 bucket_name.

    :param file_path: str path to file to be uploaded (should be in /tmp/)
    :param bucket_name: str name of bucket to push file to
    :return: None
    :rtype: None
    """
    file_name = file_path.split("/")[-1]
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(bucket_name)
    file_dest = os.path.join(REPORTS_DIR, file_name)
    bucket.upload_file(Key=file_dest, Filename=file_path)


if __name__ == "__main__":
    pass
