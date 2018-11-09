import os
import unittest

from evalrescallers import ten_k_validation_data

modules_dir = os.path.dirname(os.path.abspath(ten_k_validation_data.__file__))
data_dir = os.path.join(modules_dir, 'tests', 'data', 'ten_k_validation_data')



class TestTenKValidationData(unittest.TestCase):
    def test_load_sample_to_res_file(self):
        '''test load_sample_to_res_file'''
        expected_drugs = {'Isoniazid', 'Rifampicin', 'Ethambutol', 'Pyrazinamide'}
        expected_data = {
            'ena1': {'Isoniazid': 'n/a', 'Rifampicin': 'S', 'Ethambutol': 'R', 'Pyrazinamide': 'S'},
            'ena2': {'Isoniazid': 'S', 'Rifampicin': 'U', 'Ethambutol': 'S', 'Pyrazinamide': 'S'},
        }
        infile = os.path.join(data_dir, 'load_sample_to_res_file.tsv')
        got_drugs, got_data = ten_k_validation_data.load_sample_to_res_file(infile)
        self.assertEqual(expected_drugs, got_drugs)
        self.assertEqual(expected_data, got_data)


    def test_load_sources_file(self):
        '''test load_sources_file'''
        infile = os.path.join(data_dir, 'load_sources_file.tsv')
        expect = {
            'ena1': ('source1', 'country1'),
            'ena2': ('source1', 'country1'),
            'ena3': ('source1', 'country2'),
            'ena4': ('source2', 'country1'),
            'ena5': ('source2', 'country2'),
        }
        got = ten_k_validation_data.load_sources_file(infile)
        self.assertEqual(expect, got)


    def test_sources_file_to_country_counts(self):
        '''test sources_file_to_country_counts'''
        infile = os.path.join(data_dir, 'sources_file_to_country_counts.tsv')
        expect = {
                'Country1':  {'validate': 3, 'test': 0},
                'Country2':  {'validate': 1, 'test': 0},
                'Germany':  {'validate': 0, 'test': 1},
                'UK':  {'validate': 1, 'test': 2},
        }
        got = ten_k_validation_data.sources_file_to_country_counts(infile)
        self.assertEqual(expect, got)


    def test_load_all_data(self):
        '''test load_all_data'''
        expected_drugs = {'Isoniazid', 'Rifampicin', 'Ethambutol', 'Pyrazinamide', 'Amikacin', 'Capreomycin', 'Ciprofloxacin', 'Cycloserine', 'Ethionamide', 'Kanamycin', 'Linezolid', 'Moxifloxacin', 'Ofloxacin', 'PAS', 'Rifabutin', 'Streptomycin'}
        got_drugs, got_pheno_validation, got_pheno_test, got_predict = ten_k_validation_data.load_all_data()
        self.assertEqual(expected_drugs, got_drugs)
        _, expect_pheno = ten_k_validation_data.load_sample_to_res_file(os.path.join(ten_k_validation_data.data_dir, '10k_validation.phenotype.tsv'))
        _, expect_predict = ten_k_validation_data.load_sample_to_res_file(os.path.join(ten_k_validation_data.data_dir, '10k_validation.prediction.tsv'))
        _, expect_more_pheno = ten_k_validation_data.load_sample_to_res_file(os.path.join(ten_k_validation_data.data_dir, '10k_validation.extra_phenotypes.tsv'))

        expect_samples = set(expect_pheno.keys()).union(set(expect_more_pheno.keys()))
        got_samples = set(expect_pheno.keys())
        self.assertEqual(expect_samples, got_samples)

        for pheno_dict in got_pheno_validation, got_pheno_test:
            for sample in pheno_dict:
                for d in expect_pheno, expect_more_pheno:
                    if sample in d:
                        for k, v in d[sample].items():
                            self.assertEqual(v, pheno_dict[sample][k])

        self.assertEqual(expect_predict, got_predict)

