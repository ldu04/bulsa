"""방향 오차 2.85° 나누기 — 같은 추정 코드에 꺼진 시각만 바꿔 넣어 원인별 오차를 잰다.

    python tools/decompose_dir_error.py

넣는 시각 네 가지:
  실제 측정 시각            results/hw/run_205330_deaths.csv 그대로 (최종 58.33° 재현 확인용)
  둥근 화선 + 시각 오차 0   점화점에서 원형으로 퍼질 때의 시각 r / v
  직선 화선 + 시각 오차 0   참값 방향으로 곧게 나아갈 때의 시각
  둥근 화선 + 무작위 오차   표준편차 1.24 s, 10.4 s 를 2,000번씩 (시계 오차의 영향)

참값 정의는 tools/recompute_run205330.py 와 같다(점화점 → 판 중심, 실측 좌표).
이 값들은 재계산이지 새 실물 측정이 아니다. 좌표와 채택 센서 15개는 실제 실험과 같다.
"""
import csv
import math
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from sim.config import Config
from sim.estimator import Estimator
from sim.network import Network
from sim.node import Node

V = 0.0005785               # 화선 속도 [m/s]
IGNITION = (0.02, -0.11)    # 점화점 [m]
RADIO_RANGE = 0.36          # 추정기 이웃 반경 [m], gateway/deploy_config.json
SPACING = 0.2


def load():
    with open(os.path.join(ROOT, "results", "hw", "run_205330_deaths.csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    pos = {int(r["id"]): (float(r["x"]), float(r["y"])) for r in rows}
    t = {int(r["id"]): float(r["death_t_est"]) for r in rows}
    accepted = [int(r["id"]) for r in rows if r["accepted"] == "1"]
    return pos, t, accepted


def estimate(pos, times, accepted):
    cfg = Config(mode="ours", radio_range_m=RADIO_RANGE, dt=0.1, alert_horizon=SPACING / V,
                 dt_window=RADIO_RANGE / V, speed_true=V, spacing_m=SPACING)
    net = Network([Node(id=i, pos=pos[i], is_sink=False) for i in pos], cfg)
    est = Estimator(cfg, neighbors=net.neighbors)
    last = None
    for i in sorted(accepted, key=lambda k: times[k]):
        last = est.update([{"id": i, "pos": pos[i], "death_t_est": times[i]}], times[i], [])
    d = last["dir"]
    return math.degrees(math.atan2(d[1], d[0]))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    pos, measured, accepted = load()
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    true_deg = math.degrees(math.atan2((min(ys) + max(ys)) / 2 - IGNITION[1],
                                       (min(xs) + max(xs)) / 2 - IGNITION[0]))
    th = math.radians(true_deg)
    radial = {i: math.hypot(p[0] - IGNITION[0], p[1] - IGNITION[1]) / V for i, p in pos.items()}
    straight = {i: (p[0] * math.cos(th) + p[1] * math.sin(th)) / V for i, p in pos.items()}

    print(f"참값 {true_deg:.4f}°")
    for name, times in (("실제 측정 시각", measured),
                        ("둥근 화선 + 시각 오차 0", radial),
                        ("직선 화선 + 시각 오차 0", straight)):
        a = estimate(pos, times, accepted)
        print(f"{name:<20s} 방향 {a:8.4f}°  오차 {a - true_deg:+.3f}°")

    for sigma in (1.24, 10.4):
        random.seed(1)
        errs = sorted(estimate(pos, {i: radial[i] + random.gauss(0, sigma) for i in pos}, accepted) - true_deg
                      for _ in range(2000))
        print(f"둥근 화선 + 시각 오차 σ={sigma} s: 평균 {sum(errs) / len(errs):+.3f}°, "
              f"90% 범위 {errs[100]:+.3f} ~ {errs[1899]:+.3f}°")


if __name__ == "__main__":
    main()
