import argparse

from run_gsas2_sample_instrument_fit import run_gsas2_fit

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--project-filename", help="Name of the GSASII project file to load (*.gpx)", type=str)
    parser.add_argument("-t", "--histogram-type", help="type of powder diffraction histogram (TOF or CW)", type=str)

    parser.add_argument("-s", "--sample-refinements", help="sample parameters GSASII will refine", type=str)
    parser.add_argument("-i", "--instrument-refinements", help="instrument parameters GSASII will refine", type=str)
    parser.add_argument("-b", "--instrument-values", help="instrument parameter values to set", nargs="+", type=float)
    parser.add_argument("-v", "--sample-values", help="sample parameter values to set", nargs="+", type=float)
    parser.add_argument("-o", "--output-stem-name", help="Output stem name", type=str, default="gsas2_refinement")
    parser.add_argument("-p", "--output-directory", help="Output directory name", type=str, default="/portal")
    parser.add_argument("-n", "--num-cycles", help="Number of refinement cycles", type=int)
    # parser.add_argument('-v', '--initial-values', help='Initial values for refinement', type=str)
    args = parser.parse_args()

    # Add key-word arguments
    kwargs = {}
    if args.num_cycles:
        kwargs["num_cycles"] = args.num_cycles
    # if args.initial_values:
    #    kwargs["init_vals"] = args.initial_values

    # Run refinement
    run_gsas2_fit(
        args.project_filename,
        args.histogram_type,
        args.sample_refinements,
        args.instrument_refinements,
        args.instrument_values,
        args.sample_values,
        args.output_stem_name,
        args.output_directory,
        **kwargs,
    )
