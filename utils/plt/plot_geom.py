import argparse
import ast
import json
from pathlib import Path

import matplotlib.pyplot as plt


def load_geom(path: Path) -> dict:
    text = path.read_text(encoding="utf-8").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return ast.literal_eval(text)


def plot_polygon(geom: dict, output: Path | None = None) -> None:
    if geom.get("kind") != "polygon":
        raise ValueError(f"Unsupported kind: {geom.get('kind')}")

    points = geom.get("pnts", [])
    if not points:
        raise ValueError("Polygon has no points")

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(xs, ys, "-o", linewidth=1.5, markersize=2.5, color="#1f77b4")
    ax.fill(xs, ys, alpha=0.18, color="#1f77b4")

    material = geom.get("material", "UNKNOWN")
    ax.set_title(f"Geometry: polygon | material={material}")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")

    # 横纵比
    ax.set_aspect(1.0, adjustable="box")

    ax.grid(True, linestyle="--", alpha=0.35)

    margin_x = max((max(xs) - min(xs)) * 0.03, 1.0)
    margin_y = max((max(ys) - min(ys)) * 0.08, 1.0)
    ax.set_xlim(min(xs) - margin_x, max(xs) + margin_x)
    ax.set_ylim(min(ys) - margin_y, max(ys) + margin_y)

    plt.tight_layout()

    if output is not None:
        fig.savefig(output, dpi=200)
        print(f"saved: {output}")
    else:
        plt.show()


def main() -> None:
    geom = {
            'kind': 'polygon', 
            'pnts': 
        
            [(0.0, 0.0), (0.0, 118.8), (133.0, 118.8), (158.5, 60.7), (158.5, 58.0), (158.5, 0.0)]

            , 
            'material': 'VOID'
        }



    plot_polygon(geom, output=Path("utils\\plt\\geom\\geom.png"))


if __name__ == "__main__":
    main()