# ----------------------------------------------------------------------------
# Copyright (c) 2016-2023, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
import tempfile
from pathlib import Path
import urllib.parse

from qiime2.plugin.testing import TestPluginBase
from qiime2 import Artifact

from q2_composition import (da_barplot, DataLoafPackageDirFmt)


class TestBase(TestPluginBase):
    package = 'q2_composition.tests'

    def setUp(self):
        super().setUp()
        self.dataloaf1 = Artifact.load(self.get_data_path('dataloaf.qza'))
        self.dataloaf2 = \
            Artifact.load(self.get_data_path('dataloaf-hmp1-body-habitat.qza'))


class TestDABarplot(TestBase):

    def _get_output_filepath(self, dir, title):
        safe_title = urllib.parse.quote(title)
        return dir / f'{safe_title}-ancombc-barplot.html'

    def test_basic_dl1(self):
        with tempfile.TemporaryDirectory() as output_dir:
            output_dir = Path(output_dir)
            _ = da_barplot(output_dir,
                           self.dataloaf1.view(DataLoafPackageDirFmt),
                           feature_id_label='id')
            self.assertTrue((output_dir / 'index.html').exists())

            tongue_path = self._get_output_filepath(
                output_dir, 'bodysitetongue')
            self.assertTrue(tongue_path.exists())

            right_palm_path = self._get_output_filepath(
                output_dir, 'bodysiteright palm')
            self.assertTrue(right_palm_path.exists())

            left_palm_path = self._get_output_filepath(
                output_dir, 'bodysiteleft palm')
            self.assertTrue(left_palm_path.exists())

            # checking that spaces are converted to %20
            left_palm_path = self._get_output_filepath(
                    output_dir, 'bodysiteleft palm')
            fp = str(left_palm_path)
            expected_fp_segment = "bodysiteleft%20palm-ancombc-barplot.html"
            self.assertIn(expected_fp_segment, fp)

            # file shouldn't exist for reference column
            gut_path = self._get_output_filepath(
                output_dir, 'bodysitegut')
            self.assertFalse(gut_path.exists())

            # spot check for a feature id
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(tongue_path).read())
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(right_palm_path).read())
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(left_palm_path).read())

    def test_basic_dl2(self):
        with tempfile.TemporaryDirectory() as output_dir:
            output_dir = Path(output_dir)
            _ = da_barplot(output_dir,
                           self.dataloaf2.view(DataLoafPackageDirFmt))
            self.assertTrue((output_dir / 'index.html').exists())

            feces_path = self._get_output_filepath(
                output_dir, 'body_habitatUBERON:feces')
            self.assertTrue(feces_path.exists())

            oral_cavity_path = self._get_output_filepath(
                output_dir, 'body_habitatUBERON:oral cavity')
            self.assertTrue(oral_cavity_path.exists())

            saliva_path = self._get_output_filepath(
                output_dir, 'body_habitatUBERON:saliva')
            self.assertTrue(saliva_path.exists())

            vagina_path = self._get_output_filepath(
                output_dir, 'body_habitatUBERON:vagina')
            self.assertTrue(vagina_path.exists())

            # file shouldn't exist for reference column
            skin_path = self._get_output_filepath(
                output_dir, 'body_habitatUBERON:skin')
            self.assertFalse(skin_path.exists())

            # spot check for a feature id
            self.assertTrue(
                'g__Staphylococcus' in
                open(feces_path).read())
            self.assertTrue(
                'g__Staphylococcus' in
                open(oral_cavity_path).read())
            self.assertTrue(
                'g__Staphylococcus' in
                open(saliva_path).read())
            self.assertTrue(
                'g__Staphylococcus' in
                open(vagina_path).read())

    def test_filter_on_significance(self):
        # confirm feature presence when not filtering
        with tempfile.TemporaryDirectory() as output_dir:
            output_dir = Path(output_dir)
            _ = da_barplot(output_dir,
                           self.dataloaf1.view(DataLoafPackageDirFmt),
                           feature_id_label='id',
                           significance_threshold=1.0)

            tongue_path = self._get_output_filepath(
                output_dir, 'bodysitetongue')
            self.assertTrue(tongue_path.exists())

            right_palm_path = self._get_output_filepath(
                output_dir, 'bodysiteright palm')
            self.assertTrue(right_palm_path.exists())

            left_palm_path = self._get_output_filepath(
                output_dir, 'bodysiteleft palm')
            self.assertTrue(left_palm_path.exists())

            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(tongue_path).read())
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(right_palm_path).read())
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(left_palm_path).read())

        # confirm feature absence when filtering
        with tempfile.TemporaryDirectory() as output_dir:
            output_dir = Path(output_dir)
            _ = da_barplot(output_dir,
                           self.dataloaf1.view(DataLoafPackageDirFmt),
                           feature_id_label='id',
                           significance_threshold=1e-3)

            tongue_path = self._get_output_filepath(
                output_dir, 'bodysitetongue')
            self.assertTrue(tongue_path.exists())

            right_palm_path = self._get_output_filepath(
                output_dir, 'bodysiteright palm')
            self.assertTrue(right_palm_path.exists())

            left_palm_path = self._get_output_filepath(
                output_dir, 'bodysiteleft palm')
            self.assertTrue(left_palm_path.exists())

            # this feature is significant at this
            # threshold only in tongue and left palm
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(tongue_path).read())
            self.assertFalse(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(right_palm_path).read())
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(left_palm_path).read())

    def test_filter_on_effect_size(self):
        # confirm feature presence when not filtering
        with tempfile.TemporaryDirectory() as output_dir:
            output_dir = Path(output_dir)
            _ = da_barplot(output_dir,
                           self.dataloaf1.view(DataLoafPackageDirFmt),
                           feature_id_label='id',
                           effect_size_threshold=0)

            tongue_path = self._get_output_filepath(
                output_dir, 'bodysitetongue')
            self.assertTrue(tongue_path.exists())

            right_palm_path = self._get_output_filepath(
                output_dir, 'bodysiteright palm')
            self.assertTrue(right_palm_path.exists())

            left_palm_path = self._get_output_filepath(
                output_dir, 'bodysiteleft palm')
            self.assertTrue(left_palm_path.exists())

            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(tongue_path).read())
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(right_palm_path).read())
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(left_palm_path).read())

        # confirm feature absence when filtering
        with tempfile.TemporaryDirectory() as output_dir:
            output_dir = Path(output_dir)
            _ = da_barplot(output_dir,
                           self.dataloaf1.view(DataLoafPackageDirFmt),
                           feature_id_label='id',
                           effect_size_threshold=3.5)

            tongue_path = self._get_output_filepath(
                output_dir, 'bodysitetongue')
            self.assertTrue(tongue_path.exists())

            right_palm_path = self._get_output_filepath(
                output_dir, 'bodysiteright palm')
            self.assertTrue(right_palm_path.exists())

            left_palm_path = self._get_output_filepath(
                output_dir, 'bodysiteleft palm')
            self.assertTrue(left_palm_path.exists())

            # this feature's effect size is greater
            # than the threshold only in tongue and left palm
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(tongue_path).read())
            self.assertFalse(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(right_palm_path).read())
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(left_palm_path).read())

    def test_filter_on_feature_ids(self):
        ids_to_keep = ['bfbed36e63b69fec4627424163d20118',
                       '4b5eeb300368260019c1fbc7a3c718fc']

        # confirm feature presence when no filtering
        with tempfile.TemporaryDirectory() as output_dir:
            output_dir = Path(output_dir)
            _ = da_barplot(output_dir,
                           self.dataloaf1.view(DataLoafPackageDirFmt),
                           feature_id_label='id',
                           feature_ids=None)

            tongue_path = self._get_output_filepath(
                output_dir, 'bodysitetongue')
            self.assertTrue(tongue_path.exists())

            right_palm_path = self._get_output_filepath(
                output_dir, 'bodysiteright palm')
            self.assertTrue(right_palm_path.exists())

            left_palm_path = self._get_output_filepath(
                output_dir, 'bodysiteleft palm')
            self.assertTrue(left_palm_path.exists())

            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(tongue_path).read())
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(right_palm_path).read())
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(left_palm_path).read())

        # confirm feature absence when filtering
        with tempfile.TemporaryDirectory() as output_dir:
            output_dir = Path(output_dir)
            _ = da_barplot(output_dir,
                           self.dataloaf1.view(DataLoafPackageDirFmt),
                           feature_id_label='id',
                           feature_ids=ids_to_keep)

            tongue_path = self._get_output_filepath(
                output_dir, 'bodysitetongue')
            self.assertTrue(tongue_path.exists())

            right_palm_path = self._get_output_filepath(
                output_dir, 'bodysiteright palm')
            self.assertTrue(right_palm_path.exists())

            left_palm_path = self._get_output_filepath(
                output_dir, 'bodysiteleft palm')
            self.assertTrue(left_palm_path.exists())

            # feature ids expected to be absent are absent
            self.assertFalse(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(tongue_path).read())
            self.assertFalse(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(right_palm_path).read())
            self.assertFalse(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(left_palm_path).read())

            # feature ids expected to be present are present
            self.assertTrue(
                'bfbed36e63b69fec4627424163d20118' in
                open(tongue_path).read())
            self.assertTrue(
                'bfbed36e63b69fec4627424163d20118' in
                open(right_palm_path).read())
            self.assertTrue(
                'bfbed36e63b69fec4627424163d20118' in
                open(left_palm_path).read())

            self.assertTrue(
                '4b5eeb300368260019c1fbc7a3c718fc' in
                open(tongue_path).read())
            self.assertTrue(
                '4b5eeb300368260019c1fbc7a3c718fc' in
                open(right_palm_path).read())
            self.assertTrue(
                '4b5eeb300368260019c1fbc7a3c718fc' in
                open(left_palm_path).read())

    def test_error_on_bad_column_names(self):
        with tempfile.TemporaryDirectory() as output_dir:
            with self.assertRaisesRegex(KeyError, "id.*\"taxon\".*not"):
                da_barplot(output_dir,
                           data=self.dataloaf1.view(DataLoafPackageDirFmt),
                           feature_id_label='taxon')

        with tempfile.TemporaryDirectory() as output_dir:
            with self.assertRaisesRegex(KeyError, "label.*stderr.*not"):
                da_barplot(output_dir,
                           data=self.dataloaf1.view(DataLoafPackageDirFmt),
                           error_label='stderr')

    def test_toggle_level_delimiter(self):
        # no delimiter
        with tempfile.TemporaryDirectory() as output_dir:
            output_dir = Path(output_dir)
            _ = da_barplot(output_dir,
                           self.dataloaf2.view(DataLoafPackageDirFmt))

            feces_path = self._get_output_filepath(
                output_dir, 'body_habitatUBERON:feces')
            self.assertTrue(feces_path.exists())

            oral_cavity_path = self._get_output_filepath(
                output_dir, 'body_habitatUBERON:oral cavity')
            self.assertTrue(oral_cavity_path.exists())

            saliva_path = self._get_output_filepath(
                output_dir, 'body_habitatUBERON:saliva')
            self.assertTrue(saliva_path.exists())

            vagina_path = self._get_output_filepath(
                output_dir, 'body_habitatUBERON:vagina')
            self.assertTrue(vagina_path.exists())

            # multi-level information should be present as 'y-label'
            self.assertTrue(
                '"y_label": "d__Bacteria;p__Firmicutes;c__Bacilli;o__Staphylococcales;f__Staphylococcaceae;g__Staphylococcus"'  # noqa: E501
                in open(feces_path).read())
            self.assertTrue(
                '"y_label": "d__Bacteria;p__Firmicutes;c__Bacilli;o__Staphylococcales;f__Staphylococcaceae;g__Staphylococcus"'  # noqa: E501
                in open(oral_cavity_path).read())
            self.assertTrue(
                '"y_label": "d__Bacteria;p__Firmicutes;c__Bacilli;o__Staphylococcales;f__Staphylococcaceae;g__Staphylococcus"'  # noqa: E501
                in open(saliva_path).read())
            self.assertTrue(
                '"y_label": "d__Bacteria;p__Firmicutes;c__Bacilli;o__Staphylococcales;f__Staphylococcaceae;g__Staphylococcus"'  # noqa: E501
                in open(vagina_path).read())

            # same labels should be present as 'feature'
            self.assertTrue(
                '"feature": "d__Bacteria;p__Firmicutes;c__Bacilli;o__Staphylococcales;f__Staphylococcaceae;g__Staphylococcus"'  # noqa: E501
                in open(feces_path).read())
            self.assertTrue(
                '"feature": "d__Bacteria;p__Firmicutes;c__Bacilli;o__Staphylococcales;f__Staphylococcaceae;g__Staphylococcus"'  # noqa: E501
                in open(oral_cavity_path).read())
            self.assertTrue(
                '"feature": "d__Bacteria;p__Firmicutes;c__Bacilli;o__Staphylococcales;f__Staphylococcaceae;g__Staphylococcus"'  # noqa: E501
                in open(saliva_path).read())
            self.assertTrue(
                '"feature": "d__Bacteria;p__Firmicutes;c__Bacilli;o__Staphylococcales;f__Staphylococcaceae;g__Staphylococcus"'  # noqa: E501
                in open(vagina_path).read())

        # typical delimiter: ;
        with tempfile.TemporaryDirectory() as output_dir:
            output_dir = Path(output_dir)
            _ = da_barplot(output_dir,
                           self.dataloaf2.view(DataLoafPackageDirFmt),
                           level_delimiter=';')

            feces_path = self._get_output_filepath(
                output_dir, 'body_habitatUBERON:feces')
            self.assertTrue(feces_path.exists())

            oral_cavity_path = self._get_output_filepath(
                output_dir, 'body_habitatUBERON:oral cavity')
            self.assertTrue(oral_cavity_path.exists())

            saliva_path = self._get_output_filepath(
                output_dir, 'body_habitatUBERON:saliva')
            self.assertTrue(saliva_path.exists())

            vagina_path = self._get_output_filepath(
                output_dir, 'body_habitatUBERON:vagina')
            self.assertTrue(vagina_path.exists())

            # single-level information should be present as 'y-label'
            self.assertTrue(
                '"y_label": "g__Staphylococcus' in
                open(feces_path).read())
            self.assertTrue(
                '"y_label": "g__Staphylococcus' in
                open(oral_cavity_path).read())
            self.assertTrue(
                '"y_label": "g__Staphylococcus' in
                open(saliva_path).read())
            self.assertTrue(
                '"y_label": "g__Staphylococcus' in
                open(vagina_path).read())

            # space delimited labels should be present as 'feature'
            self.assertTrue(
                '"feature": "d__Bacteria p__Firmicutes c__Bacilli o__Staphylococcales f__Staphylococcaceae g__Staphylococcus"'  # noqa: E501
                in open(feces_path).read())
            self.assertTrue(
                '"feature": "d__Bacteria p__Firmicutes c__Bacilli o__Staphylococcales f__Staphylococcaceae g__Staphylococcus"'  # noqa: E501
                in open(oral_cavity_path).read())
            self.assertTrue(
                '"feature": "d__Bacteria p__Firmicutes c__Bacilli o__Staphylococcales f__Staphylococcaceae g__Staphylococcus"'  # noqa: E501
                in open(saliva_path).read())
            self.assertTrue(
                '"feature": "d__Bacteria p__Firmicutes c__Bacilli o__Staphylococcales f__Staphylococcaceae g__Staphylococcus"'  # noqa: E501
                in open(vagina_path).read())

        # weird delimiter: __
        with tempfile.TemporaryDirectory() as output_dir:
            output_dir = Path(output_dir)
            _ = da_barplot(output_dir,
                           self.dataloaf2.view(DataLoafPackageDirFmt),
                           level_delimiter='__')

            feces_path = self._get_output_filepath(
                output_dir, 'body_habitatUBERON:feces')
            self.assertTrue(feces_path.exists())

            oral_cavity_path = self._get_output_filepath(
                output_dir, 'body_habitatUBERON:oral cavity')
            self.assertTrue(oral_cavity_path.exists())

            saliva_path = self._get_output_filepath(
                output_dir, 'body_habitatUBERON:saliva')
            self.assertTrue(saliva_path.exists())

            vagina_path = self._get_output_filepath(
                output_dir, 'body_habitatUBERON:vagina')
            self.assertTrue(vagina_path.exists())

            # single-level information should be present as 'y-label'
            self.assertTrue(
                '"y_label": "Staphylococcus' in
                open(feces_path).read())
            self.assertTrue(
                '"y_label": "Staphylococcus' in
                open(oral_cavity_path).read())
            self.assertTrue(
                '"y_label": "Staphylococcus' in
                open(saliva_path).read())
            self.assertTrue(
                '"y_label": "Staphylococcus' in
                open(vagina_path).read())

            # space delimited labels should be present as 'feature'
            self.assertTrue(
                '"feature": "d Bacteria;p Firmicutes;c Bacilli;o Staphylococcales;f Staphylococcaceae;g Staphylococcus"'  # noqa: E501
                in open(feces_path).read())
            self.assertTrue(
                '"feature": "d Bacteria;p Firmicutes;c Bacilli;o Staphylococcales;f Staphylococcaceae;g Staphylococcus"'  # noqa: E501
                in open(oral_cavity_path).read())
            self.assertTrue(
                '"feature": "d Bacteria;p Firmicutes;c Bacilli;o Staphylococcales;f Staphylococcaceae;g Staphylococcus"'  # noqa: E501
                in open(saliva_path).read())
            self.assertTrue(
                '"feature": "d Bacteria;p Firmicutes;c Bacilli;o Staphylococcales;f Staphylococcaceae;g Staphylococcus"'  # noqa: E501
                in open(vagina_path).read())

        # missing delimiter: !
        with tempfile.TemporaryDirectory() as output_dir:
            output_dir = Path(output_dir)
            _ = da_barplot(output_dir,
                           self.dataloaf2.view(DataLoafPackageDirFmt),
                           level_delimiter='!')

            feces_path = self._get_output_filepath(
                output_dir, 'body_habitatUBERON:feces')
            self.assertTrue(feces_path.exists())

            oral_cavity_path = self._get_output_filepath(
                output_dir, 'body_habitatUBERON:oral cavity')
            self.assertTrue(oral_cavity_path.exists())

            saliva_path = self._get_output_filepath(
                output_dir, 'body_habitatUBERON:saliva')
            self.assertTrue(saliva_path.exists())

            vagina_path = self._get_output_filepath(
                output_dir, 'body_habitatUBERON:vagina')
            self.assertTrue(vagina_path.exists())

            # multi-level information should be present as 'y-label'
            self.assertTrue(
                '"y_label": "d__Bacteria;p__Firmicutes;c__Bacilli;o__Staphylococcales;f__Staphylococcaceae;g__Staphylococcus"'  # noqa: E501
                in open(feces_path).read())
            self.assertTrue(
                '"y_label": "d__Bacteria;p__Firmicutes;c__Bacilli;o__Staphylococcales;f__Staphylococcaceae;g__Staphylococcus"'  # noqa: E501
                in open(oral_cavity_path).read())
            self.assertTrue(
                '"y_label": "d__Bacteria;p__Firmicutes;c__Bacilli;o__Staphylococcales;f__Staphylococcaceae;g__Staphylococcus"'  # noqa: E501
                in open(saliva_path).read())
            self.assertTrue(
                '"y_label": "d__Bacteria;p__Firmicutes;c__Bacilli;o__Staphylococcales;f__Staphylococcaceae;g__Staphylococcus"'  # noqa: E501
                in open(vagina_path).read())

            # same labels should be present as 'feature'
            self.assertTrue(
                '"feature": "d__Bacteria;p__Firmicutes;c__Bacilli;o__Staphylococcales;f__Staphylococcaceae;g__Staphylococcus"'  # noqa: E501
                in open(feces_path).read())
            self.assertTrue(
                '"feature": "d__Bacteria;p__Firmicutes;c__Bacilli;o__Staphylococcales;f__Staphylococcaceae;g__Staphylococcus"'  # noqa: E501
                in open(oral_cavity_path).read())
            self.assertTrue(
                '"feature": "d__Bacteria;p__Firmicutes;c__Bacilli;o__Staphylococcales;f__Staphylococcaceae;g__Staphylococcus"'  # noqa: E501
                in open(saliva_path).read())
            self.assertTrue(
                '"feature": "d__Bacteria;p__Firmicutes;c__Bacilli;o__Staphylococcales;f__Staphylococcaceae;g__Staphylococcus"'  # noqa: E501
                in open(vagina_path).read())
