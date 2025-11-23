import sys
from server import translate_document
from data_models import TranslationRequest
import json
import urllib.parse
import boto3

import asyncio

def lambda_handler(event, context):
    print(f"\n===Lambda for Translation===\n")

    bucket = event.get("bucket")
    raw_key = event.get("raw_key", "")
    raw_key = urllib.parse.unquote(raw_key)
    result = event.get("result", "")
    result_json = json.loads(result)
    incoming_message = event.get("message", "")

    # print(f"OCR Reulst {result}")

    print(f"Incoming message: {incoming_message}")

    document = TranslationRequest(
        source_lang='uk',
        target_lang='en',
        content=result_json,
    )

    # Process
    result_translation = asyncio.run(translate_document(document))

    print(result_translation)

    return {
        "bucket": bucket,
        "raw_key": raw_key,
        "message": "OCR completed",
        "result": result_translation.json()
    }