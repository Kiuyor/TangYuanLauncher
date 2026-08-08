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
    ("startgame.bat",
     b"timeout /t 10", b"timeout /t 2 ",
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


def apply_patch(game_dir: str, rel: str, old: bytes, new: bytes, done_marker: bytes) -> bool:
    """就地字节级替换; 幂等(已含 done_marker 跳过); 改前备份 .bak_<ts>。返回是否改动。"""
    p = os.path.join(game_dir, rel)
    if not os.path.isfile(p):
        print(f"  [skip] {rel}: 不存在")
        return False
    with open(p, "rb") as f:
        data = f.read()
    if done_marker in data:
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
    """整文件替换: 原版 -> 增强版; 幂等(目标 md5 已匹配跳过); 改前备份 .bak_<ts>。返回是否改动。"""
    p = os.path.join(game_dir, rel)
    if not os.path.isfile(p):
        print(f"  [skip] {rel}: 不存在")
        return False
    with open(p, "rb") as f:
        cur = f.read()
    if hashlib.md5(cur).hexdigest() == expect_md5:
        print(f"  [skip] {rel}: 已是目标版本")
        return False
    if not os.path.isfile(src):
        print(f"  [skip] {rel}: 源文件缺失 {src}")
        return False
    with open(src, "rb") as f:
        new = f.read()
    bak = p + ".bak_" + time.strftime("%Y%m%d%H%M%S")
    with open(bak, "wb") as f:
        f.write(cur)
    with open(p, "wb") as f:
        f.write(new)
    print(f"  [replaced] {rel}: {len(cur)}B -> {len(new)}B (备份 {os.path.basename(bak)})")
    return True


def collect_files(game_dir: str):
    """返回 [(相对路径含反斜杠, 大小)] 按路径排序。"""
    out = []
    for root, dirs, files in os.walk(game_dir):
        dirs.sort()
        for fn in sorted(files):
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


def compress_chunk(game_dir: str, out_dir: str, idx: int, items) -> None:
    name = f"game.part{idx:02d}.7z"
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
    os.replace(tmp, os.path.join(out_dir, name))
    sz = os.path.getsize(os.path.join(out_dir, name))
    print(f"  [{name}] OK {sz/1024/1024:.1f} MB", flush=True)


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
    print("== 3/3 分块压缩")
    for i, items in enumerate(chunks):
        compress_chunk(game_dir, out_dir, i, items)
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
