import click
from dotenv import load_dotenv
from ocr_engine import OCREngine, TextractOCRProvider, visualize_results

load_dotenv()

@click.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--visualize",
    is_flag=True,
    help="Visualize the results with bounding boxes.",
)
def process(file_path, visualize):
    """
    Process a document and perform OCR.
    """
    # Configure provider
    provider = TextractOCRProvider()
    engine = OCREngine(provider=provider)
    
    # Process
    try:
        document = engine.process(file_path)
        
        # Output JSON (excluding image bytes)
        print(document.model_dump_json(indent=2))

        if visualize:
            visualize_results(document)

    except Exception as e:
        click.echo(f"Error processing document: {e}", err=True)

if __name__ == "__main__":
    process()
