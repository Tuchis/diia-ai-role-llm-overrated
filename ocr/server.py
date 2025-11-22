import uvicorn
from fastapi import FastAPI, HTTPException
import logging
import rootutils

path = rootutils.find_root(search_from=__file__, indicator=".project-root")

from pathlib import Path
from dotenv import load_dotenv
from ocr_engine import OCREngine, TextractOCRProvider, CloudVisionOCRProvider
from ocr_engine.data_models import OCRRequest

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OCR Service",
    description="A microservice that accepts document URIs and extracts text using OCR providers.",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ocr-service"}

@app.post("/process")
async def process_document(request: OCRRequest):
    try:
        if "://" not in request.uri:
            uri = Path(request.uri).absolute().as_uri()
        else:
            uri = request.uri

        if request.provider == "google":
            ocr_provider = CloudVisionOCRProvider()
        else:
            ocr_provider = TextractOCRProvider()

        engine = OCREngine(provider=ocr_provider)

        document = engine.process(uri)

        return document.model_dump(mode='json')

    except Exception as e:
        logger.error(f"OCR Processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OCR Error: {str(e)}")

if __name__ == "__main__":
    print("Starting OCR Microservice on http://localhost:6666")
    uvicorn.run(app, host="0.0.0.0", port=6666)
