from collections import namedtuple

profile_drugs = {
    'Isoniazid': 'H',
    'Rifampicin': 'R',
    'Pyrazinamide': 'Z',
    'Ethambutol': 'E',
    'Kanamycin': 'Km',
    'Amikacin': 'Am',
    'Capreomycin': 'Cm',
    'Streptomycin': 'S',
    'Ofloxacin': 'Ofx',
    'Ciprofloxacin': 'Cfx',
    'Moxifloxacin': 'Mfx',
    'Bedaquiline': 'Bdq',
    'Linezolid': 'Lzd',
    'Clofazimide': 'Cfz',
    'Cycloserine': 'Cs',
    'Terizidone': 'Trd',
}

group_to_drug = {
    1: {
        'Rifampicin',
        'Rifabutin',
        'Rifapentine',
        'Isoniazid',
        'Ethambutol',
        'Pyrazinamide'
    },
    2: {'Streptomycin', 'Kanamycin', 'Amikacin', 'Capreomycin'},
    3: {'Levofloxacin', 'Moxifloxacin', 'Gatifloxacin'},
    4: {
        'Ethionamide',
        'Prothionamide',
        'Para-aminosalicylate',
        'Para-aminosalicylate-Sodium',
        'Cycloserine',
        'Terizidone'
    },
    5: {
        'Thioacetazone',
        'Clofazimide',
        'Linezolid',
        'Amox-Clavulanate',
        'Imipenem/Cilastatin ',
        'Meropenem',
        'High dose Isoniazid',
        'Delaminid',
        'Bedaquiline ',
    },
    'A': {
        'Levofloxacin',
        'Moxifloxacin',
        'Gatifloxacin',
    },
    'B': {
        'Streptomycin',
        'Kanamycin',
        'Amikacin',
        'Capreomycin',
    },
    'C': {
        'Ethionamide',
        'Prothionamide',
        'Cycloserine',
        'Terizidone',
        'Clofazimide',
        'Linezolid',
    },
    'D1': {
        'Ethambutol',
        'Pyrazinamide',
        'High dose Isoniazid'
    },
    'D2': {
        'Delaminid',
        'Bedaquiline',
    },
    'D3': {
        'Para-aminosalicylate',
        'Para-aminosalicylate-Sodium',
        'Amox-Clavulanate',
        'Imipenem/Cilastatin',
        'Meropenem',
    },
}



Regimen = namedtuple('Regimen', ['number', 'definition', 'mandatory', 'optional'])


regimens = {
    1: Regimen(
           1,
           'DS-TB',
           {'Isoniazid', 'Rifampicin', 'Pyrazinamide', 'Ethambutol'},
           None,
       ),
    2: Regimen(
           2,
           'Mono-H DR-TB',
           {'Rifampicin', 'Pyrazinamide', 'Ethambutol'},
           {('one_of', tuple(group_to_drug['A']))},
       ),
    3: Regimen(
           3,
           'Mono-H DR-TB',
           {'Rifampicin', 'Pyrazinamide', 'Ethambutol'},
           None,
       ),
    4: Regimen(
           4,
           'H-Z DR-TB',
           {
               'Rifampicin',
               'Ethambutol',
               ('one_of', tuple(group_to_drug['A'])),
           },
           None,
       ),
    5: Regimen(
           5,
           'H-E DR-TB',
           {
               'Rifampicin',
               'Pyrazinamide',
               ('one_of', tuple(group_to_drug['A'])),
           },
           None,
       ),
    6: Regimen(
           6,
           'H-Z-E DR-TB',
           {
                'Rifampicin',
                'Ethionamide',
                ('one_of', ('Moxifloxacin', 'Levofloxacin', 'Gatifloxacin')),
                ('one_of', ('Kanamycin', 'Amikacin', 'Capreomycin')),
           },
           None,
       ),
    7: Regimen(
           7,
           'H-Z-E DR-TB',
           {
               'Rifampicin',
               'Ethionamide',
               'Streptomycin',
                ('one_of', ('Moxifloxacin', 'Levofloxacin', 'Gatifloxacin')),
           },
           None,
       ),
    8: Regimen(
           8,
           'Mono-Z DR-TB',
           {'Isoniazid', 'Rifampicin', 'Ethambutol'},
           None,
       ),
    9: Regimen(
           9,
           'Mono-E DR-TB',
           {'Isoniazid', 'Rifampicin', 'Pyrazinamide'},
           None,
       ),
    10: Regimen(
           10,
           'RR-TB',
           {
                'Isoniazid',
                'Bedaquiline',
                'Linezolid',
                ('one_of', ('Moxifloxacin', 'Levofloxacin')),
                ('one_of', ('Clofazimide', 'Cycloserine', 'Terizidone')),
           },
           None,
        ),
    11: Regimen(
           11,
           'MDR-TB',
           {
                'Bedaquiline',
                'Linezolid',
                ('one_of', ('Moxifloxacin', 'Levofloxacin')),
                ('one_of', ('Clofazimide', 'Cycloserine', 'Terizidone')),
           },
           None,
        ),
    12: Regimen(
            12,
            'XDR-TB',
            {
                ('all', tuple(group_to_drug[1])),
                ('one_of', ('Amikacin', 'Streptomycin')),
                ('one_of', ('Levofloxacin', 'Moxifloxacin', 'Gatifloxacin')),
                ('all', tuple(group_to_drug[4])),
                ('at_least_two', tuple(group_to_drug[5].difference(group_to_drug['D2']))),
                'High dose Isoniazid',
            },
            None,
        ),
}


class DstProfile:
    def __init__(self, drug_to_pheno):
        self.phenos = {x: drug_to_pheno.get(x, None) for x in profile_drugs}
        allowed_values = {'R', 'S', None}
        assert allowed_values.issuperset(set(self.phenos.values()))
        self._set_regimen()


    def _set_regimen(self):
        first_line_tuple = (
            self.phenos['Isoniazid'],
            self.phenos['Rifampicin'],
            self.phenos['Pyrazinamide'],
            self.phenos['Ethambutol'],
        )

        if first_line_tuple == ('S', 'S', 'S', 'S'):
            self.regimen = regimens[1]
        elif first_line_tuple == ('R', 'S', 'S', 'S') and self.phenos['Moxifloxacin'] == 'R':
            self.regimen = regimens[3]
        elif first_line_tuple == ('R', 'S', 'S', 'S'):
            self.regimen = regimens[2]
        elif first_line_tuple == ('R', 'S', 'R', 'S'):
            self.regimen = regimens[4]
        elif first_line_tuple == ('R', 'S', 'S', 'R'):
            self.regimen = regimens[5]
        elif first_line_tuple == ('R', 'S', 'R', 'R') and (self.phenos['Kanamycin'], self.phenos['Amikacin'], self.phenos['Capreomycin'], self.phenos['Streptomycin']) == ('R', 'R', 'R', 'S'):
            self.regimen = regimens[7]
        elif first_line_tuple == ('R', 'S', 'R', 'R'):
            self.regimen = regimens[6]
        elif first_line_tuple == ('S', 'S', 'R', 'S'):
            self.regimen = regimens[8]
        elif first_line_tuple == ('S', 'S', 'S', 'R'):
            self.regimen = regimens[9]
        elif (self.phenos['Isoniazid'], self.phenos['Rifampicin'], self.phenos['Moxifloxacin']) == ('R', 'R', 'R'):
            self.regimen = regimens[12]
        elif self.phenos['Isoniazid'] == 'R' and self.phenos['Rifampicin'] == 'R':
            self.regimen = regimens[11]
        elif self.phenos['Rifampicin'] == 'R':
            self.regimen = regimens[10]
        else:
            self.regimen = None


    def has_same_regimen(self, other):
        return self.regimen != None and other.regimen != None and self.regimen.number == other.regimen.number

