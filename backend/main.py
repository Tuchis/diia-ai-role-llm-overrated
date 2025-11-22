# main.py
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import services
import requests  # To call the Core AI service

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


class UploadRequest(BaseModel):
    filename: str
    file_type: str  # e.g., "application/pdf"
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


@app.post("/documents/upload-url")
def get_upload_url(req: UploadRequest, user=Depends(get_current_user)):
    """
    Step 1 of Translation: Get a URL to upload the file to S3.
    """
    data = services.generate_presigned_upload_url(
        user['email'], req.filename, req.file_type
    )

    if not data:
        raise HTTPException(status_code=500, detail="Could not generate URL")

    # Create the initial DB record
    services.create_translation_request(
        user['email'], data['request_id'], data['s3_key'], req.document_type
    )

    return data


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