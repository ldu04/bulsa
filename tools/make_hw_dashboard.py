"""make_hw_dashboard.py — 실물 런 기록을 대시보드에서 재생할 수 있게 만든다.

    python tools/make_hw_dashboard.py            # results/hw/run_205330.json → dashboard/hw.html + data_hw.js
    python tools/make_hw_dashboard.py <run.json>

대시보드(index.html)는 기본으로 시뮬 스냅샷(data.js)을 재생한다. 실물 런 JSON 은 같은 형식
(meta + frames.ours)이라 window.SNAPSHOTS 로 감싸기만 하면 된다. hw.html?f=1504 처럼
프레임을 지정하면 그 시각 화면이 열린다 (docs/screens 의 캡처가 이것).
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "results", "hw", "run_205330.json")
dash = os.path.join(ROOT, "dashboard")
with open(src, encoding="utf-8") as f:
    body = f.read()
with open(os.path.join(dash, "data_hw.js"), "w", encoding="utf-8") as f:
    f.write("window.SNAPSHOTS = " + body + ";\n")
with open(os.path.join(dash, "index.html"), encoding="utf-8") as f:
    html = f.read()
with open(os.path.join(dash, "hw.html"), "w", encoding="utf-8") as f:
    f.write(html.replace('<script src="data.js"></script>', '<script src="data_hw.js"></script>'))
print("dashboard/hw.html + data_hw.js <-", os.path.relpath(src, ROOT))
