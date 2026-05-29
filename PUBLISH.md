# Publishing AACP to PyPI

## First time setup

```bash
pip3 install build twine --break-system-packages
```

Create a PyPI account at https://pypi.org/account/register/

Create an API token at https://pypi.org/manage/account/token/
  Scope: Entire account (for first publish)
  Save the token -- you only see it once

## Test on TestPyPI first (recommended)

```bash
cd ~/Desktop/aacp-v1

# Build the package
python3 -m build

# Check what was built
ls dist/
# Should show:
#   aacp-1.1.0-py3-none-any.whl
#   aacp-1.1.0.tar.gz

# Upload to TestPyPI first
python3 -m twine upload --repository testpypi dist/*
# Enter: __token__
# Enter: your TestPyPI token

# Test install from TestPyPI
pip3 install --index-url https://test.pypi.org/simple/ aacp

# Quick smoke test
python3 -c "
from aacp.encoders.workflows.payroll import PayrollEncoder
enc = PayrollEncoder()
pkt = enc.fetch_employees('2026-03')
print(pkt.packet)
print('PyPI package works')
"
```

## Publish to real PyPI

```bash
python3 -m twine upload dist/*
# Enter: __token__
# Enter: your PyPI token
```

Package will be live at:
https://pypi.org/project/aacp/

Users can then install with:
pip install aacp
pip install aacp[openai]   # includes OpenAI support

## Future versions

Bump version in pyproject.toml:
  version = "1.2.0"

Rebuild and upload:
  python3 -m build
  python3 -m twine upload dist/*

## Adding to README

Add this badge at the top of README.md:
[![PyPI version](https://badge.fury.io/py/aacp.svg)](https://badge.fury.io/py/aacp)

And this install instruction:
pip install aacp
