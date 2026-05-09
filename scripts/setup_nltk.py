import os
from pathlib import Path

import nltk


def main() -> None:
    download_dir = Path(os.environ.get("NLTK_DATA", "/usr/local/share/nltk_data"))
    download_dir.mkdir(parents=True, exist_ok=True)

    for resource in ("stopwords", "wordnet", "omw-1.4"):
        nltk.download(resource, download_dir=str(download_dir))


if __name__ == "__main__":
    main()
