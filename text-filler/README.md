# Text Filler

Text filler is the component of the system responsible for masking the source language text and inserting the translated text.

## Installation

This module uses `uv` package manager. To install it, run:

```bash
uv sync --frozen
source .venv/bin/activate
```

## Usage

This module is designed to be used in conjunction with the rest of the system. The CLI interface was implemented onlu for debugging purposes and is not finalized.

## Working principle

The text filler module has two responsibilities:

1. Masking the source language text
2. Inserting the translated text

Here is the high-level overview of two modules:

### Masking

The masking module is responsible for masking the source language text. It uses classical computer vision techniques to separate the text from the background and then applies a mask to the text. The mask is generated using on of the `BackgroundInpainter` classes. Then there is some postprocessing to prevent, for example, the table edges from being masked. After that, the image is inpainted in the masking regions using the OpenCV inpainting algorithm.

As a result, we get a clean canvas to put the translated text on.

### Translated text insertion

Text inserter module has to be able to insert the translated text into the image. It's a tricky problem to solve when switching languages, as different languages convey the same idea in varying amounts of text. Therefore, a big chunk of work that text inserter has to do is to find a proper-looking font size and position for the translated text. 

Results are then rendered into a PDF file, while keeping the original background, structure, images and other elements intact.
