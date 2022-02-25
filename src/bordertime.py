import os
from PIL import Image, ImageColor
from pathlib import Path
import argparse
# import bt_exceptions
from bt_logger import _logger

# TODO __name__ == 'main'

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
arg_file_ext = args.extension
arg_file_ext = arg_file_ext.split(',')

arg_resolution = args.resolution
arg_resolution_px = arg_resolution.lower().split('x')
# TODO aspect management
arg_aspect = args.aspect
args_overwrite = args.overwrite

if all([arg_directory, arg_file]):
    raise Exception('Source must be arg_directory OR file, you used both')
if all([args.resolution, args.aspect]):
    raise Exception('Mode must be by resolution OR by aspect, you used both')

if not os.path.isdir(arg_directory):
    raise Exception(f'No folder "{arg_directory}" found')

if not (arg_color.startswith('#') and arg_color[1:].isalnum() and
        len(arg_color[1:]) == 6):
    raise ValueError(f'Wrong hexcode given {arg_color}')

if not all(map(lambda x: x.startswith('.'), arg_file_ext)):
    raise Exception('All extensions must start with "."')

if len(arg_resolution_px) != 2:
    raise Exception('Wrong resolution format, expecting smth like '
                    '1350x1080, got {}'.format(arg_resolution))

filepaths = [os.path.join(arg_directory, fname) for fname in
             os.listdir(arg_directory)]


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

    arg_wdt = int(arg_resolution_px[0])
    arg_hgt = int(arg_resolution_px[1])

    arg_ratio_is_vertical = arg_hgt > arg_wdt
    arg_ratio_is_horizontal = arg_wdt > arg_hgt
    arg_ratio_is_square = arg_hgt == arg_wdt

    canvas_background: tuple = ImageColor.getrgb(arg_color)

    img_canvas = Image.new('RGB', (arg_wdt, arg_hgt), canvas_background)
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
            _logger.warning('Skipping img "{}" because image is vertical, '
                            'but input aspect ratio is not'.format(user_fname))
            continue
        if canvas_hgt > img_hgt:
            _logger.error("Image height is smaller than canvas' height"
                          "Skipping image {}".format(user_path))
            continue

        # Keep ratio with thumbnail
        img_resized.thumbnail((canvas_hgt, canvas_hgt), Image.ANTIALIAS)
        negative_space = canvas_wdt - img_resized.width
        left_margin = negative_space // 2
        img_canvas.paste(img_resized, (left_margin, 0))
    elif img_ratio_is_horizontal:
        if not arg_ratio_is_horizontal and not arg_ratio_is_square:
            _logger.warning('Skipping img "{}" because image is horizontal, '
                            'but input aspect ratio is neither horizontal nor square'.format(user_fname))
            continue

        if canvas_wdt > img_wdt:
            _logger.error("Image width is smaller than canvas' width"
                          "Skipping image {}".format(user_path))
            continue
        # Keep ratio with thumbnail
        img_resized.thumbnail((canvas_wdt, canvas_wdt), Image.ANTIALIAS)
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


class BTImage(object):
    def __init__(self, abspath):
        ...
