from __future__ import annotations

# from bs4.dammit import UnicodeDammit
import os
from os import PathLike

import cchardet as chardet

from .parse.dammit import UnicodeDammit
from typing import TextIO, Generator

from .wrappers import gen_to_textio

# UTF-8 Encoded Smart Quotes to ASCII
_en_smart_re = {
    u"\u201c": '"',
    u"\u201d": '"',
    u"\u2018": "'",
    u"\u2019": "'",
    u"\u2026": '...',
}

# UTF-8 Smart Quote Bytes to ASCII
_en_smart_re_bytes = {
    b"\xe2\x80\x9c": b'"',  # U+201C Left Double Quotation Mark
    b"\xe2\x80\x9d": b'"',  # U+201D Right Double Quotation Mark
    b"\xe2\x80\x98": b"'",  # U+2018 Left Single Quotation Mark
    b"\xe2\x80\x99": b"'",  # U+2019 Right Single Quotation Mark
}

_win_encodings = {
    'WINDOWS-1250',
    'WINDOWS-1251',
    'WINDOWS-1252',
    'WINDOWS-1253',
    'WINDOWS-1255',
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
    def __init__(self, file: str | bytes | PathLike[str], to_ascii: str = 'None',
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
        self.file = file
        self.to_ascii = to_ascii
        self.escape_char = new_quote_escape
        self.dict = _en_smart_re
        self.byte_dict = _en_smart_re_bytes

        if isinstance(file, bytes):
            return

        if escape_files and self.escape_char:  # Escape quotes in these files
            esc_files_set = set(escape_files.split('|'))
            # Modify the dictionary if reading csv
            ext = os.path.splitext(file)[1]
            if ext in esc_files_set:
                self.dict[u"\u201c"] = self.escape_char + '"'
                self.dict[u"\u201d"] = self.escape_char + '"'
                self.byte_dict[b"\xe2\x80\x9c"] = self.escape_char.encode('utf-8') + b'"'
                self.byte_dict[b"\xe2\x80\x9d"] = self.escape_char.encode('utf-8') + b'"'

    def convert_smart(self, line: str) -> str:
        """
        Converts utf-8 smart quotes and ellipses to ascii
        Input string must already be in utf-8, not windows-1252

        :param line: String
        :return: Converted String
        """
        table = line.maketrans(self.dict)
        return line.translate(table)

    def convert_smart_b(self, line: bytes) -> bytes:
        """
        Converts utf-8 smart quotes and ellipses to ascii

        :param line: Byte String in UTF-8
        :return: Converted Byte String
        """
        for k, v in self.byte_dict.items():
            line = line.replace(k, v)
        return line

    def _parse(self, line: bytes) -> bytes:
        # Return directly if ascii
        try:
            line.decode('ascii', errors='strict')
            return line
        except UnicodeDecodeError:
            pass
        # Detect the line encoding using cchardet
        detect = chardet.detect(line)

        # If UTF-8, return directly
        if detect['encoding'] == 'UTF-8' and detect['confidence'] > 0.9:
            if self.to_ascii.lower() == 'smart':
                return self.convert_smart_b(line)
            elif self.to_ascii.lower() == 'all':
                return self.convert_smart_b(line).decode('utf-8').encode('ascii', errors='ignore')
            else:
                return line

        # If windows-1252 in results, we need to detwingle
        elif detect['encoding'] in _win_encodings:
            detwingled = UnicodeDammit.detwingle(line)  # Detwingle the line
            # Convert smart quotes to ascii
            if self.to_ascii.lower() == 'smart':
                converted = self.convert_smart_b(detwingled)
                return converted
            # Convert smart quotes to ascii, then drop all non-ascii
            elif self.to_ascii.lower() == 'all':
                converted = self.convert_smart_b(detwingled)
                converted = converted.decode('utf-8').encode('ascii', errors='ignore')
                return converted
            # Default behavior, regular UTF-8
            else:
                return detwingled

        # Otherwise
        else:
            detwingled = UnicodeDammit.detwingle(line)  # Detwingle the line
            raw = UnicodeDammit(detwingled).unicode_markup.encode('utf-8')
            return raw

    def _as_iter(self) -> Generator[bytes]:
        with open(self.file, 'rb') as f:
            for line in f:
                yield self._parse(line)

    def __enter__(self) -> TextIO:
        return gen_to_textio(self._as_iter())

    def __exit__(self, exc_type, exc_value, traceback):
        return
