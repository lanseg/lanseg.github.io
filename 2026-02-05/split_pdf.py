"""Split PDF documents into text and images.

Arguments:
    source: directory with PDF documents. Script will browse it recursively and find all PDF files.
    target: directory with the extraction results. For each PDF document a subdirectory with the
      same name will be created, and the text and images will be stored there.
"""
from pathlib import Path
import os
import sys
import subprocess
import logging
import fitz

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s  %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_text(doc, target):
    logger.info("extracting text from %s to %s", doc, target)
    result = subprocess.run(
        ["pdftotext", "-layout", str(doc), str(target)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.warning("text extraction failed on %s: %s", doc, result.stderr)

def extract_images(doc, target):
    logger.info("extracting images from %s to %s", doc, target)
    with fitz.open(doc) as pdf:
        for npage, page in enumerate(pdf):
            for nimg, img in enumerate(page.get_images(full=True)):
                data = pdf.extract_image(img[0])
                img_path = target / f"page_{npage}_img_{nimg}.{data["ext"]}"
                with open(img_path, "wb") as img_f:
                    img_f.write(data["image"])

def process(doc, target):
    base = doc.parent / doc.stem
    os.makedirs(target / base, exist_ok = True)
    extract_text(doc, target / base / "text.txt")
    imgs = target / base / "images"
    os.makedirs(imgs, exist_ok = True)
    extract_images(doc, imgs)

def main(source, target):
    pdfs = list(source.rglob("*.pdf"))
    logger.info("documents found: %d", len(pdfs))
    for i, f in enumerate(pdfs):
        logger.info("[%6d of %6d] processing %s", i, len(pdfs), f)
        process(f, target)

if __name__ == '__main__':
    source, target = sys.argv[1:]
    logger.info("Source: %s, target: %s", source, target)

    main(Path(source), Path(target))
