#!/usr/bin/env python3
from argparse import ArgumentParser
from collections import Counter
from math import ceil, log
from operator import itemgetter
from string import printable, whitespace
from sys import stdin

printable = set(printable) - set(whitespace)


def sensible_block_size(input_len):
    return input_len // 2


def group_by(contents, block_size):
    r"""
    Collect data into fixed-length chunks or blocks.
    >>> list(group_by("helloworld", 4))
    ['hell', 'owor', 'ld']
    """
    block = lambda i: contents[i * block_size: i * block_size + block_size]
    content_length = len(contents)
    length = int(ceil(float(content_length) / block_size))
    result = (block(i) for i in range(length))
    return result


def entropy(s):
    p, lns = Counter(s), float(len(s))
    return max(0, -sum(count/lns * log(count/lns, 2) for count in p.values()))


def insert_spacing(line, spacing=8):
    return " ".join(n for n in group_by(line, spacing))


def pad_bytes(bytes, length):
    return list(bytes) + [-1] * (length - len(bytes))


def format_bytes(bytes, line_length):
    result = []
    for byte_group in group_by(pad_bytes(bytes, line_length), 2):
        result.append("".join("{:02x}".format(val) if val > -1 else '  '
                              for val in byte_group))
    return " ".join(result)


def format_ascii(bytes, line_length):
    def format_chars():
        for b in pad_bytes(bytes, line_length):
            if b == -1:
                yield ' '
            elif chr(b) in printable:
                yield chr(b)
            else:
                yield '.'
    return "".join(format_chars())


def get_entropy_distribution(windows):
    res = [entropy(line) for line in windows]
    return min(res), max(res)


def hexdump(contents, line_length):
    line_groups = list(group_by(contents, line_length))

    for line_no, byte_line in enumerate(line_groups):
        print("{position:08x} {bytes} {ascii} H: {entro:2.2f}".format(
            position=line_no * line_length,
            bytes=format_bytes(byte_line, line_length),
            ascii=format_ascii(byte_line, line_length),
            entro=entropy(byte_line),
        ))


def show_entropy(contents, line_length):
    for line_no, byte_line in enumerate(group_by(contents, line_length)):
        entropies = ('{:2.2f}'.format(entropy(window)) for window in byte_line)
        print("{:08x} {}".format(
            line_no * 32 * line_length,
            " ".join(entropies)),)


def show_histogram(contents):
    byte_count = Counter(contents)

    print("Byte Count")
    for key, count in sorted(
            byte_count.items(), key=itemgetter(1), reverse=True):
        print('0x{:02x} {:d}'.format(key, count))


def get_contents(file):
    if file == "-":
        return stdin.buffer.read()
    with open(file, 'rb') as fd:
        return fd.read()


def main():
    parser = ArgumentParser(description="Visualize Binary Files")
    parser.add_argument('file', help="Either '-' for stdin or a file path.")
    parser.add_argument(
        '-l', '--line-length', default=16,
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
