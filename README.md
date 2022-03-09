# GameOfLife_BlenderAddon
A Blender Addon to simulate Conway's game of life and directly output every iteration as a rendered png. 
While running there is no visual feedback within blender. Until its finished and a small notice pops up on the bottom.

<img src="/doc/simplegif.gif" width="200" height="200">  ![This is an image](/doc/biggif.gif)

Green cells in the gifs above are the ones created in this iteration, and the other are older ones. (done by using the 'highlighting' color choice)

# Installation
1. Download this repo as zip
2. open blender got to Edit -> Preferences -> Add-ons and press Install
3. Navigate to the zip select it and install add on
4. Search for "Game of Life" and enable the add on

![This is an image](/doc/install.PNG)

# The Addon Panel
Press N in the 3D Viewport to open the sidebar. The addon is added to the sidebar and is called Game of Life.

<img src="/doc/panel.png" width="700" height="420">

## Parameter
- GAME ITERATIONS: How many cycles the simulation will run.
- SIZE_X / SIZE_Y: How big the grid is in which the simulation runs. 
- SPAWN_X / SPAWN Y: How big the Spawnarea is. In this area (centered in the mid) cells will spawn at initialization.
- BIRTH_CHANCE: The Chance per grid-cell to spawn a gameoflife-cell
- SEED: A seed for all random operations to reproduce the same results
- RESPAWN_ITERATIONS: After that amount of iterations, new cells will be initializied in the spawn area. 0 = deactivate.
- MESH: Which mesh should be rendered (CUBE, PLANE, SPHERE or TORUS)
Color choice
- 'default_material': Uses a material named 'default_material' for all cells
- highlighting: Uses a green highlight color for every cell that is newly spawned this iteration and 'default_material' for all other.
- random_colors: A random color for every new cell.
Camera (Be sure to have quadratic resolution)
- ANIMATE_CAMERA: To set the camera above the grid and zoom out as much as needed automatically.
- Orthographic: To use orthographic camera view

If ANIMATE_CAMERA is deactivated you can animate your own camera with keyframes. In that case the total amount of frames in your animation has to be the same as the game iterations. This addon increases the current frame by 1 for every iteration.

# Preparations
Saving the blend file is the most important one! Else no output is saved.

## Set quadratic resolution
Output properties -> Resolution X and Y -> set to the same value (i.e. 1080)

![This is an image](/doc/resolution.png)

## Create Light
SUN: <br/>
You can swap your point light for a sunlight for a simple light source.
Select light -> Object data properties -> Light -> Sun

<img src="/doc/sunlight.png" width="650" height="520">

HDRI: <br/>
Alternatively you can use a hdri map to light your scene.
World properties -> Surface -> Color -> Environment Texture -> Open HDRI

<img src="/doc/hdri1.png" width="720" height="420">

To then make the background transparent (if you dont want to see the HDRI Image):
Render properties -> Film -> transparent

<img src="/doc/hdri2.png" width="220" height="380">

## Create default_material
To quickly create a material for the cells select the cube:
Material properties -> rename to "default_material" -> Fake User (to save it even if no object has this material) -> Change Base Color as you like

<img src="/doc/create_material.png" width="700" height="610">

You can of course use Nodes to create a fancy material if you like.

## Save File
File -> Save as -> Select directory
In this directory the output (all the frames) will be rendered in a folder called "gameoflife_out"


# Start Simulation
## Open System_Console
Before Starting open the System Console.
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
Output is generated in the folder called "gameoflife_out" and frames have the naming scheme of "0-iteration_0.png", "1-iteration_1.png"...




# Additional Stuff
## Custom Highlight Color
You can create your own highlight color (which is green by default) by simply creating a new material named "spawn_color".

## Background Image
If you want to use a background image together with the transparent Film setting you can use this compositing layout.

![This is an image](/doc/compositing.png)

## Render Video from Images
Open a new Blender project.
Go to the Video Editing workspace.
(top bar '+') -> new-> video editing -> video editing

![This is an image](/doc/videoediting1.png)

Import the images as image strip.
Add -> Image/Sequence -> navigate to your folder -> press 'A' to select all -> import
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
