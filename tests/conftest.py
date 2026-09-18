import sys

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


class FakePage:

    def __init__(self, text):
        self._text = text

    def extract_text(self):
        return self._text


class FakeReader:

    def __init__(self, page_texts):
        self.pages = [FakePage(text) for text in page_texts]
