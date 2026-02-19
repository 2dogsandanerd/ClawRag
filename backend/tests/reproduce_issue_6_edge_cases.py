#!/usr/bin/env python3
"""
Edge-Case-Test für Issue #6

Testet verschiedene problematische Markdown-Strukturen:
1. Leere Dateien
2. Nur Whitespace
3. Nur Header ohne Content
4. Spezielle Unicode-Zeichen
5. Unvollständige Markdown-Strukturen
"""

import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from docling.document_converter import DocumentConverter


def test_content(description: str, content: str) -> dict:
    """Testet Markdown-Content."""
    result = {"description": description, "success": False, "error": None}

    # Erstelle temporäre Datei
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        converter = DocumentConverter()
        conv_result = converter.convert(temp_path)
        markdown = conv_result.document.export_to_markdown()
        result["success"] = True
        result["output_length"] = len(markdown)
    except IndexError as e:
        result["error"] = f"IndexError: {str(e)}"
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)}"
    finally:
        os.unlink(temp_path)

    return result


def main():
    print("=" * 70)
    print("Issue #6 Edge-Case Tests")
    print("=" * 70)
    print()

    test_cases = [
        ("Leere Datei", ""),
        ("Nur Newlines", "\n\n\n"),
        ("Nur Whitespace", "   \n   \n   "),
        ("Nur Header", "# Header"),
        ("Header ohne Content", "## \n### \n"),
        ("Nur horizontal rule", "---"),
        ("Nur Code-Block Marker", "```\n```"),
        ("Unvollständiger Code-Block", "```python"),
        ("Nur Listen", "- \n- \n- "),
        ("Leere Tabelle", "| | |\n| | |"),
        ("Nur Links", "[link]()"),
        ("Spezielle Unicode", "🎉🎊🎁"),
        ("Nur HTML-Kommentare", "<!-- comment -->"),
        ("Gemischt: Header + leere Listen", "# Title\n- \n- "),
        ("Unvollständige Formatierung", "**bold"),
        ("Null-Bytes (sollte nicht vorkommen, aber testen)", "text\x00text"),
    ]

    errors_found = []

    for desc, content in test_cases:
        print(f"Teste: {desc}")
        result = test_content(desc, content)

        if result["success"]:
            print(f"  ✓ OK (Output: {result.get('output_length', 0)} chars)")
        else:
            print(f"  ✗ FEHLER: {result['error']}")
            errors_found.append(result)

    print()
    print("=" * 70)
    print(
        f"Ergebnis: {len(test_cases) - len(errors_found)}/{len(test_cases)} erfolgreich"
    )

    if errors_found:
        print("\nFehler gefunden in:")
        for err in errors_found:
            print(f"  - {err['description']}: {err['error']}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
