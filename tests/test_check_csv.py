import csv
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'check_csv.py'

def run_bytes(data):
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / 'case.csv'
        path.write_bytes(data)
        return subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)

class Checks(unittest.TestCase):
    def assert_report(self, data, expected):
        result = run_bytes(data.encode('utf-8'))
        self.assertEqual(result.returncode, 0, result.stderr)
        for phrase in expected:
            self.assertIn(phrase, result.stdout)

    def test_01_standard(self):
        self.assert_report('id,name\n1,A\n2,B\n', ['总行数（不含表头）：2','列数：2','完全重复的行数：0','坏行数：0'])
    def test_02_blank_line(self):
        self.assert_report('id,name\n1,A\n\n2,B\n', ['总行数（不含表头）：3','坏行数：1；行号：3'])
    def test_03_numeric(self):
        self.assert_report('id,value\n1,42\n2,0\n', ['总行数（不含表头）：2','第 2 列 value：0','坏行数：0'])
    def test_04_dates(self):
        self.assert_report('id,date\n1,2026-10-27\n2,2026-11-01\n', ['总行数（不含表头）：2','第 2 列 date：0'])
    def test_05_500_rows(self):
        self.assert_report('id,value\n' + ''.join(f'{i},{i*2}\n' for i in range(500)), ['总行数（不含表头）：500','完全重复的行数：0'])
    def test_06_missing(self):
        self.assert_report('id,name,city\n1,,X\n2,A,\n', ['第 2 列 name：1','第 3 列 city：1'])
    def test_07_duplicate_rows(self):
        self.assert_report('id,name\n1,A\n1,A\n', ['完全重复的行数：1；行号：3'])
    def test_08_duplicate_first(self):
        self.assert_report('id,name\n1,A\n1,B\n', ['第一列重复值个数（不同的值）：1；重复行号：3','完全重复的行数：0'])
    def test_09_bad_row(self):
        self.assert_report('id,name\n1,A\n2\n', ['坏行数：1；行号：3'])
    def test_10_gb18030(self):
        result=run_bytes('编号,姓名\n1,小明\n'.encode('gb18030'))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('总行数（不含表头）：1',result.stdout)

if __name__ == '__main__': unittest.main(verbosity=2)
