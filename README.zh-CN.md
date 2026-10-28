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

## 无需安装即可运行

在源码检出/解压目录中打开普通 PowerShell 7，确认 PATH 中的原生 Python。
不需要安装运行时第三方包。

~~~powershell
python --version
python -m cwdprobe --version
python -m cwdprobe --help
~~~

也可使用发布归档：

~~~powershell
python .\cwdprobe-0.1.0.pyz --version
python .\cwdprobe-0.1.0.pyz --help
Get-FileHash .\cwdprobe-0.1.0.pyz -Algorithm SHA256
~~~

与 SHA256SUMS.txt 比较。**pyz 仍需要受支持的 Windows Python，不是独立 EXE。**
以下的 "python -m cwdprobe" 可替换为 "python .\cwdprobe-0.1.0.pyz"，运行归档不需源码。
也可在自己的环境中 "python -m pip install ." 安装源码，构建需要 setuptools。

## 第一个真实外部命令

选择自己有写权限的**完整纯 ASCII 本地根目录**，按需改示例。完整路径只允许字母、
数字、下划线、点、连字符及目录分隔符，且所有祖先不能是重解析点。
中文用户目录中的英文子目录不算 ASCII 基准。不要为获得权限而提权。

~~~powershell
$testRoot = 'C:\cwdprobe-work' # 改成自己有权限的 ASCII 位置
New-Item -ItemType Directory -Path $testRoot # 已有则跳过
New-Item -ItemType Directory -Path .\reports -Force | Out-Null
$pythonExe = (Get-Command python).Source
python -m cwdprobe --root $testRoot --report reports\python-version -- $pythonExe --version
Get-Content .\reports\python-version\report.txt
~~~

这会真实执行已安装的 Python 十二次，不是内置 Demo。**每次要换新报告目录名**；
父目录必须存在，已有报告目录绝不覆盖。

在源码目录中使用独立的相对文件读写脚本：

~~~powershell
$probeScript = (Resolve-Path .\examples\relative_io.py).Path
python -m cwdprobe --root $testRoot --report reports\relative-io -- $pythonExe $probeScript
~~~

脚本创建并读取多语言/空格文件名，断言内容一致。测试自己应用时，把 "--" 后内容换成
可信程序和参数，如 "-- C:\tools\my-app.exe --self-test"。脚本/固定资源使用绝对路径；
相对数据参数指向各个初始为空的 cwd。优先用绝对 EXE，PATH 中的 EXE 名称只解析一次。
批处理需显式指定解释器。参数采用数组及 shell=False；显式 Shell/解释器代码仍由使用者负责。

**只运行可信命令：这不是安全沙箱。** 命令继承当前用户权限和环境，可访问其他文件或网络。
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

Windows Actions 已准备 Python 3.11/3.12、默认只读和自测失败日志。
**托管 CI：NOT TESTED**，直到 GitHub 实际运行。CLI 不上传数据；CI 仅归档合成自测失败
日志，不宣称已有 CI 徽章。[验收范围](docs/VALIDATION.md) · [发布流程](docs/RELEASING.md)。
MIT 许可证，见 [LICENSE](LICENSE)。
