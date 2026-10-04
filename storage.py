import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_ROOT = PROJECT_ROOT / "data_lake" / "raw"


def save_to_local_lake(data: dict[str, Any], source: str, filename: str) -> str:
    """Write a payload to the Bronze/raw layer without transforming its values."""
    if not source or Path(source).name != source:
        raise ValueError("source must be a simple directory name")
    if not filename or Path(filename).name != filename:
        raise ValueError("filename must be a simple file name")

    folder_path = RAW_ROOT / source
    folder_path.mkdir(parents=True, exist_ok=True)
    file_path = folder_path / filename

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False, default=str)
        file.write("\n")

    print(f"Saved raw data: {file_path.relative_to(PROJECT_ROOT)}")
    return str(file_path)
