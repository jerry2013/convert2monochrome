#!/usr/bin/env python3
"""A command line tool to process and convert scanned images from PDF to monochrome."""

import argparse
import os
from io import BytesIO

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.pdfpage import PDFPage

from PIL import Image


class ImageWriter:
    def export_image(self, image):
        print("\tImage", image.name, '(%dx%d)' % image.srcsize)
        raw_data = image.stream.get_rawdata()
        i = Image.open(BytesIO(raw_data))
        # i = ImageChops.invert(i)
        i = i.convert('RGB')
        self.image = i

def main(args=None):
    parser = argparse.ArgumentParser(
        description=__doc__, add_help=True)
    parser.add_argument(
        "file", type=str, default=None, nargs="+",
        help="One or more paths to PDF files.")

    parse_params = parser.add_argument_group(
        'Filter', description='Color filter')
    parse_params.add_argument(
        "--threshold", "-t", type=int, default=0xc0,
        help="The threshold level for monochrome (default 0xc0).")

    args = parser.parse_args(args=args)
    if not args.file:
        return

    codec = 'utf-8'
    rsrcmgr = PDFResourceManager()
    out_fp = BytesIO()

    for fname in args.file:
        print('Processing', fname)
        imagewriter = ImageWriter()
        with open(fname, "rb") as in_fp:
            images = []
            #pdfminer.high_level.extract_text_to_fp(fp, output_dir=temp_dir)
            device = TextConverter(
                rsrcmgr, out_fp, codec=codec, imagewriter=imagewriter
            )

            interpreter = PDFPageInterpreter(rsrcmgr, device)
            for page in PDFPage.get_pages(in_fp):
                print("\tPage", page.pageid)
                interpreter.process_page(page)
                # convert every point to black (0x00) or white (0xff)
                img = imagewriter.image.point(lambda i: 0xff if i >= args.threshold else 0)
                images.append(img)

            device.close()

            if images:
                out_fname = os.path.join(
                    os.path.dirname(fname),
                    'enhanced_' + os.path.basename(fname)
                )
                images[0].save(out_fname, save_all=True, append_images=images[1:])
                print("\tSaved", out_fname)


if __name__ == '__main__':
    main()
