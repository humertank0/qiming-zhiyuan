#!/usr/bin/env python3
"""一键构建全国高考录取数据库 — 从桌面高考志愿填报文件夹"""

import os, sys, re, sqlite3, xlrd, openpyxl, time

DATA_DIR = r'E:\桌面\高考志愿填报'
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'admission_data.db')

def parse_any_excel(filepath):
    """智能解析任意Excel文件，自动识别表头和数据行"""
    results = []
    try:
        if filepath.endswith('.xls'):
            try:
                wb = xlrd.open_workbook(filepath)
                ws = wb.sheet_by_index(0)
                nrows, ncols = ws.nrows, ws.ncols
                def get_val(r, c):
                    v = ws.cell_value(r, c)
                    if isinstance(v, float) and v == int(v):
                        return str(int(v))
                    return str(v).strip() if v else ''
            except:
                return parse_xlsx(filepath)
        else:
            return parse_xlsx(filepath)

        # 找表头行：至少包含两个关键词才算表头（避免标题行冒充）
        header_row = 0
        for r in range(min(30, nrows)):
            row_text = ' '.join([get_val(r, c) for c in range(min(10, ncols))])
            matched = [kw for kw in ['院校', '学校', '专业', '分数', '位次', '计划'] if kw in row_text]
            if len(matched) >= 2:
                header_row = r
                break

        # 定位列
        headers = [get_val(header_row, c) for c in range(min(10, ncols))]
        col_school = col_major = col_score = col_rank = col_quota = None

        for i, h in enumerate(headers):
            hl = h.lower().replace('\n', '').replace('\r', '')  # 去掉换行符
            if col_school is None and ('院校名称' in hl or '学校名称' in hl or ('院校' in hl and '代号' not in hl) or ('学校' in hl and '代号' not in hl)):
                col_school = i
            if col_major is None and ('专业名称' in hl or ('专业' in hl and '代号' not in hl)):
                col_major = i
            if col_rank is None and any(kw in hl for kw in ['最低位次', '位次', '名次', '排名']):
                col_rank = i
            if col_score is None and any(kw in hl for kw in ['投档最低分', '最低分', '投档分', '分数线']):
                col_score = i
            if col_quota is None and any(kw in hl for kw in ['计划', '人数']):
                col_quota = i

        if col_school is None:
            col_school = 0

        for r in range(header_row + 1, nrows):
            school_raw = get_val(r, col_school)
            if not school_raw or len(school_raw) < 2:
                continue
            if any(kw in school_raw for kw in ['注', '说明', '合计', '共计']):
                continue

            # 清理学校名：去掉前导代码 "A001北京大学" → "北京大学"
            # 匹配模式：字母+数字+空格开头
            school = re.sub(r'^[A-Z]\d+\s*', '', school_raw).strip()
            if not school or len(school) < 2:
                school = school_raw.strip()

            major = get_val(r, col_major) if col_major is not None else ''
            # 去掉专业名前面的数字代号
            major = re.sub(r'^[A-Za-z0-9]+\s*', '', major).strip()

            score_str = get_val(r, col_score) if col_score is not None else ''
            rank_str = get_val(r, col_rank) if col_rank is not None else ''
            quota_str = get_val(r, col_quota) if col_quota is not None else ''

            # 处理特殊值
            score = rank = quota = None
            try:
                if score_str and score_str.replace('.', '').replace('-', '').isdigit():
                    score = int(float(score_str))
            except: pass
            try:
                if rank_str and rank_str.replace('.', '').isdigit():
                    rank = int(float(rank_str))
            except: pass
            try:
                if quota_str and quota_str.replace('.', '').isdigit():
                    quota = int(float(quota_str))
            except: pass

            if school and (score is not None or rank is not None):
                results.append({
                    'school': school,
                    'major': major,
                    'score': score,
                    'rank': rank,
                    'quota': quota,
                })

        if hasattr(wb, 'release_resources'):
            wb.release_resources()
        return results
    except Exception as e:
        return []

def parse_xlsx(filepath):
    """解析.xlsx文件"""
    results = []
    try:
        wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
        ws = wb.active
        nrows, ncols = ws.max_row, ws.max_column
        def get_val(r, c):
            v = ws.cell(r, c).value
            if v is None:
                return ''
            if isinstance(v, float) and v == int(v):
                return str(int(v))
            return str(v).strip()

        # Same logic as above
        header_row = 0
        for r in range(min(30, nrows)):
            row_text = ' '.join([get_val(r, c) for c in range(1, min(10, ncols+1))])
            if any(kw in row_text for kw in ['院校', '学校', '投档', '分数', '位次', '计划']):
                header_row = r
                break

        headers = [get_val(header_row, c) for c in range(1, min(10, ncols+1))]
        col_map = {}
        for i, h in enumerate(headers):
            i += 1
            hl = h.lower().replace('\n', '').replace('\r', '')  # 去掉换行符
            # 院校列：只取第一个，不覆盖
            if col_map.get('school') is None and ('院校名称' in hl or '学校名称' in hl or ('院校' in hl and '代号' not in hl)):
                col_map['school'] = i
            # 专业列：优先名称
            if col_map.get('major') is None and ('专业名称' in hl or ('专业' in hl and '代号' not in hl)):
                col_map['major'] = i
            # 分数列：优先匹配含"最低"的
            if col_map.get('score') is None and any(kw in hl for kw in ['投档最低分', '最低分', '投档分', '分数线', '投档线']):
                col_map['score'] = i
            # 位次列
            if col_map.get('rank') is None and any(kw in hl for kw in ['最低位次', '位次', '名次', '排名']):
                col_map['rank'] = i
            # 计划列
            if col_map.get('quota') is None and any(kw in hl for kw in ['计划', '人数']):
                col_map['quota'] = i

        if 'school' not in col_map:
            col_map['school'] = 1

        for r in range(header_row + 1, nrows + 1):
            school = get_val(r, col_map.get('school', 1))
            if not school or len(school) < 2:
                continue
            if school.startswith('注') or school.startswith('说明'):
                continue

            major = get_val(r, col_map['major']) if 'major' in col_map else ''
            score_str = get_val(r, col_map['score']) if 'score' in col_map else ''
            rank_str = get_val(r, col_map['rank']) if 'rank' in col_map else ''
            quota_str = get_val(r, col_map['quota']) if 'quota' in col_map else ''

            try:
                score = int(float(score_str)) if score_str else None
            except:
                score = None
            try:
                rank = int(float(rank_str)) if rank_str else None
            except:
                rank = None
            try:
                quota = int(float(quota_str)) if quota_str else None
            except:
                quota = None

            school = re.sub(r'^\d+\s*', '', school)
            school = re.sub(r'[（(][^)）]*[)）]$', '', school)
            major = re.sub(r'^\d+\s*', '', major)

            if school and (score or rank):
                results.append({
                    'school': school.strip(),
                    'major': major.strip() if major else '',
                    'score': score,
                    'rank': rank,
                    'quota': quota,
                })

        wb.close()
        return results
    except Exception as e:
        return []

def build_all(progress_callback=None):
    """构建完整数据库"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS admission")
    conn.execute("""
        CREATE TABLE admission (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            province TEXT,
            year INTEGER,
            school TEXT,
            major TEXT,
            score INTEGER,
            rank INTEGER,
            quota INTEGER,
            source_file TEXT
        )
    """)
    conn.execute("CREATE INDEX idx_province ON admission(province)")
    conn.execute("CREATE INDEX idx_school ON admission(school)")
    conn.execute("CREATE INDEX idx_score ON admission(score)")
    conn.execute("CREATE INDEX idx_rank ON admission(rank)")
    conn.execute("CREATE INDEX idx_major ON admission(major)")

    total = 0
    files_processed = 0

    for root, dirs, files in os.walk(DATA_DIR):
        for fname in files:
            if not fname.endswith(('.xls', '.xlsx')):
                continue
            if fname.startswith('~'):
                continue

            filepath = os.path.join(root, fname)

            # 推断省份：搜全路径（含文件夹名和文件名）
            province = '未知'
            full_path_text = root + '/' + fname
            PROV_LIST = ['北京','天津','上海','重庆','河北','山西','辽宁','吉林','黑龙江',
                         '江苏','浙江','安徽','福建','江西','山东','河南','湖北','湖南',
                         '广东','广西','海南','四川','贵州','云南','西藏','陕西','甘肃',
                         '青海','宁夏','新疆','内蒙古']
            for p in PROV_LIST:
                if p in full_path_text:
                    province = p
                    break
            # 年份检测
            year = 2024
            for y in ['2025','2024','2023','2022','2021','2020','2019','2018','2017']:
                if y in fname or y in root:
                    year = int(y)
                    break
            if year == 2024 and '25年' in root:
                year = 2025

            # 处理投档/录取/分数/一分一段等所有高考数据（同时检查文件名和路径）
            full_text = fname + root
            if not any(kw in full_text for kw in ['投档', '录取', '分数线', '分数', '一分一段', '分段表', '招生计划', '高考']):
                # 但文件名是纯年份（如2023.xlsx）且路径含省份名→一分一段表，放行
                is_year_file = re.match(r'^\d{4}\.xls', fname)
                if not is_year_file:
                    continue

            results = parse_any_excel(filepath)
            for r in results:
                if r['school'] and (r['score'] or r['rank']):
                    conn.execute(
                        "INSERT INTO admission(province, year, school, major, score, rank, quota, source_file) VALUES (?,?,?,?,?,?,?,?)",
                        (province, year, r['school'], r['major'], r['score'], r['rank'], r['quota'], fname)
                    )
                    total += 1

            files_processed += 1
            if files_processed % 50 == 0:
                print(f'  {files_processed} files, {total} records...')

    conn.commit()

    # 统计
    prov_count = conn.execute("SELECT COUNT(DISTINCT province) FROM admission").fetchone()[0]
    school_count = conn.execute("SELECT COUNT(DISTINCT school) FROM admission").fetchone()[0]
    major_count = conn.execute("SELECT COUNT(DISTINCT major) FROM admission WHERE major != ''").fetchone()[0]
    has_rank = conn.execute("SELECT COUNT(*) FROM admission WHERE rank IS NOT NULL").fetchone()[0]
    has_score = conn.execute("SELECT COUNT(*) FROM admission WHERE score IS NOT NULL").fetchone()[0]

    conn.close()

    print(f'\n===== 数据库构建完成 =====')
    print(f'文件处理: {files_processed}')
    print(f'总记录数: {total}')
    print(f'覆盖省份: {prov_count}')
    print(f'覆盖学校: {school_count}')
    print(f'覆盖专业: {major_count}')
    print(f'有位次数据: {has_rank}')
    print(f'有分数数据: {has_score}')

    return total

if __name__ == "__main__":
    t0 = time.time()
    build_all()
    print(f'\n耗时: {time.time()-t0:.0f}秒')
    print(f'数据库: {DB_PATH}')
