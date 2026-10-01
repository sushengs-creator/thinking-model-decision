# 安装、检查与更新

本工具采用 [Agent Skills 开放格式](https://agentskills.io/specification)，面向所有支持该格式的 AI Agent。核心流程不依赖 Codex 或 `skill-installer`；安装入口、目录和启用方式由你使用的 Agent 决定。通用格式可以跨产品复用，不表示每个产品或版本都已在本项目中实测。

## 方法一：让当前 AI Agent 安装

把下面整段话复制到 **你正在使用的、支持 Skill 的 AI Agent**：

```text
请为当前 AI Agent 安装“思维模型决策工具”：
https://github.com/sushengs-creator/thinking-model-decision/tree/main/skills/thinking-model-decision
请按照当前 Agent 支持的 Skill 安装方式，安装完整的 thinking-model-decision 技能目录，并检查是否可调用。
如果已经安装，请先检查版本、备份并保留我的本地新增模型和修改，再进行更新。
如果当前环境无法自动安装，请说明原因，并给出适用于当前 Agent 的手动安装步骤。
```

支持从仓库安装的 Agent 可以使用自己的安装器；需要通过设置界面导入的产品则按其导入流程操作。上面的文字是通用安装请求，不是可执行的 YAML 配置。需要联网或目录权限时，按当前环境提示处理。

安装完成后，应核对实际安装位置、版本，以及能否读取参考资料；再按产品要求刷新技能列表、开启新会话或重新加载。安装成功与已经被当前会话识别是两个状态。

## 方法二：手动下载、导入或复制

1. 在仓库页面选择 **Code → Download ZIP**，也可以[下载 main 分支 ZIP](https://github.com/sushengs-creator/thinking-model-decision/archive/refs/heads/main.zip)。
2. 解压，找到仓库中的 `skills/thinking-model-decision`。
3. 按当前 Agent 的官方安装说明，导入或复制**完整的 thinking-model-decision 文件夹**。如果产品只接受技能 ZIP，按其要求重新打包这个技能文件夹；仓库 ZIP 不一定能直接作为技能 ZIP 导入。
4. 保留文件夹结构。`SKILL.md`、`references/`、`assets/`、`scripts/` 都属于本工具的交付包，不要只粘贴入口文案而丢失模型资料。
5. 如果采用目录安装，最终结构应为 `<当前 Agent 的技能目录>/thinking-model-decision/SKILL.md`，避免多套一层仓库目录。不要把某个产品的技能目录当成所有 Agent 的通用目录。
6. 按当前产品的方式加载或启用，然后进行下文的调用检查。

目录、导入大小限制、压缩包结构和命令语法，以当前 Agent 的官方文档为准。`agents/openai.yaml` 是可选的客户端界面元数据；不识别它的 Agent 仍可依据 `SKILL.md` 和引用资源执行核心流程，无需安装额外的 OpenAI 组件。

如果当前工具没有技能安装功能，但能读取工作区文件，可把完整目录放进它能访问的工作区，然后说：

```text
请读取我提供的 thinking-model-decision 目录中的 SKILL.md，
按其中流程处理下面的问题，并按需读取该目录内的 references、assets 等资源。
我的问题是：……
```

这属于本次会话加载，不等于持久安装或自动发现。如果工具既不能安装 Skill，也不能读取完整资源，就无法运行完整模型库；不能仅靠一句提示词声称已经安装成功。

## 安装后怎样调用

使用通用自然语言，或当前 Agent 的技能选择功能：

```text
请调用 thinking-model-decision（思维模型决策工具），帮我分析一个问题。
请先逐步追问，问题清楚后给我 HTML 下一步行动计划。
我的问题是：……
```

例如，Codex 支持用 `$thinking-model-decision` 显式调用；`$` 前缀不是 Agent Skills 的统一调用要求。其他产品使用自己的语法或技能菜单。

可以用下面的请求试用：

```text
请调用思维模型决策工具帮我梳理：我学一门技能几个月了，现在不知道该不该继续。
```

正常情况下，它会先提出一个影响判断的问题，等待回答。问题清楚后，它应读取相关模型并形成有依据的 HTML 行动计划。只显示技能名，不足以证明模型资料可读或流程执行正确。

## 不同任务需要哪些能力

| 任务 | 所需能力 |
|---|---|
| 澄清问题、选择模型与分析 | 能读取 `SKILL.md` 及所需模型卡、原文和参考文件；不强制要求 Python |
| 保存 HTML 行动计划 | 能生成文件或附件；没有写入能力时应交付完整 HTML 源码并说明尚未保存 |
| 预览 HTML | 浏览器或渲染工具；缺少时须说明未做视觉验证 |
| 核实最新外部事实 | 联网检索或用户提供的当前可靠资料；未核实条件须保留为未知 |
| 新增或修订模型 | 对指定技能目录的写入权限；脚本校验需要命令执行及 Python 3.9 以上版本 |

本项目没有专用 API Key 配置；使用的平台或模型服务可能有自己的账号、额度和访问要求。是否提供某项能力，应由当前 Agent 实际检查。

## 检查完整性

让 Agent 读取 `references/library-state.json`，核对版本与模型数量。本次公开版为 **1.4.1**，包含 126 篇用户原文、126 张操作卡、100 个 WW 工具；后续数量以对应版本为准。

有命令执行能力及 Python 3.9 以上版本时，可在任意工作目录运行以下命令，将路径替换成实际安装位置：

```sh
python3 "<技能目录的实际路径>/scripts/library.py" validate
```

脚本使用 Python 标准库，通过自身位置查找资料，不依赖 Codex 的目录或工作路径。若当前环境的 Python 命令名称不同，使用实际可用的 Python 3 命令。没有执行校验时，应如实写明未运行，不能把文件复制成功等同于校验通过。

## 更新已安装版本

不同 Agent 的安装器可能拒绝覆盖，也可能直接替换文件；不要假设它会保留你的新增模型。可以这样请求：

```text
请检查当前 Agent 已安装的 thinking-model-decision 与此仓库的最新版本：
https://github.com/sushengs-creator/thinking-model-decision
先识别并备份我新增的文稿、卡片及本地修订，再在临时位置准备新版。
比较差异、保留有效修改，完成可用的校验后，按当前 Agent 的方式更新并重新加载。
请说明实际更新的位置、版本和未完成的步骤。
```

如果没有本地修改，也应先保留旧版备份，再替换完整技能包。备份放在自动发现范围以外，避免出现两个同名技能。更新公开版不会自动把自己的新增模型或决策报告上传给作者。

## Codex 的可选安装工具

在已提供 `skill-installer` 的 Codex 环境中，可以请求使用该工具安装同一仓库的 `skills/thinking-model-decision` 目录。这是一种产品专用安装方式，不是本技能的依赖，也不是其他 Agent 必须安装的组件。

下一步：[详细使用指南](USAGE.md)。
