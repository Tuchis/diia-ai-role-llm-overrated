# main.py
from fastapi import FastAPI, HTTPException, Header, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import services
import requests  # To call the Core AI service
import io

app = FastAPI(title="Diia Translation Service MVP")

# Allow your frontend to talk to your backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:80",
        "http://127.0.0.1:80",
        "http://localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- DATA MODELS ---
class AuthRequest(BaseModel):
    token: str  # The Google ID Token from frontend


class DocumentMetadata(BaseModel):
    document_type: str  # e.g., "birth_certificate"


# --- DEPENDENCIES ---
async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Validates the Bearer token in the header for every protected request.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer Token")

    token = authorization.split(" ")[1]
    user_data = services.verify_google_token(token)

    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid Google Token")

    return user_data


# --- ROUTES ---

@app.post("/auth/login")
def login(auth: AuthRequest):
    """
    Frontend sends Google Token -> Backend verifies -> Returns User Profile.
    """
    user_data = services.verify_google_token(auth.token)
    if not user_data:
        raise HTTPException(status_code=400, detail="Invalid Token")

    # Sync with DB
    db_user = services.get_or_create_user(user_data)
    return {"message": "Login successful", "user": db_user}


@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = "custom_upload",
    user=Depends(get_current_user)
):
    """
    Upload a document directly to the backend, which then uploads to S3.
    """
    # Read file content
    file_content = await file.read()

    # Upload to S3 through backend
    result = services.upload_file_to_s3(
        user['email'],
        file.filename,
        file.content_type,
        file_content
    )

    if not result:
        raise HTTPException(status_code=500, detail="Could not upload file")

    # Create the initial DB record
    services.create_translation_request(
        user['email'],
        result['request_id'],
        result['s3_key'],
        document_type
    )

    return {
        "request_id": result['request_id'],
        "status": "UPLOADED",
        "message": "File uploaded successfully"
    }


@app.post("/documents/{request_id}/start")
def start_processing(request_id: str, user=Depends(get_current_user)):
    """
    Step 2: Frontend confirms upload is done. We trigger the AI Core.
    """
    # 1. Update DB status
    services.requests_table.update_item(
        Key={'request_id': request_id},
        UpdateExpression="set #s = :status",
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={':status': 'PROCESSING'}
    )

    # 2. Trigger AI Core (Fire and forget, or async)
    # In a real app, use SQS. For hackathon, just call the endpoint.
    try:
        # Imagine this calls your GPU server
        # requests.post(settings.CORE_AI_URL + "/process", json={"request_id": request_id})
        pass
    except:
        pass  # Don't fail if AI service is down, we are just mocking the trigger

    return {"status": "PROCESSING", "message": "Sent to AI Core"}


@app.get("/documents/{request_id}")
def check_status(request_id: str, user=Depends(get_current_user)):
    """
    Step 3: Polling. Frontend checks this every 2 seconds.
    """
    item = services.get_request_status(request_id)
    if not item:
        raise HTTPException(status_code=404, detail="Request not found")

    # If done, generate a download link
    download_url = None
    if item.get('status') == 'COMPLETED' and item.get('s3_output_key'):
        download_url = services.generate_presigned_download_url(item['s3_output_key'])

    return {
        "status": item.get('status'),
        "download_url": download_url
    }


@app.get("/documents/{request_id}/download/original")
def download_original(request_id: str, user=Depends(get_current_user)):
    """
    Download the original document for a request.
    """
    item = services.get_request_status(request_id)
    if not item:
        raise HTTPException(status_code=404, detail="Request not found")

    # Verify ownership
    if item.get('user_email') != user['email']:
        raise HTTPException(status_code=403, detail="Access denied")

    s3_key = item.get('s3_input_key')
    if not s3_key:
        raise HTTPException(status_code=404, detail="Original document not found")

    # Download from S3
    file_data = services.download_file_from_s3(s3_key)
    if not file_data:
        raise HTTPException(status_code=500, detail="Failed to download file")

    return StreamingResponse(
        io.BytesIO(file_data['content']),
        media_type=file_data['content_type'],
        headers={
            "Content-Disposition": f"attachment; filename={file_data['filename']}"
        }
    )


@app.get("/documents/{request_id}/download/translated")
def download_translated(request_id: str, user=Depends(get_current_user)):
    """
    Download the translated document for a request.
    """
    item = services.get_request_status(request_id)
    if not item:
        raise HTTPException(status_code=404, detail="Request not found")

    # Verify ownership
    if item.get('user_email') != user['email']:
        raise HTTPException(status_code=403, detail="Access denied")

    if item.get('status') != 'COMPLETED':
        raise HTTPException(status_code=400, detail="Translation not yet completed")

    s3_key = item.get('s3_output_key')
    if not s3_key:
        raise HTTPException(status_code=404, detail="Translated document not found")

    # Download from S3
    file_data = services.download_file_from_s3(s3_key)
    if not file_data:
        raise HTTPException(status_code=500, detail="Failed to download file")

    return StreamingResponse(
        io.BytesIO(file_data['content']),
        media_type=file_data['content_type'],
        headers={
            "Content-Disposition": f"attachment; filename={file_data['filename']}"
        }
    )


@app.get("/documents")
def get_user_documents(user=Depends(get_current_user)):
    """
    Fetch all documents for the authenticated user.
    """
    documents = services.get_user_documents(user['email'])

    # Transform to frontend-friendly format
    result = []
    for doc in documents:
        item = {
            "id": doc.get('request_id'),
            "title": doc.get('document_type', 'Document').replace('_', ' ').title(),
            "type": doc.get('document_type', 'Unknown'),
            "date": doc.get('created_at'),
            "status": doc.get('status', 'UNKNOWN').lower(),
            "s3_input_key": doc.get('s3_input_key'),
            "s3_output_key": doc.get('s3_output_key'),
        }

        # Generate download endpoint URLs instead of presigned URLs
        if doc.get('s3_input_key'):
            item['original_url'] = f"/documents/{doc.get('request_id')}/download/original"

        if doc.get('status') == 'COMPLETED' and doc.get('s3_output_key'):
            item['translated_url'] = f"/documents/{doc.get('request_id')}/download/translated"

        result.append(item)

    return {"documents": result}