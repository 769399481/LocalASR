# Windows 签名准备

当前 LocalASR EXE 与 Phase 14 Installer 均为 **UNSIGNED**。没有代码签名证书，不伪造签名状态。未经签名或信誉不足的安装包可能触发 SmartScreen；本项目不要求绕过 SmartScreen、关闭 Defender 或改变安全策略。

未来由发布负责人配置真实证书及 Microsoft Windows SDK 的 `signtool.exe`。建议顺序：

1. 从证书存储 / 硬件令牌选取真实证书，为最终 LocalASR.exe 签名并校验。
2. 使用签名后的完整 standalone 构建 Installer。
3. 为最终 Installer 签名，使用可信时间戳服务，验证签名链和时间戳。
4. **签名完成后**重新生成 SHA256SUMS；签名会改变文件字节。

验证可使用 `signtool verify /pa /v <实际文件>` 和 PowerShell `Get-AuthenticodeSignature`。具体签名命令由真实证书提供方的存储方式决定；本文件不填假证书路径、密码或时间戳 URL。

本阶段不申请证书、不签名、不发布。没有通过浏览器下载产生的真实 Mark-of-the-Web / SmartScreen 声誉验证，不能将本地安装成功等同于公网下载无警告。
