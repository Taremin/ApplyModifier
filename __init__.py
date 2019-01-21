#Copyright (c) 2014 mato.sus304(mato.sus304@gmail.com)
#
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Apply Modifier",
    "author": "mate.sus304",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Object > Apply",
    "description": "Apply All Modifier to Mesh Object",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "website":"https://sites.google.com/site/matosus304blendernotes/home",
    "category": "Object"}


import bpy

######################################################
if bpy.app.version < (2,80,0):
    isLegacy = True
else:
    isLegacy = False 

def Set_Active_ShapeKey (name):
    Get_Active_Object().active_shape_key_index = Get_Active_Object().data.shape_keys.key_blocks.keys().index(name)

def Select_Object (obj, value):
    if isLegacy:
        obj.select = value
    else:
        obj.select_set(value)

def Get_Active_Object ():
    if isLegacy: 
        return bpy.context.scene.objects.active
    else:
        return bpy.context.window.view_layer.objects.active

def Set_Active_Object (obj):
    if isLegacy: 
        bpy.context.scene.objects.active = obj
    else:
        bpy.context.window.view_layer.objects.active = obj

def Clear_Shape_Keys(Name):
    obj = Get_Active_Object()
    if obj.data.shape_keys == None:
        return True
    
    obj.active_shape_key_index = len(obj.data.shape_keys.key_blocks)-1
    while len(obj.data.shape_keys.key_blocks)>1:
        #print(obj.data.shape_keys.key_blocks[obj.active_shape_key_index])
        
        if obj.data.shape_keys.key_blocks[obj.active_shape_key_index].name == Name:
            obj.active_shape_key_index = 0
            #print(Name)
        else:
            bpy.ops.object.shape_key_remove()
    
    bpy.ops.object.shape_key_remove()

def Clone_Object(Obj):
    tmp_obj = Obj.copy()
    tmp_obj.name = "applymodifier_tmp_%s"%(Obj.name)
    tmp_obj.data = tmp_obj.data.copy()
    tmp_obj.data.name = "applymodifier_tmp_%s"%(Obj.data.name)
    if isLegacy:
        bpy.context.scene.objects.link(tmp_obj)
    else:
        bpy.context.scene.collection.objects.link(tmp_obj)
    return tmp_obj

def Delete_Object(Obj):
    if Obj.data.users == 1:
        Obj.data.user_clear()
    for scn in bpy.data.scenes:
        try:
            if isLegacy:
                bpy.context.scene.objects.unlink(Obj)
            else:
                bpy.context.scene.collection.objects.unlink(Obj)
        except:
            pass

######################################################

def Func_Apply_Modifier(self, context, target_object = None, target_modifiers = None):
    if target_object == None:
        obj_src = Get_Active_Object()
    else:
        obj_src = target_object
    
    if len(obj_src.modifiers) == 0:
        #if object has no modifier then skip
        return True
    
    #make single user
    if obj_src.data.users != 1:
        obj_src.data = obj_src.data.copy()
    
    if obj_src.data.shape_keys == None:
        #if object has no shapekeys, just apply modifier
        for x in obj_src.modifiers:
            try:
                bpy.ops.object.modifier_apply(modifier=x.name)
            except RuntimeError:
                pass
        return True
    
    obj_fin = Clone_Object(obj_src)
    
    Set_Active_Object(obj_fin)
    Clear_Shape_Keys('Basis')
    
    if target_modifiers == None:
        target_modifiers = []
        for x in obj_fin.modifiers:
            if x.show_viewport:
                target_modifiers.append(x.name)
    
    for x in target_modifiers:
        try:
            bpy.ops.object.modifier_apply(modifier=x)
        except RuntimeError:
            pass
    
    flag_onError = False
    list_skipped = []
    
    for i in range(1, len(obj_src.data.shape_keys.key_blocks)):
        tmp_name = obj_src.data.shape_keys.key_blocks[i].name
        obj_tmp = Clone_Object(obj_src)
        
        Set_Active_Object(obj_tmp)
        Clear_Shape_Keys(tmp_name)
        
        for x in target_modifiers:
            try:
                bpy.ops.object.modifier_apply(modifier=x)
            except RuntimeError:
                pass
        
        Select_Object(obj_tmp, True)
        Set_Active_Object(obj_fin)
        try:
            bpy.ops.object.join_shapes()
            obj_fin.data.shape_keys.key_blocks[-1].name = tmp_name
        except:
            flag_onError = True
            list_skipped.append(tmp_name)
            
            
        Delete_Object(obj_tmp)
    
    if flag_onError:
        def draw(self, context):
            self.layout.label("Vertex Count Disagreement! Some shapekeys skipped.")
            for s in list_skipped:
                self.layout.label(s)

        bpy.context.window_manager.popup_menu(draw, title="Error", icon='INFO')
        
        return False
        
    tmp_name = obj_src.name
    tmp_data_name = obj_src.data.name
    obj_fin.name = tmp_name + '.tmp'
    
    
    obj_src.data = obj_fin.data
    obj_src.data.name = tmp_data_name
    
    for x in target_modifiers:
        obj_src.modifiers.remove(obj_src.modifiers[x])
            
    Delete_Object(obj_fin)
    Set_Active_Object(obj_src)
    #obj_src.select = False
    #obj_src.location[0] += -1

class OBJECT_OT_apply_all_modifier(bpy.types.Operator):
    """Apply All Modifier to Selected Mesh Object"""
    bl_idname = "object.apply_all_modifier"
    bl_label = "Apply_All_Modifier"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        targets = []
        for x in bpy.context.selected_objects:
            targets.append(x.name)
        
        bpy.ops.object.select_all(action='DESELECT')
        #print(targets)
        for x in targets:
            Func_Apply_Modifier(self, context, target_object = bpy.data.objects[x])
        
        for x in targets:
            Select_Object(bpy.data.objects[x], True)
        
        return {'FINISHED'}
    


class OBJECT_OT_apply_selected_modifier(bpy.types.Operator):
    """Apply Selected Modifier to Active Mesh Object"""
    bl_idname = "object.apply_selected_modifier"
    bl_label = "Apply_Selected_Modifier"
    bl_options = {'REGISTER', 'UNDO'}
    
    bv = bpy.props.BoolVectorProperty(name="Booleans", description="test value", size=32)
    
    mod_count = 0
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH'
    
    def execute(self, context):
        obj = Get_Active_Object()
        objname = obj.name
        bpy.ops.object.select_all(action='DESELECT')
        
        str_targets = []
        for i in range(self.mod_count):
            if self.bv[i]:
                str_targets.append(bpy.data.objects[objname].modifiers[i].name)
        
        Func_Apply_Modifier(self, context, target_object = bpy.data.objects[objname], target_modifiers = str_targets)
        
        Select_Object(obj, True)
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        obj = context.object
        self.mod_count = len(obj.modifiers)
        
        layout = self.layout
        col = layout.column()
        
        for i in range(self.mod_count):
            col.prop(self, "bv", text = obj.modifiers[i].name, index = i)
        
    

# Registration

def apply_all_modifier_button(self, context):
    self.layout.operator(
        OBJECT_OT_apply_all_modifier.bl_idname,
        text="Apply All Modifier")

def apply_selected_modifier_button(self, context):
    self.layout.operator(
        OBJECT_OT_apply_selected_modifier.bl_idname,
        text="Apply Selected Modifier")

def register():
    bpy.utils.register_class(OBJECT_OT_apply_all_modifier)
    bpy.utils.register_class(OBJECT_OT_apply_selected_modifier)
    bpy.types.VIEW3D_MT_object_apply.append(apply_all_modifier_button)
    bpy.types.VIEW3D_MT_object_apply.append(apply_selected_modifier_button)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_apply_all_modifier)
    bpy.utils.unregister_class(OBJECT_OT_apply_selected_modifier)
    bpy.types.VIEW3D_MT_object_apply.remove(apply_all_modifier_button)
    bpy.types.VIEW3D_MT_object_apply.remove(apply_selected_modifier_button)


if __name__ == "__main__":
    register()
