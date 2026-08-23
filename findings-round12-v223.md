# Deep Review Findings — 第 12 轮 (revini-editor v2.2.3)

> 审查时间: 2026-08-23 · Commit: c9ee532 (v2.2.3) · Repo: D:\re-la\revini-editor
> 本轮重点: v2.2.3 增量 — CFG 配置页 (app/cfg_fields.py + flet_app/main.py CFG 页) + s0up 预设默认集合植入 (packaging/prepare_chunks.py) + 全 UI 矩形化。
> 审查方法: 只读深审 + 纯函数探针 (import 模块直接断言) + rev.ini 字节级实证。
> 质量门: ruff 0 错误 + py_compile 通过 (健康)。

## Summary

| # | Severity | Impact | Title | File |
|---|---|---|---|---|
| 1 | MEDIUM | DATA_INTEGRITY | float 字段范围校验接受 `nan`/`NaN`, 可写入 `sensitivity nan` 破坏游戏配置 | app/cfg_fields.py:37-54 |
| 2 | MEDIUM | DATA_INTEGRITY | 准星透明度 scale 往返丢精度 (200→199), 保存时静默改写未修改字段 | app/cfg_fields.py:35,209-212 |
| 3 | MEDIUM | SUPPORT_BURDEN | CFG 页切页"丢弃"是假的: 确认丢弃后 cfg_dirty 未清、页面未重建, 修改残留 | flet_app/main.py:1327-1344 |
| 4 | LOW | DATA_INTEGRITY | `_cfg_add_exec` 把 rev.ini ProcName 行从 CRLF 改成 LF (混行尾, 已实证) | flet_app/main.py:1143-1158 |
| 5 | LOW | CODE_QUALITY | `_GROUP_HEAD_RE` 定义两次 (第 123 行死代码被第 167 行覆盖) | app/cfg_fields.py:123,167 |
| 6 | LOW | SUPPORT_BURDEN | 缺失命令永远追加到文件尾 (根因: `_GROUP_HEAD_RE` 非贪婪捕获只匹配 1 字符) | app/cfg_fields.py:170,242-250 |

## Findings

### Finding 1: float 字段范围校验接受 `nan`/`NaN`, 可写入破坏游戏配置

- **Severity**: MEDIUM
- **Impact category**: DATA_INTEGRITY
- **Location**: `app/cfg_fields.py:37-54` (`CfgField.validate`)
- **Trigger condition**: 用户在 CFG 页任一 float 字段 (灵敏度/音量/亮度等) 输入 `nan`/`NaN` 后点保存
- **Consequence**: 校验通过 → `apply_values` 把 `sensitivity nan` 写进 auto.cfg → CS:GO 的 float ConVar 解析成 NaN → 鼠标灵敏度/音量等异常, 玩家配置损坏

#### Root cause

`validate` 用 `float(raw)` 解析并靠范围比较拦截非法值:

```python
v = float(raw) if self.kind == "float" else int(raw)
...
if self.min_v is not None and v < self.min_v:
    return False, f"最小 {self.min_v}"
if self.max_v is not None and v > self.max_v:
    return False, f"最大 {self.max_v}"
return True, ""
```

`float("nan")` 返回 NaN 而不抛 ValueError; NaN 与任何数比较恒 False, 所以 `v < min_v` 与 `v > max_v` 都是 False → 校验通过。`inf`/`-inf` 因 `inf > max_v` 恒 True 被拦下, 但 **NaN 是漏网之鱼**。

#### Evidence

探针 (import app.cfg_fields 直接断言):
```
validate('nan')  -> ok=True err=''
validate('NaN')  -> ok=True err=''
validate('inf')  -> ok=False err='最大 10'
validate('2.0')  -> ok=True err=''
```

#### Suggested fix direction

`float`/`int` 解析成功后加 `math.isfinite(v)` 守卫 (NaN/±inf 均返回 False), 或改用严格数字正则预筛。

---

### Finding 2: 准星透明度 scale 往返丢精度, 保存时静默改写未修改字段

- **Severity**: MEDIUM
- **Impact category**: DATA_INTEGRITY
- **Location**: `app/cfg_fields.py:35` (scale=255/100) + `apply_values:209-212` (写回 round) + `flet_app/main.py:1105-1108` (回填 round)
- **Trigger condition**: 玩家手动改过 crosshair.cfg 的透明度 (非 255 的整数值), 之后在 CFG 页改**任意其他字段**并保存
- **Consequence**: 透明度字段没动, 但因"全量写回所有字段 + 显示值↔文件值 round 往返不精确", 透明度被静默改写 (200→199, 100→99)

#### Root cause

`_save_cfg` 把**所有 23 个字段**都放进 `updates` (非 dirty 字段也写), `apply_values` 对 scale 字段做 `round(显示值 * 2.55 + 1e-9)`。显示值 `round(文件值 / 2.55)` 有舍入, 写回时 `显示值 * 2.55` 不一定回到原文件值。

#### Evidence

探针 (alpha.scale = 2.55):
```
file=200 -> display=78 -> writeback=199  LOSS
file=100 -> display=39 -> writeback=99   LOSS
file=77  -> display=30 -> writeback=77   ok
file=255 -> display=100 -> writeback=255 ok
```

#### Suggested fix direction

①只写 dirty 字段 (而非全量), 未修改的 scale 字段不参与写回; ②或 scale 字段写回时保留原始文件值 (回填记录 `文件值↔显示值` 映射, 未改时原样写回文件值)。

---

### Finding 3: CFG 页切页"丢弃"是假的 — 确认丢弃后修改残留

- **Severity**: MEDIUM
- **Impact category**: SUPPORT_BURDEN
- **Location**: `flet_app/main.py:1327-1344` (`on_nav_change` 的 `_switch`)
- **Trigger condition**: 用户在 CFG 页改字段 → 点导航切到其他页 → 弹"切换将丢弃这些修改" → 点"丢弃并继续"
- **Consequence**: 修改**没有**被丢弃 (cfg_dirty 仍 True、cfg_vrs 仍保留修改、缓存页面仍显示修改值); 之后关闭窗口又弹一次"配置尚未保存"。用户以为丢了实际还在, 状态不一致。

#### Root cause

`on_nav_change` 离开 CFG 页时弹 `confirm_discard(_switch, ...)`, 文案承诺"丢弃这些修改", 但 `_switch` 只做了 `content_area.content = nav_content[nav_index]` 和 `save_btn.on_click` 切换, **没有清 `st["cfg_dirty"]`、没有重建 CFG 页**。对比 `on_back_to_launcher` 的 `_go` (main.py:1747-1750) 正确清理了: `st["cfg_dirty"] = False` + `nav_content[CFG_NAV_INDEX] = build_cfg_page()`。

#### Evidence

两处对照 (同一 dirty 语义, 实现不一致):
- `on_back_to_launcher._go` (1747-1750): `st["cfg_dirty"] = False` + 重建页面 ✓
- `on_nav_change._switch` (1333-1339): 只切 content, 无 dirty 清理, 无重建 ✗

#### Suggested fix direction

`_switch` 在离开 CFG 页且 cfg_dirty 时, 复用 `on_back_to_launcher._go` 的丢弃语义: 清 `st["cfg_dirty"] = False` + `nav_content[CFG_NAV_INDEX] = build_cfg_page()`。

---

### Finding 4: `_cfg_add_exec` 把 rev.ini ProcName 行从 CRLF 改成 LF (混行尾)

- **Severity**: LOW
- **Impact category**: DATA_INTEGRITY
- **Location**: `flet_app/main.py:1143-1158` (`_cfg_add_exec`)
- **Trigger condition**: 用户点 CFG 页"一键添加 +exec auto.cfg"
- **Consequence**: ProcName 行 + 紧随空行从 CRLF 变 LF, rev.ini 混行尾。CS:GO 读取一般容忍, 但不干净; 同库 `_procname_patch` 已正确处理 (显式保留 `\r`), 此函数未同步。

#### Root cause

```python
new_line = m.group(1) + m.group(2).rstrip() + " +exec auto.cfg\n"
```

`m.group(2)` 捕获含尾部 `\r`, `.rstrip()` 剥掉它, 结尾硬编码 `\n` (LF)。同库 `_procname_patch` 的 210-211 行有 `if line.endswith(b"\r"): new_line += b"\r"` 显式保留 CRLF — 平行实现未同步。

#### Evidence

字节级实证 rev.ini 当前状态:
```
line 1: 'ProcName = csgo.exe -steam ... +exec auto.cfg'  (lone LF)
line 2: ''  (lone LF)
CRLF=67 LF=69 loneLF=2
```
正是 `_cfg_add_exec` 跑过的痕迹 (该行已含 `+exec auto.cfg` 且是 lone LF)。

#### Suggested fix direction

`_cfg_add_exec` 复用 `_procname_patch` 的字节级写回 + `if line.endswith(b"\r"): new_line += b"\r"`, 或先检测文件主行尾 (`\r\n` in txt) 决定结尾。

---

### Finding 5: `_GROUP_HEAD_RE` 定义两次 (死代码)

- **Severity**: LOW
- **Impact category**: CODE_QUALITY
- **Location**: `app/cfg_fields.py:123,167`
- **Consequence**: 第 123 行的第一版正则 (带 7 个中文组名捕获) 从未被使用 — 第 167 行第二版 (通用 `[^═＝=\s]` 捕获) 覆盖了它。误导后续维护者。

#### Suggested fix direction

删除第 123 行死定义 (及其上方已废弃的 `_LINE_RE` 相关注释), 保留 167 行版本。

---

### Finding 6: 缺失命令永远追加到文件尾 (根因: `_GROUP_HEAD_RE` 非贪婪捕获)

- **Severity**: LOW
- **Impact category**: SUPPORT_BURDEN
- **Location**: `app/cfg_fields.py:170` (`_GROUP_HEAD_RE`) + `:242-250` (`apply_values` 缺失命令追加)
- **Trigger condition**: 玩家删除了 auto.cfg 中任一命令 (如 sensitivity), 在 CFG 页改其他字段保存
- **Consequence**: 缺失命令被追加到**文件尾**, 而非所属组的标题后。功能上命令仍执行 (ConVar 全局), 但组织错位; 且跨组同时缺失时全部堆在文件尾。

#### Root cause

`_GROUP_HEAD_RE = re.compile(r"//[═＝=].*\d\.\s*([^═＝=\s][^═＝=]*?)")` 的捕获组 `([^═＝=\s][^═＝=]*?)` 是**非贪婪** `*?`, 后面无约束 → 只捕获 1 个字符 (如 "鼠"), 于是 `"鼠标设置" in "鼠"` 恒 False, `_group_head_line` 的标题定位**永远匹配失败**, 恒返回 `len(lines)` (文件尾)。

> 注: 审查初稿把此归因于"`next(iter(remaining))` 用第一组名代理全部"——不准确。真实根因是正则非贪婪捕获, 导致无论单组还是跨组缺失, 都落文件尾。(修复过程中用真实 auto.cfg 标题实测发现。)

#### Suggested fix direction

正则捕获组改贪婪 `([^═＝=\s]+)`; 缺失命令按键所属组 (`_GROUP_OF`) 分组, 每组各自定位标题后追加。

---

## 修复记录 (2026-08-23)

6 项全修 + 修复过程中新增发现 1 处根因修正, 全部探针验证 PASS (ruff 0 错 + py_compile 通过):

1. **NaN 校验** — `validate` 加 `math.isfinite(v)` 守卫 (validate('nan'/'NaN'/'NAN'/'inf'/'-inf' 均拒绝)
2. **scale 往返精度** — scale 换算从 `apply_values` 移到 UI 层; 未修改的 scale 字段用文件原值写回 (200→200, 不再 200→199)
3. **切页假丢弃** — `_switch` 离开 CFG 页时清 `cfg_dirty` + 重建页面 (与 `on_back_to_launcher._go` 一致)
4. **CRLF 破坏** — `_cfg_add_exec` 改字节级操作 + `bytes([13])` 保留行尾 (实测 CRLF 文件无 lone LF, LF 文件保持 LF)
5. **死代码** — 删第 123 行 `_GROUP_HEAD_RE` 重复定义 (现仅 1 处)
6. **缺失命令追加** — 正则捕获改贪婪 `([^═＝=\s]+)` + 按键所属组分组追加 (真实 auto.cfg 实测: sensitivity→鼠标节, volume→声音节, 位置精确)

---

This review ran cold: no team memory, no production signal correlation, no Slack
context, no scheduled cadence, no PR creation, no dedup against existing issues.
