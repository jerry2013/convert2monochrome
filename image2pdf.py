#!/usr/bin/env python3
"""A command line tool to save images as pdf."""

import argparse
import os
import re

from PIL import Image


def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    return [
        int(text) if text.isdigit() else text.lower()
        for text in _nsre.split(s)
    ]


def main(args=None):
    parser = argparse.ArgumentParser(
        description=__doc__, add_help=True)
    parser.add_argument(
        "files", type=str, default=None, nargs="+",
        help="One or more paths to image files.")

    args = parser.parse_args(args=args)
    if not args.files:
        return

    path = os.path.dirname(args.files[0])
    out_fname = os.path.join(
        path,
        '..',
        'generated_%s.pdf' % os.path.basename(path)
    )

    first = True
    images = []
    for fname in sorted(args.files, key=natural_sort_key):
        im = Image.open(fname)
        try:
            print(fname, im.format, im.size, im.mode)
            im = im.convert('RGB')
        except Exception as ex:
            print(fname, ex)
            im.close()
            continue

        if first:
            im.save(out_fname)
            im.close()
            first = False
            continue

        # appending an existing pdf is slow, do it in batch of 20
        images.append(im)
        if len(images) == 20:
            images[0].save(out_fname, save_all=True, append=True, append_images=images[1:])
            while images:
                images.pop().close()

    print("\tSaved", out_fname)

if __name__ == '__main__':
    main()
