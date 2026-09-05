# app/avatar.py

> 最后核对: 2026-09-05 · 共 198 行

## 一句话职责

修改头像功能的数据层：图片校验、1:1 裁剪、游戏双文件写盘、出厂默认恢复——纯函数
+ 文件操作，无 UI 依赖。

## 公开接口

- `validate_image(data) -> str | None` — 错误消息(中文)或 None=合法。
- `crop_to_bmp / crop_to_png / crop_to_preview(data, box)` — 64×64 BMP / 64×64 PNG
  / 256×256 PNG（box = 原图像素坐标 left/top/right/bottom）。
- `save_avatar(csgo_dir, data, box, preview_path=None) -> (ok, err)` — 备份→双文件
  写盘→可选清晰预览版。
- `restore_default_avatar(csgo_dir) -> (ok, err)` — 从 assets/ 出厂头像恢复。

## 关键实现决策

- **双文件数据契约**（2026-08-23 实测 platform/）：`avatar.dat` = 64×64 24 位 BMP，
  `avatar1.dat` = 64×64 PNG，游戏内两条渲染路径分别读——必须同写，否则半新半旧。
- **透明区域填黑**：24 位 BMP 无 alpha，透明像素会变垃圾色，先合成到纯黑底。
- **两套清晰度**：游戏头像固定 64×64；启动器主页 100px 展示读 256px 预览版（存
  用户数据目录不进游戏），预览写失败不阻断主流程（主页回退 64 版）。
- `validate_image` 先读文件头拦截超大尺寸再整张解码（20MB 可解出上亿像素位图）。
- `.bak` 只保留最近一个；全部写盘走 tmp + `os.replace` 原子写。

## 坑与禁忌

- 游戏运行中写头像：游戏不会覆盖，但**重启游戏才生效**（已实测）。
- box 必须是原图像素坐标，不是 UI 裁剪框屏幕坐标（换算在 flet_app 侧按 cover 缩放
  反推）。
- 出厂头像必须随包备份进 assets/（default_avatar.dat/.dat1），禁止依赖目标机残留
  （rules.md §4.6）。

## 依赖与被依赖

- 依赖：PIL、`assets/default_avatar*`。
- 被依赖：`flet_app/main`（修改头像页/启动器预览）。

## 关联文档

- docs/DESIGN.md（修改头像视图与裁剪映射）
- [flet_app/main](../flet_app/main.md)
