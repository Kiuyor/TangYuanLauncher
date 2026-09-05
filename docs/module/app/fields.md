# app/fields.py

> 最后核对: 2026-09-05 · 共 244 行

## 一句话职责

rev.ini 字段与分组定义（UI 表现层 schema）：界面上展示哪些配置项、什么控件类型、
范围与默认值。

## 公开接口

- `FieldDef` dataclass — 字段 schema 唯一来源；`bool/text/int/combo/textarea/rank`
  类构造器输出 dict。
- `bool_field/text_field/int_field/combo_field/textarea_field/rank_field` — 兼容层
  薄封装，输出与 FieldDef 完全一致（旧调用方无需改动）。
- `FIELD_GROUPS` — 编辑页导航分组（常用设置/加载器 + `type=tools`/`type=cfg` 两个
  特殊分组，由 flet_app/main 特殊渲染）。
- `RANK_DISPLAY`（段位官方名+俗称，index+1=存储值）、`LANG_NAMES`（语言 display_map）。
- `rank_name_to_level / rank_level_to_name`。

## 关键实现决策

- **与 ini_model 分离**：模型只管解析/序列化，本模块只描述"界面要展示什么"——两者
  改动互不牵连。
- 构造器内 assert 校验默认值/范围类型（如 bool 默认必须 bool、lo<=hi），错误在导入
  期即暴露而不是运行期。
- `to_dict` 输出键必须与旧构造器逐键一致（`display_map` 为 None 时不输出该键，M4）。

## 坑与禁忌

- 新增字段选对类型：`int` 会做范围 UI 与校验，`text` 的 maxlen 决定输入截断上限
  （input_dark 手动截断的上限来源）。
- `FIELD_GROUPS` 顺序 = 编辑页导航顺序；插入分组记得 icon_key 在 flet_app/main 的
  icon_map 里有映射。

## 依赖与被依赖

- 依赖：无（纯 dataclass）。
- 被依赖：`flet_app/main`（build_page/build_field_row 按 FIELD_GROUPS 渲染）。

## 关联文档

- [app/ini_model](ini_model.md)（存储层）
- [flet_app/components/ui](../flet_app/components/ui.md)（field 类型 → 控件映射）
