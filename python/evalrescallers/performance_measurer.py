import copy
import json
import logging

from evalrescallers import mykrobe_pub_data, stats, ten_k_validation_data, who_treatment

class PerformanceMeasurer:
    def __init__(self, summary_json_file, species, r_means_resistant=True):
        self.summary_json_file = summary_json_file
        assert species in ('tb', 'staph')
        self.species = species
        self.r_means_resistant = r_means_resistant
        mykrobe_drugs, mykrobe_pheno, mykrobe_countries = mykrobe_pub_data.load_all_nature_suppl_files(self.species)
        self.truth_pheno = {}
        self.drugs = {'mykrobe': mykrobe_drugs}
        datasets = {'mykrobe': mykrobe_pheno}

        if species == 'tb':
            ten_k_drugs, ten_k_pheno_validate, ten_k_pheno_test, self.ten_k_predict = ten_k_validation_data.load_all_data()
            self.drugs['10k_test'] = ten_k_drugs
            self.drugs['10k_validate'] = ten_k_drugs
            datasets['10k_test'] = ten_k_pheno_test
            datasets['10k_validate'] = ten_k_pheno_validate
        else:
            self.ten_k_predict = None


        for dataset, d in datasets.items():
            for sample in d:
                assert sample not in self.truth_pheno
                self.truth_pheno[sample] = {'dataset': dataset, 'pheno': d[sample]}


    @classmethod
    def summary_json_to_metrics_and_var_call_counts(cls, json_file, truth_pheno, drugs, species, lower_case_r_means_resistant=True, ten_k_predict=None):
        if ten_k_predict is None:
            ten_k_predict = {}

        with open(json_file) as f:
            json_data = json.load(f)

        tools_counts = {}
        variant_counts = {}
        conf_and_depths = {}
        regimen_counts = {}

        for dataset in drugs:
            tools_counts[dataset] = {x: {} for x in drugs[dataset]}
            variant_counts[dataset] = {x: {} for x in drugs[dataset]}
            conf_and_depths[dataset] = {x: {} for x in drugs[dataset]}

        for sample in json_data:
            if sample not in truth_pheno:
                logging.warning(f'Sample "{sample}" not found in mykrobe or 10k datasets')
                continue

            dataset = truth_pheno[sample]['dataset']
            # There are "n/a"s as values for the known phenos. We want
            # to use None instead
            sample_truth_pheno = {k: v if v in {"R", "S"} else None for k, v in truth_pheno[sample]['pheno'].items()}
            sample_dst = who_treatment.DstProfile(sample_truth_pheno)
            if dataset.startswith('10k') and sample in ten_k_predict and sample in json_data:
                json_data[sample]['10k_predict'] = {
                    'resistance_calls': {drug: [[ten_k_predict[sample][drug], "NA", "NA"]] for drug in ten_k_predict[sample]},
                    'Success': True,
                }


            for tool in json_data[sample]:
                tool_pheno = {}

                for drug in drugs[dataset]:
                    try:
                        pheno = sample_truth_pheno[drug]
                    except:
                        continue

                    if pheno not in {'R', 'S'}:
                        continue

                    if tool not in tools_counts[dataset][drug]:
                        tools_counts[dataset][drug][tool] = {x: 0 for x in ['TP', 'FP', 'TN', 'FN', 'UNK', 'FAIL_R', 'FAIL_S']}
                        variant_counts[dataset][drug][tool] = {}
                        conf_and_depths[dataset][drug][tool] = {x: [] for x in ['TP', 'FP', 'TN', 'FN']}

                    if json_data[sample][tool]['Success']:
                        conf_depths_tuples = []
                        if drug in json_data[sample][tool]['resistance_calls']:
                            variants = [x[1] + '.' + x[2] for x in json_data[sample][tool]['resistance_calls'][drug] if x[1] is not None and x[2] is not None]
                            call = json_data[sample][tool]['resistance_calls'][drug][0][0]
                            for i in range(len(json_data[sample][tool]['resistance_calls'][drug])):
                                try:
                                    d = json_data[sample][tool]['resistance_calls'][drug][i][3]
                                    conf_depths_tuples.append((d['conf'], d['ref_depth'], d['alt_depth'], d['expected_depth']))
                                except:
                                    pass
                        else:
                            call = 'S'

                        if call == 'r':
                            if lower_case_r_means_resistant:
                                call = 'R'
                            else:
                                call = 'S'


                        tool_pheno[drug] = call if call in ['R', 'S'] else None



                        if call == 'R':
                            call = 'TP' if pheno == 'R' else 'FP'
                            variants.sort()
                            variant = ';'.join(variants)
                            if variant not in variant_counts[dataset][drug][tool]:
                                variant_counts[dataset][drug][tool][variant] = {'TP': 0, 'FP': 0}
                            variant_counts[dataset][drug][tool][variant][call] += 1
                        elif call == 'S':
                            call = 'TN' if pheno == 'S' else 'FN'
                        else:
                            call = 'UNK'

                        for t in conf_depths_tuples:
                            conf_and_depths[dataset][drug][tool][call].append(t)
                    else:
                        call = f'FAIL_{pheno}'

                    tools_counts[dataset][drug][tool][call] += 1

                if species == 'tb':
                    tool_dst = who_treatment.DstProfile(tool_pheno)
                    if dataset not in regimen_counts:
                        regimen_counts[dataset] = {}
                    if tool not in regimen_counts[dataset]:
                        regimen_counts[dataset][tool] = {}

                    key1 = sample_dst.regimen.number if sample_dst.regimen is not None else None
                    key2 = tool_dst.regimen.number if tool_dst.regimen is not None else None
                    key = key1, key2
                    regimen_counts[dataset][tool][key] = regimen_counts[dataset][tool].get(key, 0) + 1


        # we're only really conf from MYrkobe, so delete
        # all the entries in conf_counts that have no data
        for dataset in conf_and_depths:
            for drug, d in conf_and_depths[dataset].items():
                conf_and_depths[dataset][drug] = {x:d[x] for x in d if sum([len(z) for z in d[x].values()]) > 0}

        return tools_counts, variant_counts, conf_and_depths, regimen_counts


    @classmethod
    def add_all_counts_to_tools_counts(cls, tools_counts):
        all_counts = {}
        for dataset in tools_counts:
            for drug in tools_counts[dataset]:
                if drug not in all_counts:
                    all_counts[drug] = {}

                for tool in tools_counts[dataset][drug]:
                    if tool not in all_counts[drug]:
                        all_counts[drug][tool] = copy.copy(tools_counts[dataset][drug][tool])
                    else:
                        for k, v in tools_counts[dataset][drug][tool].items():
                            all_counts[drug][tool][k] += v

        tools_counts['all'] = all_counts


    @classmethod
    def add_all_variants_to_variant_counts(cls, variant_counts):
        all_counts = {}
        for dataset in variant_counts:
            for drug in variant_counts[dataset]:
                if drug not in all_counts:
                    all_counts[drug] = {}

                for tool in variant_counts[dataset][drug]:
                    if tool not in all_counts[drug]:
                        all_counts[drug][tool] = copy.copy(variant_counts[dataset][drug][tool])
                    else:
                        for variant, counts in variant_counts[dataset][drug][tool].items():
                            if variant not in all_counts[drug][tool]:
                                all_counts[drug][tool][variant] = copy.copy(counts)
                            else:
                                for key, count in counts.items():
                                    all_counts[drug][tool][variant][key] += count

        variant_counts['all'] = all_counts


    @classmethod
    def write_performance_stats_file(cls, tools_counts, outfile):
        all_counts = {}

        with open(outfile, 'w') as f:
            print('Dataset', 'Drug', 'Tool', 'TP', 'TN', 'FP', 'FN', 'FAIL_R', 'FAIL_S', 'UNK',
                'Sensitivity', 'Sensitivity_conf_low', 'Sensitivity_conf_high',
                'Specificity', 'Specificity_conf_low', 'Specificity_conf_high',
                'PPV', 'PPV_conf_low', 'PPV_conf_high',
                'NPV', 'NPV_conf_low', 'NPV_conf_high',
                'FNR', 'FNR_conf_low', 'FNR_conf_high',
                'FPR', 'FPR_conf_low', 'FPR_conf_high',
                sep='\t', file=f)
            for dataset in sorted(tools_counts):
                for drug in sorted(tools_counts[dataset]):
                    for tool, d in sorted(tools_counts[dataset][drug].items()):
                        if d['TP'] + d['FN'] > 0:
                            sensitivity = round(100 * d['TP'] / (d['TP'] + d['FN']), 2)
                        else:
                            sensitivity = 'NA'
                        sensitivity_conf_low, sensitivity_conf_high = stats.binconf(d['TP'], d['FN'])

                        if d['TN'] + d['FP'] > 0:
                            specificity = round(100 * d['TN'] / (d['TN'] + d['FP']), 2)
                        else:
                            specificity = 'NA'
                        specificity_conf_low, specificity_conf_high = stats.binconf(d['TN'], d['FP'])

                        if d['TP'] + d['FP'] > 0:
                            ppv = round(100 * d['TP'] / (d['TP'] + d['FP']), 2)
                        else:
                            ppv = 'NA'
                        ppv_conf_low, ppv_conf_high = stats.binconf(d['TP'], d['FP'])

                        if d['TN'] + d['FN'] > 0:
                            npv = round(100 * d['TN'] / ( d['TN'] + d['FN']), 2)
                        else:
                            npv = 'NA'
                        npv_conf_low, npv_conf_high = stats.binconf(d['TN'], d['FN'])

                        if d['FN'] + d['TP'] > 0:
                            fnr = round(100 * d['FN'] / (d['FN'] + d['TP']), 2)
                        else:
                            fnr = 'NA'
                        fnr_conf_low, fnr_conf_high = stats.binconf(d['FN'], d['TP'])

                        if d['FP'] + d['TN'] > 0:
                            fpr = round(100 * d['FP'] / (d['FP'] + d['TN']), 2)
                        else:
                            fpr = 'NA'
                        fpr_conf_low, fpr_conf_high = stats.binconf(d['FP'], d['TN'])


                        print(dataset, drug, tool, d['TP'], d['TN'], d['FP'], d['FN'], d['FAIL_R'], d['FAIL_S'], d['UNK'],
                            sensitivity, sensitivity_conf_low, sensitivity_conf_high,
                            specificity, specificity_conf_low, specificity_conf_high,
                            ppv, ppv_conf_low, ppv_conf_high,
                            npv, npv_conf_low, npv_conf_high,
                            fnr, fnr_conf_low, fnr_conf_high,
                            fpr, fpr_conf_low, fpr_conf_high,
                            sep='\t', file=f)


    @classmethod
    def write_variant_counts_file_for_one_tool(cls, variant_counts, tool, outfile):
        lines = []
        for dataset in variant_counts:
            for drug in variant_counts[dataset]:
                if tool in variant_counts[dataset][drug]:
                    for variant, counts in variant_counts[dataset][drug][tool].items():
                        ppv = round(100 * counts['TP'] / (counts['TP'] + counts['FP']), 2)
                        lines.append((dataset, drug, ppv, counts['TP'], counts['FP'], variant))

        lines.sort()

        with open(outfile, 'w') as f:
            print('Dataset', 'Drug', 'PPV', 'TP', 'FP', 'Variant', sep='\t', file=f)
            for line in lines:
                print(*line, sep='\t', file=f)


    @classmethod
    def write_all_variant_counts_files(cls, variant_counts, outprefix):
        tools = set()
        for dataset in variant_counts:
            for drug in variant_counts[dataset]:
                tools.update(set(variant_counts[dataset][drug].keys()))

        for tool in tools:
            if tool == '10k_predict':
                continue

            outfile = outprefix + f'.{tool}.tsv'
            PerformanceMeasurer.write_variant_counts_file_for_one_tool(variant_counts, tool, outfile)


    @classmethod
    def write_conf_file(cls, conf_counts, outfile):
        with open(outfile, 'w') as f:
            print('Dataset', 'Tool', 'Drug', 'Call', 'Conf', 'Ref_depth', 'Alt_depth', 'Expected_depth', sep='\t', file=f)
            for dataset in sorted(conf_counts):
                for drug in sorted(conf_counts[dataset]):
                    for tool, conf_dict in sorted(conf_counts[dataset][drug].items()):
                        for call, conf_list in sorted(conf_dict.items()):
                            conf_list.sort()
                            for c in conf_list:
                                print(dataset, tool, drug, call, *c, sep='\t', file=f)


    @classmethod
    def write_regimen_counts_file(cls, regimen_counts, outfile):
        with open(outfile, 'w') as f:
            print('Dataset', 'Tool', 'Truth_regimen', 'Called_regimen', 'Count', sep='\t', file=f)
            for dataset in sorted(regimen_counts):
                for tool in sorted(regimen_counts[dataset]):
                    for key in sorted(regimen_counts[dataset][tool], key=lambda x: (-1 if x[0] is None else x[0], -1 if x[1] is None else x[1])):
                        print(dataset, tool, *key, regimen_counts[dataset][tool][key], sep='\t', file=f)


    def run(self, outprefix):
        tools_counts, variant_counts, conf_counts, regimen_counts = PerformanceMeasurer.summary_json_to_metrics_and_var_call_counts(self.summary_json_file, self.truth_pheno, self.drugs, self.species, ten_k_predict=self.ten_k_predict, lower_case_r_means_resistant=self.r_means_resistant)
        # For TB we have the mykrobe paper data set, plus the 10k set.
        # This means we need to do the calculations of summing the
        # two data sets. But not relevant for staph, where there is only
        # the mykrobe data set.
        if self.species == 'tb':
            PerformanceMeasurer.add_all_counts_to_tools_counts(tools_counts)
            PerformanceMeasurer.add_all_variants_to_variant_counts(variant_counts)
            PerformanceMeasurer.write_regimen_counts_file(regimen_counts, outprefix + '.regimen_counts.tsv')
        PerformanceMeasurer.write_performance_stats_file(tools_counts, outprefix + '.accuracy_stats.tsv')
        PerformanceMeasurer.write_all_variant_counts_files(variant_counts, outprefix + '.variant_counts')
        PerformanceMeasurer.write_conf_file(conf_counts, outprefix + '.conf.tsv')

