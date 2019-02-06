""" Script for simplifying a mesh using blender. """
import argparse
import bpy
import math
import os
import sys


def run_blender(input_file, output_file):
    """
        List of tasks to run in blender.
        Imports the mesh, merges coplanar polygons, and exports the mesh.
    """
    # Delete the initial cube.
    bpy.ops.object.delete()

    # Import the mesh.
    bpy.ops.import_scene.obj(filepath=input_file)

    # Select the mesh.
    bpy.ops.object.select_all(action='DESELECT')
    mesh_name = os.path.basename(input_file)[:-4]
    bpy.context.scene.objects.active = bpy.data.objects[mesh_name]
    bpy.ops.object.mode_set(mode='EDIT')

    # Merge coplanar polygons.
    bpy.ops.mesh.dissolve_limited(angle_limit=math.radians(1.0))

    # Export file.
    bpy.ops.export_scene.obj(filepath=output_file)


if __name__ == '__main__':
    # Need to collect the arguments because of blender intricacies.
    argv = sys.argv

    if "--" not in argv:
        argv = []  # as if no args are passed
    else:
        argv = argv[argv.index("--") + 1:]

    # Parser the arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input .obj file.')
    parser.add_argument('--output', default=None, help='Output .obj file. Default: Overwrites input.')
    args = parser.parse_args(argv)

    # If output not given, make it the same as the input file.
    if args.output is None:
        args.output = args.input

    # Check that the input file exists.
    if not os.path.isfile(args.input):
        raise FileNotFoundError(args.input)

    # Check that the output directory exists.
    output_directory = os.path.dirname(args.output)
    if not os.path.isdir(output_directory):
        raise NotADirectoryError(output_directory)

    # Run the blender commands.
    run_blender(args.input, args.output)
