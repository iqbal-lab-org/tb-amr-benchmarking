import os
import unittest

from evalrescallers import who_treatment

modules_dir = os.path.dirname(os.path.abspath(who_treatment.__file__))
data_dir = os.path.join(modules_dir, 'tests', 'data', 'who_treatment')


class TestWhoTreatment(unittest.TestCase):
    def test_dst_profile_gets_correct_regimen(self):
        '''test DstProfile gets correct regimen'''
        phenos = {
            'Isoniazid': 'S',
            'Rifampicin': 'S',
            'Pyrazinamide': 'S',
            'Ethambutol': 'S',
        }

        profile = who_treatment.DstProfile(phenos)
        self.assertEqual(1, profile.regimen.number)

        phenos['Isoniazid'] = 'R'
        profile = who_treatment.DstProfile(phenos)
        self.assertEqual(3, profile.regimen.number)

        phenos['Moxifloxacin'] = 'S'
        profile = who_treatment.DstProfile(phenos)
        self.assertEqual(2, profile.regimen.number)

        phenos['Moxifloxacin'] = 'R'
        profile = who_treatment.DstProfile(phenos)
        self.assertEqual(3, profile.regimen.number)

        phenos = {
            'Isoniazid': 'R',
            'Rifampicin': 'S',
            'Pyrazinamide': 'R',
            'Ethambutol': 'S',
        }
        profile = who_treatment.DstProfile(phenos)
        self.assertEqual(4, profile.regimen.number)

        phenos = {
            'Isoniazid': 'R',
            'Rifampicin': 'S',
            'Pyrazinamide': 'S',
            'Ethambutol': 'R',
        }
        profile = who_treatment.DstProfile(phenos)
        self.assertEqual(5, profile.regimen.number)

        phenos = {
            'Isoniazid': 'R',
            'Rifampicin': 'S',
            'Pyrazinamide': 'R',
            'Ethambutol': 'R',
        }
        profile = who_treatment.DstProfile(phenos)
        self.assertEqual(6, profile.regimen.number)
        phenos['Kanamycin'] = 'R'
        phenos['Amikacin'] = 'R'
        phenos['Capreomycin'] = 'R'
        phenos['Streptomycin'] = 'S'
        profile = who_treatment.DstProfile(phenos)
        self.assertEqual(7, profile.regimen.number)

        phenos = {
            'Isoniazid': 'S',
            'Rifampicin': 'S',
            'Pyrazinamide': 'R',
            'Ethambutol': 'S',
        }
        profile = who_treatment.DstProfile(phenos)
        self.assertEqual(8, profile.regimen.number)

        phenos = {
            'Isoniazid': 'S',
            'Rifampicin': 'S',
            'Pyrazinamide': 'S',
            'Ethambutol': 'R',
        }
        profile = who_treatment.DstProfile(phenos)
        self.assertEqual(9, profile.regimen.number)

        phenos = {
            'Rifampicin': 'R',
        }
        profile = who_treatment.DstProfile(phenos)
        self.assertEqual(10, profile.regimen.number)

        phenos = {
            'Rifampicin': 'R',
            'Kanamycin': 'S',
            'Moxifloxacin': 'S',
        }
        profile = who_treatment.DstProfile(phenos)
        self.assertEqual(11, profile.regimen.number)

        phenos = {
            'Isoniazid': 'R',
            'Rifampicin': 'R',
        }
        profile = who_treatment.DstProfile(phenos)
        self.assertEqual(10, profile.regimen.number)

        phenos = {
            'Isoniazid': 'R',
            'Rifampicin': 'R',
            'Kanamycin': 'S',
            'Moxifloxacin': 'S',
        }
        profile = who_treatment.DstProfile(phenos)
        self.assertEqual(11, profile.regimen.number)

        phenos = {
            'Isoniazid': 'R',
            'Rifampicin': 'R',
            'Moxifloxacin': 'R',
        }
        profile = who_treatment.DstProfile(phenos)
        self.assertEqual(12, profile.regimen.number)


    def test_has_same_regimen(self):
        '''test has_same_regimen'''
        phenos = {
            'Isoniazid': None,
            'Rifampicin': 'S',
            'Pyrazinamide': 'S',
            'Ethambutol': 'S',
        }

        dst1 = who_treatment.DstProfile(phenos)
        dst2 = who_treatment.DstProfile(phenos)
        self.assertFalse(dst1.has_same_regimen(dst2))

        phenos['Isoniazid'] = 'S'
        dst1 = who_treatment.DstProfile(phenos)
        self.assertFalse(dst1.has_same_regimen(dst2))

        dst2 = who_treatment.DstProfile(phenos)
        self.assertTrue(dst1.has_same_regimen(dst2))

        phenos['Isoniazid'] = 'R'
        dst1 = who_treatment.DstProfile(phenos)
        dst2 = who_treatment.DstProfile(phenos)
        self.assertTrue(dst1.has_same_regimen(dst2))

