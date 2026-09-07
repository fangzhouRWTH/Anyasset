# 维护与发布

## 添加资产

1. 为资产选择稳定 ID 和 `content/<category>/<name>/` 路径。可复用的集合以用途命名，不以机器或当前开发者命名。
2. 在 `.gitattributes` 添加需要的 LFS 类型，**先 track 再 add**。已入 Git 历史的文件不会因新增规则自动迁移。
3. catalog 记录入口、完整伴随文件、依赖 ID、真实许可与来源。需要统一单位、轴、颜色空间的格式，把约定记录在文件或 asset 元数据中；非消费文件如说明可留在目录但不会被下载到 view。
4. `python -m anyasset catalog-check`，再运行全部集成测试。
5. `git add` 指定文件，检查 `git diff --cached`、`git lfs ls-files`，提交并 push。
6. 引擎端显式更新 lock，执行真实引擎导入/回归测试。工具测试只保证分发完整，不保证引擎格式兼容。

新测试集合不要默认加入 defaults，避免引擎启动下载大型基准。跨文件引用必须完整声明；小数据可普通 Git，大于 16 MiB 的普通 blob 被工具拒绝。

## 工具发布

1. 更新 pyproject、`__version__` 和 CLI version 的一致版本。
2. 保持 schema 1 兼容；不兼容改变用新 schema，明确迁移方式。
3. 跑 Windows/Linux CI 和本地集成测试；检查安装后的 CLI，而不仅是源码启动器。
4. 提交、push，再创建不可移动的 tag（初始版本 `v0.1.0`）。
5. 消费端固定 tag 或完整 commit 安装。无需每增加一个素材就升级工具版本；素材 commit 本身就是版本。

`update` 不会替你上传任何内容。资产 commit 和 LFS 文件应先在远端可获取，随后才能把依赖它的引擎 lock 发布。不要 force-push 覆盖被引擎引用的历史。

## 常见问题

| 问题 | 处理 |
| --- | --- |
| Binding stale / Requirements changed | 检查分支；声明未改则 sync，声明有意修改则 update 后审查 lock |
| offline 缺少 LFS | 在线/本地种子模式先 sync 完成，再离线；不要修改 lock 绕过 |
| 私有仓库 fetch 失败 | 检查当前身份的 Git/SSH/LFS 权限；工具禁止交互式 Git 凭据提示 |
| Snapshot corrupted | 停止使用它的进程，隔离损坏快照，然后 sync 重建；不要在线原地修改 |
| Asset store busy | 等待当前下载/准备完成后重试；OS 锁无需手工删文件 |
| Windows 路径错误 | 使用较短的 store 路径，保持可移植相对路径、避免名称大小写冲突 |
| 普通 Git 文件超 16 MiB | 配置 LFS，重新正确提交；已有历史迁移须单独计划 |
| 编辑仓库中只有 LFS 指针 | 先在编辑目录运行 `git lfs pull`，不要用指针文件作为模型 |

## 存储与回收

`assetctl gc --store <path> --dry-run` 只预览。首版不执行自动回收，不提供删除所有旧版本的捷径。历史绑定故意保留，防止仍在运行的旧进程失去输入。不要直接对 managed repos 运行 prune、checkout、reset 或 LFS prune。

如确需重建缓存：先停止所有消费和管理进程，保留源仓库/远端，再指定一个新 store 重新 init/sync。旧 store 的删除应是独立、确认范围后的维护动作。不能把只存在旧 store 的未备份内容当成可重建数据。

## 备份

- 备份 Git 全部所需 refs 和 LFS 实际对象；Git bundle 或 bare mirror 单独都不包含所有 LFS 内容。
- `git lfs fetch --all` 会下载历史数据并消耗带宽，适合专用备份流程，不用于普通初始化。
- 定期在没有作者工作区的干净目录恢复一组历史引擎 lock，确认远端数据可用。
- 本机 views/objects 是缓存，不是唯一备份。远端保留策略不得删除仍被已发布引擎版本引用的内容。

## 测试维护

`tests/test_manager.py` 使用临时本地 Git/LFS 仓库，不需要 GitHub 网络。增加能力时添加行为级集成测试，尤其是多项目、离线、损坏、权限和并发失败路径。测试不能写入生产 store，不允许通过测试清理用户资产。
