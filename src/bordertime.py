import os
from PIL import Image, ImageColor
from pathlib import Path
import argparse
from bt_logger import _logger
from gooey import Gooey

from bt_exceptions import BadResolution



# TODO __name__ == 'main'


def is_image(abs_path):
    if os.path.isfile(abs_path):
        path_obj = Path(os.path.basename(abs_path))
        file_ext = path_obj.suffix
        if file_ext in arg_file_ext:
            return True
        else:
            return False
    else:
        return False


@Gooey
def main():
    parser = argparse.ArgumentParser(description="Bordertime", add_help=False)
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s 1.0',
                        help="Show program's version number and exit.")
    parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                        help='Show this help message and exit.')

    parser.add_argument('-d', '--arg_directory',
                        help="Path of arg_directory containing images to crop "
                        "(can't use with -f arg)")
    parser.add_argument('-f', '--file',
                        help="Path of image to crop (can't use with -d arg)")
    parser.add_argument('-r', '--resolution',
                        help="Desired resolution (e.g. 1080x1350) (can't use "
                        "with -a arg)")
    parser.add_argument('-a', '--aspect',
                        help="Desired aspect ratio (e.g. 3:2) (can't use "
                        "with -r arg)")
    parser.add_argument('-c', '--color',
                        help="Canva background color (e.g. #777777) "
                        "(default: #FFFFFF)",
                        default='#FFFFFF')
    parser.add_argument('-e', '--extension',
                        help="File extension to crop (e.g. .jpeg or "
                        ".jpeg,.png) (default: most common image formats)",
                        default='.jpeg,.jpg,.png')
    parser.add_argument('-o', '--overwrite',
                        action='store_true',
                        help='Overwrite already existing "<fname>_btcrop" files')

    args = parser.parse_args()

    arg_directory = args.arg_directory
    # TODO file management
    arg_file = args.file
    arg_color = args.color
    global arg_file_ext
    arg_file_ext = args.extension
    arg_file_ext = arg_file_ext.split(',')

    arg_resolution = args.resolution

    arg_aspect_ratio = args.aspect

    args_overwrite = args.overwrite

    if all([arg_directory, arg_file]):
        raise Exception('Source must be arg_directory OR file, you used both')
    if all([arg_resolution, arg_aspect_ratio]):
        raise Exception(
            'Mode must be by resolution OR by aspect, you used both')
    if not any([arg_directory, arg_file]):
        raise Exception('You must specify a directory OR a file')
    if not any([arg_resolution, arg_aspect_ratio]):
        raise Exception('You must specify a resolution OR an aspect ratio')

    if not os.path.isdir(arg_directory):
        raise Exception(f'No folder "{arg_directory}" found')

    if not (arg_color.startswith('#') and arg_color[1:].isalnum() and
            len(arg_color[1:]) == 6):
        raise ValueError(f'Wrong hexcode given {arg_color}')

    if not all(map(lambda x: x.startswith('.'), arg_file_ext)):
        raise Exception('All extensions must start with "."')

    filepaths = [os.path.join(arg_directory, fname) for fname in
                 os.listdir(arg_directory)]

    filepaths = list(filter(is_image, filepaths))

    for user_path in filepaths:
        user_folder = os.path.dirname(user_path)
        user_fname = os.path.basename(user_path)

        img = Image.open(open(user_path, 'rb'))
        img_hgt = img.height
        img_wdt = img.width

        img_ratio_is_vertical = img_hgt > img_wdt
        img_ratio_is_horizontal = img_wdt > img_hgt
        img_ratio_is_square = img_hgt == img_wdt

        if arg_aspect_ratio:
            aspect_ratio = arg_aspect_ratio.split('/')
            if len(aspect_ratio) != 2:
                raise Exception(
                    'Wrong aspect ratio format, expecting something like '
                    '4/5, got {}'.format(arg_resolution))

        canvas_background: tuple = ImageColor.getrgb(arg_color)
        if arg_resolution:
            if arg_resolution == 'long_edge':
                arg_wdt_px = arg_hgt_px = img_wdt
            else:
                resolution_px = arg_resolution.lower().split('x')
                if len(resolution_px) != 2:
                    raise Exception(
                        'Wrong resolution format, expecting something like '
                        '1350x1080, got {} or long_edge'.format(arg_resolution))
                arg_wdt_px = int(resolution_px[0])
                arg_hgt_px = int(resolution_px[1])

            arg_ratio_is_vertical = arg_hgt_px > arg_wdt_px
            arg_ratio_is_horizontal = arg_wdt_px > arg_hgt_px
            arg_ratio_is_square = arg_hgt_px == arg_wdt_px

        elif arg_aspect_ratio:
            arg_wdt_ratio = int(aspect_ratio[0])
            arg_hgt_ratio = int(aspect_ratio[1])
            arg_ratio_is_vertical = arg_hgt_ratio > arg_wdt_ratio
            arg_ratio_is_horizontal = arg_wdt_ratio > arg_hgt_ratio
            arg_ratio_is_square = arg_hgt_ratio == arg_wdt_ratio
            factor = arg_wdt_ratio / arg_hgt_ratio
            if img_ratio_is_horizontal:
                arg_wdt_px = img_wdt
                arg_hgt_px = round(img_wdt / factor)
            elif img_ratio_is_vertical:
                arg_hgt_px = img_hgt
                arg_wdt_px = round(img_hgt / factor)
            else:
                raise Exception('Crop by aspect ratio is not supported yet '
                                'for horizontal images')

        img_canvas = Image.new(
            'RGB', (arg_wdt_px, arg_hgt_px), canvas_background
        )

        canvas_wdt = img_canvas.width
        canvas_hgt = img_canvas.height

        if img_canvas.size == img.size:
            continue

        new_path_obj = Path(user_fname)
        stem = new_path_obj.stem
        suffix = new_path_obj.suffix
        if '_btcrop' in stem:
            continue
        new_fname = f'{stem}_btcrop{suffix}'
        new_filepath = os.path.join(user_folder, new_fname)

        # TODO width e height based on aspect
        # TODO Image res square
        img_resized = img
        if img_ratio_is_vertical:
            if not arg_ratio_is_vertical:
                _logger.warning(
                    'Skipping img "{}" because image is vertical, '
                    'but input aspect ratio is not'.format(user_fname)
                )
                continue
            if canvas_hgt > img_hgt:
                _logger.error("Image height is smaller than canvas' height"
                              "Skipping image {}".format(user_path))
                continue

            # Keep ratio with thumbnail
            img_resized.thumbnail((canvas_hgt, canvas_hgt), Image.LANCZOS)
            negative_space = canvas_wdt - img_resized.width
            left_margin = negative_space // 2
            img_canvas.paste(img_resized, (left_margin, 0))
        elif img_ratio_is_horizontal:
            if not arg_ratio_is_horizontal and not arg_ratio_is_square:
                _logger.warning(
                    'Skipping img "{}" because image is horizontal, '
                    'but input aspect ratio is neither horizontal nor '
                    'square'.format(user_fname)
                )
                continue

            if canvas_wdt > img_wdt:
                _logger.error("Image width is smaller than canvas' width"
                              "Skipping image {}".format(user_path))
                continue
            # Keep ratio with thumbnail
            img_resized.thumbnail((canvas_wdt, canvas_wdt), Image.LANCZOS)
            negative_space = canvas_hgt - img_resized.height
            top_margin = negative_space // 2
            img_canvas.paste(img_resized, (0, top_margin))

        if args_overwrite is True:
            img_canvas.save(new_filepath, quality=95)
        else:
            if os.path.isfile(new_filepath):
                _logger.warning('File {} already exists. Use option -o to '
                                'overwrite'.format(new_filepath))
                continue
            else:
                img_canvas.save(new_filepath, quality=95)
        _logger.info(
            'New image "{0}" created (original size {1}x{2}, '
            'new size {3}x{4})'.format(
                new_fname, img_wdt, img_hgt, canvas_wdt, canvas_hgt)
        )


if __name__ == '__main__':
    main()


class BTImage(object):
    def __init__(self, abspath):
        ...
