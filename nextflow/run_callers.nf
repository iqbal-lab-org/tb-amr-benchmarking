params.help = false
params.input_data_file = ""
params.no_new_data = false
params.callers_file = ""
params.output_dir = ""
params.max_forks_run_callers = 100
params.summarise_threads = 10
params.testing = false
params.species = ""


if (params.help){
    log.info"""
        Add help message

        Required options:
            --input_data_file add description
            --callers_file    add description
            --output_dir      add description

        Other options:
            --max_forks_run_callers
                              add description

    """.stripIndent()

    exit 0
}


if (!(params.species == "tb" || params.species == "staph")) {
    exit 1, "Species must be 'tb' or 'staph', but got '${params.species}' -- aborting"
}

if (params.testing) {
    testing_string = "--testing"
}
else {
    testing_string = ""
}

input_data_file = file(params.input_data_file).toAbsolutePath()
if (!input_data_file.exists()){
    exit 1, "Input data file not found: ${params.input_data_file} -- aborting"
}

callers_file = file(params.callers_file).toAbsolutePath()
if (!callers_file.exists()){
    exit 1, "Input callers file not found: ${params.callers_file} -- aborting"
}


if (params.no_new_data) {
    setup_no_new_data = "--no_new_data"
}
else {
    setup_no_new_data = ""
}

output_dir = file(params.output_dir).toAbsolutePath()

if (output_dir.exists()) {
    println "Using existing output directory $output_dir"
}
else if (!output_dir.mkdirs()) {
    exit 1, "Error making output directory: ${params.output_dir} -- aborting"
}

caller_output_dir = file("${params.output_dir}/caller_output").toAbsolutePath()
summary_output_prefix = file("${params.output_dir}/summary").toAbsolutePath()



process setup_output_dir {
    memory '1 GB'

    input:
    file input_data_file

    output:
    file jobs_tsv into jobs_tsv_channel

    """
    evalrescallers setup_pipeline_outdir ${setup_no_new_data} ${input_data_file} jobs_tsv ${caller_output_dir}
    """
}


jobs_tsv_channel.splitCsv(header:true, sep:'\t').set{tsv_lines}


process run_callers {
    maxForks params.max_forks_run_callers
    memory {params.testing ? '100 MB' : 13.GB * task.attempt}
    errorStrategy {task.attempt < 3 ? 'retry' : 'ignore'}
    maxRetries 3

    input:
    val fields from tsv_lines

    output:
    file run_callers_done
    val(42) into summarise_input_channel

    """
    evalrescallers run_callers_on_one_sample ${testing_string} ${callers_file} ${caller_output_dir}/${fields.sample_dir} ${fields.reads1} ${fields.reads2}
    touch run_callers_done
    """
}


process summarise {
    memory {params.testing ? '100 MB' : '3 GB'}
    cpus {params.testing ? 0 : params.summarise_threads}


    input:
    val(foo) from summarise_input_channel.collect()

    output:
    file summary_done

    """
    evalrescallers make_summary_json --threads ${params.summarise_threads} ${caller_output_dir} ${summary_output_prefix}.json
    touch summary_done
    """
}

