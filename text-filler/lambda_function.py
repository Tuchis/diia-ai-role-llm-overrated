import json
import urllib.parse
import boto3
from boto3.dynamodb.conditions import Key
from text_filler.models import OCRDocument
from text_filler.visualization import visualize_results

dynamodb = boto3.resource("dynamodb")
s3_client = boto3.client("s3")
TABLE_NAME = "diia_hack_requests"
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    print(f"\n===Lambda for Filling===\n")

    print(event)

    bucket = event['bucket']
    raw_key = event['raw_key']
    raw_key = urllib.parse.unquote(raw_key)
    intermediate_key = event['intermediate_key']
    message = event['message']

    # Read translation result from S3
    print(f"Reading translation result from S3: s3://{bucket}/{intermediate_key}")
    response = s3_client.get_object(Bucket=bucket, Key=intermediate_key)
    result = response['Body'].read().decode('utf-8')

    result_with_fields = json.loads(result)
    # result_with_fields['uri'] = 's3://' + event['raw_key']
    # result_with_fields['file_format'] = event['raw_key'].split('.')[-1]
    result_json = json.dumps(result_with_fields['translated_content'])

    print(f"\n===Lambda for Filling===\n")
    print(f"Translation result size: {len(result)} bytes")

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