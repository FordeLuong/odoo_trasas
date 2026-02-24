import sys
import PyPDF2

# Set UTF-8 encoding for output
sys.stdout.reconfigure(encoding="utf-8")

pdf_path = r"d:\Tech\odoo-19.0+e.20250918\custom_addons_project2\02_TRASAS_QUANLYCONGVANDEN.pdf"

try:
    with open(pdf_path, "rb") as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        print(f"Total pages: {len(reader.pages)}\n")
        print("=" * 80)

        for i, page in enumerate(reader.pages, 1):
            print(f"\n--- PAGE {i} ---\n")
            text = page.extract_text()
            print(text)
            print("\n" + "=" * 80)

except Exception as e:
    print(f"Error: {e}")
