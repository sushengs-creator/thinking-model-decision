# v2.8.0 本轮证据

2026-11-04，新增TM-159报童模型、TM-160稳定匹配模型。[结论与范围](../results-v2.8.md)。

- [17页合集扫描](album-manifest.json)：162项去重、160篇编号模型、2条未编号；旧001–158正文未重读。
- [正文、表格与指纹](source-manifest.json)、[159配图摘要](tm159-media-manifest.json)、[160配图摘要](tm160-media-manifest.json)。14幅原图留维护区，不随包分发。
- [159独立源审](reviews/source-review-independent159.md)、[160独立源审](reviews/source-review-independent160.md)、[初次表格问题](reviews/source-archive-binding-initial.json)、[修复读回](reviews/source-archive-bindings.json)。
- [159局部输入](inputs/tool-159.json)、[160局部输入](inputs/tool-160.json)、[入口输入](inputs/entry.json)。
- [159原答](trials/tool159.json)、[160原答](trials/tool160.json)、[入口原答](trials/entry.json)；对应manifest记录实际读取资源与输出SHA。
- [局部独立评审](reviews/tool-review.md)、[入口独立评审](reviews/entry-review.md)、[订餐HTML](trials/entry159-plan.html)、[配对HTML](trials/entry160-plan.html)。
- [检索初败](initial-retrieval.json)、[最终结构与28项检索](integrity-and-retrieval.json)、[官方结构检查](official-structure-check.json)。

7份实际响应、3个独立执行上下文：两个工具执行者各顺序处理2请求；入口执行者顺序处理3请求。局部允许文字输出，不计完整HTML文件交付。入口交付2份独立HTML；静态及内容核查通过，没有成功视觉预览。

159局部适用请求按字面定义的“总预订供给/总需求”可大于100%；原答同时列出实际满足份数口径。设计期待不能覆盖真实请求，未据此判假失败或改原答。另保留两项维护失败及修复：160相邻表格空行、运行索引缺“延迟接受”信号。

[公开路径转换及原始字节对照](publication-path-transform.json)只改变资源定位。原始SHA属于执行时材料，不冒充登记后的索引SHA。计算脚本及重复TXT留维护工作区，公开JSON保留完整原答、计算证据和审阅。没有真人效果、全库行为重测或所有客户端实机验证。
