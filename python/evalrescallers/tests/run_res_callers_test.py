import filecmp
import os
import shutil
import unittest

from evalrescallers import run_res_callers

modules_dir = os.path.dirname(os.path.abspath(run_res_callers.__file__))
data_dir = os.path.join(modules_dir, 'tests', 'data', 'run_res_callers')

class TestRunResCallers(unittest.TestCase):
    def test_load_callers_file(self):
        '''test load_callers_file'''
        expected = [
            run_res_callers.Caller('Mykrobe', True, 'dir1', 'staph', None, None, None, '--opt1 val1'),
            run_res_callers.Caller('Mykrobe', True, 'dir2', 'tb', 'walker-2015', None, None, None),
            run_res_callers.Caller('Mykrobe', False, 'dir3', 'tb', 'panel_name', '/path/to/probes', '/path/to/var_to_res', '--opt2 val2'),
            run_res_callers.Caller('TB-Profiler', False, 'dir4', None, None, None, None, None),
            run_res_callers.Caller('KvarQ', True, 'dir5', None, None, None, None, None),
            run_res_callers.Caller('MTBseq', True, 'dir6', None, None, None, None, None),
            run_res_callers.Caller('ARIBA', False, 'dir7', None, 'ref_dir', None, None, None),
        ]
        infile = os.path.join(data_dir, 'load_callers_file.tsv')
        got = run_res_callers.load_callers_file(infile)
        self.assertEqual(expected, got)


    def test_summary_json_from_all_callers(self):
        '''test summary_json_from_all_callers'''
        json_dict = {
            'sample1': os.path.join(data_dir, 'summary_json_from_all_callers.1.json'),
            'sample2': os.path.join(data_dir, 'summary_json_from_all_callers.2.json'),
        }
        tmp_file = 'tmp.summary_json_from_all_callers.json'
        expected_file = os.path.join(data_dir, 'summary_json_from_all_callers.expect.json')
        run_res_callers.summary_json_from_all_callers(json_dict, tmp_file)
        self.assertTrue(filecmp.cmp(expected_file, tmp_file, shallow=False))
        os.unlink(tmp_file)


    def test_run_res_callers(self):
        '''test run_res_callers'''
        callers_file = os.path.join(data_dir, 'run_res_callers.callers.tsv')
        callers_file2 = os.path.join(data_dir, 'run_res_callers.callers.2.tsv')
        reads1 = os.path.join(data_dir, 'run_res_callers.reads1')
        reads2 = os.path.join(data_dir, 'run_res_callers.reads2')
        tmp_out = 'tmp.run_res_callers'
        run_res_callers.run_res_callers(callers_file, tmp_out, reads1, reads2, testing=True)
        self.assertTrue(os.path.exists(os.path.join(tmp_out, 'outdir1', 'command.out')))
        self.assertTrue(os.path.exists(os.path.join(tmp_out, 'outdir1', 'summary.json')))
        self.assertTrue(os.path.exists(os.path.join(tmp_out, 'outdir2', 'command.out')))
        self.assertTrue(os.path.exists(os.path.join(tmp_out, 'outdir2', 'summary.json')))
        self.assertTrue(os.path.exists(os.path.join(tmp_out, 'outdir3', 'command.out')))
        self.assertTrue(os.path.exists(os.path.join(tmp_out, 'outdir3', 'summary.json')))
        self.assertTrue(os.path.exists(os.path.join(tmp_out, 'summary.json')))
        self.assertFalse(os.path.exists(os.path.join(tmp_out, 'outdir4', 'command.out')))
        self.assertFalse(os.path.exists(os.path.join(tmp_out, 'outdir4', 'summary.json')))
        run_res_callers.run_res_callers(callers_file2, tmp_out, reads1, reads2, testing=True)
        self.assertTrue(os.path.exists(os.path.join(tmp_out, 'outdir5', 'command.out')))
        self.assertTrue(os.path.exists(os.path.join(tmp_out, 'outdir5', 'summary.json')))
        self.assertTrue(os.path.exists(os.path.join(tmp_out, 'outdir6', 'command.out')))
        self.assertTrue(os.path.exists(os.path.join(tmp_out, 'outdir6', 'summary.json')))
        shutil.rmtree(tmp_out)

