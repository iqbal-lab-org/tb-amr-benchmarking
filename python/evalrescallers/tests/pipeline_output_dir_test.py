import filecmp
import json
import os
import shutil
import unittest

from evalrescallers import pipeline_output_dir

modules_dir = os.path.dirname(os.path.abspath(pipeline_output_dir.__file__))
data_dir = os.path.join(modules_dir, 'tests', 'data', 'pipeline_output_dir')


class TestOtherFunctions(unittest.TestCase):
    def test_load_one_sample_summary_json_file(self):
        '''test load_one_sample_summary_json_file'''
        infile = os.path.join(data_dir, 'load_one_sample_summary_json_file.json')

        expect = {
            "Tool1": {
                "Success": True,
                "resistance_calls": {
                    "Drug1": [
                        ["R", "gene1", "A42B", 42]
                    ],
                    "Drug2": [
                        ["R", "gene2", "C43D", None]
                    ],
                },
                "time_and_memory": {
                    "ram": 100.0,
                    "system_time": 0.33,
                    "user_time": 1116.56,
                    "wall_clock_time": 1318.59
                }
            },
        }

        got_sample, got_dict = pipeline_output_dir.load_one_sample_summary_json_file(('sample', infile))
        self.assertEqual('sample', got_sample)
        self.assertEqual(expect, got_dict)


class TestPipelineOutputDir(unittest.TestCase):
    def test_init(self):
        '''test init'''
        expected = {'samples_per_dir': 42,
          'samples': {
            'sample1': {'name': 'sample1', 'reads': ['file1.1', 'file1.2'], 'number': 0, 'dir': '0/0'},
            'sample2': {'name': 'sample2', 'reads': ['file2.1', 'file2.2'], 'number': 1, 'dir': '0/1'}
          }
        }
        pipe_dir = os.path.join(data_dir, 'init')
        pipe_dir_obj = pipeline_output_dir.PipelineOutputDir(pipe_dir)
        self.assertEqual(expected, pipe_dir_obj.data)

        expected = {'samples_per_dir': 42, 'samples': {}}
        pipe_dir_obj = pipeline_output_dir.PipelineOutputDir('does_not_exist', samples_per_dir=42)
        self.assertEqual(expected, pipe_dir_obj.data)


    def test_load_input_data_file(self):
        '''test load_input_data_file'''
        good_file = os.path.join(data_dir, 'load_input_data_file.tsv')
        bad_file = os.path.join(data_dir, 'load_input_data_file.bad.tsv')

        with self.assertRaises(Exception):
            pipeline_output_dir.PipelineOutputDir.load_input_data_file(bad_file)

        got = pipeline_output_dir.PipelineOutputDir.load_input_data_file(good_file)
        expected = {
            's1': {'name': 's1', 'reads': ['s1_1.fq.gz', 's1_2.fq.gz'], 'number': None, 'dir': None},
            's2': {'name': 's2', 'reads': ['s2_1.fq.gz', 's2_2.fq.gz'], 'number': None, 'dir': None},
        }
        self.assertEqual(expected, got)


    def test_sample_number_to_dir(self):
        '''test sample_number_to_dir'''
        tests = [
            ((0, 10), os.path.join('0', '0')),
            ((1, 10), os.path.join('0', '1')),
            ((8, 10), os.path.join('0', '8')),
            ((9, 10), os.path.join('0', '9')),
            ((10, 10), os.path.join('1', '10')),
            ((11, 10), os.path.join('1', '11')),
        ]

        for (number, samples_per_dir), expected in tests:
            self.assertEqual(expected, pipeline_output_dir.PipelineOutputDir.sample_number_to_dir(number, samples_per_dir))


    def test_add_data_from_file(self):
        '''test add_data_from_file'''
        tmp_dir = 'tmp.test_add_data_from_file'
        data_file = os.path.join(data_dir, 'add_data_from_file.1.tsv')
        pipe_dir = pipeline_output_dir.PipelineOutputDir(tmp_dir)
        pipe_dir.add_data_from_file(data_file)
        expected_data = {
            'samples_per_dir': 100,
            'samples': {'s1': {'name': 's1', 'reads': ['s1_1.fq.gz', 's1_2.fq.gz'], 'number': 0, 'dir': os.path.join('0', '0')}},
        }
        self.assertEqual(expected_data, pipe_dir.data)
        self.assertTrue(os.path.exists(os.path.join(tmp_dir, '0', '0')))

        data_file = os.path.join(data_dir, 'add_data_from_file.2.tsv')
        pipe_dir.add_data_from_file(data_file)
        expected_data['samples']['s2'] = {'name': 's2', 'reads': ['s2_1.fq.gz', 's2_2.fq.gz'], 'number': 1, 'dir': os.path.join('0', '1')}
        self.assertEqual(expected_data, pipe_dir.data)
        self.assertTrue(os.path.exists(os.path.join(tmp_dir, '0', '1')))
        shutil.rmtree(tmp_dir)


    def test_write_json_data_file(self):
        '''test write_json_data_file'''
        tmp_dir = 'tmp.pipeline_output_dir.write_json_data_file'
        pipe_dir = pipeline_output_dir.PipelineOutputDir(tmp_dir)
        pipe_dir.data = {'spam': 'eggs', 'rush': ['lifeson', 'lee', 'peart']}
        pipe_dir.write_json_data_file()
        expected = os.path.join(data_dir, 'write_json_data_file.json')
        self.assertTrue(filecmp.cmp(expected, pipe_dir.json_data_file, shallow=False))
        shutil.rmtree(tmp_dir)


    def test_write_tsv_file(self):
        '''test write_tsv_file'''
        tmp_tsv = 'tmp.pipeline_output_dir.write_tsv_file.tsv'
        pipe_dir = pipeline_output_dir.PipelineOutputDir(os.path.join(data_dir, 'test_write_tsv_file'))
        pipe_dir.write_tsv_file(tmp_tsv)
        expected = os.path.join(data_dir, 'write_tsv_file.expect.tsv')
        self.assertTrue(filecmp.cmp(expected, tmp_tsv, shallow=False))
        os.unlink(tmp_tsv)


    def test_make_summary_json_of_all_samples(self):
        '''test make_summary_json_of_all_samples'''
        tmp_pipe_dir = 'tmp.make_summary_json_of_all_samples'
        tmp_data_file = 'tmp.make_summary_json_of_all_samples.in.tsv'
        tmp_json = 'tmp.make_summary_json_of_all_samples.json'

        with open(tmp_data_file, 'w') as f:
            print('sample1', 'reads1.1', 'reads1.2', sep='\t', file=f)
            print('sample2', 'reads2.1', 'reads2.2', sep='\t', file=f)

        pipe_dir = pipeline_output_dir.PipelineOutputDir(tmp_pipe_dir)
        pipe_dir.add_data_from_file(tmp_data_file)
        json_data_to_write = {
                'sample1': {'foo': 'bar', 'spam': ['eggs', 'shrubbery']},
                'sample2': {'x': 'y', 'swallow': ['african', 'european']},
        }

        for sample in json_data_to_write:
            outfile = os.path.join(tmp_pipe_dir, pipe_dir.data['samples'][sample]['dir'], 'summary.json')
            with open(outfile, 'w') as f:
                print(json.dumps(json_data_to_write[sample], sort_keys=True, indent=4), file=f)

        pipe_dir.make_summary_json_of_all_samples(tmp_json)
        with open(tmp_json) as f:
            got_data = data = json.load(f)
        self.assertEqual(json_data_to_write, got_data)

        os.unlink(tmp_json)
        pipe_dir.make_summary_json_of_all_samples(tmp_json, threads=2)
        with open(tmp_json) as f:
            got_data = data = json.load(f)
        self.assertEqual(json_data_to_write, got_data)

        shutil.rmtree(tmp_pipe_dir)
        os.unlink(tmp_data_file)
        os.unlink(tmp_json)

