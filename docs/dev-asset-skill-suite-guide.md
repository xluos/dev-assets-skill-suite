# Dev Asset Skill Suite 使用说明

## 套件作用

`dev-asset-skill-suite` 是一套围绕 Git 分支工作的开发资产技能。

它解决的核心问题不是“怎么写代码”，而是“怎么让一个分支上的开发记忆在跨会话时仍然可用，而且不会越写越像流水账”。

这次模型收敛后的原则很明确：

- `.dev-assets/` 只保留当前有效记忆，不复制完整源文档
- 具体做了什么，优先回 Git 提交历史看
- 具体需求、评审、方案、测试口径，优先回源文档看
- branch memory 只保留下次继续工作时最需要先知道的内容

## 目录结构

套件以当前 Git 分支为边界，在仓库里维护：

```text
.dev-assets/<branch>/
  overview.md
  development.md
  context.md
  sources.md
  manifest.json
  artifacts/
    history/
```

其中：

- `overview.md`：最短摘要。只保留当前目标、范围边界、阶段、关键约束
- `development.md`：当前工作态。重点是先看哪些目录、当前进展、阻塞、下一步
- `context.md`：稍详细但仍然有效的分支记忆，保留 why / caveat / handoff
- `sources.md`：源文档和 Git 历史入口，告诉 agent 需要时该去哪里读
- `manifest.json`：结构化元信息，例如当前 HEAD、默认基线、scope 摘要、focus areas
- `artifacts/history/`：需要落地的历史附件或归档产物

## 设计重点

### 1. 少文件，强分层

旧模型的问题是按 `prd / review / frontend / backend / test / commits` 拆得太细，导致：

- 入口文件越来越多
- 内容不断 append，越来越长
- 源文档和分支记忆重复

现在只保留三层主记忆：

1. `overview.md`：最短入口
2. `development.md`：当前工作态入口
3. `context.md`：稍详细但仍然可控的上下文

再加一个 `sources.md` 做回源索引。

### 2. `sync` 负责提交时的轻量沉淀，不负责记流水账

`dev-assets-sync` 不再把“这次做了什么”不断追加到文档末尾。

更合适的分工是：

- “做了什么、什么时候做的、改了哪些文件” → 看 Git 提交历史
- “原始需求、评审、方案、测试口径是什么” → 看源文档
- “下次继续时最需要先知道什么” → 看 `.dev-assets/`

所以 `sync` 的职责变成：

- 判断本次提交里哪些内容有跨会话价值
- 只更新和这次提交直接相关的 section
- 更新 `manifest.json` 的提交相关元信息

而 Git 导航刷新仍然主要属于 `context` 的恢复阶段。

### 3. 冷启动先看目录导航，而不是长篇笔记

`development.md` 和 `manifest.json` 会保存当前分支的 focus areas。

这不是历史记录，而是冷启动导航信息，帮助模型快速知道：

- 应该先去看哪些目录
- 当前主要改动集中在哪一层
- 接下来继续工作时可能要先进入哪些模块

## 每个 Skill 的作用

### `using-dev-assets`

套件总入口。

它不直接写资产，而是负责在 Git 仓库对话开始时判断当前应该走哪条路径：

- 继续已有分支工作时，路由到 `dev-assets-context`
- 新分支第一次开始时，路由到 `dev-assets-setup`
- 用户主动补充背景信息时，路由到 `dev-assets-update`
- 用户提到提交或 agent 判断到阶段性里程碑时，路由到 `dev-assets-sync`

### `dev-assets-setup`

初始化当前分支的开发记忆目录，并主动向用户收集：

- 源文档入口
- 当前目标与范围
- 当前阶段
- 关键约束
- 目前已知的注意点

它的重点不是继续复制一套 PRD / 评审 / 方案文档，而是把“当前记忆”和“源资料入口”先搭好。

### `dev-assets-context`

在继续开发前恢复当前分支上下文。

它会先：

- 定位资产目录
- 可选地刷新 `development.md` 的 Git 自动区
- 可选地刷新当前 HEAD、默认基线、scope 摘要、focus areas

然后由 agent 分层读取：

1. `overview.md`
2. `development.md`
3. `context.md`
4. 只有确实需要时，再去读 `sources.md` 里的源文档

### `dev-assets-update`

用于补充、修正、重写当前记忆。

当用户补充了新的背景、约束、风险、决策、源文档入口或工作状态时，这个 skill 会：

- 先结合当前会话做整理
- 再把内容写入 `overview / development / context / sources` 中最合适的 section
- 默认采用覆盖式更新，而不是继续追加同类信息

除了用户显式要求“记一下/更新一下”，也允许在以下场景隐式触发：

- 会话里连续出现理解偏差，用户多次纠正先前口径
- 用户提供了新的相关资料，而这些资料会明显改变后续理解或回源路径

但不要因为普通往返、轻微措辞修正或一次性澄清就频繁触发。

### `dev-assets-sync`

用于提交相关检查点，或 agent 判断当前已经到达一个值得收敛当前记忆的阶段。

它会：

- 只看这次提交相关的摘要
- 把本轮会话里仍有价值的 why / risk / next-step 写回当前记忆
- 更新 `manifest.json` 的提交相关元信息

它不会再单独维护 `commits.md`。需要了解具体改动时，应该优先查看 Git 历史。

## 推荐使用流程

### 流程 1：新分支第一次开始

1. 进入仓库并开始处理一个新分支上的需求
2. `using-dev-assets` 判断当前分支还没有资产目录
3. 路由到 `dev-assets-setup`
4. 初始化 `.dev-assets/<branch>/`
5. 收集源文档入口和当前摘要，而不是复制完整正文

### 流程 2：继续已有分支工作

1. 开始继续一个已经做过的需求
2. `using-dev-assets` 路由到 `dev-assets-context`
3. 刷新 `development.md` 的 Git 自动区和 focus areas
4. 先读 `overview.md`
5. 再读 `development.md`
6. 不够时再读 `context.md`
7. 仍不够时按 `sources.md` 回源

### 流程 3：中途主动补充信息

1. 用户补充了新的背景、约束、决策、风险、链接或源文档入口，或者会话中已经明显出现理解纠偏
2. `using-dev-assets` 路由到 `dev-assets-update`
3. 选择最合适的目标文件和 section
4. 直接重写当前有效内容，而不是追加同类旧内容

### 流程 4：提交前后或阶段性里程碑同步

1. 用户提到提交，或者 agent 判断当前已经形成新的稳定结论
2. `using-dev-assets` 路由到 `dev-assets-sync`
3. 只沉淀这次提交留下的关键信息
4. 需要时局部改写 `development.md` / `context.md`
5. 需要看具体改动时，回 Git 历史

## 这套设计的边界

它当前不负责的事情包括：

- 替代源文档系统
- 长期保存完整会话流水账
- 在 `.dev-assets/` 中复制所有提交历史
- 自动抓取外部链接正文并结构化归档
- 自动理解图片、附件、录音等非文本资产

它最适合的场景是：

- 一个分支会持续推进同一个需求或同一类需求点
- 你需要跨会话保持“当前有效记忆”
- 你希望冷启动时先知道该看哪些目录、当前做到哪、卡在哪

## 安装方式

查看仓库中的可用技能：

```bash
npx skills add xluos/dev-asset-skill-suite --list
```

为 Codex 全局安装整套技能：

```bash
npx skills add xluos/dev-asset-skill-suite --skill '*' -a codex -g -y
```

为所有已检测到的 agent 安装整套技能：

```bash
npx skills add xluos/dev-asset-skill-suite --all -g -y
```
