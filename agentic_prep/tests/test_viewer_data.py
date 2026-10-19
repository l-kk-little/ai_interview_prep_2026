"""Build the real viewer generator in an isolated anonymous fixture."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class ViewerDataTests(unittest.TestCase):
    def test_rebuild_is_offline_complete_safe_and_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            viewer = root / 'viewer'
            viewer.mkdir()
            source = Path(__file__).resolve().parents[1] / 'viewer/build_data.py'
            shutil.copy(source, viewer / source.name)
            texts = {'README.md': '# Start\n[a](DEPENDENCIES.md)',
                     'DEPENDENCIES.md': '# Dependencies\n</script>\u2028',
                     '01_core/a.md': '# Core'}
            for name, text in texts.items():
                path = root / name
                path.parent.mkdir(exist_ok=True)
                path.write_text(text, encoding='utf-8')
            command = [sys.executable, str(viewer / source.name)]
            subprocess.run(command, check=True, capture_output=True)
            data = (viewer / 'data.js').read_text(encoding='utf-8')
            docs = json.loads(data.split('window.A2_DOCS = ', 1)[1].rstrip(';\n'))
            self.assertEqual(texts, {d['path']: d['content'] for d in docs})
            self.assertEqual('README.md', docs[0]['path'])
            self.assertNotIn('</script>', data)
            subprocess.run(command, check=True, capture_output=True)
            self.assertEqual(data, (viewer / 'data.js').read_text(encoding='utf-8'))
