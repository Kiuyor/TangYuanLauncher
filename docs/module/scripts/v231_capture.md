# scripts/v231_capture.py

> 最后核对: 2026-09-05 · 共 111 行

## 一句话职责

视觉验收截图自动化：把应用窗口挪到未遮挡区、按相对坐标真实点击导航、置顶后逐页
截图。

## 公开接口

`python scripts/v231_capture.py <outdir> <theme>` — 产出 `{theme}-1-home.png` …
`-6-avatar.png` 六张（主页/编辑页三分组/头像页）。

## 关键实现决策

- **相对窗口矩形计算点击坐标**（find_window 按 "Tangyuan" 标题 EnumWindows），窗口
  先挪到 (1150, 80) 避开 ZCode 遮挡区。
- **置顶截图**：`SetWindowPos(TOPMOST)` + PIL ImageGrab——窗口会被 ZCode 持续压住，
  不置顶截到的是遮挡层。
- **真实鼠标事件**（ctypes mouse_event + 归一化坐标移动）：CUA 坐标点击因 ZCode
  窗口持续重绘而帧失效，这是实测得出的替代通道。

## 坑与禁忌

- 点击后要 sleep 等窗口展开/懒加载（脚本内 2.2~3.0s 不等）。
- 指针先驻停屏幕左下角——否则主页截图会出现头像悬停 tooltip。
- 产物进 `shots/`（gitignore），不入库。

## 依赖与被依赖

- 依赖：PIL、pywin32 无（纯 ctypes）；目标：运行中的 Tangyuan 窗口。
- 被依赖：tangyuan-ui skill 视觉验收流程（§四）。

## 关联文档

- docs/tokens.md §7（动效验收语境）
- AGENTS.md（截图基建说明）
