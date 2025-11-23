import json
import urllib.parse
import boto3
from boto3.dynamodb.conditions import Key
from text_filler.models import OCRDocument
from text_filler.visualization import visualize_results

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = "diia_hack_requests"
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    print(f"\n===Lambda for Filling===\n")

    bucket = event['bucket']
    raw_key = event['raw_key']
    raw_key = urllib.parse.unquote(raw_key)
    message = event['message']
    result = event['result']
    result_conv = json.loads(result)

    result_with_fields = json.loads(result)
    # result_with_fields['uri'] = 's3://' + event['raw_key']
    # result_with_fields['file_format'] = event['raw_key'].split('.')[-1]
    result_json = json.dumps(result_with_fields['translated_content'])

    print(f"\n===Lambda for Filling===\n")
    print(result)

    print(f"{bucket=} {raw_key=}")
    print(f"{message=}")
    _, email, request_id, filename = raw_key.split("/", 3)

    processed_key = f"processed/{email}/{request_id}/result.pdf"

    print(result_json)

    document = OCRDocument.from_json(result_json)
    try:
        visualize_results(document, processed_key)
    except Exception as e:
        print(e)


    # Update DynamoDB record
    try:
        response = table.update_item(
            Key={"request_id": request_id},
            UpdateExpression="SET #s = :status, s3_output_key = :output_key",
            ExpressionAttributeNames={
                "#s": "status"  # "status" is reserved, must alias
            },
            ExpressionAttributeValues={
                ":status": "COMPLETED",
                ":output_key": processed_key,
            },
            ReturnValues="UPDATED_NEW",
        )
        print("✅ DynamoDB updated:", response)
    except Exception as e:
        print("❌ DynamoDB update failed:", e)
        raise

    return {
        "status": "SUCCESS",
        "s3_input": raw_key,
        "s3_output": processed_key,
        "request_id": request_id,
        "message": "Filler completed"
    }