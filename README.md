# Parallels labs performance test

A simple script that allows you to test the performance of student labs and compare them with reference values for a given hardware.

Supports running using MPI and OpenMP.

# Usage:

## Collecting reference:

In order to be able to compare the "correct" lab in terms of execution time with the one provided by the student, it is required to run the "correct" variant with execution time measurement on the current hardware.
To do this, use the `--ref-run` option, which will collect the necessary statistics in the `timings.json` file for later comparison.
To be able to compare data with each other, you need to run `--ref-run` with the appropriate arguments for the name of the lab `--lab <name>` and parallelism `--parallelism <P1>,<P2>,...,<PN >`.

## Comparing results:

After collecting the reference results, you can do a normal run without the `--ref-run` option, which will take the reference data and compare it with the current run.
The comparison run must also match the reference run in terms of the lab name and concurrency arguments.

## Parallelism:

Tests with varying amounts of parallelism are specified in the following format:
```
--parallelism <P1>,<P2>,...,<PN>
```

By default, if no argument is given, the following values are used:

```
1, 2, ..., number_of_cores, number_of_cores + 2, number_of_cores * 2
```

## Run type:

To specify the type of parallelization, you can specify the following option:

```
--type <mpi/omp>
```

## Testing binary:

The executable file that will be tested is specified by the following option:

```
--bin <path to binary>
```

## Compare accurancy:

To set the accuracy of comparison of results, use the option:

```
--accurancy <time in ms>
```

## Just run (without compare to reference):

To get only timings results and not compare them with reference ones, use:

```
--no-ref
```

# Example:

## Collect reference timings for current hardware:
```
$ ./ref-test.py --ref-run --lab lab1-whole --bin ./lab --type mpi --parallelism 1,2,3,4
=== Checking binaries...
mpirun (Open MPI) 4.1.4

Report bugs to http://www.open-mpi.org/community/help/
=== All binaries available!
=== Reference run lab lab1-whole for parallelism: 1, 2, 3, 4
=== Binary: ./lab Type: mpi
=== Run with parallelism: 1
N = 100, t = 0.00001, e = 0.00000001, count: 22788
=== Run with parallelism 1 done in 0m:0s:253ms
=== Run with parallelism: 2
N = 100, t = 0.00001, e = 0.00000001, count: 22788
=== Run with parallelism 2 done in 0m:0s:200ms
=== Run with parallelism: 3
N = 100, t = 0.00001, e = 0.00000001, count: 22788
=== Run with parallelism 3 done in 0m:0s:184ms
=== Run with parallelism: 4
N = 100, t = 0.00001, e = 0.00000001, count: 22788
=== Run with parallelism 4 done in 0m:0s:182ms
Reference run completed. Timings:
Parallelism  Time
1            0m:0s:253ms
2            0m:0s:200ms
3            0m:0s:184ms
4            0m:0s:182ms
Total time: 0m:1s:827ms
```

## Compare results with collected references:

```
ref-test.py --lab lab1-whole --bin ./lab --type mpi --accuracy 1 --parallelism 1,2,3,4
=== Checking binaries...
mpirun (Open MPI) 4.1.4

Report bugs to http://www.open-mpi.org/community/help/
=== All binaries available!
=== Compare run lab lab1-whole for parallelism: 1, 2, 3, 4
=== Binary: ./lab Type: mpi
=== Run with parallelism: 1
N = 100, t = 0.00001, e = 0.00000001, count: 22788
=== Run with parallelism 1 done in 0m:0s:254ms
=== Invalid accuracy diff (WORSE): 1ms < 1ms Reference time is: 0m:0s:253ms
=== Run with parallelism: 2
N = 100, t = 0.00001, e = 0.00000001, count: 22788
=== Run with parallelism 2 done in 0m:0s:199ms
=== Invalid accuracy diff (BETTER): 1ms < 1ms Reference time is: 0m:0s:200ms
=== Run with parallelism: 3
N = 100, t = 0.00001, e = 0.00000001, count: 22788
=== Run with parallelism 3 done in 0m:0s:189ms
=== Invalid accuracy diff (WORSE): 5ms < 1ms Reference time is: 0m:0s:184ms
=== Run with parallelism: 4
N = 100, t = 0.00001, e = 0.00000001, count: 22788
=== Run with parallelism 4 done in 0m:0s:180ms
=== Invalid accuracy diff (BETTER): 2ms < 1ms Reference time is: 0m:0s:182ms
Compare run completed. Timings & Stats:
Accuracy: +-0m:0s:1ms
Parallelism  Valid   Result time     Reference time
1            equal   0m:0s:254ms     0m:0s:253ms
2            equal   0m:0s:199ms     0m:0s:200ms
3            worse   0m:0s:189ms     0m:0s:184ms
4            better  0m:0s:180ms     0m:0s:182ms
Total time: 0m:1s:831ms
```

# Tips & tricks, troubleshooting:

## Change reference database file:

```
--database <path to json timings database>
```

## MPI oversubscribe:

Some versions of MPI by default do not allow you to specify more cores than are available on the current hardware.
To get around this restriction for OpenMPI, script uses the `--oversubscribe` option by default.
If you have a different implementation of MPI, you can override this option with:

```
--mpi-oversubscribe-arg <arg with '--'>
```

Or disable this substitution altogether:

```
--mpi-no-oversubscribe
```
