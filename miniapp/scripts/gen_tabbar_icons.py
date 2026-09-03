# -*- coding: utf-8 -*-
"""生成小程序原生 TabBar 图标(81x81,微信推荐尺寸,透明背景)。

来源: Lucide 图标库(https://lucide.dev),经 Iconify API 取 SVG 后转 PNG。
四 Tab:今天(home)/ 记录(file-text)/ 趋势(trending-up)/ 我的(user-round)。
两态:灰 #9AAEA2(未选中)、绿 #0E9E68(选中)。

流程:
  1. 用 urllib 从 Iconify 拉取各图标两态 SVG(指定颜色)
  2. 用 Node + sharp 把 SVG 栅格化成 81x81 透明 PNG

重跑即可换色/换图标:改下方 ICONS / COLORS 后 `python gen_tabbar_icons.py`。
sharp 安装在隔离环境 ~/.workbuddy/binaries/node/workspace;如缺失会尝试 npm 安装。
"""
import os
import sys
import subprocess
import shutil
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "src", "static", "tabbar"))
os.makedirs(OUT, exist_ok=True)

# 图标映射: 输出文件名(去掉 _gray/_green) -> Lucide 图标名
ICONS = {
    "tab_today": "home",
    "tab_record": "file-text",
    "tab_trend": "trending-up",
    "tab_profile": "user-round",
}

# 两态配色(与 src/pages.json 的 tabBar.color / selectedColor 保持一致)
COLORS = {"gray": "9AAEA2", "green": "0E9E68"}

SIZE = 81
API = "https://api.iconify.design/lucide/{icon}.svg?color=%23{color}"

# ---- 定位 Node + sharp(隔离环境) ----
NODE = shutil.which("node") or r"C:\Users\Administrator\.workbuddy\binaries\node\versions\22.22.2-2\node.exe"
SHARP_DIR = r"C:\Users\Administrator\.workbuddy\binaries\node\workspace\node_modules"
if not os.path.isdir(os.path.join(SHARP_DIR, "sharp")):
    print("未找到 sharp,请先安装:", file=sys.stderr)
    print(f'  cd {os.path.dirname(SHARP_DIR)} && npm install sharp', file=sys.stderr)
    sys.exit(1)

# 临时 Node 转换器:从 stdin 读 SVG,写出 81x81 透明 PNG
CONVERTER = r"""
const sharp = require('sharp');
const fs = require('fs');
const [inp, outp] = process.argv.slice(2);
const svg = fs.readFileSync(inp);
sharp(svg, { density: 384 }).resize(%d, %d).png().toFile(outp)
  .then(() => console.log('wrote', outp))
  .catch(e => { console.error(e); process.exit(1); });
""" % (SIZE, SIZE)


def fetch_svg(icon, color):
    url = API.format(icon=icon, color=color)
    req = urllib.request.Request(url, headers={"User-Agent": "fit-app-tabbar"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def main():
    conv_path = os.path.join(HERE, "_conv_tmp.cjs")
    with open(conv_path, "w", encoding="utf-8") as f:
        f.write(CONVERTER)
    try:
        for out_name, lucide in ICONS.items():
            for tag, hexc in COLORS.items():
                svg = fetch_svg(lucide, hexc)
                svg_path = os.path.join(HERE, f"_dl_{out_name}_{tag}.svg")
                with open(svg_path, "wb") as f:
                    f.write(svg)
                png_path = os.path.join(OUT, f"{out_name}_{tag}.png")
                env = dict(os.environ, NODE_PATH=SHARP_DIR)
                try:
                    subprocess.run([NODE, conv_path, svg_path, png_path],
                                   env=env, check=True)
                except subprocess.CalledProcessError as e:
                    print("转换失败:", out_name, tag, e, file=sys.stderr)
                    sys.exit(1)
                os.remove(svg_path)
    finally:
        for f in os.listdir(HERE):
            if f.startswith("_dl_") and f.endswith(".svg"):
                try:
                    os.remove(os.path.join(HERE, f))
                except OSError:
                    pass
        try:
            os.remove(conv_path)
        except OSError:
            pass  # noqa
        try:
            os.remove(conv_path.replace(".cjs", ".mjs"))
        except OSError:
            pass
    print("done")


if __name__ == "__main__":
    main()
