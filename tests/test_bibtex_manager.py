import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'bibtex_manager.py'
spec = importlib.util.spec_from_file_location('bibtex_manager', SCRIPT)
mod = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

ORIGINAL = '''@COMMENT{jabref-meta: databaseType:bibtex;}
@article{Keep2020,
  title = {Not modified},
  year = {2020},
  file = {keep.pdf},
  groups = {Group},
  comment = {Old note}
}
@article{ExistingStrang,
  title = {On the Construction and Comparison of Difference Schemes},
  doi = {https://doi.org/10.1137/0705041},
  year = {1968},
  comment = {Existing review}
}
'''
SOURCE = '''@article{Strang1968,
  title = {On the Construction and Comparison of Difference Schemes},
  doi = {10.1137/0705041},
  year = {1968},
  comment = {New reading advice}
}
@article{Fresh2021,
  title = {Fresh work},
  doi = {10.1000/unique123},
  year = {2021}
}
'''

class BibManagerTests(unittest.TestCase):
    def test_parse_example(self):
        path = SCRIPT.parents[1] / 'examples' / 'strang_splitting_references.bib'
        self.assertEqual(len(mod.parse_bib(path.read_text(encoding='utf-8'))), 6)

    def test_merge_preserve_and_comment(self):
        updated, report = mod.merge(ORIGINAL, SOURCE)
        self.assertEqual(report['added'], ['Fresh2021'])
        self.assertEqual(len(report['matched']), 1)
        self.assertIn('ExistingStrang', report['comments_updated'])
        self.assertIn('@COMMENT{jabref-meta: databaseType:bibtex;}', updated)
        self.assertIn('file = {keep.pdf}', updated)
        self.assertIn('comment = {Existing review\n\nNew reading advice}', updated)
        self.assertIn('Fresh2021', updated)
        self.assertEqual(len(mod.parse_bib(updated)), 3)
        again, again_report = mod.merge(updated, SOURCE)
        self.assertEqual(again, updated)
        self.assertEqual(again_report['added'], [])

    def test_conflicting_doi(self):
        conflict = SOURCE.replace('10.1137/0705041', '10.9999/other')
        # Title/year same but DOI conflicts
        updated, report = mod.merge(ORIGINAL, conflict)
        self.assertEqual(updated, ORIGINAL)
        self.assertTrue(report['conflicts'])

    def test_key_collision(self):
        source = '''@article{Keep2020, title={A wholly different paper}, year={2024}}'''
        updated, report = mod.merge(ORIGINAL, source)
        self.assertEqual(updated, ORIGINAL)
        self.assertTrue(report['conflicts'])

    def test_metadata_unchanged_except_annotation(self):
        updated, _ = mod.merge(ORIGINAL, SOURCE)
        self.assertIn(ORIGINAL.split('@article{ExistingStrang')[0], updated)

    def test_invalid_unclosed(self):
        with self.assertRaises(mod.BibError):
            mod.parse_bib('@article{a, title={unclosed}')

    def test_note_add_and_idempotency(self):
        original = '@article{A, title={One}, year={2001}}'
        source = '@article{B, title={One}, year={2001}}'
        updated, report = mod.merge(original, source, 'B', 'Read first.\nThen verify.')
        self.assertIn('comment = {Read first.\nThen verify.}', updated)
        updated2, _ = mod.merge(updated, source, 'B', 'Read first.\nThen verify.')
        self.assertEqual(updated, updated2)

    def test_read_crlf(self):
        initial = '@article{A,\r\n  title = {One},\r\n  year = {2000}\r\n}\r\n'
        source = '@article{B, title = {Two}, year = {2001}}'
        updated, report = mod.merge(initial, source)
        self.assertIn('\r\n', updated)
        self.assertEqual(len(mod.parse_bib(updated)), 2)

    def test_apply_creates_backup(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'library.bib'
            target.write_text(ORIGINAL, encoding='utf-8')
            updated, _ = mod.merge(ORIGINAL, SOURCE)
            backup = mod._write_atomic(target, updated, ORIGINAL, True)
            self.assertTrue(Path(backup).exists())
            self.assertEqual(Path(backup).read_text(encoding='utf-8'), ORIGINAL)
            self.assertEqual(target.read_text(encoding='utf-8'), updated)

if __name__ == '__main__':
    unittest.main()
