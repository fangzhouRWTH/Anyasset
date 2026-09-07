# Anygine / AI 开发接入指南

目标：让引擎提交声明输入依赖，工具提供本机路径；不把资产中心绝对路径写入 C++，不使用 submodule，不在共享消费目录运行 Git checkout。

## 已检查的引擎背景

本次接入参考 `Anygine` 的 `Engine` 分支提交 `b3e32a32`：引擎使用 CMake；`Source/Anygine/Assets/Private/DataPresetCatalog.cpp` 接受 `dataRoot` 并拼接资源相对路径；根 CMake 的 `AnygineRuntimeAssets` 处理生成 shader 目录。

Anyasset 当前两个样本不构成引擎已有 Assets 的替代。**不要直接把整个引擎 Assets/Data 根目录重定向到这份示例库**；需要先将对应内容和目录合同纳入 catalog。没有修改现有运行时 AssetManager 或 shader 管线，也不假定存在 `ANYGINE_ASSET_ROOT` 环境变量支持。

## 首次接入某个引擎 checkout

先将 Anyasset 的固定工具版本安装到独立 Python venv。可从本机仓库 `python -m pip install <asset-repo>` 安装，或从已发布 tag/commit 安装：

```powershell
python -m pip install "git+ssh://git@github.com/fangzhouRWTH/Anyasset.git@v0.1.0"
```

在引擎目录放 `assets.toml`（可复制 `examples/engine/assets.toml`），忽略 `.anyasset/`。初始化本地绑定：

```powershell
assetctl init --project <engine-dir> --store <shared-store-dir>

# 仅当引擎尚无 lock，或本任务明确要升级依赖时：
assetctl update --project <engine-dir> --ref <published-asset-commit>

assetctl sync --project <engine-dir> --locked
assetctl verify --project <engine-dir>
```

可通过 `--repo <local-asset-repo>` 使用已存在的本机资产仓库作为种子；不会修改它的 checkout。初次解析需要一个已有 commit，不能引用未提交资产。

把 `assets.toml`、`assets.lock.json` 和调用脚本提交进引擎仓库。新机器沿用这些文件，只需安装工具、init、sync。工具源码位于资产 repo，但固定安装后的工具不随素材版本 checkout 改变。

## AI 每次开发前

1. 确认当前引擎 checkout 与 Git 状态，不动其他工作目录。
2. 读取引擎 `assets.toml` / `assets.lock.json`；没有本地绑定时执行 init，store 路径来自用户/开发环境配置。
3. 执行 `assetctl sync --project <engine-dir> --locked`。离线时显式加 `--offline`，缺失就报告，不退回 main 或其他本机文件。
4. 执行 `verify`，随后使用 `path <logical-id>` 获得入口。`status` 返回 `asset_ids` 可查询当前锁定集合。
5. 生成结果写引擎 build 目录。禁止改 `store/views` 和 `store/objects`，禁止在初始化过程中执行 update。
6. 切换引擎分支或修改声明后，重新同步；旧绑定会被拒绝。

机器调用例：

```python
import json
import subprocess

result = subprocess.run(
    ["assetctl", "path", "--project", str(engine_root), "tests/triangle"],
    check=True, capture_output=True, text=True, encoding="utf-8")
mesh_path = json.loads(result.stdout)["path"]
# 将 mesh_path 传给真实应用已有的文件参数/配置入口。
```

若与引擎 Python 工具共用环境：

```python
from anyasset import resolve_asset
mesh_path = resolve_asset(engine_root, "tests/triangle")
```

`resolve_asset` 无网络，不隐式升级。需要全内容校验时先调用 `AssetManager(...).status(project, verify=True)`。

## CMake 接入

将 `examples/engine/Anyasset.cmake` 复制到引擎 CMake 模块目录。要求 CMake >= 3.19（string JSON）。选择安装了 anyasset 的 Python 解释器：

```cmake
include(CMake/Anyasset.cmake)
anyasset_resolve("${CMAKE_SOURCE_DIR}" "tests/triangle" ANYASSET_TRIANGLE_PATH)
# 使用 configure_file 将路径写入 build 目录的应用配置，或传给现有测试命令。
# 不要将本机路径写回源码。该模块不会下载素材。
```

配置阶段监视声明、lock 和 resolved 文件变化；引擎启动器可先 sync，再 cmake configure。路径包含空格时仍通过参数数组传递，不拼 shell 命令。

## 本地多仓库 / 多分支

每个引擎 worktree 独立 init，store 相同：

```powershell
assetctl init --project <engine-A> --store <same-store>
assetctl init --project <engine-B> --store <same-store>
assetctl sync --project <engine-A> --locked
assetctl sync --project <engine-B> --locked
```

相同 lock 复用同一 view；不同 lock 有各自目录。没有全局 current 链接。已经运行的进程可以继续使用旧路径；首版不自动删除历史视图。

## 新增/修改开发资产

1. `assetctl edit --project <engine> --destination <new-workspace>` 创建独立作者仓库；按返回的 next 提示运行 `git lfs pull` 后再编辑二进制文件。
2. 修改 content、catalog（入口、完整文件、依赖、许可、来源），运行 catalog-check。
3. 在独立应用测试配置中显式指向编辑文件；首版没有自动绑定 dirty workspace 的功能。
4. 提交资产到工作分支并 push；PR 合入后使用最终 commit。不要让引擎依赖只存在于自己机器的提交。
5. 引擎 update 到最终 commit，再 sync、verify 和引擎本身的测试。
6. 一起提交引擎代码与 lock。更改测试预期须单独审查，不自动接受新基准图。

## CI

安装固定工具版本，配置 Git/SSH 与私有 LFS 读取凭据，然后：

```sh
assetctl init --project . --store "$RUNNER_TEMP/anyasset-store"
assetctl sync --project . --locked
assetctl verify --project .
```

缓存 store 可以减少 LFS 下载。使用同一 OS 的缓存，恢复后 init 与 sync 会重新生成本机绝对路径；不缓存项目 `.anyasset/resolved.json` 作为跨机器路径来源。不要在 CI 中解析 main 或将任何令牌写进 assets.toml。GitHub Actions 自己的仓库令牌通常不能自动读取另一个私有仓库，需要配置相应的读取权限。

## 本次提供的本地接入

在 `Anygine_main` 中提供 `Scripts/AI/anyasset.py`、`Doc/Development/Anyasset.md` 和依赖声明/lock，作为可审查的接入起点。这些文件不要求重构引擎原有资产系统。提交/推送本次资产工具的目标是 Anyasset 仓库；引擎侧改动保留供引擎开发任务审查。
