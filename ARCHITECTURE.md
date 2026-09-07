# 架构与可靠性

## 数据流

```text
assets.toml --explicit update(ref)--> assets.lock.json
                                          |
                                     sync --locked
                                          |
             managed bare Git repo -> selected file records
                                          |
                   shared SHA-256 objects (Git/LFS)
                                          |
                         staging directory + verification
                                          |
                              views/<lock-digest>
                                          |
                    per-project .anyasset/resolved.json
```

## 为什么没有消费 worktree

首版进一步使用“读取 commit 中的 Git blob 和 LFS 指针，再物化所选文件”，而不是为每个消费版本 checkout 一个完整 worktree。这样只暴露已声明的文件，没有作者脚本执行或消费目录 HEAD 切换，也避免自动 smudge 下载全部 LFS 文件。编辑命令仍会创建真正的独立 Git checkout。

## 本机布局

```text
store/
  manager.lock              操作系统字节/文件锁，文件可长期存在
  repos/<source-digest>.git 管理工具自己的 bare repo
  objects/aa/bb/<sha256>    普通资产与 LFS 共用的内容地址空间
  views/<lock-digest>/      按协议不可变的已准备快照
    snapshot.json
    content/...
  views/.prepare-*/         未发布临时目录，不能用于引擎
  bindings/<project-id>.json
```

每个 managed Git repo 设置 `lfs.storage` 到 store 根目录。Git LFS 在其 `objects/` 下按 SHA-256 分片保存数据；普通 Git 数据使用相同布局。工具只在自己管理的 bare repo 中写配置，不修改作者 repo 的 LFS 配置。不得对这个目录独立运行 `git lfs prune`：Git LFS 并不知道其他源仓库和项目的引用。

## 恢复算法

1. 验证声明与 lock 一致；同一 store 获取 OS 锁。
2. 已有快照时验证 lock 元数据和所有已选文件哈希，再生成/刷新绑定。
3. 未有快照时取得固定 commit，重新解析 catalog 与 lock 比对。
4. 已验证对象命中则复用；普通文件从 Git 读取，LFS 从种子或远端获取。
5. LFS 按缺失文件路径获取，首版每个缺失文件一次 fetch，后续可批处理。
6. 将文件复制到临时快照，检查大小与 SHA-256，然后同文件系统 rename 发布。
7. 先保存保留引用，再以临时文件 + replace 更新项目绑定。

重复调用幂等；lock 不变不会联网查询 main。完整 view 存在时离线不依赖源仓库。只有 Git 元数据存在但 LFS 内容缺失时，offline 会失败。

## 并发与版本隔离

所有修改持有 store 全局锁，包括 Git/LFS 获取、物化、注册与 GC 预览。吞吐优先级低于正确性，首版不会并行下载不同版本；超时可重试。锁由 OS 释放，不依赖手工删除 PID 文件。

不同快照间使用复制，不使用硬链接；外部误写一份快照不会破坏内容缓存或另一个版本。但相同 lock 的项目共享同一 view，误写会影响所有这些项目，所以编辑必须去独立工作区。

不承诺对恶意同用户进程实现安全沙箱。store/config 是受信任本机状态。清单校验拒绝路径穿越、非普通 Git 文件、跨平台歧义路径；项目不执行远端代码。大普通 Git blob 限制在 16 MiB，避免意外将大型素材作为文本历史处理。

## 崩溃与损坏

中断前已缓存对象可复用；未完成临时目录不会生成有效绑定。崩溃留下 `.prepare-*` 可以在停止所有工具后人工检查清理，正式 views 不受影响。

快照损坏时工具报错，不原地修复，以免正在运行的引擎看到半更新内容。停止引用该快照的进程后，由维护者将损坏快照移至隔离位置，再 sync；不要在运行中替换快照。文件 hash 校验不意味着磁盘断电事务保证；出现存储故障应验证并重新准备。

## 保留与备份

首版记录项目引用过的全部快照，避免分支切换后旧进程仍在读取时被清理。GC 只报告未引用快照，不执行删除。`refs/anyasset/retained/<commit>` 保留缓存的 Git commit；不要手工改写已发布远端历史。

本机缓存不是备份。远端备份必须包含 Git refs 和被引用 LFS 实际对象；只镜像 Git 指针不能恢复素材。离线工作需要在离线前完成目标版本 sync。不同机器各有 store，同机缓存不会自动减少其他机器首次下载。

## 后续扩展点

对象获取可扩展 HTTP/S3；快照复制可扩展 reflink；全局锁可细化为对象/快照锁；GC 可引入显式 pin/unpin、进程租约和保留期。schema 变化必须提升版本，保持旧 lock 可被旧工具使用。烘焙缓存另外设计，key 包含源 hash、导入器版本、设置和平台。
