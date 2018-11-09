import filecmp
import os
import shutil
import unittest

from evalrescallers import res_caller

modules_dir = os.path.dirname(os.path.abspath(res_caller.__file__))
data_dir = os.path.join(modules_dir, 'tests', 'data', 'res_caller')

class TestResCaller(unittest.TestCase):
    def test_mtbseq_tab_file_to_res_calls(self):
        '''test _mtbseq_tab_file_to_res_calls'''
        infile = os.path.join(data_dir, 'mtbseq_tab_file_to_res_calls.tab')
        got = res_caller.ResCaller._mtbseq_tab_file_to_res_calls(infile)
        expect = {
            'Drug1': {('R', 'gyrA', 'Glu21Gln', None)},
            'Drug2': {('R', 'Rv0042', 'Glu21Leu', None)},
        }
        self.assertEqual(expect, got)


    def test_mtbseq_outdir_to_res_calls_json_file(self):
        '''test _mtbseq_outdir_to_res_calls_json_file'''
        indir = os.path.join(data_dir, 'mtbseq_outdir_to_res_calls_json_file')
        outfile = 'tmp.mtbseq_outdir_to_res_calls_json_file.json'
        res_caller.ResCaller._mtbseq_outdir_to_res_calls_json_file(indir, outfile)
        expect = os.path.join(data_dir, 'mtbseq_outdir_to_res_calls_json_file.expect')
        self.assertTrue(filecmp.cmp(expect, outfile, shallow=False))
        os.unlink(outfile)


    def test_kvarq_var_string_parser(self):
        '''test _kvarq_var_string_parser'''
        self.assertEqual(('Isoniazid', 'inhA', 'promoter mutation -15'), res_caller.ResCaller._kvarq_var_string_parser('Isoniazid resistance::SNP1673425CT=inhA promoter mutation -15'))
        self.assertEqual(('Ethambutol', 'embB', 'M306I'), res_caller.ResCaller._kvarq_var_string_parser('Ethambutol resistance::SNP4247431GC=embB.M306I'))
        self.assertEqual(('Rifampicin', 'rpoC', 'V483G'), res_caller.ResCaller._kvarq_var_string_parser('Rifampicin resistance (compensatory)::SNP764817TG=rpoC.V483G'))
        self.assertEqual(('Isoniazid', 'katG', 'S315T'), res_caller.ResCaller._kvarq_var_string_parser('Isoniazid resistance [2155168CG=katG.S315T]'))
        self.assertEqual(('Rifampicin', 'rpoB', 'S450L'), res_caller.ResCaller._kvarq_var_string_parser('Rifampicin resistance (RRDR) [761155CT=rpoB.S450L]'))
        self.assertEqual(('Fluoroquinolones', 'Parse_error', 'Parse_error'), res_caller.ResCaller._kvarq_var_string_parser('Fluoroquinolones resistance (QRDR) [7564GC=gyrA.G88A [NONE OF MUTATIONS DOCUMENTED IN REFERENCE]]'))


    def test_tb_profiler_var_string_parser(self):
        '''test _tb_profiler_var_string_parser'''
        self.assertEqual('C42G', res_caller.ResCaller._tb_profiler_var_string_parser('42C>42G'))
        self.assertEqual('A907C', res_caller.ResCaller._tb_profiler_var_string_parser('907A>C'))
        self.assertEqual('G-17T', res_caller.ResCaller._tb_profiler_var_string_parser('-17G>T'))
        self.assertEqual('W477*', res_caller.ResCaller._tb_profiler_var_string_parser('477W>477*'))

        with self.assertRaises(Exception):
            res_caller.ResCaller._tb_profiler_var_string_parser('42C<42G')
        with self.assertRaises(Exception):
            res_caller.ResCaller._tb_profiler_var_string_parser('42>42G')
        with self.assertRaises(Exception):
            res_caller.ResCaller._tb_profiler_var_string_parser('42C>42')
        with self.assertRaises(Exception):
            res_caller.ResCaller._tb_profiler_var_string_parser('42C>43G')


    def test_json_to_resistance_calls_KvarQ(self):
        '''test _json_to_resistance_calls with KvarQ'''
        json_file = os.path.join(data_dir, 'json_to_resistance_calls.KvarQ.json')
        expected = {
            'Ethambutol': [('R', 'embB', 'M306I', None)],
            'Quinolones': [('R', 'gyrA', 'D94G', None)],
            'Amikacin': [('R', 'rrsK', 'S467S', None)],
            'Kanamycin': [('R', 'rrsK', 'S467S', None)],
        }
        got = res_caller.ResCaller._json_to_resistance_calls(json_file, 'KvarQ')
        self.assertEqual(expected, got)


    def test_json_to_resistance_calls_Mykrobe(self):
        '''test _json_to_resistance_calls with Mykrobe'''
        json_file = os.path.join(data_dir, 'json_to_resistance_calls.Mykrobe.json')
        expected = {
            'Ethambutol': [('R', 'embB', 'M306I', {'conf': 99999997, 'ref_depth': 0, 'alt_depth': 6, 'expected_depth': 6})],
            'Quinolones': [('R', 'gyrA', 'A74S', {'conf': 99999990, 'ref_depth': 0, 'alt_depth': 4, 'expected_depth': 6}), ('R', 'gyrA', 'D94G', {'conf': 99999996, 'ref_depth': 0, 'alt_depth': 2, 'expected_depth': 6})],
            'Ofloxacin': [('R', 'gyrA', 'A74S', {'conf': 99999990, 'ref_depth': 0, 'alt_depth': 4, 'expected_depth': 6})],
            'Rifampicin': [('r', 'rpoB', 'I491F', {'conf': 99999996, 'ref_depth': 0, 'alt_depth': 9, 'expected_depth': 6})],
            'Capreomycin': [('S', None, None, {})],
            'Isoniazid': [('S', None, None, {})],
            'Amikacin': [('R', 'geneX', 'NA', {'conf': None, 'ref_depth': None, 'alt_depth': None, 'expected_depth': None})],
            'Pyrazinamide': [('S', None, None, {})],
            'Kanamycin': [('S', None, None, {})],
            'Streptomycin': [('S', None, None, {})],
        }
        self.maxDiff=None
        got = res_caller.ResCaller._json_to_resistance_calls(json_file, 'Mykrobe')
        self.assertEqual(expected, got)


    def test_json_to_resistance_calls_TB_Profiler(self):
        '''test _json_to_resistance_calls with TB-Profiler'''
        json_file = os.path.join(data_dir, 'json_to_resistance_calls.TB-Profiler.json')
        expected = {
            'Ethambutol': [('R', 'embB', 'M306I', None)],
            'Quinolones': [('R', 'gyrA', 'D94G', None)],
            'Rifampicin': [('R', 'rpoB', 'I491F', None)],
        }
        got = res_caller.ResCaller._json_to_resistance_calls(json_file, 'TB-Profiler')
        self.assertEqual(expected, got)


    def test_bash_out_to_time_and_memory(self):
        '''test _bash_out_to_time_and_memory'''
        infile = os.path.join(data_dir, 'bash_out_to_time_and_memory.txt')
        expected = {
            'user_time': 19.96,
            'system_time': 1.09,
            'wall_clock_time': 21.08,
            'ram': 2533064.0
        }
        got = res_caller.ResCaller._bash_out_to_time_and_memory(infile)
        self.assertEqual(expected, got)

        expected['wall_clock_time'] = 7282.42
        infile = os.path.join(data_dir, 'bash_out_to_time_and_memory.2.txt')
        got = res_caller.ResCaller._bash_out_to_time_and_memory(infile)
        self.assertEqual(expected, got)


    def test_run_mtbseq(self):
        '''test run MTBseq'''
        reads1 = os.path.join(data_dir, 'reads_for_MTBseq_1.fastq.gz')
        reads2 = os.path.join(data_dir, 'reads_for_MTBseq_2.fastq.gz')
        tmp_dir =  'tmp.res_caller.run.MTBseq'
        caller = res_caller.ResCaller('MTBseq', tmp_dir)
        caller.run(reads1, reads2)
        self.assertTrue(os.path.exists(os.path.join(tmp_dir, 'out.json')))
        self.assertTrue(os.path.exists(os.path.join(tmp_dir, 'summary.json')))
        self.assertTrue(os.path.exists(os.path.join(tmp_dir, 'command.out')))
        shutil.rmtree(tmp_dir)


    def test_run_mykrobe(self):
        '''test run Mykrobe'''
        reads1 = os.path.join(data_dir, 'reads_1.fastq.gz')
        reads2 = os.path.join(data_dir, 'reads_2.fastq.gz')
        tmp_dir = 'tmp.res_caller.run.Mykrobe'
        caller = res_caller.ResCaller('Mykrobe', tmp_dir)
        caller.run(reads1, reads2, mykrobe_species='tb', mykrobe_panel='walker-2015')
        self.assertTrue(os.path.exists(os.path.join(tmp_dir, 'out.json')))
        self.assertTrue(os.path.exists(os.path.join(tmp_dir, 'summary.json')))
        self.assertTrue(os.path.exists(os.path.join(tmp_dir, 'command.out')))
        shutil.rmtree(tmp_dir)


    def test_run_tb_profiler(self):
        '''test run TB-Profiler'''
        reads1 = os.path.join(data_dir, 'reads_1.fastq.gz')
        reads2 = os.path.join(data_dir, 'reads_2.fastq.gz')
        tmp_dir = 'tmp.res_caller.run.TB-Profiler'
        caller = res_caller.ResCaller('TB-Profiler', tmp_dir)
        caller.run(reads1, reads2)
        self.assertTrue(os.path.exists(os.path.join(tmp_dir, 'out.json')))
        self.assertTrue(os.path.exists(os.path.join(tmp_dir, 'summary.json')))
        self.assertTrue(os.path.exists(os.path.join(tmp_dir, 'command.out')))
        shutil.rmtree(tmp_dir)


    def test_run_kvarq(self):
        '''test run KvarQ'''
        reads1 = os.path.join(data_dir, 'reads_1.fastq.gz')
        reads2 = os.path.join(data_dir, 'reads_2.fastq.gz')
        tmp_dir = 'tmp.res_caller.run.KvarQ'
        caller = res_caller.ResCaller('KvarQ', tmp_dir)
        caller.run(reads1, reads2)
        self.assertTrue(os.path.exists(os.path.join(tmp_dir, 'out.json')))
        self.assertTrue(os.path.exists(os.path.join(tmp_dir, 'summary.json')))
        self.assertTrue(os.path.exists(os.path.join(tmp_dir, 'command.out')))
        shutil.rmtree(tmp_dir)

