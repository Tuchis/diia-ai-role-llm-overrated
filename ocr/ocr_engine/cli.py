
import rootutils

path = rootutils.find_root(search_from=__file__, indicator=".project-root")

import click
from pathlib import Path
from dotenv import load_dotenv
from ocr_engine import OCREngine, TextractOCRProvider, CloudVisionOCRProvider, visualize_results

load_dotenv()

def process(uri_or_path, visualize, provider, output):
    """
    Process a document and perform OCR.
    """
    # Normalize to URI
    if "://" not in uri_or_path:
        uri = Path(uri_or_path).absolute().as_uri()
    else:
        uri = uri_or_path

    print(uri)

    # Configure provider
    if provider == "google":
        ocr_provider = CloudVisionOCRProvider()
    else:
        ocr_provider = TextractOCRProvider()

    engine = OCREngine(provider=ocr_provider)
    
    # Process
    document = engine.process(uri)

    json_output = document.model_dump_json(indent=2)

    return json_output

    # Output JSON (excluding image bytes)
    json_output = document.model_dump_json(indent=2)
    
    if output:
        output.write_text(json_output, encoding="utf-8")
        click.echo(f"Output written to {output}")
    else:
        print(json_output)

    if visualize:
        visualize_results(document)


if __name__ == "__main__":
    process()
