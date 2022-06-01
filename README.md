# unisafe

[![Build](https://github.com/ionite34/unisafe/actions/workflows/push-main.yml/badge.svg)](https://github.com/ionite34/unisafe/actions/workflows/push-main.yml)
[![codecov](https://codecov.io/gh/ionite34/unisafe/branch/main/graph/badge.svg?token=359D2BXVEM)](https://codecov.io/gh/ionite34/unisafe)
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fionite34%2Funisafe.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2Fionite34%2Funisafe?ref=badge_shield)

A stand-in replacement for `builtins.open` to read unknown or mixed text file encodings into UTF-8.
Optionally automatically converts UTF-8 or Windows-1252 smart quotes into UTF-8 or ASCII.


```python
from unisafe import uread

# API is same as builtins.open, use read() for all lines
with uread('file.csv') as f:
    lines = f.read()

# Use an iterator to get each text line
with uread('file.csv') as f:
    for line in f:
        print(line)
```

The `uread` function returns a [TextIOWrapper](https://docs.python.org/3/library/io.html#io.TextIOWrapper), just like Python's built-in [open](https://docs.python.org/3/library/functions.html#open)
(when using the 'r' mode). API behavior is exactly the same as the built-in method, besides the additional runtime encoding detection and conversions.
A file handle will opened in the 'rb' or read binary mode. Writing is not supported.

```python
from unisafe import uread

f1 = open('test.txt', 'r', encoding='utf-8')
type(f1)
# -> _io.TextIOWrapper

f2 = uread('test.txt')
type(f2)
# -> _io.TextIOWrapper
```

Works with the [csv](https://docs.python.org/3/library/csv.html) library and third party libraries such
as [pandas](https://github.com/pandas-dev/pandas)

```python
from unisafe import uread
import pandas as pd
import csv

with uread('file.csv') as f:
    table = csv.reader(f)
    
with uread('file.csv') as f:
    df = pd.read_csv(f, encoding='utf-8')
```

## License

The code in this project is released under the [MIT License](LICENSE).

[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fionite34%2Funisafe.svg?type=large)](https://app.fossa.com/projects/git%2Bgithub.com%2Fionite34%2Funisafe?ref=badge_large)
