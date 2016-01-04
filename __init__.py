# Written by Trevor Harris aka BeigeAlert.
# Feel free to modify at your leisure, just make sure you
# give credit where it's due.
# Cheers! -Beige
# Last modified November 22, 2014

bl_info = {
    "name": "Natural Selection 2 Spark Geometry IO Script",
    "author": "Trevor \"BeigeAlert\" Harris",
    "blender": (2, 71, 0),
    "location": "File > Import-Export",
    "description": "Copies data between Blender and the Spark Editor via the clipboard.  Use these scripts in Blender, and Ctrl+C/Ctrl+V inside of Spark.",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "support": 'COMMUNITY',
    "category": "Import-Export"}
    
import bpy

from bpy.props import (BoolProperty, StringProperty)

class ImportSparkData(bpy.types.Operator):
    """Imports spark data from the clipboard"""
    bl_idname = "import_scene.spark"
    bl_label = "Spark Data from clipboard"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}
    
    #context group
    correct_units = BoolProperty(
        name = "Unit Correction",
        description = "Interpret Spark Data as inches, rather than meters, and have Blender conform to this.  Take, for example, a 64x64 inch square from Spark.  With this option enabled, this square will be 64x64 Blender Units.  With this option off, it will be 1.6256x1.6256 Blender Units (inches -> meters conversion!!!).",
        default = True,
        )
    
    correct_axes = BoolProperty(
        name = "Axes Correction",
        description = "Blender and Spark coordinate systems differ slightly.  This option will perform conversion operations to ensure that North, South, East, West, Up, and Down are identical in both software packages.  Recommend you leave this on.",
        default = True,
        )
    
    import_textures = BoolProperty(
        name = "Import Textures",
        description = "Attempt to import spark materials into Blender.  This will import only the albedo (diffuse) map from the texture, and it will be assigned as a UV layer in blender, NOT as a Blender material.  Ensure that the material files the imported data refer to are contained in one of the texture directories below, otherwise Blender will not know where to find the DDS texture files.",
        default = True,
        )
        
    tex_dir_1 = StringProperty(
        name = "Game Directory",
        description = "The script needs to know where the game textures are so it can make the proper associations when importing and exporting.  Example: \"C:\\Program Files (x86)\\Steam\\steamapps\\common\\Natural Selection 2\\ns2\\\"",
        default = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Natural Selection 2\\ns2\\",
        )
    
    tex_dir_2 = StringProperty(
        name = "Alternate Directory 1",
        description="An optional, additional directory to search for textures.  If you have custom textures included via a mod, this is where you should list the path to your \"output\" folder.  (eg. \"c:\\projects\\ns2mods\\myAwesomeLevelMod\\output\\ )",
        default = "",
        )
    
    tex_dir_3 = StringProperty(
        name = "Alternate Directory 2",
        description="Another optional, additional directory to search for textures.",
        default = "",
        )
    
    tex_dir_4 = StringProperty(
        name = "Alternate Directory 3",
        description="YET ANOTHER optional, additional directory to search for textures.",
        default = "",
        )
    
    tex_dir_5 = StringProperty(
        name = "Alternate Directory 4",
        description="You thought it was over with #3... but you were wrong... DEAD WRONG!  Here we are: THE FOURTH AND FINAL ALTERNATE TEXTURE DIRECTORY!!! MUAHAHAHAHAHAHAHA!!!",
        default = "",
        )

    def execute(self, context):
        from . import ImportSparkClipboard
        keywords = self.as_keywords()
        ImportSparkClipboard.ImportClipboardData(self, context, **keywords)
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class ExportSparkData(bpy.types.Operator):
    """Exports spark data to the clipboard"""
    bl_idname = "export_scene.spark"
    bl_label = "Spark Data to clipboard"
    bl_options = {'REGISTER', 'PRESET'}
    
    #context group
    selection_only = BoolProperty(
        name = "Selection Only",
        description = "Only export the selected objects.",
        default = True,
        )
        
    correct_units = BoolProperty(
        name = "Unit Correction",
        description = "Interpret Blender units as inches in Spark; otherwise 1 BU = 1 meter.",
        default = True,
        )
    
    correct_axes = BoolProperty(
        name = "Axes Correction",
        description = "Blender and Spark coordinate systems differ slightly.  This option will perform conversion operations to ensure that North, South, East, West, Up, and Down are identical in both software packages.  Recommend you leave this on.",
        default = True,
        )
    
    export_textures = BoolProperty(
        name = "Export Textures",
        description = "This exports the textures applied to each face via UV layers.  The file extension is changed to \".material\", and the file path is stripped off up to and including \"ns2\" and/or \"output\".  For example, if a face has a UV texture from \"C:\\Program Files (x86)\\Steam\\steamapps\\common\\Natural Selection 2\\ns2\\materials\\descent\\descent_ceiling_01.dds\", the new path becomes \"materials\\descent\\descent_ceiling_01.material\".  If this option is unchecked, the materials default to a developer texture. Muahahahahahaha!!!!!",
        default = True,
        )
        
    def execute(self, context):
        from . import ExportSparkClipboard
        keywords = self.as_keywords()
        ExportSparkClipboard.ExportClipboardData(self, context, **keywords)
        return {'FINISHED'}
        
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ImportSparkData.bl_idname, text="Spark Data (from clipboard)")

def menu_func_export(self, context):
    self.layout.operator(ExportSparkData.bl_idname, text="Spark Data (to clipboard)")

def register():
    bpy.utils.register_class(ImportSparkData)
    bpy.utils.register_class(ExportSparkData)
    bpy.types.INFO_MT_file_import.append(menu_func_import)
    bpy.types.INFO_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ImportSparkData)
    bpy.utils.unregister_class(ExportSparkData)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()

