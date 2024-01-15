#!/usr/bin/env python3
"""A command line tool to process and convert scanned images from PDF to monochrome."""

import argparse, textwrap
import os
from io import BytesIO
from sys import stdin

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.pdfpage import PDFPage

from PIL import Image, ImageDraw, ImageEnhance


class ImageWriter:
    def export_image(self, image):
        print("\tImage", image.name, '(%d, %d)' % image.srcsize)
        raw_data = image.stream.get_rawdata()
        i = Image.open(BytesIO(raw_data))
        # i = ImageChops.invert(i)
        i = i.convert('RGB')
        self.image = i

def floodfill(img: Image, xy, thresh):
    pixel = img.getpixel(xy)
    print("\t\tPixel", '(%4d, %4d)' % xy, pixel)
    if pixel < 0xff:
        ImageDraw.floodfill(img, xy, 0xff, thresh=thresh)
        #draw = ImageDraw.Draw(img)
        #draw.regular_polygon((xy, 50), 10, fill=0xff)

def process_image(img: Image, contrast=1, brightness=1, sharpness=1, threshold=0, tolerance=None):
    if img.mode != 'L':
        # convert to greyscale
        img = img.convert('L')

    if contrast > 0 and contrast != 1:
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast)

    if brightness > 0 and brightness != 1:
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(brightness)

    if sharpness > 0 and sharpness != 1:
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(sharpness)

    if threshold > 0:
        # convert every point to black (0x00) or white (0xff)
        img = img.point(lambda i: 0xff if i >= threshold else 0)
    elif threshold < 0:
        # convert every point to white (0xff) if above the |threshold|
        img = img.point(lambda i: 0xff if i >= -threshold else i)

    if tolerance is not None:
        floodfill(img, (5, 5), thresh=tolerance)
        floodfill(img, (5, img.size[1] - 5), thresh=tolerance)
        floodfill(img, (img.size[0] - 5, 5), thresh=tolerance)
        floodfill(img, (img.size[0] - 5, img.size[1] - 5), thresh=tolerance)
    return img


def main(args=None):
    parser = argparse.ArgumentParser(
        description=__doc__,
        add_help=True,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--interactive", "-i", action="store_true",
        help="Prompt before generating output.")
    parser.add_argument(
        "file", type=str, default=None, nargs="+",
        help="One or more paths to PDF files.")

    parse_params = parser.add_argument_group(
        'Filter', description='Color filter')
    parse_params.add_argument(
        "--threshold", "-t", type=int, default=0xc0,
        help=textwrap.dedent("""\
                             If 0, keep grayscale.
                             >0, the threshold level for monochrome, turning to black (<t) or white (>=t).
                             <0, white out (>=|t|).
                             (default 192 or 0xc0)."""),
    )
    parse_params.add_argument(
        "--contrast", "-c", type=float, default=1.0,
        help=textwrap.dedent("""\
                             If 1, no change.
                             <1 reduces the contrast of the image.
                             >1 increases the contrast of the image.
                             (default 1.0)."""),
    )
    parse_params.add_argument(
        "--brightness", "-b", type=float, default=1.0,
        help=textwrap.dedent("""\
                             If 1, no change.
                             <1 darkens the image.
                             >1 brightens the image.
                             (default 1.0)."""),
    )
    parse_params.add_argument(
        "--sharpness", "-s", type=float, default=1.0,
        help=textwrap.dedent("""\
                             If 1, no change.
                             >1 sharpens the image.
                             factor<1 blurs the image.
                             (default 1.0)."""),
    )

    parse_edge = parser.add_argument_group(
        'Corner', description='Fill corners')
    parse_edge.add_argument(
        "--tolerance", "-f", type=int, default=None,
        help="The tolerance (difference) for edge detection (default None).")

    args = parser.parse_args(args=args)
    if not args.file:
        return

    codec = 'utf-8'
    rsrcmgr = PDFResourceManager()
    out_fp = BytesIO()

    for fname in args.file:
        print('Processing', fname)
        images = []
        with open(fname, "rb") as in_fp:
            imagewriter = ImageWriter()
            #pdfminer.high_level.extract_text_to_fp(fp, output_dir=temp_dir)
            device = TextConverter(
                rsrcmgr, out_fp, codec=codec, imagewriter=imagewriter
            )

            cnt = 0
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            for page in PDFPage.get_pages(in_fp):
                cnt += 1
                print("\tPage", cnt, "id:", page.pageid)
                interpreter.process_page(page)

                img = process_image(
                    imagewriter.image,
                    contrast=args.contrast,
                    brightness=args.brightness,
                    sharpness=args.sharpness,
                    threshold=args.threshold,
                    tolerance=args.tolerance,
                )
                if args.interactive:
                    img_name = '%s_page_%d.png' % (fname, cnt)
                    img.save(img_name)
                    img.close()
                    images.append(img_name)
                else:
                    images.append(img)

            device.close()

        if images:
            if args.interactive:
                print("Press any key to continue...")
                stdin.read(1)

            out_fname = os.path.join(
                os.path.dirname(fname),
                'enhanced_' + os.path.basename(fname)
            )
            if args.interactive:
                images = [
                    Image.open(fn).convert('RGB')
                    for fn in images
                    if os.path.exists(fn)
                ]
            images[0].save(out_fname, save_all=True, append_images=images[1:])
            print("\tSaved", out_fname)


if __name__ == '__main__':
    main()
