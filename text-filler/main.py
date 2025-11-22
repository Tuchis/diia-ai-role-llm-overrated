import click
from pathlib import Path
from dotenv import load_dotenv
from ocr_engine import OCREngine, TextractOCRProvider
from text_filler.visualization import visualize_results
from text_filler.models import OCRDocument
load_dotenv()

@click.command()
@click.argument("document_manifest", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--visualize",
    is_flag=True,
    help="Visualize the results with bounding boxes.",
)
def process(document_manifest: Path, visualize: bool):
    """
    Process a document and perform OCR.
    """
    with open(document_manifest, "r") as f:
        document = OCRDocument.from_json(f.read())

    visualize_results(document, document_manifest.with_suffix(".pdf"))


if __name__ == "__main__":
    process()
