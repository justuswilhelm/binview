#!/usr/bin/env python3
from argparse import ArgumentParser
from collections import Counter
from colorsys import hls_to_rgb
from math import ceil, log
from string import printable, whitespace
from sys import stdin

printable = set(printable) - set(whitespace)


def sensible_line_length(input_len):
    pows = [2 ** n for n in range(3, 4)]
    for pow in reversed(pows):
        if input_len % pow == 0:
            return pow
    return 16


def group_by(contents, block_size=None):
    r"""
    Collect data into fixed-length chunks or blocks.
    >>> list(group_by("helloworld", 4))
    ['hell', 'owor', 'ld']
    """
    block = lambda i: contents[i * block_size: i * block_size + block_size]
    content_length = len(contents)
    block_size = block_size or sensible_line_length(content_length)
    length = int(ceil(float(content_length) / block_size))
    result = [block(i) for i in range(length)]
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
    hue_map = lambda val: val / 255.0
    r, g, b = [int(v * 255) for v in hls_to_rgb(hue_map(val), 0.5, 1)]
    return format_colored("{:02x}".format(val), r, g, b)


def entropy_color(entropy, min_entropy, max_entropy):
    g = int((float(entropy - min_entropy) / (max_entropy - min_entropy)) * 255)
    return (255 - g, g, 0)


def format_entropy(entropy, min_entropy, max_entropy):
    entropy_formatted = "Entropy: {}".format(round(entropy, 2))
    return format_colored(
        entropy_formatted, *entropy_color(entropy, min_entropy, max_entropy))


def format_ascii(bytes):
    return " ".join(group_by("".join(
        b if b in printable else '.' for b in
        map(chr, filter(lambda x: x is not None, bytes)))))


def format_colored(s, r, g, b):
    return "\x1b[38;2;{red};{green};{blue}m{s}\x1b[0m".format(
        red=r, green=g, blue=b, s=s,)


def get_entropy_distribution(windows):
    res = [entropy(line) for line in windows]
    return min(res), max(res)


def main():
    parser = ArgumentParser(description="Visualize Binary Files")
    parser.add_argument('file', help="Either '-' for stdin or a file path.")
    parser.add_argument(
        '-l', '--line-length', default=24,
        help='Specify how many bytes per line should be shown.',
    )
    args = parser.parse_args()
    print(args)

    if args.file == "-":
        contents = stdin.buffer.read()
    else:
        with open(args.file, 'rb') as fd:
            contents = fd.read()
    assert contents, "Input was empty."

    line_groups = group_by(contents, args.line_length)
    block_size = len(line_groups[0])

    min_entropy, max_entropy = get_entropy_distribution(line_groups)

    for line_no, byte_line in enumerate(line_groups):
        if len(byte_line) < block_size:
            byte_line = byte_line.ljust(block_size, b'\0')
        print("{position:08x} {bytes} {ascii} {entro}".format(
            position=line_no * block_size,
            bytes=format_bytes(byte_line),
            ascii=format_ascii(byte_line),
            entro=format_entropy(entropy(byte_line), min_entropy, max_entropy),
        ))


if __name__ == "__main__":
    main()
