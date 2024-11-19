import argparse

from run_gsas2_refinement_upload import run_gsas2_fit

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cif-filename", help="Name of CIF file to load (*.cif)", type=str)
    parser.add_argument("-f", "--gsas-filename", help="Name of gsas file to load (*.gsa) ", type=str)
    parser.add_argument(
        "-i", "--instrument-params-filename", help="Name of instrument parameters file to load (*.prm)", type=str
    )
    parser.add_argument("-o", "--output-stem-name", help="Output stem name", type=str, default="gsas2_refinement")
    parser.add_argument("-p", "--output-directory", help="Output directory name", type=str, default="/portal")
    parser.add_argument("-s", "--scatter-type", help='Scatter type: ["N", "X"]', choices=["N", "X"], type=str)
    parser.add_argument("-b", "--bank-id", help="Index of the bank to use", type=str)
    parser.add_argument("-l", "--xmin", help="Xmin", type=str)
    parser.add_argument("-r", "--xmax", help="Xmax", type=str)
    parser.add_argument("-n", "--num-cycles", help="Number of refinement cycles", type=int)
    parser.add_argument("-v", "--initial-values", help="Initial values for refinement", type=str)
    args = parser.parse_args()

    bank_id = int(args.bank_id)
    left_bound = float(args.xmin)
    right_bound = float(args.xmax)

    # Add key-word arguments
    kwargs = dict()
    if args.num_cycles:
        kwargs["num_cycles"] = args.num_cycles
    if args.initial_values:
        kwargs["init_vals"] = args.initial_values

    # Run refinement
    run_gsas2_fit(
        args.cif_filename,
        args.gsas_filename,
        args.instrument_params_filename,
        args.output_stem_name,
        args.scatter_type,
        bank_id,
        left_bound,
        right_bound,
        args.output_directory,
        **kwargs,
    )
