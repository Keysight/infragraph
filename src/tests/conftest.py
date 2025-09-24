import pytest
import sys
import os

if __package__ in ["", None]:
    # this path will be used instead of an installed package when running tests
    # within the development environment src/infragraph directory
    sys.path.insert(
        0,
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    )
    print(f"Testing code using src\n{sys.path}")
