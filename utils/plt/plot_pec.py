import argparse
import ast
import json
from pathlib import Path

import matplotlib.pyplot as plt


def load_data(path: Path) -> dict:
    text = path.read_text(encoding="utf-8").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return ast.literal_eval(text)


def plot_areas(area_map: dict, output: Path | None = None) -> None:
    fig, ax = plt.subplots(figsize=(12, 4))

    all_x = []
    all_y = []

    for name, area in area_map.items():
        points = area.get("points", [])
        if not points:
            continue

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        all_x.extend(xs)
        all_y.extend(ys)

        material = area.get("material", "UNKNOWN")
        color = "#d62728" if material == "PEC" else "#1f77b4"

        ax.plot(xs, ys, "-", linewidth=1.2, color=color)
        ax.fill(xs, ys, alpha=0.22, color=color, label=name)

        cx = sum(xs[:-1]) / max(len(xs[:-1]), 1)
        cy = sum(ys[:-1]) / max(len(ys[:-1]), 1)
        ax.text(cx, cy, name, fontsize=8, ha="center", va="center")

    if not all_x or not all_y:
        raise ValueError("No valid areas to plot")

    x_min, x_max = min(all_x), max(all_x)
    y_min, y_max = min(all_y), max(all_y)
    width = max(x_max - x_min, 1.0)
    height = max(y_max - y_min, 1.0)

    target_ratio = 3.0  # 1:3 画布，对应宽:高 = 3:1
    current_ratio = width / height

    if current_ratio < target_ratio:
        target_width = height * target_ratio
        pad = (target_width - width) / 2
        x_min -= pad
        x_max += pad
    else:
        target_height = width / target_ratio
        pad = (target_height - height) / 2
        y_min -= pad
        y_max += pad

    margin_x = max((x_max - x_min) * 0.03, 1.0)
    margin_y = max((y_max - y_min) * 0.05, 1.0)

    ax.set_xlim(x_min - margin_x, x_max + margin_x)
    ax.set_ylim(y_min - margin_y, y_max + margin_y)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("PEC Areas")
    ax.grid(True, linestyle="--", alpha=0.35)

    plt.tight_layout()

    if output is not None:
        fig.savefig(output, dpi=200)
        print(f"saved: {output}")
    else:
        plt.show()


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot PEC area map from JSON/Python-dict file.")
    parser.add_argument("input", help="Path to area map file")
    parser.add_argument("-o", "--output", help="Optional output image path")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else None

    data = load_data(input_path)
    plot_areas(data, output_path)


if __name__ == "__main__":
    """
    main() 
    pass
    # """


    data =  {
                "PEC_1": {"points": [(389.6, 53.0), (389.6, 49.8), (395.6, 49.8), (395.6, 53.0), (397.6, 53.0), (397.6, 49.8), (401.2, 49.8), (401.2, 53.0), (456.7, 53.0), (456.7, 46.3), (463.9, 46.3), (463.9, 53.0), (466.2, 53.0), (466.2, 49.8), (470.2, 49.8), (470.2, 53.0), (471.7, 53.0), (471.7, 49.8), (475.7, 49.8), (475.7, 53.0), (476.9, 53.0), (476.9, 49.8), (480.9, 49.8), (480.9, 53.0), (480.9, 54.0), (485.9, 54.0), (485.9, 49.0), (520.9, 49.0), (520.9, 54.0), (480.9, 58.0), (480.9, 59.0), (482.9, 59.0), (507.9, 59.0), (507.9, 61.0), (509.9, 61.0), (509.9, 59.0), (537.9, 59.0), (537.9, 0.0), (130.0, 0.0), (130.0, 53.0), (158.5, 53.0), (158.5, 50.5), (163.0, 50.5), (163.0, 53.0), (167.8, 53.0), (167.8, 46.3), (175.0, 46.3), (175.0, 53.0), (372.7, 53.0), (372.7, 46.3), (379.9, 46.3), (379.9, 53.0), (383.0, 53.0), (383.0, 49.8), (387.1, 49.8), (387.1, 53.0), (389.6, 53.0)]},
                "PEC_2": {"points": [(475.7, 58.0), (475.7, 61.2), (471.7, 61.2), (471.7, 58.0), (470.2, 58.0), (470.2, 61.2), (466.2, 61.2), (466.2, 58.0), (461.9, 58.0), (461.9, 64.7), (454.7, 64.7), (454.7, 58.0), (401.2, 58.0), (401.2, 61.2), (397.6, 61.2), (397.6, 58.0), (395.6, 58.0), (395.6, 61.0), (389.6, 61.0), (389.6, 58.0), (387.1, 58.0), (387.1, 61.2), (383.5, 61.2), (383.5, 58.0), (377.9, 58.0), (377.9, 64.7), (370.7, 64.7), (370.7, 58.0), (173.0, 58.0), (173.0, 64.7), (165.8, 64.7), (165.8, 58.0), (163.0, 58.0), (163.0, 60.7), (163.0, 60.8), (163.0, 61.2), (135.0, 61.2), (135.0, 70.0), (537.9, 70.0), (537.9, 68.0), (507.9, 68.0), (482.9, 61.2), (480.9, 61.2), (476.9, 61.2), (476.9, 58.0), (475.7, 58.0)]},
                "PEC_3": {"points": [(133.0, 61.0), (134.0, 61.0), (134.0, 60.7), (158.5, 60.7), (158.5, 58.0), (133.0, 58.0), (130.0, 58.0), (130.0, 70.0), (130.0, 115.8), (0.0, 115.8), (0.0, 118.8), (130.0, 118.8), (133.0, 118.8), (133.0, 70.0), (133.0, 61.0)]},
                "PEC_4": {"points": [(0.0, 55.8), (0.0, 60.8), (50.0, 60.8), (50.0, 55.8), (80.0, 55.8), (80.0, 55.2), (50.0, 55.2), (50.0, 50.8), (5.0, 50.8), (5.0, 0.0), (0.0, 0.0), (0.0, 55.2), (0.0, 55.8)]}
            }



    output_path = Path("utils\\plt\\pec\\pec.png")

    plot_areas(data, output_path)
    
