from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPen

from src.domain.config.m2u_convconst import init_constants


class GeometryPreviewService:
    def _make_font(self, family: str, point_size: int, weight: int = QFont.Normal) -> QFont:
        font = QFont(family)
        font.setWeight(weight)
        font.setPointSize(max(1, int(point_size)))
        return font

    def load_geometry_area_result(self, device_name: str) -> dict[str, Any]:
        constants = init_constants(device_name)
        source_path = Path(constants.mid_symbols_json)
        if not source_path.exists():
            return {"source_path": str(source_path), "area_result": None}

        payload = json.loads(source_path.read_text(encoding="utf-8"))
        area_result = payload.get("geometry", {}).get("area_cac_result", {})
        if not area_result:
            area_result = payload.get("sT", {}).get("geometry", {}).get("area_cac_result", {})
        return {
            "source_path": str(source_path),
            "area_result": area_result if isinstance(area_result, dict) else None,
        }

    def generate_pointset_file(self, device_name: str) -> dict[str, Any]:
        constants = init_constants(device_name)
        source_path = Path(constants.mid_symbols_json)
        if not source_path.exists():
            raise FileNotFoundError(f"中间文件不存在：{source_path}")

        payload = json.loads(source_path.read_text(encoding="utf-8"))
        void_area = payload.get("geometry", {}).get("area_cac_result", {}).get("void_area", {})
        pnts = void_area.get("pnts", []) if isinstance(void_area, dict) else []
        if not isinstance(pnts, list) or not pnts:
            raise ValueError("当前 mid_symbols.json 中没有可用的 void_area.pnts 数据。")

        rows: list[list[str]] = []
        for point in pnts:
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                continue
            try:
                x = float(point[0])
                y = float(point[1])
            except (TypeError, ValueError):
                continue
            rows.append(["0.0", f"{y:g}", f"{x:g}"])

        if not rows:
            raise ValueError("void_area.pnts 中没有可转换的坐标点。")

        output_path = source_path.parent / "points.txt"
        output_path.write_text("\n".join(" ".join(row) for row in rows) + "\n", encoding="utf-8")
        return {"path": str(output_path), "rows": rows}

    def load_pointset_file(self, device_name: str) -> dict[str, Any]:
        constants = init_constants(device_name)
        path = Path(constants.pre_jsonl).parent / "points.txt"
        if not path.exists():
            return {"path": "", "rows": []}

        rows: list[list[str]] = []
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 3:
                rows.append(parts[:3])
        return {"path": str(path), "rows": rows}

    def generate_geometry_preview(
        self,
        device_name: str,
        area_result: dict[str, Any],
        preview_kind: str,
        aspect_ratio: float,
        resolution_scale: float,
    ) -> dict[str, Any]:
        constants = init_constants(device_name)
        normalized_kind = preview_kind if preview_kind in {"pec", "void"} else "pec"
        output_path = Path(constants.pre_jsonl).parent / f"geometry_preview_{normalized_kind}.png"
        self._render_geometry_preview(
            area_result,
            output_path,
            preview_kind=normalized_kind,
            aspect_ratio=aspect_ratio,
            resolution_scale=resolution_scale,
        )
        return {"path": str(output_path), "preview_kind": normalized_kind}

    def _render_geometry_preview(
        self,
        area_result: dict[str, Any],
        output_path: Path,
        preview_kind: str = "pec",
        aspect_ratio: float = 1.0,
        resolution_scale: float = 1.0,
    ) -> None:
        entities: list[tuple[str, list[QPointF], QColor, QColor]] = []
        all_x: list[float] = []
        all_y: list[float] = []

        def collect_entity(
            name: str,
            entity: dict[str, Any],
            line_hex: str,
            fill_rgba: tuple[int, int, int, int],
        ) -> None:
            points = entity.get("points")
            if not isinstance(points, list) or len(points) < 2:
                points = entity.get("pnts", [])
            if not isinstance(points, list) or len(points) < 2:
                return
            normalized: list[QPointF] = []
            for point in points:
                if not isinstance(point, (list, tuple)) or len(point) < 2:
                    continue
                try:
                    x = float(point[0])
                    y = float(point[1])
                except (TypeError, ValueError):
                    continue
                normalized.append(QPointF(x, y))
                all_x.append(x)
                all_y.append(y)
            if len(normalized) >= 2:
                entities.append(
                    (
                        name,
                        normalized,
                        QColor(line_hex),
                        QColor(fill_rgba[0], fill_rgba[1], fill_rgba[2], fill_rgba[3]),
                    )
                )

        void_area = area_result.get("void_area", {})
        pec_connected_components = area_result.get("pec_connected_components", {})
        metal_area_entities = area_result.get("metal_area_entities", {})

        if preview_kind == "void" and isinstance(void_area, dict):
            collect_entity("void_area", void_area, "#4f81bd", (79, 129, 189, 56))

        if preview_kind == "pec" and isinstance(pec_connected_components, dict):
            palette = [
                ("#d97a2b", (217, 122, 43, 68)),
                ("#5f88af", (95, 136, 175, 58)),
                ("#6b9080", (107, 144, 128, 58)),
                ("#8b5e83", (139, 94, 131, 58)),
                ("#9c6644", (156, 102, 68, 58)),
            ]
            for index, (name, entity) in enumerate(pec_connected_components.items()):
                if not isinstance(entity, dict):
                    continue
                line_hex, fill_rgba = palette[index % len(palette)]
                collect_entity(str(name), entity, line_hex, fill_rgba)
        elif preview_kind == "pec" and isinstance(metal_area_entities, dict):
            palette = [
                ("#d97a2b", (217, 122, 43, 68)),
                ("#5f88af", (95, 136, 175, 58)),
                ("#6b9080", (107, 144, 128, 58)),
                ("#8b5e83", (139, 94, 131, 58)),
                ("#9c6644", (156, 102, 68, 58)),
            ]
            for index, (name, entity) in enumerate(metal_area_entities.items()):
                if not isinstance(entity, dict):
                    continue
                line_hex, fill_rgba = palette[index % len(palette)]
                collect_entity(str(name), entity, line_hex, fill_rgba)

        if not entities or not all_x or not all_y:
            raise ValueError("area_cac_result 中没有可绘制的 points/pnts 数据。")

        x_min, x_max = 0.0, max(all_x)
        y_min, y_max = 0.0, max(all_y)
        width = max(x_max - x_min, 1.0)
        height = max(y_max - y_min, 1.0)
        target_ratio = min(max(float(aspect_ratio), 0.001), 1000.0)
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
        world = QRectF(
            x_min - margin_x,
            y_min - margin_y,
            (x_max - x_min) + margin_x * 2,
            (y_max - y_min) + margin_y * 2,
        )

        safe_scale = min(max(float(resolution_scale), 0.5), 6.0)
        canvas_width = max(900, int(round(1800 * safe_scale)))
        canvas_height = max(380, int(round(760 * safe_scale)))
        image = QImage(canvas_width, canvas_height, QImage.Format_ARGB32)
        image.fill(QColor("#f7f9fc"))
        font_scale = max(1.0, 2.0 * safe_scale)
        border_scale = max(1.0, 0.5 * (safe_scale**2))
        grid_scale = max(1.0, 0.5 * (safe_scale**2))

        painter = QPainter(image)
        try:
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.TextAntialiasing, True)

            left_margin = max(96, int(round(84 + 56 * font_scale + 10 * grid_scale)))
            top_margin = max(68, int(round(42 + 34 * font_scale)))
            right_margin = max(60, int(round(28 + 28 * font_scale)))
            bottom_margin = max(96, int(round(56 + 40 * font_scale + 14 * grid_scale)))
            plot_rect = QRectF(
                left_margin,
                top_margin,
                max(240, canvas_width - left_margin - right_margin),
                max(180, canvas_height - top_margin - bottom_margin),
            )

            def map_point(point: QPointF) -> QPointF:
                x_ratio = 0.5 if world.width() == 0 else (point.x() - world.left()) / world.width()
                y_ratio = 0.5 if world.height() == 0 else (point.y() - world.top()) / world.height()
                x = plot_rect.left() + x_ratio * plot_rect.width()
                y = plot_rect.bottom() - y_ratio * plot_rect.height()
                return QPointF(x, y)

            border_pen = QPen(QColor("#7f8c98"))
            border_pen.setWidth(max(1, int(round(border_scale))))
            painter.setPen(border_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(plot_rect)

            tick_font = self._make_font("Microsoft YaHei UI", max(10, int(round(11 * font_scale))))
            painter.setFont(tick_font)
            painter.setPen(QColor("#526170"))

            def nice_step(max_value: float, target_ticks: int = 6) -> float:
                if max_value <= 0:
                    return 1.0
                rough = max_value / max(target_ticks, 1)
                exponent = math.floor(math.log10(rough))
                scale = 10 ** exponent
                normalized = rough / scale
                if normalized <= 1:
                    nice = 1.0
                elif normalized <= 2:
                    nice = 2.0
                elif normalized <= 5:
                    nice = 5.0
                else:
                    nice = 10.0
                return nice * scale

            def build_ticks(max_value: float) -> list[float]:
                if max_value <= 0:
                    return [0.0]
                step = nice_step(max_value)
                ticks: list[float] = [0.0]
                tick = step
                while tick <= max_value + step * 0.5:
                    ticks.append(tick)
                    tick += step
                return ticks

            x_ticks = build_ticks(max(world.right(), 0.0))
            y_ticks = build_ticks(max(world.bottom(), 0.0))

            grid_pen = QPen(QColor("#c8d4df"))
            grid_pen.setStyle(Qt.DashLine)
            grid_pen.setWidth(max(1, int(round(grid_scale))))
            painter.setPen(grid_pen)
            for x_value in x_ticks:
                x_ratio = 0.0 if world.width() == 0 else (x_value - world.left()) / world.width()
                if x_ratio < -1e-9 or x_ratio > 1 + 1e-9:
                    continue
                x = plot_rect.left() + x_ratio * plot_rect.width()
                painter.drawLine(QPointF(x, plot_rect.top()), QPointF(x, plot_rect.bottom()))
            for y_value in y_ticks:
                y_ratio = 0.0 if world.height() == 0 else (y_value - world.top()) / world.height()
                if y_ratio < -1e-9 or y_ratio > 1 + 1e-9:
                    continue
                y = plot_rect.bottom() - y_ratio * plot_rect.height()
                painter.drawLine(QPointF(plot_rect.left(), y), QPointF(plot_rect.right(), y))

            painter.setPen(border_pen)
            painter.drawRect(plot_rect)

            for x_value in x_ticks:
                x_ratio = 0.0 if world.width() == 0 else (x_value - world.left()) / world.width()
                if x_ratio < -1e-9 or x_ratio > 1 + 1e-9:
                    continue
                x = plot_rect.left() + x_ratio * plot_rect.width()
                painter.drawLine(
                    QPointF(x, plot_rect.bottom()),
                    QPointF(x, plot_rect.bottom() + max(8, int(round(8 * grid_scale)))),
                )
                painter.drawText(
                    QRectF(
                        x - max(52, int(round(64 * font_scale))),
                        plot_rect.bottom() + max(10, int(round(10 * grid_scale))),
                        max(104, int(round(128 * font_scale))),
                        max(20, int(round(28 * font_scale))),
                    ),
                    Qt.AlignHCenter | Qt.AlignTop,
                    f"{int(x_value) if abs(x_value - round(x_value)) < 1e-9 else x_value:g}",
                )

            for y_value in y_ticks:
                y_ratio = 0.0 if world.height() == 0 else (y_value - world.top()) / world.height()
                if y_ratio < -1e-9 or y_ratio > 1 + 1e-9:
                    continue
                y = plot_rect.bottom() - y_ratio * plot_rect.height()
                painter.drawLine(
                    QPointF(plot_rect.left() - max(8, int(round(8 * grid_scale))), y),
                    QPointF(plot_rect.left(), y),
                )
                painter.drawText(
                    QRectF(
                        0,
                        y - max(10, int(round(14 * font_scale))),
                        max(20, plot_rect.left() - max(12, int(round(14 * grid_scale)))),
                        max(20, int(round(28 * font_scale))),
                    ),
                    Qt.AlignRight | Qt.AlignVCenter,
                    f"{int(y_value) if abs(y_value - round(y_value)) < 1e-9 else y_value:g}",
                )

            label_font = self._make_font("Microsoft YaHei UI", max(12, int(round(13 * font_scale))))
            painter.setFont(label_font)

            for _name, points, line_color, fill_color in entities:
                path = QPainterPath()
                mapped_points = [map_point(point) for point in points]
                path.moveTo(mapped_points[0])
                for point in mapped_points[1:]:
                    path.lineTo(point)
                if mapped_points[0] != mapped_points[-1]:
                    path.closeSubpath()

                painter.fillPath(path, fill_color)
                outline_pen = QPen(line_color)
                outline_pen.setWidth(1)
                painter.setPen(outline_pen)
                painter.drawPath(path)
        finally:
            painter.end()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        if not image.save(str(output_path)):
            raise RuntimeError(f"无法保存图形预览：{output_path}")
