# 发布与维护

仓库名：`lrtfm/bibtex-manager`。版本以 `VERSION` 为准，Git 标签使用 `v<版本>`。发布前更新 `CHANGELOG.md`，运行测试并审阅待提交文件。MIT 许可证已由维护者确认。

## 首次发布

下面命令适用于尚未初始化、尚未创建 GitHub 仓库的源码目录；若仓库或远程已存在，不要重复创建，也不要强制推送。

```bash
gh auth login --hostname github.com
gh auth status
python3 -m unittest discover -s tests -v
python3 scripts/package_release.py
git init -b main
git add .
git diff --cached --stat
git commit -m "Release bibtex-manager v0.1.0"
gh repo create lrtfm/bibtex-manager --public --source=. --remote=origin --push
```

推送后检查 Actions 成功，再建立版本标签及 GitHub Release：

```bash
gh run list --repo lrtfm/bibtex-manager --limit 5
# 将 RUN_ID 替换为对应提交的实际运行编号
gh run watch RUN_ID --repo lrtfm/bibtex-manager --exit-status
git tag -a v0.1.0 -m "bibtex-manager v0.1.0"
git push origin v0.1.0
gh release create v0.1.0 dist/bibtex-manager-0.1.0.zip \
  dist/bibtex-manager-0.1.0.zip.sha256 --verify-tag \
  --title "bibtex-manager v0.1.0" --notes-file CHANGELOG.md
```

通过 `git ls-remote --heads origin main`、`gh release view v0.1.0` 及下面的发现命令核验公开结果：

```bash
npx skills add lrtfm/bibtex-manager --list
```

## 后续版本

更新 `VERSION`、变更记录及文档里的固定版本示例。运行测试与打包，提交并推送主分支，确认对应 CI 成功，再使用新版本标签重复上述发布操作。不要移动已发布标签。
