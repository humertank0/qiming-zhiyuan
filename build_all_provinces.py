#!/usr/bin/env python3
"""暴力全解析——不再纠结表头格式，扫描所有Excel找出学校+分数/位次"""

import os, re, sqlite3, xlrd, openpyxl, time

DATA_DIR = r'E:\桌面\高考志愿填报'
DB_PATH = r'E:\桌面\启明志愿\all_provinces.db'

# 省份关键词（按优先级，长的在前避免误匹配）
PROVINCES = ['黑龙江','内蒙古','北京','天津','上海','重庆','河北','山西','辽宁','吉林',
             '江苏','浙江','安徽','福建','江西','山东','河南','湖北','湖南',
             '广东','广西','海南','四川','贵州','云南','西藏','陕西','甘肃',
             '青海','宁夏','新疆']

def detect_province(filepath):
    """从文件路径中提取省份名"""
    for p in PROVINCES:
        if p in filepath:
            return p
    return '其他'

def detect_year(fpath):
    """从路径和文件名中提取年份"""
    for y in range(2025, 2016, -1):
        if str(y) in fpath:
            return y
    return 2024

def parse_cell(v):
    """归一化单元格值"""
    if v is None:
        return ''
    if isinstance(v, float):
        if v == int(v):
            return str(int(v))
        return str(v)
    return str(v).strip()

def find_school_name(text):
    """从文本中提取学校名——找大学/学院结尾的片段"""
    # 去掉前导代码 A001等
    text = re.sub(r'^[A-Z]\d+\s*', '', text)
    # 如果有大学或学院结尾，优先取最后一段
    parts = re.split(r'[（(]', text)
    name = parts[0].strip()
    if name and len(name) >= 3:
        return name
    return text

def brute_parse_xlsx(filepath):
    """暴力解析xlsx：找到所有包含数字的列，猜学校/分数/位次"""
    results = []
    try:
        wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
        for ws in wb.worksheets:
            # 批量读取所有行（iter_rows比逐格cell()快100倍）
            all_rows = []
            for row in ws.iter_rows(max_col=20, values_only=True):
                all_rows.append([parse_cell(v) for v in row])
            nrows = len(all_rows)
            if nrows < 3:
                continue
            ncols = len(all_rows[0]) if all_rows else 0

            # 策略：扫描所有行，找同时包含"大学"或"学院" + 数字的行
            school_idx = None
            score_idx = None
            rank_idx = None

            # 先找表头来确定列位置
            for r in range(min(10, len(all_rows))):
                row_text = ' '.join(all_rows[r])
                for c, val in enumerate(all_rows[r]):
                    clean = val.lower().replace('\n', '')
                    if '院校名称' in clean or '学校名称' in clean:
                        school_idx = c
                    elif school_idx is None and ('院校' in clean and '代号' not in clean):
                        school_idx = c
                    if '投档最低分' in clean or '最低投档分' in clean:
                        score_idx = c
                    elif score_idx is None and '投档分' in clean:
                        score_idx = c
                    elif score_idx is None and ('最低分' in clean and '同分' not in clean):
                        score_idx = c
                    if '最低位次' in clean:
                        rank_idx = c
                    elif rank_idx is None and '位次' in clean:
                        rank_idx = c

            # 如果表头法失败了，用启发式：第一列是学校名（含大学/学院），后面某列是数字
            if school_idx is None:
                for c in range(min(ncols, 5)):
                    for r in range(min(20, len(all_rows))):
                        if '大学' in all_rows[r][c] or '学院' in all_rows[r][c]:
                            school_idx = c
                            break
                    if school_idx is not None:
                        break

            # 如果学校列也没找到，跳过这个sheet
            if school_idx is None:
                continue

            # 找出分数列（数值列，且值在300-750之间）
            if score_idx is None:
                score_counts = {}
                for c in range(min(ncols, 10)):
                    if c == school_idx:
                        continue
                    count = 0
                    for r in range(5, min(50, len(all_rows))):
                        try:
                            v = float(all_rows[r][c])
                            if 300 <= v <= 750:
                                count += 1
                        except:
                            pass
                    if count >= 5:
                        score_counts[c] = count
                if score_counts:
                    score_idx = max(score_counts, key=score_counts.get)

            # 找位次列（大整数，通常在100-999999范围）
            if rank_idx is None:
                rank_counts = {}
                for c in range(min(ncols, 10)):
                    if c == school_idx or c == score_idx:
                        continue
                    count = 0
                    for r in range(5, min(50, len(all_rows))):
                        try:
                            v = float(all_rows[r][c])
                            if 100 <= v <= 999999:
                                count += 1
                        except:
                            pass
                    if count >= 5:
                        rank_counts[c] = count
                if rank_counts:
                    rank_idx = max(rank_counts, key=rank_counts.get)

            # 解析数据行
            for r in range(len(all_rows)):
                row = all_rows[r]
                if school_idx >= len(row):
                    continue
                school_raw = row[school_idx]
                if not school_raw or len(school_raw) < 3:
                    continue
                if any(kw in school_raw for kw in ['注', '说明', '合计', '代号', '页码']):
                    continue

                school = find_school_name(school_raw)
                if '大学' not in school and '学院' not in school:
                    continue

                score = None
                if score_idx is not None and score_idx < len(row):
                    try:
                        s = float(row[score_idx])
                        if 300 <= s <= 750:
                            score = int(s)
                    except:
                        pass

                rank = None
                if rank_idx is not None and rank_idx < len(row):
                    try:
                        rk = float(row[rank_idx])
                        # 位次>750(非分数范围)且>=100
                        if rk >= 100 and (rk > 750 or rk < 300):
                            rank = int(rk)
                    except:
                        pass

                if school and (score is not None or rank is not None):
                    # 提取专业（如果有的话，通常在school后面一列）
                    major = ''
                    if school_idx + 1 < len(row) and school_idx + 1 != score_idx:
                        v = row[school_idx + 1]
                        if v and not any(kw in v for kw in ['专业', '代号', '名称']):
                            major = re.sub(r'^\d+\s*', '', v).strip()

                    results.append({
                        'school': school,
                        'major': major[:30] if major else '',
                        'score': score,
                        'rank': rank,
                    })

        wb.close()
    except Exception as e:
        pass
    return results

def brute_parse_xls(filepath):
    """暴力解析xls"""
    results = []
    try:
        wb = xlrd.open_workbook(filepath)
        for si in range(wb.nsheets):
            ws = wb.sheet_by_index(si)
            nrows, ncols = ws.nrows, min(ws.ncols, 20)
            if nrows < 3:
                continue

            all_rows = []
            for r in range(nrows):
                row = [parse_cell(ws.cell_value(r, c)) for c in range(ncols)]
                all_rows.append(row)

            school_idx = score_idx = rank_idx = None

            # 找表头
            for r in range(min(10, len(all_rows))):
                for c, val in enumerate(all_rows[r]):
                    clean = val.lower().replace('\n', '')
                    if school_idx is None and ('院校名称' in clean or '学校名称' in clean or (('院校' in clean or '学校' in clean) and '代号' not in clean)):
                        school_idx = c
                    if score_idx is None and ('投档最低分' in clean or '最低分' in clean or '分数线' in clean):
                        score_idx = c
                    if rank_idx is None and '位次' in clean:
                        rank_idx = c

            # 启发式找列
            if school_idx is None:
                for c in range(min(5, ncols)):
                    for r in range(3, min(15, nrows)):
                        if '大学' in all_rows[r][c] or '学院' in all_rows[r][c]:
                            school_idx = c
                            break
                    if school_idx is not None:
                        break

            if school_idx is None:
                continue

            if score_idx is None:
                best, best_c = 0, None
                for c in range(min(10, ncols)):
                    if c == school_idx:
                        continue
                    cnt = 0
                    for r in range(3, min(30, nrows)):
                        try:
                            v = float(all_rows[r][c])
                            if 300 <= v <= 750:
                                cnt += 1
                        except:
                            pass
                    if cnt > best:
                        best, best_c = cnt, c
                if best >= 3:
                    score_idx = best_c

            if rank_idx is None:
                best, best_c = 0, None
                for c in range(min(10, ncols)):
                    if c == school_idx or c == score_idx:
                        continue
                    cnt = 0
                    for r in range(3, min(30, nrows)):
                        try:
                            v = float(all_rows[r][c])
                            if 100 <= v <= 999999:
                                cnt += 1
                        except:
                            pass
                    if cnt > best:
                        best, best_c = cnt, c
                if best >= 3:
                    rank_idx = best_c

            for r in range(len(all_rows)):
                row = all_rows[r]
                if school_idx >= len(row):
                    continue
                school_raw = row[school_idx]
                if not school_raw or len(school_raw) < 3:
                    continue
                if any(kw in school_raw for kw in ['注', '说明', '合计', '代号', '页码', '院校', '学校', '专业']):
                    continue

                school = find_school_name(school_raw)
                if '大学' not in school and '学院' not in school:
                    continue

                score = None
                if score_idx is not None and score_idx < len(row):
                    try:
                        s = float(row[score_idx])
                        if 300 <= s <= 750:
                            score = int(s)
                    except:
                        pass

                rank = None
                if rank_idx is not None and rank_idx < len(row):
                    try:
                        rk = float(row[rank_idx])
                        # 位次>750(非分数范围)且>=100
                        if rk >= 100 and (rk > 750 or rk < 300):
                            rank = int(rk)
                    except:
                        pass

                if school and (score is not None or rank is not None):
                    major = ''
                    if school_idx + 1 < len(row) and school_idx + 1 != score_idx and school_idx + 1 != rank_idx:
                        v = row[school_idx + 1]
                        if v and '大学' not in v and '学院' not in v:
                            major = re.sub(r'^\d+\s*', '', v).strip()

                    results.append({
                        'school': school,
                        'major': major[:30] if major else '',
                        'score': score,
                        'rank': rank,
                    })

        wb.release_resources()
    except Exception as e:
        pass
    return results

def build():
    """构建全量数据库"""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE admission (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            province TEXT, year INTEGER, school TEXT, major TEXT,
            score INTEGER, rank INTEGER, source TEXT
        )
    """)
    conn.execute("CREATE INDEX idx_p ON admission(province)")
    conn.execute("CREATE INDEX idx_s ON admission(school)")

    total, files_done = 0, 0

    for root, dirs, files in os.walk(DATA_DIR):
        for fname in files:
            if not fname.endswith(('.xls', '.xlsx')):
                continue
            if fname.startswith('~'):
                continue
            filepath = os.path.join(root, fname)
            province = detect_province(filepath)
            year = detect_year(filepath)

            results = []
            if filepath.endswith('.xlsx'):
                results = brute_parse_xlsx(filepath)
            else:
                results = brute_parse_xls(filepath)

            for r in results:
                conn.execute(
                    "INSERT INTO admission(province, year, school, major, score, rank, source) VALUES (?,?,?,?,?,?,?)",
                    (province, year, r['school'], r['major'], r['score'], r['rank'], fname[:50])
                )
                total += 1

            files_done += 1
            if files_done % 500 == 0:
                print(f'  {files_done} files, {total} records...')

    conn.commit()
    prov_count = conn.execute("SELECT COUNT(DISTINCT province) FROM admission").fetchone()[0]
    rank_count = conn.execute("SELECT COUNT(*) FROM admission WHERE rank IS NOT NULL AND rank > 0").fetchone()[0]
    conn.close()
    print(f'\nDone: {files_done} files, {total} records, {prov_count} provinces, {rank_count} with rank')
    return total

if __name__ == '__main__':
    t0 = time.time()
    build()
    print(f'Time: {time.time()-t0:.0f}s')
