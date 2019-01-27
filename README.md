# Terraform

### What is this?
This is a project which hopes to estimate food risk using river location
    and rainfall data.
    
### How do I set this up?
You can set up the environment by cloning the repository and then running
    the `install_venv.sh` script to install a virtual environment with
    all the necessary python packages.
Once this is installed (this may take some time due to `basemap`), you
    can activate the virtual environment by running
```bash
source venv/bin/activate
```
Additionally to use the `terrain` functionality you will need
    to install pymesh. To do so,
[follow the instructions here](https://pymesh.readthedocs.io/en/latest/installation.html).
    

### Plotting
The `XPlot` class in `plotting/XPlot.py` is a wrapper class used to plot
    weather animations. Additionally two scripts are provided for
    automatically plotting the precipitation rate and total precipitation
    weather data in the `plotting` directory.

These scripts additionally take an optional `--save` flag which when
    added will save the animation in the `plotting/animations` directory.

##### Example
````bash
./plotting/animate_precipitation_rate.py --save
````

### Terrain Generation
The `TerrainGenerator` class in `terrain/TerrainGenerator.py` is a wrapper
    around the `STALGO` straight skeleton engine. This class will generate a
    terrain (.off file) from a river outline (.ipe file) and additionally will
    remove the vertices, faces, and edges that occurs inside the river.

Running the generator will produce two files, `terrain/data/terrain.off` and
    `terrain/data/terrain_subset.off`. These are the initially generated
    terrain and the terrain without the river respectively.

##### Example
```python
from terrain import TerrainGenerator
terr_gen = TerrainGenerator(stalgo_executable='<path-to-STALGO>',
                            ipe_file='data/terrain_data/boston_harbor_outline.ipe')
terr_gen.run()
```
    