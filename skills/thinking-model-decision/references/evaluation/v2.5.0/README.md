# v2.5.0 本轮证据

本轮新增 TM-156《决策树》。[完整范围和结论](../results-v2.5.md)。

- [完整合集扫描清单](album-manifest.json)：16 页、158 条去重项目、156 个编号模型、2 条非编号内容；结束标志已核对。
- [来源指纹](source-manifest.json)：本轮只完整重读 TM-156，2 张正文表格和 11 幅图片逐一核对；旧文 001–155 只核对目录元数据。
- [图片审阅](tm156-media-review.md)与[图像指纹](tm156-media-manifest.json)：原图只保留在维护工作区，未随技能分发。
- [局部请求](trial-inputs.json)与[入口请求](entry-inputs.json)：两名执行者各在一个上下文完成两案，共 4 份实际模拟回答。
- [局部原答清单](trials/tool-trials-manifest.json)、[入口原答清单](trials/entry-trials-manifest.json)及[完整 HTML](trials/entry-staged-choice.html)。
- [来源独立复核](reviews/source-and-cases-review.md)、[局部逐案评审](reviews/tool-review.md)、[入口逐案评审](reviews/entry-review.md)。
- [结构和检索检查](integrity-and-retrieval.json)、[初次检索失败](initial-retrieval.json)及[官方结构检查](official-structure-check.json)。

公开副本只将本机绝对路径换成相对路径或维护位置标签；保留原答和评审的全部内容。清单和评审中的原始 SHA 指向实际运行时文件，公开副本 SHA 见[路径转换对照](publication-path-transform.json)。原答没有按评审意见回填；局部误用回答保留一处不影响时序结论的措辞问题及 P3 观察。来源评审发生在试跑前，其“尚不能发布”状态是历史时点记录；发布结论以本轮最终检查为准。

HTML 做了内容、计算、链接和静态结构检查，没有浏览器视觉预览；没有真实业务效果、真人用户可用性或所有客户端验证。
