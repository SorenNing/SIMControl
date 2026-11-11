from pathlib import Path
import struct

root = Path(__file__).resolve().parents[1]
for path in [root / 'Vendor/CCSIMTool', Path('/var/minis/workspace/ccsim-five3-review/five3/CCSIM')]:
    data = path.read_bytes()
    print(path, len(data), data[:4].hex())
    if data[:4] == bytes.fromhex('cafebabe'):
        count = struct.unpack_from('>I', data, 4)[0]
        slices = [struct.unpack_from('>IIIII', data, 8 + 20*i) for i in range(count)]
    else:
        slices = [(0, 0, 0, len(data), 0)]
    for cpu, sub, offset, size, align in slices:
        thin = data[offset:offset+size]
        print(' slice', hex(cpu), hex(sub), offset, size, align, 'header', thin[:32].hex())
        ncmds = struct.unpack_from('<I', thin, 16)[0]
        pos = 32
        for _ in range(ncmds):
            cmd, length = struct.unpack_from('<II', thin, pos)
            if cmd in (0xc, 0x80000018, 0x8000001f):
                nameoff = struct.unpack_from('<I', thin, pos+8)[0]
                print(' dylib', thin[pos+nameoff:pos+length].split(b'\0')[0])
            elif cmd in (0x1d, 0x80000034):
                off, z = struct.unpack_from('<II', thin, pos+8)
                print(' data', hex(cmd), off, z)
                if cmd == 0x1d:
                    magic, length2, count = struct.unpack_from('>III', thin, off)
                    print(' signature',hex(magic), length2, count)
                    for j in range(count):
                        typ, rel = struct.unpack_from('>II', thin, off+12+8*j)
                        bmagic, blen = struct.unpack_from('>II', thin, off+rel)
                        print('  sigblob',hex(typ),hex(bmagic),blen)
            pos += length
