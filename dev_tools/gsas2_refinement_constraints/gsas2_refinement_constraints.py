import argparse

from run_gsas2_refinement_constraints import run_gsas2_fit

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--project-filename", help="Name of the GSASII project file to load (*.gpx)", type=str)
    parser.add_argument("-v", "--equation-variables", help="equation constraint variables list", type=str, nargs="+")
    parser.add_argument("-c", "--equation-coefficients", help="equation constraint coefficient list", type=str, nargs="+")
    parser.add_argument("-t", "--equation-totals", help="equation constriant total", type=float, nargs="+")
    parser.add_argument("-i", "--equivalence-variables", help="equivalence constraint variable list", type=str, nargs="+")
    parser.add_argument("-e", "--equivalence-coefficients", help="optional equivalence constraints coefficient list", type=str, nargs="+")
    parser.add_argument("-o", "--output-stem-name", help="Output stem name", type=str, default="gsas2_refinement")
    parser.add_argument("-p", "--output-directory", help="Output directory name", type=str, default="/portal")
    parser.add_argument("-n", "--num-cycles", help="Number of refinement cycles", type=int, default=5)
    args = parser.parse_args()

    # format string inputs into lists
    if args.equation_variables is not None:
        for i in range(len(args.equation_variables)):
            args.equation_variables[i] = [s.strip() for s in args.equation_variables[i].split(",")]

    if args.equation_coefficients is not None:
        for i in range(len(args.equation_coefficients)):
            args.equation_coefficients[i] = [float(s) for s in args.equation_coefficients[i].split(",")]
    else:
        for i in range(len(args.equation_variables)):
            args.equation_coefficients[i] = [1]*len(args.equation_variables[i])

    if args.equivalence_variables is not None:
        for i in range(len(args.equivalence_variables)):
            args.equivalence_variables[i] = [s.strip() for s in args.equivalence_variables[i].split(",")]

    if args.equivalence_coefficients is not None:
        for i in range(len(args.equivalence_coefficients)):
            args.equivalence_coefficients[i] = [float(s) for s in args.equivalence_coefficients[i].split(",")]
    else:
        for i in range(len(args.equivalence_coefficients)):
            args.equivalence_coefficients[i] = [1.0] * len(args.equivalence_variables[i])

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
