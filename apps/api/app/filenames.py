"""The .csv extension rule, shared by the upload validation and the report download name."""

CSV_EXTENSION = ".csv"


def is_csv(filename: str) -> bool:
    return filename.lower().endswith(CSV_EXTENSION)


def csv_stem(filename: str) -> str:
    """The filename without its final .csv extension, whatever its case."""
    return filename[: -len(CSV_EXTENSION)] if is_csv(filename) else filename
