#!/usr/bin/env python3

from argparse import ArgumentParser
import sys, os
import json
import time
import subprocess
import multiprocessing
from datetime import datetime


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def fatal(*args, **kwargs):
    eprint(*args, **kwargs)
    exit(1)


def load_timings(timings_file, create=False):
    if not os.path.exists(timings_file):
        if create:
            return {}
        else:
            fatal("No database found:", timings_file, "Please collect a new one with --ref-run")
    with open(timings_file, "r") as file:
        return json.load(file)


def save_timings(timings_file, timings):
    with open(timings_file, "w") as file:
        json.dump(timings, file, indent=2)


def run_mpi(bin, parallelism, oversubscribe_option):
    if oversubscribe_option is None:
        subprocess.run(["mpirun", "-np", str(parallelism), bin])
    else:
        subprocess.run(["mpirun", oversubscribe_option, "-np", str(parallelism), bin])


def run_omp(bin, parallelism):
    new_env = os.environ.copy()
    new_env["OMP_NUM_THREADS"] = str(parallelism)
    subprocess.run([bin], env=new_env)


def check_binaries(type, bin):
    eprint("=== Checking binaries...")
    if not os.path.exists(bin):
        fatal("Binary not found:", bin)
    if type == "mpi":
        subprocess.run(["mpirun", "--version"])
    eprint("=== All binaries available!")


def prepare_run(args):
    if args.type == "mpi":
        mpi_oversubscribe_arg = args.mpi_oversubscribe_arg
        if args.mpi_no_oversubscribe:
            mpi_oversubscribe_arg = None
        return lambda p: lambda: run_mpi(args.bin, p, mpi_oversubscribe_arg)
    elif args.type == "omp":
        return lambda p: lambda: run_omp(args.bin, p)
    else:
        fatal("Unknown type:", args.type)


def measure_time(runnable):
    start = time.time()
    runnable()
    stop = time.time()
    return round((stop - start) * 1000)


def get_default_parallelism():
    noc = multiprocessing.cpu_count()
    return [str(x + 1) for x in range(noc)] + [str(noc + 2)] + [str(noc * 2)]


def parse_parallelism(arg):
    if arg is None:
        return get_default_parallelism()
    return [str(int(x)) for x in arg.split(",")]


def format_time(time_ms):
    time_s = round(time_ms / 1000)
    time_m = round(time_s / 60)
    time_s %= 60
    time_ms %= 1000
    return "{}m:{}s:{}ms".format(time_m, time_s, time_ms)


def print_timings_table(results):
    eprint("{:<12} {:<15}".format("Parallelism", "Time"))
    for par, time_ms in results.items():
        eprint("{:<12} {:<15}".format(par, format_time(time_ms)))


def print_timings_cmp_table(results, ref_results, accuracy):
    eprint("Accuracy: +-" + format_time(accuracy))
    eprint("{:<12} {:<7} {:<15} {:<15}".format("Parallelism", "Valid", "Result time", "Reference time"))
    for par, res_ms in results.items():
        ref_ms = ref_results[par]
        valid = "equal"
        if abs(ref_ms - res_ms) > accuracy:
            if ref_ms > res_ms:
                valid = "better"
            else:
                valid = "worse"
        eprint("{:<12} {:<7} {:<15} {:<15}".format(par, valid, format_time(res_ms), format_time(ref_ms)))


def ref_run(args):
    database = load_timings(args.database, create=True)
    parallelism = parse_parallelism(args.parallelism)
    runnable = prepare_run(args)
    lab = args.lab

    check_binaries(args.type, args.bin)

    eprint("=== Reference run lab", lab, "for parallelism:", ", ".join([str(x) for x in parallelism]))
    eprint("=== Binary:", args.bin, "Type:", args.type)

    results = {}
    cur_results = {}
    if lab in database:
        results = database[lab]
    for par in parallelism:
        eprint("=== Run with parallelism:", par)
        time_ms = measure_time(runnable(par))
        eprint("=== Run with parallelism", par, "done in", format_time(time_ms))
        results[par] = time_ms
        cur_results[par] = time_ms

    eprint("Reference run completed. Timings:")
    print_timings_table(cur_results)

    database[lab] = results
    save_timings(args.database, database)


def get_ref_results(database, lab, parallelism):
    if lab not in database:
        fatal("No ref results for lab:", lab)
    ref_results = database[lab]
    for par in parallelism:
        if par not in ref_results:
            fatal("No ref results for lab:", lab, "with parallelism:", par)
    return ref_results


def compare_results(ref_ms, res_ms, accuracy):
    diff = abs(ref_ms - res_ms)
    if diff < accuracy:
        eprint("=== Valid accuracy.")
    else:
        desc = "BETTER"
        if ref_ms < res_ms:
            desc = "WORSE"
        eprint("=== Invalid accuracy diff ({}): {}ms < {}ms Reference time is: {}".format(desc, diff, accuracy, format_time(ref_ms)))


def cmp_run(args):
    database = {}
    if not args.no_ref:
        database = load_timings(args.database)
    parallelism = parse_parallelism(args.parallelism)
    runnable = prepare_run(args)
    lab = args.lab

    ref_results = None
    if not args.no_ref:
        ref_results = get_ref_results(database, lab, parallelism)

    check_binaries(args.type, args.bin)

    if args.no_ref:
        eprint("=== Non-compare run lab", lab, "for parallelism:", ", ".join([str(x) for x in parallelism]))
    else:
        eprint("=== Compare run lab", lab, "for parallelism:", ", ".join([str(x) for x in parallelism]))
    eprint("=== Binary:", args.bin, "Type:", args.type)

    results = {}
    for par in parallelism:
        eprint("=== Run with parallelism:", par)
        time_ms = measure_time(runnable(par))
        eprint("=== Run with parallelism", par, "done in", format_time(time_ms))
        results[par] = time_ms
        if not args.no_ref:
            compare_results(ref_results[par], time_ms, args.accuracy)

    if args.no_ref:
        eprint("Non-compare run completed. Timings:")
        print_timings_table(results)
    else:
        eprint("Compare run completed. Timings & Stats:")
        print_timings_cmp_table(results, ref_results, args.accuracy)

def run(args):
    if args.ref_run:
        ref_run(args)
    else:
        cmp_run(args)


def main(args):
    eprint("Total time:", format_time(measure_time(lambda: run(args))))


def parse_args():
    parser = ArgumentParser("Test labs performance")
    parser.add_argument(
        "--ref-run",
        action="store_true",
        default=False,
        help="Collect reference timings for current hardware"
    )
    parser.add_argument(
        "--no-ref",
        default=False,
        action="store_true",
        help="Just run selected binary. No need to compare with reference."
    )
    parser.add_argument(
        "--database",
        type=str,
        default="timings.json",
        help="Reference timings database file"
    )
    parser.add_argument(
        "--lab",
        type=str,
        required=True,
        help="Select lab number (can be any string)"
    )
    parser.add_argument(
        "--bin",
        type=str,
        required=True,
        help="Lab exec to test"
    )
    parser.add_argument(
        "--accuracy",
        type=int,
        default=1000,
        help="Set accuracy (ms) to compare with reference timings (default: 1000ms)"
    )
    parser.add_argument(
        "--parallelism",
        type=str,
        default=None,
        help="""Select tesing parallelism. Format: '<P1>,<P2>,...,<PN>'
        By default it tests from 1 to number of cores, cores + 2 and cores * 2.
        Example for 8-core hw: 1,2,3,4,5,6,7,8,10,16"""
    )
    parser.add_argument(
        "--type",
        type=str,
        default="mpi",
        choices=["mpi", "omp"],
        help="Type of run"
    )
    parser.add_argument(
        "--mpi-oversubscribe-arg",
        type=str,
        default="--oversubscribe",
        help="""Argument to be passed to MPI to prevent termination on startup
        with parallelism exceeding machine capabilities
        (argument depends on the implementation of MPI). Has no effect for OMP runs."""
    )
    parser.add_argument(
        "--mpi-no-oversubscribe",
        default=False,
        action="store_true",
        help="Do not substiture MPI oversubscribe option (see --mpi_oversubscribe_arg)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    exit(main(parse_args()))

