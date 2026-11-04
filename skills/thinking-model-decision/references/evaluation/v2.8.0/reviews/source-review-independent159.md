# TM-159 独立来源审阅

时间：2026-11-04T01:28:59.428683+00:00

完整读取浏览器正文及2张HTML表；独立重算见[source-arithmetic159.json](source-arithmetic159.json)。本文评审者未目视媒体；主代理媒体检查另记。正文UTF-16码元6710，FNV b0ec5c42，源保持原样。

- **ratio_drift / P1_source**：Only demand changes makes80%wrong contradicts earlier correct statement. Keep original; runtime must keep alpha fixed if Cu/Co fixed and recompute Q from changed distribution.
- **forecast_recourse / P1_source**：Can forecast or replenish does not categorically exclude model. Uncertainty after forecasting remains; fixed guaranteed emergency is compatible with the article objective.
- **discrete_median / P2_source**：Symmetric costs imply a median, not exactly50%strictly each side. Original table has .3/.4/.3 around10.
- **service_metrics / P1_misuse_risk**：Economic alpha=.8, cycle service=.9 and pooled unit fill=.99 atQ11 are different. Any service or cash redline is a separate constraint.
- **strict_monotonicity / P2_source**：Larger cost asymmetry changes target quantile under fixed distribution; discrete order quantity can remain unchanged.
- **cost_objective / P1_misuse_risk**：Emergency100 is gross cash; underage80 is incremental. Do not double count. Expectedcost230 is not cashmaximum320.
- **policy_demand / P2_source**：Policy changes may alter demand but do not logically force a change. Re-estimate conditional distribution without manufacturing evidence.
- **research_history_scope / P3_limit**：Store news/history verbatim with provenance; do not upgrade broad most errors or individual bias claims to verified facts.

## 核查来源与范围

- [MIT primary course notes: assumptions, incremental marginal comparison, overage/underage, CDF lower quantile; read pages1–7 extracted text. The note also uses the upper-tail complementary ratio, which must not be confused with CDF alpha.](https://ocw.mit.edu/courses/15-772j-d-lab-supply-chains-fall-2014/6952be57b43aa185119c6f114908bcc5_MIT15_772JF14_Newsboy.pdf)
- [Original 2000 paper abstract, introductory experimental pattern and model definition pp404–406. Supports the specified experiments, not all managers or all sectors. Full experimental/reanalysis replication not performed.](https://faculty.wharton.upenn.edu/wp-content/uploads/2012/04/Cachon_schweitzer_ms.pdf)

结论：正文可用于可追溯归档；操作层必须明确以上边界。尚未据此宣称卡片、运行工具或实际行为测试通过。

## 完整源归档补绑定

2026-11-04T01:36:47.783823+00:00：源Markdown SHA-256 `2bf344d2472eeee74f535f1a8cf705123fa69e43f921e0dbf8663592fdb4afd3` 已与source-manifest实算对齐，全部正文去空白字序及2张表逐格保持原文。草稿指纹与已审版本一致。媒体清单含root逐张目视摘要；我仅核对10份图片字节哈希和清单，没有个人目视。归档就绪不改变行为测试未执行/未审阅状态。
