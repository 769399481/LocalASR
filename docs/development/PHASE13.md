> 当前发布信息（Phase 15）：LocalASR 0.1.0 RC；项目 https://github.com/769399481/LocalASR；PolyForm Noncommercial 1.0.0 / Source-available。下文为历史阶段记录，其中当时未确定的地址或许可不代表当前状态。

> 许可状态更新：以下为历史记录。Phase 14 起 LocalASR 使用 PolyForm Noncommercial 1.0.0，定位 Source-available（源码公开）；商业授权见根目录 COMMERCIAL_LICENSE.md。

# Phase 13 — Repository Cleanup & GitHub Preparation

日期：2026-10-12。结论：**Phase 13 COMPLETE — repository preparation only; public release pending owner decisions**。

本阶段未初始化项目 Git 仓库、未提交、未创建远端、未上传 EXE、未打 tag、未制作 Installer。用本地忽略目录内的临时 Git probe 验证真实忽略规则，不等于对项目作首次提交。

| # | 项目 | 最终结果 |
| --- | --- | --- |
| 1 | Cleanup Plan | [清理清单](CLEANUP_PLAN.md) 在移动前建立；扫描所有顶层目录，按 KEEP / REGENERATABLE / ARCHIVE / DELETE / REVIEW 分类 |
| 2 | KEEP | src、tests、requirements、构建入口 / spec / hooks、公共说明、GitHub 模板保留 |
| 3 | ARCHIVE | Phase 7–12.6 报告移入 docs/development；旧 DEVELOPMENT 成为 CORE_HISTORY。旧 README / 报告原件和两份过期迁移脚本保存在本地 archive/local-originals |
| 4 | DELETE | 没有永久删除；根目录空文件 6.16 移入本地归档 |
| 5 | REGENERATABLE | build、dist、vendor runtime、生成 notices、Python cache、临时验证产物忽略，仍留本地 |
| 6 | 仓库结构 | 公开结构见下方；本地私有目录存在但不进入 Git 候选清单 |
| 7 | .gitignore | 覆盖模型、构建、日志、录音输入 / 导出、Recovery、配置、缓存、IDE、OS 元数据、wheel / EXE / DLL；未误排除 spec、脚本、docs、tests |
| 8 | Models | large-v3、small、Marian、HF cache 和模型权重均排除；README 说明首次按需下载 |
| 9 | Build artifacts | 约 19.38 GB 的历史 dist 内容留在本地；不提交 2.497 GB standalone。以后通过 Releases 提供完整目录包 |
| 10 | Phase reports | docs/development/PHASE7.md 至 PHASE12_6.md；历史路径已脱敏，原件保留 |
| 11 | Validation | 原始证据整体本地忽略，不删除唯一证据；[公开验证摘要](VALIDATION.md) 保留测试、性能、包体和范围索引 |
| 12 | README | 先功能、下载状态、使用、隐私、系统要求、限制，再开发入口；没有假 Release URL 或假截图 |
| 13 | DEVELOPMENT | 新环境 / asr / Python 3.11、测试、运行、构建及覆盖风险，明确 mock / Tk / manual / hardware 区别 |
| 14 | ARCHITECTURE | 简述文件、实时、AudioSource、翻译、Session、导出、UI、模型、硬件和分发边界 |
| 15 | PRIVACY | 与代码白名单及本地保存行为一致；明确日志可能含路径，Recovery 含字幕，下载联网 |
| 16 | SECURITY | 无虚构邮箱；敏感问题先请求私密渠道，不公开敏感日志或漏洞细节 |
| 17 | CONTRIBUTING | 分支 / PR、全量测试、依赖与 UI / packaging 影响说明、不提交私人数据 |
| 18 | THIRD_PARTY_NOTICES | 补齐 tkinterdnd2 / TkDnD / PyAudioWPatch / NumPy / PyAV / FFmpeg / NVIDIA 等用途、版本、许可和来源；二进制法律复核仍是发布前事项 |
| 19 | Model licenses | small 与 large-v3 固定模型卡 MIT；Marian Apache-2.0。Marian 本地卡 Git blob SHA-1 与 catalog 的 cc6fb518752007783a71d6c62af0c8d5f6523975 一致，亦核对上游模型卡；具体来源见根目录 notices |
| 20 | Requirements | 四份依赖文件保留既有固定直接版本；无本机 wheel 路径、无删除已用依赖、无升级。torch 仍供翻译 / 构建使用，不移除；不是完整传递依赖 lock |
| 21 | Issue templates | bug / feature 模板，版本、Windows、复现、可选脱敏诊断；不要求上传音频或转录 |
| 22 | PR template | 内容、测试、UI、packaging、新增依赖及隐私检查 |
| 23 | CI | 已评估，暂不启用未经 runner 验证的 Actions；Windows 模拟 Core 和 Tk 分层建议在 DEVELOPMENT，硬件独立人工验证 |
| 24 | Version | src/app_version.py 为唯一声明；GUI、Diagnostics、下载 User-Agent、build/spec 已读取它；README 仅链接来源，不维护副本 |
| 25 | Release Notes | 根目录模板准备 Highlights / Features / Requirements / Known limitations / Downloads / Checksums；未发布 |
| 26 | SHA256 | distribution/checksums.ps1，输入显式文件路径，拒绝覆盖输入 / 已有输出 / 同名冲突；README 样例哈希 smoke 通过 |
| 27 | 根目录 | 历史阶段报告和旧开发长文已移走；本地数据按用户要求留盘，公开树清晰 |
| 28 | 自动测试 | **280 / 280 PASS，49.022 秒**，Conda asr 全量 discovery；核心断言未弱化 |
| 29 | Build path | check_build_paths.py 只读检查 13 个入口 / 资源 / spec 路径及语法通过；build.ps1 PowerShell 语法通过。无外部 icon，UI 素材由 Tk 生成，DnD 由 spec 收集。没有实际 rebuild |
| 30 | 用户待决定 | 主项目 License、GitHub owner / repo、正式安全联系方式、发布文件名称 / 下载位置 |
| 31 | Release 前剩余 | License 决定、实际 FFmpeg / NVIDIA 等分发义务复核、正式截图、最终制品 SHA256、一次精简 Release Check；不启动大型新验证阶段 |
| 32 | Verdict | **Phase 13 COMPLETE**：仓库与文档准备完成，公开开源许可及正式发布仍未完成。停止，不进入下一阶段 |

## 公开版本控制结构

```text
LocalASR/
├── .github/                 # Issue / PR templates
├── src/
├── tests/
├── distribution/            # source scripts, spec, hooks only
├── docs/
│   ├── DEVELOPMENT.md
│   ├── ARCHITECTURE.md
│   ├── development/         # sanitized history, plan, validation summary
│   └── images/              # formal screenshots pending
├── .gitignore
├── build.ps1
├── requirements*.txt
├── README.md
├── LICENSE                  # pending owner decision, not a license grant
├── PRIVACY.md
├── SECURITY.md
├── CONTRIBUTING.md
├── THIRD_PARTY_NOTICES.md
└── RELEASE_NOTES_TEMPLATE.md
```

## 审查与可复现边界

版本控制候选文本扫描没有发现 API key、token、私钥、开发者用户目录或私人邮箱。唯一邮箱匹配是测试中合成的 `user@example.com`；测试中的 Windows example 路径也是模拟断言，不依赖该目录存在。原报告中的开发机路径已通用化；原件及真实日志、Recovery、配置不公开。模式扫描并不能保证未来新增文件绝无敏感数据，首次提交仍应审查 staged diff。

所有本地 Markdown 链接检查通过。历史原始 validation 链接转换为明确的本地证据标识，避免 clone 后产生假可访问链接。所有 UI / Core 文件与 Phase 12.6 哈希比对，只有 recommendation.py 的文档引用变化；没有核心逻辑或 UI 变化。测试只将一个源路径示例替换为通用 example 路径，断言语义不变。

本地证据在 validation/phase13：regression.txt、rollback-check.json、public-files.txt、checksum-smoke.txt。五个 Phase 10 / 11 / 12 / 12.5 / 12.6 EXE 哈希匹配之前记录，未重建或覆盖。原 Phase 12.6 的耳机、实体多显示器、Explorer 跨窗口拖放与物理 DPI 验证限制继续有效；macOS 未实现。


