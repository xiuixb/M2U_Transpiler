from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QRectF, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap, QTextCursor, QTextDocument
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QHeaderView,
    QPushButton,
    QPlainTextEdit,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.presentation.controller import FrontendController


def pretty_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def path_tail(value: str, limit: int = 56) -> str:
    if len(value) <= limit:
        return value
    return "..." + value[-(limit - 3) :]


class RouteTableWidget(QTableWidget):
    def __init__(self, rows: int, columns: int, parent: QWidget | None = None) -> None:
        super().__init__(rows, columns, parent)
        self.setFocusPolicy(Qt.ClickFocus)

    def wheelEvent(self, event) -> None:  # type: ignore[override]
        if self.hasFocus():
            super().wheelEvent(event)
            event.accept()
            return
        event.ignore()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        self.setFocus()
        super().mousePressEvent(event)


class FocusComboBox(QComboBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFocusPolicy(Qt.ClickFocus)

    def wheelEvent(self, event) -> None:  # type: ignore[override]
        if self.hasFocus():
            super().wheelEvent(event)
            event.accept()
            return
        event.ignore()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        self.setFocus()
        super().mousePressEvent(event)


class GraphicsImageView(QGraphicsView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene().addItem(self.pixmap_item)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setRenderHints(self.renderHints())
        self._zoom = 1.0

    def set_pixmap(self, pixmap: QPixmap) -> None:
        self.pixmap_item.setPixmap(pixmap)
        self.scene().setSceneRect(QRectF(pixmap.rect()))

    def clear_pixmap(self) -> None:
        self.pixmap_item.setPixmap(QPixmap())
        self.scene().setSceneRect(QRectF())
        self.resetTransform()
        self._zoom = 1.0

    def set_zoom(self, zoom: float) -> None:
        self._zoom = min(max(float(zoom), 0.05), 20.0)
        self.resetTransform()
        self.scale(self._zoom, self._zoom)

    def zoom(self) -> float:
        return self._zoom

    def fit_image(self) -> None:
        pixmap = self.pixmap_item.pixmap()
        if pixmap.isNull():
            self.resetTransform()
            self._zoom = 1.0
            return
        self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
        self._zoom = self.transform().m11()

    def wheelEvent(self, event) -> None:  # type: ignore[override]
        if self.pixmap_item.pixmap().isNull():
            event.ignore()
            return
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.set_zoom(self._zoom * factor)
        event.accept()


class TextSearchBar(QWidget):
    def __init__(self, editor: QTextEdit | QPlainTextEdit, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.editor = editor
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索文本")
        self.search_input.textChanged.connect(self._update_state)
        self.search_input.returnPressed.connect(self.find_next)

        self.prev_button = QPushButton("上一个")
        self.next_button = QPushButton("下一个")
        self.status_label = QLabel("")

        self.prev_button.clicked.connect(self.find_previous)
        self.next_button.clicked.connect(self.find_next)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(QLabel("搜索"))
        layout.addWidget(self.search_input, 1)
        layout.addWidget(self.prev_button)
        layout.addWidget(self.next_button)
        layout.addWidget(self.status_label)
        self._update_state()

    def _update_state(self) -> None:
        has_query = bool(self.search_input.text().strip())
        self.prev_button.setEnabled(has_query)
        self.next_button.setEnabled(has_query)
        if not has_query:
            self.status_label.setText("")

    def find_next(self) -> None:
        self._find(backward=False)

    def find_previous(self) -> None:
        self._find(backward=True)

    def _find(self, backward: bool) -> None:
        query = self.search_input.text().strip()
        if not query:
            self.status_label.setText("")
            return

        document = self.editor.document()
        cursor = self.editor.textCursor()
        flags = QTextDocument.FindBackward if backward else QTextDocument.FindFlags()
        found = document.find(query, cursor, flags)
        if found.isNull():
            wrap_cursor = QTextCursor(document)
            wrap_cursor.movePosition(QTextCursor.End if backward else QTextCursor.Start)
            found = document.find(query, wrap_cursor, flags)

        if found.isNull():
            self.status_label.setText("未找到")
            return

        self.editor.setTextCursor(found)
        self.editor.ensureCursorVisible()
        self.status_label.setText("已定位")


class KeyValueCard(QFrame):
    def __init__(self, title: str, value: str = "-") -> None:
        super().__init__()
        self.setObjectName("keyValueCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(66)
        self.setMaximumHeight(80)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("cardTitle")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("cardValue")
        self.value_label.setWordWrap(True)
        self.value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)


class DevicePanel(QWidget):
    def __init__(self, controller: FrontendController) -> None:
        super().__init__()
        self.controller = controller
        self.select_button = QPushButton("选择器件文件")
        self.select_button.clicked.connect(self._choose_file)
        self.open_dir_button = QPushButton("打开文件目录")
        self.open_dir_button.clicked.connect(self._open_file_dir)
        self.open_dir_button.setEnabled(False)

        self.cards: dict[str, KeyValueCard] = {
            "device_name": KeyValueCard("当前器件名"),
            "input_file": KeyValueCard("输入文件"),
            "device_dir": KeyValueCard("器件目录"),
            "workdir": KeyValueCard("Workdir"),
            "device_config_path": KeyValueCard("配置文件"),
        }

        grid = QGridLayout()
        for index, key in enumerate(self.cards):
            row, col = divmod(index, 2)
            grid.addWidget(self.cards[key], row, col)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(10)
        actions.addWidget(self.select_button)
        actions.addWidget(self.open_dir_button)
        actions.addStretch(1)

        root = QVBoxLayout(self)
        root.addLayout(actions)
        root.addLayout(grid)
        root.addStretch(1)

    def _choose_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 MCL/M2D 文件",
            "",
            "MCL Files (*.mcl *.m2d);;All Files (*.*)",
        )
        if file_path:
            self.controller.select_device(file_path)

    def _open_file_dir(self) -> None:
        device = self.controller.state.current_device or {}
        input_file = device.get("input_file", "")
        if not input_file:
            return
        directory = Path(input_file).resolve().parent
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(directory)))

    def update_view(self, state: dict[str, Any]) -> None:
        device = state.get("current_device") or {}
        for key, card in self.cards.items():
            value = str(device.get(key, "-")) if device else "-"
            card.value_label.setText(path_tail(value))
            card.value_label.setToolTip(value)
        self.open_dir_button.setEnabled(bool(device.get("input_file")))


class ConfigPanel(QWidget):
    def __init__(self, controller: FrontendController) -> None:
        super().__init__()
        self.controller = controller
        self.path_fields: dict[str, QLineEdit] = {}
        self.runtime_fields: dict[str, QLineEdit] = {}
        self.default_runtime_fields: dict[str, QLineEdit] = {}
        self.default_debug_fields: dict[str, QComboBox] = {}
        self.route_parse_boxes: dict[str, QCheckBox] = {}
        self.route_symbol_boxes: dict[str, QCheckBox] = {}

        self.reload_button = QPushButton("读取配置")
        self.save_button = QPushButton("保存配置")
        self.reload_button.clicked.connect(self.controller.reload_config)
        self.save_button.clicked.connect(self._save)

        toolbar = QHBoxLayout()
        toolbar.addWidget(self.reload_button)
        toolbar.addWidget(self.save_button)
        toolbar.addStretch(1)

        self.path_group = self._build_paths_group()
        self.runtime_group = self._build_runtime_group()
        self.default_group = self._build_default_group()
        self.route_group = self._build_route_group()

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.addLayout(toolbar)
        content_layout.addWidget(self.route_group)
        content_layout.addWidget(self.path_group)
        content_layout.addWidget(self.runtime_group)
        content_layout.addWidget(self.default_group)
        content_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)

        root = QVBoxLayout(self)
        root.addWidget(scroll)

    def _build_paths_group(self) -> QGroupBox:
        group = QGroupBox("路径参数")
        form = QFormLayout(group)
        for key in [
            "data_dir",
            "workdir",
            "pre_jsonl",
            "parsed_json",
            "mid_round1_json",
            "mid_round2_json",
            "mid_symbols_json",
            "uni_symbols_json",
            "llmconv_json",
            "symbols_json",
            "infile_dir",
            "material_dir",
        ]:
            field = QLineEdit()
            field.setReadOnly(True)
            self.path_fields[key] = field
            form.addRow(key, field)
        return group

    def _build_runtime_group(self) -> QGroupBox:
        group = QGroupBox("运行参数")
        form = QFormLayout(group)
        for key in [
            "axis_mcl_dir",
            "axis_unipic_dir",
            "IF_Conv2Void",
            "bool_Revo_vector",
            "ywaveResolutionRatio",
            "zwaveResolutionRatio",
            "unit_lr",
            "emitter_type",
        ]:
            field = QLineEdit()
            field.textChanged.connect(lambda _text, k=key: self._mark_dirty(k))
            self.runtime_fields[key] = field
            form.addRow(key, field)
        return group

    def _build_default_group(self) -> QGroupBox:
        group = QGroupBox("全局默认值")
        layout = QVBoxLayout(group)

        hint = QLabel("这里修改的是 m2u_convconst 默认值。新器件配置会以这里为默认起点。")
        hint.setObjectName("routeHint")
        layout.addWidget(hint)

        runtime_form = QFormLayout()
        for key in [
            "axis_mcl_dir",
            "axis_unipic_dir",
            "IF_Conv2Void",
            "bool_Revo_vector",
            "ywaveResolutionRatio",
            "zwaveResolutionRatio",
            "unit_lr",
            "emitter_type",
            "material_dir",
        ]:
            field = QLineEdit()
            field.textChanged.connect(lambda _text, k=key: self._mark_conv_defaults_dirty(k))
            self.default_runtime_fields[key] = field
            runtime_form.addRow(key, field)

        debug_form = QFormLayout()
        for key in [
            "variable_debug",
            "function_debug",
            "str2qty_debug",
            "emit_debug",
            "area_debug",
            "port_debug",
            "conduct2void_debug",
            "llmconv_debug",
        ]:
            field = FocusComboBox()
            field.addItems(["False", "True"])
            field.currentTextChanged.connect(lambda _text, k=key: self._mark_conv_defaults_dirty(k))
            self.default_debug_fields[key] = field
            debug_form.addRow(key, field)

        runtime_box = QGroupBox("默认运行参数")
        runtime_box.setLayout(runtime_form)
        debug_box = QGroupBox("默认调试参数")
        debug_box.setLayout(debug_form)

        layout.addWidget(runtime_box)
        layout.addWidget(debug_box)
        return group

    def _build_route_group(self) -> QGroupBox:
        group = QGroupBox("路由参数")
        layout = QVBoxLayout(group)
        hint = QLabel("全局路由配置。两列都不选时，默认走纯规则/PLY。")
        hint.setObjectName("routeHint")
        layout.addWidget(hint)

        self.route_table = RouteTableWidget(0, 3)
        self.route_table.setHorizontalHeaderLabels(["命令", "LLM解析", "LLM符号处理"])
        self.route_table.verticalHeader().setVisible(False)
        self.route_table.setSelectionMode(QTableWidget.NoSelection)
        self.route_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.route_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.route_table.setMinimumHeight(320)
        self.route_table.horizontalHeader().setStretchLastSection(False)
        self.route_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for index in [1, 2]:
            self.route_table.horizontalHeader().setSectionResizeMode(index, QHeaderView.ResizeToContents)
        layout.addWidget(self.route_table)
        return group

    def _mark_dirty(self, _key: str) -> None:
        if self.controller.state.has_config:
            self.controller.update_config(self.collect_config())

    def _mark_conv_defaults_dirty(self, _key: str) -> None:
        if self.controller.state.conv_defaults is not None:
            self.controller.update_conv_defaults(self.collect_conv_defaults())

    def _mark_route_dirty(self) -> None:
        if self.controller.state.route_config:
            self.controller.update_route_config(self.collect_route_config())

    def collect_config(self) -> dict[str, Any]:
        config = deepcopy_or_empty(self.controller.state.device_config)
        config.setdefault("paths", {})
        config.setdefault("runtime", {})
        for key, field in self.path_fields.items():
            config["paths"][key] = field.text()
        for key, field in self.runtime_fields.items():
            config["runtime"][key] = parse_scalar(field.text())
        return config

    def collect_route_config(self) -> dict[str, Any]:
        route_config = deepcopy_or_empty(self.controller.state.route_config)
        rows = []
        llmparse_commands = []
        llmconv_commands = []
        supported_commands = route_config.get("supported_commands", [])
        regexparse_commands = route_config.get("regexparse_commands", [])
        for command in supported_commands:
            llm_parse = self.route_parse_boxes[command].isChecked()
            llm_symbol = self.route_symbol_boxes[command].isChecked()
            rows.append(
                {
                    "command": command,
                    "pure_rule": not llm_parse,
                    "llm_parse": llm_parse,
                    "llm_symbol": llm_symbol,
                }
            )
            if llm_parse:
                llmparse_commands.append(command)
            if llm_symbol:
                llmconv_commands.append(command)
        route_config["command_rows"] = rows
        route_config["llmparse_commands"] = llmparse_commands
        route_config["mcl2mid_llmconv_commands"] = llmconv_commands
        route_config["regexparse_commands"] = regexparse_commands
        return route_config

    def collect_conv_defaults(self) -> dict[str, Any]:
        conv_defaults = deepcopy_or_empty(self.controller.state.conv_defaults)
        conv_defaults.setdefault("runtime_defaults", {})
        conv_defaults.setdefault("debug_defaults", {})
        for key, field in self.default_runtime_fields.items():
            conv_defaults["runtime_defaults"][key] = parse_scalar(field.text())
        for key, field in self.default_debug_fields.items():
            conv_defaults["debug_defaults"][key] = field.currentText() == "True"
        return conv_defaults

    def _save(self) -> None:
        config_data = self.collect_config() if self.controller.state.has_device else None
        route_config = self.collect_route_config() if self.controller.state.route_config else None
        conv_defaults = self.collect_conv_defaults() if self.controller.state.conv_defaults is not None else None
        self.controller.save_config(config_data, route_config, conv_defaults)

    def _rebuild_route_table(self, route_config: dict[str, Any]) -> None:
        rows = route_config.get("command_rows", [])
        self.route_parse_boxes.clear()
        self.route_symbol_boxes.clear()
        self.route_table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            command = row["command"]
            item = QTableWidgetItem(command)
            self.route_table.setItem(row_index, 0, item)
            self.route_table.setRowHeight(row_index, 34)

            parse_box = QCheckBox()
            symbol_box = QCheckBox()

            parse_box.setChecked(bool(row.get("llm_parse", False)))
            symbol_box.setChecked(bool(row.get("llm_symbol", False)))

            parse_box.toggled.connect(lambda *_args: self._mark_route_dirty())
            symbol_box.toggled.connect(lambda *_args: self._mark_route_dirty())

            self.route_parse_boxes[command] = parse_box
            self.route_symbol_boxes[command] = symbol_box

            self.route_table.setCellWidget(row_index, 1, self._centered_widget(parse_box))
            self.route_table.setCellWidget(row_index, 2, self._centered_widget(symbol_box))

        visible_rows = min(max(len(rows), 1), 12)
        header_height = self.route_table.horizontalHeader().height()
        self.route_table.setMinimumHeight(header_height + visible_rows * 34 + 12)
        self.route_table.setMaximumHeight(header_height + visible_rows * 34 + 16)

    def _centered_widget(self, widget: QWidget) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widget, alignment=Qt.AlignCenter)
        return container

    def update_view(self, state: dict[str, Any]) -> None:
        config = state.get("device_config") or {}
        conv_defaults = state.get("conv_defaults") or {}
        route_config = state.get("route_config") or {}
        paths = config.get("paths", {})
        runtime = config.get("runtime", {})
        default_runtime = conv_defaults.get("runtime_defaults", {})
        default_debug = conv_defaults.get("debug_defaults", {})
        enabled = state.get("has_device", False)

        self.reload_button.setEnabled(enabled or bool(route_config) or bool(conv_defaults))
        self.save_button.setEnabled(enabled or bool(route_config) or bool(conv_defaults))
        is_dirty = (
            state.get("config_dirty")
            or state.get("route_dirty")
            or state.get("conv_defaults_dirty")
        )
        self.save_button.setText("保存配置 *" if is_dirty else "保存配置")

        for key, field in self.default_runtime_fields.items():
            field.blockSignals(True)
            field.setText(str(default_runtime.get(key, "")))
            field.blockSignals(False)
        for key, field in self.default_debug_fields.items():
            field.blockSignals(True)
            value = "True" if default_debug.get(key, False) else "False"
            field.setCurrentText(value)
            field.blockSignals(False)

        for key, field in self.path_fields.items():
            field.blockSignals(True)
            field.setText(str(paths.get(key, "")))
            field.blockSignals(False)
        for key, field in self.runtime_fields.items():
            field.blockSignals(True)
            field.setText(str(runtime.get(key, "")))
            field.blockSignals(False)
            field.setEnabled(enabled)

        if route_config:
            current_count = self.route_table.rowCount()
            new_count = len(route_config.get("command_rows", []))
            if current_count != new_count or not self.route_parse_boxes:
                self._rebuild_route_table(route_config)
                return

            for row in route_config.get("command_rows", []):
                command = row["command"]
                parse_box = self.route_parse_boxes.get(command)
                symbol_box = self.route_symbol_boxes.get(command)
                if parse_box is None or symbol_box is None:
                    self._rebuild_route_table(route_config)
                    return
                parse_box.blockSignals(True)
                parse_box.setChecked(bool(row.get("llm_parse", False)))
                parse_box.blockSignals(False)
                symbol_box.blockSignals(True)
                symbol_box.setChecked(bool(row.get("llm_symbol", False)))
                symbol_box.blockSignals(False)

class PipelinePanel(QWidget):
    def __init__(self, controller: FrontendController) -> None:
        super().__init__()
        self.controller = controller

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["llm", "ply"])
        self.mode_combo.currentTextChanged.connect(self.controller.set_mode)

        self.step_combo = QComboBox()
        for step in [1, 2, 3, 4, 5, 9]:
            self.step_combo.addItem(f"Step {step}", step)

        self.run_step_button = QPushButton("运行单步")
        self.run_all_button = QPushButton("运行全流程")
        self.refresh_artifacts_button = QPushButton("刷新文件")
        self.clear_log_button = QPushButton("清空日志")
        self.full_log_button = QPushButton("完整日志")
        self.full_log_window: QDialog | None = None
        self.run_step_button.clicked.connect(self._run_step)
        self.run_all_button.clicked.connect(self.controller.run_pipeline)
        self.refresh_artifacts_button.clicked.connect(self.controller.refresh_artifacts)
        self.clear_log_button.clicked.connect(self.controller.clear_logs)
        self.full_log_button.clicked.connect(self._show_full_log)

        self.result_view = QTextEdit()
        self.result_view.setObjectName("monoTextView")
        self.result_view.setReadOnly(True)
        self.result_search = TextSearchBar(self.result_view)
        self.result_view.setPlaceholderText("当前尚无运行结果。")
        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("monoTextView")
        self.log_view.setReadOnly(True)
        self.log_search = TextSearchBar(self.log_view)
        self.log_view.setPlaceholderText("当前尚无运行日志。")
        self.log_view.setPlainText(self.controller.get_logs())
        self.controller.log_message.connect(self._handle_log_message)

        toolbar_frame = QFrame()
        toolbar_frame.setObjectName("toolbarFrame")
        toolbar_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        controls = QHBoxLayout()
        controls.setContentsMargins(14, 12, 14, 12)
        controls.setSpacing(10)
        controls.addWidget(QLabel("模式"))
        controls.addWidget(self.mode_combo)
        controls.addWidget(QLabel("步骤"))
        controls.addWidget(self.step_combo)
        controls.addWidget(self.run_step_button)
        controls.addWidget(self.run_all_button)
        controls.addWidget(self.refresh_artifacts_button)
        controls.addWidget(self.clear_log_button)
        controls.addWidget(self.full_log_button)
        controls.addStretch(1)
        toolbar_frame.setLayout(controls)

        result_frame = QFrame()
        result_frame.setObjectName("resultFrame")
        result_layout = QVBoxLayout(result_frame)
        result_layout.setContentsMargins(14, 14, 14, 14)
        result_layout.setSpacing(10)
        result_caption = QLabel("最近一次运行结果")
        result_caption.setObjectName("panelHeading")
        result_layout.addWidget(result_caption)
        result_layout.addWidget(self.result_search)
        result_layout.addWidget(self.result_view)

        log_frame = QFrame()
        log_frame.setObjectName("resultFrame")
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(14, 14, 14, 14)
        log_layout.setSpacing(10)
        log_caption = QLabel("运行日志")
        log_caption.setObjectName("panelHeading")
        log_layout.addWidget(log_caption)
        log_layout.addWidget(self.log_search)
        log_layout.addWidget(self.log_view)

        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(14)
        content.addWidget(result_frame, 4)
        content.addWidget(log_frame, 5)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)
        root.addWidget(toolbar_frame)
        root.addLayout(content, 1)

    def _run_step(self) -> None:
        step = self.step_combo.currentData()
        self.controller.run_step(int(step))

    def _handle_log_message(self, message: str) -> None:
        if message == "":
            self.log_view.clear()
            if self.full_log_window is not None:
                dialog_view = self.full_log_window.findChild(QPlainTextEdit, "fullLogView")
                if dialog_view is not None:
                    dialog_view.clear()
            return
        cursor = self.log_view.textCursor()
        cursor.movePosition(QTextCursor.End)
        if self.log_view.toPlainText():
            cursor.insertText("\n")
        cursor.insertText(message)
        self.log_view.setTextCursor(cursor)
        self.log_view.ensureCursorVisible()
        if self.full_log_window is not None and self.full_log_window.isVisible():
            dialog_view = self.full_log_window.findChild(QPlainTextEdit, "fullLogView")
            if dialog_view is not None:
                dialog_cursor = dialog_view.textCursor()
                dialog_cursor.movePosition(QTextCursor.End)
                if dialog_view.toPlainText():
                    dialog_cursor.insertText("\n")
                dialog_cursor.insertText(message)
                dialog_view.setTextCursor(dialog_cursor)
                dialog_view.ensureCursorVisible()

    def _show_full_log(self) -> None:
        if self.full_log_window is None:
            dialog = QDialog(self)
            dialog.setWindowTitle("完整日志")
            dialog.resize(1160, 760)
            dialog_view = QPlainTextEdit()
            dialog_view.setObjectName("fullLogView")
            dialog_view.setReadOnly(True)
            dialog_view.setPlainText(self.controller.get_logs())
            dialog_search = TextSearchBar(dialog_view)
            close_button = QPushButton("关闭")
            close_button.clicked.connect(dialog.close)
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(14, 14, 14, 14)
            layout.setSpacing(10)
            layout.addWidget(dialog_search)
            layout.addWidget(dialog_view)
            layout.addWidget(close_button, 0, Qt.AlignRight)
            self.full_log_window = dialog
        else:
            dialog_view = self.full_log_window.findChild(QPlainTextEdit, "fullLogView")
            if dialog_view is not None:
                dialog_view.setPlainText(self.controller.get_logs())
        self.full_log_window.show()
        self.full_log_window.raise_()
        self.full_log_window.activateWindow()

    def update_view(self, state: dict[str, Any]) -> None:
        mode = state.get("mode", "llm")
        self.mode_combo.blockSignals(True)
        self.mode_combo.setCurrentText(mode)
        self.mode_combo.blockSignals(False)

        supports_step = mode == "llm"
        can_run = state.get("can_run", False)
        is_running = state.get("is_running", False)
        self.run_step_button.setEnabled(can_run and supports_step and not is_running)
        self.run_all_button.setEnabled(can_run and not is_running)
        self.step_combo.setEnabled(supports_step and not is_running)
        self.clear_log_button.setEnabled(bool(self.log_view.toPlainText()) or is_running)
        self.full_log_button.setEnabled(bool(self.log_view.toPlainText()) or is_running)

        result = state.get("last_run_result")
        if result:
            if result.get("ok") is False and "error" in result:
                self.result_view.setPlainText(result["error"])
            else:
                self.result_view.setPlainText(pretty_json(result))
        else:
            self.result_view.clear()


class ArtifactPanel(QWidget):
    def __init__(self, controller: FrontendController) -> None:
        super().__init__()
        self.controller = controller

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._open_selected)
        self.list_widget.setMinimumWidth(260)
        self.list_widget.setMaximumWidth(360)

        self.path_label = QLabel("未打开文件")
        self.kind_label = QLabel("-")
        self.editor = QPlainTextEdit()
        self.editor.setObjectName("monoTextView")
        self.editor.textChanged.connect(self._on_text_changed)
        self.search_bar = TextSearchBar(self.editor)

        self.refresh_button = QPushButton("刷新列表")
        self.open_button = QPushButton("打开")
        self.save_button = QPushButton("保存")
        self.validate_button = QPushButton("校验并保存")
        self.refresh_button.clicked.connect(self.controller.refresh_artifacts)
        self.open_button.clicked.connect(self._open_selected)
        self.save_button.clicked.connect(lambda: self.controller.save_opened_artifact(validate=False))
        self.validate_button.clicked.connect(lambda: self.controller.save_opened_artifact(validate=True))

        left = QVBoxLayout()
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(10)
        left.addWidget(self.refresh_button)
        left.addWidget(self.list_widget)
        left_widget = QWidget()
        left_widget.setLayout(left)

        right_top = QFormLayout()
        right_top.addRow("文件路径", self.path_label)
        right_top.addRow("文件类型", self.kind_label)

        right_buttons = QHBoxLayout()
        right_buttons.addWidget(self.open_button)
        right_buttons.addWidget(self.save_button)
        right_buttons.addWidget(self.validate_button)
        right_buttons.addStretch(1)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(10)
        right.addLayout(right_top)
        right.addLayout(right_buttons)
        right.addWidget(self.search_bar)
        right.addWidget(self.editor)
        right_widget = QWidget()
        right_widget.setLayout(right)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)
        root.addWidget(left_widget, 2)
        root.addWidget(right_widget, 5)

    def _open_selected(self, _item: QListWidgetItem | None = None) -> None:
        item = self.list_widget.currentItem()
        if not item:
            return
        path = item.data(Qt.UserRole)
        self.controller.open_artifact(path)

    def _on_text_changed(self) -> None:
        if self.controller.state.opened_artifact:
            self.controller.update_artifact_content(self.editor.toPlainText())

    def update_view(self, state: dict[str, Any]) -> None:
        artifacts = state.get("artifacts", [])
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for artifact in artifacts:
            exists = "存在" if artifact["exists"] else "缺失"
            item = QListWidgetItem(self._format_item_label(artifact, exists))
            item.setData(Qt.UserRole, artifact["path"])
            item.setToolTip(artifact["path"])
            self.list_widget.addItem(item)
        self.list_widget.blockSignals(False)

        opened = state.get("opened_artifact")
        self.path_label.setText(opened["path"] if opened else "未打开文件")
        self.path_label.setToolTip(opened["path"] if opened else "")
        self.kind_label.setText(opened["kind"] if opened else "-")

        incoming_content = state.get("artifact_content", "")
        current_content = self.editor.toPlainText()
        if current_content != incoming_content:
            cursor = self.editor.textCursor()
            position = cursor.position()
            anchor = cursor.anchor()
            self.editor.blockSignals(True)
            self.editor.setPlainText(incoming_content)
            self.editor.blockSignals(False)

            next_cursor = self.editor.textCursor()
            max_pos = len(incoming_content)
            next_cursor.setPosition(min(anchor, max_pos))
            if anchor != position:
                next_cursor.setPosition(min(position, max_pos), QTextCursor.KeepAnchor)
            else:
                next_cursor.setPosition(min(position, max_pos))
            self.editor.setTextCursor(next_cursor)

        enabled = opened is not None
        self.open_button.setEnabled(bool(artifacts))
        self.save_button.setEnabled(enabled)
        self.validate_button.setEnabled(enabled)
        self.save_button.setText("保存 *" if state.get("artifact_dirty") else "保存")

    def _format_item_label(self, artifact: dict[str, Any], exists: str) -> str:
        if artifact["key"] == "source_m2d":
            return f"源文件 [{exists}]"
        return f"{artifact['key']} [{exists}]"


class SimulationPanel(QWidget):
    def __init__(self, controller: FrontendController) -> None:
        super().__init__()
        self.controller = controller

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._open_selected)
        self.list_widget.setMinimumWidth(260)
        self.list_widget.setMaximumWidth(360)

        self.path_label = QLabel("未打开结果文件")
        self.kind_label = QLabel("-")
        self.editor = QPlainTextEdit()
        self.editor.setObjectName("monoTextView")
        self.editor.textChanged.connect(self._on_text_changed)
        self.search_bar = TextSearchBar(self.editor)

        self.refresh_button = QPushButton("刷新结果文件")
        self.open_button = QPushButton("打开")
        self.save_button = QPushButton("保存")
        self.refresh_button.clicked.connect(self.controller.refresh_simulation_files)
        self.open_button.clicked.connect(self._open_selected)
        self.save_button.clicked.connect(self.controller.save_opened_simulation_file)

        left = QVBoxLayout()
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(10)
        left.addWidget(self.refresh_button)
        left.addWidget(self.list_widget)
        left_widget = QWidget()
        left_widget.setLayout(left)

        right_top = QFormLayout()
        right_top.addRow("文件路径", self.path_label)
        right_top.addRow("文件类型", self.kind_label)

        right_buttons = QHBoxLayout()
        right_buttons.addWidget(self.open_button)
        right_buttons.addWidget(self.save_button)
        right_buttons.addStretch(1)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(10)
        right.addLayout(right_top)
        right.addLayout(right_buttons)
        right.addWidget(self.search_bar)
        right.addWidget(self.editor)
        right_widget = QWidget()
        right_widget.setLayout(right)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)
        root.addWidget(left_widget, 2)
        root.addWidget(right_widget, 5)

    def _open_selected(self, _item: QListWidgetItem | None = None) -> None:
        item = self.list_widget.currentItem()
        if not item:
            return
        path = item.data(Qt.UserRole)
        self.controller.open_simulation_file(path)

    def _on_text_changed(self) -> None:
        if self.controller.state.opened_simulation_file:
            self.controller.update_simulation_content(self.editor.toPlainText())

    def update_view(self, state: dict[str, Any]) -> None:
        simulation_files = state.get("simulation_files", [])
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for file_info in simulation_files:
            item = QListWidgetItem(file_info["key"])
            item.setData(Qt.UserRole, file_info["path"])
            item.setToolTip(file_info["path"])
            self.list_widget.addItem(item)
        self.list_widget.blockSignals(False)

        opened = state.get("opened_simulation_file")
        self.path_label.setText(opened["path"] if opened else "未打开结果文件")
        self.path_label.setToolTip(opened["path"] if opened else "")
        self.kind_label.setText(opened["kind"] if opened else "-")

        incoming_content = state.get("simulation_content", "")
        current_content = self.editor.toPlainText()
        if current_content != incoming_content:
            cursor = self.editor.textCursor()
            position = cursor.position()
            anchor = cursor.anchor()
            self.editor.blockSignals(True)
            self.editor.setPlainText(incoming_content)
            self.editor.blockSignals(False)

            next_cursor = self.editor.textCursor()
            max_pos = len(incoming_content)
            next_cursor.setPosition(min(anchor, max_pos))
            if anchor != position:
                next_cursor.setPosition(min(position, max_pos), QTextCursor.KeepAnchor)
            else:
                next_cursor.setPosition(min(position, max_pos))
            self.editor.setTextCursor(next_cursor)

        enabled = opened is not None
        self.open_button.setEnabled(bool(simulation_files))
        self.save_button.setEnabled(enabled)
        self.save_button.setText("保存 *" if state.get("simulation_dirty") else "保存")


class GeometryPreviewPanel(QWidget):
    def __init__(self, controller: FrontendController) -> None:
        super().__init__()
        self.controller = controller
        self.current_pixmap = QPixmap()
        self.ratio_options = self._build_ratio_options()
        self.resolution_options = [
            ("1x", 1.0),
            ("1.5x", 1.5),
            ("2x", 2.0),
            ("3x", 3.0),
            ("4x", 4.0),
            ("5x", 5.0),
            ("6x", 6.0)
        ]

        self.source_label = QLabel("未读取中间结果")
        self.ratio_label = QLabel("横纵比")
        self.ratio_combo = FocusComboBox()
        self.ratio_combo.setEditable(True)
        self.ratio_combo.setMinimumWidth(140)
        for label, value in self.ratio_options:
            self.ratio_combo.addItem(label, value)
        self.ratio_combo.currentIndexChanged.connect(self._on_ratio_combo_changed)
        self.ratio_combo.lineEdit().editingFinished.connect(self._on_ratio_input_changed)
        self.resolution_label = QLabel("分辨率：1x")
        self.resolution_combo = FocusComboBox()
        self.resolution_combo.setMinimumWidth(110)
        for label, value in self.resolution_options:
            self.resolution_combo.addItem(label, value)
        self.resolution_combo.currentIndexChanged.connect(self._on_resolution_changed)

        self.load_button = QPushButton("读取中间结果")
        self.draw_pec_button = QPushButton("画 PEC")
        self.draw_void_button = QPushButton("画 VOID")
        self.reset_zoom_button = QPushButton("适应")
        self.clear_button = QPushButton("清空显示")
        self.load_button.clicked.connect(self.controller.refresh_geometry_area_result)
        self.draw_pec_button.clicked.connect(lambda: self.controller.generate_geometry_preview("pec"))
        self.draw_void_button.clicked.connect(lambda: self.controller.generate_geometry_preview("void"))
        self.reset_zoom_button.clicked.connect(self._reset_zoom)
        self.clear_button.clicked.connect(self.controller.clear_geometry_preview)
        self.image_placeholder = QLabel("尚未生成图形预览。")
        self.image_placeholder.setAlignment(Qt.AlignCenter)
        self.image_placeholder.setMinimumHeight(520)
        self.image_placeholder.setObjectName("previewCanvas")
        self.image_placeholder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_view = GraphicsImageView()
        self.image_view.setObjectName("previewCanvas")
        self.image_view.setMinimumHeight(520)
        self.image_view.hide()

        top = QFormLayout()
        top.addRow("中间文件", self.source_label)

        actions = QHBoxLayout()
        actions.addWidget(self.load_button)
        actions.addWidget(self.draw_pec_button)
        actions.addWidget(self.draw_void_button)
        actions.addWidget(self.reset_zoom_button)
        actions.addWidget(self.clear_button)
        actions.addStretch(1)

        ratio_row = QHBoxLayout()
        ratio_row.setContentsMargins(0, 0, 0, 0)
        ratio_row.setSpacing(10)
        ratio_row.addWidget(QLabel("横纵比"))
        ratio_row.addWidget(self.ratio_combo)
        ratio_row.addWidget(self.ratio_label)
        ratio_row.addSpacing(12)
        ratio_row.addWidget(QLabel("分辨率"))
        ratio_row.addWidget(self.resolution_combo)
        ratio_row.addWidget(self.resolution_label)
        ratio_row.addStretch(1)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)
        root.addLayout(top)
        root.addLayout(actions)
        root.addLayout(ratio_row)
        root.addWidget(self.image_placeholder, 1)
        root.addWidget(self.image_view, 1)

    def _build_ratio_options(self) -> list[tuple[str, float]]:
        options: list[tuple[str, float]] = []
        value = 20.0
        while value >= 1.0:
            options.append((f"{value:g}", value))
            value -= 0.5
        denominator = 2.0
        while denominator <= 20.0:
            options.append((f"1/{denominator:g}", 1.0 / denominator))
            denominator += 0.5
        return options

    def _format_ratio(self, ratio: float) -> str:
        for label, value in self.ratio_options:
            if abs(value - ratio) < 1e-9:
                return label
        return f"{ratio:g}"

    def _apply_ratio(self, ratio: float) -> None:
        safe_ratio = min(max(float(ratio), 0.001), 1000.0)
        self.ratio_combo.blockSignals(True)
        self.ratio_combo.setCurrentText(self._format_ratio(safe_ratio))
        self.ratio_combo.blockSignals(False)
        self.ratio_label.setText(f"横纵比：{safe_ratio:g}")
        self.controller.set_geometry_aspect_ratio(safe_ratio)

    def _parse_ratio_text(self, text: str) -> float:
        raw = text.strip()
        if "/" in raw:
            left, right = raw.split("/", 1)
            numerator = float(left.strip())
            denominator = float(right.strip())
            if denominator == 0:
                raise ValueError("ratio denominator cannot be zero")
            return numerator / denominator
        return float(raw)

    def _on_ratio_combo_changed(self, _index: int) -> None:
        data = self.ratio_combo.currentData()
        if data is None:
            return
        self._apply_ratio(float(data))

    def _on_ratio_input_changed(self) -> None:
        try:
            ratio = self._parse_ratio_text(self.ratio_combo.currentText())
        except ValueError:
            ratio = self.controller.state.geometry_aspect_ratio
        self._apply_ratio(ratio)

    def _on_resolution_changed(self, _index: int) -> None:
        data = self.resolution_combo.currentData()
        if data is None:
            return
        scale = float(data)
        self.resolution_label.setText(f"分辨率：{scale:g}x")
        self.controller.set_geometry_resolution_scale(scale)

    def _reset_zoom(self) -> None:
        if self.current_pixmap.isNull():
            self.image_placeholder.show()
            self.image_view.hide()
            return
        self.image_view.fit_image()

    def _apply_pixmap(self, fit_view: bool = False) -> None:
        if self.current_pixmap.isNull():
            self.image_view.clear_pixmap()
            self.image_view.hide()
            self.image_placeholder.show()
            return
        self.image_placeholder.hide()
        self.image_view.show()
        self.image_view.set_pixmap(self.current_pixmap)
        if fit_view:
            self.image_view.fit_image()

    def update_view(self, state: dict[str, Any]) -> None:
        source_path = state.get("geometry_source_path", "")
        preview_path = state.get("geometry_preview_path", "")
        aspect_ratio = float(state.get("geometry_aspect_ratio", 1.0) or 1.0)
        resolution_scale = float(state.get("geometry_resolution_scale", 1.0) or 1.0)
        self.source_label.setText(source_path or "未读取中间结果")
        self.source_label.setToolTip(source_path)
        self.ratio_combo.blockSignals(True)
        self.ratio_combo.setCurrentText(self._format_ratio(aspect_ratio))
        self.ratio_combo.blockSignals(False)
        self.ratio_label.setText(f"横纵比：{aspect_ratio:g}")
        resolution_index = 0
        for index, (_label, value) in enumerate(self.resolution_options):
            if abs(value - resolution_scale) < 1e-9:
                resolution_index = index
                break
        self.resolution_combo.blockSignals(True)
        self.resolution_combo.setCurrentIndex(resolution_index)
        self.resolution_combo.blockSignals(False)
        self.resolution_label.setText(f"分辨率：{resolution_scale:g}x")
        if preview_path and Path(preview_path).exists():
            pixmap = QPixmap(preview_path)
            if not pixmap.isNull():
                is_new_preview = preview_path != self.image_view.property("previewPath")
                if preview_path != self.image_view.property("previewPath"):
                    self.image_view.setProperty("previewPath", preview_path)
                self.current_pixmap = pixmap
                self._apply_pixmap(fit_view=is_new_preview)
                return
        self.current_pixmap = QPixmap()
        self.image_view.setProperty("previewPath", "")
        self._apply_pixmap()


class PointSetPanel(QWidget):
    def __init__(self, controller: FrontendController) -> None:
        super().__init__()
        self.controller = controller

        self.path_label = QLabel("未生成点集文件")
        self.generate_button = QPushButton("生成点集")
        self.generate_button.clicked.connect(self.controller.generate_pointset_file)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Z", "Y", "X"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)

        top = QFormLayout()
        top.addRow("点集文件", self.path_label)

        actions = QHBoxLayout()
        actions.addWidget(self.generate_button)
        actions.addStretch(1)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)
        root.addLayout(top)
        root.addLayout(actions)
        root.addWidget(self.table, 1)

    def update_view(self, state: dict[str, Any]) -> None:
        pointset_path = state.get("pointset_path", "")
        pointset_rows = state.get("pointset_rows", [])
        self.path_label.setText(pointset_path or "未生成点集文件")
        self.path_label.setToolTip(pointset_path)
        self.table.setRowCount(len(pointset_rows))
        for row_index, row in enumerate(pointset_rows):
            for col_index in range(3):
                value = row[col_index] if col_index < len(row) else ""
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_index, col_index, item)


class TranslationResultPanel(QWidget):
    def __init__(self, controller: FrontendController) -> None:
        super().__init__()
        self.current_subpanel = "result_files"

        self.result_files_button = QPushButton("结果文件")
        self.geometry_button = QPushButton("图形预览")
        self.pointset_button = QPushButton("点集")
        self.result_files_button.setCheckable(True)
        self.geometry_button.setCheckable(True)
        self.pointset_button.setCheckable(True)
        self.result_files_button.clicked.connect(lambda: self._set_subpanel("result_files"))
        self.geometry_button.clicked.connect(lambda: self._set_subpanel("geometry_preview"))
        self.pointset_button.clicked.connect(lambda: self._set_subpanel("pointset"))

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setSpacing(10)
        toolbar.addWidget(self.result_files_button)
        toolbar.addWidget(self.geometry_button)
        toolbar.addWidget(self.pointset_button)
        toolbar.addStretch(1)

        self.result_files_panel = SimulationPanel(controller)
        self.geometry_panel = GeometryPreviewPanel(controller)
        self.pointset_panel = PointSetPanel(controller)
        self.stacked = QStackedWidget()
        self.stacked.addWidget(self.result_files_panel)
        self.stacked.addWidget(self.geometry_panel)
        self.stacked.addWidget(self.pointset_panel)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)
        root.addLayout(toolbar)
        root.addWidget(self.stacked, 1)
        self._set_subpanel("result_files")

    def _set_subpanel(self, subpanel: str) -> None:
        self.current_subpanel = subpanel
        self.result_files_button.setChecked(subpanel == "result_files")
        self.geometry_button.setChecked(subpanel == "geometry_preview")
        self.pointset_button.setChecked(subpanel == "pointset")
        if subpanel == "result_files":
            self.stacked.setCurrentIndex(0)
        elif subpanel == "geometry_preview":
            self.stacked.setCurrentIndex(1)
        else:
            self.stacked.setCurrentIndex(2)
            self.pointset_panel.controller.load_pointset_file()

    def update_view(self, state: dict[str, Any]) -> None:
        self.result_files_panel.update_view(state)
        self.geometry_panel.update_view(state)
        self.pointset_panel.update_view(state)


class LLMConfigPanel(QWidget):
    def __init__(self, controller: FrontendController) -> None:
        super().__init__()
        self.controller = controller
        self.current_category = "parse"
        self.current_scope = "system"
        self.current_group = ""
        self.current_key = ""

        self.category_combo = QComboBox()
        self.category_combo.addItem("解析提示词", "parse")
        self.category_combo.addItem("符号处理提示词", "symbol")
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)

        self.prompt_type_list = QListWidget()
        self.prompt_type_list.itemClicked.connect(self._open_prompt_type_selected)
        self.prompt_type_list.setMinimumWidth(220)
        self.prompt_type_list.setMaximumWidth(280)

        self.command_list = QListWidget()
        self.command_list.itemClicked.connect(self._on_command_selected)
        self.command_list.setMinimumWidth(280)
        self.command_list.setMaximumWidth(380)

        self.path_label = QLabel("未加载 LLM 提示词配置")
        self.key_label = QLabel("-")
        self.editor = QPlainTextEdit()
        self.editor.setObjectName("monoTextView")
        self.editor.textChanged.connect(self._on_text_changed)
        self.search_bar = TextSearchBar(self.editor)

        self.refresh_button = QPushButton("读取 LLM 配置")
        self.save_button = QPushButton("保存 LLM 配置")
        self.refresh_button.clicked.connect(self.controller.reload_config)
        self.save_button.clicked.connect(self._save)

        left = QVBoxLayout()
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(10)
        left.addWidget(QLabel("一级分类"))
        left.addWidget(self.category_combo)
        left.addWidget(QLabel("提示词选择"))
        left.addWidget(self.prompt_type_list, 2)
        self.command_label = QLabel("命令")
        left.addWidget(self.command_label)
        left.addWidget(self.command_list, 3)
        left_widget = QWidget()
        left_widget.setLayout(left)

        right_top = QFormLayout()
        right_top.addRow("配置文件", self.path_label)
        right_top.addRow("当前条目", self.key_label)

        right_buttons = QHBoxLayout()
        right_buttons.addWidget(self.refresh_button)
        right_buttons.addWidget(self.save_button)
        right_buttons.addStretch(1)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(10)
        right.addLayout(right_top)
        right.addLayout(right_buttons)
        right.addWidget(self.search_bar)
        right.addWidget(self.editor)
        right_widget = QWidget()
        right_widget.setLayout(right)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)
        root.addWidget(left_widget, 2)
        root.addWidget(right_widget, 6)

    def _category_groups(self) -> tuple[tuple[str, str], tuple[str, str], str]:
        if self.current_category == "symbol":
            return (
                ("m2u_task_dict", "mcl_midconv"),
                ("mcl2mid_mclcontext_dict", "mcl2mid_json_dict"),
                "命令上下文提示词",
            )
        return (
            ("m2u_task_dict", "parse"),
            ("parse_cmd_dict", "json_dict"),
            "命令解析提示词",
        )

    def _on_category_changed(self) -> None:
        self.current_category = str(self.category_combo.currentData() or "parse")
        self.current_scope = "system"
        self.current_group = ""
        self.current_key = ""
        self._refresh_navigation()

    def _set_target_selection(self, widget: QListWidget, target: tuple[str, str]) -> bool:
        for index in range(widget.count()):
            item = widget.item(index)
            if item.data(Qt.UserRole) == target:
                widget.setCurrentItem(item)
                return True
        return False

    def _set_list_selection(self, widget: QListWidget, target: Any) -> bool:
        for index in range(widget.count()):
            item = widget.item(index)
            if item.data(Qt.UserRole) == target:
                widget.setCurrentItem(item)
                return True
        return False

    def _current_prompt_target(self) -> tuple[str, str]:
        if not self.current_group:
            return ("", "")
        if self.current_scope == "command":
            return (self.current_group, "__command__")
        return (self.current_group, self.current_key)

    def _refresh_navigation(self) -> None:
        prompt_config = self.controller.state.prompt_config or {}
        system_target, command_groups, command_label = self._category_groups()
        parse_group, json_group = command_groups

        previous_type = self._current_prompt_target()
        previous_command = self.command_list.currentItem().data(Qt.UserRole) if self.command_list.currentItem() else ""

        self.prompt_type_list.blockSignals(True)
        self.prompt_type_list.clear()
        prompt_items = [
            ("系统提示词", system_target),
            (command_label, (parse_group, "__command__")),
            ("JSON输出提示词", (json_group, "__command__")),
        ]
        for label, target in prompt_items:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, target)
            self.prompt_type_list.addItem(item)
        self.prompt_type_list.blockSignals(False)

        command_names: set[str] = set()
        for group_name in command_groups:
            command_names.update(prompt_config.get(group_name, {}).keys())

        self.command_list.blockSignals(True)
        self.command_list.clear()
        for command_name in sorted(command_names):
            item = QListWidgetItem(command_name)
            item.setData(Qt.UserRole, command_name)
            self.command_list.addItem(item)
        self.command_list.blockSignals(False)

        selected_command = previous_command if previous_command in command_names else ""
        if not selected_command and command_names:
            selected_command = sorted(command_names)[0]
        if selected_command:
            self._set_list_selection(self.command_list, selected_command)
        else:
            self.command_list.clearSelection()

        if not self._set_target_selection(self.prompt_type_list, previous_type) and self.prompt_type_list.count():
            self.prompt_type_list.setCurrentRow(0)

        if self.prompt_type_list.currentItem():
            self._open_prompt_type_selected(self.prompt_type_list.currentItem())
        else:
            self.current_group = ""
            self.current_key = ""
            self._update_editor()

    def _open_prompt_type_selected(self, _item: QListWidgetItem | None = None) -> None:
        item = self.prompt_type_list.currentItem()
        if not item:
            return
        self.current_group, key_marker = item.data(Qt.UserRole)
        if key_marker == "__command__":
            self.current_scope = "command"
            self.command_label.setVisible(True)
            self.command_list.setVisible(True)
            current_command = self.command_list.currentItem().data(Qt.UserRole) if self.command_list.currentItem() else ""
            self.current_key = str(current_command or "")
        else:
            self.current_scope = "system"
            self.command_label.setVisible(False)
            self.command_list.setVisible(False)
            self.current_key = key_marker
        self._update_editor()

    def _on_command_selected(self, _item: QListWidgetItem | None = None) -> None:
        if self.current_scope != "command":
            return
        item = self.command_list.currentItem()
        if not item:
            self.current_key = ""
        else:
            self.current_key = item.data(Qt.UserRole)
        self._update_editor()

    def _update_editor(self) -> None:
        prompt_config = self.controller.state.prompt_config or {}
        content = prompt_config.get(self.current_group, {}).get(self.current_key, "")
        self.key_label.setText(self.current_key or "-")
        current_content = self.editor.toPlainText()
        if current_content != content:
            cursor = self.editor.textCursor()
            position = cursor.position()
            anchor = cursor.anchor()
            self.editor.blockSignals(True)
            self.editor.setPlainText(content)
            self.editor.blockSignals(False)
            next_cursor = self.editor.textCursor()
            max_pos = len(content)
            next_cursor.setPosition(min(anchor, max_pos))
            if anchor != position:
                next_cursor.setPosition(min(position, max_pos), QTextCursor.KeepAnchor)
            else:
                next_cursor.setPosition(min(position, max_pos))
            self.editor.setTextCursor(next_cursor)

    def _on_text_changed(self) -> None:
        if not self.current_group or not self.current_key:
            return
        prompt_config = deepcopy_or_empty(self.controller.state.prompt_config)
        prompt_config.setdefault(self.current_group, {})
        prompt_config[self.current_group][self.current_key] = self.editor.toPlainText()
        self.controller.update_prompt_config(prompt_config)

    def _save(self) -> None:
        prompt_config = deepcopy_or_empty(self.controller.state.prompt_config)
        self.controller.save_config(None, None, None, prompt_config)

    def update_view(self, state: dict[str, Any]) -> None:
        prompt_config = state.get("prompt_config") or {}
        prompt_path = str(self.controller.config_service.get_prompt_config_path())
        self.path_label.setText(prompt_path if prompt_config else "未加载 LLM 提示词配置")
        self.path_label.setToolTip(prompt_path if prompt_config else "")
        selected_index = 1 if self.current_category == "symbol" else 0
        self.category_combo.blockSignals(True)
        self.category_combo.setCurrentIndex(selected_index)
        self.category_combo.blockSignals(False)
        self.command_label.setVisible(self.current_scope == "command")
        self.command_list.setVisible(self.current_scope == "command")
        self._refresh_navigation()
        self.save_button.setEnabled(bool(prompt_config))
        self.save_button.setText("保存 LLM 配置 *" if state.get("prompt_dirty") else "保存 LLM 配置")


class MainWindow(QMainWindow):
    PANEL_ORDER = {
        "device": 0,
        "config": 1,
        "pipeline": 2,
        "file": 3,
        "translation_result": 4,
        "simulation": 4,
        "llm_config": 5,
    }

    def __init__(self, controller: FrontendController) -> None:
        super().__init__()
        self.controller = controller
        self.setWindowTitle("M2U Local Workbench")
        self.resize(1480, 920)
        self.setMinimumSize(1200, 760)

        self.status_cards = {
            "input": KeyValueCard("输入文件"),
            "device": KeyValueCard("当前器件"),
            "mode": KeyValueCard("模式"),
            "status": KeyValueCard("状态"),
        }

        self.sidebar_buttons: dict[str, QPushButton] = {}
        sidebar = self._build_sidebar()
        top_bar = self._build_top_bar()
        self.stacked = self._build_panels()
        self.message_label = QLabel("准备就绪。")
        self.message_label.setObjectName("messageBar")
        self.message_label.setWordWrap(True)
        self.message_label.setMinimumHeight(40)
        self.message_label.setMaximumHeight(52)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(14)
        body.addWidget(sidebar, 0)
        body.addWidget(self.stacked, 1)

        root = QVBoxLayout()
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(14)
        root.addWidget(top_bar)
        root.addLayout(body, 1)
        root.addWidget(self.message_label)

        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)
        self._apply_style()

        self.controller.state_changed.connect(self.update_view)
        self.controller.message_changed.connect(self._show_message)
        self.controller.initialize()

    def _build_top_bar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("topBar")
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        frame.setMaximumHeight(98)
        layout = QGridLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setHorizontalSpacing(12)
        layout.setColumnStretch(0, 5)
        layout.setColumnStretch(1, 2)
        layout.setColumnStretch(2, 1)
        layout.setColumnStretch(3, 1)

        layout.addWidget(self.status_cards["input"], 0, 0)
        layout.addWidget(self.status_cards["device"], 0, 1)
        layout.addWidget(self.status_cards["mode"], 0, 2)
        layout.addWidget(self.status_cards["status"], 0, 3)
        return frame

    def _build_sidebar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("sidebar")
        frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        frame.setMinimumWidth(220)
        frame.setMaximumWidth(260)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        mapping = [
            ("\u5668\u4ef6", "device"),
            ("\u914d\u7f6e", "config"),
            ("\u8fd0\u884c", "pipeline"),
            ("\u6587\u4ef6", "file"),
            ("\u8f6c\u8bd1\u7ed3\u679c", "translation_result"),
            ("LLM\u914d\u7f6e", "llm_config"),
        ]
        for label, panel in mapping:
            button = QPushButton(label)
            button.clicked.connect(lambda _checked=False, p=panel: self.controller.set_active_panel(p))
            button.setCheckable(True)
            button.setMinimumHeight(52)
            self.sidebar_buttons[panel] = button
            layout.addWidget(button)
        layout.addStretch(1)
        return frame

    def _build_panels(self) -> QStackedWidget:
        self.device_panel = DevicePanel(self.controller)
        self.config_panel = ConfigPanel(self.controller)
        self.pipeline_panel = PipelinePanel(self.controller)
        self.artifact_panel = ArtifactPanel(self.controller)
        self.translation_result_panel = TranslationResultPanel(self.controller)
        self.llm_config_panel = LLMConfigPanel(self.controller)

        stacked = QStackedWidget()
        stacked.addWidget(self.device_panel)
        stacked.addWidget(self.config_panel)
        stacked.addWidget(self.pipeline_panel)
        stacked.addWidget(self.artifact_panel)
        stacked.addWidget(self.translation_result_panel)
        stacked.addWidget(self.llm_config_panel)
        return stacked

    def update_view(self, state: dict[str, Any]) -> None:
        current_device = state.get("current_device") or {}
        self.status_cards["input"].value_label.setText(path_tail(current_device.get("input_file", "-")))
        self.status_cards["input"].value_label.setToolTip(current_device.get("input_file", "-"))
        self.status_cards["device"].value_label.setText(current_device.get("device_name", "-"))
        self.status_cards["mode"].value_label.setText(state.get("mode", "-"))
        self.status_cards["status"].value_label.setText(state.get("status_label", "-"))

        panel = state.get("active_panel", "device")
        if panel == "simulation":
            panel = "translation_result"
        self.stacked.setCurrentIndex(self.PANEL_ORDER[panel])
        for key, button in self.sidebar_buttons.items():
            button.setChecked(key == panel)

        panel_views = {
            "device": self.device_panel,
            "config": self.config_panel,
            "pipeline": self.pipeline_panel,
            "file": self.artifact_panel,
            "translation_result": self.translation_result_panel,
            "llm_config": self.llm_config_panel,
        }
        panel_views[panel].update_view(state)

    def _show_message(self, message: str, is_error: bool) -> None:
        self.message_label.setText(message)
        self.message_label.setProperty("error", is_error)
        self.message_label.style().unpolish(self.message_label)
        self.message_label.style().polish(self.message_label)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                background: #eef3f7;
                color: #1b2733;
                font-family: "Microsoft YaHei UI";
                font-size: 13px;
            }
            QMainWindow {
                background: #eef3f7;
            }
            QFrame, QGroupBox, QPlainTextEdit, QTextEdit, QListWidget, QLineEdit, QComboBox {
                background: #f7f9fc;
                border: 1px solid #c8d4df;
                border-radius: 12px;
            }
            QGroupBox {
                margin-top: 12px;
                padding-top: 14px;
                font-weight: 600;
                color: #16324f;
            }
            QLineEdit, QComboBox {
                min-height: 34px;
                padding: 0 10px;
                selection-background-color: #16324f;
                selection-color: #ffffff;
            }
            QListWidget, QPlainTextEdit, QTextEdit {
                padding: 8px;
                selection-background-color: #d97a2b;
                selection-color: #ffffff;
            }
            #monoTextView, #fullLogView {
                font-family: "Consolas", "Cascadia Mono", "Microsoft YaHei UI";
                font-size: 13px;
            }
            QPushButton {
                background: #dfe8f0;
                color: #16324f;
                border: 0;
                border-radius: 12px;
                padding: 10px 18px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #d3e0eb;
            }
            QPushButton:checked {
                background: #4f7aa3;
                color: #ffffff;
            }
            QPushButton:pressed {
                background: #40688f;
                color: #ffffff;
            }
            QPushButton:disabled {
                background: #a7b7c6;
                color: #eff4f8;
            }
            QLabel[error="true"] {
                color: #b9471d;
                font-weight: 700;
            }
            #topBar {
                background: transparent;
                border: 0;
            }
            #sidebar {
                background: #deebf3;
            }
            #sidebar QPushButton {
                background: #edf3f8;
                color: #24415d;
                border: 1px solid #d0dce7;
                text-align: center;
                font-size: 15px;
                font-weight: 700;
            }
            #sidebar QPushButton:hover {
                background: #e2ebf3;
                border: 1px solid #bcccdc;
            }
            #sidebar QPushButton:checked {
                background: #5f88af;
                color: #ffffff;
                border: 1px solid #5f88af;
            }
            #sidebar QPushButton:pressed {
                background: #4f7aa3;
                color: #ffffff;
            }
            #toolbarFrame, #resultFrame, #messageBar, #keyValueCard {
                background: #f7f9fc;
            }
            #messageBar {
                border: 1px solid #c8d4df;
                border-radius: 12px;
                padding: 10px 14px;
                font-weight: 600;
                color: #16324f;
            }
            #cardTitle {
                color: #58708a;
                font-size: 11px;
                font-weight: 600;
                background: rgba(128, 168, 204, 0.14);
                border: 1px solid rgba(126, 162, 194, 0.42);
                border-radius: 0;
                padding: 3px 7px;
            }
            #cardValue {
                color: #1b2733;
                font-size: 13px;
                font-weight: 700;
                background: rgba(128, 168, 204, 0.18);
                border: 1px solid rgba(126, 162, 194, 0.48);
                border-radius: 0;
                padding: 4px 7px;
            }
            #panelHeading {
                font-size: 14px;
                font-weight: 700;
                color: #16324f;
                background: transparent;
                border: 0;
            }
            """
        )


def parse_scalar(raw: str) -> Any:
    text = raw.strip()
    if text == "":
        return ""
    if text in {"True", "False"}:
        return text == "True"
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return text


def deepcopy_or_empty(value: dict[str, Any] | None) -> dict[str, Any]:
    return json.loads(json.dumps(value if value is not None else {}))
