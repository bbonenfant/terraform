# Terraform

### What is this?
This is a project which hopes to estimate food risk using river location
    and rainfall data.
    
### How do I set this up?
You can set up the environment by cloning the repository and then running
    the `install_venv.sh` script to install a virtual environment with
    all the necessary python packages.
Once this is installed ~~(this may take some time due to `basemap`)~~, you
    can activate the virtual environment by running
```bash
source venv/bin/activate
```
Additionally to use the `terrain` functionality you will need
    to install pymesh. To do so,
[follow the instructions here](https://pymesh.readthedocs.io/en/latest/installation.html).

**NOTE:** You cannot pip install pymesh.
    

### Plotting
The `XPlot` class in `plotting/XPlot.py` is a wrapper class used to plot
    weather animations. Additionally two scripts are provided for
    automatically plotting the precipitation rate and total precipitation
    weather data in the `plotting` directory.

These scripts additionally take an optional `--save` flag which when
    added will save the animation in the `plotting/animations` directory.

**NOTE:** Now the `basemap` library is not auto installed. To use the plotting
portion of this you will need to pip install basemap from
`git+https://github.com/matplotlib/basemap.git`

##### Example
````bash
./plotting/animate_precipitation_rate.py --save
````

### Terrain Generation
**NOTE:** You need to have blender for the polygon simplification process.
You can download it here: https://www.blender.org/download/

The `TerrainGenerator` class in `terrain/TerrainGenerator.py` is a wrapper
    around the `STALGO` straight skeleton engine. This class will generate a
    terrain (.off file) from a either river outline (.ipe file) or image of
    a river trace, and additionally will remove the vertices, faces, and edges
    that occurs inside the river. Then it will simplify and merge coplanar
    polygons using blender and construct a `terrain` object by parsing the
    output .obj file.

Running the generator will produce a few files:
 - `terrain/data/contour.png`                   - Image showing OpenCV contours.
                                                    (from trace file)
 - `terrain/data/river.ipe`                     - Generated .ipe file to be used as
                                                    input to STALGO.
                                                    (from trace file)
 - `terrain/data/river_out.ipe`                 - The .ipe file output by STALGO.
 - `terrain/data/terrain.off`                   - the STALGO output file.
 - `terrain/data/river_subset.obj`              - the pymesh output file.
 - `terrain/data/terrain_subset.obj`            - the pymesh output file.
 - `terrain/data/simplified_river_subset.obj`   - the blender output file.
 - `terrain/data/simplified_river_subset.mtl`   - extraneous blender output file.
 - `terrain/data/simplified_terrain_subset.obj` - the blender output file.
 - `terrain/data/simplified_terrain_subset.mtl` - extraneous blender output file.

You might need to provide the `stalgo_executable` and/or `blender_executable` since
    these will most likely not be the same location for you as they are for me.

##### Examples
From image:
```python
from terrain import TerrainGenerator
terr_gen = TerrainGenerator(river_trace_image='data/terrain_data/detroit_rivers.png')
terr_gen.run()
print(terr_gen.terrain)
print(terr_gen.terrain.river)

'terrain_subset :: NumberOfVertices = 4812, NumberOfFaces = 1005'
'river_subset :: NumberOfVertices = 4469, NumberOfFaces = 895'
```

From .ipe file:
```python
from terrain import TerrainGenerator
terr_gen = TerrainGenerator(ipe_file='data/terrain_data/boston_harbor_outline.ipe')
terr_gen.run()
print(terr_gen.terrain)

'terrain_subset :: NumberOfVertices = 2943, NumberOfFaces = 612'
```

### RainFlow
The `RainFlow` class in `terrain/RainFlow.py` is a class used to handle simulation
of rainfall flowing down generated terrain into rivers from `TerrainGenerator`. This is handled by time stepped process
where a 2D square grid of cell size `mesh_size` is overlaid on top of the terrain to characterize the water level and slope
at each point in the terrain. 
    

##### Example
Below is a visualization of the rain flow process for the terrain surrounding Houston, TX. 
Numbers denote water levels in a cell, and '.' denotes a water level of zero.

The initial image assumes a constant water level in each cell before any rainflow.

```python
from terrain import TerrainGenerator
from terrain.RainFlow import RainFlow
terr_gen = TerrainGenerator(river_trace_image='data/terrain_data/houston_rivers.png')
terr_gen.run()

terrain = Object(obj_file='data/simplified_terrain_subset.obj')
rain_flow = RainFlow(terrain=terrain,mesh_size=0.02,rainfall_rate=1)
print(rain_flow.__repr__())

                                                          
                           111                            
                        111111                            
                  11111111111                             
                 111111111111              11             
              111111111111111             111             
            11111111111111111            111              
           111111111111111111           1111              
         111111111111111111111111      11111              
         1111111111111111111111111    11111               
       111111111111111111111111111   111111               
      1111111111111111111 1 111111111111111111            
     111111 111111111111111111111111111111111111          
   1111111111111111111111111111111111111111111111         
 1111111111111111111111111111111111  111111111111111      
 111111 1111111111111111111111111111111111111 11111111    
 11111111111 1111111111111111111111111111111111111111111  
 1111111111111 11111111111111111111111111111111111111111  
 11111111111111111111111 11111111111111111111111 111111111
  1111111111111111 1 111111111111111111111111111 111111111
   11111111111111111111111111111111 1111111111111111111111
     11111111 1111111111111111111111111111111111111111 111
      11111111111111111 1111   111111111111111111111111111
       111111111111111111111111111111111111111111111111111
         111111111111111111111111111111111111111111111111 
          1   1  1111111 11111111111111111111111111111111 
                   111111 111111111111111111 111111111    
                    1111111111111111111111111111111111    
                      111111111 1111111111111111111111    
                       1111111111111111111111111111       
                         11111111 1111111111111111        
                            111111111111111111111         
                             11111111111111111111         
                              111111111111111111          
                                  111        11           
                                                          
```
The final image represents a steady-state solution of water levels after rain flow simulation
which also gives an approximate location for the rivers in the network.

```python
rain_flow.simulate(25)
print(rain_flow.__repr__())
                                                          
                           ...                            
                        ......                            
                  ...........                             
                 ............              ..             
              ...............             .4.             
            .........113417....            ...              
           ........5.925.19...           ....              
         .....6.3453.............      .....              
         ....24434................    .....               
       .....1232.........2.37.....   ......               
      ....28.12.........4 2 41................            
     ...... 3......3.8..3332298.................          
   ......5...5.124.219.........4...33............         
 .....2.6.74..3224..2..........4.3.  3...1817...1.....      
 .....1 6..3.....................3.722.1.1720.. 5.......    
 ...18.17...1 21.............4..........12.....63........  
 ....151....1.3 23.6.224...9.5.4..9....6.2.....3116......  
 .......56....133.5.1152 49...4..8..5.5........3 261.6....
  .......54....... . 1112.3.......112..........3 2.2622...
   .....645...129.1..3.4..........4 ..22.4.....2....22....
     ....4..10 1211.....4.1.............21.45.....44...28 3..
      .......35.......2 ....   ...77233...523...22........
       ................66...........132....4.1...14........
         ..............45.........222...22..23.112........ 
          .   .  ....... 2.........3.21.12.2.214......... 
                   ....72 3445....35221....4 443......    
                    ....27434425....1..33.....2.......    
                      ........1 9..1..1......11513......    
                       .........310...29...3........       
                         ......2. .7.9...1109......        
                            .....9..7............         
                             ....................         
                              ..................          
                                  ...        ..           
                                                          
```
