#!/usr/bin/env python3
"""Write Debian's three-member ar container; never invoke the host ar tool."""
from pathlib import Path
import argparse
import os

MEMBERS = ('debian-binary', 'control.tar.gz', 'data.tar.gz')


def pack(output, member_dir, epoch=0):
    output, member_dir = Path(output), Path(member_dir)
    if epoch < 0:
        raise ValueError('SOURCE_DATE_EPOCH must be nonnegative')
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + '.tmp')
    try:
        with temporary.open('wb') as archive:
            archive.write(b'!<arch>\n')
            for name in MEMBERS:
                body = (member_dir / name).read_bytes()
                fields = ((name, 16), (str(epoch), 12), ('0', 6), ('0', 6),
                          ('100644', 8), (str(len(body)), 10))
                if any(len(value.encode('ascii')) > width for value, width in fields):
                    raise ValueError('ar header field exceeds its native width')
                header = ''.join(value.ljust(width) for value, width in fields).encode('ascii') + b'`\n'
                if len(header) != 60:
                    raise ValueError('ar header must be exactly 60 bytes')
                archive.write(header)
                archive.write(body)
                if len(body) & 1:
                    archive.write(b'\n')
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('member_dir', type=Path)
    parser.add_argument('--epoch', type=int, default=int(os.environ.get('SOURCE_DATE_EPOCH', '0')))
    args = parser.parse_args()
    result = pack(args.output, args.member_dir, args.epoch)
    print(f'{result}: {result.stat().st_size} bytes')


if __name__ == '__main__':
    main()
