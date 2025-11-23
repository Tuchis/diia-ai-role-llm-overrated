import sys
from ocr_engine.cli import process
import json
import urllib.parse
import boto3


def lambda_handler(event, context):
    print(f"\n===Lambda for OCR===\n")

    bucket = event.get("bucket")
    raw_key = event.get("raw_key", "")
    raw_key = urllib.parse.unquote(raw_key)
    incoming_message = event.get("message", "")

    uri = f"s3://{bucket}/{raw_key.lstrip('/')}"

    print(f"Bucket: {bucket}")
    print(f"Raw Key: {raw_key=}, {uri=}")
    print(f"Incoming message: {incoming_message}")

    # Process
    result = process(uri, False, 'textract', incoming_message)

    return {
        "bucket": bucket,
        "raw_key": raw_key,
        "message": "OCR completed",
        "result": result,
    }