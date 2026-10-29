# cwdprobe

**检查可信 Windows 命令在不同工作目录名称下是否表现不同。** 在纯 ASCII 基准、中文、
日文、韩文、空格和合法标点六类 cwd 执行同一命令，生成本地文本/JSON 报告。
默认每类在全新目录中重复两次。

[English](README.md) · [v0.1.0 说明](docs/releases/v0.1.0.md) · [报告格式](docs/REPORT.md)

适合访问相对文件的 CLI 冒烟测试，省去矩阵、Windows 进程树、有界字节捕获和比较报告
的编写。已有 pytest 或 PowerShell 测试套件也可能足够，无需为本工具迁移。

**v0.1.0 已验证：Windows 11 x64，原生 CPython 3.11 或 3.12。**
Windows 10、ARM64、Python 3.13 及更高版本均为 **NOT TESTED**。
包元信息的 Python 3.11 最低要求不是更广泛的支持保证。

## 从 Release 快速开始

在 [v0.1.0 Release 附件](https://github.com/QSO41/cwdprobe/releases/tag/v0.1.0)下载
**cwdprobe-0.1.0.pyz** 和 **SHA256SUMS.txt**，不需要源码 ZIP 或克隆仓库。
在下载目录打开普通的**原生 Windows PowerShell 7**，确认 PATH 中有 Python 3.11 或 3.12。
**pyz 仍需 Python，不是独立 EXE。** 无运行时第三方包需要安装；不能用 WSL/Linux 代替。

### 1. 检查 Python 和归档

~~~powershell
$pythonExe = (Get-Command python -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
& $pythonExe --version
& $pythonExe -c "import os, sys; print(os.name, sys.executable)"
$expectedHash = ((Get-Content .\SHA256SUMS.txt -Raw).Trim() -split '\s+')[0]
$actualHash = (Get-FileHash .\cwdprobe-0.1.0.pyz -Algorithm SHA256).Hash
if ($actualHash -ne $expectedHash) { throw 'SHA-256 mismatch; stop here' }
& $pythonExe .\cwdprobe-0.1.0.pyz --version
~~~

确认第一处版本为 **3.11.x 或 3.12.x**，平台行以 **nt** 开头，归档版本为 **0.1.0**。
Python 不存在或不在该范围时先停止。哈希比较不区分大小写，不匹配则中止代码块；
校验和可发现字节不一致，并不验证发布者身份。

### 2. 准备测试根目录

在**自己拥有且可写、已存在的本地 ASCII 父目录**下选择专用文件夹。
例如只有当 `D:\work` 属于你且可写时，才使用 `D:\work\cwdprobe-work`。
在提示中输入完整绝对路径，下面的代码会在目标不存在时创建它。
cwdprobe 启动时 `--root` 必须已经存在；检查的是**完整路径及所有父目录**，
盘符后只允许字母、数字、下划线、点、连字符和目录分隔符，不能有路径穿越或重解析祖先。
中文用户目录下的英文子目录不算 ASCII 基准。不要提权，也不要自动切换到 TEMP/TMP
掩盖要求。如果没有合适的位置，先停止；这不代表被测应用失败。

~~~powershell
$testRoot = Read-Host 'Full ASCII path for a dedicated test root you own'
if (-not (Test-Path -LiteralPath $testRoot)) {
    New-Item -ItemType Directory -Path $testRoot -ErrorAction Stop | Out-Null
}
~~~

### 3. 执行真实的外部文件 IO 命令

下面的自包含命令调用已安装的 Python，在每个新 cwd 中创建并读取中文、日文、韩文及
含空格的文件名，检查内容一致。不依赖源码或内置 Demo。
代码按需创建报告父目录；**不要提前创建报告目标目录**，它由 cwdprobe 创建。
`--report` 的父目录必须已存在，目标每次必须全新；GUID 自动换新报告名，绝不覆盖旧报告。

**只运行可信命令：这不是安全沙箱。** 命令继承当前用户权限和环境，可访问其他文件或网络。

~~~powershell
$reportParent = Join-Path (Get-Location).Path 'reports'
if (-not (Test-Path -LiteralPath $reportParent)) {
    New-Item -ItemType Directory -Path $reportParent -ErrorAction Stop | Out-Null
}
$report = Join-Path $reportParent ('io-' + [guid]::NewGuid().ToString('N'))
$code = @'
from pathlib import Path
payload = '中文 / 日本語 / 한국어 / "quoted text"'
for name in ('中文 file.txt', '日本語.txt', '한국어.txt'):
    path = Path(name)
    path.write_text(payload, encoding='utf-8')
    if path.read_text(encoding='utf-8') != payload:
        raise SystemExit('roundtrip mismatch')
print('relative-io-ok')
'@
& $pythonExe .\cwdprobe-0.1.0.pyz --root $testRoot --report $report -- $pythonExe -c $code
$testExit = $LASTEXITCODE
Get-Content (Join-Path $report 'report.txt')
"cwdprobe exit: $testExit"
~~~

预期 `PASS: NO_DIFFERENCE_OBSERVED | 12 executions | cleanup=PASS`，退出码 0。
先看报告首行状态、路径矩阵和 Cleanup；原始输出和详情在 JSON 中。
这是自建安全 IO 样例，不是真实第三方故障复现；PASS 只覆盖此次命令和这些路径样本。

测试自己的应用时，只把 **`--` 后**的命令换成可信程序和参数，
如 `-- C:\tools\my-app.exe --self-test`；`--` 前是 cwdprobe 参数。
每次重新生成报告名。脚本/固定资源使用绝对路径；
相对数据参数指向各个初始为空的 cwd。优先用绝对 EXE，PATH 中的 EXE 名称只解析一次。
批处理需显式指定解释器。参数采用数组及 shell=False；显式 Shell/解释器代码仍由使用者负责。

工具不扫描应用、不上传报告、不修改永久系统设置。

## 读懂结果

| 状态 / finding | 含义 | 退出码 |
| --- | --- | --- |
| PASS / NO_DIFFERENCE_OBSERVED | 所测样例均退出 0，输出稳定可比较 | 0 |
| FAIL / PATH_SENSITIVE_FAILURE | ASCII 成功，某变体稳定退出非 0 | 1 |
| FAIL / GENERAL_FAILURE | 所有样例稳定退出非 0 | 1 |
| INCONCLUSIVE / BASELINE_FAILURE | ASCII 失败但另一类成功 | 3 |
| INCONCLUSIVE | 超时、超限、解码失败、重复不稳定或输出差异 | 3 |
| TOOL_ERROR | 设置、启动、捕获、清理或报告无法完成 | 2 |
| INTERRUPTED | Ctrl+C/KeyboardInterrupt，并尽可能清理 | 130 |

**路径相关差异不等于确定 Unicode 编码根因。** 退出 0 仍需用户的冒烟测试断言功能正确。
单纯输出不同不会自动判为失败。--normalize-cwd 可在跨类比较时仅替换确切 cwd，保留原始
证据；重复稳定性比较总会忽略新目录带来的确切 cwd 变化。

report.txt 为摘要。report.json 包含解析后的 argv、EXE SHA-256、设置、OS/代码页、
路径/码点、状态、耗时、两流原始字节前缀、哈希和严格解码诊断。
脚本、依赖、完整环境不做快照。分享前检查私有路径/参数/输出，base64 不是脱敏。

参数：--repeats 1..10（默认 2）、--timeout 秒（默认 10）、--max-bytes 每流每次
上限（默认 1 MiB，最大 16 MiB）、--encoding utf-8、--normalize-cwd。详见 --help。
编码只影响解码，不改子进程 locale。高限额/重复次数增加内存；超时不能抢占阻塞的
Windows CreateProcess 或执行前的 EXE 哈希。

### 可选：识别一个预期失败

沿用上面的变量，以下模拟命令故意只在非 ASCII cwd 中退出 23。
它是安全的自建故障样例，不声称任何第三方应用存在故障。

~~~powershell
$failureReport = Join-Path $reportParent ('expected-failure-' + [guid]::NewGuid().ToString('N'))
$failureCode = 'import os, sys; sys.exit(23 if not os.getcwd().isascii() else 0)'
& $pythonExe .\cwdprobe-0.1.0.pyz --root $testRoot --report $failureReport -- $pythonExe -c $failureCode
$failureExit = $LASTEXITCODE
Get-Content (Join-Path $failureReport 'report.txt')
"cwdprobe exit: $failureExit"
~~~

预期 `FAIL / PATH_SENSITIVE_FAILURE`，退出码 1：英文、空格、标点路径成功，
中文、日文、韩文路径退出 23。这个预期 FAIL 表示工具观察到了模拟故障，不是工具运行失败。

## 清理与排错

正常完成只删除自己新建并验证归属的 cwdprobe-<id> 目录。根目录和报告保留，报告由用户
检查后自行删除。Job Object 在超时、超限及父进程退出时结束遗留后代。Ctrl+C 在短暂归属
转换期间延后，再安全报告。强杀、断电或不安全/锁定内容可留下目录；没有旧运行清理命令，
也不会自动删除历史目录。

| 症状 | 处理 |
| --- | --- |
| 根目录 / SETUP_ERROR | 检查完整路径已存在、ASCII、本地且可写；换其他自有位置，不提权。 |
| 报告目录错误 | 建立父目录，换新叶目录；目录设置失败时不会写入新报告。 |
| LAUNCH_ERROR / EXECUTION_ERROR | 读 JSON 行内 error，核对绝对 EXE/脚本路径及解释器。 |
| DECODE_ERROR | 确认输出实际编码、检查原字节，必要时选如 --encoding gbk。 |
| TIMEOUT / OUTPUT_LIMIT | 检查可信命令后按需调限额；无法判断不是 Unicode 诊断。 |
| CLEANUP_ERROR / owner 初始化不完整 | 检查确切 workspace，只关闭自己的句柄，审查内容/链接后人工处理；勿删除根目录或其他目录。 |

清理采用验证后的 Windows 句柄，拒绝重解析点、硬链接、归属替换和特殊文件。
owner 不完整时保留目录，报告 cleanup FAIL 和原始错误。勿并发修改活动运行树。

## 反馈

遇到 Bug、配置障碍、成功案例或建议，可[提交 Issue](https://github.com/QSO41/cwdprobe/issues)。
简短说明以下信息即可：

1. Windows 版本/架构、Python 版本、cwdprobe 版本。
2. 执行的测试命令，必要时对敏感参数脱敏。
3. 预期结果与实际结果，方便时附 status/finding。
4. 哪一步让你卡住。
5. 是否比原有脚本更方便，以及原因。

分享前检查本地路径、命令参数和程序输出，删除私人信息。
不要求完整日志/报告、Stars 或公开业务源码；JSON 中的 base64 输出也没有脱敏。

## 源码方式（可选）

在克隆/解压的源码目录，直接运行 `python -m cwdprobe --version` 或
`python -m cwdprobe --help`，无需安装运行时第三方包。
把上文的 `& $pythonExe .\cwdprobe-0.1.0.pyz` 换成 `python -m cwdprobe` 即可从源码运行。
也可在自己的环境中 `python -m pip install .` 安装，构建需要 setuptools。
`examples/relative_io.py` 是额外源码示例，Release 快速开始不依赖它。

## 范围、开发与 CI

只实现 cwd 变化，不做账户/profile 模拟、TEMP/TMP 矩阵、代码页修改、程序/项目搬迁、
资料复制、长路径认证、交互/GUI 或修复。WSL/Linux 不算 Windows 验收。
真实第三方 Bug 复现仍为 NOT TESTED。

~~~powershell
$env:CWDPROBE_TEST_ROOT = $testRoot # 专用测试根，不用共享工作目录
python -m unittest discover -s tests -v
python tools\check.py
python tools\build.py
~~~

42 项有效测试覆盖生命周期、参数、IO、诊断、分类和清理；部分测试仅在自己的夹具上
拒写/恢复权限、创建/移除联接。不需管理员或第三方测试包。
构建生成可重复的 dist/cwdprobe.pyz，仍需 Python。

**托管 CI：PASS**，实际环境为 Windows Server 2025 x64、CPython 3.11.9 和 3.12.10：
[已观察的验收运行](https://github.com/QSO41/cwdprobe/actions/runs/40728447477)。
两个任务均通过全部 42 项测试、可重复构建及隔离模式 zipapp 冒烟测试。
Windows 工作流默认只读。CLI 不上传数据；CI 仅归档合成自测失败日志。
[验收范围](docs/VALIDATION.md) · [发布流程](docs/RELEASING.md)。
MIT 许可证，见 [LICENSE](LICENSE)。
