# 历史与验证证据索引

这里保留适合公开的阶段报告及摘要。报告是当时状态的记录，不代表当前所有环境均已验证。Phase 13 已通用化开发机绝对路径；未脱敏原件和原始音频 / 日志 / 截图仍留在本地忽略目录，clone 不附带它们。

历史：[Core 1–5](CORE_HISTORY.md)、[Phase 7](PHASE7.md)、[8](PHASE8.md)、[9](PHASE9.md)、[10](PHASE10.md)、[11](PHASE11.md)、[12](PHASE12.md)、[12.5](PHASE12_5.md)、[12.6](PHASE12_6.md)。

## 最新已完成基线

Phase 12.6：280 项完整测试通过；独立版启动、文件 ASR、Marian 翻译、双语 DOCX、五种输出、系统音频、Overlay 和安全退出通过。内部原生拖放已验证，Explorer 跨窗口拖放未验证。

包体 2,497,279,284 字节，比 Phase 12.5 增加 7,978 字节。旧回退目录保持原状。150.641 秒系统音频回归中音频与翻译零丢弃；这不是永久无丢帧或长期无泄漏保证。

## 本地证据分类（路径相对仓库根目录）

| 类别 | 本地路径举例 | 公开策略 |
| --- | --- | --- |
| 测试 / 性能 / 尺寸 | validation/phase12_6/regression-final.txt、responsiveness.json、build-size.json | 保留原件；公开本页与阶段报告中的数值摘要 |
| 实际 packaged 证据 | validation/phase12_6/packaged/、interactive.json、system/report.json | 含路径 / 设备 / 合成字幕，默认不提交 |
| 原始音频 / 截图 / 生成导出 | validation/ 各阶段子目录 | 本地留存，不提交重复二进制或未审查材料 |
| 原件备份 | archive/local-originals/ | 只供本地追溯，不公开 |

旧报告中的 `validation/...` 等行内路径是证据标识，不是承诺 Git clone 存在的文件。唯一证据未删除。

