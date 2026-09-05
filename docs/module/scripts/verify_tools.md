# scripts/verify_tools.py

> 最后核对: 2026-09-05 · 共 241 行

## 一句话职责

回归验证门：修复工具闭环 + UI 构造冒烟 + ruff 全库零错误，退出码 0/1。

## 公开接口

`python scripts/verify_tools.py`（用 .venv 的解释器跑）。check(name, cond) 逐项打印
PASS/FAIL，结尾汇总。

## 覆盖清单

- `_install_loader`：不覆盖原件 Loader.exe/revLoader.exe、md5 幂等、同大小不同内容
  仍覆盖。
- `_update_items`：备份/覆盖/幂等/同大小不同内容四路径。
- `_speedup_startgame`：10s→2s、CRLF 保留、幂等、无 timeout 分支。
- `_backup_file`、`_clean_reg_leftover`（键不存在路径）、`run_tool`（成功/缺脚本/
  超时杀树）。
- 静态检查：启动优先 newloader、`_install_loader(d, None)` 自动就位、Popen 用
  loader_exe、工具页已删「安装优化 Loader」。
- **UI 构造冒烟（2026-09-05 counter_text 回归后新增）**：构造带 max_length 的
  `input_dark`，模拟超限输入断言手动截断——此类"构造期 TypeError"ruff/导入均不报，
  专堵 flet kwarg 兼容类回归。
- ruff 全库 0 错误（app/flet_app/main.py/scripts）。

## 坑与禁忌

- `_clean_reg_leftover` 的存在分支会动**真实注册表**（只测不存在的安全分支）；
  历史上跑测试曾顺带清掉真实的 pending 残留（属良性副作用但要知情）。
- 超时测试的 bat 用 `ping -n` 延迟不用 `timeout` 命令——git-bash PATH 里 GNU timeout
  会遮蔽 Windows timeout.exe。

## 依赖与被依赖

- 依赖：`app.tools`、`flet_app.main`（导入即冒烟）、`flet_app.components.ui`。
- 被依赖：开发流程（每轮修复后必跑）；不入运行时。

## 关联文档

- [app/tools](../app/tools.md)
- AGENTS.md（跑法与时机）
