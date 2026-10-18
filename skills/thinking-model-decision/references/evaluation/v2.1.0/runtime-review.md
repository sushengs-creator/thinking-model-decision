# v2 工作流与维护运行审计

审计对象：`<skill>`。开始时为 v2.0.0 / revision 63 / 142 TM / 100 WW；处于 143 增量制作阶段的版本数量不列为缺陷。

已读 skill-creator 规范及本技能 SKILL、guided-dialogue、questioning-toolkit、toolbox-orchestration、decision-routing、tool-runtime、maintenance、decision-report、html-action-plan，并审查 library、runtime、runtime registration 脚本。没有读取 `references/evaluation/cases.md`、`criteria.md` 或任何私人案例，也没有上传材料。

## 实质发现与修复

### R1 / P2：旧卡片可被重新登记成“当前运行工具”——已修复

修复前证据：`register_runtime.py` 的 `prepare`（原第25–49行）只确认模型 ID 存在，随后对源、卡和运行文件重新计算 SHA；`tool_runtime.py validate`（原第70–98行）只检查路径、运行索引指纹与证据文件存在，不读取用户索引里的 `card_status`、`card_source_sha256`。因此来源更新后被标记 `needs_review` 的旧卡，可通过重新登记取得一套新的运行指纹。

实际复现使用临时的单模型虚构 fixture：令 `card_status=needs_review`，且 `card_source_sha256` 不同于当前 `source_sha256`。修复前 `prepare` 接受，`validate` 返回 `ok: true`，`show` 返回 `fingerprints_current: true`。完整结果保留在 `runtime-adversarial-results.json`。这违反维护流程第64行“原卡保留但标记 needs_review，不能继续当作当前样例直接使用”的约束。

修复：新增 `tool_runtime.py:48` 的 `registered_card_issues`，同时核对卡片待复核状态、卡片对应的来源指纹、用户索引登记的正文/卡片文件指纹。`register_runtime.py:28` 在登记前拒绝这些问题；`tool_runtime.py:119` 的校验、`show` 也一致呈现。没有要求旧卡必须升级为 `behavior_checked`，原有 `source_reviewed` 卡正常通过。

修复后同一复现：登记返回明确错误；`validate` 返回 `ok: false`；`show` 显示 `card_source_is_current: false`、`invocation_status: review_required`。另加入“未登记就直接编辑原文或卡片”的拒绝测试，防止以重算运行指纹掩盖库索引未登记的变化。

二次审查补充：真实 `library.py` schema 还允许 `draft`，它表示卡片审阅未完成。第一轮修复只拦截 `needs_review`，未审阅、缺失或未知状态仍能登记为 `source_checked`，且校验与搜索均误显当前。对此另存 `runtime-card-status-before.json`，没有修改旧复现记录。最终将可支撑已登记运行工具的卡状态限定为 `source_reviewed`、`sample_reviewed`、`behavior_checked`；三种状态都仍可开始 `authored` 运行工具的正常登记流程。新增一项回归覆盖 `draft`、未知及缺失状态的拒绝、校验失败、show/search 待复核提示，以及全部三个认可状态的正常登记。修复后原始结果为 `runtime-card-status-after.json`。

### R2 / P2：搜索结果不显示陈旧状态——已修复

修复前证据：`tool_runtime.py search` 原第164–193行直接将 runtime metadata 作为候选返回，不检查运行文件、原文、卡片或 WW 正文。一个源已变化的 TM 候选仍显示相同路径、任务和输出；只有另外执行 `show` 才知道陈旧，而入口的 `show` 是可选路径提示。

实际复现：修改临时模型的原文后，`show` 检出 `stale source fingerprint`，同次 `search` 仍返回不带任何陈旧警告的候选。结果同样保存在修复前 JSON。

修复：`tool_runtime.py:232` 对将返回的候选加实际状态检查，TM 和 WW 均返回 `fingerprints_current`、`freshness_issues`、`invocation_status`；TM 另含 `runtime_status` 和 `card_source_is_current`。陈旧条目仍可被发现，但明确标记 `review_required`，不能把词面命中当作已可直接调用。当前一致的结果写 `registered_current`，仍保留“非适用性或置信度”声明，不把文件一致称为真实效果验证。

新增回归同时改变 TM、WW 内容，确认两者仍可检索、均显式标陈旧；不隐藏候选或放松任何原有校验。

## 工作流检查结果

以下为文件规则一致性检查，并非本轮新做的真人对话或完整端到端行为验证。

| 检查点 | 证据位置 | 结论 |
|---|---|---|
| 逐轮追问与等待真实回答 | SKILL:31–37；guided-dialogue:9–11、44–55 | 每轮一个主要缺口，禁止伪造用户回答；信息足够或用户要求直接结果时推进。无需再增加固定问卷。 |
| 选型、互补交接及停止 | SKILL:43–62；toolbox-orchestration:19–41；tool-runtime:40–44 | 已要求每工具改变产物或行动、移除无贡献工具、解决冲突及停止条件；没有机械的固定工具数。 |
| 事实、推断、价值、假设、未知 | SKILL:64；tool-runtime:17–22、34–38；decision-report:9–15 | 已分开用户陈述和独立核验，区分意向/执行/结果，保留条件分支。未发现需要扩大规则的缺陷。 |
| 总预算与时间窗口 | SKILL:72；decision-report:19–21；toolbox-orchestration:39 | 已合计各工具动作、沟通准备复盘及已用资源，分开本周/每周/跨周期额度。无需重复加入同义限制。 |
| 默认 HTML 与降级 | SKILL:68–74；html-action-plan:7–22 | 明确分析完成后默认 HTML、用户指定格式优先；不可写入时交完整源码并准确说明状态；每轮追问不生成文件。 |
| HTML 内容安全与隐私 | html-action-plan:9–11；SKILL:82；maintenance:97、142–144 | 已要求正文和属性转义、离线内容、真实报告留任务、公开试跑用虚构/经授权材料、同步保留私人修改。 |
| 更新原文可靠性 | maintenance:3、9–10、64、128、138–144 | 不凭标题造文、保留可追溯全文、分开试跑与现实效果；但获取能力缺少历史成功方法的操作路由，见下方建议。 |

## 给主代理的文档衔接建议（本子任务未编辑）

1. 维护流程应链接新整理的来源获取经验：区分合集枚举和正文读取，普通浏览器 DOM 与直连请求是不同结果；单个直连请求返回验证页不能代表所有已授权途径均不可读。记录获取方式、完整性及真实失败类型。若正常浏览器本身要求人机验证，则请求用户完成验证，不绕过。此项主代理已在处理。
2. 搜索状态新增后，在维护或运行说明中解释 `review_required` 先回原文/卡片复核；`registered_current` 只表示登记与文件一致，不改变卡片/运行试跑的等级。
3. 每日自动更新是用户授权的独立调度，不应变成所有读者安装后的默认外部动作。维护文档可说“技能不自行安排定时任务；如用户已配置定时任务，沿用同一维护流程”。

## 实际验证

- 修复前：`library.py validate` 与 `tool_runtime.py validate` 均通过；原有 runtime 11、registration 3、WW audit 10，共24项脚本测试通过。结果：`runtime-test-results.json`。
- 修复后：runtime 14、registration 5、WW audit 10，共29项脚本测试通过；两个正式库校验再次通过；实际检索同时返回 TM/WW 并显示当前状态。结果：`runtime-test-results-after.json`。
- 二次审查最终复跑：runtime 14、registration 6、WW audit 10，共30项脚本测试通过。结果：`runtime-test-results-final.json`。复跑时主代理正在登记143原文，库已暂变为2.1.0/revision64/143源/142卡；library校验通过，runtime校验按预期检出 `Version mismatch` 与 `Migration inventory mismatch`。这是真实过渡状态，须在主代理完成卡片/运行登记后再次校验，不能据此声称2.1.0最终库已通过。
- 缺陷最小复现及修复后同场景原始结果：`runtime-adversarial-results.json`、`runtime-adversarial-results-after.json`。
- skill-creator `quick_validate.py` 本次环境无法执行：系统 Python 缺少 `yaml`（PyYAML）。未把它声称为通过，也不把依赖缺失列为技能自身缺陷。
- 本轮没有完成 HTML 视觉预览、全部142模型行为重跑或真实用户结果验证；以上结构/脚本通过不能替代这些证据。

## 编辑范围

仅修改 staged skill 的 `scripts/register_runtime.py`、`scripts/tool_runtime.py`、`scripts/test_register_runtime.py`、`scripts/test_tool_runtime.py`，以及本审计目录中的报告与原始测试回执。未改知识源、模型卡、运行工具正文、公开 README 或版本状态。初次测试生成的相关 Python bytecode 已清理；后续均使用 `PYTHONDONTWRITEBYTECODE=1`。


公开副本说明：仅将本机专属路径改成相对位置或通用占位；原始作答、失败与阶段状态保持不变。当前发布状态以本轮汇总记录为准。
