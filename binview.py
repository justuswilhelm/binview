#!/usr/bin/env python3
from argparse import ArgumentParser
from collections import Counter
from math import ceil, log
from operator import itemgetter
from string import printable, whitespace
from sys import stdin

printable = set(printable) - set(whitespace)


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
        print("{:08x} {:2.2f}".format(
            line_no * 32 * line_length,
            entropy(byte_line)))


def show_histogram(contents):
    byte_count = Counter(contents)

    print("Byte Count")
    for key, count in sorted(
            byte_count.items(), key=itemgetter(1), reverse=True):
        print('{:02x} ({}) {:d}'.format(key, chr(key) if chr(key) in printable
                                        else bytes([key]), count))


def correlation(a, b, n, window=10):
    """
    Correlation method that just measures == and not *. Great for detecting
    text similarity.

    >>> correlation([1, 1], [1, 1], 0)
    2
    >>> correlation([1, 0], [0, 1], 0)
    0
    >>> correlation([1, 0], [0, 1], 1) # b -> [1, 0]
    1
    """
    def shift():
        return b[n:] + [None] * (len(a) - n)
    assert len(a) == len(b)
    a, b = list(a), list(b)

    return sum(a == b for a, b in zip(a[:window], shift()[:window]))


def show_autocorrelation(contents, short=False, no_peaks=5, max_n=100,
                         preview=10):
    corrs = [
        correlation(contents, contents, n) for n in range(
            min(len(contents), max_n))]
    peaks = sorted(enumerate(corrs), reverse=True, key=itemgetter(1))
    if len(peaks) > 1:
        if short:
            print(peaks[1][0])
            return

        print("Potential periodicity: {} bytes".format(peaks[1][0]))
        print("Offset Content")
        for pos, corr in peaks[:no_peaks]:
            print("{:03x} {}... {}".format(
                pos, contents[pos:pos+preview],
                "(comparison)" if pos == 0 else ""))
    else:
        if short:
            print(0)
            exit(1)
        print("No periodicity")


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
    parser.add_argument(
        '-a', '--autocorrelation', default=False, action='store_true',
        help='Show autocorrelation',
    )
    parser.add_argument(
        '-s', '--short-autocorrelation', default=False, action='store_true',
        help='Output only the first candidate for periodicty',
    )
    args = parser.parse_args()
    assert sum((args.entropy_only, args.histogram, args.autocorrelation)) in [0, 1], """
Can only select one mode"""

    contents = get_contents(args.file)

    if args.entropy_only:
        show_entropy(contents, args.line_length)
    elif args.histogram:
        show_histogram(contents)
    elif args.autocorrelation:
        show_autocorrelation(contents, short=args.short_autocorrelation)
    else:
        hexdump(contents, args.line_length)


if __name__ == "__main__":
    main()
