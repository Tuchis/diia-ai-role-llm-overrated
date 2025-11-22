import click
from pathlib import Path
from dotenv import load_dotenv
from . import OCREngine, TextractOCRProvider, visualize_results

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
    # Normalize to URI
    if "://" not in uri_or_path:
        uri = Path(uri_or_path).absolute().as_uri()
    else:
        uri = uri_or_path

    # Configure provider
    provider = TextractOCRProvider()
    engine = OCREngine(provider=provider)
    
    # Process
    try:
        document = engine.process(uri)
        
        # Output JSON (excluding image bytes)
        print(document.model_dump_json(indent=2))

        if visualize:
            visualize_results(document)

    except Exception as e:
        click.echo(f"Error processing document: {e}", err=True)

if __name__ == "__main__":
    process()
