# SIMControl

独立的系统控制中心蜂窝管理模块，适用于越狱环境下的 iOS 16/17。

## 功能

- 在系统默认控制中心提供“蜂窝管理”模块
- 展开后显示各 SIM 卡线路状态
- 显示系统读取到的真实运营商名称，而不是 SIM 标签
- 保留原 CCSIM 的 SIM 线路启用/停用能力
- 不依赖 ControlCenter18 或五键扩展

## 依赖

- CCSupport (`com.opa334.ccsupport`)
- CoreTelephony
- 系统控制中心模块机制
- 越狱环境中的原始 `CCSIMTool`

## 构建

仓库只提供源码和手动触发的 GitHub Actions 工作流。工作流采用 macOS 的 iPhoneOS SDK 构建 arm64/arm64e，并生成独立 deb。

本次源码同步不包含构建产物，也未触发构建。

## 目录

- `src/`：模块、控制器、服务和行视图源码
- `Resources/`：模块信息与图标资源
- `Vendor/`：保留签名和 entitlements 的后端工具
- `tools/`：本地检查、构建、打包和验证脚本
- `.github/workflows/`：手动构建工作流
