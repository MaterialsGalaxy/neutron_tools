import argparse

from run_gsas2_gpx_refinement import run_gsas2_fit

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--project-filename", help="Name of the GSASII project file to load (*.gpx)", type=str)
    parser.add_argument("-d", "--delta-filename", help="Name of the delta file to load", type=str)
    parser.add_argument("-o", "--output-stem-name", help="Output stem name", type=str, default="gsas2_refinement")
    parser.add_argument("-p", "--output-directory", help="Output directory name", type=str, default="/portal")
    parser.add_argument("-n", "--num-cycles", help="Number of refinement cycles", type=int, default=5)
    args = parser.parse_args()

    # Add key-word arguments
    kwargs = dict()
    if args.num_cycles:
        kwargs["num_cycles"] = args.num_cycles

    # Run refinement
    run_gsas2_fit(
        args.project_filename,
        args.delta_filename,
        args.output_stem_name,
        args.output_directory,
        **kwargs,
    )
