#!/usr/bin/env python3
"""
Debug-Test für Issue #6

Zeigt genau, wo der IndexError auftritt.
"""

import sys
import os
import tempfile
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat


def debug_markdown_processing(content: str):
    """Debug-Methode die zeigt, wo der Fehler auftritt."""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        print(f"Testing content: {repr(content)}")
        print()

        # Step 1: Create converter
        print("Step 1: Creating converter...")
        converter = DocumentConverter()
        print("  ✓ Converter created")

        # Step 2: Convert
        print("Step 2: Converting file...")
        result = converter.convert(temp_path)
        print(f"  ✓ Converted, result type: {type(result)}")
        print(f"  ✓ Document type: {type(result.document)}")

        # Step 3: Try export_to_markdown
        print("Step 3: Calling export_to_markdown()...")
        try:
            markdown = result.document.export_to_markdown()
            print(f"  ✓ Success! Length: {len(markdown)}")
        except IndexError as e:
            print(f"  ✗ IndexError in export_to_markdown: {e}")
            traceback.print_exc()

        # Step 4: Try export_to_dict
        print("Step 4: Calling export_to_dict()...")
        try:
            doc_dict = result.document.export_to_dict()
            print(f"  ✓ Success!")
        except IndexError as e:
            print(f"  ✗ IndexError in export_to_dict: {e}")
            traceback.print_exc()

    except Exception as e:
        print(f"✗ Error in step 1 or 2: {type(e).__name__}: {e}")
        traceback.print_exc()
    finally:
        os.unlink(temp_path)


if __name__ == "__main__":
    print("=" * 70)
    print("Issue #6 Debug Test")
    print("=" * 70)
    print()

    test_cases = [
        ("Header ohne Content", "## \n### \n"),
        ("Nur Listen", "- \n- \n- "),
    ]

    for desc, content in test_cases:
        print(f"\n{'=' * 70}")
        print(f"Test: {desc}")
        print("=" * 70)
        debug_markdown_processing(content)
        print()
