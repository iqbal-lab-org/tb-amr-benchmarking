import csv
import multiprocessing
import os
import subprocess

import evalrescallers


def make_dir(d):
    if not os.path.exists(d):
        os.mkdir(d)


def download_one_run(run_id, outdir):
    success_file = f'{outdir}.success'
    fail_file = f'{outdir}.fail'
    if os.path.exists(success_file):
        return True
    elif os.path.exists(fail_file):
        return False

    command = f'enaDataGet -f fastq -d {outdir} {run_id}'
    print(command)
    completed_process = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
    if completed_process.returncode == 0:
        with open(success_file, 'w') as f:
            return True
    else:
        with open(fail_file, 'w') as f:
            return False


def cat_reads_and_clean(to_cat, outfile):
    if len(to_cat) == 1:
        os.rename(to_cat[0], outfile)
        return True
    else:
        cat = 'cat ' + ' '.join(to_cat) + ' > ' + outfile
        print(cat)
        completed_process = subprocess.run(cat, shell=True, stdout=subprocess.PIPE)
        if completed_process.returncode == 0:
            for f in to_cat:
                os.unlink(f)

            return True
        else:
            return False


def download_sample(outdir, sample_id, run_ids):
    success_file = os.path.join(outdir, 'success')
    fail_file = os.path.join(outdir, 'fail')

    if os.path.exists(success_file):
        return True
    elif os.path.exists(fail_file):
        return False
    elif os.path.exists(outdir):
        completed_process = subprocess.run(f'rm -rf {outdir}', shell=True)

    make_dir(outdir)
    success_statuses = {}
    fwd_reads = []
    rev_reads = []

    for run_id in sorted(run_ids):
        run_out = os.path.join(outdir, run_id)
        success_statuses[run_id] = download_one_run(run_id, run_out)
        if not success_statuses[run_id]:
            with open(fail_file, 'w') as f:
                return False

        fwd = os.path.join(outdir, run_id, run_id, f'{run_id}_1.fastq.gz')
        fwd_reads.append(fwd)
        rev = os.path.join(outdir, run_id, run_id, f'{run_id}_2.fastq.gz')
        rev_reads.append(rev)
        if not (os.path.exists(fwd) and os.path.exists(rev)):
            with open(fail_file, 'w') as f:
                return False

    fwd_reads.sort()
    rev_reads.sort()
    fwd = os.path.join(outdir, 'reads_1.fastq.gz')
    rev = os.path.join(outdir, 'reads_2.fastq.gz')
    fwd_cat_ok = cat_reads_and_clean(fwd_reads, fwd)
    if fwd_cat_ok:
        rev_cat_ok = cat_reads_and_clean(rev_reads, rev)
        if rev_cat_ok:
            for f in os.listdir(outdir):
                f_path = os.path.join(outdir, f)
                if os.path.isdir(f_path) or f.endswith('.success'):
                    command = f'rm -rf {f_path}'
                    completed_process = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
                    if completed_process.returncode != 0:
                        with open(fail_file, 'w') as f:
                            return False
            with open(success_file, 'w') as f:
                return True

    with open(fail_file, 'w') as f:
        return False


def load_accessions():
    eval_dir = os.path.abspath(os.path.dirname(evalrescallers.__file__))
    data_dir = os.path.join(eval_dir, 'data')
    pheno_file = os.path.join(data_dir, '10k_validation.phenotype.tsv')
    accessions = []
    with open(pheno_file) as f:
        dict_reader = csv.DictReader(f, delimiter='\t')
        accessions = [x['ena_id'] for x in dict_reader]

    accessions.sort()
    return accessions


def get_sample(sample):
    runs = sorted(sample.split('.'))
    print('Getting', sample, ','.join(runs))
    samples_dir = sample[:6]
    make_dir(samples_dir)
    sample_dir = os.path.join(samples_dir, sample)
    if download_sample(sample_dir, sample, runs):
        print('Success', sample, ','.join(runs))
    else:
        print('Fail', sample, ','.join(runs))



def get_samples(output_dir, threads=1):
    samples = load_accessions()
    print(f'Going to download {len(samples)} samples using {threads} thread(s)...')
    make_dir(output_dir)
    os.chdir(output_dir)

    with multiprocessing.Pool(threads) as pool:
        pool.map(get_sample, samples)


