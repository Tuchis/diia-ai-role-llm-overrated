import rootutils

path = rootutils.find_root(search_from=__file__, indicator=".project-root")

import click
from pathlib import Path
from dotenv import load_dotenv
from ocr_engine import OCREngine, TextractOCRProvider, CloudVisionOCRProvider, visualize_results

load_dotenv()


def process(uri_or_path, visualize, provider, output, debug=False):
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

    if not debug:
        return json_output

    # Output JSON (excluding image bytes)
    json_output = document.model_dump_json(indent=2)

    if output:
        with open(output, "w") as f:
            f.write(json_output)
        click.echo(f"Output written to {output}")
    else:
        print(json_output)

    if visualize:
        visualize_results(document)


@click.command()
@click.argument(
    "uri_or_path", required=True, type=click.Path(exists=True)
)
@click.option("--visualize", is_flag=True, help="Visualize results")
@click.option(
    "--provider", default="textract", help="OCR provider (textract or google)"
)
@click.option(
    "--output", type=click.Path(path_type=Path), help="Output file for JSON results"
)
def main(uri_or_path, visualize, provider, output):
    process(uri_or_path, visualize, provider, output, debug=True)


if __name__ == "__main__":
    main()
