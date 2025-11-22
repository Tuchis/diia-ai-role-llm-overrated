from typing import Any

def extract_all_text(data: Any, ignore_keys: list[str]) -> list[str]:
    """
    Recursively extracts all translatable strings from the JSON structure
    to form a single context for validation.
    """
    texts = []
    if isinstance(data, dict):
        for k, v in data.items():
            if k not in ignore_keys:
                texts.extend(extract_all_text(v, ignore_keys))
    elif isinstance(data, list):
        for item in data:
            texts.extend(extract_all_text(item, ignore_keys))
    elif isinstance(data, str):
        # Apply the same heuristic as the translator: skip empty or numeric
        if data.strip() and not data.isnumeric():
            texts.append(data)
    return texts
