import re


class Formatter:
    """Whitespace-only cleanup; punctuation and token spelling are preserved."""

    ABBREVIATIONS = {"mr.", "mrs.", "ms.", "dr.", "prof.", "sr.", "jr.",
                     "st.", "vs.", "etc.", "e.g.", "i.e."}

    @staticmethod
    def clean(text: str) -> str:
        paragraphs = []
        # Retain explicit paragraphs; ASR's single newlines become spaces.
        for block in re.split(r"\n\s*\n", text.strip()):
            current, sentences, length = [], 0, 0
            for word in block.split():
                current.append(word)
                length += len(word) + 1
                tail = word.rstrip('\"\'”’)]}')
                abbreviation = (tail.lower() in Formatter.ABBREVIATIONS
                                or bool(re.fullmatch(r"(?:[A-Za-z]\.)+", tail)))
                boundary = tail.endswith((".", "!", "?", "。", "！", "？")) and not abbreviation
                if boundary:
                    sentences += 1
                # Prefer sentence boundaries; cap unpunctuated speech at a word
                # boundary. Never edit the inside of a URL/email/number.
                if (boundary and (sentences >= 4 or length >= 600)) or length >= 1200:
                    paragraphs.append(" ".join(current))
                    current, sentences, length = [], 0, 0
            if current:
                paragraphs.append(" ".join(current))
        return "\n\n".join(paragraphs)
