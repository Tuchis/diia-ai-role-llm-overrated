import click
import os
from dotenv import load_dotenv
from ocr_engine import process_document, visualize_results

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
    result = process_document(file_path)
    print(result.model_dump_json(indent=2))

    if visualize:
        visualize_results(file_path, result)


if __name__ == "__main__":
    process()
