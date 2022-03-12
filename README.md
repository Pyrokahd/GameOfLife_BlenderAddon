# GameOfLife_BlenderAddon
v1.5 <br/>
A Blender Addon to simulate Conway's game of life and directly output every iteration as a rendered png. 
While running there is no visual feedback within blender. Until its finished and a small notice pops up on the bottom.

 <img src="/doc/pattern1.gif" width="200" height="200"> ![This is an image](/doc/biggif.gif) <img src="/doc/glider_spawner.gif" width="200" height="200"> <img src="/doc/3dcamera.gif" width="200" height="200"> 

In the gifs above the cells created in this iteration are colored differently than cells form a previous iteration. (done by using the default 'highlighting' color choice)

# Installation
1. Download this repo as zip
2. open blender got to Edit -> Preferences -> Add-ons and press Install
3. Navigate to the zip select it and install add on
4. Search for "Game of Life" and enable the add on

![This is an image](/doc/install.PNG)

# The Addon Panel
Press N in the 3D Viewport to open the sidebar. The addon is added to the sidebar and is called Game of Life.

<img src="panel20.png" width="550" height="455">

## Parameter
- GAME ITERATIONS: How many cycles the simulation will run.
- SIZE_X / SIZE_Y: How big the grid is in which the simulation runs. 
- SPAWN_X / SPAWN Y: How big the Spawnarea is. In this area (centered in the mid) cells will spawn at initialization.
- BIRTH_CHANCE: The Chance per grid-cell to spawn a gameoflife-cell
- SEED: A seed for all random operations to reproduce the same results
- RESPAWN_ITERATIONS: After that amount of iterations, new cells will be initializied in the spawn area. 0 = deactivate.
- MAX_RESPAWNS: How often a respawn due to RESPAWN_ITERATIONS should happen. 0 = after every RESPAWN_ITERATIONS. Only relevant if RESPAWN_ITERATIONS is not 0.
- MESH: Which mesh should be rendered (CUBE, PLANE, SPHERE or TORUS) <br/>
**Use Plane for best speed! Its about 200 times faster to create than the other meshes!** <br/>
Color choice:
- 'default_material': Uses a material named 'default_material' for all cells
- highlighting: Uses the highlight color for every cell that is newly spawned this iteration and 'default_material' for all other.
- random_colors: A random color for every new cell.
- Default (COLOR): The color for all cells.
- Highlight (COLOR): The color for cells when highlighted via the highlighting setting.
Camera (Be sure to have quadratic resolution)
- ANIMATE_CAMERA: To set the camera above the grid and zoom out as much as needed automatically.
- Orthographic: To use orthographic camera view

If ANIMATE_CAMERA is deactivated you can animate your own camera with keyframes. In that case the total amount of frames in your animation has to be the same as the game iterations. This addon increases the current frame by 1 for every iteration.

## Experimental Settings
- Start State Image: Loads an image from your drive, to be used as a start state. Each black pixel will be one cell when starting the simulation. Deactivates the other initialization. (If an image with the same name is already in the blend file, it is used instead)
- USE THIS IMAGE AS START STATE: To activate the image as start state. 
- Preview: A preview of your loaded image, might need rescaling to refresh if you load another.

When using this setting, the size of the loaded image has to be within the size of the set game map (SIZE_X and SIZE_Y). Else it wont be loaded.

### Custom Materials
You can use your own materials by creating one named "custom_default_material" for the default material and one "custom_highlight_material" for the highlight material, within your blend file.

<img src="/doc/example_custom_colors.png" width="180" height="180">

# Preparations
Saving the blend file is the most important one! Else no output is saved.

## Set quadratic resolution
Output properties -> Resolution X and Y -> set to the same value (i.e. 1080)

![This is an image](/doc/resolution.png)

## Create Light

### HDRI
You can use a hdri map to light your scene, which is probably the best way and fastest way (in rendering) to add good light. <br/>
World properties -> Surface -> Color -> Environment Texture -> Open HDRI <br/>
Good HDRIs can be found at https://polyhaven.com/ for example.

<img src="/doc/hdri1.png" width="720" height="420">

To then make the background transparent (if you dont want to see the HDRI Image): <br/>
Render properties -> Film -> transparent

<img src="/doc/hdri2.png" width="220" height="380">

### SUN
You can swap your point light for a sunlight for a simple light source. <br/>
Select light -> Object data properties -> Light -> Sun <br/>
But you probaly need to play with the strength.

<img src="/doc/sunlight.png" width="630" height="500">

### Sky Texture
Another option is to use a sky texture in the world shader. <br/>
Shading workspace -> select World instead of Object (node window top left) -> add 'Sky Texture' Node -> Change to 'Preetham' or 'Hosek/Wilkie' -> connect to background color and world output 

<img src="/doc/skytexture.png">

## Save File
File -> Save as -> Select directory <br/>
In this directory the output (all the frames) will be rendered in a folder called "gameoflife_out"


# Start Simulation
## Open System_Console
Before Starting open the System Console. <br/>
Window -> Toggle System_Console 

![This is an image](/doc/systemconsole.png)

There you can see if the addon is still running after started. You can also see how long it takes per iteration and which is the current one.

## Abort while running
The System Console can also be used to terminate the process by clicking in it and pressing CTRL+C (Windows) or CMD+C (MAC).
This is usefull if you want to stop it early or need access to blender again to change settings. (While running, Blender is unresponsive)

Now you can run as many simulations as you like. The addon will clean old data up before starting a new run. 
However rename your old "gameoflife_out" folder to keep the previous run.

## Run the Simulation
You can now press "Run GameOfLife" in the Addon panel to start the simulation.
Output is generated by default in the folder called "gameoflife_out" and frames have the naming scheme of "0-iteration_0.png", "1-iteration_1.png"...




# Additional Stuff
## Background Image
If you want to use a background image together with the transparent Film setting you can use this compositing layout.

![This is an image](/doc/compositing.png)

## Render Video from Images
Open a new Blender project.
Go to the Video Editing workspace. <br/>
(top bar '+') -> new-> video editing -> video editing

![This is an image](/doc/videoediting1.png)

Import the images as image strip. <br/>
Add -> Image/Sequence -> navigate to your folder -> press 'A' to select all -> import <br/>
Make sure they are ordered correctly from top to bottom.

![This is an image](/doc/openimagestrip.png)

### Settings
1. Set Resolution to the rendered Resolution.
2. Set Frame Rate to a value you like (i.e. 15)
3. Set Frame Range to fit your images
4. Set Output path
5. Change File Format to FFmpeg Video and Container to MPEG-4
6. Render the output (CTRL+F12) or Render -> Render Animation

![This is an image](/doc/videosettings1.png) ![This is an image](/doc/videosettings2.png)

## Create GIF with Python and Pillow
Also if you know how to use python scripts here is some code to generate a gif from the images: <br/>
Requires Pillow (PIL): https://pillow.readthedocs.io/en/stable/installation.html 
```
from PIL import Image, ImageDraw
import os
import time

start = time.time()

# PARAMETER
path = "gamoflife_out" # PATH TO IMAGE FOLDER
fps = 30 # SET FPS
width = 0  # SET TO != 0 TO RESIZE IMAGES
height = 0 # SET TO != 0 TO RESIZE IMAGES

time_per_image = (1000/fps)  # in milliseconds

# save all file names in a dict with the number behind '_' as key
# expects file names with format [name]_[number].[filetype], i.e. image_0.png, image_1.png ...
all_names = {}
for name in os.listdir(path):
    number = name.split("_")[1].split(".")[0]
    all_names[int(number)] = name
# sort the dict
sorted_all_names = dict( sorted(all_names.items()) )

# use sorted list of image names to load images
all_images = []
for k, v in sorted_all_names.items():
    img = Image.open(os.path.join(path, v))
    if width != 0 and height != 0:
        img = img.resize((width, height))
    all_images.append(img)

# Save gif in same directory as this script
savepath = ""
# save gif using first image and appending all other
all_images[0].save(os.path.join(savepath, "myGif.gif"), save_all=True,
                                    append_images=all_images[1:], optimize=False, duration=time_per_image, loop=0)
end = time.time()
print(f"gif created. Duration {end-start}s")
```
