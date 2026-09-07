# 接口合同 v1

工具版本为 `0.1.0`，数据 `schema` 为整数 `1`。二者独立演进。Python >= 3.11；CLI 使用 UTF-8 JSON，成功 stdout 一行 JSON、退出 0，业务/文件/数据错误 stderr 一行 `{"code":"ASSET_ERROR","error":"..."}`、退出 2。参数解析错误由 argparse 输出帮助并退出 2。子进程 Git 输出不污染成功 JSON。

## CLI

所有项目命令支持 `--project <directory>`（默认 cwd）及 `--store <directory>`。未给 store 时读取项目 `.anyasset/config.json`。`init` 首次必须显式提供 store。

| 命令 | 参数 | 变更 | 结果主要字段 |
| --- | --- | --- | --- |
| `init` | `--source <url>` 可选，默认 Anyasset SSH URL；`--repo <path>` 可选 | 如无声明则创建；写本机 config；不写 lock | project, store, source |
| `update` | `--ref <branch/tag/full SHA>` 必需；`--offline` 可选 | 更新 lock；保存 Git 元数据；不下载 LFS 内容 | 完整 lock |
| `sync` | `--locked` 必需；`--offline` 可选 | 获取缺失内容、校验、发布快照与绑定 | schema, lock_digest, root, assets |
| `status` | 无额外参数 | 只读（获取 store 锁） | current, commit, snapshot, root, asset_ids, verified=false |
| `verify` | 无额外参数 | 对绑定与全部已选文件计算哈希 | 同 status，verified=true |
| `path` | `<asset_id>` 位置参数 | 无网络、无修改 | asset_id, path |
| `edit` | `--destination <new-directory>` 必需 | 新建独立 Git 编辑仓库 | workspace, commit, next |
| `gc` | `--dry-run` 必需 | 无删除 | retained, unreferenced_snapshots, dry_run |
| `catalog-check` | `--repo <directory>` 默认 cwd | 检查工作目录清单和文件存在 | valid, assets, collections |

`status current=false` 是成功查询，退出 0；自动构建应使用 `verify` 或 `path` 的失败码阻止继续。`path` 检查声明/lock/绑定一致性及目标存在，**不扫描全库哈希**；严格验证先运行 `verify`。没有 `latest` 隐式解析，没有 `--remote` 式自动升级。

## Python API

```python
from anyasset import AssetManager, AssetError, resolve_asset

manager = AssetManager("D:/AssetStore/Anyasset")
manager.init("D:/engine", source="git@github.com:fangzhouRWTH/Anyasset.git")
lock = manager.update("D:/engine", ref="main")  # 仅显式升级
binding = manager.sync("D:/engine", offline=False)
status = manager.status("D:/engine", verify=True)
path = resolve_asset("D:/engine", "defaults/checker")  # pathlib.Path
```

公开方法签名：

```python
AssetManager(store: str | Path)
init(project, source=DEFAULT_SOURCE, repo=None) -> dict
update(project, ref, offline=False) -> dict
sync(project, offline=False) -> dict
status(project, verify=False) -> dict
edit(project, destination) -> dict
gc() -> dict
resolve_asset(project, asset_id) -> Path
```

以 `_` 开头的方法不属于兼容承诺。预期操作失败抛出 `AssetError`；调用 Python API 的宿主也应捕获磁盘/权限等 `OSError`。API 不承诺不可信任意类型输入的异常归一化；CLI 已统一常见输入错误。

## catalog.json

结构见 [catalog.schema.json](schemas/catalog.schema.json)。每个资产由稳定 ID 标识：

```json
{
  "entry": "content/models/example/model.gltf",
  "files": ["content/models/example/model.gltf", "content/models/example/model.bin"],
  "depends": ["textures/example"],
  "license": "<actual-license>",
  "origin": "<actual-source-and-upstream-version>"
}
```

`entry` 必须属于自己的 files；`depends` 递归展开且不能有环；集合是资产 ID 数组。纹理、材质、sidecar、许可附件、外部 bin 等凡是消费需要的文件都要列出；目录不会隐式递归加入。共享文件可以被多个资产引用，最终按路径去重。

路径统一 POSIX 相对路径且以 `content/` 开头。禁止 `..`、绝对路径、反斜杠、Windows 保留名称、结尾空格/点、大小写冲突、glob 字符和逗号。Git symlink、submodule 和大于 16 MiB 的普通 Git 文件在解析时被拒绝；大文件应使用 LFS。只支持标准 SHA-256 LFS 指针，不支持 LFS pointer extensions。

## 引擎声明 assets.toml

```toml
schema = 1
source = "git@github.com:fangzhouRWTH/Anyasset.git"
collections = ["defaults", "tests/model-import"]
```

source 是版本身份的一部分，应使用团队统一、跨机器可访问的 URL。用 `init --repo` 表达本机种子，不把本机路径写入生产 source。配置 changes 均进入 requirements_digest，改变声明后需要显式 update。首版不解析版本范围，ref 仅来自 update 参数。

## assets.lock.json

结构见 [lock.schema.json](schemas/lock.schema.json)。由工具生成，禁止手工改文件哈希来接受不匹配内容。

- `commit`：源仓库完整 40 位 SHA-1 commit。
- `requirements_digest`：声明解析为 JSON 后的 canonical SHA-256。
- `collections`：去重排序后的集合。
- `files`：按 path 排序，包含 path、sha256、size、lfs。
- `assets`：依赖闭包中所有逻辑 ID 到入口路径的映射。

JSON canonicalization：Python `json.dumps(sort_keys=True,separators=(',',':'),ensure_ascii=False)` 的 UTF-8 编码。`lock_digest` 是完整 lock 的 canonical SHA-256；普通 Git 文件和 LFS 文件的内容校验都用实际字节 SHA-256，文件在快照中不做换行转换。

lock 固定元数据与内容，**不是签名**。它提供可复现性与一致性校验，不代替仓库权限和可信来源审查。

## 本机配置与绑定

`.anyasset/config.json`：schema、store（绝对路径）、可选 repo（本机种子路径）。

`.anyasset/resolved.json`：schema、lock_digest、root（快照绝对目录）、assets（逻辑 ID 到绝对文件路径）。结构见 [binding.schema.json](schemas/binding.schema.json)。引擎可读这个文件，或通过 API/CLI 读取单个文件路径；必须验证 lock_digest，不能复用旧分支留下的绑定。

store 的 `bindings/<project-id>.json` 保留项目引用过的所有快照；`snapshot.json` 保存对应完整 lock。它们是工具内部协议，使用者不直接修改。
