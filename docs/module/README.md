# 模块文档索引 (docs/module/)

每个 Python 模块一篇文档，目录结构镜像仓库。单篇六节模板：一句话职责 / 公开接口 /
关键实现决策 / 坑与禁忌 / 依赖与被依赖 / 关联文档。侧重"代码直读不出来的为什么"，
API 只列签名不抄实现。**维护铁律见仓库根 AGENTS.md：模块接口/行为/坑位变更，当轮
同步对应文档并更新文头「最后核对」日期。**

> 最后核对: 2026-09-05

## 模块地图

| 模块 | 一句话职责 |
|---|---|
| [main.py](main.md) | 进程入口：Nuitka 打包模式引擎路径 + 隐藏启动防白窗 |
| [app/locator](app/locator.md) | CS:GO 目录 / rev.ini / cfg 目录自动定位 |
| [app/settings](app/settings.md) | settings.json 持久化 (%APPDATA%\RevIniEditor) |
| [app/avatar](app/avatar.md) | 头像数据层：校验/裁剪/双文件写盘/恢复默认 |
| [app/fields](app/fields.md) | rev.ini 字段与分组定义 (UI 表现层 schema) |
| [app/ini_model](app/ini_model.md) | rev.ini 解析/序列化 (保留注释/行尾/编码) |
| [app/cfg_fields](app/cfg_fields.md) | CFG 页字段定义 + s0up 预设解析/写回引擎 |
| [app/tools](app/tools.md) | 修复工具元数据/执行 + 内置资源安装 (newloader/皮肤库) |
| [flet_app/main](flet_app/main.md) | 全部视图装配与业务逻辑 (3042 行, 按视图域分节) |
| [flet_app/theme](flet_app/theme.md) | 设计令牌唯一来源 + 深浅换装 set_scheme |
| [flet_app/components/ui](flet_app/components/ui.md) | 唯一组件库 (rules §1 禁页面内联) |
| [scripts/verify_tools](scripts/verify_tools.md) | 回归验证门 (工具链闭环 + UI 构造冒烟 + ruff) |
| [scripts/v231_capture](scripts/v231_capture.md) | 视觉验收截图自动化 (定位/点击/置顶截图) |
| [scripts/measure_startup](scripts/measure_startup.md) | 打包版启动耗时测量 (进程→窗口可见) |
| [packaging/prepare_chunks](packaging/prepare_chunks.md) | 游戏目录补丁 + 分块压缩 + chunks.iss 契约 |
| [packaging/make_icon](packaging/make_icon.md) | 应用图标抠图生成 (一次性工具) |

## 依赖图

```
main.py (入口)
└─ flet_app/main.py ──────────── 全部视图/业务装配
   ├─ flet_app/components/ui.py ─ 唯一组件库
   ├─ flet_app/theme.py ──────── 设计令牌 (消费铁律: theme.COL_X 动态访问)
   ├─ app/tools.py ───────────── assets/ 内置资源 (newloader/items_730)
   ├─ app/locator.py ─────────── 目录定位
   ├─ app/settings.py ────────── settings.json (被 locator 反向引用)
   ├─ app/ini_model.py ───────── rev.ini 模型
   ├─ app/fields.py ──────────── 字段 schema
   ├─ app/cfg_fields.py ──────── CFG 字段+写回引擎
   └─ app/avatar.py ──────────── 头像数据层 (PIL)

跨层引用 (运行时 ← 工具链):
- scripts/verify_tools.py → app.tools / flet_app.main (导入冒烟)
- packaging/prepare_chunks.py → app.cfg_fields.S0UP_FILES (文件清单单一事实源)
  → 产出 build/chunks.iss → packaging/installer.iss #include
```
