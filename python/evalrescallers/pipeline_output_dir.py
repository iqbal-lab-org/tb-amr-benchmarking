import json
import logging
import multiprocessing
import os
import pathlib


def load_one_sample_summary_json_file(data_tuple):
    sample, json_file = data_tuple
    if not os.path.exists(json_file):
        return sample, None

    with open(json_file) as f:
        data = json.load(f)

    return sample, data


class PipelineOutputDir:
    def __init__(self, output_dir, samples_per_dir=100):
        self.output_dir = os.path.abspath(output_dir)
        self.json_data_file = os.path.join(self.output_dir, 'data.json')
        if os.path.exists(self.json_data_file):
            with open(self.json_data_file) as f:
                self.data = json.load(f)
        else:
            self.data = {'samples_per_dir': samples_per_dir, 'samples': {}}


    @classmethod
    def load_input_data_file(cls, input_data_file):
        samples = {}

        with open(input_data_file) as f:
            for line in f:
                sample_name, reads1, reads2 = line.rstrip().split()
                if sample_name in samples:
                    raise Exception('Sample name "' + sample_name + '" found twice. Cannot continue')
                samples[sample_name] = {'name': sample_name, 'reads': [reads1, reads2], 'number': None, 'dir': None}

        return samples


    @classmethod
    def sample_number_to_dir(cls, sample_number, samples_per_dir):
        return os.path.join(str(sample_number // samples_per_dir), str(sample_number))


    def add_data_from_file(self, input_data_file):
        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)

        data_from_file = PipelineOutputDir.load_input_data_file(input_data_file)

        for this_sample_name, sample_dict in data_from_file.items():
            if this_sample_name in self.data['samples']:
                raise Exception('Sample already exists. Cannot add another with the same name. Sample name: ' + this_sample_name)

            sample_dict['number'] = len(self.data['samples'])
            sample_dict['dir'] = PipelineOutputDir.sample_number_to_dir(sample_dict['number'], self.data['samples_per_dir'])
            pathlib.Path(os.path.join(self.output_dir, sample_dict['dir'])).mkdir(parents=True)
            self.data['samples'][this_sample_name] = sample_dict


    def write_json_data_file(self):
        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)

        with open(self.json_data_file, 'w') as f:
            print(json.dumps(self.data, sort_keys=True, indent=4), file=f)


    def write_tsv_file(self, outfile):
        with open(outfile, 'w') as f:
            print('name', 'reads1', 'reads2', 'sample_dir', sep='\t', file=f)
            for sample_name, d in sorted(self.data['samples'].items()):
                print(sample_name, d['reads'][0], d['reads'][1], d['dir'], sep='\t', file=f)


    def make_summary_json_of_all_samples(self, outfile, threads=1):
        samples_and_files_list = [(sample, os.path.join(self.output_dir, self.data['samples'][sample]['dir'], 'summary.json')) for sample in self.data['samples']]
        pool = multiprocessing.Pool(processes=threads)
        results = pool.map(load_one_sample_summary_json_file, samples_and_files_list)
        pool.close()
        all_data = {}
        for sample, sample_data in sorted(results):
            if sample_data is None:
                logging.warning(f'No JSON file for sample {sample}')
                continue

            all_data[sample] = sample_data

        with open(outfile, 'w') as f:
            print(json.dumps(all_data, sort_keys=True, indent=4), file=f)

