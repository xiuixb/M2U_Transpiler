class geo_counter:
    def __init__(self):
        self.vertex_count = 0
        self.edge_count = 0
        self.ploygon_count = 0
        self.wire_count = 0
        self.circle_count = 0
        self.arc_count = 0
        self.face_count = 0
        self.vector_count = 0
        self.revolution_count = 0
        self.subFaceSelection_count = 0
        self.mask_count = 0
        self.Dgn_count = 0
        self.Ez_count = 0
        self.Er_count = 0
        self.Ephi_count = 0
        self.Bz_count = 0
        self.Br_count = 0
        self.Bphi_count = 0
        self.voltageDgn_count = 0
        self.currentDgn_count = 0
        self.PoyntingDgn_count = 0
        self.inductor_count = 0
        

    def get_vertex_count(self):
        self.vertex_count += 1
        return self.vertex_count

    def get_edge_count(self):
        self.edge_count += 1
        return self.edge_count

    def get_polygon_count(self):
        self.ploygon_count += 1
        return self.ploygon_count

    def get_wire_count(self):
        self.wire_count += 1
        return self.wire_count

    def get_circle_count(self):
        self.circle_count += 1
        return self.circle_count

    def get_arc_count(self):
        self.arc_count += 1
        return self.arc_count

    def get_face_count(self):
        self.face_count += 1
        return self.face_count

    def get_vector_count(self):
        self.vector_count += 1
        return self.vector_count

    def get_revolution_count(self):
        self.revolution_count += 1
        return self.revolution_count

    def get_subFaceSelection_count(self):
        self.subFaceSelection_count += 1
        return self.subFaceSelection_count

    def get_mask_count(self):
        self.mask_count += 1
        return self.mask_count

    def get_Dgn_count(self):
        self.Dgn_count += 1
        return self.Dgn_count

    def get_Ez_count(self):
        self.Ez_count += 1
        return self.Ez_count

    def get_Er_count(self):
        self.Er_count += 1
        return self.Er_count

    def get_Ephi_count(self):
        self.Ephi_count += 1
        return self.Ephi_count

    def get_Bz_count(self):
        self.Bz_count += 1
        return self.Bz_count

    def get_Br_count(self):
        self.Br_count += 1
        return self.Br_count

    def get_Bphi_count(self):
        self.Bphi_count += 1
        return self.Bphi_count
    
    def get_voltageDgn_count(self):
        self.voltageDgn_count += 1
        return self.voltageDgn_count
    
    def get_currentDgn_count(self):
        self.currentDgn_count += 1
        return self.currentDgn_count
    
    def get_PoyntingDgn_count(self):
        self.PoyntingDgn_count += 1
        return self.PoyntingDgn_count
    
    def get_inductor_count(self):
        self.inductor_count += 1
        return self.inductor_count
        


def get_file_str(GeomBuilders):
    """
    GeomCtrl{
      nameid = theGeomCtrl
      GeomBuilder{
        nameid = geoBuilder1
        kind   = point
        ......
      }

      GeomBuilder{
        nameid = geoBuilder2
        kind   = line
        ......
      }
    }
    """
    GeomBuilders_txt = "\n".join([GeomBuilders[i] for i in range(len(GeomBuilders))])
    return "GeomCtrl{\n"+ \
            f"  nameid = theGeomCtrl\n" + \
            f"{GeomBuilders_txt}\n" + \
            "}"


def get_polygon_str(nameid, kind, name, type, pnts):
    """
    GeomBuilder {
        nameid = polyBuilder1    // 构建器ID（可选）
        kind   = polygon         // 必须为"polygon"，标识多边形类型
        name   = my_polygon      // 多边形名称（用于后续引用）
        type   = polygon         // 构造方式（可选，默认"Polygon"）
        pnts   = [               // 顶点坐标列表（必选）
            0.0 0.0 0.0,           // 顶点1 (x, y, z)
            10.0 0.0 0.0,          // 顶点2
            10.0 5.0 0.0,          // 顶点3
            0.0 5.0 0.0            // 顶点4（自动闭合）
        ]
    }
    """
    return "  GeomBuilder {\n"+ \
            f"    nameid = {nameid}\n" + \
            f"    kind = {kind}\n" + \
            f"    name = {name}\n" + \
            f"    type = {type}\n" + \
            f"    pnts = {pnts}\n" + \
            "  }"

def get_wire_str(nameid, kind, name, edge_list, tolerance: float = 1e-7, orientation: int = 0):
    """
    GeomBuilder {
        nameid     = wireBuilder1      // 构建器ID（可选）
        kind       = wire              // 必须为"wire"，标识线框类型
        name       = my_wire           // 线框名称（用于后续引用）
        builderlist = [edge1, edge2, edge3]  // 构成线框的边或其他线框名称列表（必须已存在）
        tolerance  = 0.000001          // 连接容差（可选，默认 1e-7）
        orientation = 0                // 方向（可选，0=自动，1=强制顺向，-1=强制逆向）
    }
    """
    return "  GeomBuilder {\n"+ \
            f"    nameid = {nameid}\n" + \
            f"    kind = {kind}\n" + \
            f"    name = {name}\n" + \
            f"    builderlist = {edge_list}\n" + \
            f"    tolerance = {tolerance}\n" + \
            f"    orientation = {orientation}\n" + \
            "  }"

def get_vector_str(nameid, kind, name , type, dims:str = "", vertexlist:str = ""):
    """
    GeomBuilder {
        nameid = vectorBuilder1    // 构建器ID（可选）
        kind   = vector            // 必须为"vector"，标识向量类型
        name   = my_vector         // 向量名称（用于后续引用）
        type   = Dim | Two_Pnt     // 构造方式类型（必选）直接分量定义向量/通过两顶点定义向量
        //如果是Dim
        dims  = [2.0 5.0 3.0]    // 向量分量（DX, DY, DZ）
        //如果是Two_Pnt
        vertexlist  = [point1, point2]  // 起点和终点顶点名称（必须已存在）
    }
    """
    return "  GeomBuilder {\n"+ \
            f"    nameid = {nameid}\n" + \
            f"    kind = {kind}\n" + \
            f"    name = {name}\n" + \
            f"    type = {type}\n" + \
            f"    dims = {dims}\n" + \
            "  }"

def get_revolution_str(nameid, kind, name,  base, vector, material: str = "", type: str = 'oneWay', angle: float = 360.0):
    """
    GeomBuilder {
        nameid   = revolBuilder1    // 构建器ID（可选）
        kind     = revolution       // 必须为"revolution"，标识旋转体类型
        name     = my_revol         // 旋转体名称（用于后续引用）
        type     = oneWay | twoWay  // 旋转方式（可选，默认"oneWay"）
        base     = base_curve       // 基几何体名称（必须已存在，如边或线框）
        vector   = axis_vector      // 旋转轴向量名称（必须已存在）
        angle    = 270.0            // 旋转角度（可选，默认360.0）
    }
    """
    return "  GeomBuilder {\n"+ \
            f"    nameid = {nameid}\n" + \
            f"    kind = {kind}\n" + \
            f"    name = {name}\n" + \
            f"    type = {type}\n" + \
            f"    base = {base}\n" + \
            f"    vector = {vector}\n" + \
            f"    angle = {angle}\n" + \
            f"    material = {material}\n" + \
            "  }"

def get_edge_str(nameid, kind, name, type, vertexlist: list = [], start: str = "", edge: str = "", face: str = "", U1: float = 0.0, U2: float = 1.0, V1: float = 0.0, V2: float = 1.0, T1: float = 0.0, T2: float = 1.0):
    """
    GeomBuilder {
        nameid = edgeBuilder1    // 构建器ID（可选）
        kind   = edge            // 必须为"edge"，标识边类型
        name   = my_edge         // 边名称（用于后续引用）
        type   = Two_Pnt | Pnt_Vector | Edge_On_Surface  // 构造方式类型（必选）
        //如果是两点模式(type = Two_Pnt)
        vertexlist = [point1, point2]  // 起点和终点顶点名称（必须已存在）
        //如果是沿向量延伸 (type = "Pnt_Vector")
        start  = point1          // 起点顶点名称（必须已存在）
        edge   = direction_vec    // 方向向量名称（必须已存在，由 `Geom_Vector_TxtBuilder` 创建）
        //如果是曲面上参数化边 (type = "Edge_On_Surface")
        face   = face1            // 曲面名称（必须已存在）
        U1     = 0.0              // 曲面参数U起点（可选，默认0.0）
        U2     = 1.0              // 曲面参数U终点（可选，默认1.0）
        V1     = 0.0              // 曲面参数V起点（可选，默认0.0）
        V2     = 1.0              // 曲面参数V终点（可选，默认1.0）
        T1     = 0.0              // 边参数化起点（可选，默认0.0）
        T2     = 1.0              // 边参数化终点（可选，默认1.0）
    }
    """ 
    if type == "Two_Pnt":
        return "  GeomBuilder {\n"+ \
               f"    nameid = {nameid}\n" + \
               f"    kind = {kind}\n" + \
               f"    name = {name}\n" + \
               f"    type = {type}\n" + \
               f"    vertexlist = {vertexlist}\n" + \
               "  }"
    elif type == "Pnt_Vector":
        return "  GeomBuilder {\n"+ \
               f"    nameid = {nameid}\n" + \
               f"    kind = {kind}\n" + \
               f"    name = {name}\n" + \
               f"    type = {type}\n" + \
               f"    start = {start}\n" + \
               f"    edge = {edge}\n" + \
               "  }"
    elif type == "Edge_On_Surface":
        return "  GeomBuilder {\n"+ \
               f"    nameid = {nameid}\n" + \
               f"    kind = {kind}\n" + \
               f"    name = {name}\n" + \
               f"    type = {type}\n" + \
               f"    face = {face}\n" + \
               f"    U1 = {U1}\n" + \
               f"    U2 = {U2}\n" + \
               f"    V1 = {V1}\n" + \
               f"    V2 = {V2}\n" + \
               f"    T1 = {T1}\n" + \
               f"    T2 = {T2}\n" + \
               "  }"
    else:
        print(f"边类型定义不正确")

def get_face_str(nameid, kind, name, wireName, isPlanar: int = 1):
    """
    GeomBuilder {
        nameid   = faceBuilder1      // 构建器ID（可选）
        kind     = face              // 指定几何类型为面
        name     = my_face           // 面名称（用于后续引用）
        wireName = my_wire           // 已存在的线框（Wire）名称
        isPlanar = 1                 // 是否为平面（1=平面，0=非平面，可选，默认1）
    }
    """
    return "  GeomBuilder {\n"+ \
            f"    nameid = {nameid}\n" + \
            f"    kind = {kind}\n" + \
            f"    name = {name}\n" + \
            f"    wireName = {wireName}\n" + \
            f"    isPlanar = {isPlanar}\n" + \
            "  }"