from __future__ import annotations

# from bs4.dammit import UnicodeDammit
from os import PathLike

from .parse.dammit import UnicodeDammit
from typing import TextIO, Generator
import pathlib

from .wrappers import gen_to_textio

_en_smart_re = {
    u"\u201c": '"',
    u"\u201d": '"',
    u"\u2018": "'",
    u"\u2019": "'",
    u"\u2026": '...',
}


def uread(file: str | bytes | PathLike[str], to_ascii: str = 'Smart',
          escape_files: str | None = '.csv', new_quote_escape: str = '"') -> TextIO:
    """
    Context Manager for reading a file of unknown encoding as unicode.

    :param file: Path to file to read
    :param new_quote_escape: Escape char for converted ascii quotes
    :param to_ascii: Convert to ascii
    :param escape_files: File Extensions to escape converted quotes (Use | to delimit multiple extensions)
    :param new_quote_escape: Escape char for converted ascii quotes (Default: '"' (Double Quote)))

    to_ascii modes:
    - 'Smart': Converts smart quotes to ascii
    - 'All': Convert smart quotes, then drops all non-ascii chars
    - 'None': No conversion
    """
    with URead(file, to_ascii, escape_files, new_quote_escape) as f:
        return f


class URead:
    def __init__(self, file: str | bytes | PathLike[str], to_ascii: str = 'Smart',
                 escape_files: str | None = '.csv', new_quote_escape: str = '"'):
        """
        Context Manager for reading a file of unknown encoding as unicode.

        :param file: Path to file to read
        :param new_quote_escape: Escape char for converted ascii quotes
        :param to_ascii: Convert to ascii
        :param escape_files: File Extensions to escape converted quotes (Use | to delimit multiple extensions)
        :param new_quote_escape: Escape char for converted ascii quotes (Default: '"' (Double Quote)))

        to_ascii modes:
        - 'Smart': Converts smart quotes to ascii
        - 'All': Convert smart quotes, then drops all non-ascii chars
        - 'None': No conversion
        """
        self.file_path = file
        self.to_ascii = to_ascii
        self.escape_char = new_quote_escape
        self.dict = _en_smart_re

        if escape_files:  # Escape quotes in these files
            esc_files_set = set(escape_files.split('|'))
            # Modify the dictionary if reading csv
            ext = pathlib.Path(file).suffix
            if ext in esc_files_set and self.escape_char:
                self.dict[u"\u201c"] = self.escape_char + '"'
                self.dict[u"\u201d"] = self.escape_char + '"'

    def convert_smart(self, line: str) -> str:
        """
        Converts utf-8 smart quotes and ellipses to ascii
        Input string must already be in utf-8, not windows-1252

        :param line: String
        :return: Converted String
        """
        table = line.maketrans(self.dict)
        return line.translate(table)

    def _parse(self, line: bytes) -> bytes:
        # Decode the bytes using chardet
        decoded = UnicodeDammit(line)
        # Print encoding
        encoding = decoded.original_encoding

        # If ascii, return directly
        if encoding == 'ascii':
            return decoded.unicode_markup.encode('utf-8')

        # If encoding is not ascii, detwingle to convert windows-1252 if present
        detwingled = UnicodeDammit.detwingle(line)  # Detwingled UTF-8 bytes

        # If '1252' mode, return det_uni directly
        if self.to_ascii.lower() == 'smart':
            return self.convert_smart(detwingled.decode('utf-8')).encode('utf-8')

        # For 'All', also remove all non-ascii chars at this point
        elif self.to_ascii.lower() == 'all':
            # Attempt lossy convert to ascii then back to filter out non-ascii
            return detwingled.decode('utf-8').encode('ascii', 'ignore')

        # For any other option, return as utf-8 byte-string
        return detwingled

    def _as_iter(self) -> Generator[bytes]:
        with open(self.file_path, 'rb') as f:
            for line in f:
                yield self._parse(line)

    def __enter__(self) -> TextIO:
        return gen_to_textio(self._as_iter())

    def __exit__(self, exc_type, exc_value, traceback):
        return
