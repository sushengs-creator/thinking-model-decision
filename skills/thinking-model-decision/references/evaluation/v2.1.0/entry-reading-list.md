# 实际读取清单

读取根目录：`<skill>/`。

## 完整阅读

- `SKILL.md`：四个请求的入口识别和边界。
- `references/guided-dialogue.md`：A的单轮澄清，C的暂停处理。
- `references/questioning-toolkit.md`：澄清候选与不替用户作答边界；A没有宣称完整运行某个编号工具。
- `references/toolbox-orchestration.md`：D的工具分工与合并预算。
- `references/tool-runtime.md`：D的运行、证据和状态分离。
- `references/decision-report.md`：D的交付内容。
- `references/html-action-plan.md`：D的独立HTML与静态检查。
- `references/second-order-check.md`：D的条件、反作用和竞争情景。
- `references/tools/TM-085.md`、`references/cards/TM-085.md`：候选瓶颈。
- `references/tools/TM-111.md`、`references/cards/TM-111.md`：统一发布前的准备状态与异常规则。
- `references/tools/TM-142.md`、`references/cards/TM-142.md`：分工、选择权与既有职责。
- `references/wan-tools/WW-1.4.md`：三人合计资源、周界和他人能动性。

## 目录和路由读取

- `references/decision-routing.md`
- `references/tool-catalog.md`
- `references/wan-catalog.md`

三份目录最初与其他参考合并读取，工具总输出发生截断，因此不声称三份全部正文都已阅读。随后对上述三份文件用 `rg -n 'TM-085|TM-111|TM-142|WW-1\.4|协作|合作|瓶颈|硬约束'` 定位并实际读取返回的匹配行，选型依赖这些可见条目及之后完整阅读的具体工具正文。

## 输出及检查范围

- 写入本目录 `entry-responses.md`、`entry-plan.html`、本清单 `entry-reading-list.md`。
- 仅检查上述目标文件是否存在，随后读回自己的这三个输出；未读取本目录其他文件。
- 静态检查HTML可解析、语言和字符集、导航锚点、来源链接路径、离线依赖、打印及窄屏样式声明、预算合计；未进行浏览器视觉检查。
- 未读取evaluation、audit或其他代理输出；未读取原文文章、其他工具正文、记忆或技能外资料；未联网；未外部发送；未修改技能。

## E场景第一轮的追加读取

- 重新完整读取最新的 `SKILL.md` 和 `references/guided-dialogue.md`。
- 本轮只进行情境澄清，没有选择或声称运行某个编号模型，没有推测用户后续回答，没有生成新HTML。
- 仅追加 `entry-responses.md` 中的E请求与第一轮实际回答，并更新本读取清单；随后读回这两份自己的输出以核对保存。
- 未读取evaluation、audit或其他代理输出，未联网或外部发送。

## E场景第二轮的读取与保存

- 沿用已读的最新 `SKILL.md`、`references/guided-dialogue.md`；本轮没有新增资料读取或编号工具调用。
- 只根据新收到的用户回答更新已知信息：同事原话与用户推断不同、操作学习目标、10月23日期限、两人合计90人分钟和分工意愿。
- 追加用户第二轮回答与实际澄清问题，随后读回自己的记录和本清单核对保存；未推测下一轮回答，未生成新HTML。
- 未读取evaluation、audit或其他代理输出，未联网或外部发送。

## E场景第三轮的实际读取与保存

本轮完整读取：

- 最新 `SKILL.md`。
- `references/tools/TM-107.md`、`references/cards/TM-107.md`。
- `references/tools/TM-127.md`、`references/cards/TM-127.md`。
- `references/tools/TM-143.md`、`references/cards/TM-143.md`。

本轮目录定位：对 `references/decision-routing.md`、`references/tool-catalog.md`、`references/wan-catalog.md` 使用 `rg -n 'TM-107|TM-127|TM-142|WW-1\.4|第三选择'`，实际阅读匹配行。先按具体知识与演示缺口读取107、127，再根据路由读取143，用其核对已改变的二选一前提及备选。

沿用此前实际完整读到的：`references/toolbox-orchestration.md`、`references/tool-runtime.md`、`references/decision-report.md`、`references/html-action-plan.md`、`references/second-order-check.md`、`references/tools/TM-142.md`、`references/cards/TM-142.md`、`references/wan-tools/WW-1.4.md`。

保存与核对：只新建 `entry-third-choice-plan.html`，追加 `entry-responses.md` 和本清单；读回自己的这三份输出做静态核对。核对90人分钟总预算、今天10人分钟沟通上限、角色状态、内部导航、本地来源路径与HTML离线依赖。未读取evaluation、audit或其他代理输出，未读原文文章，未联网、未使用浏览器、未外部发送，未修改技能或讲稿。


公开副本说明：仅将本机专属路径改成相对位置或通用占位；原始作答、失败与阶段状态保持不变。当前发布状态以本轮汇总记录为准。
