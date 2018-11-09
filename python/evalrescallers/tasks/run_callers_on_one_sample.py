from evalrescallers import run_res_callers

def run(options):
    run_res_callers.run_res_callers(
        options.callers_file,
        options.outdir,
        options.reads1,
        options.reads2,
        testing=options.testing, 
    )

