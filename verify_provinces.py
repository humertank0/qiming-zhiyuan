#!/usr/bin/env python3
"""逐省验证录取数据准确性"""
import sqlite3, random, sys
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'E:\桌面\启明志愿\all_provinces.db'
conn = sqlite3.connect(DB_PATH)

PROVINCES = ['河南','河北','山东','贵州','浙江','安徽','广西','山西','江西','广东',
             '湖南','云南','重庆','甘肃','四川','内蒙古','黑龙江','陕西','福建',
             '江苏','湖北','辽宁','吉林','新疆','海南','宁夏','天津','上海','北京']

KNOWN_SCHOOLS = {
    '浙江': '浙江大学', '江苏': '南京大学', '上海': '复旦大学', '北京': '北京大学',
    '山东': '山东大学', '湖北': '武汉大学', '湖南': '中南大学', '广东': '中山大学',
    '四川': '四川大学', '陕西': '西安交通大学', '福建': '厦门大学',
    '天津': '南开大学', '安徽': '中国科学技术大学', '黑龙江': '哈尔滨工业大学',
    '吉林': '吉林大学', '辽宁': '大连理工大学', '重庆': '重庆大学',
    '甘肃': '兰州大学', '河南': '郑州大学', '河北': '河北工业大学',
    '山西': '太原理工大学', '江西': '南昌大学', '广西': '广西大学',
    '云南': '云南大学', '贵州': '贵州大学', '内蒙古': '内蒙古大学',
    '新疆': '新疆大学', '海南': '海南大学', '宁夏': '宁夏大学',
}

failed = []
passed = []

for prov in PROVINCES:
    school_hint = KNOWN_SCHOOLS.get(prov, '')

    # 找该省有rank的学校-专业组合
    if school_hint:
        rows = conn.execute(
            "SELECT school, major, score, rank, year FROM admission WHERE province=? AND school LIKE ? AND rank>0 ORDER BY rank LIMIT 5",
            (prov, f'%{school_hint}%')
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT school, major, score, rank, year FROM admission WHERE province=? AND rank>0 ORDER BY rank LIMIT 5",
            (prov,)
        ).fetchall()

    if not rows:
        # 放宽条件
        rows = conn.execute(
            "SELECT school, major, score, rank, year FROM admission WHERE province=? AND score>0 ORDER BY score DESC LIMIT 5",
            (prov,)
        ).fetchall()

    if rows:
        # 检查合理性
        issues = []
        for r in rows:
            school, major, score, rank, year = r
            if rank and (rank < 1 or rank > 2000000):
                issues.append(f'rank异常: {rank}')
            if score and (score < 200 or score > 750):
                issues.append(f'score异常: {score}')

        sample = rows[0]
        status = 'PASS'
        if issues:
            status = f'WARN: {"; ".join(issues)}'
            failed.append((prov, issues))
        else:
            passed.append(prov)

        rank_str = f'位次{sample[3]}' if sample[3] else ''
        score_str = f'{sample[2]}分' if sample[2] else ''
        print(f'[{status}] {prov:6s} | {sample[0][:22]:22s} | {sample[1][:22]:22s} | {score_str:6s} | {rank_str:8s} | {sample[4]}年')
    else:
        print(f'[FAIL] {prov:6s} | 无数据')
        failed.append((prov, ['无数据']))

print(f'\n==========')
print(f'通过: {len(passed)}省')
print(f'失败: {len(failed)}省')
if failed:
    print('失败详情:')
    for prov, issues in failed:
        print(f'  {prov}: {issues}')

conn.close()
