from collections import OrderedDict
import copy
import filecmp
import json
import os
import shutil
import unittest

from evalrescallers import plots

modules_dir = os.path.dirname(os.path.abspath(plots.__file__))
data_dir = os.path.join(modules_dir, 'tests', 'data', 'plots')


class TestPlots(unittest.TestCase):
    def test_make_map_figure(self):
        '''test make_map_figure'''
        tmp_out = 'tmp.plots.make_map_figure'
        plots.make_map_figure(tmp_out)
        assert os.path.exists(f'{tmp_out}.pdf')
        assert os.path.exists(f'{tmp_out}.R')
        os.unlink(f'{tmp_out}.pdf')
        os.unlink(f'{tmp_out}.R')
        try:
            os.unlink('.RData')
        except:
            pass


    def test_make_res_or_susc_samples_bar_chart(self):
        '''test make_res_or_susc_samples_bar_chart'''
        infile = os.path.join(data_dir, 'make_res_or_susc_samples_bar_chart.tsv')
        tmp_out = 'tmp.make_res_or_susc_samples_bar_chart.res'
        dataset = 'set1'
        tools = OrderedDict([('tool1', 'T1'), ('tool2', 'T2'), ('tool3', 'T3'), ('tool4', 'T4')])
        drugs = OrderedDict([('Drug1', 'D1'), ('Drug2', 'D2')])
        plots.make_res_or_susc_samples_bar_chart("R", infile, dataset, tools, drugs, tmp_out, y_axis_label="Y LABEL")
        os.unlink(f'{tmp_out}.pdf')
        os.unlink(f'{tmp_out}.R')
        os.unlink(f'{tmp_out}.tsv')


        tmp_out = 'tmp.make_res_or_susc_samples_bar_chart.susc.pdf'
        plots.make_res_or_susc_samples_bar_chart("S", infile, dataset, tools, drugs, tmp_out, y_axis_label="Y LABEL")
        os.unlink(f'{tmp_out}.pdf')
        os.unlink(f'{tmp_out}.R')
        os.unlink(f'{tmp_out}.tsv')
        try:
            os.unlink('.RData')
        except:
            pass


    def test_make_res_susc_bar_charts(self):
        '''test make_res_susc_bar_charts'''
        outprefix = 'tmp.make_res_susc_bar_charts'
        infile = os.path.join(data_dir, 'make_res_susc_bar_charts.tsv')
        datasets = ['set1', 'set2']
        tools = OrderedDict([('tool1', 'T1'), ('tool2', 'T2'), ('tool3', 'T3'), ('tool4', 'T4')])
        drugs = OrderedDict([('Drug1', 'D1'), ('Drug2', 'D2')])
        plots.make_res_susc_bar_charts(infile, datasets, tools, drugs, outprefix)

        for dataset in datasets:
            for r_or_s in 'R', 'S':
                out = f'{outprefix}.{dataset}.{r_or_s}'
                for ext in 'R', 'pdf', 'tsv':
                    self.assertTrue(os.path.exists(f'{out}.{ext}'))
                    os.unlink(f'{out}.{ext}')

        try:
            os.unlink('.RData')
        except:
            pass
