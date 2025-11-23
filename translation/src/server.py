import logging
import os
import uvicorn
import uuid
from fastapi import FastAPI, HTTPException, BackgroundTasks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from data_models import TranslationResponse, TranslationRequest
from engine import TranslationEngine, AIRUN_ENDPOINT
from helper import extract_all_text
from injection_detector import is_prompt_injected

engine = TranslationEngine()


async def translate_document(request: TranslationRequest):
    """
    Receives a JSON document, recursively translates its content,
    and returns the preserved structure with translated values.
    """
    logger.info(f"Received translation request: {request.source_lang} -> {request.target_lang} using {request.model}")

    try:
        all_text_list = extract_all_text(request.content, request.ignore_keys)
        concatenated_text = " ".join(all_text_list)

        if is_prompt_injected(concatenated_text):
            #TODO change DynamoDB
             logger.warning("Request blocked by prompt injection check.")
             raise HTTPException(status_code=400, detail="Content blocked by security policies.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Injection check processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Security check processing error: {str(e)}")

    try:
        translated_data = await engine.process_document(
            request.content, 
            request.source_lang, 
            request.target_lang,
            request.model,
            request.ignore_keys
        )

        return TranslationResponse(
            job_id=f"job_{str(uuid.uuid4())}",
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            translated_content=translated_data,
            initial_content=request.content
        )

    except Exception as e:
        logger.error(f"Translation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal translation processing error")

async def get_languages():
    return {
        "uk": "Ukrainian",
        "en": "English",
        "de": "German",
        "pl": "Polish",
        "es": "Spanish"
    }

