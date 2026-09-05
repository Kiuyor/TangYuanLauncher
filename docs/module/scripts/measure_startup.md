# scripts/measure_startup.py

> 最后核对: 2026-09-05 · 共 134 行

## 一句话职责

精确测量打包版 RevIniEditor.exe 的启动耗时：进程创建 → flet 引擎窗口可见。

## 公开接口

`python scripts/measure_startup.py [exe路径] [工作目录]`（默认指向
build/nuitka/main.dist）。

## 关键实现决策

- **只认"启动后新出现"的 flet.exe 进程窗口**——排除已运行实例/残留进程干扰。
- 计时口径三级：t0=进程创建调用 / 新引擎进程出现 / 引擎窗口 `IsWindowVisible`
  翻转（=UI 就绪）。
- ctypes 全部 API **显式声明 restype/argtypes**：64 位 Windows 句柄是 64 位指针，
  默认 restype=c_int 会截断 → API 静默失败/误关句柄（deep-review 双 agent M1）。

## 坑与禁忌

- 首次运行/新目录时杀软逐文件扫描 exe+引擎（约 150MB），单次结果波动大——**重复
  多次取 min/中位数**再下结论。
- EnumProcesses 失败要报错返回空列表，不能静默跑满 30s 报"未见窗口"。

## 依赖与被依赖

- 依赖：纯 ctypes（无第三方）。
- 被依赖：打包链性能验收（packaging/README_分发版.md 记录口径）。

## 关联文档

- packaging/README_分发版.md
