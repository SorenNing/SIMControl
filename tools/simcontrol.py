"""Shared constants and read-only Mach-O checks (Python standard library only)."""
from pathlib import Path
import hashlib
import plistlib
import struct

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = 'com.ning.simcontrol'
VERSION = '1.0'
BUNDLE_ID = PACKAGE + '.module'
BUNDLE = 'Library/ControlCenter/Bundles/SIMControl.bundle'
HELPER = 'usr/libexec/SIMControl/CCSIMTool'
PROVENANCE = 'usr/libexec/SIMControl/provenance.json'
HELPER_SHA256 = 'b9ef962cd0e75374c5499f955d57595ca8367b5ecb8d8c0c2d067a0849e218a9'
PRIVATE_DYLIB = '/System/Library/PrivateFrameworks/ControlCenterUIKit.framework/ControlCenterUIKit'
DEB = ROOT / 'dist' / f'{PACKAGE}_{VERSION}_iphoneos-arm64e.deb'
SOURCES = tuple(f'src/SIMControl{name}.m' for name in ('Module', 'Controller', 'Service', 'Row'))
RESOURCE_HASHES = {
    'CCSIM@3x.png': '097dd959719755c747f1474a790b44358bfb0d88b7eb70b9245573a15066ab53',
    'SettingsIcon@3x.png': 'fb98b7f82820e6e05fb3063774577b6834bad20df62e6a507b60be9da26af039',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def signature(thin, offset, length, require_adhoc=False):
    """Validate CodeDirectory page hashes, including the unmodified helper."""
    blob = thin[offset:offset + length]
    require(len(blob) == length and length >= 12, 'truncated code signature')
    magic, total, count = struct.unpack_from('>III', blob)
    require(magic == 0xfade0cc0 and 12 + 8*count <= total <= length, 'bad signature SuperBlob')
    slots = {}
    for i in range(count):
        slot, pos = struct.unpack_from('>II', blob, 12 + 8*i)
        require(slot not in slots and 12 + 8*count <= pos <= total - 8, 'bad signature index')
        kind, size = struct.unpack_from('>II', blob, pos)
        require(size >= 8 and pos + size <= total, 'signature blob out of range')
        slots[slot] = (kind, blob[pos:pos + size])
    directories = []
    for slot, (kind, cd) in slots.items():
        if slot != 0 and not 0x1000 <= slot <= 0x1005:
            continue
        require(kind == 0xfade0c02 and len(cd) >= 44, 'bad CodeDirectory')
        _, _, version, flags, hashes, ident, special, pages, limit = struct.unpack_from('>9I', cd)
        size, algorithm, _, shift = struct.unpack_from('4B', cd, 36)
        algorithms = {1: ('sha1', 20), 2: ('sha256', 32), 3: ('sha256', 20), 4: ('sha384', 48)}
        require(algorithm in algorithms and size == algorithms[algorithm][1], 'unsupported code hash')
        require(0 < shift <= 16 and 0 < limit <= offset, 'invalid signed range')
        if version >= 0x20300 and len(cd) >= 64:
            require(struct.unpack_from('>Q', cd, 56)[0] in (0, limit), 'unexpected 64-bit code limit')
        page_size = 1 << shift
        require(pages == (limit + page_size - 1)//page_size, 'CodeDirectory page count mismatch')
        require(hashes - special*size >= 44 and hashes + pages*size <= len(cd), 'code hash table out of range')
        require(44 <= ident < len(cd) and b'\0' in cd[ident:], 'missing signing identifier')
        if require_adhoc:
            require(flags & 2, 'module must have its own ad-hoc signature')
        for page in range(pages):
            content = thin[page*page_size:min((page + 1)*page_size, limit)]
            digest = hashlib.new(algorithms[algorithm][0], content).digest()[:size]
            require(digest == cd[hashes + page*size:hashes + (page + 1)*size], 'code page hash mismatch')
        for special_slot in (2, 5, 7):
            if special_slot in slots:
                require(special_slot <= special, 'signature special slot is not hashed')
                digest = hashlib.new(algorithms[algorithm][0], slots[special_slot][1]).digest()[:size]
                require(digest == cd[hashes - special_slot*size:hashes - (special_slot - 1)*size], 'signature special-slot hash mismatch')
        directories.append({'slot': slot, 'identifier': cd[ident:].split(b'\0')[0].decode(),
                            'flags': hex(flags), 'hash_type': algorithm, 'code_pages': pages})
    require(any(item['slot'] == 0 for item in directories), 'missing primary CodeDirectory')
    entitlements = None
    if 5 in slots:
        require(slots[5][0] == 0xfade7171, 'bad XML entitlement blob')
        entitlements = plistlib.loads(slots[5][1][8:])
        require(isinstance(entitlements, dict), 'invalid helper entitlement dictionary')
    return {'sha256': sha256(blob), 'slots': sorted(slots), 'directories': directories,
            'entitlement_keys': sorted(entitlements or {})}


def chained_formats(thin, offset, length, subtype):
    blob = thin[offset:offset + length]
    require(len(blob) == length and length >= 28, 'truncated chained fixups')
    version, starts, imports, symbols, count, import_format, symbol_format = struct.unpack_from('<7I', blob)
    require(version == 0 and 28 <= starts <= length - 4, 'bad chained fixups header')
    require(0 <= imports <= length and 0 <= symbols <= length and symbol_format == 0, 'bad chained data offsets')
    widths = {1: 4, 2: 8, 3: 16}
    require(import_format in widths and imports + count*widths[import_format] <= length, 'bad chained imports table')
    segments = struct.unpack_from('<I', blob, starts)[0]
    require(starts + 4 + 4*segments <= length, 'bad chained segment table')
    formats = set()
    for i in range(segments):
        relative = struct.unpack_from('<I', blob, starts + 4 + 4*i)[0]
        if not relative:
            continue
        pos = starts + relative
        require(starts + 4 + 4*segments <= pos <= length - 22, 'bad chained segment offset')
        size, page_size, pointer_format, _, _, pages = struct.unpack_from('<IHHQIH', blob, pos)
        require(22 + 2*pages <= size and pos + size <= length, 'bad chained page table')
        require(page_size in (4096, 16384), 'unsupported chained page size')
        allowed = {1, 9, 12} if subtype == 0x80000002 else {2, 6}
        require(pointer_format in allowed, f'unsupported iOS 16/17 chained pointer format {pointer_format}')
        formats.add(pointer_format)
    require(formats, 'empty chained fixups')
    return {'formats': sorted(formats), 'import_format': import_format, 'imports': count}


def macho(data, module=False):
    if data[:4] == b'\xca\xfe\xba\xbe':
        require(len(data) >= 8, 'truncated fat header')
        count = struct.unpack_from('>I', data, 4)[0]
        require(0 < count <= 4 and 8 + 20*count <= len(data), 'bad fat architecture table')
        slices = [struct.unpack_from('>IIIII', data, 8 + 20*i) for i in range(count)]
    else:
        require(not module and len(data) >= 32, 'module must be a universal Mach-O')
        cpu, subtype = struct.unpack_from('<II', data, 4)
        slices = [(cpu, subtype, 0, len(data), 0)]
    if module:
        require(len(slices) == 2 and {s[1] for s in slices} == {0, 0x80000002}, 'module needs arm64 and arm64e ABI-v2 (0x80000002)')
    result, occupied = [], []
    for cpu, subtype, offset, size, alignment in slices:
        require(cpu == 0x100000c and subtype in (0, 0x80000002), 'unsupported CPU subtype')
        require(0 <= alignment <= 20 and offset % (1 << alignment) == 0, 'bad fat alignment')
        require(size >= 32 and 0 <= offset <= len(data) - size, 'slice outside file')
        if len(slices) > 1 or offset:
            require(offset >= 8 + 20*len(slices), 'slice overlaps fat header')
        require(all(offset + size <= a or offset >= b for a, b in occupied), 'overlapping fat slices')
        occupied.append((offset, offset + size))
        thin = data[offset:offset + size]
        require(thin[:4] == b'\xcf\xfa\xed\xfe', 'expected little-endian 64-bit Mach-O')
        _, tcpu, tsub, kind, count, cmdsize, _, _ = struct.unpack_from('<8I', thin)
        require((tcpu, tsub) == (cpu, subtype), 'fat/thin CPU subtype mismatch')
        require(kind in ((6, 8) if module else (2,)), 'unexpected Mach-O file type')
        require(0 < count <= cmdsize//8 and 32 + cmdsize <= size, 'invalid load command table')
        pos, loads, commands = 32, [], {}
        for _ in range(count):
            require(pos + 8 <= 32 + cmdsize, 'truncated load command')
            cmd, length = struct.unpack_from('<II', thin, pos)
            require(length >= 8 and length % 8 == 0 and pos + length <= 32 + cmdsize, 'invalid load command length')
            if cmd in (0xc, 0x80000018, 0x8000001f, 0x20, 0x80000023):
                require(length >= 24, 'truncated dylib load command')
                string_pos = struct.unpack_from('<I', thin, pos + 8)[0]
                require(24 <= string_pos < length, 'invalid dylib path offset')
                raw = thin[pos + string_pos:pos + length]
                require(b'\0' in raw, 'unterminated dylib name')
                loads.append({'command': hex(cmd), 'path': raw.split(b'\0')[0].decode()})
            if cmd in (0x1d, 0x80000034):
                require(cmd not in commands and length == 16, 'duplicate or invalid linkedit command')
                a, b = struct.unpack_from('<II', thin, pos + 8)
                require(a >= 32 + cmdsize and b > 0 and a + b <= size, 'linkedit data outside slice')
                commands[cmd] = (a, b)
            if cmd == 0x32:
                require(length >= 24, 'bad build version')
                platform, minimum = struct.unpack_from('<II', thin, pos + 8)
                require(platform == 2, 'Mach-O must target iPhoneOS')
                if module:
                    require(minimum == 16 << 16, 'module deployment target must be iOS 16.0')
            pos += length
        require(pos == 32 + cmdsize, 'load command size mismatch')
        require(0x1d in commands, 'missing code signature')
        signed = signature(thin, *commands[0x1d], require_adhoc=module)
        chained = None
        if module:
            require(any(item['path'] == PRIVATE_DYLIB and item['command'] == '0xc' for item in loads), 'ControlCenterUIKit must be a real LC_LOAD_DYLIB')
            denied = ('cc18', 'c18five', 'controlcenter18', 'substrate', 'substitute', 'libhooker', 'ellekit')
            require(all(not any(token in item['path'].lower() for token in denied) for item in loads), 'foreign CC18 or hook-engine dependency')
            require(0x80000034 in commands, 'module requires LC_DYLD_CHAINED_FIXUPS')
            chained = chained_formats(thin, *commands[0x80000034], subtype)
        result.append({'cpu': hex(cpu), 'subtype': hex(subtype), 'size': size,
                       'loads': loads, 'signature': signed, 'chained_fixups': chained})
    if not module:
        require(len(result) == 1 and result[0]['subtype'] == '0x0', 'original helper must remain arm64')
        require({5, 7}.issubset(result[0]['signature']['slots']), 'original helper XML/DER entitlements must remain present')
    return {'sha256': sha256(data), 'size': len(data), 'slices': result}


def control_fields(data):
    fields = {}
    for line in data.decode('utf-8').splitlines():
        require(line and not line[0].isspace() and ':' in line, 'control must contain simple nonempty fields')
        key, value = line.split(':', 1)
        require(key not in fields and value.strip(), 'duplicate or empty control field')
        fields[key] = value.strip()
    wanted = {'Package': PACKAGE, 'Version': VERSION, 'Architecture': 'iphoneos-arm64e',
              'Maintainer': 'Ning&Netskao', 'Author': 'Ning&Netskao',
              'Depends': 'firmware (>= 16.0), firmware (<< 18.0), com.opa334.ccsupport',
              'Icon': f'file:///{BUNDLE}/SettingsIcon@3x.png'}
    for key, value in wanted.items():
        require(fields.get(key) == value, f'incorrect control field: {key}')
    return fields


def module_plist(data):
    info = plistlib.loads(data)
    wanted = {'CFBundleIdentifier': BUNDLE_ID, 'CFBundleExecutable': 'SIMControl',
              'NSPrincipalClass': 'SIMControlModule', 'CFBundlePackageType': 'BNDL',
              'CFBundleShortVersionString': VERSION, 'MinimumOSVersion': '16.0',
              'UIDeviceFamily': [1, 2], 'ModuleSize': {'columns': 1, 'rows': 1},
              'CCSModuleDefaultSize': {'Width': 1, 'Height': 1}}
    for key, value in wanted.items():
        require(info.get(key) == value, f'incorrect module Info.plist key: {key}')
    require(info.get('CFBundleIcons', {}).get('CFBundlePrimaryIcon', {}).get('CFBundleIconFiles') == ['SettingsIcon'], 'module must reuse SettingsIcon')
    return info
