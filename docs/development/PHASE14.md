> 当前发布信息（Phase 15）：LocalASR 0.1.0 RC；项目 https://github.com/769399481/LocalASR；PolyForm Noncommercial 1.0.0 / Source-available。下文为历史阶段记录，其中当时未确定的地址或许可不代表当前状态。

# Phase 14 — Windows Installer & Distribution

2026-10-13 最终结论：**COMPLETE WITH KNOWN VALIDATION LIMITATIONS**。

完成真实安装包编译、安装版运行、卸载与同版重装。收尾没有重建应用，也没有重复已通过的系统音频、许可证或载荷哈希验证。未上传、发布、打 tag 或进入 Phase 15。

## 最终交付

| 项目 | 结果 |
| --- | --- |
| Installer | dist/release-final/LocalASR-Setup-0.1.0-win64.exe |
| 大小 | **1,303,219,736 字节**，1.303219736 GB（十进制） |
| SHA256 | **48A0C9D3C09E3648DFC6BF7E0CF5F970E0B02C5D9ED2E5504AF9C36B1009EE99** |
| 校验文件 | dist/release-final/SHA256SUMS.txt |
| Standalone | dist/LocalASR-Phase14；2,497,284,677 字节 |
| 压缩效果 | 安装包为载荷的 52.1855%，减少约 47.8145% |
| 编译 | Inno Setup 6.7.3，成功；最终耗时 209.668 秒 |
| 签名 | NotSigned |
| 版本来源 | src/app_version.py，LocalASR 0.1.0 |
| AppId | {013B05DD-FB78-45E4-8C99-1256B77D01F2} |
| Publisher | LocalASR Project |

早期 dist/release/ 候选仍保留，但最终选择 release-final。最后一次编译仅同步卸载默认保留用户数据的隐私说明，应用载荷没有再次变化。Phase 10 / 11 / 12 / 12.5 / 12.6 回退版本未改动。

## 安装设计与验证

使用 Inno Setup，完整打包已验证载荷，LZMA2/fast solid 压缩；不替换或压缩 native DLL。不含模型，不新增 VC redist 安装器。默认 per-user 路径为 %LOCALAPPDATA%\Programs\LocalASR，PrivilegesRequired=lowest，真实普通用户安装不需要管理员权限，程序条目写入 HKCU。测试工具的沙箱放行不代表 UAC 提权。

真实最终向导显示官方 PolyForm Noncommercial 1.0.0 许可证，实际完成安装并启动应用。载荷 6,366 个文件哈希全部一致。开始菜单快捷方式已在资源管理器中实际双击启动。桌面快捷方式可选；创建、卸载删除和重装恢复通过，未单独双击。向导为 Inno 默认风格，没有新品牌设计或依赖。

用户数据与模型独立于应用目录，默认 %LOCALAPPDATA%\LocalASR。卸载保留模型、设置、输出、恢复记录、日志、缓存，没有删除这些目录的指令。

## 安装版运行结果

| 项目 | 结论 |
| --- | --- |
| File ASR | PASS：11 秒已有合成英文音频，large-v3 CUDA，TXT/DOCX/JSON/SRT/VTT 完整 |
| Translation | PASS：本地 Marian CPU + OpenCC，中文结果及双语 DOCX |
| Microphone realtime | PARTIAL：真实采集帧、两次安全启停；没有真人讲话识别验证 |
| System Audio | PASS：真实 Realtek loopback，9 条英文 final、9 条中文，音频/翻译零丢弃，正常退出 |
| Overlay | PARTIAL：安装版窗口实际显示及会话流程覆盖，未独立完成全部双语视觉和交互验收 |
| Model discovery | PASS：既有 small、large-v3、opus-mt-en-zh，重装后真实页面均显示已安装 |
| Diagnostics | PASS：frozen 安装版硬件/CUDA/依赖诊断与路径隔离 |
| First-run | PASS：重装后空数据目录中首次准备、模型缺失提示均通过 |
| clean shutdown | PASS：重装后正常关闭，0 个 LocalASR 残留进程 |

系统音频首次因静音未识别没有计为 PASS；取消静音后重测成功。末条 endpoint 延迟约 0.719 秒、翻译约 0.515 秒、总约 1.234 秒，仅为本次短测末条指标。partial 合并/丢弃并非音频丢弃，不声称所有事件计数均为零。

真实安装版清除 Conda/Python 搜索路径、使用独立工作目录及本地离线模型，加载模块来自安装目录或 Windows。VC runtime 随载荷保留；本机已有系统环境，不等同干净 Windows 认证。

## 保护、卸载、保留、重装

- 运行中安装：拒绝继续，退出码 **7**，未强杀 LocalASR。
- 运行中卸载：实际提示先关闭 LocalASR，点击 OK 后退出码 **1**；InitializeUninstall=False，未提前删除应用文件。computer-use 临时进程授权曾超时，但后续已有实际提示和退出证据，本次不重复重试。
- 正常卸载：应用先正常关闭，卸载退出码 **0**，耗时 **8.841 秒**；应用目录、开始菜单、桌面快捷方式、Add/Remove Programs 条目均删除。
- 用户数据：models/output/recovery/logs/cache 五处保留哨兵哈希一致；真实 gui_settings.json 卸载前后及重装后 SHA256 均与本地验证记录一致（个人配置指纹不公开）。哨兵验证目录保留策略，不声称比对全部历史数据。
- 模型保留：默认模型目录哨兵未变，外部实际模型仍被重装后的真实 GUI 识别，无重新下载；未重复计算全部权重哈希。
- Reinstall：同一 release-final 安装包，退出码 **0**，耗时 **106.190 秒**；配置不变，快捷方式及程序条目恢复。真实 EXE 使用原测试数据目录正常启动，三种模型显示已安装，随后正常退出。
- Upgrade：**PARTIAL**。同版覆盖和卸载后重装通过；没有真实旧 Installer，不将其当作跨版本升级 PASS。

最终候选仍安装在默认用户目录，应用已关闭。保留测试日志、用户数据和模型，没有额外清理。

## 自动测试与资源记录

Conda asr 中执行完整自动回归：**280 tests，52.584 秒，OK**。证据：validation/phase14/regression-closeout.txt。没有弱化核心断言，没有新增应用依赖，没有重写 ASR、Translation 或 GUI。

安装过程中采样到 Inno 实际子进程峰值工作集约 37,871,616 字节，不是严格全程峰值；编译峰值内存未测量。时间受本机缓存和负载影响。

## 许可与修改范围

项目采用 **PolyForm Noncommercial License 1.0.0**，表述为 **Source-available / 源码公开**，不称 OSI 开源。官方原文保持不变，商业使用需单独联系 **yehao769399481@gmail.com**。商业许可说明与官方 LICENSE 分开；第三方组件保留各自许可。未发送邮件。

主要文件：LICENSE、COMMERCIAL_LICENSE.md、README.md、SECURITY.md、CONTRIBUTING.md、PRIVACY.md、THIRD_PARTY_NOTICES.md、RELEASE_NOTES_TEMPLATE.md；src/ui_strings.py 的许可说明；distribution/build.py 的独立 Phase 14 入口；distribution/installer/LocalASR.iss、build_installer.ps1、validate_installed.ps1；旧 distribution/installer.iss 兼容入口；docs/INSTALLER.md、docs/CODE_SIGNING.md、docs/DEVELOPMENT.md 和本阶段报告。收尾只调整本地验证辅助脚本的最终候选路径并更新报告。

已核查宽松许可、PyInstaller exception、Inno 许可边界。**LEGAL REVIEW RECOMMENDED**：实际 FFmpeg/PyAV、NVIDIA、Microsoft VC runtime 等二进制再分发、源码/重链接义务和传递通知仍需适当审查，工程测试不等同法律许可确认。

## Known limitations 与 Release blockers

未完整验证：真实跨版本 Upgrade、干净 Windows / Windows 10、自定义 Unicode 安装路径、真人麦克风讲话、耳机专项、实体多显示器、部分物理 DPI、资源管理器跨窗口拖放。桌面快捷方式未单独双击，Overlay 安装版完整视觉验收未重做。macOS 尚未实现。

当前没有发现阻止本阶段本地安装、卸载、重装的功能问题。**这不等于批准公开发布**：公开分发前仍需完成 native 第三方许可审查、确定正式仓库/发布地址、决定签名及未签名提示策略，并执行发布清单。当前安装包未签名，互联网下载后的 SmartScreen 信誉未验证，没有绕过安全防护。

详见 [验证矩阵](PHASE14_INSTALLER_VALIDATION.md)。Phase 14 按范围完成并停止；没有开展 Phase 15，也没有上传、发布或打 tag。



