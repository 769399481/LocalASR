# Windows Installer

技术：Inno Setup 6；维护入口为 `distribution/installer/LocalASR.iss`。旧 `distribution/installer.iss` 只是 include 兼容入口，不维护第二套安装方案。

固定 AppId：`{013B05DD-FB78-45E4-8C99-1256B77D01F2}`，沿用早期未发布脚本。升级不得随意改变。Publisher 为 `LocalASR Project`，项目 URL 为 https://github.com/769399481/LocalASR，支持链接为该仓库 /issues，更新链接为 /releases；无独立官网。

## 构建

使用官方 [Inno Setup](https://jrsoftware.org/isinfo.php) 编译器；可通过 `-Compiler` 传入已安装的 ISCC.exe。开发机已有 6.7.3，本阶段不安装另一套工具链。

```powershell
# 仅当需要更新载荷时；独立目标保留 Phase 10–14：
conda run -n asr --no-capture-output python distribution/build.py --variant optimized --phase15
# 只检查载荷 / 版本 / 编译器，不编译：
.\distribution\installer\build_installer.ps1 -Standalone dist/LocalASR-Phase15 -OutputDirectory dist/release-phase15 -CheckOnly
# 编译到独立 RC 目录；已有产物会拒绝覆盖：
.\distribution\installer\build_installer.ps1 -Standalone dist/LocalASR-Phase15 -OutputDirectory dist/release-phase15
# 自定义已验证载荷、编译器与输出目录：
# 使用 -Standalone、-Compiler、-OutputDirectory 三个参数
```

版本仅从 `src/app_version.py` 读取并与载荷 EXE ProductVersion 比较。输出 `LocalASR-Setup-<version>-win64.exe`、`SHA256SUMS.txt`、`build-summary.json`。`dist/` 被 Git 忽略。构建脚本不安装 / 升级依赖，不压缩或删除 native DLL，不打包模型。

压缩使用 LZMA2/fast + solid；应用资源保持完整。Inno 自动按载荷计算所需安装空间，不用固定错误数字。还要为安装包、临时解压和以后按需下载的模型预留空间。此脚本可重复按相同输入构建，不宣称时间戳等因素下逐字节可复现。

## 安装、升级、卸载

- Windows 10 / 11 x64 目标；每用户安装，`PrivilegesRequired=lowest`，默认 `%LOCALAPPDATA%\Programs\LocalASR`。
- 模型 / 设置 / 日志 / Recovery 默认在 `%LOCALAPPDATA%\LocalASR`，导出还可能位于用户自选目录。
- 创建开始菜单 LocalASR，可选桌面快捷方式，默认不选。Finish 可启动应用，不打开浏览器。
- 许可证页面使用未修改的 PolyForm 官方原文。商业授权信息单独随包提供。
- 升级在相同 AppId 下覆盖应用文件，不删除用户数据。不提供激进删除旧目录；不同历史版本出现废弃文件时需要显式逐项迁移规则，不能递归清空安装目录。
- 安装 / 卸载前用 WMI 检查 LocalASR 进程，存在任何实例或无法检查时暂停 / 拒绝，要求用户正常关闭；不强杀。安装另启用 Restart Manager，不自动重启应用。
- 卸载无 `UninstallDelete`，不删除模型、设置、导出或恢复数据。没有可选数据清除，以降低误删风险。

尚无正式上一版本 Installer，升级测试只能按同 AppId 受控重装评估，不能冒充真实跨版本迁移通过。应用图标沿用 EXE，Setup 使用 Inno 默认图标；本阶段不做新品牌设计。

签名见 [CODE_SIGNING](CODE_SIGNING.md)。第三方分发复核见 [THIRD_PARTY_NOTICES](../THIRD_PARTY_NOTICES.md)，不把主项目 PolyForm 条款套给第三方。


