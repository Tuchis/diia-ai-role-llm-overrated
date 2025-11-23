# OCR Engine

OCR Engine is a vendor-agnostic OCR component of our document translation system. Currently, it supports Amazon Textract and Google Cloud Vision.

## Installation

This module uses `uv` package manager. To install it, run:

```bash
uv sync --frozen
source .venv/bin/activate
```

## Usage

This module is designed to be used in conjunction with the rest of the system. The CLI interface was implemented only for debugging purposes and is not finalized.

To function properly, the OCR Engine requires the following environment variable to be set:

When using **Amazon Textract**:
```sh
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_SESSION_TOKEN=your_session_token
AWS_REGION=your_aws_region
```

When using **Google Cloud Vision**:
```sh
GOOGLE_APPLICATION_CREDENTIALS=your_service_account_json_path
```

## Working principle

The OCR Engine was designed to be vendor agnostic. It provides a unified interface for different OCR vendors and allows for easy switching between them. It uses normalized coordinates for the bounding boxes and polygons of the text, and has a normalized confidence score (which, however, is different between vendors).

The reason for implementing two providers was made due to Cloud Vision's superior support for the Ukrainian language. It also supports setting a language hint, which considerably improves the quality of the OCR results. The difference between the two providers was sometimes night and day. For example, Textract would often replace small Cyryllic letters with their capitalized Latin lookalikes, which greatly affected the quality of the OCR results. 
