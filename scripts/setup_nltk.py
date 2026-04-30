import nltk


def main() -> None:
    for resource in ("stopwords", "wordnet", "omw-1.4"):
        nltk.download(resource)


if __name__ == "__main__":
    main()
