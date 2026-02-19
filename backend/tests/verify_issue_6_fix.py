#!/usr/bin/env python3
"""
Verifizierungstest für Issue #6 Fix

Testet, dass der Fix für "list index out of range" funktioniert.
Der Test nutzt direkt die docling_service.process_file() Methode.
"""

import sys
import os
import tempfile
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.services.docling_service import docling_service


def test_content(description: str, content: str) -> dict:
    """Testet Markdown-Content über den DoclingService."""
    result = {
        "description": description,
        "success": False,
        "error": None,
        "fallback_used": False,
    }

    # Erstelle temporäre Datei
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        # Nutze den DoclingService (async)
        async def process():
            return await docling_service.process_file(temp_path)

        response = asyncio.run(process())

        if response.get("success"):
            result["success"] = True
            result["content_length"] = len(response.get("content", ""))
            result["fallback_used"] = (
                response.get("metadata", {}).get("docling_fallback") == "plaintext"
            )
        else:
            result["error"] = response.get("error", "Unknown error")

    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)}"
    finally:
        os.unlink(temp_path)

    return result


def main():
    print("=" * 70)
    print("Issue #6 Fix-Verifizierung")
    print("=" * 70)
    print()
    print("Testet die problematischen Fälle mit dem aktuellen Fix:")
    print()

    # Diese Fälle haben vorher den IndexError verursacht
    test_cases = [
        ("Header ohne Content", "## \n### \n"),
        ("Nur Listen", "- \n- \n- "),
        ("Gemischt: Header + leere Listen", "# Title\n- \n- "),
        ("Normale Markdown-Datei", "# Hello\n\nThis is content."),
    ]

    all_passed = True

    for desc, content in test_cases:
        print(f"Teste: {desc}")
        result = test_content(desc, content)

        if result["success"]:
            fallback_info = " (Fallback: Plaintext)" if result["fallback_used"] else ""
            print(
                f"  ✓ OK{fallback_info} - Content: {result.get('content_length', 0)} chars"
            )
        else:
            print(f"  ✗ FEHLER: {result['error']}")
            all_passed = False

    print()
    print("=" * 70)

    if all_passed:
        print("✓ Alle Tests erfolgreich! Der Fix funktioniert.")
        return 0
    else:
        print("✗ Einige Tests fehlgeschlagen.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
