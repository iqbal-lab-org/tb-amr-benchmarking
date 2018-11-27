import csv
import os

import evalrescallers

# The samples from the sources below constitute the
# "test" dataset, to be kept back until the final evaluaiton.
# The others are the "validation" dataset.
test_sources = {
    ('Hamburg', 'Germany'),
    ('Birmingham', 'UK'),
    ('Leeds', 'UK'),
    ('Italy_MGITstudy', 'Italy'),
    ('Netherlands', 'Netherlands'),
}

eval_dir = os.path.abspath(os.path.dirname(evalrescallers.__file__))
data_dir = os.path.join(eval_dir, 'data')
sources_file = os.path.join(data_dir, '10k_validation.sample_sources.tsv')

def load_sample_to_res_file(infile):
    sample_to_res = {}
    added_quinolones = False
    quinolones = {'Ciprofloxacin', 'Moxifloxacin', 'Ofloxacin'}

    with open(infile) as f:
        tsv_reader = csv.DictReader(f, delimiter='\t')
        data = {}
        drugs = {x for x in tsv_reader.fieldnames if x not in ['ena_id', 'oxford_id']}

        for row in tsv_reader:
            assert row['ena_id'] not in data
            data[row['ena_id']] = {drug: row[drug] for drug in drugs}
            quinolone_res = [row.get(q, None) for q in quinolones]
            if 'R' in quinolone_res:
                data[row['ena_id']]['Quinolones'] = 'R'
                added_quinolones = True
            elif set(quinolone_res) == {'S'}:
                data[row['ena_id']]['Quinolones'] = 'S'
                added_quinolones = True

    if added_quinolones:
        drugs.add('Quinolones')

    return drugs, data


def load_sources_file(infile):
    data = {}

    with open(infile) as f:
        tsv_reader = csv.DictReader(f, delimiter='\t')
        for row in tsv_reader:
            assert row['ena_id'] not in data
            data[row['ena_id']] = (row['source'], row['country'])

    return data


def sources_file_to_country_counts(infile):
    counts = {}

    with open(infile) as f:
        tsv_reader = csv.DictReader(f, delimiter='\t')
        for row in tsv_reader:
            if row['country'] not in counts:
                counts[row['country']] = {'test': 0, 'validate': 0}

            if (row['source'], row['country']) in test_sources:
                counts[row['country']]['test'] += 1
            else:
                counts[row['country']]['validate'] += 1

    return counts


def load_all_data():
    drugs, pheno_data = load_sample_to_res_file(os.path.join(data_dir, '10k_validation.phenotype.tsv'))
    drugs2, predict_data = load_sample_to_res_file(os.path.join(data_dir, '10k_validation.prediction.tsv'))
    assert drugs == drugs2

    extra_drugs, extra_pheno_data = load_sample_to_res_file(os.path.join(data_dir, '10k_validation.extra_phenotypes.tsv'))
    drugs.update(extra_drugs)
    all_samples = set(pheno_data.keys()).union(set(extra_pheno_data.keys()))
    for sample in all_samples:
        d1 = pheno_data.get(sample, {})
        d2 = extra_pheno_data.get(sample, {})
        d1.update(d2)
        pheno_data[sample] = d1

    guid_to_source = load_sources_file(os.path.join(data_dir, '10k_validation.sample_sources.tsv'))
    pheno_data_validation = {}
    pheno_data_test = {}
    for sample, d in pheno_data.items():
        if guid_to_source.get(sample, None) in test_sources:
            pheno_data_test[sample] = d
        else:
            pheno_data_validation[sample] = d

    return drugs, pheno_data_validation, pheno_data_test, predict_data

