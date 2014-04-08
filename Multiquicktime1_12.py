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
import os, json
from bpy.app.handlers import persistent
from bpy.types import Menu, Panel, UIList


#First set up the most important functions and classes. Namely Do_Dialog (with user defined export location), and Autoquicktime (again with selectable export settings.


def dodialog_save(filename):
        #Settings Path
        settings_path  = '"' + bpy.path.abspath(filename) + '"'
        #Check if settings file already exists.
        print("Checking file exists... " + str(bpy.path.abspath(filename)) + " ... Resut: " + str(os.path.exists(bpy.path.abspath(filename))))
        if os.path.isfile(bpy.path.abspath(filename)):
            #print("qt_export --dodialog --loadsettings=" + settings_path + " --savesettings=" + settings_path)
            os.system("qt_export --dodialog --loadsettings=" + settings_path + " --savesettings=" + settings_path)
        else:
            #print("qt_export --dodialog --savesettings=" + settings_path)
            os.system("qt_export --dodialog --savesettings=" + settings_path)
        print("Saved settings to " + settings_path)

def multi_quicktime(quicktime):
        name = quicktime.name
        settings = quicktime.settings
        overridefps = quicktime.overridefps
        sequencerate = quicktime.sequencerate
         
        #Variables:
        scene = bpy.context.scene
        renderpath = scene.render.filepath
        outputpath = scene.multi_quicktime.output_dir
        ext = scene.render.file_extension
        fstart = scene.frame_start
        fend = scene.frame_end
        #Framerate depends on if overridefps is true
        if overridefps:    
            framerate = sequencerate #previously scene.render.fps,  now superseded by manual sequence rate.
        else:
            framerate = scene.render.fps
        ###FRAME RANGE AND DURATION 
        allframes = RenderedFrames()
        firstframe = allframes.firstframe
        lastframe = allframes.lastframe
        begin = (fstart - firstframe) / framerate
        end = (fend - firstframe + 1) / framerate # +1 is to make the frame range inclusive. Otherwise last frame will be dropped.
        ###INPUT DIRECTORY AND FILENAMES
        framepath = bpy.path.abspath(renderpath)
        framedir = framepath.rsplit("/",1)[0]+"/"
        framebegin = framepath + str(firstframe).zfill(4) + ext
        ###OUTPUT DIRECTORY AND FILENAMES
        outpath = bpy.path.abspath(outputpath)
        movie = outpath + name + ".mov"
        #Overwrite Settings
        overwrite = ""
        if bpy.context.scene.multi_quicktime.multiquicktime_overwrite:
            overwrite = "--replacefile "
        #Settings File:
        settings_file = '"' + bpy.path.abspath(settings) + '"'
        #print(settings_file)
        if os.path.isfile(bpy.path.abspath(settings)):
            #Run qt_export
            qt_string = "qt_export " + overwrite + "--sequencerate=" + str(framerate) + " --duration=" + str(begin) + "," + str(end) + " " + framebegin + " --loadsettings=" + settings_file +  " " + movie
            os.system(qt_string)
            #print("#############")
            #print(str(quicktime.watermark))
            if quicktime.watermark:
                #print("Doing Quicktime with Watermark")
                do_watermark(movie,quicktime.watermark_file, quicktime.name)
            if quicktime.watermark_preview:
                #print("Doing Preview Image with Watermark")
                watermark_image = bpy.path.abspath(bpy.context.scene.render.filepath) + str(quicktime.watermark_frame).zfill(4) + bpy.context.scene.render.file_extension
                #print(watermark_image)
                do_watermark(watermark_image, quicktime.watermark_frame_file, quicktime.name)
            if quicktime.auto_open:
                os.system("open -a Quicktime\ Player\ 7 " + movie)

        else:
            print("ERROR: No settings found. Skipping export.")

def do_watermark(video,watermark_file,outputname):
    ffmpeg = "ffmpeg" #(os.path.realpath(__file__).rsplit("/",1)[0]) + "/multiqtsettings/ffmpeg"
    ffmpeg_e = ffmpeg.replace(" ", "\\ ")   
    video_e = video.replace(" ", "\\ ")
    video_split = video_e.rsplit(".",1)
    watermark_file_e = bpy.path.abspath(watermark_file).replace(" ", "\\ ")
    qscale = "" #This gets set below for exporting images.
    #Work out output container:
    if video_split[1] in ["png","tga","jpg","jpeg","tiff"]:
        container = "jpg"
        qscale = " -qscale:v 3"
    else:
        container = video_split[1]
    #Get output directory
    outputdir = bpy.path.abspath(bpy.context.scene.multi_quicktime.output_dir).replace(" ", "\\ ")
    string = ffmpeg_e + " -y -i " + video_e + qscale + " -vf \"movie=" + watermark_file_e + " [watermark]; [in][watermark] overlay=0:0 [out]\" "  + outputdir + outputname+ "_watermarked." + container
    #print("$$$$$ String is: \n" +  string + "\n $$$$$")
    os.system(string)



class RenderedFrames:
    "A class for getting info about what rendered frames *acutally* exist"
    def __init__(self):
        scene = bpy.context.scene
        render_path = bpy.path.abspath(scene.render.filepath)
        render_dir = render_path.rsplit("/",1)[0]
        render_name = render_path.rsplit("/",1)[1]
        ext = scene.render.file_extension
        
        #print(render_dir)
        dirfiles = os.listdir(render_dir)
        frames = [] #List of frames that *actually* exist in the output directory.
        
        
        #get list of files in directory
        for file in dirfiles:
            #print(file)
            if file.endswith(ext):
                if file.startswith(render_name):
                    if render_name == "":
                        frame = file.rsplit(ext)[0]
                    else:
                        frame = file.rsplit(ext)[0].split(render_name,1)[1]
                    try:
                        frame_no = int(frame)
                        frames.append(frame_no)
                    except ValueError:
                        print("Value Error Getting Frames List. Have all frames rendered correctly?")
        #print(frames)
        
        self.firstframe = frames[0]
        self.lastframe = frames[-1]

class DoDialog(bpy.types.Operator):
    """Set up export settings for quicktime auto export."""
    bl_idname = "render.do_dialog"
    bl_label = "Set Export Settings"
    filename = bpy.props.StringProperty(name = "settings file", default = "default")
    
    def execute(self, context):
        dodialog_save(self.filename)
        return {'FINISHED'}
    
class MultiQuicktimeFrames(bpy.types.Operator):
    bl_idname = "render.multi_quicktime"
    bl_label = "Multi-Quicktime Sequence"
        
    def execute(self, context):
        #Run a for loop over each instance of MultiQuicktimes.
        for item in bpy.context.scene.multi_quicktime.quicktimes:
            mute = item.mute
            if mute:
                multi_quicktime(item)
        return{'FINISHED'}

class AddQT(bpy.types.Operator): #Adds a new quicktime to the list of outputs.
    """Adds a new quicktime to the list of those to make after render completes."""
    bl_idname = "render.add_multi_quicktime"
    bl_label = "Add Multi-Quicktime Output"
    name = bpy.props.StringProperty(name = "name", default = "quicktime")
    
    def execute(self,context):
        new_qt = bpy.context.scene.multi_quicktime.quicktimes.add()
        new_qt.name = self.name
        return{'FINISHED'}


class RemoveQT(bpy.types.Operator): #Removes a quicktime from the list    
    bl_idname = "render.remove_multi_quicktime"
    bl_label = "Remove MultiQuicktime Output"
    
    def execute (self,context):
        bpy.context.scene.multi_quicktime.quicktimes.remove(0)
        return{"FINISHED"}
    
class DelQT(bpy.types.Operator):
    bl_idname = "render.delete_multi_quicktime"
    bl_label = "Delete Specific MultiQuicktime Output"
    to_remove = bpy.props.StringProperty(name = "name", default = "_name_of_quicktime_")
    
    def execute(self,context):
        active_quicktime = bpy.context.scene.multi_quicktime.active_quicktime
        bpy.context.scene.multi_quicktime.quicktimes.remove(active_quicktime) #need to change the active quicktime after this...
        if active_quicktime > 0:
            bpy.context.scene.multi_quicktime.active_quicktime = active_quicktime - 1
        else:
            bpy.context.scene.multi_quicktime.active_quicktime = 0
        return{"FINISHED"}

# Version 1.11: Ability to import/export a text file with a list of quicktimes to create.

# Export:

class ExportQTList(bpy.types.Operator):
    bl_idname = "render.export_qtlist"
    bl_label = "Export the current list of Quicktimes to export."
    filepath = bpy.props.StringProperty(name = "filename", subtype = 'FILE_PATH', default = ((os.path.realpath(__file__).rsplit("/",1)[0]) + "/multiqtsettings/defaultsettingslist.txt"))
    
    def execute(self, context):    
        quicktimes = bpy.context.scene.multi_quicktime.quicktimes
        qt_dict = {}
        
        for qt in quicktimes:
            # The list of props goes as follows:
            # [name, mute, settings, overridefps, sequencerate, auto_open, watermark, etc...]
            # Create sub dict for props:
            name = qt.name
            props = {"name" : qt.name,
                "mute" : qt.mute,
                "settings" : qt.settings,
                "overridefps" : qt.overridefps,
                "sequencerate" : qt.sequencerate,
                "auto_open" : qt.auto_open,
                "watermark" : qt.watermark,
                "watermark_preview" : qt.watermark_preview,
                "watermark_frame" : qt.watermark_frame,
                "watermark_frame_file" : qt.watermark_frame_file}
            props_list = [
                qt.name, 
                qt.mute, 
                qt.settings, 
                qt.overridefps, 
                qt.sequencerate, 
                qt.auto_open, 
                qt.watermark, 
                qt.watermark_preview, 
                qt.watermark_frame, 
                qt.watermark_frame_file]
            qt_dict[name] = props
        
        ## Great, I have my dict. Now lets export it to a file.
        #print(json.dumps(qt_dict))
        with open(self.filepath, "w") as f:
            json.dump(qt_dict, f)
            
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class ImportQTList(bpy.types.Operator):
    bl_idname = 'render.import_qtlist'
    bl_label = 'Import a list of quicktimes to export from a file.'
    filepath = bpy.props.StringProperty(name = "filename", subtype = 'FILE_PATH', default = ((os.path.realpath(__file__).rsplit("/",1)[0]) + "/multiqtsettings/defaultsettingslist.txt"))
    
    def execute(self, context):
        print("Importing settings from: " + self.filepath)
        with open(self.filepath, "r") as f:
            qt_dict_restored = json.load(f)

        # Set the qt_settings appropriately:

        # First delete any existing QT settings:
        quicktimes = bpy.context.scene.multi_quicktime.quicktimes
        while len(quicktimes.items()) > 0:
            quicktimes.remove(0)
        #Set the active quicktime to something sensible:
        bpy.context.scene.multi_quicktime.active_quicktime = 0
        
        # Now create the replacements:
        new_quicktimes = qt_dict_restored.keys()
        for key in new_quicktimes:
            new_settings = qt_dict_restored[key]
            print("Doing settings for : " + key)
            bpy.ops.render.add_multi_quicktime(name = key)
            qt = quicktimes[key]
            qt.name = new_settings["name"]
            qt.mute = new_settings["mute"]
            qt.settings = new_settings["settings"]
            qt.overridefps = new_settings["overridefps"]
            qt.sequencerate = new_settings["sequencerate"]
            qt.auto_open = new_settings["auto_open"]
            qt.watermark = new_settings["watermark"]
            qt.watermark_preview = new_settings["watermark_preview"]
            qt.watermark_frame = new_settings["watermark_frame"]
            qt.watermark_frame_file = new_settings["watermark_frame_file"]
            print("Finished!")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    

#We need a user creatable list of quicktimes to create, each with a user defined settings file.


class MultiQuicktimes(bpy.types.PropertyGroup): #This holds the list of quicktimes to make.
    name = bpy.props.StringProperty(name="Filename", default = "Quicktime")
    settings = bpy.props.StringProperty(name="Settings",subtype='FILE_PATH', default = ((os.path.realpath(__file__).rsplit("/",1)[0]) + "/multiqtsettings/default.st"))
    mute = bpy.props.BoolProperty(name="Mute", default=True)
    overridefps = bpy.props.BoolProperty(name = "Override FPS", default = False)
    sequencerate = bpy.props.FloatProperty(name = "Sequence Rate", default = 25) #bpy.context.scene.render.fps) #Why wont this work?
    auto_open = bpy.props.BoolProperty(name="Open When Done", default = False)
    #Watermark Stuff
    #Video
    watermark = bpy.props.BoolProperty(name = "Watermark Video", default=False)
    watermark_file = bpy.props.StringProperty(name="Watermark Image",subtype = 'FILE_PATH',default = ((os.path.realpath(__file__).rsplit("/",1)[0]) + "/multiqtsettings/WatermarkDefault.png"))
    #Frame
    watermark_preview = bpy.props.BoolProperty(name = "Watermark Frame", default = False)
    watermark_frame = bpy.props.IntProperty(name="Preview Frame", default = 1)
    watermark_frame_file = bpy.props.StringProperty(name="Watermark Frame Image",subtype = 'FILE_PATH',default = ((os.path.realpath(__file__).rsplit("/",1)[0]) + "/multiqtsettings/WatermarkFrameDefault.png")) 
    

class MultiQuicktimeProps(bpy.types.PropertyGroup): #Class to hold basic props, plus functions to create new ones?
    multiquicktime_on = bpy.props.BoolProperty(
        name = "Multi-Quicktime",
        description = "Automatically generate multiple quicktime files once render finishes.",
        default = False)
    multiquicktime_overwrite = bpy.props.BoolProperty(
        name = "Overwrite",
        description = "Overwrite Existing Files. WARNING: Will not overwrite if a file is open in quicktime or elsewhere.",
        default = True)
    quicktimes = bpy.props.CollectionProperty(type=MultiQuicktimes)
    output_dir = bpy.props.StringProperty(name="Output Directory", subtype='DIR_PATH',description="Directory to send quicktime files to.", default = bpy.context.user_preferences.filepaths.temporary_directory)
    active_quicktime = bpy.props.IntProperty(name="Active Quicktime", default = 0)
    
    
# Now create the UI Stuff

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
        
        
#Handler code for auto sequencing after rendering.

#handle = "" #XXX UGLY Dummy Variable.
rendering_check = 0
animation_count = 0

@persistent
def render_started(scene):  #This gets assigned to render_pre
    global rendering_check, animation_count
    rendering_check = 1
    #print(rendering_check)
    
@persistent
def check_animation(scene): #This gets assigned to frame_change_post, used to count frames rendered.
    global rendering_check, animation_count
    if rendering_check == 1:
        animation_count += 1

@persistent
def kill_render(scene): #This gets assigned to render_cancel
    global rendering_check, animation_count
    if hasattr(handle, "status") and handle.status == True:
        rendering_check = 0
        animation_count = 0

@persistent
def end_render(scene): #This gets assigned to render_complete
    global rendering_check, animation_count
    if animation_count >=2:
            print("Anim Finshed")
            #Thing to run goes here:
            if bpy.context.scene.multi_quicktime.multiquicktime_on:
                bpy.ops.render.multi_quicktime()
        #End of thing to run.
    animation_count = 0
    rendering_check = 0
    
######

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

    
if __name__ == '__main__':
    register()