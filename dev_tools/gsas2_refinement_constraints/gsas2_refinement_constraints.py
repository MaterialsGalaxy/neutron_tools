import argparse

from run_gsas2_refinement_constraints import run_gsas2_fit

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--project-filename", help="Name of the GSASII project file to load (*.gpx)", type=str)
    parser.add_argument("-v", "--equation-variables", help="equation constraint variables list", type=str)
    parser.add_argument("-c", "--equation-coefficients", help="equation constraint coefficient list", type=str)
    parser.add_argument("-t", "--equation-totals", help="equation constriant total", type=float)
    parser.add_argument("-i", "--equivalence-variables", help="equivalence constraint variable list", type=str)
    parser.add_argument("-e", "--equivalence-coefficients", help="optional equivalence constraints coefficient list", type=str)
    parser.add_argument("-o", "--output-stem-name", help="Output stem name", type=str, default="gsas2_refinement")
    parser.add_argument("-p", "--output-directory", help="Output directory name", type=str, default="/portal")
    parser.add_argument("-n", "--num-cycles", help="Number of refinement cycles", type=int, default=5)
    args = parser.parse_args()

    # format string inputs into lists
    if args.equation_variables is not None:
        args.equation_variables = [s.strip() for s in args.equation_variables.split(",")]

    if args.equation_coefficients is not None:
        args.equation_coefficients = [float(s) for s in args.equation_coefficients.split(",")]
    else:
        args.equation_coefficients = [1]*len(args.equation_variables)

    if args.equivalence_variables is not None:
        args.equivalence_variables = [s.strip() for s in args.equivalence_variables.split(",")]

    if args.equivalence_coefficients is not None:
        args.equivalence_coefficients = [float(s) for s in args.equivalence_coefficients.split(",")]
    else:
        args.equivalence_coefficients = [1.0] * len(args.equivalence_variables)

    # Add key-word arguments
    kwargs = dict()
    if args.num_cycles:
        kwargs["num_cycles"] = args.num_cycles

    # Run refinement
    run_gsas2_fit(
        args.project_filename,
        args.equation_variables,
        args.equation_coefficients,
        args.equation_totals,
        args.equivalence_variables,
        args.equivalence_coefficients,
        args.output_stem_name,
        args.output_directory,
        **kwargs,
    )
