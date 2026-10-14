# Phase 14 Installer Validation Matrix

2026-10-13 — **COMPLETE WITH KNOWN VALIDATION LIMITATIONS**。

PASS=已执行并符合预期；PARTIAL=部分覆盖；NOT TESTED=未执行。最终候选为 dist/release-final/LocalASR-Setup-0.1.0-win64.exe。

| 检查 | 状态 | 实际结果 / 限制 |
| --- | --- | --- |
| Inno 编译 | PASS | 6.7.3，209.668 秒；LZMA2/fast solid |
| Installer size / SHA256 | PASS | 1,303,219,736 字节；详见最终报告和 SHA256SUMS.txt |
| per-user 默认安装 | PASS | 普通用户，无管理员权限，HKCU |
| 自定义 Unicode 安装路径 | NOT TESTED | 仅测试默认路径 |
| License 页面 | PASS | 最终候选真实显示官方 PolyForm Noncommercial 1.0.0 原文 |
| 开始菜单 | PASS | 实际双击开始菜单目录内 .lnk 启动安装版 |
| 桌面快捷方式 | PARTIAL | 创建、卸载删除、重装恢复通过；未单独双击 |
| Add/Remove Programs | PASS | 正确信息，卸载删除，重装恢复 |
| 载荷哈希 | PASS | 6,366 文件一致；本次未重复 |
| 安装版 File ASR | PASS | 11 秒已有合成英文语音，large-v3 GPU，五种输出 |
| Translation / 双语 DOCX | PASS | 本地 Marian CPU + OpenCC，中文及双语输出 |
| Microphone | PARTIAL | 实际采集帧、两次启停；无真人讲话识别验证 |
| System Audio | PASS | 9 English final、9 中文；audio drop=0、translation drop=0；正常退出 |
| Overlay | PARTIAL | 安装版窗口显示、会话流程覆盖；未独立完成全部双语视觉/交互验收 |
| Model discovery | PASS | 重装后真实页面三种已有模型均显示已安装，无下载 |
| First-run / 模型缺失 | PASS | 重装后空测试数据目录，两个提示检查通过 |
| Diagnostics / isolation | PASS | frozen，清除 Conda/Python 路径，模块来自安装目录或 Windows |
| 运行中安装保护 | PASS | 退出码 7，拒绝继续，无强杀 |
| 运行中卸载保护 | PASS | 实际提示关闭应用；点击 OK 后退出码 1，未提前删除应用 |
| 正常卸载 | PASS | 退出码 0，8.841 秒；应用目录、快捷方式、HKCU 条目删除 |
| 数据 / 配置保留 | PASS | 五处保留哨兵哈希一致；真实 gui_settings.json 哈希一致 |
| 模型保留 | PASS | 默认模型目录哨兵保留；外部真实模型重装后仍识别；未重哈希全部权重 |
| Reinstall | PASS | 同一最终包，退出码 0，106.190 秒；配置不变，真实启动和模型识别通过 |
| clean shutdown | PASS | 重装后正常关闭，0 个 LocalASR 残留进程 |
| 跨版本 Upgrade | PARTIAL | 固定 AppId、同版覆盖/重装通过；没有真实旧 Installer |
| 项目许可 / 商业说明 | PASS | 官方原文；Source-available；商业说明独立 |
| 第三方分发许可 | PARTIAL | native 再分发 LEGAL REVIEW RECOMMENDED |
| 签名 / SmartScreen | PARTIAL | NotSigned；未测试公网下载信誉，不绕过防护 |
| 完整自动测试 | PASS | Conda asr，280 tests，52.584 秒，OK |

## 证据

本地 validation/phase14/：installed-core/、installed-system-retry/、installed-integrity.json、wizard.log、running-guard-final.*、uninstall-running.*、normal-final-uninstall.*、normal-uninstall-verification.json、reinstall-final-install.*、reinstall-verification.json、reinstall-startup/、reinstall-manual.json、regression-closeout.txt。

第一次静音导致的系统音频失败保留在 installed-system/，没有算 PASS。临时安装/卸载进程的 computer-use 曾授权超时，后续已有保护提示和退出证据，不再重复重试。私人路径原始日志不作为公开仓库内容发布。

物理耳机、多显示器、部分 DPI、资源管理器跨窗口拖放的历史未验证范围保持不变。详见 [最终报告](PHASE14.md)。未进入 Phase 15，未上传、发布或打 tag。
