# 发布说明

沿用仓库 `lrtfm/bibtex-manager` 及现有 `origin`，无需重新初始化或创建远程。版本以 `VERSION` 为准，标签为 `v<版本>`；不要移动已发布标签。

## 本地准备

未发布的修改记录在 `CHANGELOG.md` 对应版本下；正式发布时将“未发布”改为发布日期。检查版本、变更记录和待提交差异后打包：

```sh
python3 scripts/package_release.py
```

该命令自动运行测试、验证示例和技能头部，生成 `dist/bibtex-manager-<版本>.zip` 及 `.zip.sha256`，无需事先重复运行同一套测试。归档使用脚本中的文件白名单，不含 Git 历史、缓存或个人文献。

将最终源码和文档提交到本地，确保打包内容对应发布提交。本地提交和打包均不上传内容；未获推送或发布授权时到此为止。

## 推送与发布

以下仅用于已获授权的发布，需有可用的 GitHub CLI 登录。命令在仓库根目录运行，版本从文件读取：

```sh
release_version=$(cat VERSION)
git push origin main
gh run list --repo lrtfm/bibtex-manager --commit "$(git rev-parse HEAD)" --limit 5
```

确认该提交的 CI 成功后，创建并推送对应标签，再检查标签触发的 CI。工作流会检查标签与 `VERSION` 是否一致：

```sh
git tag -a "v${release_version}" -m "bibtex-manager v${release_version}"
git push origin "v${release_version}"
```

标签 CI 成功后，上传对应提交生成的归档及校验文件：

```sh
gh release create "v${release_version}" \
  "dist/bibtex-manager-${release_version}.zip" \
  "dist/bibtex-manager-${release_version}.zip.sha256" \
  --verify-tag --title "bibtex-manager v${release_version}" \
  --notes-file CHANGELOG.md
```

完成后用 `gh release view "v${release_version}"` 核对版本及附件。CI 只测试和保存构建产物，不会自动创建 GitHub Release。
