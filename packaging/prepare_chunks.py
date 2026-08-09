"""打包时游戏预处理: 补丁 + 分块压缩 + 生成 chunks.iss

用法: python prepare_chunks.py <game_dir> <out_dir>
  game_dir = D:\\re-la\\game (将被就地打补丁: startgame.bat 提速 + rev.ini 中文, 幂等+备份)
  out_dir  = build\\chunks (输出 game.partNN.7z + 父目录生成 chunks.iss 契约)

契约(子 agent B 的 installer.iss 依赖):
  - 分块命名: game.partNN.7z (NN = 00 起两位十进制)
  - 分块内路径: 相对 game 根目录, 解压到 {app}\\game 即还原
  - chunks.iss 内容: #define ChunkCount N + [Files] dontcopy 条目
"""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
import time

SEVENZ = r"D:\7-Zip\7z.exe"
TARGET_CHUNK_MB = 1200
CHUNK_BYTES = TARGET_CHUNK_MB * 1024 * 1024
# 扩展皮肤库源 (revini-editor 仓库 assets/; 已提交 git)
EXT_ITEMS_BIN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "assets", "items_730.bin")

PATCHES = [
    # (相对路径, 旧字节, 新字节, 幂等判定字节)
    # 注意: 新字节末尾不带空格 — 原实现 `b"timeout /t 2 "` 尾随空格会让
    # `timeout /t 10 /nobreak` 变成 `timeout /t 2  /nobreak` 双空格 (deep-review 6轮 Low-7)
    ("startgame.bat",
     b"timeout /t 10", b"timeout /t 2",
     b"timeout /t 2"),
    ("rev.ini",
     b"Language = English", b"Language = schinese",
     b"Language = schinese"),
]

# 整文件替换补丁 (原版 -> 增强版; 幂等 = md5 已为目标)
FILE_REPLACEMENTS = [
    # (相对路径, 源文件, 目标 md5)
    ("platform\\items_730.bin", EXT_ITEMS_BIN,
     "0cfbf18a567f2ab1df95669102198096"),
]


def _marker_line_present(data: bytes, marker: bytes) -> bool:
    """幂等判定: marker 是否作为**完整 token**出现在行首(行首可选空白)。

    与 tools.py _speedup_startgame 的行首锚定同语义 (deep-review 8轮 F3):
    裸子串 `marker in data` 会把 b"timeout /t 2" 误匹配 b"timeout /t 20 /nobreak"
    (未提速变体) 或 banner/ECHO 文本里的同形字样, 导致假幂等跳过、发行包静默漏提速。
    行首锚定 + 词边界 (后随空白或行尾, 含 CRLF 的 \\r) 保证只认真正的目标行。
    """
    return re.search(rb"(?m)^[ \t]*" + re.escape(marker) + rb"(?=[ \t\r]|$)", data) is not None


def apply_patch(game_dir: str, rel: str, old: bytes, new: bytes, done_marker: bytes) -> bool:
    """就地字节级替换; 幂等(已含 done_marker 跳过); 改前备份 .bak_<ts>。返回是否改动。"""
    p = os.path.join(game_dir, rel)
    if not os.path.isfile(p):
        print(f"  [skip] {rel}: 不存在")
        return False
    with open(p, "rb") as f:
        data = f.read()
    if _marker_line_present(data, done_marker):
        print(f"  [skip] {rel}: 已是目标状态")
        return False
    if old not in data:
        print(f"  [skip] {rel}: 未找到目标字节 (旧={old!r})")
        return False
    bak = p + ".bak_" + time.strftime("%Y%m%d%H%M%S")
    with open(bak, "wb") as f:
        f.write(data)
    with open(p, "wb") as f:
        f.write(data.replace(old, new))
    print(f"  [patched] {rel}: {old!r} -> {new!r} (备份 {os.path.basename(bak)})")
    return True


def apply_file_replacement(game_dir: str, rel: str, src: str, expect_md5: str) -> bool:
    """整文件替换: 原版 -> 增强版; 幂等(目标 md5 已匹配跳过); 改前备份 .bak_<ts>。返回是否改动。

    expect_md5: FILE_REPLACEMENTS 声明的目标 md5。运行时对 src 实测并与常量断言一致
    (deep-review 6轮 Low-5): 常量是手工维护的, 若更新 assets 后忘改常量, 幂等判定会
    永不命中(每轮生成新 .bak 堆积)或误跳过 — 实测不一致直接报错, 强制同步常量。
    """
    if not os.path.isfile(src):
        print(f"  [skip] {rel}: 源文件缺失 {src}")
        return False
    with open(src, "rb") as f:
        new = f.read()
    src_md5 = hashlib.md5(new).hexdigest()
    if src_md5 != expect_md5:
        sys.exit(f"[FATAL] {rel}: 源文件 md5 与常量不一致 (src={src_md5} expect={expect_md5}). "
                 f"更新 assets 后请同步 FILE_REPLACEMENTS 常量 (deep-review 6轮 Low-5)")
    p = os.path.join(game_dir, rel)
    if not os.path.isfile(p):
        print(f"  [skip] {rel}: 不存在")
        return False
    with open(p, "rb") as f:
        cur = f.read()
    if hashlib.md5(cur).hexdigest() == expect_md5:
        print(f"  [skip] {rel}: 已是目标版本")
        return False
    bak = p + ".bak_" + time.strftime("%Y%m%d%H%M%S")
    with open(bak, "wb") as f:
        f.write(cur)
    with open(p, "wb") as f:
        f.write(new)
    print(f"  [replaced] {rel}: {len(cur)}B -> {len(new)}B (备份 {os.path.basename(bak)})")
    return True


def collect_files(game_dir: str):
    """返回 [(相对路径含反斜杠, 大小)] 按路径排序。

    排除补丁备份 .bak_<ts> (deep-review 6轮): _patch_file/_replace_file 生成的
    备份会残留目录, 不打进发行分块 (否则玩家安装后目录多出 2 个冗余备份,
    且每轮重跑 prepare_chunks 累积更多 .bak 污染分块)。
    """
    out = []
    for root, dirs, files in os.walk(game_dir):
        dirs.sort()
        for fn in sorted(files):
            if fn.endswith(".bak_") or ".bak_" in fn:
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, game_dir)
            out.append((rel.replace("/", "\\"), os.path.getsize(full)))
    return out


def chunk_files(files, target):
    """贪心按路径序分组, 每块累计 >= target。返回 [ [ (rel,size)... ] ]"""
    chunks, cur, cur_sz = [], [], 0
    for item in files:
        cur.append(item)
        cur_sz += item[1]
        if cur_sz >= target:
            chunks.append(cur)
            cur, cur_sz = [], 0
    if cur:
        chunks.append(cur)
    return chunks


def _chunk_fingerprint(game_dir: str, items) -> str:
    """块内文件指纹: (rel, size, mtime) 组合的 sha256。
    增量跳过判断 (deep-review 6轮 Low-6): 内容未变的块不重压。
    mtime 用整数纳秒 (st_mtime_ns), 避免秒级精度误判同秒修改。"""
    import hashlib as _h
    h = _h.sha256()
    for rel, sz in items:
        full = os.path.join(game_dir, rel)
        try:
            mt = os.stat(full).st_mtime_ns
        except OSError:
            mt = 0
        h.update(f"{rel}|{sz}|{mt}\n".encode())
    return h.hexdigest()


def _load_manifest(out_dir: str) -> dict:
    """读增量 manifest: {idx: fingerprint}。不存在/损坏返回空。"""
    p = os.path.join(out_dir, "manifest.json")
    try:
        import json
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {int(k): v for k, v in data.items()}
    except (OSError, ValueError, TypeError):
        pass
    return {}


def _save_manifest(out_dir: str, manifest: dict) -> None:
    """写增量 manifest (块指纹缓存, 供下次重跑跳过未变块)。"""
    import json
    p = os.path.join(out_dir, "manifest.json")
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
    os.replace(tmp, p)


def compress_chunk(game_dir: str, out_dir: str, idx: int, items,
                   manifest: dict) -> bool:
    """压缩单块; 指纹未变且产物存在时跳过 (增量缓存, deep-review 6轮 Low-6)。
    返回是否实际压缩 (False = 命中缓存跳过)。"""
    name = f"game.part{idx:02d}.7z"
    fp = _chunk_fingerprint(game_dir, items)
    out = os.path.join(out_dir, name)
    if manifest.get(idx) == fp and os.path.isfile(out) and os.path.getsize(out) > 0:
        print(f"  [{name}] 未变, 跳过 (增量缓存)", flush=True)
        return False
    tmp = os.path.join(out_dir, f"game.part{idx:02d}.tmp7z")  # 先写临时, 原子替换占位文件
    if os.path.exists(tmp):
        os.remove(tmp)
    list_file = os.path.join(out_dir, f"part{idx:02d}.list")
    with open(list_file, "w", encoding="utf-8") as f:
        f.writelines(rel + "\n" for rel, _ in items)
    cmd = [SEVENZ, "a", "-t7z", "-mx=9", "-m0=LZMA2", "-md=64m",
           "-mfb=273", "-ms=on", "-mmt=on", tmp, "@" + list_file]
    print(f"  [{name}] {len(items)} 文件 ...", flush=True)
    r = subprocess.run(cmd, cwd=game_dir, capture_output=True, check=False)
    if r.returncode != 0:
        sys.exit(f"7z 失败 ({name}): {r.stderr.decode('utf-8', 'replace')[-800:]}")
    os.replace(tmp, out)
    sz = os.path.getsize(out)
    print(f"  [{name}] OK {sz/1024/1024:.1f} MB", flush=True)
    return True


def main() -> None:
    game_dir = os.path.abspath(sys.argv[1])
    out_dir = os.path.abspath(sys.argv[2])
    os.makedirs(out_dir, exist_ok=True)
    print(f"== 1/3 游戏补丁: {game_dir}")
    for rel, old, new, marker in PATCHES:
        apply_patch(game_dir, rel, old, new, marker)
    for rel, src, md5 in FILE_REPLACEMENTS:
        apply_file_replacement(game_dir, rel, src, md5)
    print("== 2/3 收集文件清单")
    files = collect_files(game_dir)
    total = sum(s for _, s in files)
    print(f"  {len(files)} 文件, {total/1024/1024/1024:.2f} GB")
    if not files:
        sys.exit(f"[FATAL] 游戏目录无文件: {game_dir} (检查路径是否被 shell 转义)")
    chunks = chunk_files(files, CHUNK_BYTES)
    print(f"  分为 {len(chunks)} 块 (目标 {TARGET_CHUNK_MB}MB/块)")
    # 增量缓存 (deep-review 6轮 Low-6): 指纹未变的块跳过重压
    manifest = _load_manifest(out_dir)
    print("== 3/3 分块压缩 (增量: 未变块跳过)")
    for i, items in enumerate(chunks):
        compress_chunk(game_dir, out_dir, i, items, manifest)
        manifest[i] = _chunk_fingerprint(game_dir, items)
    _save_manifest(out_dir, manifest)
    iss = os.path.join(os.path.dirname(out_dir), "chunks.iss")
    with open(iss, "w", encoding="utf-8") as f:
        f.write("; 由 prepare_chunks.py 自动生成 - 请勿手改\n")
        f.write(f"#define ChunkCount {len(chunks)}\n\n")
        f.write("; 以下 Source 行嵌在 installer.iss 的 [Files] 段内(include), 不带 [Files] 头\n")
        f.write("; nocompression: 分块已是 7z 压缩数据, Inno 不再二次压缩(否则单线程 lzma2 压 5.7G 要 30-50 分钟)\n")
        for i in range(len(chunks)):
            f.write(f'Source: "..\\build\\chunks\\game.part{i:02d}.7z"; DestDir: "{{tmp}}"; Flags: dontcopy nocompression\n')
    print(f"== 完成: {len(chunks)} 块 -> {out_dir}")
    print(f"   契约: {iss}")


if __name__ == "__main__":
    main()
