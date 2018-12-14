import filecmp
import json
import os
import shutil
import unittest

from evalrescallers import mykrobe_pub_data

modules_dir = os.path.dirname(os.path.abspath(mykrobe_pub_data.__file__))
data_dir = os.path.join(modules_dir, 'tests', 'data', 'mykrobe_pub_data')


class TestMykrobePubData(unittest.TestCase):
    def test_load_nature_suppl_file_tb(self):
        '''test load_nature_suppl_file tb data'''
        infile = os.path.join(data_dir, 'load_nature_suppl_file.tb.txt')
        got_drugs, got_sample_to_res, got_sample_to_country = mykrobe_pub_data.load_nature_suppl_file(infile, 'tb')
        expect_drugs = {'Kanamycin', 'Streptomycin', 'Ciprofloxacin', 'Rifampicin', 'Amikacin', 'Ofloxacin', 'Isoniazid', 'Moxifloxacin', 'Capreomycin', 'Ethambutol', 'Quinolones'}
        expect_sample_to_res = {
                'SRR2100187': {'Rifampicin': 'S', 'Isoniazid': 'R', 'Ethambutol': 'S', 'Ciprofloxacin': 'S', 'Moxifloxacin': 'R', 'Quinolones': 'R'},
            'SRR2100184': {'Rifampicin': 'S', 'Isoniazid': 'S', 'Ethambutol': 'S', 'Ciprofloxacin': 'S', 'Moxifloxacin': 'S', 'Quinolones': 'S'},
            'SRR2100185': {'Rifampicin': 'S', 'Isoniazid': 'S', 'Ethambutol': 'S'},
        }
        expect_sample_to_country = {'SRR2100187': 'UK', 'SRR2100184': 'UK', 'SRR2100185': 'UK'}
        self.assertEqual(expect_drugs, got_drugs)
        self.assertEqual(expect_sample_to_res, got_sample_to_res)
        self.assertEqual(expect_sample_to_country, got_sample_to_country)


    def test_load_nature_suppl_file_staph(self):
        '''test load_nature_suppl_file staph data'''
        infile = os.path.join(data_dir, 'load_nature_suppl_file.staph.txt')
        got_drugs, got_sample_to_res, got_sample_to_country = mykrobe_pub_data.load_nature_suppl_file(infile, 'staph')
        expect_drugs = {'Gentamicin', 'Penicillin', 'Trimethoprim', 'Erythromycin', 'Methicillin', 'Ciprofloxacin', 'Rifampicin', 'Tetracycline', 'Mupirocin', 'FusidicAcid', 'Clindamycin', 'Vancomycin'}
        expect_sample_to_res = {
            'ERR410034': {'Gentamicin': 'S', 'Penicillin': 'R', 'Trimethoprim': 'S', 'Erythromycin': 'S', 'Methicillin': 'S', 'Ciprofloxacin': 'S', 'Rifampicin': 'S', 'Tetracycline': 'S', 'Mupirocin': 'S', 'FusidicAcid': 'S', 'Vancomycin': 'S'},
            'ERR410035': {'Gentamicin': 'S', 'Penicillin': 'S', 'Trimethoprim': 'S', 'Erythromycin': 'R', 'Methicillin': 'S', 'Ciprofloxacin': 'S', 'Rifampicin': 'S', 'Tetracycline': 'S', 'Mupirocin': 'S', 'FusidicAcid': 'S', 'Vancomycin': 'S'},
            'ERR410036': {'Gentamicin': 'S', 'Penicillin': 'S', 'Trimethoprim': 'S', 'Erythromycin': 'S', 'Methicillin': 'S', 'Ciprofloxacin': 'S', 'Rifampicin': 'S', 'Tetracycline': 'S', 'Mupirocin': 'S', 'FusidicAcid': 'S', 'Vancomycin': 'S'},
        }
        self.assertEqual(expect_drugs, got_drugs)
        self.assertEqual(expect_sample_to_res, got_sample_to_res)
        self.assertEqual({}, got_sample_to_country)


    def test_load_sample_to_country_file(self):
        '''test load_sample_to_country_file'''
        expect = {
            'id1': 'country1',
            'id2': 'country2',
        }
        infile = os.path.join(data_dir, 'load_sample_to_country_file.tsv')
        got = mykrobe_pub_data.load_sample_to_country_file(infile)
        self.assertEqual(expect, got)


    def test_load_all_nature_suppl_files_tb(self):
        '''test load_all_nature_suppl_files tb data'''
        input_dir = os.path.join(data_dir, 'load_all_nature_suppl_files')
        got_drugs, got_sample_to_res, got_sample_to_country = mykrobe_pub_data.load_all_nature_suppl_files('tb')
        expect_drugs = {'Kanamycin', 'Streptomycin', 'Ciprofloxacin', 'Rifampicin', 'Amikacin', 'Ofloxacin', 'Isoniazid', 'Moxifloxacin', 'Capreomycin', 'Ethambutol', 'Quinolones'}
        expect_sample_to_res = {}
        expect_sample_to_country = {}
        for i in '7', '8', '9', '10':
            _, data, new_countries = mykrobe_pub_data.load_nature_suppl_file(os.path.join(mykrobe_pub_data.publication_suppl_files_dir, f'ncomms10063-s{i}.txt'), 'tb')
            expect_sample_to_res.update(data)
            expect_sample_to_country.update(new_countries)

        self.assertEqual(expect_drugs, got_drugs)
        self.assertEqual(got_sample_to_res, expect_sample_to_res)
        self.assertEqual(expect_sample_to_country, got_sample_to_country)
        self.assertEqual(len(got_sample_to_country), len(got_sample_to_res))


    def test_load_all_nature_suppl_files_staph(self):
        '''test load_all_nature_suppl_files staph data'''
        input_dir = os.path.join(data_dir, 'load_all_nature_suppl_files')
        got_drugs, got_sample_to_res, got_sample_to_country = mykrobe_pub_data.load_all_nature_suppl_files('staph')
        expect_drugs = {'Gentamicin', 'Penicillin', 'Trimethoprim', 'Erythromycin', 'Methicillin', 'Ciprofloxacin', 'Rifampicin', 'Tetracycline', 'Mupirocin', 'FusidicAcid', 'Clindamycin', 'Vancomycin'}
        _, expect_sample_to_res, got_sample_to_country = mykrobe_pub_data.load_nature_suppl_file(os.path.join(mykrobe_pub_data.publication_suppl_files_dir, f'ncomms10063-s4.txt'), 'staph')
        self.assertEqual(expect_drugs, got_drugs)
        self.assertEqual(got_sample_to_res, expect_sample_to_res)
        self.assertEqual({}, got_sample_to_country)
