from evalrescallers import pipeline_output_dir

def run(options):
    pipe_dir = pipeline_output_dir.PipelineOutputDir(options.outdir)
    if not options.no_new_data:
        pipe_dir.add_data_from_file(options.data_tsv)
        pipe_dir.write_json_data_file()
    pipe_dir.write_tsv_file(options.out_tsv)

