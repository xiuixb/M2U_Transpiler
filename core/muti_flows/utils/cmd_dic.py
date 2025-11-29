# src/utils/cmd_dic.py
# ============================================================
# 定义 MAGIC/UNIPIC 脚本的所有命令关键字。
# 供预处理阶段判断 command 名称使用。
# ============================================================

CMD_KEYWORDS_SINGLE = {
    # 1️⃣ Geometry
    "POINT", "LINE", "AREA", "VOLUME", "MARK", "GRID", "AUTOGRID", "SYSTEM",

    # 2️⃣ Material
    "MATERIAL", "CONDUCTOR", "CONDUCTANCE", "DIELECTRIC", "VOID", "INDUCTOR",
    "CAPACITOR", "RESISTOR", "FILM", "FOIL", "SURFACE_LOSS", "GAS_CONDUCTIVITY", "POLARIZER",

    # 3️⃣ Ports & Boundaries
    "PORT", "OUTGOING", "RESONANT_PORT", "FREESPACE",

    # 4️⃣ Sources
    "EMIT", "PHOTON", "IONIZATION", "SECONDARY", "BEAM", "EXPLOSIVE",

    # 5️⃣ Algorithms
    "MAXWELL", "POISSON", "CONTINUITY", "CIRCUIT", "LORENTZ", "MODE", "EIGENMODE",
    "DRIVER", "COILS", "CURRENT_SOURCE", "SPECIES", "TIME_STEP",

    # 6️⃣ Control Flow
    "DO", "ENDDO", "IF", "ELSEIF", "ELSE", "ENDIF", "CONTROL", "CALL", "RETURN", "PRESET", "TIMER", "DURATION",

    # 7️⃣ Output & Diagnostics
    "TABLE", "DISPLAY", "CONTOUR", "VECTOR", "VIEWER", "PHASESPACE",
    "TAGGING", "GRAPHICS", "STATISTICS", "HEADER", "PARAMETER", "EXPORT", "DUMP",

    # 8️⃣ Variable & Function
    "ASSIGN", "REAL", "INTEGER", "CHARACTER", "FUNCTION",

    # 9️⃣ Execution
    "START", "STOP", "TERMINATE", "COMMAND", "KEYBOARD",

    # 🔟 Misc
    "SYMMETRY", "MATCH", "IMPORT", "BLOCK", "ENDBLOCK", "TRAMLINE", "JOIN", "LOOKBACK", "CABLE",
    "ECHO", "NOECHO", "COMMENT", "C", "Z", "!", "DELIMITER",
    "LIST", "$NAMELIST$", "MCLDIALOG", "PARALLEL_GRID", "SHIM",

    # 
    "RANGE"
}

CMD_KEYWORDS_MULTI = {
    # ====== OBSERVE 系列 ======
    "OBSERVE CIRCUIT",
    "OBSERVE COLLECTED",
    "OBSERVE EMITTED",
    "OBSERVE FIELD",
    "OBSERVE FIELD_ENERGY",
    "OBSERVE FIELD_INTEGRAL",
    "OBSERVE FIELD_POWER",
    "OBSERVE INDUCTOR",
    "OBSERVE INTERVAL",
    "OBSERVE IONIZATION",
    "OBSERVE NEUTRAL_GAS",
    "OBSERVE PARTICLE_STATISTICS",
    "OBSERVE SECONDARY",
    "OBSERVE SPACE_HARMONIC",
    "OBSERVE RESISTOR",
    "OBSERVE TRAMLINE",

    # ====== EMISSION 系列 ======
    "EMISSION BEAM",
    "EMISSION EXPLOSIVE",
    "EMISSION GYRO",
    "EMISSION HIGH_FIELD",
    "EMISSION PHOTOELECTRIC",
    "EMISSION THERMIONIC"
}


