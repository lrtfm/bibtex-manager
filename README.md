# bibtex-manager

面向 JabRef 的保守增量合并工具：按 DOI 或标题与年份匹配条目，保留既有引用键和元数据，并可追加阅读备注。Python 3.10+，运行脚本仅依赖标准库。版本见 [VERSION](VERSION)，改动见 [CHANGELOG.md](CHANGELOG.md)。

## 安装与调用

通过 `skills` CLI 安装（需要 Node.js/npm）：

```sh
npx skills add lrtfm/bibtex-manager --skill bibtex-manager -a codex
# 全局安装追加 -g
```

也可克隆仓库直接运行，或使用 [Releases](https://github.com/lrtfm/bibtex-manager/releases) 中的 ZIP。手动安装应保留完整技能目录，包括 `VERSION`、脚本和引用资料；客户端发现方式及安装器要求以其自身说明为准。

调用示例：

```text
使用 $bibtex-manager，将 incoming.bib 合并到 /完整路径/library.bib。
核对预演后完成合并，保留备份并验证。
```

只需预览时说明“不写入”。执行约定见 [SKILL.md](SKILL.md)，无需额外的授权套话；技能不赋予文件访问权限。

## 命令行

在技能目录中运行，将路径替换为实际文件。预演包含输入结构校验：

```sh
python3 scripts/bibtex_manager.py merge --target /path/to/library.bib \
  --incoming /path/to/incoming.bib --diff
python3 scripts/bibtex_manager.py merge --target /path/to/library.bib \
  --incoming /path/to/incoming.bib --apply
```

- 默认仅预览，`--apply` 才写入；`--create` 允许目标不存在，并非禁止修改已有目标。
- `--comment-key KEY --comment-file notes.txt` 为输入中的指定条目追加备注，两参数须成对使用。
- 默认备份为 `library.bib.bak.<时间戳>`；仅在当前目标已有可靠恢复副本时考虑 `--no-backup`。无变化时不写入、不生成备份。
- JSON 报告包含 `added`、`matched`、`comments_updated`、`unchanged`、`conflicts`。有冲突时整次写入中止，其他数组只是拟操作。退出码 `0` 表示成功（包括预览），`2` 表示冲突或错误。

## 行为与恢复

- 按规范化 DOI 优先、标题与年份其次匹配；标识冲突、引用键冲突或多重匹配会中止。已有匹配条目仅更新 `comment`，不自动协调其他字段。
- 保留未修改部分的原文、UTF-8 BOM、换行符和 JabRef 元数据；备注字段可能重新序列化。备注仅按文本包含关系去重，不做语义判断；阅读计划可用[模板](references/reading-plan.md)。
- 不联网核验元数据，也不下载 PDF。结构校验不保证完整 BibTeX/BibLaTeX 或 JabRef 兼容性，输入的顶层元数据不导入；示例仅作演示。
- 写入前检查目标是否变化，并以临时文件原子替换；这不是文件锁，应避免并发编辑。恢复前保留当前版本，关闭编辑器，核对备份后再恢复。

## 维护

更新前保留自己的修改。克隆仓库可在工作区干净时用 `git pull --ff-only` 更新；安装副本再从已验证的开发版本同步。安装器管理的副本按其更新或卸载说明操作。

核对实现或准备交付时运行：

```sh
python3 -m unittest discover -s tests -v
python3 scripts/bibtex_manager.py validate examples/strang_splitting_references.bib
```

需要打包时运行 `python3 scripts/package_release.py`，生成版本 ZIP 和 SHA-256；打包不等于发布。详见 [发布说明](PUBLISHING.md)。普通文献导入无需重跑工具测试。

许可证：[MIT](LICENSE)。
