# Generate the mixed encoding test file

def main():
    # Here's a UTF8 document.
    utf8 = ("\N{SNOWMAN}" * 3).encode("utf8")

    # Here's a Windows-1252 document.
    windows_1252 = (
        " \N{LEFT DOUBLE QUOTATION MARK}Some really cursed file"
        "\N{RIGHT DOUBLE QUOTATION MARK} ").encode("windows_1252")

    # Multibyte characters in UTF-8
    # to test that they don't get mistaken for smart quotes
    multi_utf8 = (
        '\N{LATIN SMALL LIGATURE OE} '  # 2-byte char '\xc5\x93'
        '\N{LATIN SUBSCRIPT SMALL LETTER X} '  # 3-byte char '\xe2\x82\x93'
        '\u1041 '  # Myanmar Digit One (U+1041)
        '\U00016844'  # Bamum Letter Phase-A Unknown (U+16844)
    ).encode("utf8")
    # Join the byte strings together
    doc = utf8 + windows_1252 + multi_utf8

    # Write the file
    with open("test_multi.txt", "wb") as f:
        f.write(doc)


if __name__ == "__main__":
    main()
