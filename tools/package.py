#!/usr/bin/env python3
"""Stage only this standalone module; do not touch an installed control centre."""
from pathlib import Path
import gzip,io,json,shutil,tarfile
from mkdeb import pack
from simcontrol import ROOT,BUNDLE,HELPER,PROVENANCE,DEB,HELPER_SHA256,RESOURCE_HASHES,sha256,require,module_plist,control_fields,macho

def archive(root,out):
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w',format=tarfile.USTAR_FORMAT) as tar:
        for p in [root]+sorted(root.rglob('*')):
            require(not p.is_symlink(),'unexpected symbolic link')
            name='.' if p==root else './'+p.relative_to(root).as_posix()
            info=tarfile.TarInfo(name);info.uid=info.gid=0;info.uname=info.gname='root';info.mtime=0
            if p.is_dir():info.type=tarfile.DIRTYPE;info.mode=0o755;tar.addfile(info)
            elif p.is_file():
                data=p.read_bytes();info.size=len(data);info.mode=p.stat().st_mode&0o7777
                tar.addfile(info,io.BytesIO(data))
            else:raise ValueError('unexpected input '+str(p))
    with out.open('wb') as stream:
        with gzip.GzipFile(fileobj=stream,mode='wb',mtime=0) as output:output.write(buffer.getvalue())

def main():
    helper=(ROOT/'Vendor/CCSIMTool').read_bytes();require(sha256(helper)==HELPER_SHA256,'helper changed')
    module=(ROOT/'build/SIMControl').read_bytes();macho(module,module=True);macho(helper)
    info=(ROOT/'Resources/Info.plist').read_bytes();module_plist(info)
    text=(ROOT/'control').read_bytes();control_fields(text)
    stage=ROOT/'build/stage';members=ROOT/'build/deb-members'
    for p in (stage,members):
        if p.exists():shutil.rmtree(p)
        p.mkdir(parents=True)
    def put(name,data,mode=0o644):
        p=stage/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);p.chmod(mode)
    put(BUNDLE+'/SIMControl',module,0o755);put(BUNDLE+'/Info.plist',info)
    for name,digest in RESOURCE_HASHES.items():
        data=(ROOT/'Resources'/name).read_bytes();require(sha256(data)==digest,'resource changed: '+name);put(BUNDLE+'/'+name,data)
    put(HELPER,helper,0o755);put(PROVENANCE,(ROOT/'Vendor/provenance.json').read_bytes())
    control=ROOT/'build/control';control.mkdir(exist_ok=True)
    (control/'control').write_bytes(text)
    (members/'debian-binary').write_bytes(b'2.0\n')
    archive(control,members/'control.tar.gz');archive(stage,members/'data.tar.gz')
    pack(DEB,members)
    print(json.dumps({'package':str(DEB),'size':DEB.stat().st_size,'sha256':sha256(DEB.read_bytes())},indent=2))
if __name__=='__main__':main()
