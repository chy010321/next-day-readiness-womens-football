# v1.1.1 GitHub / Zenodo 发布说明

这是 `v1.1.1` 的**维护与纠错发布包**。它不是新的实质性模型重分析，因此不应标注为 `v1.2.0`。

## 本版本已完成

- 修复 `alpha=0` 的实现：现在使用 `LinearRegression()`，不再使用 `Ridge(alpha=0)`。
- 统一术语：模型中使用的是 3/7 天 **readiness-reporting rates**，不是 wellness-reporting rates。
- 增强复现实验的自动校验范围。
- 修正表格、图号、缺失数据说明、Zenodo 元数据和 GitHub 文档。
- 使用 Type 42 字体嵌入重新生成 Figure 1 和 Figure 2。
- 根据完整复跑审计，主结果、选中的惩罚参数和已报告的敏感性结果均未改变。

## 创建 GitHub Release

1. 将此压缩包解压后的内容替换到 GitHub 仓库默认分支。
2. 检查 `.zenodo.json`、`CITATION.cff` 和 `README.md` 已显示 `v1.1.1`。
3. 在 GitHub 的 **Releases -> Draft a new release** 中创建 tag：`v1.1.1`。
4. 标题建议：`v1.1.1 - reproducibility and reporting corrections`。
5. 复制 `docs/RELEASE_NOTES_v1.1.1.md` 中的发布说明。
6. 发布后等待 Zenodo 自动归档并生成新的版本 DOI。
7. DOI 生成后，按照 `docs/AFTER_ZENODO_DOI_v1.1.1.md` 仅在默认分支和投稿稿件中填入 DOI；不要修改已发布的 tag。

## 不要现在创建 v1.2.0

`v1.2.0` 应留给真正的实质性重分析，例如 weekday/month 重新编码、增加朴素基线和 population-only 基线、cold-start 分层、预测值 1--10 边界敏感性、真实部署可用性分析等。详见 `EDITORIAL_AND_ANALYSIS_NEXT_STEPS.md`。
