# Phase 16 — Official GitHub Release

日期：2026-10-14。最终状态：**READY TO PUBLISH — AUTHORIZATION REQUIRED**。

**没有发布成功，不标记 RELEASED。** GitHub API 使用现有 Git 凭据返回 HTTP 401；gh 未安装或不在 PATH，标准安装位置亦未找到。未输出或保存凭据，未尝试交互登录、刷新或反复重试。按用户要求停在安全位置。

| # | 项目 | 实际状态 |
| --- | --- | --- |
| 1 | Phase 16 status | READY TO PUBLISH — AUTHORIZATION REQUIRED |
| 2 | Final version | 0.1.0，未改变 |
| 3 | Repository | https://github.com/769399481/LocalASR |
| 4 | Visibility | 本阶段未确认；认证 API 检查失败，后续需要确认 public |
| 5 | Main branch | 目标 main；根目录尚未初始化 Git，无当前分支 |
| 6 | Remote | 目标 origin=https://github.com/769399481/LocalASR.git；尚未添加 |
| 7 | Final commit hash | 无，本阶段未 commit |
| 8 | Commit message | 未执行；现有 Git 身份已配置，不需要虚构身份；恢复后依据远端实际历史选择消息 |
| 9 | Push | 未执行 |
| 10 | Tag | 目标 v0.1.0，未创建 |
| 11 | Tag push | 未执行 |
| 12 | Release title | 目标 LocalASR 0.1.0 |
| 13 | Release URL | 尚未创建；https://github.com/769399481/LocalASR/releases/tag/v0.1.0 仅为预期地址，不声称可用 |
| 14 | Release state | 未创建；正式发布计划为非 draft、非 prerelease |
| 15 | Release Notes | RELEASE_NOTES_0.1.0.md 已存在；未发布，保留当前 RC 措辞；恢复发布时再调整正式正文及相对链接 |
| 16 | Installer filename | LocalASR-Setup-0.1.0-win64.exe |
| 17 | Local path | dist/release-phase15/LocalASR-Setup-0.1.0-win64.exe（仓库相对路径） |
| 18 | Size | **1,303,059,102 bytes**，本阶段重新读取一致 |
| 19 | SHA256 | **D148B3ADF46660E1EC878AB7DE6D7AA01A54DDEF01AEFEA7D861D87B75AB2836**，本阶段重新计算一致 |
| 20 | SHA256SUMS | 与最终 Phase 15 EXE 一致，无 Phase 14 旧 hash，无需修改 |
| 21 | Installer upload | 未执行 |
| 22 | SHA256 upload | 未执行 |
| 23 | Source archives | 未创建 tag/Release，未验证自动 archives；不手工上传源码 ZIP |
| 24 | README rendering | 本地双语文件完整；GitHub 远端渲染本阶段未验证 |
| 25 | Language switch | 本地 README.md / README_EN.md 互链保留，Phase 15.1 已验证；远端未验证 |
| 26 | License | PolyForm Noncommercial License 1.0.0；官方原文保持不变；Source-available |
| 27 | Commercial Licensing | 商业用途单独授权；yehao769399481@gmail.com；无价格/付款新增 |
| 28 | Security | yehao769399481@gmail.com，SECURITY.md 保留 |
| 29 | Signing | UNSIGNED，未改变 |
| 30 | SmartScreen | Unknown Publisher / SmartScreen 可能提示；不建议禁用安全保护 |
| 31 | Upgrade | PARTIAL，保留真实限制 |
| 32 | macOS | 未正式支持，不作为本次发布平台 |
| 33 | Third-party notices | 存在；LEGAL REVIEW RECOMMENDED 保留；本阶段未发现明确再分发违规，不做大规模法律研究 |
| 34 | Source cleanliness | 快速检查 121 个候选文件，忽略模型、dist、build、日志、私有音频、恢复、配置、缓存、工具和验证产物；尚未 stage |
| 35 | Secrets | 模式扫描未发现凭据或真实私人开发路径；用户指定公开联系邮箱允许。不是对未来变更的绝对保证 |
| 36 | Asset list | 计划只上传最终 EXE 与 SHA256SUMS.txt；不上传模型、报告或 standalone 目录 |
| 37 | Download verification | NOT TESTED：没有已发布 asset 可下载 |
| 38 | Downloaded SHA256 | 不适用；只有本地最终 EXE 哈希已确认 |
| 39 | Known limitations | 保留 Phase 15 / 15.1 的未签名、硬件/显示器/DPI/拖放、真人麦克风、protected audio、macOS 等边界 |
| 40 | Publication blockers | 当前阻止发布的是 GitHub authentication / authorization；尚未发现产品或制品 blocker |
| 41 | Final verdict | **READY TO PUBLISH — AUTHORIZATION REQUIRED** |

## 恢复发布的准确位置

1. 用户完成 GitHub 登录授权。可安装官方 GitHub CLI 后执行 `gh auth login`，或修复现有 Git Credential Manager 登录；不要把 token 放入源码、文档或聊天。
2. 再检查 GitHub API/Release 权限、仓库 public 状态和远端 refs。此次只读 `git ls-remote` 未返回 refs，不能据此跳过恢复时的远端历史检查。
3. 初始化/确认 main 和 origin，检查 staging diff 与 source privacy，再 commit、非强制 push main。
4. 创建或核对 annotated v0.1.0，push tag，创建正式 Release 并上传最终 EXE / SHA256SUMS。
5. 验证主页、双语 README、Release 正文、assets 和 checksum；权限允许时下载到独立临时目录再校验。

认证失败后没有继续执行发布变更，根目录仍未 git init。README 未提前改成已上线，未创建草稿 Release，也未覆盖 tag、force push、改写历史或重新构建 Installer。无需重复 Phase 15 的 ASR / Translation / System Audio / Overlay / 安装验证。

原始本地证据：validation/phase16/integrity.json、source-candidate.txt、source-scan.json、status.json。凭据只用于现有认证机制的内存中请求，不写入报告或仓库。

本阶段停止，等待用户完成认证后继续发布。
