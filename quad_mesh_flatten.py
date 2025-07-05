import bpy
import bmesh
from mathutils import Vector

bl_info = {
    "name": "Quad Mesh Flatten",
    "author": "hip & Claude",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Edit",
    "description": "Flatten quad mesh to plane by projecting one vertex to the plane defined by other three vertices",
    "category": "Mesh",
}

def flatten_quad_to_plane(projection_axis=None):
    """
    選択された4頂点のメッシュを平面にする
    最初の3頂点で平面を定義し、4番目の頂点をその平面上に移動
    """
    
    # アクティブオブジェクトを取得
    obj = bpy.context.active_object
    
    # メッシュオブジェクトかチェック
    if obj is None or obj.type != 'MESH':
        return {"CANCELLED"}, "メッシュオブジェクトを選択してください"
    
    # 編集モードに切り替え
    bpy.context.view_layer.objects.active = obj
    if bpy.context.mode != 'EDIT_MESH':
        bpy.ops.object.mode_set(mode='EDIT')
    
    # 編集モードでbmeshを取得
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    
    # 選択された頂点を取得
    selected_verts = [v for v in bm.verts if v.select]
    
    # 4頂点が選択されているかチェック
    if len(selected_verts) != 4:
        return {"CANCELLED"}, f"4つの頂点を選択してください。現在選択: {len(selected_verts)}個"
    
    # 最後に選択された頂点を取得（アクティブな頂点）
    active_vert = bm.select_history[-1] if bm.select_history else selected_verts[-1]
    
    # 平面を定義する3頂点を取得（アクティブでない頂点）
    plane_verts = [v for v in selected_verts if v != active_vert]
    
    if len(plane_verts) != 3:
        return {"CANCELLED"}, "平面定義用の3頂点が正しく取得できませんでした"
    
    # 3頂点の座標を取得
    v1, v2, v3 = [v.co for v in plane_verts]
    
    # 軸指定投影の場合
    if projection_axis:
        # 平面の法線ベクトルを計算
        edge1 = v2 - v1
        edge2 = v3 - v1
        normal = edge1.cross(edge2).normalized()
        
        # 法線がゼロベクトルの場合（3点が一直線上）
        if normal.length < 1e-6:
            return {"CANCELLED"}, "選択された3頂点が一直線上にあります。平面を定義できません。"
        
        # 平面上の点として v1 を使用
        plane_point = v1
        target_point = active_vert.co
        
        # 各軸方向にのみ移動させて平面との交点を見つける
        if projection_axis == 'X':
            # X軸方向の直線と平面の交点を計算
            # 直線: P = target_point + t * (1, 0, 0)
            # 平面: normal · (P - plane_point) = 0
            direction = Vector((1, 0, 0))
        elif projection_axis == 'Y':
            # Y軸方向の直線と平面の交点を計算
            direction = Vector((0, 1, 0))
        elif projection_axis == 'Z':
            # Z軸方向の直線と平面の交点を計算
            direction = Vector((0, 0, 1))
        
        # 直線と平面の交点を計算
        # normal · (target_point + t * direction - plane_point) = 0
        # t = -normal · (target_point - plane_point) / normal · direction
        denominator = normal.dot(direction)
        
        if abs(denominator) < 1e-6:
            return {"CANCELLED"}, f"{projection_axis}軸方向の直線が平面と平行です。交点を計算できません。"
        
        numerator = -normal.dot(target_point - plane_point)
        t = numerator / denominator
        
        # 交点を計算
        projected_point = target_point + t * direction
        
        # 4番目の頂点を投影点に移動
        active_vert.co = projected_point
        distance_to_plane = abs(t)
        
    else:
        # 通常の平面投影
        # 平面の法線ベクトルを計算
        edge1 = v2 - v1
        edge2 = v3 - v1
        normal = edge1.cross(edge2).normalized()
        
        # 法線がゼロベクトルの場合（3点が一直線上）
        if normal.length < 1e-6:
            return {"CANCELLED"}, "選択された3頂点が一直線上にあります。平面を定義できません。"
        
        # 平面上の点として v1 を使用
        plane_point = v1
        
        # 4番目の頂点を平面上に投影
        target_point = active_vert.co
        
        # 点から平面への投影計算
        to_target = target_point - plane_point
        distance_to_plane = to_target.dot(normal)
        projected_point = target_point - distance_to_plane * normal
        
        # 4番目の頂点を投影点に移動
        active_vert.co = projected_point
        distance_to_plane = abs(distance_to_plane)
    
    # メッシュを更新
    bmesh.update_edit_mesh(obj.data)
    
    message = f"頂点を平面上に移動しました。移動距離: {distance_to_plane:.6f}"
    return {"FINISHED"}, message

class MESH_OT_flatten_quad_to_plane(bpy.types.Operator):
    """Flatten quad mesh to plane defined by 3 vertices"""
    bl_idname = "mesh.flatten_quad_to_plane"
    bl_label = "Flatten to Plane"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        result, message = flatten_quad_to_plane()
        if result == {"CANCELLED"}:
            self.report({'ERROR'}, message)
        else:
            self.report({'INFO'}, message)
        return result

class MESH_OT_flatten_quad_to_x_plane(bpy.types.Operator):
    """Move vertex along X-axis to intersect with plane defined by 3 vertices"""
    bl_idname = "mesh.flatten_quad_to_x_plane"
    bl_label = "Move along X to Plane"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        result, message = flatten_quad_to_plane('X')
        if result == {"CANCELLED"}:
            self.report({'ERROR'}, message)
        else:
            self.report({'INFO'}, message)
        return result

class MESH_OT_flatten_quad_to_y_plane(bpy.types.Operator):
    """Move vertex along Y-axis to intersect with plane defined by 3 vertices"""
    bl_idname = "mesh.flatten_quad_to_y_plane"
    bl_label = "Move along Y to Plane"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        result, message = flatten_quad_to_plane('Y')
        if result == {"CANCELLED"}:
            self.report({'ERROR'}, message)
        else:
            self.report({'INFO'}, message)
        return result

class MESH_OT_flatten_quad_to_z_plane(bpy.types.Operator):
    """Move vertex along Z-axis to intersect with plane defined by 3 vertices"""
    bl_idname = "mesh.flatten_quad_to_z_plane"
    bl_label = "Move along Z to Plane"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        result, message = flatten_quad_to_plane('Z')
        if result == {"CANCELLED"}:
            self.report({'ERROR'}, message)
        else:
            self.report({'INFO'}, message)
        return result

class VIEW3D_PT_quad_mesh_flatten(bpy.types.Panel):
    """Quad Mesh Flatten Panel"""
    bl_label = "Quad Mesh Flatten"
    bl_idname = "VIEW3D_PT_quad_mesh_flatten"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Edit'
    bl_context = 'mesh_edit'
    
    def draw(self, context):
        layout = self.layout
        
        # 使用方法の説明
        box = layout.box()
        box.label(text="使用方法:", icon='INFO')
        box.label(text="1. 4つの頂点を選択")
        box.label(text="2. 最後に移動させたい頂点を選択")
        box.label(text="3. 下のボタンをクリック")
        
        layout.separator()
        
        # 現在の選択状態を表示
        obj = context.active_object
        if obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH':
            bm = bmesh.from_edit_mesh(obj.data)
            selected_verts = [v for v in bm.verts if v.select]
            
            if len(selected_verts) == 4:
                layout.label(text="✓ 4頂点選択済み", icon='CHECKMARK')
            else:
                layout.label(text=f"選択頂点数: {len(selected_verts)}/4", icon='ERROR')
        else:
            layout.label(text="編集モードでメッシュを選択", icon='ERROR')
        
        layout.separator()
        
        # メインボタン
        col = layout.column(align=True)
        col.scale_y = 1.5
        
        # 通常の平面投影
        col.operator("mesh.flatten_quad_to_plane", 
                    text="平面化", 
                    icon='MESH_PLANE')
        
        layout.separator()
        
        # 軸別投影
        row = layout.row(align=True)
        row.operator("mesh.flatten_quad_to_x_plane", 
                    text="X軸移動", 
                    icon='AXIS_SIDE')
        row.operator("mesh.flatten_quad_to_y_plane", 
                    text="Y軸移動", 
                    icon='AXIS_FRONT')
        row.operator("mesh.flatten_quad_to_z_plane", 
                    text="Z軸移動", 
                    icon='AXIS_TOP')

def register():
    bpy.utils.register_class(MESH_OT_flatten_quad_to_plane)
    bpy.utils.register_class(MESH_OT_flatten_quad_to_x_plane)
    bpy.utils.register_class(MESH_OT_flatten_quad_to_y_plane)
    bpy.utils.register_class(MESH_OT_flatten_quad_to_z_plane)
    bpy.utils.register_class(VIEW3D_PT_quad_mesh_flatten)

def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_quad_mesh_flatten)
    bpy.utils.unregister_class(MESH_OT_flatten_quad_to_z_plane)
    bpy.utils.unregister_class(MESH_OT_flatten_quad_to_y_plane)
    bpy.utils.unregister_class(MESH_OT_flatten_quad_to_x_plane)
    bpy.utils.unregister_class(MESH_OT_flatten_quad_to_plane)

if __name__ == "__main__":
    register()
    print("Quad Mesh Flatten アドオンが登録されました")