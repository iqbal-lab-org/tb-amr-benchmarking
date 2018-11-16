import csv
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time

logging.basicConfig(level=logging.INFO)
allowed_callers = {'ARIBA', 'KvarQ', 'MTBseq', 'Mykrobe', 'TB-Profiler'}
tb_profiler_change_regex = re.compile(r'''^(?P<position>-?\d*)(?P<sequence>[A-Z\*]+)$''')
kvarq_var_with_square_brackets_regex = re.compile(r'''^resistance.*\[.*=(?P<gene>.*)\.(?P<variant>[A-Z0-9]+)\]$''')

class ResCaller:
    def __init__(self, caller, outdir):
        assert caller in allowed_callers
        self.caller = caller
        self.outdir = os.path.abspath(outdir)
        self.json_results_file = os.path.join(self.outdir, 'out.json')
        self.summary_output_json = os.path.join(self.outdir, 'summary.json')
        self.command_stdouterr_file = os.path.join(self.outdir, 'command.out')


    def _clean_run_dir(self, skip=False):
        if self.caller == 'KvarQ' or self.caller == 'ariba' or skip:
            pass
        elif self.caller == 'MTBseq':
            to_delete = ['Amend', 'Bam', 'Classification', 'GATK_Bam', 'Groups', 'Joint', 'Mpileup', 'Position_Tables', 'Statistics']
            for directory in to_delete:
                try:
                    shutil.rmtree(os.path.join(self.outdir, directory))
                except:
                    pass
        elif self.caller == 'Mykrobe':
            shutil.rmtree(os.path.join(self.outdir, 'tmp'))
            shutil.rmtree(os.path.join(self.outdir, 'mykrobe'))
        elif self.caller == 'TB-Profiler':
            json_old = os.path.join(self.outdir, 'results', 'out.results.json')
            os.rename(json_old, self.json_results_file)
            shutil.rmtree(os.path.join(self.outdir, 'bam'))
            shutil.rmtree(os.path.join(self.outdir, 'results'))
            shutil.rmtree(os.path.join(self.outdir, 'vcf'))
        else:
            raise Exception('Caller "' + self.caller + '" not recognised. Must be one of: ' + str(allowed_callers))


    @classmethod
    def _mtbseq_tab_file_to_res_calls(cls, tab_file):
        res_calls = {}

        with open(tab_file) as f:
            file_reader = csv.DictReader(f, delimiter='\t')
            for d in file_reader:
                if d['ResistanceSNP'] is not None and len(d['ResistanceSNP'].strip()) > 0:
                    # Lines look like eg:
                    # fluoroquinolones (FQ)
                    drug = d['ResistanceSNP'].split()[0].capitalize()
                    if drug == 'Fluoroquinolones':
                        drug = 'Quinolones'
                    gene = d['Gene'] if d['GeneName'] == '-' else d['GeneName']
                    # in the "uncovered" file, the Subst has a space.
                    # In the "variant" file, it has things like: Met306Ile (atg/atC)
                    if d['Subst'] == ' ':
                        variant = None
                    else:
                        variant = d['Subst'].split()[0]
                    if drug not in res_calls:
                        res_calls[drug] = set()
                    res_calls[drug].add(('R', gene, variant, None))

        return res_calls


    @classmethod
    def _mtbseq_outdir_to_res_calls_json_file(cls, mtbseq_dir, json_out):
        # The two files we want are in the Called/ directory.
        # They have names like this:
        #   sampleID_libID.gatk_position_uncovered_cf4_cr4_fr75_ph4_outmode000.tab
        #   sampleID_libID.gatk_position_variants_cf4_cr4_fr75_ph4_outmode000.tab
        # so first need to find those files
        called_dir = os.path.join(mtbseq_dir, 'Called')
        if not os.path.exists(called_dir):
            raise FileNotFoundError(f'MTBseq "Called" directory not found. Looked for: {called_dir}')

        tab_files = [x for x in os.listdir(called_dir) if x.endswith('.tab')]
        variants_file = None
        uncovered_file = None
        for filename in os.listdir(called_dir):
            if not filename.endswith('.tab'):
                continue

            if '_uncovered_' in filename:
                uncovered_file = os.path.join(called_dir, filename)
            elif '_variants_' in filename:
                variants_file = os.path.join(called_dir, filename)

        if variants_file is None:
            raise FileNotFoundError(f'MTBseq variants file not found in dir {called_dir}')

        res_calls = ResCaller._mtbseq_tab_file_to_res_calls(variants_file)
        if uncovered_file is not None:
            new_res_calls = ResCaller._mtbseq_tab_file_to_res_calls(uncovered_file)
            for drug, call_list in new_res_calls.items():
                if drug not in res_calls:
                    res_calls[drug] = set()
                res_calls[drug].update(call_list)

        for drug in res_calls:
            res_calls[drug] = sorted(list(res_calls[drug]))

        with open(json_out, 'w') as f:
            json.dump(res_calls, f, sort_keys=True, indent=4)


    @classmethod
    def _kvarq_var_string_parser(cls, var_string):
        if var_string.startswith('remark'):
            return None, None, None
        elif 'resistance' not in var_string:
            raise Exception(f'Cannot parse line of KvarQ output: {var_string}')

        drug, the_rest = var_string.split(maxsplit=1)

        if '::' in the_rest:
            # looks like one of these:
            #   Isoniazid resistance::SNP1673425CT=inhA promoter mutation -15'
            #   Ethambutol resistance::SNP4247431GC=embB.M306I
            if '=' in the_rest:
                gene_and_mutation = the_rest.split(':')[-1].split('=')[-1]
                if '.' in gene_and_mutation:
                    gene, mutation = gene_and_mutation.split('.')
                else:
                    gene, mutation = gene_and_mutation.split(None, maxsplit=1)
                return drug, gene, mutation
        else:
            # looks like:
            #   Isoniazid resistance [2155168CG=katG.S315T]
            #   Rifampicin resistance (RRDR) [761155CT=rpoB.S450L]
            match = kvarq_var_with_square_brackets_regex.search(the_rest)

            if match is not None:
                return drug, match.group('gene'), match.group('variant')

        logging.warning(f'Got drug as "{drug}" but could not get variant from TB-Profiler string: {var_string}')
        return drug, 'Parse_error', 'Parse_error'


    @classmethod
    def _tb_profiler_var_string_parser(cls, var_string):
        if '>' not in var_string:
            raise Exception(f'Expected ">" in variant string from TB-Profiler, but got "{var_string}"')

        change_before, change_after = var_string.split('>')
        match_before = tb_profiler_change_regex.search(change_before)
        match_after = tb_profiler_change_regex.search(change_after)

        if match_before is None or match_after is None:
            raise Exception(f'Error using regex on variant string "{var_string}" from TB-Profiler')

        if len(match_before.group('position')) == 0:
            raise Exception(f'Could not get position of variant from "{var_string}" from TB-Profiler')

        if len(match_after.group('position')) > 0 and match_before.group('position') != match_after.group('position'):
            raise Exception(f'Positions not the same in variant string "{var_string}" from TB-Profiler')

        return match_before.group('sequence') + match_before.group('position') + match_after.group('sequence')


    @classmethod
    def _json_to_resistance_calls(cls, json_in, caller):
        with open(json_in) as f:
            json_data = json.load(f)

        resistance_calls = {}
        quinolones = {'Ciprofloxacin', 'Moxifloxacin', 'Ofloxacin'}

        if caller == 'KvarQ':
            try:
                res_list = json_data['analyses']['MTBC/resistance']
            except:
                raise Exception(f'Could not find analysis -> MTBC/resistance in JSON file "{os.path.abspath(json_in)}". Cannot continue')

            for res_line in res_list:
                drug, gene, change = ResCaller._kvarq_var_string_parser(res_line)
                if drug is None:
                    continue

                if drug == 'Fluoroquinolones':
                    drug = 'Quinolones'

                if drug == 'Kanamycin/Amikacin':
                    drugs = drug.split('/')
                else:
                    drugs = [drug]

                for d in drugs:
                    if d not in resistance_calls:
                        resistance_calls[d] = []

                    resistance_calls[d].append(('R', gene, change, None))
        elif caller == 'MTBseq':
            resistance_calls = json_data
        elif caller == 'Mykrobe':
            sample_names = list(json_data.keys())
            if len(sample_names) != 1:
                raise Exception(f'Expected one key in json file "{os.path.abspath(json_in)}" but got: {sample_names}')

            sample_name = sample_names[0]

            try:
                suscept_data = json_data[sample_name]['susceptibility']
            except:
                raise Exception(f'Error getting susceptibility from file "{os.path.abspath(json_in)}"')

            for drug in suscept_data:
                if drug not in resistance_calls:
                    resistance_calls[drug] = []

                if drug in quinolones:
                    if 'Quinolones' not in resistance_calls:
                        resistance_calls['Quinolones'] = []

                if suscept_data[drug]['predict'] in {'r', 'R'}:

                    for variant in suscept_data[drug]['called_by']:
                        # Presence of a gene just has the gene name.
                        # Variant calls have an underscore
                        if '_' in variant:
                            gene, change = variant.split('_')
                            # Most vars look like this: embB_Q497R-Q497R. But not all.
                            # Have also seen this: fabG1_C-15X-C. Try spltting on "-" to get
                            # two things, but if that doesn't wok then keep everything
                            changes = change.split('-')
                            if len(changes) == 2:
                                if changes[0] != changes[1]:
                                    raise Exception(f'Unexpected format in "called_by" key: {variant}')
                                this_change = changes[0]
                            else:
                                this_change = change
                        else:
                            gene = variant
                            this_change = 'NA'
                        try:
                            conf = int(suscept_data[drug]['called_by'][variant]['info']['conf'])
                        except:
                            conf = None

                        try:
                            ref_depth = int(suscept_data[drug]['called_by'][variant]['info']['coverage']['reference']['median_depth'])
                        except:
                            ref_depth = None

                        try:
                            alt_depth = int(suscept_data[drug]['called_by'][variant]['info']['coverage']['alternate']['median_depth'])
                        except:
                            alt_depth = None

                        try:
                            expected_depths = suscept_data[drug]['called_by'][variant]['info']['expected_depths']
                            expected_depth = round(sum(expected_depths) / len(expected_depths))
                        except:
                            expected_depth = None

                        to_append = (suscept_data[drug]['predict'], gene, this_change, {'conf': conf, 'ref_depth': ref_depth, 'alt_depth': alt_depth, 'expected_depth': expected_depth})
                        resistance_calls[drug].append(to_append)
                        if drug in quinolones:
                            resistance_calls['Quinolones'].append(to_append)

                else:
                    to_append = (suscept_data[drug]['predict'], None, None, {})
                    resistance_calls[drug].append(to_append)
                    if drug in quinolones:
                        resistance_calls['Quinolones'].append(to_append)
        elif caller == 'TB-Profiler':
            if 'small_variants_dr' not in json_data:
                raise Exception(f'Expected one key in json file "{os.path.abspath(json_in)}" but got: {sample_names}')

            for data in json_data['small_variants_dr']:
                drug = data['drug'].capitalize()
                if drug == 'Fluoroquinolones':
                    drug = 'Quinolones'
                change = ResCaller._tb_profiler_var_string_parser(data['change'])
                if drug not in resistance_calls:
                    resistance_calls[drug] = []
                resistance_calls[drug].append(('R', data['gene'], change, None))
        else:
            raise Exception('Caller "' + caller + '" not recognised. Must be one of: ' + str(allowed_callers))

        return resistance_calls


    @classmethod
    def _bash_out_to_time_and_memory(cls, infile):
        stats = {}

        with open(infile) as f:
            in_time_lines = False
            for line in f:
                if not in_time_lines:
                    if line.startswith('\tCommand being timed:'):
                        in_time_lines = True
                elif line.startswith('\tElapsed (wall clock) time (h:mm:ss or m:ss): '):
                    time_fields = line.rstrip().split()[-1].split(':')
                    if not 2 <= len(time_fields) <= 3:
                        raise Exception(f'Error getting time from this line: {line}')
                    time_in_seconds = float(time_fields[-1]) + 60 * float(time_fields[-2])
                    if len(time_fields) == 3:
                        time_in_seconds += 60 * 60 * float(time_fields[0])
                    stats['wall_clock_time'] = time_in_seconds
                elif line.startswith('\tUser time (seconds): '):
                    stats['user_time'] = float(line.rstrip().split()[-1])
                elif line.startswith('\tSystem time (seconds): '):
                    stats['system_time'] = float(line.rstrip().split()[-1])
                elif line.startswith('\tMaximum resident set size (kbytes): '):
                    stats['ram'] = float(line.rstrip().split()[-1])

        return stats


    def run(self, reads1, reads2, mykrobe_species=None, mykrobe_panel=None, mykrobe_custom_probe_file=None, mykrobe_custom_var_to_res=None, debug=False, fake_for_fast_test=False, command_line_opts=None):
        if command_line_opts is None:
            command_line_opts = ''

        logging.info(f'Setting up output directory {self.outdir!r} for caller {self.caller}')
        reads1 = os.path.abspath(reads1)
        reads2 = os.path.abspath(reads2)
        if not os.path.exists(reads1):
            raise FileNotFoundError(f'Reads file 1 not found: {reads1!r}')
        if not os.path.exists(reads2):
            raise FileNotFoundError(f'Reads file 2 not found: {reads2!r}')

        try:
            os.mkdir(self.outdir)
        except:
            raise Exception(f'Error mkdir {self.outdir!r}. Cannot continue')

        original_dir = os.getcwd()
        os.chdir(self.outdir)
        logging.info(f'Output directory {self.outdir!r} set up for caller {self.caller}')

        if self.caller == 'KvarQ':
            command = [f'kvarq scan {command_line_opts} -l MTBC -t 1 -p {reads1} {self.json_results_file}']
        elif self.caller == 'MTBseq':
            # MTBseq uses /tmp/ when sorting BAM files. This means
            # we need a unique sample and/or library name, otherwise the
            # filenames in /tmp/ are not guaranteed to be unique. See
            # https://github.com/ngs-fzb/MTBseq_source/issues/22
            # Use the PID, plus the current time for extra paranoia
            sample = f'{os.getppid()}.{time.time()}'

            # Needs reads named in a specific way in the directory
            # where it is run. Make symlinks with the correct name
            link1 = f'{sample}_libID_R1.fastq.gz'
            link2 = f'{sample}_libID_R2.fastq.gz'
            try:
                os.symlink(reads1, link1)
                os.symlink(reads2, link2)
            except:
                raise Exception(f'Error making symlinks to reads files reads1 reads2')

            reads1 = os.path.abspath(link1)
            reads2 = os.path.abspath(link2)
            command = [f'MTBseq --step TBfull']
        elif self.caller == 'Mykrobe':
            assert mykrobe_species in ['tb', 'staph']
            command = [f'mykrobe predict sample {mykrobe_species} {command_line_opts}']

            if mykrobe_species == 'tb':
                if mykrobe_custom_probe_file is not None or mykrobe_custom_var_to_res is not None:
                    assert None not in {mykrobe_custom_probe_file, mykrobe_custom_var_to_res}
                    mykrobe_panel = 'custom'
                    command.append(f'--panel custom --custom_probe_set_path {mykrobe_custom_probe_file} --custom_variant_to_resistance_json {mykrobe_custom_var_to_res}')
                else:
                    assert mykrobe_panel is not None
                    command.append(f'--panel {mykrobe_panel}')

            command.append(f'--seq {reads1} {reads2} --output {self.json_results_file}')
        elif self.caller == 'TB-Profiler':
            command = [f'tb-profiler profile {command_line_opts} -1 {reads1} -2 {reads2} -p out']
        else:
            raise Exception('Caller "' + self.caller + '" not recognised. Must be one of: ' + str(allowed_callers))

        if fake_for_fast_test:
            if self.caller == 'Mykrobe' and mykrobe_panel == 'Fail':
                raise Exception('Deliberately failing test run')

            command = f'/usr/bin/time -v sleep 1s &> {self.command_stdouterr_file}'
            res_call_dict = {
                'KvarQ': {'Ethambutol': [('R', 'embB', 'M306I', None)]},
                'MTBseq': {'Ethambutol': [('R', 'embB', 'M306L', None)]},
                'Mykrobe': {'Ethambutol': [('r', 'embB', 'M306J', 42)]},
                'TB-Profiler': {'Ethambutol': [('R', 'embB', 'M306K', None)]},
            }
            resistance_calls = res_call_dict[self.caller]
        else:
            # Want to redirect stderr and stdout to the output file.
            # Specify bash shell with "executable='/bin/bash'" in the
            # subprocess.run call, so the '&>' works.
            command = '/usr/bin/time -v ' + ' '.join(command) + ' &> ' + self.command_stdouterr_file


        logging.info(f'Running command: {command}')
        completed_process = subprocess.run(command, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
        os.chdir(original_dir)

        # MTBseq currently makes the files we need to get the resistance
        # calls, but crashes before the end of the whole pipeline. So we
        # don't expect return code of zero. Counts as success if we can
        # get the resistance calls from the files
        if self.caller == 'MTBseq' and not fake_for_fast_test:
            try:
                ResCaller._mtbseq_outdir_to_res_calls_json_file(self.outdir, self.json_results_file)
            except:
                raise Exception(f'Could not get resistance calls from MTBseq output dir {self.outdir}')
        elif completed_process.returncode != 0:
            raise Exception(f'Error running command: {command}\nError code:{completed_process.returncode}\nOutput was:\n{completed_process.stdout}')

        if not debug:
            self._clean_run_dir(skip=fake_for_fast_test)

        if not fake_for_fast_test:
            resistance_calls = ResCaller._json_to_resistance_calls(self.json_results_file, self.caller)
        time_and_memory = ResCaller._bash_out_to_time_and_memory(self.command_stdouterr_file)
        summary_data = {'resistance_calls': resistance_calls, 'time_and_memory': time_and_memory}

        with open(self.summary_output_json, 'w') as f:
            json.dump(summary_data, f, sort_keys=True, indent=4)

