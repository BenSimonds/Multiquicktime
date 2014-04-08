# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_info = {
    "name": "Multi Quicktime",
    "author": "Ben Simonds",
    "version": (1, 12),
    "blender": (2, 69, 0),
    "location": "Properties > Render > MultiQuicktime",
    "description": "Automatically Converts an Image Sequence to multiple quicktime movies once a render finishes.",
    "warning": "Requires qt_tools and ffmpeg",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Render",
    }

import bpy
from .multiquicktime import *

# UI:

class MULTIQUICKTIME_UL_quicktimes(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # assert(isinstance(item, bpy.types.SceneRenderLayer)
        quicktime = item
        layout.label(quicktime.name, icon='RENDER_ANIMATION', translate=False)
        layout.prop(quicktime, "mute", text="", index=index)
        #layout.prop(quicktime, "sequencerate", text="", index=index)



class MultiQuicktimePanel(Panel):
    """Creates the UI Panel for the MultiQuicktime settings."""
    bl_label = "Multi-Quicktime"
    bl_idname = "OBJECT_PT_multiquicktime"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    
    def draw(self,context):
        scene = bpy.context.scene
        mqt = scene.multi_quicktime
        layout = self.layout
        
        #Normal settings (global to all exports).
        row = layout.row()
        row.prop(mqt, 'multiquicktime_on', text = "Auto Generate After Render")
        row.prop(mqt, 'multiquicktime_overwrite')
        
        row = layout.row()
        row.prop(mqt, 'output_dir')
        
        row = layout.row()
        row.label(text = "Outputs:")
        
        col = row.column()
        row = col.row(align = True)
        row.operator('render.export_qtlist', text = "Export List", icon = "EXPORT")
        row.operator('render.import_qtlist', text = "Import List", icon = "IMPORT")
        
        if len(mqt.quicktimes.items()) == 0:
            row = layout.row()
            row.operator('render.add_multi_quicktime', text = "Add Multi Quicktime Output", icon ='ZOOMIN')
        else:
            #Make Sure active quicktime is a valid number.
            if mqt.active_quicktime < len(mqt.quicktimes):
                quicktime = mqt.quicktimes[mqt.active_quicktime]
            else:
                quicktime = mqt.quicktimes[0]

        
            row = layout.row()
            row.template_list('MULTIQUICKTIME_UL_quicktimes', 'MultiQuicktimes', bpy.context.scene.multi_quicktime, "quicktimes", bpy.context.scene.multi_quicktime, "active_quicktime")
            
            
            col = row.column(align=True)
            col.operator('render.add_multi_quicktime', text = "", icon ='ZOOMIN')
            col.operator('render.delete_multi_quicktime', text = "", icon = 'ZOOMOUT').to_remove = quicktime.name
            
            
            row = layout.row()
            row.separator()
           
            row = layout.row()
            row.prop(quicktime,'name',text = "Name")
            
            row = layout.row()
            row.prop(quicktime,'auto_open')
            #row.prop(quicktime,'mute',text = "Mute")
                
            row = layout.row(align = True)    
            row.prop(quicktime, 'overridefps', text = "Override Sequence Rate")
            col = row.column()
            col.prop(quicktime,'sequencerate',text = "")
            col.active = quicktime.overridefps
                
            row = layout.row(align = True)
            row.prop(quicktime,'settings',text = "Settings File")
            row.operator('render.do_dialog', text = "", icon = "SCRIPT").filename = quicktime.settings #Configure Button
            
            #Watermark Options
            row = layout.row()
            row.prop(quicktime, 'watermark')
            if mqt.quicktimes[mqt.active_quicktime].watermark:
                row.prop(quicktime, 'watermark_file')
            
            row = layout.row()
            row.prop(quicktime, 'watermark_preview')
            if mqt.quicktimes[mqt.active_quicktime].watermark_preview:    
                row.prop(quicktime, 'watermark_frame')
                row.prop(quicktime, 'watermark_frame_file')
            
            #Give user a flag if config file does not exist...
            row = layout.row()
            if os.path.isfile(bpy.path.abspath(quicktime.settings)) == False:
                row.label(text = "WARNING: No config file found.", icon ='ERROR')
        
        
        row = layout.row()
        row.separator()
    
        row = layout.row()
        row.operator('render.multi_quicktime', text = "Generate Outputs from Frames")

# Registration:

def register():
    #Properties:
    bpy.utils.register_class(MultiQuicktimes)
    bpy.utils.register_class(MultiQuicktimeProps)    
    bpy.types.Scene.multi_quicktime = bpy.props.PointerProperty(type=MultiQuicktimeProps)
    #print(bpy.context.scene.multi_quicktime.multiquicktime_on)
    #Operatorstypes.
    bpy.utils.register_class(DoDialog)    
    bpy.utils.register_class(MultiQuicktimeFrames)
    bpy.utils.register_class(AddQT)
    bpy.utils.register_class(RemoveQT)
    bpy.utils.register_class(DelQT)
    bpy.utils.register_class(ExportQTList)
    bpy.utils.register_class(ImportQTList)
    #UI Stuff:
    bpy.utils.register_class(MultiQuicktimePanel)
    bpy.utils.register_class(MULTIQUICKTIME_UL_quicktimes)
    #Handlers:
    bpy.app.handlers.render_pre.append(render_started)
    bpy.app.handlers.render_cancel.append(kill_render)
    bpy.app.handlers.render_complete.append(end_render)
    bpy.app.handlers.frame_change_post.append(check_animation)
    

def unregister():
    #Properties:
    bpy.utils.unregister_class(MultiQuicktimes)
    bpy.utils.unregister_class(MultiQuicktimeProps)    
    #Operatorstypes.
    bpy.utils.unregister_class(DoDialog)    
    bpy.utils.unregister_class(MultiQuicktimeFrames)
    bpy.utils.unregister_class(AddQT)
    bpy.utils.unregister_class(RemoveQT)
    bpy.utils.unregister_class(DelQT)
    bpy.utils.unregister_class(ExportQTList)
    bpy.utils.unregister_class(ImportQTList)
    #UI Stuff:
    bpy.utils.unregister_class(MultiQuicktimePanel)
    bpy.utils.unregister_class(MULTIQUICKTIME_UL_quicktimes)
    #Handlers:
    bpy.app.handlers.render_pre.remove(render_started)
    bpy.app.handlers.render_cancel.remove(kill_render)
    bpy.app.handlers.render_complete.remove(end_render)
    bpy.app.handlers.frame_change_post.remove(check_animation)
        