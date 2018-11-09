from evalrescallers import ten_k_reads_download

def run(options):
    ten_k_reads_download.get_samples(options.outdir, threads=options.threads)

