# cwdprobe

在六种全新工作目录中执行同一条可信命令，生成本地兼容性报告。
Windows 原生 Python 3.11+，运行时仅使用标准库，无服务器或付费 API。
当前为尚未公开发布的本地 MVP。[English](README.md)

首版只测 **cwd（当前工作目录）**，不模拟中文 Windows 账户、用户配置目录、
程序安装目录或 TEMP/TMP。它不能保证复现研究报告中的所有真实故障。

在普通 PowerShell 7 中进入项目，准备自己有写权限的纯 ASCII 测试根目录，
然后运行（已有目录不需再次创建，每次报告目录必须是新名字）：

```powershell
New-Item -ItemType Directory -Path C:\cwdprobe-work
New-Item -ItemType Directory -Path reports
python -m cwdprobe --root C:\cwdprobe-work --report reports\good --demo good
python -m cwdprobe --root C:\cwdprobe-work --report reports\bad --demo ascii-only
```

正常样例在英文、中文、日文、韩文、空格、合法 ASCII 标点路径中创建并读取
多语言文件；默认每种目录运行两次。故障样例是**人为模拟**：仅在非 ASCII cwd
退出 23。不是某个第三方产品已被本工具证实有问题。

测试自己的命令：

```powershell
python -m cwdprobe --root C:\cwdprobe-work --report reports\app -- C:\tools\app.exe --self-test
```

请只运行可信命令。**这不是安全沙箱**，命令拥有当前用户权限，可访问外部文件或
网络。工具本身不上传报告，不扫描运行其他项目。参数按数组传递，不拼接 Shell；
脚本需要显式指定解释器和脚本的绝对路径。各样例 cwd 初始为空，不复制项目。

完整测试根路径必须为无空格和特殊符号的 ASCII 本地绝对路径，且祖先不能是联接
或符号链接。中文用户目录下的英文文件夹不会被误认作纯 ASCII 基准。
创建目录被拒绝时请换自己有权限的位置，不要以管理员身份测试。

结果含义：

- **PASS**：所测样例全部退出 0，输出稳定可比较；不代表所有 Unicode 路径均兼容。
- **FAIL / PATH_SENSITIVE_FAILURE**：英文基准成功，某些变体稳定退出非 0；不能据此确定编码根因。
- **FAIL / GENERAL_FAILURE**：所有路径均失败，不能归因于 Unicode。
- **INCONCLUSIVE**：基准不成立、超时、输出超限、解码失败、重复不稳定或单纯输出不同。
- **TOOL_ERROR**：工具无法完成启动、捕获、目录设置或安全清理。

退出码依次为 0、1、3、2，中断为 130。`report.txt` 供阅读，`report.json`
保存参数、实际路径、退出码、耗时、stdout/stderr 原始字节前缀、SHA-256 和解码诊断。
输出编码默认 UTF-8，可用 `--encoding gbk` 等显式选择；不会替子程序改系统代码页。
`--normalize-cwd` 仅为比较替换确切 cwd，保留原始证据，不能把其他差异静默抹去。

工具只清理自己创建且通过归属检查的随机运行目录；遇到联接、硬链接或锁定文件时
保留目录并报错。超时和正常父进程退出都会关闭 Job Object，结束遗留后代进程。
强制结束工具、断电或恶意并发改目录不在清理保证内。报告可能含私有路径或命令输出，
分享前自行检查；默认报告目录已加入 gitignore。

测试与构建：

```powershell
$env:CWDPROBE_TEST_ROOT = 'C:\cwdprobe-work'
python -m unittest discover -s tests -v
python tools\check.py
python tools\build.py
python dist\cwdprobe.pyz --root C:\cwdprobe-work --report reports\archive --demo good
```

构建为可重复生成的 `.pyz`，仍需 Python，不是独立 `.exe`。
详见[竞品与需求证据](docs/RESEARCH.md)、[报告约定](docs/REPORT.md)及
[验收范围](docs/VALIDATION.md)。本地验证 Windows 11 x64 / Python 3.11、3.12，
其他版本和 GitHub 托管 CI 不冒充已通过。许可证：MIT。
