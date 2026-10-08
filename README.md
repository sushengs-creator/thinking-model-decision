# 思维模型决策工具

有困惑时，从一句话开始。工具通过一步一步的追问，帮你理清问题，再用思维模型比较选择，每次分析完成后，默认给出一份 **HTML 下一步行动计划**，包含决策依据、执行安排和调整条件。

知识库包含作者提供的 **133篇思维模型原文、133张操作卡，以及万维钢现代思维工具100讲的本地技能资料快照**，已整理87条跨库关系。当前Skill版本为 **1.6.0**。这些是可组合的参考资料，不是233个彼此独立、全部验证过的模型。

## 最简单的安装方法

把下面整段话复制到 **你正在使用的、支持 Skill 的 AI Agent**：

```text
请为当前 AI Agent 安装“思维模型决策工具”：
https://github.com/sushengs-creator/thinking-model-decision/tree/main/skills/thinking-model-decision
请按照当前 Agent 支持的 Skill 安装方式，安装完整的 thinking-model-decision 技能目录，并检查是否可调用。
如果已经安装，请先检查版本、备份并保留我的本地新增模型和修改，再进行更新。
如果当前环境无法自动安装，请说明原因，并给出适用于当前 Agent 的手动安装步骤。
```

安装完成并被当前 Agent 识别后，可以这样使用：

```text
请调用 thinking-model-decision（思维模型决策工具），帮我一步一步梳理这个困惑，最后给我 HTML 下一步行动计划：
我最近在纠结……
```

本工具采用 [Agent Skills 开放格式](https://agentskills.io/specification)，面向所有支持该格式的 AI Agent，安装方式由各 Agent 决定。核心流程不依赖 Codex 或 `skill-installer`；后者只是部分环境可用的安装工具。使用时需要 Agent 能读取完整技能包及相关资料；保存 HTML 需要文件生成能力。各产品的导入入口、技能目录、调用语法和能力可能不同，本项目尚未逐一实测。

它是运行在 AI Agent 中的 **Skill**，运行需要你使用的平台或模型服务。本仓库没有独立聊天服务，也不要求额外配置专用 API Key。

不会安装或希望手动安装，可查看[详细安装与更新指南](docs/INSTALL.md)。

## 一次决策怎样进行

**说出困惑 → 逐轮澄清 → 校准问题 → 选择模型 → 交付 HTML 下一步行动计划。**

- 你可以只讲一件事或一种困惑，不用先填表，也不用知道模型名称。
- 通常每轮只问一个关键问题，收到你的回答再推进。
- 对话会逐步弄清：发生了什么、真正要决定什么、希望得到什么、有哪些限制和选择。
- 信息足够就停止常规追问；一般选一个主模型和必要补充，解释它们怎样改变判断。
- 最终交付可离线打开、可打印的 HTML 文件，包含当前建议、事实与假设、方案比较、行动依据和安排，以及调整条件；对话里附简短结论和文件链接。

如果你已经准备好材料，可以直接要求出报告。如果暂时不想继续回答，也可以说“先给我一份阶段性报告”。报告之后改变目标或约束，只需补充变化，工具会更新 HTML 并说明变更，不用重答全部问题。无需每次再要求“转成 HTML”；单轮澄清不出文件，明确要求纯文本或其他格式时遵从你的选择。

## 调用方式与规则

通用说法是“请调用 thinking-model-decision（思维模型决策工具）”。如果你的 Agent 提供技能菜单或专用命令，使用该产品的调用方式；例如 Codex 可以用 `$thinking-model-decision`。`$` 前缀不是跨 Agent 的统一要求。工具根据你这次想做的事情选择路径，不必背固定口令。

| 你想做什么 | 可以直接这样说 |
|---|---|
| 从模糊困惑开始 | “用思维模型决策工具帮我梳理，先一步一步问我。” |
| 比较选择 | “我有A、B两个方案，先帮我澄清目标和约束，再出报告。” |
| 材料已经充分 | “这些是背景、目标和限制，请直接给决策报告。” |
| 暂时不想补充 | “根据现有信息先给阶段性报告，把不确定的地方标出来。” |
| 先暂停 | “今天先暂停。”（停止追问和分析；只有你同时要求时才出阶段性报告。） |
| 修改已有报告 | “情况变了：……请更新受影响的结论和行动。” |
| 复盘 | “这是上次的判断、行动和结果，帮我区分决策、执行和环境变化。” |
| 新增模型 | “这是思维模型134的文稿，请更新工具，完成卡片、关系核对和试跑。” |

默认每轮一个主要问题，等你回答再推进；已有信息不重复问，未知不替你编。问题、目标、关键限制和可比较选项清楚后，就进入分析和报告，不再要求你批准开始。报告使用实际读过的模型，默认一个主模型、至多三个补充或反证工具；没有适合的模型就说明原因，不凑数量。模型帮助比较，最终价值排序与选择仍由你决定。

仅提供文稿或要求审稿不会自动入库。明确要求维护时，只修改本次指定的目标；缺少写入或校验能力会标明未完成步骤。普通分析无需 Python，无法联网时会保留外部事实的待核实状态。保存 HTML 需要文件写入能力；不具备时会给可保存的完整源码，并如实说明尚未生成文件。

完整步骤、虚构对话示例、报告说明和常见问题见 **[详细使用指南](docs/USAGE.md)**。

## 模型库与维护

- [133个用户模型目录](skills/thinking-model-decision/references/user-catalog.md)
- [万维钢100个工具目录](skills/thinking-model-decision/references/wan-catalog.md)
- [万维钢整体运行框架与九类任务指引](skills/thinking-model-decision/references/wan-framework.md)
- [按问题选择模型](skills/thinking-model-decision/references/decision-routing.md)
- [跨库关系](skills/thinking-model-decision/references/relation-catalog.md)
- [新增文章、修订及复盘流程](skills/thinking-model-decision/references/maintenance.md)

新文章可以尚未发布。维护流程会保留原编号和来源，提炼操作卡，核对与已有模型的关系，实际试跑，再更新版本。使用者自己的修改默认只保存在其本地；不会自动上传到本仓库。

你可以通过Issue反馈可复现的问题，或通过Pull Request提交改进。请只提交有权分享的内容，并使用虚构或充分匿名化的示例；不要提交真实合同、账号密钥、聊天记录或个人决策报告。维护者审阅后决定是否合入。

## 来源、署名与验证范围

本工具由 [sushengs-creator](https://github.com/sushengs-creator) 整理与维护，133篇编号思维模型保留各自原文及来源。万维钢部分来自作者提供的本地技能快照，**不是原课程逐字稿，也不表示万维钢参与制作、审定或背书**。来源记录见[来源说明](skills/thinking-model-decision/references/source-notes.md)，使用与署名说明见[NOTICE](NOTICE.md)。

v1.0完成资料完整性、模型卡来源核对及指定场景试跑；v1.1另完成一组四轮对话和三个边界场景的模拟验证。模拟通过不等于现实决策效果已得到保证。详见[v1.0验证记录](skills/thinking-model-decision/references/evaluation/results-v1.0.md)与[v1.1验证记录](skills/thinking-model-decision/references/evaluation/results-v1.1.md)。

v1.1.1补清公开调用、暂停、能力不足及维护范围规则，另完成七条独立模拟回复审阅。见[公开版检查与修订](docs/SKILL-REVIEW.md)和[v1.1.1验证记录](skills/thinking-model-decision/references/evaluation/results-v1.1.1.md)。

v1.2将用户再次提供的万维钢源文件逐条核对，100/100工具正文一致；补入整体框架、组合语法、证据协议和九类任务程序，并完善检索。100工具与125篇用户模型在同一技能内按问题选择，读者不需要另装一个万维钢 Skill。见[完整融入说明](docs/WAN-INTEGRATION.md)。

v1.2.1 按用户提供的《从0到1写出高质量Skill，先设计触发，再设计流程》逐项审阅：明确触发边界和交付复核，修复来源审计失败残留旧通过结果、独立安装后的验证链接，并分别测试触发与三类决策场景。见 [18项标准、问题及修复证据](docs/QUALITY-AUDIT.md)。

v1.3.0新增 **TM-126「具身认知」**：根据作者提供的完整文稿，检查动作与反馈是否帮助理解步骤背后的关系，保留知识缺口、认知负荷与可替代学习方式等边界。新增原文、操作卡、三条跨库关联及有限适用/误用试跑。详见 [126篇更新记录](skills/thinking-model-decision/references/evaluation/results-v1.3.md)。

v1.4.0 将 HTML 下一步行动计划设为完成分析、阶段性建议和后续更新的默认交付，补入通用离线模板、行动依据与交付检查。逐步澄清和用户指定格式仍然优先；126 篇模型与 100 个 WW 条目不变。见 [HTML 交付验证记录](skills/thinking-model-decision/references/evaluation/results-v1.4.md)。

v1.4.1 将安装、调用和更新说明改为面向支持 Agent Skills 的 AI Agent，区分通用技能包与产品专用安装工具，并补充能力要求及手动加载路径。见 [跨 Agent 安装检查](skills/thinking-model-decision/references/evaluation/results-v1.4.1.md)。

v1.5.0 新增 **TM-127—TM-132**：观察学习、概念转变模型、交互记忆系统、双环学习、费曼学习法和福格行为模型。同步原文、模型卡、问题路由与15条跨库关系；合集核对、正文读取限制和本轮验证范围见 [新增六篇更新记录](skills/thinking-model-decision/references/evaluation/results-v1.5.md)。

真实决策仍以当前证据、个人目标和实际约束为准。个人案例与 HTML 报告默认留在当前任务及其输出目录，不写入通用技能库或自动公开发布。与AI助手聊天本身的数据处理，遵循你使用的平台规则。

v1.6.0 新增 **TM-133 反馈干预理论**，从已发表文章提炼模型卡、调用边界与跨库关系，区分收到建议、实际采用和独立掌握。公开正文提取及验证范围见 [第133篇更新记录](skills/thinking-model-decision/references/evaluation/results-v1.6.md)。
