# cwdprobe R1 质量审查与发布就绪报告

日期：2026-10-28。最终判断：**READY WITH LIMITATIONS**。

本轮实际修改了核心代码，并完成回归。没有发现尚未解决的发布阻断问题。
结论仅针对下述已验证范围，不等于覆盖所有 Windows、Unicode 路径或第三方应用。
没有创建 GitHub 远程仓库，没有 Push、Release、数据上传或系统级安装。

## 1. 审查基线、方法与安全边界

开始时 HEAD 为 `5a61ee9b7d7a558068a9cdbc93aa018ab157aa6f`，工作树干净。
先只读检查，再设计受控复现；没有将上一轮 PASS 当作本轮证据。

本轮逐项检查了：

- 全部 9 个 `cwdprobe/*.py` 模块：入口、参数、实验、分类、工作区、Win32 文件句柄、Job、捕获和演示程序。
- 原有 5 个测试文件、构建/验收/检查脚本、独立 IO 示例、项目元信息、MIT、gitignore、gitattributes 和 Windows 工作流。
- 两份 README，以及研究、设计、计划、报告协议、验收和验证说明。
- 旧的两个验收目录：66 个文件的长度/SHA-256、8 份 JSON/文本报告、原始流字节的哈希、两份旧 manifest 和测试日志。
- 原 `.pyz`：整体哈希及压缩包内各源码与 `git show 5a61ee9:<path>` 的逐项比较。

安排了两名独立只读审查者，分别检查进程/捕获和目录/分类边界；其审查未执行测试，
本报告中的运行结果来自本轮实际命令。最终变更复审未发现新的阻断缺陷。

环境：原生 Windows 11 x64，build 26200；PowerShell 7.6.5；
CPython 3.11.15、3.12.14；已安装 Node.js 24.15.0。确认没有管理员令牌。
Python 3.11 的 platform 字符串称 Windows 10，但实际为同一台 Windows 11，不能计作 Windows 10 验收。

原始证据在项目内 `local-acceptance/r1-20261028/`，被 Git 忽略。
工作目录实验复用上一轮专属于本项目的 ASCII 验收根目录，只在其全新 R1 子目录创建样例。
没有修改其他项目或已有工作文件。临时 DACL/联接测试仅作用于自己的测试夹具；
普通测试不提权，不改注册表、系统 PATH、永久环境变量或用户账户。
离线 pip 验证只安装到项目内 target；pip 自身使用并清理了系统临时构建缓存。

## 2. 发现的问题、复现与修复

没有确认 P0/P1。以下是已确认并修复的 P2 核心可靠性问题，不能因概率低而跳过。

| 编号 | 原问题与实际复现 | 修复和回归 |
| --- | --- | --- |
| R1-01 | `Popen` 已创建挂起进程、但尚未向调用方返回时收到 SIGINT，`proc` 仍为空，旧实现无法终止该子进程。保留真实 Popen 对象并在返回前触发 SIGINT，确认 `poll()` 仍为空；RED 测试通过确切句柄兜底回收，没有执行子程序代码。 | 在进程对象和捕获线程归属转换的短临界区延后 SIGINT；随后恢复原 handler 并交付中断。回归验证中断后进程已退出、用户代码未执行。 |
| R1-02 | 第一个捕获线程启动后中断，或线程配额错误，使旧清理代码 join 未启动线程，抛出 RuntimeError，丢失结构化报告。 | 安全完成启动转换；RuntimeError 作为 TOOL_ERROR；仅 join 确实启动的线程，关闭未使用管道。SIGINT、线程启动失败各有回归。 |
| R1-03 | 独占创建 owner 标记后模拟磁盘满，旧代码直接 rmdir，因标记仍在而掩盖原错误；最终报告 `workspace=null / NOT_NEEDED`，实际有残留。 | `WorkspaceInitializationError` 保存已分配路径及原错误；报告 TOOL_ERROR/SETUP_ERROR、cleanup FAIL 和保留目录。归属不完整时不猜测删除权限。覆盖 stat/标记建立的异常路径。 |
| R1-04 | 在真实目录清理的第一次删除前触发 SIGINT，旧异常路径会逃出报告生成流程。 | 仅在安全清理转换期间延后 SIGINT，完成处置后报告 INTERRUPTED；保留实际 cleanup 结果。 |

修复过程中另加两项防倒退检查：捕获初始化 OSError 不得继续恢复用户进程；
清理阶段中断不得覆盖已有 TOOL_ERROR。两项都经历了 RED→GREEN。
合计新增 **7 项回归测试**，文件为 `tests/test_r1_regressions.py`。

命令格式、JSON schema 版本、现有状态/退出码、默认矩阵和 `--demo` 均保持兼容。
没有增加 GUI、语言适配层、项目复制、TEMP 模式或复杂集成。

## 3. 核心安全与结论可信度

| 检查 | 结论 | 证据与范围 |
| --- | --- | --- |
| argv / Shell | PASS | `.exe` 解析一次，`Popen` 数组和 shell=False；空参数、空格、中文、引号、尾反斜杠、`&`、`$(...)` 按字面验证。显式传 `cmd /c` 或解释器代码仍是用户自己的执行决定。 |
| ASCII 基准 | PASS | 检查完整输入绝对路径、解析后完整路径、本地磁盘类型和全部祖先；实际中文项目父路径被拒绝。不是仅检查叶子名。 |
| 清理边界 | PASS | 随机目录、owner、原目录身份；先完整清点，祖先和后代句柄拒绝写/删除共享；OPEN_REPARSE_POINT 检查，再以句柄删除。联接、硬链接、目录替换、重命名锁及边界外 sentinel 均有实际回归。 |
| 超时 / 进程树 | PASS | 挂起启动→Job 归属→恢复；超时、输出超限和父进程正常退出都会结束遗留后代，并等待 active count 归零。Job 只管理本次创建的进程。 |
| 原始流与上限 | PASS | 两流并发二进制读取；每流每次保留量有上限；严格解码失败保留原字节、hash、诊断。包含无效 UTF-8、其他 codec 和超大双流输出测试。 |
| 分类 | PASS | 普遍失败、有效基准下的变体失败、坏基准、启动错误、超时、解码、输出差异、重复不稳定分开；并非所有非零或异常都叫 Unicode 错误。 |
| JSON / 文本 | PASS | 最终 10 组外部实验的状态、finding、行数、流字节长度与 SHA-256 一致。文本是摘要，不含全部逐进程 error/流正文；详细原因需读 JSON。 |
| 报告隐私 | PASS（本地与源码边界） | 不上传、不转储完整环境；记录路径/argv/输出是复现所需，但可能含私密内容。ensure_ascii、base64 都不是脱敏。旧/新原始证据及安装产物未进入 Git。 |

这不是安全沙箱；用户命令可访问用户权限范围内的其他文件和网络。
只运行可信命令。恶意并发文件系统修改、内核/强制结束、断电、外部服务等不在保证内。
超时不能抢占 Windows 同步 CreateProcess 或运行前的 EXE 哈希操作。
每流每次限额也不是总 RAM/磁盘配额：高限额和大量重复会放大报告内存，建议使用默认值。

## 4. 真实外部命令验证

全部通过普通 `-- EXE ARG ...` 接口，不依赖 `--demo`。
最终证据为 `r1-20261028/final-external/external-manifest.json` 及对应报告；
每组均为六类路径、两次重复，即 **10 组、120 次执行**。

| 外部命令 / 场景 | 实际状态 |
| --- | --- |
| 已安装原生 Python 3.11 `--version` | PASS，12 次一致 |
| 已安装原生 Python 3.12 `--version` | PASS，12 次一致 |
| Python 运行现有 `examples/relative_io.py` | PASS，多语言和空格文件名实际读写 |
| Python 运行独立脚本，脚本路径含中文/空格，带字面特殊参数 | PASS，参数和 UTF-8 文件内容逐项断言 |
| 现有 Node.js 运行独立 JS IO 脚本 | PASS；EXE 自身位于带空格目录，脚本路径/文件名/参数亦覆盖中文和空格 |
| Python 输出实际 cwd | INCONCLUSIVE / OUTPUT_DIFFERENCE，退出 3，符合预期 |
| 同一命令显式 `--normalize-cwd` | PASS，原始字节未被修改 |
| 自构造的仅非 ASCII cwd 退出 23 | FAIL / PATH_SENSITIVE_FAILURE，符合预期；**模拟故障** |
| 自构造的所有 cwd 退出 17 | FAIL / GENERAL_FAILURE，符合预期；**模拟故障** |
| 最终 `.pyz` 在隔离导入环境运行外部 Python | PASS，12 次一致 |

独立 IO 脚本是自行编写的安全小程序，Python/Node 是已安装的可信运行时；
这些不构成对某个真实第三方 Bug 的复现。没有下载、安装或执行未知第三方软件。

报告含解析后的 EXE 路径与 SHA-256、完整 argv、设置、OS/代码页、实际 cwd/码点、
退出码、耗时及原始输出，足以重建本轮实验步骤。它不打包脚本、依赖和完整环境，
因此不是自包含的应用快照；复现者仍须保留自己的脚本/依赖版本。

普通用户现在可复制 README 中的示例，使用 Get-Command 和 Resolve-Path 得到解释器、
脚本绝对路径，无需了解内部模块。测试根目录必须预先存在且满足完整 ASCII 规则，
报告父目录也须存在、报告叶目录必须是新名字；这两项仍是使用门槛。

## 5. 真实 Windows 控制台 Ctrl+C

验证设计依据 [GenerateConsoleCtrlEvent](https://learn.microsoft.com/en-us/windows/console/generateconsolectrlevent)
和 [独立控制台规则](https://learn.microsoft.com/en-us/windows/console/creation-of-a-console)。
CTRL_C_EVENT 无法限制到非零进程组，因此没有向当前共享终端广播。

本轮创建新的隐藏控制台；发送前用 GetConsoleProcessList 确认只有自建控制器和
cwdprobe 两个预期进程。控制器只在启动目标后让自身忽略事件，然后发送真实
Windows CTRL_C_EVENT；目标正在运行自建睡眠子程序。控制台外另放一个自建哨兵。
整个控制器也处在测试自建 Job 内，异常兜底不靠扫描或按名字杀进程。

最终实际结果：**PASS**。退出码 130；INTERRUPTED；cleanup PASS；
目标子进程已退出；运行目录不存在；控制台外哨兵仍存活。
最后仅通过自己的 Popen 句柄回收测试哨兵。没有结束无关软件。

证据：`final-external/console-result.json`、控制器日志及
`final-external/console-ctrlc-report/report.json`。
这比 `_thread.interrupt_main()` 更进一步，覆盖了操作系统真实控制台事件；
仍没有亲自按键或验证每一种终端模拟器，也没有测试关闭窗口和强制终止。

## 6. 自动化、构建与安装复验

| 验证 | Python 3.11.15 | Python 3.12.14 |
| --- | --- | --- |
| 未修改原提交的原 35 项 | PASS，33.145 秒 | PASS，20.694 秒 |
| 最终原 35 + 新增 7 项 | PASS，42 项，34.996 秒 | PASS，42 项，21.534 秒 |
| 失败 / 错误 / 跳过 | 0 / 0 / 0 | 0 / 0 / 0 |
| 两次 `.pyz` 构建与实际 smoke | PASS | PASS |

最终完整验收目录分别为 `local-acceptance/run-5f0146ee1009/` 和
`local-acceptance/run-f9a860dc1aed/`。两者记录相同的最终 `.pyz` SHA-256：

`92c1ec784f19fe1d4db1d070626e2ee1d5a4ce34e0ddfa4a4fe55295f717e08d`

原 `.pyz` 已另存为 R1 证据中的 `original-cwdprobe.pyz`，没有丢弃。
其 `0f2927...59b0a4` 哈希、包内源码和原提交全部对应。
旧 66 个验收文件哈希未变，8 份旧报告的流哈希/行数/摘要得到独立核对。

隔离 `.pyz` 测试使用绝对归档路径、离开源码包目录的空工作目录（证据树中的 clean-cwd）、
`-I -S` 和只保留必要 Windows 变量的新环境；无 PYTHONPATH/PYTHONHOME/site-packages。
这证明运行不依赖源码可导入或 Codex 会话；**不等于一台全新 Windows 安装已验收**。

另用现有 pip/setuptools/wheel，设置 no-index/no-deps/no-build-isolation，
把本项目离线安装到项目内 `installed/`，再以 `-I -S` 仅导入该目录运行 12 次外部命令，PASS。
未修改系统 Python。联网构建隔离安装、全新机器安装没有验证。

## 7. 与短脚本、pytest、PowerShell 的真实差异

反向对照实际运行了 `r1-20261028/simple_baseline.py`：**20 行标准库脚本**，
完成六类目录、两次重复、相同可信 Python 命令、退出码和二进制输出记录；12 次均成功。
所以，如果需求只是“一条命令换六个 cwd 看是否退出 0”，短脚本确实足够替代本项目。

| 环节 | 自建 Python / pytest / PowerShell | cwdprobe |
| --- | --- | --- |
| 首次配置 | 已有 pytest 时加参数化 fixture 很自然；一次性脚本约 20 行就能跑基础矩阵 | 需要 Python、获取源码/pyz，准备 ASCII 根目录和新报告目录；无需自己编写矩阵 runner |
| 每次执行 | 编写脚本后同样可以一条命令；pytest 通常 `pytest -q` | 一条 `python -m cwdprobe ... -- EXE ARGS`；不是“一条命令”本身形成差异 |
| 看退出结果 | 打印或断言很简单 | 已约定 general/path/baseline/inconclusive/tool error 和退出码 |
| 异常处置 | 普通 subprocess.run 有超时，但 Windows 进程树、输出流限额、生命周期边界仍需实现或借助成熟库 | 复用已有 Job/捕获/清理实现；维护成本由项目承担，并没有消失 |
| 复现报告 | 自定字段，容易与自己的测试系统贴合 | 固定机器协议、原始字节、诊断、哈希和上下文；没有完整依赖快照 |
| CI 集成 | 已有测试框架时可能更省事 | 可复用同一命令，但仍需 ASCII 根目录准备；当前 GitHub 云端流程尚未执行 |
| 维护与灵活性 | 自己承担脚本维护；复杂断言更自由 | 用户少维护一套通用 runner，但接受本项目的范围、固定矩阵和 Python 运行时 |

[pytest 原生参数化](https://docs.pytest.org/en/stable/how-to/parametrize.html) 已能组织矩阵；
PowerShell 也可直接用 [.NET ArgumentList](https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.processstartinfo.argumentlist)
可靠传参。cwdprobe 没有独占技术能力。

实际省去的是：编写并维护完整路径基准校验、约定矩阵、重复隔离、Windows Job 生命周期、
有界双流捕获、原字节诊断、保守分类和统一报告的工作。没有测出节省多少分钟，
也没有用户访谈或采用率证据。对 Windows CLI 维护者、没有现成测试框架的项目有小而明确的价值；
对已有完善 pytest/trycmd/PowerShell 测试基础的项目，不建议仅为 cwdprobe 迁移工作流。

## 8. 可发布性、限制与后续边界

MIT 文件、项目元信息和安装包中的 License-Expression/License-File 已核查；
运行时 dependencies 为空，无第三方源码/二进制被打包；zipapp 内含本项目 LICENSE。
构建所用现有 setuptools/wheel 只是构建工具，不随 `.pyz` 分发。
测试与报告使用的原始本地路径未写进已跟踪源文件；报告应由使用者审阅后再分享。

Windows Actions 工作流已准备：Python 3.11/3.12/3.13 矩阵，contents: read，
不保留 checkout 凭据，10 分钟上限，测试、检查、可重复构建和 zipapp smoke。
根据官方已读取的 [checkout v7](https://raw.githubusercontent.com/actions/checkout/v7/action.yml)
和 [setup-python v7](https://raw.githubusercontent.com/actions/setup-python/v7/action.yml) 更新版本；
两段 PowerShell run 块通过本机语法解析。没有安装 actionlint/YAML 校验器，
**托管云端 CI 仍为 NOT TESTED**；工作流准备好不等于云端已通过。
没有自建服务、后台值守、付费 API 或新云资源。

仍为 **NOT TESTED**：Windows 10、ARM64、Python 3.13、真实不同 Windows 账户名称、
真实映射 SMB 盘、全新 Windows 安装、特定终端的人工键盘 Ctrl+C/关窗、断电/强杀清理、
真实第三方软件 Bug 复现、联网隔离 pip 安装、托管 CI。

明确不在当前能力内：TEMP/TMP 矩阵、profile/注册表/系统代码页模拟、程序/项目搬迁、
大型工程复制、Unicode 全集认证、故障自动修复。退出 0 仍须用户程序自己断言功能正确。
单人维护可行，但 Win32 适配和安全回归是实际维护责任，不能宣传为无需维护。

## 9. Git 记录与停止状态

基线提交：`5a61ee9`。本轮核心修复提交：
`23cff0c` — `fix: preserve process ownership and reports across interrupts`。
修改三处核心模块，增加 7 项回归，并更新 README、报告边界、验证说明和基础 CI。

本报告随后独立提交，标题为 `docs: record independent R1 quality and readiness review`；
交付时 HEAD 为该文档提交，核心实现仍对应 `23cff0c`。精确提交号可运行
`git log -2 --oneline` 核对。本报告不尝试把自身提交哈希写入自身内容。

最终交付检查要求：工作树干净、无 remote、旧证据哈希不变、R1 ASCII 子根目录为空。
被忽略的本地证据和构建/离线安装产物保留供人工验收，不强制删除。

**READY WITH LIMITATIONS**：可作为范围明确的本地 Release Candidate 供用户验收；
无已确认但未修复的阻断问题。本轮到此停止，不创建 GitHub 仓库、不 Push、不发布 Release。
