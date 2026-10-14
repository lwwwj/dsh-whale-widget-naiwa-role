# -*- coding: utf-8 -*-
"""把一段音频装成 dsh-whale-widget 的自定义音频片段（DSH_HOME/whale-audio/<id>.wav + audio.json）。

用法:
  python _install_audio.py <音频文件> [片段id] [显示名]
  python _install_audio.py                       # 不带参数：把 data/whale-audio 里已有的片段补齐进索引

客户端里写死用到的两个 id：
  nailong_laugh  点一下挂件时播的「奶蛙笑声」
  andi           点第二下时播的「安迪」
换音频文件时保持 id 不变即可。

宿主路由 /dsh-whale/audio-fragment.wav?id=<id> 直接回传该文件字节，客户端用 Web Audio
decodeAudioData 按容器内容解码，所以 mp3 字节放在 .wav 文件名下也能播。
"""
import argparse
import json
import os
import shutil
import sys
import time

DEFAULTS = [("nailong_laugh", "奶蛙笑声"), ("andi", "安迪")]


def dsh_home():
    return os.environ.get("DSH_HOME") or os.path.join(os.path.expanduser("~"), ".dsh")


def load_index(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            idx = json.load(fh)
        if isinstance(idx, dict) and isinstance(idx.get("groups"), list) and isinstance(idx.get("fragments"), list):
            return idx
    except Exception as exc:
        print("no usable audio index (%s) -> fresh" % exc)
    return {"version": 1, "groups": [], "fragments": []}


def upsert(idx, frag, name):
    idx["fragments"] = [x for x in idx["fragments"] if not (isinstance(x, dict) and x.get("id") == frag)]
    idx["fragments"].append({"id": frag, "name": name, "createdAt": int(time.time() * 1000)})


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("audio", nargs="?", help="要安装的音频文件；省略则只补索引里缺的默认片段")
    ap.add_argument("frag", nargs="?", default="nailong_laugh", help="片段 id（默认 nailong_laugh）")
    ap.add_argument("name", nargs="?", default="奶蛙笑声", help="显示名")
    ap.add_argument("--dir", dest="dst", default=os.path.join(dsh_home(), "whale-audio"))
    a = ap.parse_args()

    os.makedirs(a.dst, exist_ok=True)
    idx_path = os.path.join(a.dst, "audio.json")
    idx = load_index(idx_path)

    if a.audio:
        src = a.audio
        if not os.path.exists(src):
            raise SystemExit("missing source: " + src)
        dst = os.path.join(a.dst, a.frag + ".wav")
        if os.path.abspath(src) != os.path.abspath(dst):
            shutil.copyfile(src, dst)
        with open(dst, "rb") as fh:
            head = fh.read(4)
        print("installed %s -> %s (%d bytes, head=%r)" % (src, dst, os.path.getsize(dst), head))
        upsert(idx, a.frag, a.name)
    else:
        src_dir = os.path.join(here, "..", "data", "whale-audio")
        for frag, name in DEFAULTS:
            p = os.path.join(src_dir, frag + ".wav")
            if not os.path.exists(p):
                continue
            dst = os.path.join(a.dst, frag + ".wav")
            if os.path.abspath(p) != os.path.abspath(dst):
                shutil.copyfile(p, dst)
            print("installed %s (%d B)" % (dst, os.path.getsize(dst)))
            upsert(idx, frag, name)

    with open(idx_path, "w", encoding="utf-8") as fh:
        json.dump(idx, fh, ensure_ascii=False, indent=2)
    print("wrote", idx_path)
    print(json.dumps(idx, ensure_ascii=False))


if __name__ == "__main__":
    main()
