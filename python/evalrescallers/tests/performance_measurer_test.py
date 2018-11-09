import copy
import filecmp
import json
import os
import shutil
import unittest

from evalrescallers import performance_measurer

modules_dir = os.path.dirname(os.path.abspath(performance_measurer.__file__))
data_dir = os.path.join(modules_dir, 'tests', 'data', 'performance_measurer')


class TestPerformanceMeasurer(unittest.TestCase):
    def test_summary_json_to_metrics_and_var_call_counts(self):
        '''test summary_json_to_metrics_and_var_call_counts'''
        drugs = {
            'mykrobe': {'Isoniazid', 'Rifampicin'},
            '10k': {'Rifampicin', 'Pyrazinamide'},
        }

        json_file = os.path.join(data_dir, 'summary_json_to_metrics_and_var_call_counts.json')

        truth_pheno = {
            'sample1': {
                'dataset': 'mykrobe',
                'pheno': {'Isoniazid': 'R', 'Rifampicin': 'S'}
            },
            'sample2': {
                'dataset': 'mykrobe',
                'pheno': {'Isoniazid': 'R', 'Rifampicin': 'R'}
            },
            'sample3': {
                'dataset': '10k',
                'pheno': {'Rifampicin': 'S', 'Pyrazinamide': 'R'}
            },
            'sample4': {
                'dataset': '10k',
                'pheno': {'Rifampicin': 'S', 'Pyrazinamide': 'R'}
            },
            'sample5': {
                'dataset': '10k',
                'pheno': {'Rifampicin': 'R', 'Pyrazinamide': 'R'}
            },
        }

        got_tool_counts, got_variant_counts, got_conf_and_depths, got_regimen_counts = performance_measurer.PerformanceMeasurer.summary_json_to_metrics_and_var_call_counts(json_file, truth_pheno, drugs, 'tb')

        expect_tool_counts = {
            'mykrobe': {
                'Isoniazid': {
                    'tool1': {'TP': 2, 'FP': 0, 'TN': 0, 'FN': 0, 'FAIL_R': 0, 'FAIL_S': 0, 'UNK': 0},
                    'tool2': {'TP': 1, 'FP': 0, 'TN': 0, 'FN': 0, 'FAIL_R': 1, 'FAIL_S': 0, 'UNK': 0},
                },
                'Rifampicin': {
                    'tool1': {'TP': 1, 'FP': 0, 'TN': 1, 'FN': 0, 'FAIL_R': 0, 'FAIL_S': 0, 'UNK': 0},
                    'tool2': {'TP': 0, 'FP': 0, 'TN': 0, 'FN': 1, 'FAIL_R': 0, 'FAIL_S': 1, 'UNK': 0},
                },
            },
            '10k': {
                'Rifampicin': {
                    'tool1': {'TP': 0, 'FP': 0, 'TN': 2, 'FN': 0, 'FAIL_R': 0, 'FAIL_S': 0, 'UNK': 0},
                    'tool2': {'TP': 0, 'FP': 1, 'TN': 0, 'FN': 0, 'FAIL_R': 0, 'FAIL_S': 0, 'UNK': 1},
                },
                'Pyrazinamide': {
                    'tool1': {'TP': 1, 'FP': 0, 'TN': 0, 'FN': 1, 'FAIL_R': 0, 'FAIL_S': 0, 'UNK': 0},
                    'tool2': {'TP': 1, 'FP': 0, 'TN': 0, 'FN': 1, 'FAIL_R': 0, 'FAIL_S': 0, 'UNK': 0},
                },
            },
        }
        self.assertEqual(expect_tool_counts, got_tool_counts)

        expect_variant_counts = {
            'mykrobe': {
                'Isoniazid': {
                    'tool1': {'gene1.X42Y': {'TP': 1, 'FP': 0}, 'gene1.A1B': {'TP': 1, 'FP': 0}},
                    'tool2': {'gene1.A1B': {'TP': 1, 'FP': 0}},
                },
                'Rifampicin': {
                    'tool1': {'gene2.C1D;gene2.E2F': {'TP': 1, 'FP': 0}},
                    'tool2': {},
                },
            },
            '10k': {
                'Rifampicin': {
                    'tool1': {},
                    'tool2': {'gene2.I42M': {'TP': 0, 'FP': 1}},
                },
                'Pyrazinamide': {
                    'tool1': {'gene3.X10Y': {'TP': 1, 'FP': 0}},
                    'tool2': {'gene3.X10Y': {'TP': 1, 'FP': 0}},
                },
            },

        }
        self.assertEqual(expect_variant_counts, got_variant_counts)

        expect_conf_and_depths = {
            'mykrobe': {
                'Rifampicin': {},
                'Isoniazid': {
                    'tool1': {'TP': [(42, 0, 10, 11), (43, 0, 11, 11)], 'FP': [], 'TN': [], 'FN': []},
                    'tool2': {'TP': [(44, 0, 12, 11)], 'FP': [], 'TN': [], 'FN': []},
                },
            },
            '10k': {
                'Pyrazinamide': {
                    'tool1': {'TP': [(100, 2, 14, 11)], 'FP': [], 'TN': [], 'FN': []},
                    'tool2': {'TP': [(1001, 0, 5, 1100)], 'FP': [], 'TN': [], 'FN': []},
                },
                'Rifampicin': {'tool2': {'TP': [], 'FP': [(50, 1, 13, 11)], 'TN': [], 'FN': []}},
            },
        }
        self.assertEqual(expect_conf_and_depths, got_conf_and_depths)


        expect_regimen_counts = {
            'mykrobe': {
                'tool1': {(10, 10): 1, (None, None): 1},
                'tool2': {(None, None): 1, (10, None): 1},
            },
            '10k': {
                'tool1': {(None, None): 2},
                'tool2': {(None, None): 1, (None, 10): 1},
            },
        }
        self.assertEqual(expect_regimen_counts, got_regimen_counts)


        # One call is "r" in the input json. Test the option lower_case_r_means_resistant=False)
        got_tool_counts, got_variant_counts, got_conf_and_depths, got_regimen_counts = performance_measurer.PerformanceMeasurer.summary_json_to_metrics_and_var_call_counts(json_file, truth_pheno, drugs, 'tb', lower_case_r_means_resistant=False)
        expect_tool_counts['mykrobe']['Isoniazid']['tool1']['TP'] -= 1
        expect_tool_counts['mykrobe']['Isoniazid']['tool1']['FN'] += 1
        del expect_variant_counts['mykrobe']['Isoniazid']['tool1']['gene1.X42Y']
        expect_conf_and_depths['mykrobe']['Isoniazid']['tool1']['FN'] = [(42, 0, 10, 11)]
        expect_conf_and_depths['mykrobe']['Isoniazid']['tool1']['TP'] = [(43, 0, 11, 11)]
        self.assertEqual(expect_tool_counts, got_tool_counts)
        self.assertEqual(expect_variant_counts, got_variant_counts)
        self.maxDiff = None
        self.assertEqual(expect_conf_and_depths, got_conf_and_depths)


    def test_add_all_counts_to_tools_counts(self):
        '''test add_all_counts_to_tools_counts'''
        tools_counts = {
            'mykrobe': {
                'drug1': {
                    'tool1': {'TP': 2, 'FP': 0, 'TN': 0, 'FN': 1, 'FAIL_R': 0, 'FAIL_S': 0, 'UNK': 2},
                    'tool2': {'TP': 1, 'FP': 1, 'TN': 0, 'FN': 0, 'FAIL_R': 1, 'FAIL_S': 0, 'UNK': 3},
                },
                'drug2': {
                    'tool1': {'TP': 1, 'FP': 1, 'TN': 2, 'FN': 3, 'FAIL_R': 1, 'FAIL_S': 0, 'UNK': 0},
                    'tool2': {'TP': 1, 'FP': 0, 'TN': 0, 'FN': 1, 'FAIL_R': 1, 'FAIL_S': 0, 'UNK': 0},
                },
            },
            '10k': {
                'drug2': {
                    'tool1': {'TP': 2, 'FP': 1, 'TN': 4, 'FN': 1, 'FAIL_R': 1, 'FAIL_S': 0, 'UNK': 0},
                    'tool2': {'TP': 0, 'FP': 1, 'TN': 0, 'FN': 0, 'FAIL_R': 0, 'FAIL_S': 0, 'UNK': 1},
                },
                'drug3': {
                    'tool1': {'TP': 1, 'FP': 1, 'TN': 0, 'FN': 1, 'FAIL_R': 1, 'FAIL_S': 0, 'UNK': 0},
                    'tool2': {'TP': 1, 'FP': 0, 'TN': 1, 'FN': 0, 'FAIL_R': 0, 'FAIL_S': 0, 'UNK': 1},
                },
            },
        }

        expect_all = {
            'drug1': {
                'tool1': {'TP': 2, 'FP': 0, 'TN': 0, 'FN': 1, 'FAIL_R': 0, 'FAIL_S': 0, 'UNK': 2},
                'tool2': {'TP': 1, 'FP': 1, 'TN': 0, 'FN': 0, 'FAIL_R': 1, 'FAIL_S': 0, 'UNK': 3},
            },
            'drug2': {
                'tool1': {'TP': 3, 'FP': 2, 'TN': 6, 'FN': 4, 'FAIL_R': 2, 'FAIL_S': 0, 'UNK': 0},
                'tool2': {'TP': 1, 'FP': 1, 'TN': 0, 'FN': 1, 'FAIL_R': 1, 'FAIL_S': 0, 'UNK': 1},
            },
            'drug3': {
                'tool1': {'TP': 1, 'FP': 1, 'TN': 0, 'FN': 1, 'FAIL_R': 1, 'FAIL_S': 0, 'UNK': 0},
                'tool2': {'TP': 1, 'FP': 0, 'TN': 1, 'FN': 0, 'FAIL_R': 0, 'FAIL_S': 0, 'UNK': 1},
            },
        }
        expect_tools_counts = copy.copy(tools_counts)
        expect_tools_counts['all'] = expect_all
        performance_measurer.PerformanceMeasurer.add_all_counts_to_tools_counts(tools_counts)
        self.assertEqual(expect_tools_counts, tools_counts)


    def test_add_all_variants_to_variant_counts(self):
        '''test add_all_variants_to_variant_counts'''
        variant_counts = {
            'mykrobe': {
                'drug1': {
                    'tool1': {'var1': {'TP': 1, 'FP': 0}, 'var2': {'TP': 1, 'FP': 0}},
                    'tool2': {'var3': {'TP': 1, 'FP': 0}},
                },
                'drug2': {
                    'tool1': {'var4': {'TP': 1, 'FP': 0}},
                    'tool2': {'var5': {'TP': 0, 'FP': 1}},
                },
            },
            '10k': {
                'drug2': {
                    'tool1': {'var4': {'TP': 0, 'FP': 1}},
                    'tool2': {},
                },
                'drug3': {
                    'tool1': {'var6': {'TP': 1, 'FP': 0}},
                    'tool2': {'var7': {'TP': 1, 'FP': 0}},
                },
            },
        }

        expect_all = {
            'drug1': {
                'tool1': {'var1': {'TP': 1, 'FP': 0}, 'var2': {'TP': 1, 'FP': 0}},
                'tool2': {'var3': {'TP': 1, 'FP': 0}},
            },
            'drug2': {
                'tool1': {'var4': {'TP': 1, 'FP': 1}},
                'tool2': {'var5': {'TP': 0, 'FP': 1}},
            },
            'drug3': {
                'tool1': {'var6': {'TP': 1, 'FP': 0}},
                'tool2': {'var7': {'TP': 1, 'FP': 0}},
            },
        }

        expect_variant_counts = copy.copy(variant_counts)
        expect_variant_counts['all'] = expect_all
        performance_measurer.PerformanceMeasurer.add_all_variants_to_variant_counts(variant_counts)
        self.assertEqual(expect_variant_counts, variant_counts)


    def test_write_performance_stats_file(self):
        '''test write_performance_stats_file'''
        tool_counts = {
            'mykrobe': {
                'drug1': {
                    'tool1': {'TP': 9, 'FP': 1, 'TN': 10, 'FN': 2, 'FAIL_R': 1, 'FAIL_S': 0, 'UNK': 1},
                },
                'drug2': {
                    'tool2': {'TP': 10, 'FP': 0, 'TN': 3, 'FN': 0, 'FAIL_R': 1, 'FAIL_S': 0, 'UNK': 0},
                },
            },
            '10k': {
                'drug3': {
                    'tool1': {'TP': 3, 'FP': 3, 'TN': 1, 'FN': 1, 'FAIL_R': 0, 'FAIL_S': 0, 'UNK': 1},
                },
            },
        }

        expected_file = os.path.join(data_dir, 'write_performance_stats_file.tsv')
        tmp_file = 'tmp.write_performance_stats_file.tsv'
        performance_measurer.PerformanceMeasurer.write_performance_stats_file(tool_counts, tmp_file)
        self.assertTrue(filecmp.cmp(expected_file, tmp_file, shallow=False))
        os.unlink(tmp_file)

    def test_write_variant_counts_file_for_one_tool(self):
        '''test write_variant_counts_file_for_one_tool'''
        tmp_out = 'tmp.write_variant_counts_file_for_one_tool.tsv'
        variant_counts = {
            'mykrobe': {
                'drug1': {
                    'tool1': {'var1': {'TP': 1, 'FP': 0}, 'var2': {'TP': 1, 'FP': 0}},
                    'tool2': {'var3': {'TP': 1, 'FP': 0}},
                },
                'drug2': {
                    'tool1': {'var4': {'TP': 1, 'FP': 0}},
                    'tool2': {'var5': {'TP': 0, 'FP': 1}},
                },
            },
            '10k': {
                'drug2': {
                    'tool1': {'var4': {'TP': 0, 'FP': 1}},
                    'tool2': {},
                },
                'drug3': {
                    'tool1': {'var6': {'TP': 1, 'FP': 0}},
                    'tool2': {'var7': {'TP': 1, 'FP': 0}},
                },
            },
        }

        performance_measurer.PerformanceMeasurer.add_all_variants_to_variant_counts(variant_counts)
        performance_measurer.PerformanceMeasurer.write_variant_counts_file_for_one_tool(variant_counts, 'tool1', tmp_out)
        expect_file = os.path.join(data_dir, 'write_variant_counts_file_for_one_tool.tool1.tsv')
        self.assertTrue(filecmp.cmp(expect_file, tmp_out, shallow=False))
        performance_measurer.PerformanceMeasurer.write_variant_counts_file_for_one_tool(variant_counts, 'tool2', tmp_out)
        expect_file = os.path.join(data_dir, 'write_variant_counts_file_for_one_tool.tool2.tsv')
        self.assertTrue(filecmp.cmp(expect_file, tmp_out, shallow=False))
        os.unlink(tmp_out)



    def test_write_all_variant_counts_files(self):
        '''test write_all_variant_counts_files'''
        variant_counts = {
            'mykrobe': {
                'drug1': {
                    'tool1': {'var1': {'TP': 1, 'FP': 0}, 'var2': {'TP': 1, 'FP': 0}},
                    'tool2': {'var3': {'TP': 1, 'FP': 0}},
                },
                'drug2': {
                    'tool1': {'var4': {'TP': 1, 'FP': 0}},
                    'tool2': {'var5': {'TP': 0, 'FP': 1}},
                },
            },
            '10k': {
                'drug2': {
                    'tool1': {'var4': {'TP': 0, 'FP': 1}},
                    'tool2': {},
                },
                'drug3': {
                    'tool1': {'var6': {'TP': 1, 'FP': 0}},
                    'tool2': {'var7': {'TP': 1, 'FP': 0}},
                },
            },
        }
        tmp_prefix = 'tmp.write_all_variant_counts_files'
        performance_measurer.PerformanceMeasurer.add_all_variants_to_variant_counts(variant_counts)
        performance_measurer.PerformanceMeasurer.write_all_variant_counts_files(variant_counts, tmp_prefix)
        for tool in 'tool1', 'tool2':
            got_file = f'{tmp_prefix}.{tool}.tsv'
            self.assertTrue(os.path.exists(got_file))
            expect_file = os.path.join(data_dir, f'write_all_variant_counts_files.{tool}.tsv')
            self.assertTrue(filecmp.cmp(expect_file, got_file, shallow=False))
            os.unlink(got_file)


    def test_write_conf_file(self):
        '''test write_conf_file'''
        conf_counts = {
            'mykrobe': {
                'drug1': {
                    'tool1': {'TP': [(42, 0, 10, 50), (43, 1, 12, 50)], 'FP': [(1, 0, 1, 50), (4, 1, 2, 50), (3, 1, 3, 50)], 'TN': [(100, 1, 50, 50), (101, 2, 55, 50)], 'FN': [(6, 2, 3, 50)]},
                    'tool2': {'TP': [(44, 1, 20, 50)], 'FP': [], 'TN': [], 'FN': []},
                },
            },
            '10k': {
                'drug1': {
                    'tool1': {'TP': [(11, 1, 5, 50)], 'FP': [(8, 0, 4, 50)], 'TN': [(1, 0, 1, 50), (50, 0, 60, 50)], 'FN': [(4, 0, 5, 50)]},
                },
                'drug2': {'tool2': {'TP': [], 'FP': [(50, 10, 1000, 500)], 'TN': [], 'FN': []}},
            },
        }

        tmp_file = 'tmp.plots.write_conf_file.tsv'
        expected_file = os.path.join(data_dir, 'write_conf_file.tsv')
        performance_measurer.PerformanceMeasurer.write_conf_file(conf_counts, tmp_file)
        self.assertTrue(filecmp.cmp(expected_file, tmp_file, shallow=False))
        os.unlink(tmp_file)


    def test_write_regimen_counts_file(self):
        '''test write_regimen_counts_file'''
        regimen_counts = {
            'mykrobe': {
                'tool1': {(1, 1): 20, (2,3): 1, (None, 1): 1, (4, None): 10, (None, None): 6},
                'tool2': {(None, None): 1, (10, None): 1},
            },
            '10k': {
                'tool1': {(3, 3): 2},
                'tool2': {(2, 2): 1, (10, 10): 11},
            },
        }

        tmp_file = 'tmp.write_regimen_counts_file.tsv'
        expected_file = os.path.join(data_dir, 'write_regimen_counts_file.tsv')
        performance_measurer.PerformanceMeasurer.write_regimen_counts_file(regimen_counts, tmp_file)
        self.assertTrue(filecmp.cmp(expected_file, tmp_file, shallow=False))
        os.unlink(tmp_file)


    def test_run_tb(self):
        '''test run on tb data'''
        infile = os.path.join(data_dir, 'run.tb.in.json')
        outprefix = 'tmp.performance_measurer.tb.run'
        p = performance_measurer.PerformanceMeasurer(infile, 'tb')
        p.run(outprefix)
        expected_file = os.path.join(data_dir, 'run.tb.out.accuracy_stats.tsv')
        self.assertTrue(filecmp.cmp(expected_file, outprefix + '.accuracy_stats.tsv'))
        os.unlink(outprefix + '.accuracy_stats.tsv')
        expected_file = os.path.join(data_dir, 'run.tb.out.conf.tsv')
        self.assertTrue(filecmp.cmp(expected_file, outprefix + '.conf.tsv'))
        os.unlink(outprefix + '.conf.tsv')
        expected_file = os.path.join(data_dir, 'run.tb.out.regimen_counts.tsv')
        self.assertTrue(filecmp.cmp(expected_file, outprefix + '.regimen_counts.tsv'))
        os.unlink(outprefix + '.regimen_counts.tsv')
        for tool in 'tool1', 'tool2':
            got_file = f'{outprefix}.variant_counts.{tool}.tsv'
            self.assertTrue(os.path.exists(got_file))
            expect_file = os.path.join(data_dir, f'run.tb.out.variant_counts.{tool}.tsv')
            self.assertTrue(filecmp.cmp(expect_file, got_file, shallow=False))
            os.unlink(got_file)


    def test_run_staph(self):
        '''test run on staph data'''
        infile = os.path.join(data_dir, 'run.staph.in.json')
        outprefix = 'tmp.performance_measurer.staph.run'
        p = performance_measurer.PerformanceMeasurer(infile, 'staph')
        p.run(outprefix)
        expected_file = os.path.join(data_dir, 'run.staph.out.accuracy_stats.tsv')
        self.assertTrue(filecmp.cmp(expected_file, outprefix + '.accuracy_stats.tsv'))
        os.unlink(outprefix + '.accuracy_stats.tsv')
        expected_file = os.path.join(data_dir, 'run.staph.out.conf.tsv')
        self.assertTrue(filecmp.cmp(expected_file, outprefix + '.conf.tsv'))
        os.unlink(outprefix + '.conf.tsv')
        for tool in 'tool1', 'tool2':
            got_file = f'{outprefix}.variant_counts.{tool}.tsv'
            self.assertTrue(os.path.exists(got_file))
            expect_file = os.path.join(data_dir, f'run.staph.out.variant_counts.{tool}.tsv')
            self.assertTrue(filecmp.cmp(expect_file, got_file, shallow=False))
            os.unlink(got_file)


