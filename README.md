# tb-amr-benchmarking

Pipeline for benchmarking TB AMR callers.

## Installation

Nextflow and singularity need to be installed.

Clone this repository, and build the singularity container:

    cd singularity
    sudo singularity build container.img singularity.def

Those commands made a new container called `container.img`.

## Running the pipeline

The pipeline is run using nextflow. Basic instructions follow, but you may
need to change nextflow options or config depending on your environment.

The nextflow script to run is `nextflow/run_callers.nf` in this repository.

Two input tab-delimited files are required:
* A file with sample names and reads file paths.
  This should have no header line, and
  one line per sample. Column 1 = sample name, Column 2 = reads file 1,
  Column 3 = reads file 2.
* A file defining which callers to use. This needs the following columns:
  1. Name of caller. Must be one of: ARIBA, KvarQ, MTBseq, Mykrobe, TB-Profiler.
  2. 0 or 1. 0 means for each sample, do not rerun if the results are already
     found. 1 means always rerun, deleting the old data. See the section
     below on rerunning the pipeline.
  3. Name of tool to use in output files (will also be used as the
     subdirectory name in the output directory).
  4. Species. Must be "tb" (this is here for the future, when we may want to
     evaluate other species).
  5. Only applicable to ARIBA and Mykrobe. If ARIBA, should be the reference
     directory. If Mykrobe, should be a panel name to use a built-in panel,
     or a "." if providing your own panel using columns 6 and 7.
     Use "." for all other tools.
  6. Probes FASTA file. Only applicable for mykrobe, otherwise use ".".
     Must not be "." if tool is Mykrobe and column 5 is ".".
  7. Mykrobe resistance to drug JSON file. Put "." if the tool is not mykrobe.
     Must not be "." if tool is Mykrobe and column 5 is ".".
  8. Any command line options to pass to the tool when it is run.
     Put a "." to use the default options.

Assuming those files are called `data.tsv` and `callers.tsv`, run the pipeline
with a command like this (where you will need to fix
`/your/path/to/the/container.img`):

```
nextflow run nextflow/run_callers.nf \
  -with-singularity /your/path/to/the/container.img \
  --species tb \
  --input_data_file data.tsv \
  --callers_file callers.tsv \
  --output_dir OUT
```

That will write the output to the directory `OUT`.

All the results will be summarised into a single JSON file called
`OUT/summary.json`.
This file is used as input to code in the repository
https://github.com/iqbal-lab-org/tb-amr-benchmarking-paper.


## Rerunning the pipeline

The pipeline can be run more than once on the same output directory, but
with different callers (by using a different `callers.tsv` file), or by adding
more samples (by adding lines to the `data.tsv` file).


* If you are adding new samples, then
rerun the `nextflow run` command with no changes.
* If you are not adding new samples, then add the option `--no_new_data` to the
nextflow command.
* If you have changed the `callers.tsv` file, then rerun with the option
`--no_new_data`. Or if you have also added new samples, then do not use the
`--no_new_data` option.

If new samples or tools are added, then those new samples/tools will be run.
Existing runs will either be left alone (ie not rerun), or will be deleted
and rerun depending on column 2 of the `callers.tsv` file. 0 will mean that
nothing is rerun (but new samples/tools are run). 1 will mean that any existing
results for that tool are discarded, and everything is run from scratch for
that tool.
