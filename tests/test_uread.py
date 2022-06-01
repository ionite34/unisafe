import io
import csv
from dataclasses import dataclass
import pandas as pd
import pytest
from pytest_lazyfixture import lazy_fixture as fx

from unisafe.uread import uread

expected_raw = """1,"Oh, what is this. This is a system” now, such there.",test
2,"In these kind of “Cases”, we will do some “tests” like such.",test
3,"This is a normal sentence, but with ellipsis…",test
"""

expected_converted = """1,"Oh, what is this. This is a system" now, such there.",test
2,"In these kind of "Cases", we will do some "tests" like such.",test
3,"This is a normal sentence, but with ellipsis…",test
"""


@dataclass
class TestData:
    raw: str

    def as_io(self) -> io.StringIO:
        return io.StringIO(self.raw)

    def lines(self) -> list[str]:
        # Returns a list of lines without newline chars
        return self.raw.splitlines()


@pytest.fixture(scope='module')
def data_raw():
    return TestData(expected_raw)


@pytest.fixture(scope='module')
def data_conv():
    return TestData(expected_converted)


@pytest.fixture(scope='function')
def get_open():
    return lambda: open('test.csv', 'r', encoding='windows-1252')


@pytest.fixture(scope='function')
def get_uread():
    return lambda: uread('test.csv', escape_files=None)


@pytest.fixture(scope='function')
def get_uread_csv():
    return lambda: uread('test.csv')


# Test Read Usage with Context Manager
@pytest.mark.parametrize('func, data', [
    (fx('get_open'), fx('data_raw')),
    (fx('get_uread'), fx('data_conv'))
])
def test_uread_cx_read(func, data):
    with func() as f:
        assert f.readable()
        assert not f.writable()
        assert not f.closed
        assert f.read() == data.raw  # Read to joined str
    with func() as f:
        assert f.readlines() == data.as_io().readlines()  # Read to list
    with func() as f:
        assert f.readline(1) == data.as_io().readline(1)  # Read specific line
    with func() as f:
        with pytest.raises(io.UnsupportedOperation):  # Write should not be allowed
            f.write('test')


# Test Read Usage without Context Manager
@pytest.mark.parametrize('func, data', [
    (fx('get_open'), fx('data_raw')),
    (fx('get_uread'), fx('data_conv'))
])
def test_uread_read(func, data):
    f = func()
    assert isinstance(f, io.TextIOWrapper)
    assert f.readable()
    assert f.read() == data.raw
    assert not f.closed
    f.close()
    assert f.closed


# Test Read as Iterable
@pytest.mark.parametrize('func, data', [
    (fx('get_open'), fx('data_raw')),
    (fx('get_uread'), fx('data_conv'))
])
def test_uread_cx_iter(func, data):
    with func() as f, data.as_io() as d:
        for line, expected in zip(f, d):
            assert line == expected


# Test Read to CSV and Quote escaping
@pytest.mark.parametrize('func, data', [
    (fx('get_open'), fx('data_raw')),
    (fx('get_uread_csv'), fx('data_conv'))
])
def test_uread_cx_csv(func, data):
    with func() as f:
        f_rows = csv.reader(f)
        for row, expected in zip(f_rows, data.lines()):
            escaped_vals = []
            for val in row:
                # If the val contains a comma, enclose it in quotes
                if ',' in val:
                    val = f'"{val}"'
                escaped_vals.append(val)
            assert ','.join(escaped_vals) == expected


# Test Read to Pandas DataFrame
@pytest.mark.parametrize('func, data', [
    (fx('get_open'), fx('data_raw')),
    (fx('get_uread_csv'), fx('data_conv'))
])
def test_uread_cx_pandas(func, data):
    with func() as f:
        df = pd.read_csv(f)
        f_rows = csv.reader(f)
        for pd_row, csv_row in zip(df.itertuples(), f_rows):
            for pd_item, csv_item in zip(pd_row, csv_row):
                assert pd_item == csv_item


# Test Multi-Encoding File
def test_uread_multi_encoding():
    # Built-in method should fail
    with pytest.raises(UnicodeDecodeError):
        with open('test_multi.txt', 'r', encoding='utf-8') as f:
            f.read()
    with pytest.raises(UnicodeDecodeError):
        with open('test_multi.txt', 'r', encoding='windows-1252') as f:
            f.read()
    # Confirm the incorrect parts with error escape
    with open('test_multi.txt', 'r', encoding='utf-8', errors='replace') as f:
        result = f.read()
        # There should be 2 replacement chars
        assert result.count(u'\uFFFD') == 2
        # Assert literal values
        assert result == '☃☃☃ \uFFFDSome really cursed file\uFFFD œ ₓ ၁ 𖡄'

    # Using uread (Normalize Smart)
    with uread('test_multi.txt') as f:
        result = f.read()
        assert result == '☃☃☃ “Some really cursed file” œ ₓ ၁ 𖡄'


# Test Exceptions
@pytest.mark.parametrize('func, data', [
    (lambda x: open(x), fx('data_raw')),
    (lambda x: uread(x), fx('data_conv'))
])
def test_uread_exceptions(func, data):
    # Invalid file
    with pytest.raises(FileNotFoundError):
        with func('not_exist.txt') as f:
            f.read()
