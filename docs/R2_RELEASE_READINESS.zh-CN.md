# cwdprobe v0.1.0 首次发布准备报告（R2）

日期：2026-10-28。建议：**GO——本地发布准备完成，公开操作仍须用户确认；Release 还须等待托管 CI。**

## 项目与本轮改动

名称保持 **cwdprobe**：为可信 Windows 命令构造六类隔离 cwd，提供保守的退出/输出分类和本地报告。
本轮没有修改核心、42 项测试、构建工具、包元信息或许可证；没有增加功能或运行时依赖。
内部版本、pyproject、CLI 与拟发布版本均为 **0.1.0**。

实际改动：重写对应的英文/中文 README；补足真实外部命令、归档运行、清理和排错说明；
收敛 Windows CI 到 Python 3.11/3.12，固定官方 Action SHA，保留失败日志；
加强 gitignore；准备 Release Notes、校验文件、手动发布流程和本报告。

## 验证结果

原生 Windows 11 x64，非管理员，PowerShell 7.6.5。测试只使用自建可信样例。
经用户明确授权，仅在此前项目专用 ASCII 根目录中新建 R2 子目录；日志和资产都在项目内。

| 项目 | 结果 |
| --- | --- |
| CPython 3.11.15 全部适用测试 | PASS：42 项，34.749 秒，无失败/错误/跳过 |
| CPython 3.12.14 全部适用测试 | PASS：42 项，21.919 秒，无失败/错误/跳过；通过工作流的同一测试脚本本地执行 |
| README 外部 Python 版本、独立 IO 示例 | PASS：两解释器各两组、每组 12 次 |
| 版本化 pyz 隔离运行 | PASS：两解释器各 12 次 IO；离开源码包目录，使用 -I -S 和最小环境 |
| 帮助、版本、README PowerShell 语法 | PASS：源码/归档两解释器，参数与实现核对一致 |
| 可重复构建 | PASS：两次构建哈希相同；版本化文件与 R1 核心包逐字节一致 |
| CI 本地检查 | PASS：YAML 解析、四段 PowerShell 语法与执行、受控失败 7 的日志/退出码传播 |
| GitHub 托管 CI / Artifact 上传 | **NOT TESTED**：没有远程仓库，没有触发工作流或上传 |

README/归档额外验证共 **6 组、72 次执行**；不把预期退出 7 的日志探针计为产品测试失败。
最终构建仅含 9 个项目模块、顶层入口和 LICENSE，共 11 个成员；没有报告、字节码、
个人资料或第三方二进制。pyz 大小 **36,187 字节**，仍需要受支持的原生 Python，不是独立 EXE。

原始 R2 日志、工作流提取脚本、资产清单和扫描结果保留在被忽略的
`local-acceptance/r2-20261028/`；工作流本地日志在 `ci-results/`。以前的验收目录未删除。

## GitHub Actions 准备情况

`.github/workflows/windows.yml` 使用 windows-latest，Python 3.11/3.12，10 分钟上限；
默认 contents: read，不持久化 checkout 凭据，无额外 Secrets，无自由命令输入或事件文本插入 Shell。
执行全部测试、格式/元信息检查、两次构建和隔离归档冒烟。失败时仅收集合成自测的
`ci-results/*.log`，保留 7 天，不收集用户报告目录。

已核对当前官方 [checkout v7](https://raw.githubusercontent.com/actions/checkout/v7/action.yml)、
[setup-python v7](https://raw.githubusercontent.com/actions/setup-python/v7/action.yml)、
[upload-artifact v7](https://raw.githubusercontent.com/actions/upload-artifact/v7/action.yml) 引用，
并固定完整提交 SHA。只读权限和 SHA 固定遵循 [GitHub 安全指引](https://docs.github.com/en/actions/reference/security/secure-use)。
本地脚本成功不能替代托管验证；没有添加成功徽章，也没有额外操作系统矩阵或发布流水线。

## 公开安全、历史与许可证

独立只读审查覆盖基线全部 **3 个历史提交、41 个唯一文件内容对象**，总 155,669 字节，
最大对象 16,857 字节；之后再扫描 R2 变更及最终新增提交。未发现凭据签名、真实私人绝对路径、
私人文件、原始报告/日志、无关大文件或第三方打包资产。通用技术路径和合成测试数据保留。
这是一轮人工与模式扫描结论，不宣称穷尽所有秘密检测能力。

全部作者/提交者使用 `cwdprobe contributors <contributors@cwdprobe.invalid>`，没有私人邮箱。
此通用邮箱不会自动关联用户的 GitHub 贡献身份。没有重写历史。
gitignore 现覆盖日志、构建/安装目标、任意子目录的 report.json/report.txt、env 和常见私钥容器。
历史技术验收摘要已脱离私人数据，原始证据仍被忽略。

MIT 文件、版权、包声明及 pyz 内许可证一致。运行时只有标准库，无第三方代码/资产随包分发；
Windows 系统 DLL 和开发机 Python 没有被复制进发布文件。

仓库名称再次精确检索：GitHub `cwdprobe in:name` 未返回同名仓库；网页结果仅见无关目录/探针名称，
未发现明显软件冲突。未预留命名空间、未做商标清查；实际创建前需核对所选 OWNER 下是否可用。

## 待发布文件与文档

发布候选目录：`dist/v0.1.0/`，仅上传以下三项：

- `cwdprobe-0.1.0.pyz`
- `SHA256SUMS.txt`
- `LICENSE`

pyz SHA-256：

`92c1ec784f19fe1d4db1d070626e2ee1d5a4ce34e0ddfa4a4fe55295f717e08d`

对应公开校验记录：`docs/releases/SHA256SUMS-v0.1.0.txt`。
英文 README 为主，中文对应；Release Notes 在 `docs/releases/v0.1.0.md`；
手动步骤在 `docs/RELEASING.md`。没有自动更新器、安装器、网站或付费服务。

## 尚未验证与边界

**NOT TESTED**：托管 Windows CI、Artifact 上传、Windows 10、ARM64、Python 3.13+、
全新 Windows 安装、不同真实 Windows 账户、真实映射 SMB、人工按键/特定终端关窗、
断电/强杀清理、真实第三方 Bug 复现。本轮未重复联网 pip 安装，R1 的项目内离线安装证据仍保留。
R1 已有的真实控制台 CTRL_C_EVENT 验证不等于人工按键；R2 未重新测试该终端事件，
但相关核心不变且 42 项回归全部复跑。

只测 cwd，不做账户/profile、TEMP/TMP、代码页或程序/项目搬迁模拟；不是安全沙箱，
路径敏感不等于编码根因，退出 0 仍需用户程序断言功能正确。
没有已确认但未解决的发布阻断项；如果首次托管 CI 失败，必须先修复再发布 Release。

## 本地记录与后续最少步骤

R2 准备提交：`3f4e982` — `chore: prepare v0.1.0 documentation and Windows CI`。
本报告与完成清单随后单独提交，交付时用 `git log -2 --oneline` 核对两项新增记录。
最终检查包括工作树干净、无 remote、无 tag、R2 ASCII 子目录为空；证据/候选文件保留供验收。

本轮未创建仓库、Push、创建/推送 Tag 或发布 Release。用户确认后才进行：

1. 在确定的 GitHub 命名空间创建空的 cwdprobe 仓库。
2. 绑定其 URL，首次 `git push -u origin HEAD:main`。
3. 观察该提交的 Windows 3.11/3.12 托管 CI；失败则停下修复，通过后如实更新 CI 表述。
4. 核对最终提交和哈希，再创建/推送 v0.1.0 Tag，并用现有说明和上述三文件创建 Release。

**GO 的含义是可以请求用户批准首次公开操作，不是本轮已经发布。**
