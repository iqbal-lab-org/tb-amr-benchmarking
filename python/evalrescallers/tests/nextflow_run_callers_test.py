import glob
from operator import itemgetter
import json
import os
import sys
import shutil
import subprocess
import unittest

from evalrescallers import run_res_callers

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)))
import nextflow_helper
data_dir = os.path.join(nextflow_helper.data_root_dir, 'nextflow_run_callers')
modules_dir = os.path.dirname(os.path.abspath(run_res_callers.__file__))


class TestNextflowRunCallers(unittest.TestCase):
    def test_nextflow_run_callers(self):
        '''test nextflow_run_callers'''
        nextflow_helper.write_config_file()
        input_data_file = 'tmp.nextflow_run_callers.data.tsv'
        with open(input_data_file, 'w') as f:
            reads_prefix = os.path.join(data_dir, 'reads')
            print('ERR025839', reads_prefix + '.1.1.fq', reads_prefix + '.1.2.fq', sep='\t', file=f)
            print('sample2', reads_prefix + '.2.1.fq', reads_prefix + '.2.2.fq', sep='\t', file=f)

        callers_file = os.path.join(data_dir, 'callers.tsv')
        nextflow_file = os.path.join(nextflow_helper.nextflow_dir, 'run_callers.nf')
        work_dir = 'tmp.nextflow_run_callers.work'
        outdir = 'tmp.nextflow_run_callers.out'

        command = ' '.join([
            'nextflow run',
            '--input_data_file', input_data_file,
            '--callers_file', callers_file,
            '--output_dir', outdir,
            '--species tb',
            '--testing',
            '-c', nextflow_helper.config_file,
            '-w ', work_dir,
            nextflow_file,
        ])

        try:
            completed_process = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as e:
            print('Error running nextflow\nCommand: ', command)
            print('Output:', e.stdout.decode(), sep='\n')
            print('\n____________________________________\n')
            self.assertTrue(False)

        os.unlink(input_data_file)
        nextflow_helper.clean_files()

        expected_json = os.path.join(data_dir, 'expected.summary.json')
        with open(expected_json) as f:
            expect_json_data = json.load(f)

        files_to_check = [
            os.path.join(outdir, 'caller_output', '0', '0', 'summary.json'),
            os.path.join(outdir, 'caller_output', '0', '1', 'summary.json'),
        ]
        tools = ['KvarQ', 'Mykrobe.tb.Fail', 'Mykrobe.tb.walker-2015', 'TB-Profiler']

        for filename in files_to_check:
            with open(filename) as f:
                got = json.load(f)

            for tool in tools:
                # Check resistance calls. Can't check memory and time because
                # will be different each time it's run
                self.assertEqual(expect_json_data[tool]['Success'], got[tool]['Success'])
                if tool == 'Mykrobe.tb.Fail':
                    continue

                self.assertEqual(expect_json_data[tool]['resistance_calls'], got[tool]['resistance_calls'])
                self.assertIn('time_and_memory', got[tool])
                self.assertIn('ram', got[tool]['time_and_memory'])
                self.assertIn('system_time', got[tool]['time_and_memory'])
                self.assertIn('user_time', got[tool]['time_and_memory'])
                self.assertIn('wall_clock_time', got[tool]['time_and_memory'])

        shutil.rmtree(work_dir)


        self.assertTrue(os.path.exists(os.path.join(outdir, 'summary.json')))

        for r_string in ['r_is_resistant', 'r_is_susceptible']:
            prefix = os.path.join(outdir, f'summary.{r_string}.')
            for suffix in ['accuracy_stats.tsv'] + [f'variant_counts.{x}.tsv' for x in tools]:
                self.assertTrue(os.path.exists(prefix + suffix))

        shutil.rmtree(outdir)


