#!/usr/bin/env python3
from argparse import ArgumentParser
from collections import Counter
from colorsys import hls_to_rgb
from functools import lru_cache
from math import ceil, log
from operator import itemgetter
from shutil import get_terminal_size
from string import printable, whitespace
from sys import stdin

from xtermcolor import colorize
colorize = lru_cache(maxsize=2**12)(colorize)

printable = set(printable) - set(whitespace)


def sensible_block_size(input_len):
    return input_len // 2


def group_by(contents, block_size=None):
    r"""
    Collect data into fixed-length chunks or blocks.
    >>> list(group_by("helloworld", 4))
    ['hell', 'owor', 'ld']
    """
    block = lambda i: contents[i * block_size: i * block_size + block_size]
    content_length = len(contents)
    block_size = block_size or sensible_block_size(content_length)
    length = int(ceil(float(content_length) / block_size))
    result = (block(i) for i in range(length))
    return result


def entropy(s):
    p, lns = Counter(s), float(len(s))
    return max(0, -sum(count/lns * log(count/lns, 2) for count in p.values()))


def insert_spacing(line, spacing=8):
    return " ".join(n for n in group_by(line, spacing))


def format_bytes(bytes):
    result = []
    for byte_group in group_by(bytes):
        result.append("".join(format_byte(val) for val in byte_group))
    return " ".join(result)


def format_byte(val):
    return colorize("{:02x}".format(val), rgb=byte_color(val))


@lru_cache()
def byte_color(val):
    hue_map = lambda val: val / 255.0
    r, g, b = [int(v * 255) for v in hls_to_rgb(hue_map(val), 0.5, 1)]
    return r << 16 | g << 8 | b


def entropy_color(entropy, min_entropy, max_entropy):
    """
    >>> entropy_color(1, 0, 1)
    65280
    >>> entropy_color(1, 1, 2)
    16711680
    """
    g = int((float(entropy - min_entropy) / (max_entropy - min_entropy)) * 255)
    return (255 - g) << 16 | g << 8


def format_entropy(entropy, min_entropy, max_entropy):
    entropy_formatted = "Entropy: {}".format(round(entropy, 2))
    return colorize(entropy_formatted, rgb=entropy_color(
        entropy, min_entropy, max_entropy))


def format_ascii(bytes):
    return " ".join(group_by("".join(
        b if b in printable else '.' for b in
        map(chr, filter(lambda x: x is not None, bytes)))))


def get_entropy_distribution(windows):
    res = [entropy(line) for line in windows]
    return min(res), max(res)


def hexdump(contents, line_length):
    def pad_byte_line(byte_line):
        if len(byte_line) < line_length:
            # TODO still not satisfactory since 0 still gets displayed...
            return byte_line.ljust(line_length, b'\0')
        else:
            return byte_line

    line_groups = list(group_by(contents, line_length))

    min_entropy, max_entropy = get_entropy_distribution(line_groups)

    for line_no, byte_line in enumerate(line_groups):
        print("{position:08x} {bytes} {ascii} {entro}".format(
            position=line_no * line_length,
            bytes=format_bytes(pad_byte_line(byte_line)),
            ascii=format_ascii(pad_byte_line(byte_line)),
            entro=format_entropy(entropy(byte_line), min_entropy, max_entropy),
        ))


def show_entropy(contents, line_length):
    line_groups = list(group_by(contents, line_length))

    min_entropy, max_entropy = get_entropy_distribution(line_groups)

    for line_no, byte_line in enumerate(group_by(line_groups, 32)):
        print("{:08x} ".format(line_no * 32 * line_length), end='')
        for window in byte_line:
            print(colorize(
                'X', entropy_color(entropy(window), min_entropy, max_entropy)),
                end='',)
        print()


def show_histogram(contents):
    byte_count = Counter(contents)

    print("Byte Count")
    for key, count in sorted(
            byte_count.items(), key=itemgetter(1), reverse=True):
        print(colorize('0x{:02x} {:d}'.format(key, count),
              rgb=byte_color(key)))


def get_contents(file):
    if file == "-":
        contents = stdin.buffer.read()
    else:
        with open(file, 'rb') as fd:
            contents = fd.read()
    assert contents, "Input was empty."
    return contents


def get_default_width():
    """Estimate the needed character width using the terminal width and round it
    to the next candidate in candates list."""
    candidates = range(8, 33, 8)
    # 0.2 is a pure guess
    width = get_terminal_size()[0] * 0.19
    return min(candidates, key=lambda x: abs(x - width))


def main():
    parser = ArgumentParser(description="Visualize Binary Files")
    parser.add_argument('file', help="Either '-' for stdin or a file path.")
    parser.add_argument(
        '-l', '--line-length', default=get_default_width(),
        required=False, type=int,
        help='Specify how many bytes per line should be shown.',
    )
    parser.add_argument(
        '-i', '--histogram', default=False, action='store_true',
        help='Show histogram', required=False,
    )
    parser.add_argument(
        '-e', '--entropy-only', default=False, action='store_true',
        help='Show only entropy per byte line.', required=False,
    )
    args = parser.parse_args()
    assert not all((
        args.entropy_only, args.histogram)), "Can only select one mode"

    contents = get_contents(args.file)

    if args.entropy_only:
        show_entropy(contents, args.line_length)
    elif args.histogram:
        show_histogram(contents)
    else:
        hexdump(contents, args.line_length)


if __name__ == "__main__":
    main()
