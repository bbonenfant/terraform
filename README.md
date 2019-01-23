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
    