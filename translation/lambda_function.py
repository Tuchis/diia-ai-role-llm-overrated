import sys
from http.client import HTTPException

from server import translate_document
from data_models import TranslationRequest
import json
import urllib.parse

import asyncio


import boto3


dynamodb = boto3.resource("dynamodb")
TABLE_NAME = "diia_hack_requests"
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    print(f"\n===Lambda for Translation===\n")

    bucket = event.get("bucket")
    raw_key = event.get("raw_key", "")
    raw_key = urllib.parse.unquote(raw_key)
    result = event.get("result", "")
    result_json = json.loads(result)
    incoming_message = event.get("message", "")

    _, email, request_id, filename = raw_key.split("/", 3)

    # print(f"OCR Reulst {result}")

    print(f"Incoming message: {incoming_message}")

    try:
        document = TranslationRequest(
            source_lang='uk',
            target_lang='en',
            content=result_json,
        )

        # Process
        result_translation = asyncio.run(translate_document(document, raw_key))
    except Exception as ex:
        response = table.update_item(
            Key={"request_id": request_id},
            UpdateExpression="SET #s = :status",
            ExpressionAttributeNames={
                "#s": "status"  # "status" is reserved, must alias
            },
            ExpressionAttributeValues={
                ":status": "FAILED",
            },
            ReturnValues="UPDATED_NEW",
        )
        raise HTTPException(status_code=500, detail=str(ex))

    print(f"{result_translation}")
    print(f"{result}")

    return {
        "bucket": bucket,
        "raw_key": raw_key,
        "message": "OCR completed",
        "result": result_translation.json(),
        "previous": result
    }