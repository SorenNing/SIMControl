from pathlib import Path
import hashlib,json,plistlib,subprocess,time
root=Path(__file__).resolve().parents[1]
out=root/'local-checks';out.mkdir(exist_ok=True)
sources=['src/SIMControlModule.m','src/SIMControlController.m','src/SIMControlService.m','src/SIMControlRow.m']
report={'checks':[],'ios_built':False,'device_tested':False}
for arch in ('arm64e','arm64'):
    for name in sources:
        start=time.monotonic()
        cmd=['clang-19','-fsyntax-only','-fobjc-arc','-fblocks','-Werror=implicit-function-declaration','-Werror=objc-method-access','-target',arch+'-apple-ios16.0','-isysroot','/var/minis/shared/sdks/iPhoneOS16.5.sdk','-Isrc',name]
        log=out/(arch+'-'+Path(name).name+'.log')
        with log.open('w') as f:p=subprocess.run(cmd,cwd=root,stdout=f,stderr=subprocess.STDOUT,timeout=240)
        item={'arch':arch,'source':name,'exit':p.returncode,'seconds':round(time.monotonic()-start,1)}
        report['checks'].append(item);(out/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(item),flush=True)
        if p.returncode:raise SystemExit(p.returncode)
report['sha256']={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'src').glob('*')) if p.is_file()}
report['passed']=True
(out/'validation.json').write_text(json.dumps(report,indent=2));print('ALL_SYNTAX_PASSED',flush=True)
