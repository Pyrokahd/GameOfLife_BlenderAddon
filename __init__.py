bl_info = {
    "name" : "Game of Life",
    "author" : "Christian Herzog",
    "version" : (2, 0),
    "blender" : (3, 0, 0),
    "location" : "3D_Viewport > Sidebar(N) > Game of Life",
    "warning" : "Setting the parameter to high will lead to " \
     "long processing times! Check Window -> Toggle System_Console for info while running",
    "wiki_url" : "https://github.com/Pyrokahd/GameOfLife_BlenderAddon",
    "category" : "Simulation Render"
}

import bpy
import math
import numpy as np
import os
import re
from bpy.props import *
import time
import random 

#import bgl
#import bpy.utils.previews
#from gpu_extras.batch import batch_for_shader
#import gpu

###############################################
###############################################
########### PROPERTY UPDATE FUNCTIONS #########
###############################################
###############################################
def allow_image_preview(_self,context):
    """
    called from GameOfLifeProperties when changing image path.
    Also sets the start state image to be used later (or not depending on setting)
    """
    print("CHANGE PREVIEW IMAGETEXTURE...")
    
    #load image and image texture
    # self reference to propertygroup where i was called from (game_of_life_propertygroup)
    # from there we take the value for the property IMG_PATH
    imagepath = _self.IMG_PATH  
    
    # Create texture from image
    img = bpy.data.images.load(imagepath, check_existing=True) # load from disk path
    imagename = imagepath.split("/")[-1]
    if imagename in bpy.data.images.keys():
        print("Image already in blend file, loading from blend file instead...")
        img = bpy.data.images[imagename] # imagepath.split("/")[-1 returns the image name from path
        
    #img = bpy.data.images['test2.png']  # or read from blend file
    if not "previewTexture" in bpy.data.textures.keys():
        texture = bpy.data.textures.new(name="previewTexture", type="IMAGE")
    else:
        texture = bpy.data.textures["previewTexture"]
    texture.image = img
    tex = bpy.data.textures['previewTexture']
    tex.extension = 'CLIP' #EXTEND # CLIP # CLIP_CUBE # REPEAT # CHECKER
    tex.use_interpolation = False # to get clear pixels
    
    # CHANGE PointerProperty "preview_texture"
    _self.preview_texture = tex
    
    
    # CREATE START_STATE_IMAGE
    # delte previous start state image
    if "START_STATE_IMAGE" in bpy.data.images.keys():
        #bpy.data.meshes.remove(obj.data)
        bpy.data.images.remove(bpy.data.images["START_STATE_IMAGE"])
    # SET IMAGE IN BLEND FILE AS START_STATE_IMAGE
    if "START_STATE_IMAGE" not in bpy.data.images.keys():
        # create start img with same size as img
        start_img = bpy.data.images.new(name="START_STATE_IMAGE", width=img.size[0], height=img.size[1])
    else:
        print("SHOULD NEVER BE HEREE")
        start_img = bpy.data.images["START_STATE_IMAGE"]
    # copy the pixels
    start_img.pixels = img.pixels
    print("done loading START image")
    
                
# to correct illegal settings
def fix_size_x(self, context):
    if self.SPAWN_X > self.SIZE_X:
        self.SIZE_X = self.SPAWN_X
        
def fix_size_y(self, context):
    if self.SPAWN_Y > self.SIZE_Y:
        self.SIZE_Y = self.SPAWN_Y
        
def fix_spawn_x(self, context):
    if self.SPAWN_X > self.SIZE_X:
         self.SPAWN_X = self.SIZE_X
        
def fix_spawn_y(self, context):
    if self.SPAWN_Y > self.SIZE_Y:
        self.SPAWN_Y = self.SIZE_Y

###############################################
###############################################
########### MENU AND PROPERTY STUFF ###########
###############################################
###############################################    

# create custom property group
class  GameOfLifeProperties(bpy.types.PropertyGroup):

    preview_texture : PointerProperty (
        type = bpy.types.Texture,
        description = "temp storage for texture to be previewed"
    )
    
    life_cycles : IntProperty(
        name = "GAME ITERATIONS",
        description = "How many iterations for game of life",
        default = 10,
        min = 0
    )
    SIZE_X : IntProperty(
        name = "SIZE_X",
        description = "Map Size in X. Shoule be >= Spawn_X",
        default = 500,
        min = 1,
        max = 10000,
        update = fix_spawn_x
    )
    SIZE_Y : IntProperty(
        name = "SIZE_Y",
        description = "Map Size in Y. Shoule be >= Spawn_Y",
        default = 500,
        min = 1,
        max = 10000,
        update = fix_spawn_y
    )
    SPAWN_X : IntProperty(
        name = "SPAWN_X",
        description = "Spawn Area size in X. Is centered in map grid. Shoule be <= Size_X",
        default = 21,
        min = 1,
        max = 500,
        update = fix_size_x
    )
    SPAWN_Y : IntProperty(
        name = "SPAWN_Y",
        description = "Spawn Area size in Y. Is centered in map grid. Shoule be <= Size_Y",
        default = 21,
        min = 1,
        max = 500,
        update = fix_size_y
    )
    BIRTH_CHANCE : FloatProperty(
        name = "BIRTH_CHANCE",
        description = "Chance of spawning a game-cell per grid-cell at initialization. The higher the more cells spawn in the spawn area.",
        default = 0.2,
        min = 0.01,
        max = 1.0
    )
    SEED : IntProperty(
        name = "SEED",
        description = "Seed for random generation",
        default = 42,
        min = 0,
        max = 999999999
    )
    RESPAWN_ITER : IntProperty(
        name = "RESPAWN_ITER",
        description = "After How many Ingame Iterations should new cells spawn. They use the spawn area and Birth_chance that is set. Set 0 to deactivate!",
        default = 0,
        min = 0
    )
    MAX_RESPAWNS : IntProperty(
        name = "MAX_RESPAWNS",
        description = "How often respawn should trigger. 0 means for every xth iteration set in RESPAWN_ITERATIONS, so set 0 to deactivate!",
        default = 0,
        min = 0
    )
    MESH_DROPDOWN : EnumProperty(
        name = "MESH",
        description = "Defines which Mesh is used as cell. Plane has a much better performance!",
        items = [("CUBE", "Cube", "select cube"),
        ("PLANE",  "Plane", "Best Performance! Select plane"),
        ("SPHERE",  "UVSphere", "select UVSphere"),
        ("TORUS",  "Torus", "select Torus")],
        default = "PLANE"
    )
    RANDOM_COLOR : BoolProperty(
        name = "RANDOM_COLOR",
        description = "Wheter or not to use random colored materials for the cells",
        default = False
    )
    ANIMATE_CAM : BoolProperty(
        name = "ANIMATE_CAMERA",
        description = "Disable for using your own camera animation. with same amount of frames as game iterations.",
        default = True
    )
    ORTHO_CAM : BoolProperty(
        name = "Orthographic",
        description = "Activate, to set animated camera to be orthographic (else its perspective). If ANIMATE_CAMERA is disabled: NO EFFECT",
        default = True
    )
    COLOR_CHOICE : EnumProperty(
        description = "color",
        items = [
                ("DEFAULT", "'default_material'", "Default material for cells. A white Principled BSDF by default."+
                " Can be overwritten by creating your own material named 'custom_default_material'"),
                ("HIGHLIGHT",  "highlighting", "Uses 'default_material' but also highlights newly created cells "+
                "in green with a material named 'highlight_material'. Can be overwritten by creating your own material"+
                " named 'custom_highlight_material'."),
                ("RANDOM",  "random colors", "Creates a random color for each new cell")
                ],
        default = "HIGHLIGHT"
    )
    DEFAULT_COLOR: bpy.props.FloatVectorProperty(
        name="Default",
        description="Default cell color in RGBA. Can be overwritten by creating your own material named 'custom_default_material'",
        size=4,
        subtype="COLOR",
        default=(1, 1, 1, 1),
        min=0,
        max=1
        #update=update_view,  # some sort of connected update method?
    )
    HIGHLIGHT_COLOR: bpy.props.FloatVectorProperty(
        name="Highlight",
        description="Highlight cell color in RGBA. Can be overwritten by creating your own material named 'custom_highlight_material'",
        size=4,
        subtype="COLOR",
        default=(0, 0.6, 0, 1),
        min=0,
        max=1
        #update=update_view,  
    )
    
    EXPORT_PATH: bpy.props.StringProperty(
        name = "Export dir",
        description = "Path to a directory in which all rendered images are saved.",
        subtype = "DIR_PATH",
        default = "//gameoflife_out"
    )
    
    
    # PROPERTIES FOR EXPERIMENTAL SETTINGS PANEL
    
    IMG_PATH: bpy.props.StringProperty(
        name = "Start State Image",
        description = "Select an image to represent the start state. Each black Pixel in the image"+
        " will be one cell at start!  If an image with the same name is already in the blendfile, this will be used instead!"+
        "   If the image is larger (width and height) than the game SIZE, this setting will be ignored!",
        subtype = "FILE_PATH",
        default = "",
        update = allow_image_preview
    )
    USE_START_IMG : BoolProperty(
        name = "USE THIS IMAGE AS START STATE",
        description = "If True and an image is loaded as Start State, each black pixel in the image will"+
        " spawn as a cell when starting, instead of the normal random spawn."+
        "   If the image is larger (width and height) than the game SIZE, this setting will be ignored!",
        default = False
    )
    
    # my_enum : bpy.props.EnumProperty{name="Enum Dropdown",
    # description="desctp" items = [("op1",  "text op1", "value") , ("op2",  "text op2", "value2")]}

# add panel

class GoL_panel(bpy.types.Panel):
    bl_label = "Game of Life"  # is shown as name of the panel
    bl_idname = "OBJECT_PT_GoL_Panel"  # just an id but convention wants _PT_ for panel
    # where in which window should it be
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # the N button windows
    bl_category = 'Game of Life'  # or "new tab" for something new
    
    
    def draw(self, context):
        layout = self.layout
        game_of_life_propertygroup = context.scene.game_of_life_propertygroup
        
        
        col_req = layout.column(heading = "Requirements")
        col_req.label(text="GameOfLife Scene Requirements:", icon="ERROR")
        col_req.label(text="A Camera named 'Camera'", icon="DECORATE" )
        col_req.label(text="A light source (SUN/HDRI)", icon="DECORATE")
        col_req.label(text="Saved this .blend file", icon="DECORATE")
        
        
        col_params = layout.box().column(heading = "PARAMETER:")
        col_params.prop(game_of_life_propertygroup, "life_cycles")
        #col_params.label(text="Make SIZE >= SPAWN!")
        size_row = col_params.row()
        size_row.prop(game_of_life_propertygroup, "SIZE_X")
        size_row.prop(game_of_life_propertygroup, "SIZE_Y")
        spawn_row = col_params.row()
        spawn_row.prop(game_of_life_propertygroup, "SPAWN_X")
        spawn_row.prop(game_of_life_propertygroup, "SPAWN_Y")
        col_params.prop(game_of_life_propertygroup, "BIRTH_CHANCE")
        col_params.prop(game_of_life_propertygroup, "SEED")
        respawn_row = col_params.row()
        respawn_row.prop(game_of_life_propertygroup, "RESPAWN_ITER")
        respawn_row.prop(game_of_life_propertygroup, "MAX_RESPAWNS")
        col_params.prop(game_of_life_propertygroup, "MESH_DROPDOWN")
        col_params.label(text="Color choice:")
        col_params.row().prop(game_of_life_propertygroup, "COLOR_CHOICE", expand = True)
        color_rows = col_params.row()
        color_rows.prop(game_of_life_propertygroup, "DEFAULT_COLOR")
        color_rows.prop(game_of_life_propertygroup, "HIGHLIGHT_COLOR")
        
        expects = layout.column().box()
        expectsrow = expects.row()
        expectsrow.prop(game_of_life_propertygroup, "ANIMATE_CAM")
        expectsrow.prop(game_of_life_propertygroup, "ORTHO_CAM")
        expects.label(text="Expects quadratic aspect ratio (Resolution)", icon="OUTPUT")
        
        warn_col = layout.column()
        warn_col.label(text="It is slow when spawning lots of cells!", icon="MEMORY")
        
        
        col_expl = layout.column(heading = "")
        #col_expl.label(text="Every Iteration also increases current frame.")
        #col_expl.label(text="Renders are saved in directory of this blend file.", icon="FILE_FOLDER")
        col_expl.prop(game_of_life_propertygroup, "EXPORT_PATH")
        
        
        col_run = layout.column(heading_ctxt = "run simulation")
        col_run.label(text="Open System_Console FIRST for info", icon="INFO")
        # creates button to execute operator
        col_run.operator("addonname.start_gameoflife")  # bl_idname of my operator
        # bl_label is used as title for the button = "Render GameOfLife"
        
        col_info = layout.column(heading="additional info")  # not showing header, why?
        col_info.label(text="Last Game State will be visible in scene.")
        
        #col_info.popover("OBJECT_PT_GoL_exp_Panel")  # seems to be more for choosing textures, materials and such
                
                            ##col_info.prop_search(bpy.data, "textures", bpy.data, "images")  # just some silly tests

        # Need pointer properties for that however they work...
        #col.template_ID_preview(bpy.data.images, "Image", new="test2.png",)


class GoL_exp_settings_panel(bpy.types.Panel):
    """
    A new Panel for settings for experimental features, new panel to no overcrowd the main panel
    """
    bl_label = "Experimental Settings"  # is shown as name of the panel
    bl_idname = "OBJECT_PT_GoL_exp_Panel"  # just an id but convention wants _PT_ for panel
    # where in which window should it be (BELOW THE MAIN PANEL)
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # the N button windows
    bl_category = 'Game of Life'
    
    def draw(self, context):
        layout = self.layout
        game_of_life_propertygroup = context.scene.game_of_life_propertygroup
        
        col_exp = layout.column(heading="")
        col_exp.label(text="EXPERIMENTAL SETTINGS:")
        col_exp_box = col_exp.box()
        
        col_exp_box.label(text="Load an image, to spawn a cell for each black pixel.")
        col_exp_box.prop(game_of_life_propertygroup, "IMG_PATH")
        col_exp_box.prop(game_of_life_propertygroup, "USE_START_IMG")
        
        
        #name = game_of_life_propertygroup.IMG_PATH
        #print("now in draw")
        #print(game_of_life_propertygroup.preview_tex )
        
        if game_of_life_propertygroup.preview_texture != None:
            layout.column().label(text="")
            # Preview texture texturepreview
            col_exp_box.label(text="Preview:    (rescale to refresh the view)")
            col_exp_box.template_preview(game_of_life_propertygroup.preview_texture)

        
##########################################
##########################################
########### GAME OF LIFE STUFF ###########
##########################################
##########################################

# rule 1: Cells with one or no neighbour die
# rule 2: cells with four or more neighbours die
# rule 3: cells with two or three noighbours survive)
# rule 4: a field with three neighbours becomes a cell

# NOTE THERE IS NO LIFE UPDATE IN THE VIEWPORT, ALL WILL BE DONE IN THE EXECUTE 
# VIEWPORT ONLY UPDATES AFTER THE WHOLE SCRIPT IS RUN!
# THEREFOR VIEWPORT ONLY SHOWS THE LAST STATE

class Worldgrid():
    """Create a world from an 2 dim array"""
    def __init__(self, x, y):
        # size is x y
        self.size = (x,y) # -1 because with array of size 5 max index is 4
        self.world = np.zeros((x,y), dtype=int)  # world = numpy array of size x,y
        
    def get_world(self):
        return self.world
    
    def get_size(self):
        return self.size
    
    def add_cell(self,x,y):
        self.world[x][y] = 1

    def remove_cell(self,x,y):
        self.world[x][y] = 0
        
    def set_world(self, newarray):
        self.world = newarray

def check_cell_status(x,y,world):
    """returns 0 if a cell does and 1 if it lifes:"""
    

def render_output(iteration, output_dir, operator, output_file_pattern_string = '%d-iteration_%d.jpg'):
    """
    Render the current image/state to the given output path. Use "iteration" to define the number behind image name.
    """
    # saved file or specificly set path 
    if bpy.data.is_saved or (output_dir != "" or output_dir != "//gameoflife_out" ):
        bpy.context.scene.render.filepath = os.path.join(output_dir, (output_file_pattern_string % (iteration, iteration)))
        bpy.ops.render.render(write_still = True)
    else:
        print("BLEND FILE NOT SAVED!, NO RENDERS ARE SAVED!")
        operator.report({'INFO'}, "NO RENDER SAVED! Please save your blend file first")


def create_random_color_list(COLOR_CHOICE):
    # Remove old Materials 
    #print("remove")
    for mat in  bpy.data.materials:
        if re.search(r"^RandMat", mat.name) != None and re.search(r"^RandMat", mat.name).group() == "RandMat":
            #print(mat)
            bpy.data.materials.remove(mat)
            
    all_mats = []
    # only create if random color = true, else the scene has to many colors
    if COLOR_CHOICE == "RANDOM":
        #RED
        end_step = 1.05
        step_size = 0.15
        
        for c1 in np.arange(0, end_step, step_size):
            mat = bpy.data.materials.new(name="RandMat.001") #set new material to variable
            mat.diffuse_color = (1, round(c1,2), 0, 1) #change color RGBA
            all_mats.append(mat)
        for c1 in np.arange(0, end_step, step_size):
            mat = bpy.data.materials.new(name="RandMat.001") #set new material to variable
            mat.diffuse_color = (1, 0, round(c1,1), 1) #change color RGBA
            all_mats.append(mat)
            
        #GREEN
        for c1 in np.arange(0, end_step, step_size):
            mat = bpy.data.materials.new(name="RandMat.001") #set new material to variable
            mat.diffuse_color = (0, 1, round(c1,1), 1) #change color RGBA
            all_mats.append(mat)
        for c1 in np.arange(0, end_step, step_size):
            mat = bpy.data.materials.new(name="RandMat.001") #set new material to variable
            mat.diffuse_color = (round(c1,2), 1, 0, 1) #change color RGBA
            all_mats.append(mat)
            
        #BLUE
        for c1 in np.arange(0, end_step, step_size):
            mat = bpy.data.materials.new(name="RandMat.001") #set new material to variable
            mat.diffuse_color = (round(c1,2), 0, 1, 1) #change color RGBA
            all_mats.append(mat)   
        for c1 in np.arange(0, end_step, step_size):
            mat = bpy.data.materials.new(name="RandMat.001") #set new material to variable
            mat.diffuse_color = (0, round(c1,1), 1, 1) #change color RGBA
            all_mats.append(mat)   
        
        # add some more because pure colors are underrepresented in this init
        #more red
        mat = bpy.data.materials.new(name="RandMat.001") #set new material to variable
        mat.diffuse_color = (1, 0, 0, 1) #change color RGBA
        all_mats.append(mat)
        #more greend
        mat = bpy.data.materials.new(name="RandMat.001") #set new material to variable
        mat.diffuse_color = (0, 1, 0, 1) #change color RGBA
        all_mats.append(mat)  
        #more blue
        mat = bpy.data.materials.new(name="RandMat.001") #set new material to variable
        mat.diffuse_color = (0, 0, 1, 1) #change color RGBA
        all_mats.append(mat)   
        mat = bpy.data.materials.new(name="RandMat.001") #set new material to variable
        mat.diffuse_color = (0, 0, 1, 1) #change color RGBA
        all_mats.append(mat)   
        
    return all_mats    
    
    
    
    #activeObject = bpy.context.active_object #Set active object to variable
    mat = bpy.data.materials.new(name="MaterialName") #set new material to variable
    mat.diffuse_color = (1, 0, 0) #change color    
    #activeObject.data.materials.append(mat) #add the material to the object
    bpy.context.object.active_material.diffuse_color = (1, 0, 0) #change color    
    
    

def create_cube(X, Y, _world, CUBE_MAT):
    """
    Creates a cube at given coords. 
    World is used to get the size of the grid for a proper Offset to center the cubes
    """
    #start = time.time() ###
    
    # set location in grid  # +1 because here we need the max index not the max length
    # we shift the position of the cubes based on the index! to center the visuals
    # floor to round down to int. i.e. a 3x3 grid needs to be shifted by 1 along X and Y to center it (not by 2)
    x_pos = np.floor( (X)-0.5*_world.get_size()[0] )+1  # center grid to origin by spawning all cubes with offset
    y_pos = np.floor( (Y)-0.5*_world.get_size()[1] )+1

    
    bpy.ops.mesh.primitive_cube_add(size=0.9, calc_uvs=True, location=(x_pos,y_pos,0))
    current_cube = bpy.context.active_object
    current_cube.name = "Cell"
    
    #end = time.time() ###
    #print(f"Create cube: {end - start}") ###
    
    # set material
    current_cube.data.materials.append(CUBE_MAT) #
    
def create_plane_quick(X, Y, _world, CUBE_MAT):
    """
    Creates a Plane at given coords. 
    World is used to get the size of the grid for a proper Offset to center the cubes
    """
    # 1000 planes with this take 0.353 sec instead of 60.286 sec with create_plane()!
    
    x_pos = np.floor( (X)-0.5*_world.get_size()[0] )+1  # center grid to origin by spawning all cubes with offset
    y_pos = np.floor( (Y)-0.5*_world.get_size()[1] )+1
    
    size = 0.9
    size = size/2

    name = "Cell"
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    obj.location = (x_pos,y_pos,0) # SET OBJ ORIGIN
    coll = bpy.data.collections.get("Collection")  # get collection
    coll.objects.link(obj)  # link to collection in outliner
    bpy.context.view_layer.objects.active = obj  # make new object selected

    verts = []
    edges = []
    faces = []
    
    # VERTS RELATIVE TO ORIGIN!
    verts.append((-size,-size,0))  # uses X Y Z coords
    verts.append((-size,+size,0))
    verts.append((+size,+size,0))
    verts.append((+size,-size,0))
    #edges.append((0,1))  # no edges needed, because the face will create them by default
    faces.append((0,1,2,3))  # uses indecies from verts array 
    
    # simplest version to create mesh https://docs.blender.org/api/current/bpy.types.Mesh.html
    # bmesh allows for more complex stuff  https://docs.blender.org/api/current/bmesh.html
    mesh.from_pydata(verts, edges, faces)

    obj.data.materials.append(CUBE_MAT) # append material to active object


def create_plane(X, Y, _world, CUBE_MAT):
    """ 
    DEPRICATED use create_plane_quick()!
    Creates a Plane at given coords. 
    World is used to get the size of the grid for a proper Offset to center the cubes
    """
    
    # set location in grid  # +1 because here we need the max length not the max index
    # we shift the position of the cubes based on the offset between map and spawn map! to center the visuals
    # floor to round down to int. i.e. a 3x3 grid needs to be shifted by 1 along X and Y to center it (not by 2)
    x_pos = np.floor( (X)-0.5*_world.get_size()[0] )+1  # center grid to origin by spawning all cubes with offset
    y_pos = np.floor( (Y)-0.5*_world.get_size()[1] )+1

    
    bpy.ops.mesh.primitive_plane_add(size=0.9, calc_uvs=True, location=(x_pos,y_pos,0))
    current_plane = bpy.context.active_object
    current_plane.name = "Cell"
    
    # set material
    current_plane.data.materials.append(CUBE_MAT) #
    
def create_torus(X, Y, _world, CUBE_MAT):
    x_pos = np.floor( (X)-0.5*_world.get_size()[0] )+1
    y_pos = np.floor( (Y)-0.5*_world.get_size()[1] )+1
    bpy.ops.mesh.primitive_torus_add(generate_uvs =True, location=(x_pos,y_pos,0), major_segments=22, minor_segments=10,
    major_radius=0.35, minor_radius=0.12)
    current_obj = bpy.context.active_object
    bpy.ops.object.shade_smooth()  # shade active smooth
    current_obj.name = "Cell"
    current_obj.data.materials.append(CUBE_MAT) #
    
def create_uvsphere(X, Y, _world, CUBE_MAT):
    x_pos = np.floor( (X)-0.5*_world.get_size()[0] )+1
    y_pos = np.floor( (Y)-0.5*_world.get_size()[1] )+1
    bpy.ops.mesh.primitive_uv_sphere_add(calc_uvs =True, location=(x_pos,y_pos,0), radius=0.45)
    current_obj = bpy.context.active_object
    bpy.ops.object.shade_smooth()  # shade active smooth
    current_obj.name = "Cell"
    current_obj.data.materials.append(CUBE_MAT) #

    
def delete_all_cells():
    for obj in bpy.data.objects:
        # check if mesh name starts with "Cube" or "Plane"
        if re.search(r"^Cell", obj.name) != None and re.search(r"^Cell", obj.name).group() == "Cell":
            bpy.data.meshes.remove(obj.data, do_unlink=True) # delete mesh #this also deletes the obj
            #bpy.data.objects.remove(obj, do_unlink=True)  # del only object
    for mesh in bpy.data.meshes:
        if ((re.search(r"^Sphere", mesh.name) != None and re.search(r"^Sphere", mesh.name).group() == "Sphere") or
            (re.search(r"^Torus", mesh.name) != None and re.search(r"^Torus", mesh.name).group() == "Torus") or
            (re.search(r"^Plane", mesh.name) != None and re.search(r"^Plane", mesh.name).group() == "Plane") or
            (re.search(r"^Cube", mesh.name) != None and re.search(r"^Cube", mesh.name).group() == "Cube") or
            (re.search(r"^Cell",mesh.name) != None and re.search(r"^Cell", mesh.name).group() == "Cell")):
            bpy.data.meshes.remove(mesh, do_unlink=True)  # del only object

def update_visuals(_world, CUBE_MAT, HIGHLIGHT_MAT, pre_map, my_mesh = "PLANE", ALL_MATS = [], COLOR_CHOICE = "DEFAULT"):
    """
    Removes all cubes in the world then creates new cubes based on world array
    _world = current world 
    pre_map = world array of previous iteration, to only update changed locations
    CUBE_MAT is the default_mat, its called CUBE because it used to be only for cubes
    spawn_mat is HIGHLIGHT_MAT
    -
    ALL_MATS means all random materials it does not include CUBE_MAT or HIGHLIGHT_MAT
    """
    spawn_mat = HIGHLIGHT_MAT 
    cube_mat_create = CUBE_MAT  # to change material but still keep original as CUBE_MAT   
    
    # transpose map because its created with np array[x=columns][y=rows] but visualls its [x=rows][y=columns]
    current_map = np.copy(_world.get_world())
    current_map = np.transpose(current_map)
    
    # same offset as by create_plane / cube, also - offset !, gleiche operation rückgängig
    # then use map[y][x] to compare because np array first index is row then column
    offsetx = np.floor(-0.5*_world.get_size()[0])+1
    offsety = np.floor(-0.5*_world.get_size()[1])+1
    
    #############################
    # remove mesh of dead cells #   
    #############################
    # needs to be data.objects to get location! (not #bpy.data.meshes)
    for obj in bpy.data.objects:
        # check if mesh name starts with "Cube" or "Plane"
        if re.search(r"^Cell", obj.name) != None and re.search(r"^Cell", obj.name).group() == "Cell":
            #remove mesh if not already there and still there in current map[Y][X]
            # indecies need to be int
            if not current_map[int(obj.location[1]-offsety)][int(obj.location[0]-offsetx)] == 1:
                bpy.data.meshes.remove(obj.data) # delete mesh #this also deletes the obj
                #bpy.data.objects.remove(obj, do_unlink=True)  # del only object
                 
    # 1. check where is a 1 in the array
    ## NOTE: technically we get indy then indx, because first index in numpy array
    ### is for row and second for column. But since we also create the cells with [x][y]
    ### it is consistent and works. (the game logic has 0,0 in top left and the visuals in bot left)
    ### which is no problem because its decoupled. 
    ### !Except! when comparing object location with numpy array location.
    ### Thats why in this case we use [y][x] (in the for loop above this text)
    ### And why array of the map is transposed for comparison betwwen visual and logic


    ####################
    # Create new cells #   
    ####################
    #pre_map = np.transpose(pre_map)
    
     # get indecies where the array == 1
    indx, indy = np.nonzero(_world.get_world() == 1)  # returns two lists (1 dim) one for each index [][]
    actually_created = 0   ###
    start = time.time() ###
    print(f"cells alive: {len(indx)}") ##
    print(f"Creating cells...")
    # loop through those index pairs and create cubes at all positions with value = 1
    for i in range(len(indx)):
        _x = indx[i]
        _y = indy[i]
        # only create if not already 1 in previous map
        if not pre_map[_x][_y] == 1:    
            # wenn random color = true und ALL_MATS not empty, override CUBE_MAT
            if COLOR_CHOICE == "RANDOM" and (ALL_MATS != None and len(ALL_MATS) > 0):
                cube_mat_create = random.choice(ALL_MATS) 
            # Set new spawning cells to green
            elif COLOR_CHOICE == "HIGHLIGHT": 
                cube_mat_create = spawn_mat
            
            if my_mesh == "CUBE":
                create_cube(_x, _y, _world, cube_mat_create)
                actually_created+=1
            elif my_mesh == "PLANE":
                create_plane_quick(_x, _y, _world, cube_mat_create)
                actually_created+=1
            elif my_mesh == "SPHERE":
                create_uvsphere(_x, _y, _world, cube_mat_create)
                actually_created+=1
            elif my_mesh == "TORUS":
                create_torus(_x, _y, _world, cube_mat_create)
                actually_created+=1
    
    # here it is about visual and data structure therefore transpose and swap x and y again:
    pre_map = np.transpose(pre_map)
    # also if COLOR_CHOICE == HIGHLIGHT, set already living cells from previous iteration to default 
    if COLOR_CHOICE == "HIGHLIGHT":
        for obj in bpy.data.objects:
            # if object is cube or plane
            if (re.search(r"^Cell", obj.name) != None and re.search(r"^Cell", obj.name).group() == "Cell"):
                # if it already was 1 (alive) in previous
                if pre_map[ int(obj.location[1]-offsety) ][ int(obj.location[0]-offsetx) ] == 1:
                    # check if default material is in its material list
                    if "default_material" not in obj.material_slots.keys(): # and "Material" not in obj.material_slots.keys():
                        obj.data.materials[0] = CUBE_MAT  # set active mat to cube mat
                        
                            ### example of adding to mat list (assigning only works in edit mode though)
                            ## add new material 
                            ## set new material as active slot
                            #obj.active_material_index = obj.material_slots.keys().index("default_material")  #assign index of cube material
                            ## assign material
                            #obj.data.materials[0] = CUBE_MAT   
    
    end = time.time() ###
    print(f"actually created {actually_created}") ###
    print(f"create time: {end - start}") ###

    

def get_relevant_cells(_world):
    """
    returns a list of all relevant cells to be checked for updating according to game of life rules.
    each cell is a tuple of x and y coordinate: (x,y) in int.
    """
    # To update the cells in the world array we have to check which Game of Life Rules apply
    # Relevant are only alive cells and their neighbours since new cells only appear next to alive cells
    relevant_cells = []  # save cells as (x,y) pair. (a cell class could also be made)
    
    # temporary for looping over all cells.
    # Because if we add stuff to a list while we loop it
    # we get the wrong result 
    relevant_cells_temp = []  
    
    # get all cells that are alive  (just like in update visuals)
    indx, indy = np.nonzero(_world.get_world() == 1)
    for i in range(len(indx)):
        relevant_cells.append((indx[i], indy[i])) 
    
    #print("Nodes with 1")
    #print(relevant_cells)
    
    relevant_cells_temp = relevant_cells.copy()
        
    # get all neighbours
    for cell in relevant_cells_temp:  
        # FOR ALL NEIGHBOUR CELLS WE HAVE TO:
        # check if out of bounds!
        # check if already in relevenat_cells
        # Note: the grid has 0,0 in top left (thats how numpy arrays work)
        # Note: for the viewport however it is bottom left (because we make - offset in bot directions
        # by rotating camera along X 180° we would have the same view
        
        # cell[0] is x and cell[1] is y
        x = cell[0]
        y = cell[1]
        max_x = _world.get_size()[0]-1  # we want max index not max length
        max_y = _world.get_size()[1]-1
        
        # TOP ROW #
        # top
        if not y-1 < 0:
            cell_to_add = (x,y-1)
            if not cell_to_add in relevant_cells:
                relevant_cells.append( cell_to_add )
        # top left
        if not x-1 < 0 and not y-1 < 0:
            cell_to_add = (x-1,y-1)
            if not cell_to_add in relevant_cells:
                relevant_cells.append( cell_to_add )
        # top right
        if not x+1 > max_x and not y-1 < 0:
            cell_to_add = (x+1,y-1)
            if not cell_to_add in relevant_cells:
                relevant_cells.append( cell_to_add )
        # MID ROW #
        # left
        if not x-1 < 0:
            cell_to_add = (x-1,y)
            if not cell_to_add in relevant_cells:
                relevant_cells.append( cell_to_add )
        #right
        if not x+1 > max_x:
            cell_to_add = (x+1,y)
            if not cell_to_add in relevant_cells:
                relevant_cells.append( cell_to_add )
        # BOT ROW #
        # bot
        if not y+1 > max_y:
            cell_to_add = (x,y+1)
            if not cell_to_add in relevant_cells:
                relevant_cells.append( cell_to_add )
        # bot left
        if not y+1 > max_y and not x-1 < 0:
            cell_to_add = (x-1,y+1)
            if not cell_to_add in relevant_cells:
                relevant_cells.append( cell_to_add )
        # bot right
        if not y+1 > max_y and not x+1 > max_x:
            cell_to_add = (x+1,y+1)
            if not cell_to_add in relevant_cells:
                relevant_cells.append( cell_to_add )
    return relevant_cells

def count_neighbours(cell, _world, currentgrid):
    """
    Takes a cell: (x,y) tuple, and counts how many alive neighbours it has
    """
    count = 0
    x = cell[0]
    y = cell[1]
    
    max_x = _world.get_size()[0]-1  # we want max index
    max_y = _world.get_size()[1]-1 
    
    worldgrid = currentgrid #_world.get_world()
    # TOP ROW #
    # top
    if not y-1 < 0:
        cell_to_check = (x,y-1)
        if worldgrid[cell_to_check[0]][cell_to_check[1]] == 1:  # worldgrid[new_x][new_y]
            #print("top")
            count += 1
    # top left
    if not x-1 < 0 and not y-1 < 0:
        cell_to_check = (x-1,y-1)
        if worldgrid[cell_to_check[0]][cell_to_check[1]] == 1:
            #print("top left")
            count += 1
    # top right
    if not x+1 > max_x and not y-1 < 0:
        cell_to_check = (x+1,y-1)
        if worldgrid[cell_to_check[0]][cell_to_check[1]] == 1:
            #print("top right")
            count += 1
    # MID ROW #
    # left
    if not x-1 < 0:
        cell_to_check = (x-1,y)
        if worldgrid[cell_to_check[0]][cell_to_check[1]] == 1:
            #print("left")  #####
            count += 1
    # right
    if not x+1 > max_x:
        cell_to_check = (x+1,y)
        if worldgrid[cell_to_check[0]][cell_to_check[1]] == 1:
            #print("right")
            count += 1
    # BOT ROW #
    # bot
    if not y+1 > max_y:
        cell_to_check = (x,y+1)
        if worldgrid[cell_to_check[0]][cell_to_check[1]] == 1:
            #print("bot")   ###
            count += 1
    # bot left
    if not y+1 > max_y and not x-1 < 0:
        cell_to_check = (x-1,y+1)
        if worldgrid[cell_to_check[0]][cell_to_check[1]] == 1:
            #print("bot left")
            count += 1
    # bot right
    if not y+1 > max_y and not x+1 > max_x:
        cell_to_check = (x+1,y+1)
        if worldgrid[cell_to_check[0]][cell_to_check[1]] == 1:
            #print("bot right")  ###
            count += 1 
    return  count
    

def update_cells(_relevant_cells, _world):
    """
    Sets all relevant cells in the array to 0 or 1 according to the game of life rules.
    Cells are still tuples in form (x,y)
    """
    # rule 1: Cells with one or no neighbour die
    # rule 2: cells with four or more neighbours die
    # (rule 3: cells with two or three noighbours survive)
    # rule 4: a field with three neighbours becomes a cell
    
    dead_cells = []
    alive_cells = []
    temp_world_grid = np.copy(_world.get_world())
    
    for cell in _relevant_cells:
        n_count = count_neighbours(cell, _world, temp_world_grid)
        # RULE 1 and 2
        if n_count <= 1 or n_count >= 4:
            dead_cells.append(cell)
        # RULE 3, but only for cells that are already alive !
        elif (n_count == 2) and _world.get_world()[cell[0]][cell[1]] == 1:
            alive_cells.append(cell)
        # RULE 4
        elif n_count == 3:
            alive_cells.append(cell)
    
    # this updates the world object in def execute since _world is a relative variable
    # that points to the original
    for dead_cell in dead_cells:
        _world.remove_cell(dead_cell[0],dead_cell[1]) 
        
    for alive_cell in alive_cells:
        _world.add_cell(alive_cell[0],alive_cell[1])                             



def init_map_witharea(_world, area, birth_chance = 0.1):
    """
    Variant of ini_map with a define area in the middle of the map.
    Only in this area cells will spawn
    area is tuple of x and y
    """
    
    # offset relative to world size and areasize
    worldsize = _world.get_size()
    areasize = area
    
    # EXPECTS QUADRATIC SIZES for simplicity
    offsetx = worldsize[0]-areasize[0]  # +1 because now we need full length and not indecies
    offsety = worldsize[1]-areasize[1]
    # Half of that offset needs to be added to each point in order to center
    # the "inner square" with the "outer square", which is our world array.

    for x in range(area[0]):
        for y in range(area[1]):
            chance = random.uniform(0,1)  # random float between 0 and 1
            if chance <= birth_chance:
                # difference between rounding with floor and int doesnt matter.
                # if the number is uneven (like 1.5) that means you cant center 
                # the inner square because then you have something like a 3x3 square in 4x4 square
                # and we only work with ints in a grid! So int instead of floor just means
                # it leans to the right bottom instead of left top
                # however we do need an int in the end to use as index
                
                # That offset is only needed here since all other cells use those cells as reference points
                _world.add_cell(x+ int(np.floor(offsetx/2)), y+ int(np.floor(offsety/2)) )
                
                
def blender_image_to_numpy_array(img):
    """
    Takes a blender img and returns it as a numpy array in which dark pixels are 1 and light are 0.
    """
    # GET IMAGE WIDTH
    width = img.size[0]
    height = img.size[1]

    # GET PIXELS AS RGB LIST
    all_rgb_pixels = []
    rgb_pixel = []
    i = 0
    # 5x5 = 25 pixel with 4 channel RGBA
    # loop over all pixels, group RGBA together and add to list
    for pixelvalue in img.pixels:
        i += 1
        if i % 4 == 0:
            all_rgb_pixels.append(rgb_pixel)
            rgb_pixel = []
        # to ignore the A value only append if its not the fourth
        else: 
            rgb_pixel.append(pixelvalue)
            
    # CONVERT PIXEL TO GREYSCALE
    imagegrey = []
    for pixel in all_rgb_pixels:
        R, G, B = pixel[0], pixel[1], pixel[2]
        greypixel = round(0.2989 * R + 0.5870 * G + 0.1140 * B, 1)
        # REVERT TO 1 FOR BLACK PIXEL AND 0 FOR WHITE! (we want cells to be black = 1, but RGBA has black as 0)
        if greypixel > 0.5:
            greypixel = 0
        else:
            greypixel = 1
        imagegrey.append(greypixel)
    
    # RECONSTRUCT IMAGE 
    # to shape it into nparray[width][height]
    imageArrayRestructured = []
    row = []
    n = 0
    for pixel in imagegrey:
        n += 1
        row.append(pixel)
        if n % width == 0 and n != 0:
            imageArrayRestructured.append(row)
            row = []
    imageArrayRestructured = np.array(imageArrayRestructured)
    
    # We need to transpose!, the image is read from bot to top but then saved from top to bot which flipped it
    imageArrayRestructured = np.transpose(imageArrayRestructured)
    #print(imageArrayRestructured)
    return imageArrayRestructured   
                
                
def init_map_with_start_img(_world, start_state_image):
    """
    Takes an image and converts every black pixel (or dark in generell) into a cell.
    """
    start_state_img_array = blender_image_to_numpy_array(start_state_image)
    map = np.copy(_world.get_world())
    
    offsetx = int((_world.get_world().shape[0]-start_state_img_array.shape[0])/2)
    offsety = int((_world.get_world().shape[1]-start_state_img_array.shape[1])/2) 

    # directly manipulates world array instead of adding cells
    for x in range(start_state_img_array.shape[0]):
        for y in range(start_state_img_array.shape[1]):  
            map[x+offsetx][y+offsety] = start_state_img_array[x][y]
            
    # Rotate because ( not needed )  
    #map = np.rot90(map, k=0, axes=(0,1))
    _world.set_world(map)
    print("Map initialized with image...")
    
    
    
def get_max_distance_from_center(r_cells, _world):
    """
    The max distance of the furthest cell relativ to map center,
    with the offsets (0,0 is top left and not center). In Numpy array.
    In viewport 0,0 is bot left!
    
    Example: If map is of size 5 
    and index is 2
    the actual max index is 2 - (5/2) = -0.5 then absolute and floor => 0 
    since index 2 is the center of a 5x5 grid (along this axis)
    """
    # current index / Hälfte
    #  absolut nehmen und dann floor 
    max_size_x = _world.get_size()[0]
    max_size_y = _world.get_size()[1]

    
    max_distance=0
    
    for cell in r_cells:
        distancex = cell[0] - (max_size_x/2)
        distancex = np.absolute(distancex)
        distancex = np.floor(distancex)
        #print(f"distancex {distancex}")
        if distancex > max_distance:
            max_distance = distancex
            
        distancey = cell[1] - (max_size_y/2)
        distancey = np.absolute(distancey)
        distancey = np.floor(distancey)
        #print(f"distancey {distancey}")
        if distancey > max_distance:
            max_distance = distancey
            
    #print(f"max distance {max_distance}")
    return max_distance

def adjust_camera(camera, center_grid_size):
    """
    Adjust camera z axis according to center_grid_size (which encloses all cells).
    Basically set it so that we see all cubes in the scene
    """
    #camera on z = 10 sees 7x7 grid
    # ratio is 10/7 = 1.429 => camera z = Size.X * 1.429  (changed to 1.35 to be closer )
    # size.x is now defined by the position of the cell the furthest away from origin BUT:
    # even if this is coded correctly it would lead to weird jumps!
    
    # IF CAMERA IS ORTHOGONAL CHANGE ORTHO SCALE
    if bpy.data.cameras["Camera"].type == "ORTHO":
        if bpy.data.cameras["Camera"].ortho_scale < round(center_grid_size, 3):
            print(f"SET CAMERA ORTHO SCALE TO: {round(center_grid_size, 3)}")
            bpy.data.cameras["Camera"].ortho_scale = round(center_grid_size, 3) 
    # ELSE MOVE CAMERA ALONG Z AXIS
    else:
    # only if it increases camera range, we dont want decreases that would be weird jump cuts
        if camera.location[2] < round(center_grid_size*1.45, 3):
            print(f"SET CAMERA TO: {round(center_grid_size*1.45, 3)}")
            camera.location[2] = round(center_grid_size*1.45, 3)
            
########################           
########################
####### OPERATOR #######
########################
########################
class Start_game_of_life(bpy.types.Operator):
    """
    Starting a game of life using default cubes over a given period of cycles.
    Each iteration is saved as a render in the working directory.
    """
    bl_idname = "addonname.start_gameoflife"
    bl_label = "> Run GameOfLife <"
    # register with undo system
    # bl_options = {"REGISTER","UNDO"}
    
    #Properties are created in its own class! And are called directly at the start of execute
    
    def execute(self, context): 
        game_of_life_propertygroup = context.scene.game_of_life_propertygroup
        
        print()
        print(20*"_")
        #############################
        ### GET DEFAULT MATERIALS ###
        DEFAULT_COLOR = game_of_life_propertygroup.DEFAULT_COLOR
        HIGHLIGHT_COLOR = game_of_life_propertygroup.HIGHLIGHT_COLOR
        
        # check if its there
        all_mat_names = []
        for mat in bpy.data.materials:
            all_mat_names.append(mat.name)
        # if not create it 
        if not "default_material" in all_mat_names:
            CUBE_MAT = bpy.data.materials.new(name="default_material") #set new material to variable
            CUBE_MAT.diffuse_color = DEFAULT_COLOR #change color RGBA
        bpy.data.materials["default_material"].diffuse_color = DEFAULT_COLOR    # set color to new one
        CUBE_MAT = bpy.data.materials["default_material"]
        CUBE_MAT.specular_intensity = 0
        CUBE_MAT.roughness = 1
    
        # check if its there
        # if not create it 
        if not "highlight_material" in all_mat_names:
            HIGHLIGHT_MAT = bpy.data.materials.new(name="highlight_material") #set new material to variable
            HIGHLIGHT_MAT.diffuse_color = HIGHLIGHT_COLOR #change color RGBA
        bpy.data.materials["highlight_material"].diffuse_color = HIGHLIGHT_COLOR    # set color to new one
        HIGHLIGHT_MAT = bpy.data.materials["highlight_material"]
        HIGHLIGHT_MAT.specular_intensity = 0
        HIGHLIGHT_MAT.roughness = 1
        
        # Overwrite materials with custome ones if they exist
        if "custom_highlight_material" in all_mat_names:
            HIGHLIGHT_MAT = bpy.data.materials["custom_highlight_material"]
        if "custom_default_material" in all_mat_names:
            CUBE_MAT = bpy.data.materials["custom_default_material"]    
            
        ### SET DEFAULT RENDER PATH ###
        # will be overwritten if Export Path is set
        RENDER_PATH = os.path.join("//", "gameoflife_out")  # // = relative path of blend file 
        print(f"PATH IS: {RENDER_PATH}")
        print(20*"_")
        ######################
        ### GET PROPERTIES ###
        ######################
        
        life_cycles = game_of_life_propertygroup.life_cycles
        SIZE_X = game_of_life_propertygroup.SIZE_X
        SIZE_Y = game_of_life_propertygroup.SIZE_Y
        SPAWN_X = game_of_life_propertygroup.SPAWN_X
        SPAWN_Y = game_of_life_propertygroup.SPAWN_Y
        BIRTH_CHANCE = game_of_life_propertygroup.BIRTH_CHANCE
        SEED = game_of_life_propertygroup.SEED
        RESPAWN_ITER = game_of_life_propertygroup.RESPAWN_ITER
        SELECTED_MESH = game_of_life_propertygroup.MESH_DROPDOWN
        ANIMATE_CAM = game_of_life_propertygroup.ANIMATE_CAM
        COLOR_CHOICE = game_of_life_propertygroup.COLOR_CHOICE
        ORTHO_CAM = game_of_life_propertygroup.ORTHO_CAM
        MAX_RESPAWNS = game_of_life_propertygroup.MAX_RESPAWNS
        USE_START_IMG = game_of_life_propertygroup.USE_START_IMG
        
        EXPORT_PATH = game_of_life_propertygroup.EXPORT_PATH
        if not EXPORT_PATH == "" or EXPORT_PATH == "gameoflife_out":
            RENDER_PATH = EXPORT_PATH  # use newly set path
        
        ##########################
        ### START STATE CHECKS ###
        ##########################
        # is created when loading and changed when loading another, creation here should not be needed
        ## CHECK IF START STATE IMAGE CAN BE USED
        if "START_STATE_IMAGE" not in bpy.data.images.keys() and USE_START_IMG:
            print("No Start State Image loaded!... ignoring setting continue with normal settings")
            self.report({'WARNING'}, "No Start State Image loaded!, simulating wiht normal settings")
            USE_START_IMG = False
        # Check Size of start state image and set use_start_img to false if its to big
        if "START_STATE_IMAGE" in bpy.data.images.keys():
            START_IMG = bpy.data.images["START_STATE_IMAGE"]
            # x und y vertauschen weill das bild 90° im uhrzeigersinn gekippt ins array gelegt wird
            if START_IMG.size[0] > SIZE_Y or START_IMG.size[0] > SIZE_X:
                print("Start State Image to big!... ignoring setting continue with normal settings")
                USE_START_IMG = False
        else:
            USE_START_IMG = False
        
        print()
        print(f"PATH EXPORT: {EXPORT_PATH}")
        #RENDER_PATH = os.path.join("//", EXPORT_PATH)
        #################
        ### GAME INIT ###
        #################
        delete_all_cells()
        # delete default cube
        if "Cube" in bpy.data.objects.keys():
            bpy.data.objects.remove(bpy.data.objects["Cube"], do_unlink=True)

        # Define Cam to be ortho or perspective
        
        if ANIMATE_CAM and ORTHO_CAM:
            bpy.data.cameras["Camera"].type = "ORTHO"
        elif ANIMATE_CAM:
            bpy.data.cameras["Camera"].type = "PERSP"
            
            
        # params
        random.seed(SEED)  # set seed to reproduce
        print("START GAME OF LIFE") 
        time.sleep(0.5)
        SPAWN_AREA = (SPAWN_X, SPAWN_Y)  # SPAWN AREA HAS TO BE SMALLER THAN SIZEX AND SIZEY
        
        # create world with params
        world = Worldgrid(SIZE_X,SIZE_Y)
        bpy.context.scene.frame_set(0)  # if something else should be animated synchron
        
        # Create material list if set to random color (if COLOR_CHOICE is "RANDOM")
            # if random_color is false it just removes already existing "RandMat" Materials
        ALL_MATS = create_random_color_list(COLOR_CHOICE)
        
        # Initialise camera 
            #camera = bpy.context.scene.camera  # we only have 1 camera so first # bpy.data.cameras["Camera"]
            #print(bpy.context.scene.camera)  # Gets Camera Object (orange thing)
            #print(bpy.data.cameras["Camera"])  # Gets Camera (green thing)
        if ANIMATE_CAM:
            camera = bpy.context.scene.camera
            camera.location = (0,0,0) 
            camera.rotation_euler = (0,0,math.radians(0))
            camera.location[2] = 1
            if bpy.data.cameras["Camera"].type == "ORTHO":
                bpy.data.cameras["Camera"].ortho_scale = 3
        
        # Random init state
        previous_map_array = np.copy(world.get_world())  # dont want reference -> copy
        
        if USE_START_IMG:
            init_map_with_start_img(world, bpy.data.images["START_STATE_IMAGE"])
        else:
            init_map_witharea(world,area=SPAWN_AREA, birth_chance=BIRTH_CHANCE)
            #world.add_cell(250,250)  # a test to add cell manually

        # ADJUST CAMERA TO CURRENT CELLS
        if ANIMATE_CAM:
            r_cells = get_relevant_cells(world)
            m_dist = get_max_distance_from_center(r_cells, world)
            inner_grid_size = m_dist*2+1  # distance * 2 to get the grid around the center
            adjust_camera(camera, inner_grid_size)
        
        # first image
        update_visuals(world, CUBE_MAT, HIGHLIGHT_MAT, previous_map_array, SELECTED_MESH, ALL_MATS, COLOR_CHOICE)
        
        render_output(0, RENDER_PATH, self)
        
        # debug prints
        print("Start State:")

        #print(np.transpose(world.get_world()))  # flip image 180° along x is = this
        print(world.get_world())  # -90° rotation along z = image
        #######################
        #######################
        ### LIFE CYCLE LOOP ###
        #######################
        #######################
        respawns_count = 0
        print("Simulation Started")
        for i in range(life_cycles):
            # optional respawn
            if RESPAWN_ITER != 0:
                if (i % RESPAWN_ITER == 0 and i > 0) and (respawns_count < MAX_RESPAWNS or MAX_RESPAWNS == 0):
                    respawns_count += 1
                    divide_spawn_area = 1  # in case you want to reduce spawn window
                    init_map_witharea(world,area=(int(SPAWN_AREA[0]/divide_spawn_area),
                     int(SPAWN_AREA[1]/divide_spawn_area)), birth_chance=BIRTH_CHANCE)
                     
                     
            
            ## GET RELEVANT CELLS ##
            r_cells = get_relevant_cells(world)
            ## UPDATE CELLS ##
            previous_map_array = np.copy(world.get_world())  # dont want reference -> copy # map before updating
            update_cells(r_cells, world)
            ## UPDATE VISUALS ###
            update_visuals(world, CUBE_MAT, HIGHLIGHT_MAT, previous_map_array, SELECTED_MESH, ALL_MATS, COLOR_CHOICE)
            ## ADJUST CAMERA ##
            if ANIMATE_CAM:
                r_cells = get_relevant_cells(world)
                m_dist = get_max_distance_from_center(r_cells, world)
                inner_grid_size = m_dist*2+1  # distance * 2 to get the grid around the center
                adjust_camera(camera, inner_grid_size)
            ## RENDER IMAGE ##
            bpy.context.scene.frame_set(i)  # optional for other things that are animated in a "normal" way
            render_output(i+1, RENDER_PATH, self)
            print(i)
            
        
        self.report({'INFO'}, f"Simulation Ended: images in {RENDER_PATH}")
        print("FINISHED GAME OF LIFE")
        print(f"Results at location of blend file in: {RENDER_PATH}")
        return {'FINISHED'}


######################################
######################################
########### REGISTER STUFF ###########
######################################
######################################

#todo add game of life prop
classes = [GameOfLifeProperties, GoL_panel, GoL_exp_settings_panel, Start_game_of_life]

def register():
    #bpy.utils.register_class(Test_panel)
    for cls in classes:
        bpy.utils.register_class(cls)
        # add the properties to scene
        bpy.types.Scene.game_of_life_propertygroup = bpy.props.PointerProperty(type = GameOfLifeProperties)

def unregister():
    #bpy.utils.unregister_class(Test_panel)
    for cls in classes:
        bpy.utils.unregister_class(cls)
        # remove properties from scene
        del bpy.types.Scene.game_of_life
    

if __name__ == "__main__":
    print()
    print()
    register()  # register script and add to menu
    #unregister()  # unregister this script and remove from menu
    
    #bpy.ops.addonname.start_gameoflife()  # id name of created bpy.types.Operator
                    #### bpy.context.scene.frame_set(30) # example for setting frame 