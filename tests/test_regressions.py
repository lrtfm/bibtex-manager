from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_bibtex_manager import mod, SCRIPT


class RegressionTests(unittest.TestCase):
    def test_incoming_duplicates_keep_all_notes(self):
        incoming = '''@article{A, title={One}, year={2000}, comment={First}}
@article{B, title={One}, year={2000}, comment={Second}}'''
        output, report = mod.merge('', incoming, 'A', 'Extra')
        self.assertEqual(report['added'], ['A'])
        self.assertEqual(len(mod.parse_bib(output)), 1)
        self.assertEqual(mod.parse_bib(output)[0].field('comment'), 'First\n\nExtra\n\nSecond')
        again, _ = mod.merge(output, incoming, 'A', 'Extra')
        self.assertEqual(again, output)

    def test_unknown_comment_key_rejected(self):
        with self.assertRaises(mod.BibError):
            mod.merge('', '@article{A,title={One}}', 'Missing', 'Note')

    def test_comment_cannot_close_entry_early(self):
        for note in ('}{', 'note} , title={other'):
            with self.subTest(note=note), self.assertRaises(mod.BibError):
                mod.merge('', '@article{A,title={One}}', 'A', note)

    def test_escaped_brace_is_valid_comment(self):
        output, _ = mod.merge('', '@article{A,title={One}}', 'A', r'Use \{ here')
        self.assertIn(r'Use \{ here', output)

    def test_literal_quote_in_braced_title(self):
        entries = mod.parse_bib('@article{A,title={An unmatched " quote},year={2000}}')
        self.assertEqual(entries[0].field('year'), '2000')

    def test_changed_target_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'a.bib'
            p.write_text('Changed by another editor')
            with self.assertRaises(mod.BibError):
                mod._write_atomic(p, 'replacement', 'original', True)
            self.assertEqual(p.read_text(), 'Changed by another editor')
            self.assertEqual(list(Path(d).glob('*.bak.*')), [])


class CLITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.target = self.root/'target.bib'
        self.source = self.root/'source.bib'
        self.original = b'\xef\xbb\xbf@COMMENT{jabref-meta: databaseType:bibtex;}\r\n@article{A,title={One},year={2000}}\r\n'
        self.target.write_bytes(self.original)
        self.source.write_text('@article{B,title={Two},year={2001}}')

    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)

    def merge(self, *args):
        return self.cli('merge', '--target', self.target, '--incoming', self.source, *args)

    def test_dry_run_has_no_side_effects(self):
        result = self.merge('--diff')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('DRY RUN', result.stdout)
        self.assertEqual(self.target.read_bytes(), self.original)
        self.assertEqual(sorted(x.name for x in self.root.iterdir()), ['source.bib', 'target.bib'])

    def test_apply_preserves_bytes_and_backup(self):
        result = self.merge('--apply')
        self.assertEqual(result.returncode, 0, result.stderr)
        data = self.target.read_bytes()
        self.assertTrue(data.startswith(self.original))
        self.assertNotIn(b'\n', data.replace(b'\r\n', b''))
        backups = list(self.root.glob('*.bak.*'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), self.original)
        self.assertEqual(self.merge('--apply').returncode, 0)
        self.assertEqual(self.target.read_bytes(), data)
        self.assertEqual(len(list(self.root.glob('*.bak.*'))), 1)

    def test_conflict_aborts_entire_write(self):
        self.source.write_text('@article{Fresh,title={New}}\n@article{A,title={Different},year={2025}}')
        result = self.merge('--apply')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.target.read_bytes(), self.original)
        self.assertEqual(list(self.root.glob('*.bak.*')), [])

    def test_missing_target_requires_create(self):
        self.target.unlink()
        self.assertEqual(self.merge('--apply').returncode, 2)
        self.assertFalse(self.target.exists())
        self.assertEqual(self.merge('--create').returncode, 0)
        self.assertFalse(self.target.exists())
        self.assertEqual(self.merge('--create', '--apply').returncode, 0)
        self.assertEqual(len(mod.parse_bib(self.target.read_text())), 1)

    def test_comment_options_must_be_paired(self):
        self.assertEqual(self.merge('--comment-key', 'B', '--apply').returncode, 2)
        note = self.root/'note.txt'
        note.write_text('')
        self.assertEqual(self.merge('--comment-file', note, '--apply').returncode, 2)
        self.assertEqual(self.target.read_bytes(), self.original)

    def test_invalid_input_and_same_file_rejected(self):
        self.source.write_text('@article{B,title={broken}')
        self.assertEqual(self.merge('--apply').returncode, 2)
        self.assertEqual(self.target.read_bytes(), self.original)
        self.assertEqual(self.cli('merge', '--target', self.target, '--incoming', self.target, '--apply').returncode, 2)

    def test_version(self):
        result = self.cli('--version')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), (SCRIPT.parents[1]/'VERSION').read_text().strip())


if __name__ == '__main__':
    unittest.main()
