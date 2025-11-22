import click
from pathlib import Path
from dotenv import load_dotenv
from ocr_engine import OCREngine, TextractOCRProvider
from text_filler.visualization import visualize_results
from text_filler.models import OCRDocument
load_dotenv()

@click.command()
@click.argument("uri_or_path")
@click.option(
    "--visualize",
    is_flag=True,
    help="Visualize the results with bounding boxes.",
)
def process(uri_or_path, visualize):
    """
    Process a document and perform OCR.
    """
    # # Normalize to URI
    # if "://" not in uri_or_path:
    #     uri = Path(uri_or_path).absolute().as_uri()
    # else:
    #     uri = uri_or_path

    # # Configure provider
    # provider = TextractOCRProvider()
    # engine = OCREngine(provider=provider)
    
    # # Process
    # document = engine.process(uri)

    # with open("output.json", "w") as f:
    #     f.write(document.to_json())

    with open("test-google.json", "r") as f:
        document = OCRDocument.from_json(f.read())
    
    # Output JSON (excluding image bytes)
    print(document.model_dump_json(indent=2))

    if visualize:
        visualize_results(document)


if __name__ == "__main__":
    process()
