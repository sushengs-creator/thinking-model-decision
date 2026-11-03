# v2.7.0 本轮证据

新增 TM-158《排队模型》。[验证结论与范围](../results-v2.7.md)。

- [16页完整合集扫描](album-manifest.json)：160项去重、158篇编号模型、2条非编号内容，结束及首尾复核通过；001–157旧正文未重读。
- [正文来源与指纹](source-manifest.json)、[18图逐张审阅](tm158-media-review.md)、[媒体指纹](tm158-media-manifest.json)。原图保存在维护区，不随技能分发。
- [独立原文审阅](reviews/source-review-independent.md)、[卡片与案例输入审阅](reviews/source-and-cases-review.md)。原文保留，错误与过强推断在派生操作规则中限定。
- [局部输入](trial-inputs.json)、[入口输入](entry-inputs.json)；初次与复跑均为执行者真实原答，分别保留。[初次局部清单](trials/tool-trials-manifest.json)、[局部复跑清单](trials/tool-retest-manifest.json)、[初次入口清单](trials/entry-trials-manifest.json)、[入口复跑清单](trials/entry-retest-manifest.json)。
- [初次局部失败评审](reviews/tool-review-initial.md)、[局部最终独立评审](reviews/tool-review.md)、[入口最终独立评审](reviews/entry-review.md)、[当前完整HTML原答](trials/entry-queue-choice-retest.html)。
- [初次检索测试记录](initial-retrieval.json)、[最终结构与检索](integrity-and-retrieval.json)、[官方结构检查](official-structure-check.json)。初次旧入口名称与预期ID对应错误经纠正，不冒称修改了旧工具召回机制。

总计8份实际响应，来自4名执行者各自一个上下文、每个上下文顺序处理2请求。初次误用回答曾将外排存量误加到昨日流量，保留失败原答；新增存量/流量/时间窗规则后，重新执行两份局部及两份入口请求并独立评审。最终状态不抹去初次失败。

公开副本只做资源定位转换；[原始/公开字节对照](publication-path-transform.json)记录SHA。清单里的执行时SHA不是路径转换后字节，也不是正式登记后的索引SHA。HTML仅内容与静态检查，没有成功视觉预览、真人使用、业务效果或所有客户端验证。
