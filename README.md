# SIMControl

独立的系统控制中心 SIM 卡切换模块，面向普通无根越狱的 iOS 16/17。

## 功能

- 系统默认控制中心模块，标题“SIM卡切换”，采用双层 SIM 图标
- 展开后显示用户设置的 SIM 标签和两条线路的启用状态
- 通过原始 CCSIMTool 请求 SIM 线路启用/停用
- 保持设置列表图标和 Sileo 包图标不变，不依赖 ControlCenter18 或五键扩展

## 依赖

- 普通无根越狱（`/var/jb`），CCSupport (`com.opa334.ccsupport`)
- iOS 16/17 系统 CoreTelephony 和控制中心模块机制
- 仓库 `Vendor/CCSIMTool`：保留原始签名与 entitlements，不能从源码重新生成；来源和 SHA256 见 `Vendor/provenance.json`

## 构建

在 macOS 的 Xcode/iPhoneOS SDK 环境执行 `bash tools/build-macos.sh`。需要 `xcrun`、iOS SDK 的 clang/lipo/codesign、Python 3，以及仓库内的 `tools/linker/ControlCenterUIKit.framework/ControlCenterUIKit.tbd`。脚本生成签名的 arm64/arm64e 通用模块、打包为 `iphoneos-arm64` 普通无根 deb，并运行 `tools/verify.py` 静态校验；产物在 `dist/`。模块、helper、图标资源分别部署到 `/var/jb` 下相应目录。

GitHub Actions 的 `build.yml` 仅支持 `workflow_dispatch` 手动启动，源码提交不会运行构建或发布。源码取自 2026-11-13 的 `34e37ca9`，再修正普通无根安装路径和验证器。未在 macOS 编译或真机运行验证；已交付 deb 与此提交重编译结果的逐字节等价性未知，helper 在普通无根设备的运行有效性须自行核验。

## 目录

- `src/`：模块、控制器、服务和行视图源码
- `Resources/`：模块信息与图标资源
- `Vendor/`：保留签名和 entitlements 的后端工具
- `tools/`：本地检查、构建、打包和验证脚本
- `.github/workflows/`：仅手动构建的工作流
