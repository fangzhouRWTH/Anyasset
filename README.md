# Anyasset — Anygine 开发资产库

Anyasset 管理引擎开发所需的标准素材、测试输入和共享参考数据。它不替代引擎运行时 AssetManager，也不是 submodule：引擎提交依赖声明和精确 lock，本机工具为多个项目提供可同时存在的资产快照。

**状态：v0.1.0 基础实现，Python 3.11+，Git，Git LFS。** 工具无第三方运行时依赖。仓库目前只有两个原创最小样本（PNG 棋盘、OBJ 三角形），没有迁移 Anygine 原有素材。PNG 由 `scripts/generate_checker.py` 生成并通过 LFS 跟踪；数据管理验证不替代引擎导入测试。

## 快速开始

仓库地址：`git@github.com:fangzhouRWTH/Anyasset.git`。

```powershell
git clone git@github.com:fangzhouRWTH/Anyasset.git Anyasset
cd Anyasset
git lfs install --local
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install .

# 首次给某个引擎工作目录建立本地绑定；路径换成自己的。
.\.venv\Scripts\assetctl.exe init --project D:/projects/Anygine/Anygine_main --store D:/AssetStore/Anyasset

# 首次解析或有意升级才运行 update。
.\.venv\Scripts\assetctl.exe update --project D:/projects/Anygine/Anygine_main --ref main
.\.venv\Scripts\assetctl.exe sync --project D:/projects/Anygine/Anygine_main --locked
.\.venv\Scripts\assetctl.exe verify --project D:/projects/Anygine/Anygine_main
.\.venv\Scripts\assetctl.exe path --project D:/projects/Anygine/Anygine_main defaults/checker
```

Linux/macOS 使用 `.venv/bin/assetctl`。开发本工具可 `python -m pip install -e .`；消费项目使用固定工具版本的非 editable 安装，避免作者 checkout 改变已安装工具。

也可以使用 `python scripts/assetctl.py ...` 从源码启动，但它会执行这个源码 checkout 当前的工具版本。

向引擎仓库提交 `assets.toml` 和 `assets.lock.json`；在引擎 `.gitignore` 中加入 `.anyasset/` 和本地资产仓库所在目录。不要提交缓存、绝对路径或嵌套 Git 仓库。已有 lock 的新机器只运行 `init` 和 `sync --locked`，不运行 `update`。

## 核心约定

1. **固定内容**：lock 包含资产源、完整 commit、所选集合、闭包内每个文件的 SHA-256/大小/LFS 标记、逻辑 ID 到入口文件的映射。
2. **共享下载**：同一 store 的所有项目复用 `objects/`，已缓存内容不会因项目数增加而重复下载。
3. **版本并存**：`views/<lock-digest>/` 不原地升级；不同 lock 使用不同目录，相同 lock 复用同一目录。
4. **路径本地化**：`.anyasset/resolved.json` 保存本机路径，`assets.toml` 和 lock 不保存本机路径（远端 source 应用可移植 Git URL）。
5. **明确升级**：`update` 改 lock；`sync --locked` 恢复 lock；`path` 只读，不联网。
6. **源输入不写入**：快照按协议只读，工具不覆盖已发布快照。v0.1 不设置系统 ACL，无法阻止外部编辑器改文件；`verify` 和 `sync` 会发现已选文件的内容变化并报错。
7. **写入串行化**：同一 store 的修改使用操作系统文件锁；进程退出会释放锁。30 秒等待超时后明确报错，可重试。

## 目录与责任

| 路径 | 内容 |
| --- | --- |
| `catalog.json` | 资产 ID、入口、完整文件列表、依赖、来源和许可、集合 |
| `content/` | 纳入版本管理的实际素材和测试输入 |
| `anyasset/` | Python API 与 CLI 实现 |
| `schemas/` | v1 JSON Schema 合同（TOML 声明用对应 JSON 数据模型描述） |
| `scripts/` | 源码启动器与本地验证脚本 |
| `examples/engine/` | 引擎依赖声明、Python 与 CMake 接入示例 |
| `tests/` | 临时 Git/LFS 仓库集成测试，不使用 GitHub 凭证或生产素材 |
| `.github/workflows/ci.yml` | Windows/Linux、Python 3.11/3.12 CI |

详细文档：

- [ANYGINE_INTEGRATION.md](ANYGINE_INTEGRATION.md)：引擎和 AI 调用方式。
- [INTERFACES.md](INTERFACES.md)：CLI、Python API、数据格式和错误约定。
- [ARCHITECTURE.md](ARCHITECTURE.md)：缓存、并发、恢复、版本边界。
- [MAINTENANCE.md](MAINTENANCE.md)：新增素材、发布、备份、故障处理。
- [AGENTS.md](AGENTS.md)：修改本库时必须遵循的工程约定。

## 日常工作

```powershell
# 获取指定引擎提交对应的资产
assetctl sync --project <engine-dir> --locked

# 无网络工作；缺失数据会失败，不静默使用其他版本
assetctl sync --project <engine-dir> --locked --offline

# 切换引擎分支后先检查，再恢复
assetctl status --project <engine-dir>
assetctl sync --project <engine-dir> --locked

# 有意升级：先确保目标资产 commit 已发布，再验证并提交引擎 lock
assetctl update --project <engine-dir> --ref <asset-tag-or-full-commit>
assetctl sync --project <engine-dir> --locked
assetctl verify --project <engine-dir>

# 编辑工作区独立于共享快照
assetctl edit --project <engine-dir> --destination <new-author-directory>

# 仅预览，不删除文件
assetctl gc --store <store-dir> --dry-run
```

可选本地种子：`init ... --repo <local-asset-repository>`。解析 Git commit 时优先从此仓库获取；联网模式的 sync 也可从其 LFS 对象目录导入已验证的对象，然后才向远端获取剩余对象。这里的“联网模式”只是允许联网，有完整本地种子时无需远端下载。`--offline` 要求共享 store 已准备好，不自动导入种子中的缺失 LFS 文件。重新 `init` 不传 `--repo` 可解除种子绑定。

## 验证

```powershell
python -m unittest discover -s tests -v
python -m anyasset catalog-check
```

测试覆盖双项目共享、多版本与回滚、离线、LFS、本地种子、依赖闭包、错误 lock、路径校验、损坏快照、进程并发和独立编辑。

## 首版边界

- 单个引擎 lock 对应一个源仓库 commit；未实现跨源依赖求解或逐资产版本约束。
- 已实现对象缓存去重；快照文件使用普通复制，多个版本仍可能占用重复磁盘空间，不使用硬链接。
- 已选资产的外部文件引用必须显式进入 `files`/`depends`；没有自动解析 glTF/USD/FBX 的全部引用。
- 不运行资产仓库里的构建脚本或 Git hooks，不内置导入器、烘焙器或派生缓存。
- 消费同步不支持自动开发覆盖；开发内容在独立工作区测试，发布后更新 lock。
- GC 只预览，保守保留项目历史绑定和 Git refs；对象清理、租约及远端备份是后续扩展。
- 限同机本地磁盘 store，不承诺网络共享文件系统上的锁与原子操作语义。
- Git LFS 成本仍按远端服务计算。缓存减少重复下载，不消除远端历史版本存储费。

## 许可

`catalog.json` 中两个原创样本按 CC0-1.0 提供。第三方素材必须逐项注明实际许可和来源；不要将未知许可内容标成 CC0。工具代码尚未选择对外开源许可证，仓库所有者可后续确定；公开仓库不自动授予开源许可。
