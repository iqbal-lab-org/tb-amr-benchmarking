from evalrescallers import pipeline_output_dir

def run(options):
    pipe_dir = pipeline_output_dir.PipelineOutputDir(options.pipeline_dir)
    pipe_dir.make_summary_json_of_all_samples(options.outfile, threads=options.threads)

