#!/usr/bin/env python3
"""Verify the standalone deb without running its payload."""
import gzip,io,json,plistlib,struct,sys,tarfile
from pathlib import Path
from simcontrol import ROOT,DEB,BUNDLE,HELPER,PROVENANCE,HELPER_SHA256,RESOURCE_HASHES,RESOURCE_PATHS,require,sha256,macho,module_plist,control_fields

def main():
    path=Path(sys.argv[1]) if len(sys.argv)>1 else DEB
    b=path.read_bytes();require(b[:8]==b'!<arch>\n','bad ar magic');q=8;members={}
    while q<len(b):
        h=b[q:q+60];require(len(h)==60 and h[58:]==b'`\n','bad ar header')
        name=h[:16].decode().strip().rstrip('/');size=int(h[48:58]);q+=60
        require(name not in members and q+size<=len(b),'duplicate/truncated member');members[name]=b[q:q+size];q+=size+size%2
    require(q==len(b) and set(members)=={'debian-binary','control.tar.gz','data.tar.gz'},'invalid deb members')
    require(members['debian-binary']==b'2.0\n','invalid deb version')
    files={};fields=None
    for name in ('control.tar.gz','data.tar.gz'):
        raw=gzip.decompress(members[name]);off=0
        while raw[off:off+512]!=bytes(512):
            h=raw[off:off+512];require(len(h)==512 and h[257:263]==b'ustar\0' and h[156:157] not in (b'x',b'g',b'L',b'K'),'requires raw USTAR')
            size=int(h[124:136].rstrip(b'\0 ') or b'0',8);off+=512+((size+511)//512)*512
        with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tar:
            for entry in tar:
                rel=entry.name.removeprefix('./')
                require(entry.uid==entry.gid==0 and not entry.pax_headers,'unexpected ownership/PAX')
                require(not Path(rel).is_absolute() and '..' not in Path(rel).parts,'unsafe path')
                if entry.isdir():continue
                require(entry.isfile(),'unexpected link/device')
                data=tar.extractfile(entry).read()
                if name.startswith('control'):
                    require(rel=='control','unexpected maintainer script');fields=control_fields(data)
                else:
                    require(rel not in files,'duplicate file');files[rel]=(data,entry.mode)
    expected={BUNDLE+'/SIMControl',BUNDLE+'/Info.plist',HELPER,PROVENANCE}|set(RESOURCE_PATHS.values())
    require(set(files)==expected,'unexpected/missing payload file')
    require(fields,'control missing');info=module_plist(files[BUNDLE+'/Info.plist'][0])
    require(info['CFBundleDisplayName']=='SIM卡切换','wrong module title')
    require(info.get('CCSModuleSize')=={'Portrait':{'Width':1,'Height':1},'Landscape':{'Width':1,'Height':1}},'CCSupport sizes missing')
    helper=files[HELPER][0];require(sha256(helper)==HELPER_SHA256,'helper changed')
    for p,(data,mode) in files.items():require(mode==(0o755 if p in (HELPER,BUNDLE+'/SIMControl') else 0o644),'wrong file mode: '+p)
    for n,digest in RESOURCE_HASHES.items():require(sha256(files[RESOURCE_PATHS[n]][0])==digest,'icon resource mismatch: '+n)
    module_report=macho(files[BUNDLE+'/SIMControl'][0],module=True);helper_report=macho(helper)
    report={'package':path.name,'size':len(b),'sha256':sha256(b),'control':fields,'module':module_report,'helper':helper_report,'archive':'ar/gzip/raw USTAR','runtime_tested':False}
    target=ROOT/'dist/package-validation.json';target.parent.mkdir(exist_ok=True);target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('VERIFY_OK',path.name,len(b),report['sha256'])
if __name__=='__main__':main()
