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
