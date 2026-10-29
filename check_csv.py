#!/usr/bin/env python3
import argparse
import csv
import io
import sys
from collections import defaultdict


def show_lines(lines):
    shown = ', '.join(str(line) for line in lines[:10])
    return shown if shown else '无'


def main():
    parser = argparse.ArgumentParser(description='检查 CSV 文件的数据质量')
    parser.add_argument('path', help='CSV 文件路径')
    args = parser.parse_args()
    try:
        raw = open(args.path, 'rb').read()
        try:
            content = raw.decode('utf-8-sig', errors='strict')
        except UnicodeDecodeError:
            content = raw.decode('gb18030', errors='strict')
            if content.encode('gb18030', errors='strict') != raw:
                raise UnicodeError('GB18030 无法无损往返，编码不确定')
        if any(ord(c) < 32 and c not in '\t\r\n' for c in content):
            raise UnicodeError('包含异常控制字符，编码或数据不确定')
        with io.StringIO(content, newline='') as file:
            reader = csv.reader(file, strict=True)
            header = next(reader, None)
            if header is None:
                print('错误：CSV 文件为空，没有表头。', file=sys.stderr)
                return 1
            missing = [0] * len(header)
            seen_rows = {}
            duplicates = []
            first_values = defaultdict(list)
            bad_lines = []
            count = 0
            previous_end = reader.line_num
            for row in reader:
                line = previous_end + 1
                previous_end = reader.line_num
                count += 1
                if len(row) != len(header):
                    bad_lines.append(line)
                for index, value in enumerate(row[:len(header)]):
                    if value == '':
                        missing[index] += 1
                row_key = tuple(row)
                if row_key in seen_rows:
                    duplicates.append(line)
                else:
                    seen_rows[row_key] = line
                if row:
                    first_values[row[0]].append(line)
            repeated_values = [(value, lines) for value, lines in first_values.items() if len(lines) > 1]
            print(f'总行数（不含表头）：{count}')
            print(f'列数：{len(header)}')
            print('每列缺失值数量（仅统计空字符串）：')
            for index, name in enumerate(header):
                print(f'  第 {index + 1} 列 {name}：{missing[index]}')
            print(f'完全重复的行数：{len(duplicates)}；行号：{show_lines(duplicates)}')
            duplicate_lines = sorted(line for _, lines in repeated_values for line in lines[1:])
            print(f'第一列重复值个数（不同的值）：{len(repeated_values)}；重复行号：{show_lines(duplicate_lines)}')
            print(f'列数与表头不一致的坏行数：{len(bad_lines)}；行号：{show_lines(bad_lines)}')
            print('行号从文件第一行表头开始计数，每项最多显示 10 个行号。')
            return 0
    except (OSError, UnicodeError, csv.Error) as error:
        print(f'错误：{error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
