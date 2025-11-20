import openai
import base64
import os
import argparse

API_KEY = os.getenv("AIRUN_API_KEY")
DEFAULT_MODEL_NAME = "gemini-2.5-flash"
MODEL_CHOICES = [
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-5-nano-2025-08-07",
    "gemini-2.5-flash",
    "claude-4-5-haiku",
    "codemie-text-embedding-ada-002"
]

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

client = openai.AzureOpenAI(
    api_key=API_KEY,
    azure_endpoint="https://codemie.lab.epam.com/llms",
    api_version="2024-02-01"
)

def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Call CodeMie/AIRUN endpoint")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL_NAME, choices=MODEL_CHOICES, required=False, help="Model name")
    return parser.parse_args()

def main(args: argparse.Namespace):
    response = client.chat.completions.create(
        model=args.model,
        messages=[
            {"role": "user", "content": "Translate this text to English:\nХто тримає цей район?"}
        ]
    )
    print(response)

if __name__ == "__main__":
    args = get_args()
    main(args)
