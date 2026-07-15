from __future__ import annotations

import argparse
import shutil
import tempfile
import zipfile
from pathlib import Path

from lxml import etree
from PIL import Image


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
}


def _replace_one(docx_path: Path, image_path: Path, media_name: str) -> None:
    with Image.open(image_path) as image:
        img_w, img_h = image.size

    with zipfile.ZipFile(docx_path, "r") as zin:
        rels = etree.fromstring(zin.read("word/_rels/document.xml.rels"))
        rel_ids = set()
        for rel in rels.findall("rel:Relationship", NS):
            target = rel.get("Target", "").replace("\\", "/")
            if target == f"media/{media_name}":
                rel_ids.add(rel.get("Id"))

        if not rel_ids:
            raise ValueError(f"{media_name} is not referenced by document.xml")

        document_xml = zin.read("word/document.xml")
        doc = etree.fromstring(document_xml)
        changed = False
        for blip in doc.xpath(".//a:blip", namespaces=NS):
            embed_id = blip.get(f"{{{NS['r']}}}embed")
            if embed_id not in rel_ids:
                continue
            inline = blip
            while inline is not None and inline.tag != f"{{{NS['wp']}}}inline":
                inline = inline.getparent()
            if inline is None:
                continue
            extent = inline.find("wp:extent", NS)
            if extent is not None and extent.get("cx"):
                cx = int(extent.get("cx"))
                cy = round(cx * img_h / img_w)
                extent.set("cy", str(cy))
                pic_ext = inline.find(".//pic:spPr/a:xfrm/a:ext", NS)
                if pic_ext is not None:
                    pic_ext.set("cx", str(cx))
                    pic_ext.set("cy", str(cy))
                changed = True

        if not changed:
            raise ValueError(f"Could not update display extent for {media_name}")

        new_document_xml = etree.tostring(
            doc,
            xml_declaration=True,
            encoding="UTF-8",
            standalone="yes",
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp_path = Path(tmp.name)

        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                name = info.filename
                if name == f"word/media/{media_name}":
                    zout.writestr(info, image_path.read_bytes())
                elif name == "word/document.xml":
                    zout.writestr(info, new_document_xml)
                else:
                    zout.writestr(info, zin.read(name))

    shutil.move(str(tmp_path), docx_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("docx", type=Path)
    parser.add_argument("image", type=Path)
    parser.add_argument("--media-name", default="image1.png")
    args = parser.parse_args()

    _replace_one(args.docx, args.image, args.media_name)
    print(args.docx)


if __name__ == "__main__":
    main()
