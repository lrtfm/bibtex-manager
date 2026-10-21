# bibtex-manager

面向 JabRef `.bib` 数据库的保守增量合并 Skill：按 DOI 或标题与年份识别重复条目，保留原始引用键和元数据，追加阅读备注，并在写入前预览、写入时备份。

Python 3.10+，运行脚本仅使用标准库。当前版本见 [VERSION](VERSION)，变更见 [CHANGELOG.md](CHANGELOG.md)。

## 安装

### 使用 npx skills

需要 Node.js 和 npm；`skills` CLI 的运行要求以其[官方说明](https://github.com/vercel-labs/skills)为准。

```bash
# 查看可安装的 Skill，不执行安装
npx skills add lrtfm/bibtex-manager --list

# 安装到当前项目，供 Codex 使用
npx skills add lrtfm/bibtex-manager --skill bibtex-manager -a codex

# 全局安装，供所有项目使用
npx skills add lrtfm/bibtex-manager --skill bibtex-manager -a codex -g
```

也可以省略 `-a codex`，交互选择其他受支持的 agent。此仓库根目录包含 `SKILL.md`，无需发布 npm 包。安装后在后续对话中使用；如客户端未发现，请刷新技能列表或新开对话。

### 克隆并直接运行

```bash
git clone https://github.com/lrtfm/bibtex-manager.git
cd bibtex-manager
python3 scripts/bibtex_manager.py --version
python3 scripts/bibtex_manager.py validate examples/strang_splitting_references.bib
```

也可从 [Releases](https://github.com/lrtfm/bibtex-manager/releases) 下载 ZIP，解压后进入 `bibtex-manager` 目录。手动安装时将整个目录放入客户端支持的 skills 目录，保留 `VERSION`、`scripts/`、`examples/` 和 `references/`，不要只复制 `SKILL.md`。

## 让 agent 使用

在支持显式 Skill 调用的客户端输入：

```text
使用 $bibtex-manager，将 incoming.bib 合并到 /完整路径/library.bib。
先验证并展示 dry-run 和冲突；确认目标文件后应用，保留备份。
```

亦可直接描述“合并 BibTeX、按 DOI 去重、保留 JabRef 分组并追加阅读备注”。是否自动选用取决于客户端。Skill 不赋予额外文件权限；目标文件必须实际可访问。脚本本身不联网核验文献，agent 应先用权威来源核验待导入资料。

## 命令行使用

以下命令均在 Skill 目录中运行；将目标路径替换为自己的文件。

```bash
# 验证输入结构
python3 scripts/bibtex_manager.py validate examples/strang_splitting_references.bib

# 默认仅预览；--diff 展示拟修改内容
python3 scripts/bibtex_manager.py merge --target /path/to/library.bib \
  --incoming examples/strang_splitting_references.bib --diff

# 核对目标与差异后写入，自动生成 library.bib.bak.<时间戳>
python3 scripts/bibtex_manager.py merge --target /path/to/library.bib \
  --incoming examples/strang_splitting_references.bib --apply

# 向输入中的指定条目追加阅读计划，仍先预览
python3 scripts/bibtex_manager.py merge --target /path/to/library.bib \
  --incoming examples/strang_splitting_references.bib \
  --comment-key Strang1968 --comment-file references/reading-plan.md --diff

# 创建单独的导入文件（不会覆盖已有文件的规则不变）
python3 scripts/bibtex_manager.py merge --target /path/to/new-library.bib \
  --incoming examples/strang_splitting_references.bib --create --apply
```

`--create` 允许目标不存在；`--apply` 才写入。`--comment-key` 与 `--comment-file` 必须成对提供，key 必须存在于输入中。`--no-backup` 可禁用备份，通常不建议使用。无变化时不写入、不生成冗余备份。退出码 `0` 表示成功（含预览），`2` 表示冲突、输入或文件错误。

JSON 报告包含 `added`、`matched`、`comments_updated`、`unchanged` 和 `conflicts`。存在冲突时整次操作不写入；此时其他数组仅表示分析出的拟操作，不表示已应用。备份可在关闭编辑器后手动复制回目标文件。

## 行为与边界

- DOI 优先匹配；标题与年份匹配也可识别缺少 DOI 的条目。相同标题/年份但 DOI 不同、相同 DOI 但标题不同、引用键冲突或多重匹配会中止合并。
- 保留目标中未修改部分的原文、UTF-8 BOM、换行符、JabRef 元数据、分组及附件字段；备注更新会重新序列化该字段。已有备注不删除，重复追加同一备注保持幂等。
- 仅合并条目及备注，不自动协调作者、年份、期刊、URL、分组或附件等其他字段的差异；请检查预览并在 JabRef 中按需处理。
- 结构检查器不等同于完整 BibTeX/BibLaTeX 编译器，不承诺支持所有宏、字段拼接、交叉引用或非标准语法。不要将含 `@string` / `@preamble` 的文件作为输入直接导入；输入的顶层元数据不会被迁移。先展开宏或在 JabRef 中处理。
- 不执行 DOI 检索、PDF 下载或语义去重。示例中的 6 条 Strang splitting 文献及阅读计划属于演示资料，正式引用前须复核原始来源。
- 写入前检查目标是否发生变化，并通过同目录临时文件替换；这不是文件锁。应用时应关闭正在修改该库的其他程序，避免同时写入。

## 更新与卸载

通过 `npx skills` 安装的副本：

```bash
npx skills check
npx skills update bibtex-manager
npx skills remove bibtex-manager
```

全局更新可加 `-g`；项目更新可加 `-p`。更新前保存自己的修改。克隆安装的用户在工作区干净时运行 `git pull --ff-only`，然后重新运行测试。固定版本可用 `git checkout v0.1.0`；如需升级回主分支，先 `git switch main`。

## 测试与打包

```bash
python3 -m unittest discover -s tests -v
python3 scripts/bibtex_manager.py validate examples/strang_splitting_references.bib
python3 scripts/package_release.py
```

打包程序先运行测试，再生成 `dist/bibtex-manager-<版本>.zip` 和对应 SHA-256 校验文件。归档使用明确的文件清单，不包含 Git 历史、缓存、备份或个人文献。GitHub Actions 在 Linux 的 Python 3.10、3.14 和 macOS 的 Python 3.14 上测试，并保留构建产物；版本标签必须与 `VERSION` 一致。详见 [发布说明](PUBLISHING.md)。

## 许可证

本项目采用 [MIT License](LICENSE)。
