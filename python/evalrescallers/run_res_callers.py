import collections
import json
import logging
import os
import shutil
import traceback

from evalrescallers import res_caller
logging.basicConfig(level=logging.INFO)


Caller = collections.namedtuple('Caller', ['name', 'force', 'outdir_name', 'mykrobe_species', 'mykrobe_panel', 'mykrobe_probes', 'mykrobe_var_to_res', 'command_line_opts'])

def load_callers_file(infile):
    callers = []
    allowed_callers = {'ARIBA', 'KvarQ', 'MTBseq', 'Mykrobe', 'TB-Profiler'}
    allowed_mykrobe_species = {'staph', 'tb'}

    with open(infile) as f:
        for line in f:
            tool, force, outdir_name, mykrobe_species, mykrobe_panel, mykrobe_probes, mykrobe_var_to_res, command_line_opts = line.rstrip().split('\t')
            assert tool in allowed_callers
            force = force == '1'
            if command_line_opts == '.':
                command_line_opts = None

            if tool == 'ARIBA':
                # We're also using mykrobe_panel column for the ariba reference directory.
                assert mykrobe_panel != '.'
                callers.append(Caller(tool, force, outdir_name, None, mykrobe_panel, None, None, command_line_opts))
            elif tool == 'Mykrobe':
                assert mykrobe_species in allowed_mykrobe_species

                if mykrobe_species == 'staph' and mykrobe_probes == '.':
                    callers.append(Caller(tool, force, outdir_name, mykrobe_species, None, None, None, command_line_opts))
                elif mykrobe_panel in {'bradley-2015', 'walker-2015', 'Fail'}:
                    callers.append(Caller(tool, force,outdir_name,  mykrobe_species, mykrobe_panel, None, None, command_line_opts))
                else:
                    assert mykrobe_probes != '.' and mykrobe_var_to_res != '.'
                    callers.append(Caller(tool, force, outdir_name, mykrobe_species, mykrobe_panel, mykrobe_probes, mykrobe_var_to_res, command_line_opts))
            else:
                callers.append(Caller(tool, force, outdir_name, None, None, None, None, command_line_opts))


    logging.debug(f'Loaded callers file {infile}')
    return callers


def summary_json_from_all_callers(json_files_dict, outfile):
    summary_data = {}

    for caller_name, json_file in json_files_dict.items():
        if os.path.exists(json_file):
            with open(json_file) as f:
                json_data = json.load(f)
            json_data['Success'] = True
            summary_data[caller_name] = json_data
        else:
            summary_data[caller_name] = {'Success': False}

    with open(outfile, 'w') as f:
        json.dump(summary_data, f, sort_keys=True, indent=4)


def run_res_callers(callers_file, outdir, reads1, reads2, testing=False):
    logging.info(f'Run callers from file {callers_file}')
    root_outdir = os.path.abspath(outdir)
    if not os.path.exists(root_outdir):
        os.mkdir(root_outdir)
    reads1 = os.path.abspath(reads1)
    reads2 = os.path.abspath(reads2)
    ran_any_caller = False
    summary_json_files = {}
    callers_to_run = load_callers_file(callers_file)
    any_fails = False
    panel_name = None

    for caller in callers_to_run:
        logging.info(f'Setting up to run caller {caller}')
        if caller.name == 'Mykrobe':
            if caller.mykrobe_species == 'tb':
                panel_name = caller.mykrobe_panel if caller.mykrobe_probes is None else None

        caller_outdir = os.path.join(root_outdir, caller.outdir_name)
        success_file = os.path.join(caller_outdir, 'done')
        summary_json_files[caller.outdir_name] = os.path.join(caller_outdir, 'summary.json')

        if os.path.exists(caller_outdir):
            if caller.force or not os.path.exists(success_file):
                logging.info(f'deleting existing caller directory {caller_outdir}')
                shutil.rmtree(caller_outdir)
            else:
                continue

        this_res_caller = res_caller.ResCaller(caller.name, caller_outdir)
        ran_any_caller = True

        try:
            logging.info(f'Start running {caller}')
            this_res_caller.run(reads1, reads2,
                mykrobe_panel=panel_name,
                mykrobe_species=caller.mykrobe_species,
                mykrobe_custom_probe_file=caller.mykrobe_probes,
                mykrobe_custom_var_to_res=caller.mykrobe_var_to_res,
                fake_for_fast_test=testing,
                command_line_opts=caller.command_line_opts,
                ariba_ref=caller.mykrobe_panel,
            )
        except Exception:
            any_fails = True
            logging.info(f'Failed {caller}. Traceback is:')
            logging.info(traceback.format_exc())
            continue

        with open(success_file, 'w') as f:
            pass


    if ran_any_caller:
        logging.info('Making summary JSON file')
        summary_json = os.path.join(root_outdir, 'summary.json')
        summary_data = summary_json_from_all_callers(summary_json_files, summary_json)

