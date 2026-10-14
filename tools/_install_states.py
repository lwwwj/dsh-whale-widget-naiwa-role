# -*- coding: utf-8 -*-
"""把 data/whale-roles 里的 6 张状态图装成插件角色（写进 DSH_HOME/whale-roles）。

用法:
  python _install_states.py                  # 源目录 = 本脚本上一级的 data/whale-roles
  python _install_states.py --from <目录>     # 自定义源目录
  python _install_states.py --to <目录>       # 自定义目标目录（默认 %USERPROFILE%\\.dsh\\whale-roles）

环境变量 DSH_HOME 可以整体覆盖用户数据目录（默认 %USERPROFILE%\\.dsh）。
注意：这一步会把 roles.json 重写成这 6 条（state0 置顶显示为「奶蛙」）。
"""
import argparse
import json
import os
import shutil
import time

STATES = [
    ("state0", "奶蛙"),
    ("state1", "奶蛙·大笑"),
    ("state2", "安迪"),
    ("state3", "奶蛙·思考"),
    ("state4", "奶蛙·完成"),
    ("state5", "奶蛙·指点"),
]


def dsh_home():
    return os.environ.get("DSH_HOME") or os.path.join(os.path.expanduser("~"), ".dsh")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", default=os.path.join(here, "..", "data", "whale-roles"))
    ap.add_argument("--to", dest="dst", default=os.path.join(dsh_home(), "whale-roles"))
    a = ap.parse_args()
    os.makedirs(a.dst, exist_ok=True)
    now = int(time.time() * 1000)
    roles = []
    for i, (sid, name) in enumerate(STATES):
        src = os.path.join(a.src, sid + ".png")
        if not os.path.exists(src):
            raise SystemExit("missing " + src)
        dst = os.path.join(a.dst, sid + ".png")
        if os.path.abspath(src) != os.path.abspath(dst):
            shutil.copyfile(src, dst)
        roles.append({"id": sid, "name": name, "format": "png",
                      "pinnedAt": 1 if sid == "state0" else None, "createdAt": now + i})
        print("installed role %s (%d B)" % (sid, os.path.getsize(dst)))
    path = os.path.join(a.dst, "roles.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"version": 1, "roles": roles}, fh, ensure_ascii=False, indent=2)
    print("wrote", path)


if __name__ == "__main__":
    main()
