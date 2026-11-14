from pathlib import Path
import hashlib,json,plistlib,shutil
root=Path('/var/minis/workspace/SIMControl')
base=Path('/var/minis/workspace/ccsim-five3-review/five3')
# Derive the registration plist from the original, including device-family keys.
p=plistlib.loads((base/'Info.plist').read_bytes())
p.update(CFBundleExecutable='SIMControl',CFBundleIdentifier='com.ning.simcontrol.module',CFBundleName='SIM卡切换',CFBundleDisplayName='SIM卡切换',CFBundleShortVersionString='1.0',CFBundleVersion='1',NSPrincipalClass='SIMControlModule',MinimumOSVersion='16.0')
p['ModuleSize']={'columns':1,'rows':1}
p['CCSModuleDefaultSize']={'Width':1,'Height':1}
p['CCSModuleSize']={'Portrait':{'Width':1,'Height':1},'Landscape':{'Width':1,'Height':1}}
p['CFBundleIcons']={'CFBundlePrimaryIcon':{'CFBundleIconFiles':['SettingsIcon']}}
(root/'Resources/Info.plist').write_bytes(plistlib.dumps(p,sort_keys=False))
for name in ('CCSIM@3x.png','SettingsIcon@3x.png'):
    shutil.copyfile(base/name,root/'Resources'/name)
helper=Path('/var/minis/workspace/ccsim-five3-review/CCSIMTool')
shutil.copyfile(helper,root/'Vendor/CCSIMTool')
(root/'Vendor/CCSIMTool').chmod(0o755)
manifest={'CCSIMTool':{'source':'ControlCenter18 3.0-beta4 original CCSIM tool; developed by Netskao','size':helper.stat().st_size,'sha256':hashlib.sha256(helper.read_bytes()).hexdigest(),'cpu':'arm64','recompiled':False},'original_module':'netskao.ccsim','original_module_binary_included':False,'resources':[{'file':n,'sha256':hashlib.sha256((base/n).read_bytes()).hexdigest()} for n in ('CCSIM@3x.png','SettingsIcon@3x.png')]}
(root/'Vendor/provenance.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('RESOURCES_PREPARED',root)
