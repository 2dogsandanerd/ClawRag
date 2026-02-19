#!/usr/bin/env python3
"""
Reproduktionstest für Issue #6: "list index out of range" bei Markdown-Verarbeitung

Dieser Test verifiziert:
1. Welche Markdown-Dateien das Problem verursachen
2. Wo genau der Fehler auftritt
3. Ob der Fix funktioniert

Usage:
    source venv/bin/activate
    python backend/tests/reproduce_issue_6.py
"""

import sys
import os
import traceback

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pathlib import Path
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import ConversionResult


def test_markdown_file(file_path: str) -> dict:
    """
    Testet eine einzelne Markdown-Datei mit Docling.

    Returns:
        dict mit Ergebnis: {"success": bool, "error": str, "traceback": str}
    """
    result = {
        "file": file_path,
        "success": False,
        "error": None,
        "traceback": None,
        "has_content": False,
    }

    try:
        # Erstelle Converter (ohne PDF-spezifische Optionen für MD)
        converter = DocumentConverter()

        # Konvertiere die Datei
        conversion_result = converter.convert(file_path)

        # Versuche export_to_markdown
        try:
            markdown_content = conversion_result.document.export_to_markdown()
            result["success"] = True
            result["has_content"] = len(markdown_content) > 0
            result["content_length"] = len(markdown_content)
            result["content_preview"] = (
                markdown_content[:200] if markdown_content else ""
            )
        except IndexError as e:
            result["error"] = f"IndexError in export_to_markdown: {str(e)}"
            result["traceback"] = traceback.format_exc()
        except Exception as e:
            result["error"] = (
                f"Error in export_to_markdown: {type(e).__name__}: {str(e)}"
            )
            result["traceback"] = traceback.format_exc()

    except Exception as e:
        result["error"] = f"Error in convert: {type(e).__name__}: {str(e)}"
        result["traceback"] = traceback.format_exc()

    return result


def find_markdown_files(directory: str) -> list:
    """Finde alle Markdown-Dateien im Verzeichnis."""
    md_files = []
    for root, dirs, files in os.walk(directory):
        # Skip venv und andere nicht-relevante Ordner
        dirs[:] = [
            d for d in dirs if d not in ["venv", "__pycache__", ".git", "node_modules"]
        ]
        for file in files:
            if file.endswith(".md"):
                md_files.append(os.path.join(root, file))
    return md_files


def main():
    """Hauptfunktion zum Testen aller Markdown-Dateien."""
    print("=" * 70)
    print("Issue #6 Reproduktionstest: Markdown 'list index out of range'")
    print("=" * 70)
    print()

    # Teste Markdown-Dateien aus dem Repository
    repo_root = Path(__file__).parent.parent.parent
    md_files = find_markdown_files(str(repo_root))

    print(f"Gefunden: {len(md_files)} Markdown-Dateien")
    print()

    success_count = 0
    error_count = 0
    errors = []

    for i, md_file in enumerate(md_files, 1):
        print(f"[{i}/{len(md_files)}] Teste: {os.path.basename(md_file)}")
        result = test_markdown_file(md_file)

        if result["success"]:
            success_count += 1
            print(f"    ✓ OK (Länge: {result.get('content_length', 0)} chars)")
        else:
            error_count += 1
            print(f"    ✗ FEHLER: {result['error']}")
            errors.append(result)

            # Zeige Traceback für Debugging
            if result["traceback"]:
                print(f"    Traceback:")
                for line in result["traceback"].split("\n")[-5:]:  # Letzte 5 Zeilen
                    if line.strip():
                        print(f"      {line}")

    print()
    print("=" * 70)
    print("ZUSAMMENFASSUNG")
    print("=" * 70)
    print(f"Erfolgreich: {success_count}/{len(md_files)}")
    print(f"Fehler:      {error_count}/{len(md_files)}")
    print()

    if errors:
        print("Dateien mit Fehlern:")
        for err in errors:
            print(f"  - {err['file']}")
            print(f"    Fehler: {err['error']}")
        print()
        return 1
    else:
        print("✓ Keine Fehler gefunden!")
        print()
        print("Mögliche Erklärungen:")
        print(
            "  1. Die betroffenen Dateien haben spezielle Eigenschaften (leer, korrumpiert, etc.)"
        )
        print(
            "  2. Der Fehler tritt nur bei bestimmten Dateien aus dem User-Report auf"
        )
        print("  3. Wir müssen eine Beispieldatei vom User erhalten")
        print()
        return 0


if __name__ == "__main__":
    sys.exit(main())
