# v1.1.0 上传与 Zenodo 归档：从这里开始

本包用于创建 GitHub Release `v1.1.0` 和对应的 Zenodo 软件归档 DOI。该版本包含主分析资格标准统一、完整部署流程调参、更新的图表和完整可复现代码。

## 先确认：不要上传什么

**不要**把以下文件上传到 GitHub 或 Zenodo：

- 原始 `subjective.zip`；
- 原始 SoccerMon 数据文件；
- 本地 `outputs/` 中生成的完整 player-day CSV、individual predictions 或缓存；
- Python 虚拟环境、LaTeX 编译缓存。

本包不包含上述文件。

## 第 1 步：上传到 GitHub

1. 解压本 ZIP。
2. 打开 GitHub 仓库：`chy010321/next-day-readiness-womens-football`。
3. 将**解压后根目录中的全部内容**上传或替换到仓库根目录。
4. Commit message 建议：

```text
Release-ready v1.1.0 full-pipeline tuning and manuscript refinement
```

5. 刷新仓库主页，确认根目录至少可看到：

```text
.zenodo.json
CITATION.cff
LICENSE
README.md
requirements.txt
environment.yml
main.tex
references.bib
code/
data/
docs/
figures/
reproducibility/
sections/
supplementary/
tables/
```

尤其确认 `.zenodo.json` 存在，且其中版本为 `1.1.0`。

## 第 2 步：创建 GitHub Release

1. 在仓库中进入 **Releases**。
2. 选择 **Draft a new release**。
3. Tag 填：

```text
v1.1.0
```

4. Release title 填：

```text
Next-day readiness forecasting code and reproducibility materials v1.1.0
```

5. Release Notes 直接复制 `docs/RELEASE_NOTES_v1.1.0.md` 的内容。
6. 点击 **Publish release**。

## 第 3 步：检查 Zenodo

1. 登录 Zenodo。
2. 点击个人头像 → **GitHub**。
3. 点击 **Sync now**，确认仓库仍为 Enabled。
4. 等待 Zenodo 出现 v1.1.0 记录。
5. 打开记录后核查：
   - Version 是 `v1.1.0`；
   - 作者 Haoyang Cheng；
   - 单位 Wuhan Sport University；
   - ORCID `0009-0009-4123-2610`；
   - Licence 是 MIT；
   - 未出现 `subjective.zip` 或原始 SoccerMon 数据；
   - 相关来源包含 SoccerMon DOI `10.5281/zenodo.10033832`。
6. 复制该版本的**具体 version DOI**，不要复制 all-versions / concept DOI。

## 第 4 步：将新 DOI 写回论文

打开：

```text
sections/05_declarations.tex
```

将其中 `v1.1.0` 的 DOI 占位说明替换为真实 DOI，例如：

```text
10.5281/zenodo.12345678
```

然后在 Overleaf 用 **pdfLaTeX + Biber** 重新编译。

## 第 5 步：可复现性自检（推荐）

下载官方 SoccerMon `subjective.zip` 到本地，但不要上传到 GitHub。然后运行：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python code\run_all.py --data-zip "C:\你的路径\subjective.zip"
```

若末尾显示：

```text
All archived numerical verification checks passed.
```

说明关键数值结果已被本地复现。
