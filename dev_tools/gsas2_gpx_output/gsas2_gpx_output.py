import argparse

from run_gsas2_gpx_output import run_gsas2_fit

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--project-filename", help="Name of the GSASII project file to load (*.gpx)", type=str)
    parser.add_argument("-o", "--output-stem-name", help="Output stem name", type=str, default="gsas2_refinement")
    args = parser.parse_args()

    # Run refinement
    run_gsas2_fit(
        args.project_filename,
        args.output_stem_name,
    )
