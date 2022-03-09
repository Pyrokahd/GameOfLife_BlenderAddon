# GameOfLife_BlenderAddon
A Blender Addon to simulate Conway's game of life and directly output every iteration as png.

# Installation
1. Download this repo as zip
2. open blender got to Edit -> Preferences -> Add-ons and press Install
3. Navigate to the zip select it and install add on
4. Search for "Game of Life" and enable the add on

![This is an image](/doc/install.PNG)

# The Addon Panel
Press N in the 3D Viewport to open the sidebar. The addon is added to the sidebar and is called Game of Life.

![This is an image](/doc/install.PNG)

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
Camera
- ANIMATE_CAMERA: To set the camera above the grid and zoom out as much as needed automatically.
- Orthographic: To use orthographic camera view

If ANIMATE_CAMERA is deactivated you can animate your own camera with keyframes. In that case the total amount of frames in your animation has to be the same as the game iterations. This addon increases the current frame by 1 for every iteration.

# Preperation
## Create Light
You can swap your point light for a sunlight for a simple light source.

Alternatively you can use a hdri map to light your scene.


## Create cell_material
## Save File

# Start Simulation
## Open System_Console
## Abort while running

# Additional Stuff
## Custom Highlight Color
## Transparent Background
