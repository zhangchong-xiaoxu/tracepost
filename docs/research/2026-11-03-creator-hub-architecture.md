---
type: research
status: done
updated: 2026-11-03
---

# tracepost 架构复核

> 研究时项目暂名 Creator Hub，后因同名项目已存在改名为 tracepost；正文保留研究当时的称呼。

> 对应 [产品规格](../specs/2026-11-03-creator-hub.md)。`done` 表示本轮研究已整理，不表示实现、平台授权或实机验收已完成。
> 方法：公开官方文档检索、Context7 文档查询、GitHub 元数据 / 许可 / 关键源码抽查。未安装候选项目、未登录账号、未运行采集、未创建 public 仓库。

## 1. 结论与已确认决策

**推荐一个本地优先的数据产品，不推荐把几个现成爬虫 / MCP 服务套在同一个页面里。**

最小完整架构是：**平台 adapter → 有口径的 SQLite 快照 → 共用查询与分析 module → Web / CLI / MCP**。浏览器只是可替换的数据入口，不是产品核心，也不让 AI 每次查数都重新操作网页。

用户本轮确认：

- 第一版同时支持抖音、小红书，包含本地 Web 看板与 Agent 接口。
- 作品基础指标、平台可得的深度指标、历史快照趋势、粉丝趋势、同内容跨平台比较均需要；读评论不阻塞首版。
- public 的是源码，用户各自在本机运行；Windows 优先、跨平台设计，不做在线账号托管。
- 采用 **MIT** 方向，降低复用 / 集成门槛；不直接引入 AGPL 实现。许可证选择不能保证项目获得关注。

相对旧规格，需要改变的不是“换一个采集框架”，而是：

1. 看板与跨平台比较不再后置到不确定的未来。
2. Playwright 不等于只读 DOM：后台自带导出、页面产生的 JSON 响应、DOM 是不同采集路径。
3. 先建立可信数据契约，再接 UI / Agent；不能直接继承候选项目的缺失值、时间和身份假设。
4. 官方 API 能力按平台、账号和申请结果选择，不把“浏览器保底”变成“任何情况下都必须爬”。

## 2. 架构方案比较

以下是基于本次约束的工程判断，不是性能实测排名。

| 方案 | 好处 | 对本项目的实际代价 | 结论 |
| --- | --- | --- | --- |
| 直接扩展 `xhs-trail` | MIT，已有 React 看板、FastAPI、SQLite 和快照分析 | 单小红书、文件导入、按日模型；缺失默认 0，需要改身份、口径、观测时间和同步状态 | 可选择性复用 UI / 导入逻辑，不默认原样 fork 成最终核心 |
| 拼接现成抖音 MCP + 小红书 CLI | 最快得到各自演示 | 多套登录态、状态目录、错误协议、数据模型与更新生命周期；抖音候选还有 AGPL 限制 | 适合探索，不作为 MIT 首版底座 |
| 本地模块化单体 | 一个事实源，Web / Agent 一致；只维护两个平台 adapter | 需要实现最小快照契约与统一错误语义 | **推荐** |
| 浏览器扩展 + 本地应用 | 用户可在日常浏览器中主动读取，登录摩擦可能更小 | 扩展权限、分发及本地桥接；Native Messaging 还需平台相关注册，不天然省掉本地程序 [B4] | 专用浏览器体验不成立时再比较 |
| 全 TypeScript / Node | 一个语言生态，Playwright 与 MCP 都可用 | 本轮明确的 MIT 小红书 / 分析候选在 Python，直接选此路线会减少代码复用 | 可行备选，不因“前端也是 TS”就先重写采集 / 分析 |
| 云端 SaaS / Docker 优先 / 桌面壳 | 远程常开或安装入口统一 | 前者改变账号托管与登录条件；后者增加打包升级工作，不解决数据准确性 | 首版不选；不是永久禁止 |

不引入 LangChain / 多 Agent 编排、Redis / Celery、PostgreSQL、插件市场。这里的任务是有界采集和确定性查询，没有需要这些能力的已确认需求。

## 3. 数据入口：按字段选，不强求两平台对称

### 3.1 推荐采集次序

1. **正式开放 API**：当应用资格、用户授权、字段与历史覆盖都满足时使用。
2. **浏览器触发官方导出**：如果后台文件能覆盖目标字段，用 Playwright 操作导出并接收文件。这是自动采集，不是要求人每天手动导出；下载能力有官方文档 [B2]，两平台实际导出覆盖尚未实测。
3. **读取正常浏览产生的结构化响应**：先安装响应监听，再导航 / 点击 / 翻页；只提取目标数据字段。Playwright 明确支持响应事件与等待响应 [B1]。
4. **DOM 读取**：补充页面独有字段或作为最后的数据解析路径。不要用截图 OCR / LLM 猜数字作为正常链路。

这是**预先验证后的路径选择**，不是失败后盲目自动切换。权限拒绝、验证码、账号异常时停止；解析结构改变时保留错误，不伪装成空数据。JSON 响应也会变化，并非稳定或获授权的公共接口。

不复制 cookie 到独立 HTTP 爬虫、不重放签名接口、不使用 stealth / 指纹伪装 / 验证码绕过作为默认产品能力。浏览器只读本人数据仍不等于符合平台条款或无风控风险。

### 3.2 平台官方接入核实与证据等级

**重要限制**：平台文档多为动态站点。本轮独立研究获取了官方域名的搜索摘录，但部分直接 fetch 只返回页面壳。下表因此标为“官方页搜索摘录”，**不冒充完整正文核验、申请成功或实际接口测试**。链接供进入实现前重新核对。

| 平台 / 能力 | 本轮找到的依据 | 对架构的影响 / 未核实项 |
| --- | --- | --- |
| 抖音开发者入驻 | FAQ 摘录区分个人身份与企业身份；移动 / 网站应用主体资格与“小玩法”不同 [D1] | **开发者主体 ≠ 授权的创作者账号**。需核对应用类型与主体，不应推导为“所有个人创作者都无法授权已有合规应用” |
| 抖音视频列表 / 视频数据 | 查到查询授权账号视频列表、特定视频数据与视频数据能力文档；摘录出现 `video.list.bind` / `video.data.bind` [D2]、[D3]、[D4] | 存在正式候选，不可泛称“抖音没有 API”。文档描述用户视频，未见仅限本应用发布的限制；既有作品、可见性、字段与额度仍须申请后实测 |
| 抖音 `data.external.item` | 查到点赞 / 分享 / 评论数量等数据文档；摘录提示创建时间窗口及首次授权后数据准备限制 [D5] | 不能当作无限历史回填。评论**数量**不等于评论正文 |
| 抖音评论列表 | 查到独立评论管理文档，支持评论列表这一能力 [D6] | 读取正文需要独立的能力 / 权限核验；不随作品计数默认获得，也不进入首版硬验收 |
| 抖音粉丝数据 | 能力中心搜索摘录写明特定开发者主体准入，用户粉丝数据文档涉及画像 [D7]、[D8] | **画像接口不等于粉丝总量时间序列**；不能据此宣称已解决粉丝趋势。个体工商户适用性、总量及历史序列接口仍待核实 |
| 小红书电商开放平台 | 检索到商品、订单、库存、物流等经营文档 [X1] | 此类文档不能证明能读取普通创作者的笔记表现 |
| 小红书 SNS 登录平台 | 检索到 OAuth / 用户基础信息参考 [X2] | 支持登录不等于提供笔记指标、粉丝趋势或评论权限 |
| 小红书商业开放平台 MAPI / 蒲公英 | 检索到品牌、代理商、服务商与商业合作场景文档，包含部分笔记 / 评论相关服务 [X3]、[X4] | 不能把合作订单场景的数据能力当作任意个人全部作品的通用 API；具体身份、授权和范围仍需逐接口核实 |
| 小红书创作者中心 | 本轮未找到能证实“普通个人创作者自助申请并读取全部所需数据”的正式 API 文档；网页读取与导出有开源实践 [R1]、[R2] | 当前无已验证的官方 API 主路径。**未找到不等于不存在**；第三方脚本存在也不能证明平台没有 API |

**适用结论**：首版不能依赖所有使用者都有开发者主体或审核通过的应用。保留正式 API 的位置，但先准备在授权范围内验证浏览器路线；不要为此强迫使用者注册营业主体，也不建议“挂靠”来规避准入。发现合适的官方能力后可替换某个平台 / 字段的数据入口，不改查询契约。

## 4. 开源候选：复用到哪里为止

本节区分“读过源码 / 许可”和“运行验证”。所有候选均**未运行**；检查范围不构成完整安全或依赖审计。快照为本轮通过 GitHub API 读到的 commit。

| 候选 / 快照 | 实际检查范围 | 复用判断 |
| --- | --- | --- |
| [xhs-analytics][R1] `b201cf0` | MIT `LICENSE`、依赖、`api.py` / `auth.py` / `config.py` 关键段 | 首选小红书采集候选。已看到页面响应读取与笔记 / 账号 / 粉丝方法；需改状态目录、输出与错误契约 |
| [xhs-trail][R2] `b07c184` | MIT `LICENSE`、后端 / 前端 manifest、`models.py`、README | 选择性复用 UI、导入和分析思路；不是直接兼容的 Hub 数据核心 |
| [douyin-creator-mcp][R3] `e5d59bd` | AGPL `LICENSE`、manifest、extractors / session 关键段 | 说明专用浏览器、采集 / 查询分离这条路线已有实践；**当前 MIT 路线不复制其实现** |
| [data-scientist-community][R4] `d0631c1` | AGPL `LICENSE`、架构、依赖、目录与 README | 完整多平台产品参考，但有 Python + JS 采集、可选桌面壳 / 飞书及 macOS 运行假设；不整体引入 |
| [douyin-creator-cockpit][R5] `e9b365f` | MIT `LICENSE`、README、目录 | 正式导出 → SQLite 的参考；README 明确依赖 macOS Chrome + AppleScript，不能宣称可直接用于 Windows |
| [3441293738/creatorhub][R6] `d54012e` | README、元数据、未截断的完整文件树 | 已有同名多平台工作台，含发布等不同范围；本轮未找到许可文件、GitHub license 为 null，不作为可复制分发的底座 |
| [wenyg/douyin-creator-tools][R7] `e35dbe2` | README、元数据、未截断的完整文件树 | 重作品 / 评论与回复，不是完整分析层；未找到许可文件，不直接复用 |
| [MediaCrawler][R8] | 当前上游 `LICENSE` | 非商业学习许可证，不能作为 MIT 产品的默认复用依赖；本机曾经可用不等于有再分发权 |

### 两个会影响实现的源码发现

- **`xhs-trail` 的 `Snapshot`**：`snapshot_date` 是日期；多项指标声明 `default=0`；`Note` 的原生 ID 是 `xhs_note_id`。[源码][R2-model] 这些适合它自己的输入假设，但不满足本 Hub 的“缺失不等于 0、每次观测保留时间、多平台身份”契约。因此优先借 UI / 导入逻辑，不把旧表直接包成统一数据库。
- **`xhs-analytics` 的 `get_user_notes` / 监听逻辑**：可见默认条数上限，部分失败路径返回已收集列表，通用监听还有捕获异常后跳过的行为。[源码][R1-api] 直接把返回列表当成完整同步会丢失覆盖信息。包装 / 修改时必须显式返回 `complete / partial / failed`、实际范围与错误，先用夹具验证再接真人账号。

此处不宣称候选的运行功能有缺陷；指出的是**直接复用时与本规格不匹配的假设**。MIT 也要求保留适用版权 / 许可声明；public 无许可不等于可自由分发，GitHub 官方有明确说明 [L1]。

## 5. 推荐架构与 module 的职责

```text
                  用户本人完成登录 / 验证
                           |
        抖音 adapter       |       小红书 adapter
        API / browser      |       browser / export
                  \        |        /
                   Collection module
              有界采集、profile 锁、覆盖与错误
                           |
                   校验并写入 SQLite
              内容 / 账号 / 关联 / 快照 / sync_run
                           |
                 Query & Analysis module
             新鲜度、缺失、趋势、增量、并排比较
                    /      |      \
              Local Web   CLI     MCP stdio
```

### 5.1 两个值得建立的 seam

- **平台 seam**：两平台真实存在差异，adapter 向 Collection module 返回同一批观测结果。Interface 只表达“读哪些账号 / 内容、时间范围、上限及结果”，隐藏 URL、页面、登录与分页细节。平台字段覆盖不足显式返回，不让调用方了解整个浏览器流程。
- **消费者 seam**：Web、CLI、MCP 都使用 Query & Analysis module。计算只在一处实现；三种入口是薄 adapter，不各写一套“7 天增量”。

不再额外搭一个通用连接器平台。先写两个真实 adapter，允许少量必要差异；没有第三种真实需求前不设计插件安装协议。

### 5.2 数据不变量

- 平台作品彼此独立；跨平台关联用用户确认的 `content_group`，可以解除，不按标题静默合并。
- 账号 / 内容保留稳定原生 ID；来源可能返回应用级或加密 ID，须保留 `id_namespace`，不能猜测与网页 ID 相同。
- `observed_at` / `collected_at`、平台统计时点 / 区间、内容发布时间各有用途，不能只留一个“日期”。
- 指标保留数值或 `null`、原字段、单位、时间口径、来源与缺失原因；DOM 的“1.2万”也要保留显示精度，不能暗示精确到个位。
- 同一次运行重试幂等，新一次观察追加；一个平台失败不删除另一个平台或以前的快照。分页未完成不能声明“全部作品”。
- 粉丝曲线可从真实总量观测积累；相邻观测差是净变化，不冒充平台新增 / 流失明细。
- 24h / 7d 只用真实窗口或附近真实观测，返回实际时间偏移；应用没运行时没有自动观测，不能事后伪造历史。
- 对比优先并排显示平台数据和定义，不把抖音播放与小红书曝光混成统一总量或统一排名。

这些是数据契约，不要求首版为每种概念建立一层抽象或一张表。SQLite 的具体表结构在真实样本后确定。

### 5.3 同步与浏览器生命周期

- 专用 profile 位于用户状态目录，不在源码仓库；一个账号同时只有一个登录 / 同步操作，其他调用返回 busy。
- 优先 `launchPersistentContext` 管理专用浏览器；Playwright 文档明确同一 user data directory 不能被多个实例同时使用，且不支持自动化默认 Chrome profile [B3]。Chrome 136 起对默认目录的远程调试有限制 [B5]。
- CDP 仅作实际需要时的备选，不默认开放端口或接管日常浏览器。Playwright 也注明 CDP 连接保真度低于原生连接 [B3]。
- 一个有上限的串行同步执行器足够；浏览器工作不阻塞查询事件循环。若需隔离超时 / 崩溃，可用同应用管理的子进程，不引入队列服务器。
- 运行状态至少区分 `running / success / partial / failed / user_action_required`，记录进度、错误和上次成功；重启后将未完成运行标成中断，不能永久假装运行中。
- Web 与多个 CLI / MCP 进程必须共享 profile 排他规则，不能只依赖单个进程内的锁。
- 定时采集默认关闭。启用后只说明“应用运行时自动同步”；无常驻运行不能承诺全天数据覆盖。

### 5.4 Agent 接口

建议首版同时保留机器可读 CLI 和小型 MCP 查询入口，调用同一个 Python query module，不要求 Agent 理解数据库或操纵浏览器。

- 能力组保持少量：状态 / 覆盖，作品查询，作品表现 / 趋势，账号粉丝趋势，跨平台关联比较。
- 返回可验证 JSON：`schema_version`、数据、来源、观测时间、缺失原因、覆盖 / 警告、分页；MCP 使用 `structuredContent` 与 output schema，并兼顾客户端文本 JSON 读取 [A1]。
- 默认只查询已有快照。Agent 主动 `sync` 是单独的联网 / 本地写操作，明确启用才暴露，参数限于已配置账号和范围。
- `readOnlyHint` 是行为提示，不是权限系统；在实际注册工具与执行路径上隔离操作 [A2]。
- 不暴露任意 SQL、任意 URL 抓取、通用 browser tools 或发布 / 回复；评论和标题按不可信数据处理，不当作 Agent 指令。
- 不内置聊天 Agent，不要求模型 Key。数据发给用户选择的外部 Agent 后会进入该 Agent 的数据边界，应明确告知；“本地存储”不等于“接云端模型也不外发”。

### 5.5 技术组合与发行

建议 **Python + FastAPI + SQLite + Playwright，React / TypeScript 静态前端**，是候选组合而非已获依赖安装授权。

- Python 是本轮 MIT 采集和看板候选的共同语言，减少跨运行时包装；CLI 可先用标准库，SQLite 优先最小持久层，不为小功能增加框架。
- FastAPI 复用候选现有生态，提供类型校验 / HTTP 入口，避免自研本地 Web 框架；能够服务构建好的前端资源 [W1]。
- React / TypeScript 选择来自已检查的 `xhs-trail` 前端 manifest，不代表必须复制其全部页面或依赖。只有表格、详情、曲线、关联和状态这几类首版交互，不先搭大型 BI。
- 前端在发行前构建，由本地 Python 应用服务；使用者不需要另起 Node 服务。开发者仍需要前端构建工具；具体安装 / 打包路径必须实测后再宣称一键可用。
- 首版不以 Electron / Tauri 包装获得“桌面感”，也不为纯本地页面增加 SSR。若实测安装摩擦高，再比较桌面发行方式。
- HTTP 默认 loopback，校验 Host / Origin，保护登录、同步及本地关联修改入口；不把 CORS 或 localhost 本身当作授权机制。

## 6. GitHub public：真正值得展示的部分

已经存在多平台工具和同名 `CreatorHub`，不要以“第一个多平台面板”作定位，也不要以未经测试的全平台支持吸引使用者。

建议定位：**为创作者与 AI Agent 提供可信、可追溯的本地内容表现数据**。这是产品定位建议，不是市场需求或传播效果已经得到验证。

首版公开包应包含：

1. 清晰的中英文简介、真实能力矩阵、Windows 安装 / 登录 / 故障恢复说明。
2. 同一套看板的合成数据 demo，无需账号、模型 Key 或登录；明显标注示例，不冒充真人指标。
3. 可复现的 parser / 数据契约夹具测试，以及一段 Agent 查询示例；不要求真人账号才能开始贡献。
4. MIT 与第三方声明；合成 / 经审核脱敏的截图和夹具，不放 cookie、profile、账号数据、原始网络日志、私人工作区引用。
5. 用新仓库发布，不改变当前私人工作区可见性；“Creator Hub”继续作内部暂名，正式发布前另选有辨识度的名字。

静态在线 demo 可以以后发布，但本轮未创建 Pages、CI、release 或仓库。文档写出交付要求不等于获准执行外部发布。

## 7. 实施顺序与停止条件

这是后续实现建议，不是本轮已执行计划：

1. **小红书一篇真实内容**：建议先用 MIT 候选验证，授权登录、稳定 ID、至少 3 个可见指标、字段口径与快照，人工核对。失败先解决访问 / 解析，不先做漂亮看板掩盖问题。
2. **抖音同样闭环**：验证官方入口适用性或浏览器导出 / 页面读取。MIT 路线下不复制 AGPL 实现；允许比小红书多一些独立适配工作。
3. **两平台持久查询**：重复同步、缺失 / 0、分页不完整、登录失效、profile 冲突、实际观测增量均可测；再让 Web / CLI / MCP 共用查询。
4. **首版产品验收**：作品与账号趋势、跨平台手动关联、状态面板、Agent 查询、无账号 demo。以上全部完成才算 v0.1，不能把双平台 / UI 重新降为远期。

评论在核心能力通过后再试；不因此拖延首版。定时同步、自动写回下游内容台账、远程部署、其他平台和平台写操作另设范围。

尚需在对应实施节点确认：

- 本人是否已有合规开发者应用及可用权限；本轮未获取这些个人事实，不假定已具备。
- 浏览器访问风险接受、账号授权与具体依赖；最终名称 / 仓库归属 / 外部发布。
- 是否允许 Agent 主动同步；同步频率、采样容差、数据保留和历史导入规则。

**复查触发**：MIT 候选的适配成本高于自写小 adapter、专用浏览器无法完成真实登录 / 数据访问、需要远程常开或多用户、发行体验不达标时，重比整体架构。没有这些证据，不加插件、桌面壳或分布式设施。

## 8. 验证记录

- 已读用户规格与作者私有内容台账的 CSV → JSON 脚本；它是消费者，不是采集器，本轮未修改。
- 已按上表抽查仓库源码 / manifests / LICENSE；两处“未找到许可证”的文件树响应均 `truncated=false`。
- 已查 Playwright、Chrome、FastAPI、MCP 官方资料；平台 API 的搜索摘录单独标注，未升级为账号权限事实。
- 已将本轮用户决策同步回规格；未执行应用测试，因为本轮没有实现或安装应用。
- 没有账号实测、长期稳定性测量、完整依赖 / 许可审计、市场验证或 star 增长证据。

## 来源

### 平台官方文档线索（本轮主要为官方页搜索摘录）

[D1]: https://developer.open-douyin.com/docs/resource/zh-CN/developer/join/issues
[D2]: https://developer.open-douyin.com/m/docs/resource/zh-CN/dop/develop/openapi/video-management/douyin
[D3]: https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/video-management/douyin/search-video/video-data
[D4]: https://developer.open-douyin.com/capacity-center-page/capacity-detail/7180522194714230845
[D5]: https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/video-management/video-data/get-comment-data
[D6]: https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/interaction-management/comment-management-user/comment-list
[D7]: https://partner.open-douyin.com/capacity-center-page/capacity-detail/7180550425647513661
[D8]: https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/account-management/fans-portrait-data/
[X1]: https://open.xiaohongshu.com/document/developer/file/58
[X2]: https://openaccount.xiaohongshu.com/docs/api-reference
[X3]: https://ad-market.xiaohongshu.com/docs-center?bizType=943&articleId=3169
[X4]: https://pgy.xiaohongshu.com/help/detail?id=22aa451e5f92647735efb60001b704d2&userType=6

### 实际读取的开源与协议来源

[R1]: https://github.com/SingularGuyLeBorn/xhs-analytics/tree/b201cf02403c5785a0c2c087829c71d94acc0f9c
[R1-api]: https://github.com/SingularGuyLeBorn/xhs-analytics/blob/b201cf02403c5785a0c2c087829c71d94acc0f9c/xhs_analytics/api.py
[R2]: https://github.com/DeanThompson/xhs-trail/tree/b07c18481dbef270f94c73a0bd55bef654e7d708
[R2-model]: https://github.com/DeanThompson/xhs-trail/blob/b07c18481dbef270f94c73a0bd55bef654e7d708/src/xhs_trail/models.py
[R3]: https://github.com/caidabai123/douyin-creator-mcp/tree/e5d59bd857f34cc9f698f9d86bda9d225fcae990
[R4]: https://github.com/Xavier-168/data-scientist-community/tree/d0631c1d845e0cb6ec21b498d77fab9e7b024e73
[R5]: https://github.com/johenking/douyin-creator-cockpit/tree/e9b365fba1a16dc5a337ea925f7a3d8eb8734274
[R6]: https://github.com/3441293738/creatorhub/tree/d54012e0bb2aa6e09474a04a7f1f1fc54a8a291a
[R7]: https://github.com/wenyg/douyin-creator-tools/tree/e35dbe27548cff292cc2d709417467a3bd464ed1
[R8]: https://github.com/NanmiCoder/MediaCrawler/blob/main/LICENSE
[B1]: https://playwright.dev/docs/network
[B2]: https://playwright.dev/docs/api/class-download
[B3]: https://playwright.dev/docs/api/class-browsertype
[B4]: https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging
[B5]: https://developer.chrome.com/blog/remote-debugging-port
[A1]: https://modelcontextprotocol.io/specification/2025-11-25/server/tools
[A2]: https://github.com/modelcontextprotocol/typescript-sdk/blob/main/docs/servers/tools.md
[W1]: https://fastapi.tiangolo.com/tutorial/static-files/
[L1]: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository
