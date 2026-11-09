#!/usr/bin/env python3
"""Stash 去广告覆写生成器（2026-11-08 建；GitHub Actions 每天自动运行一次）

合成一份 Stash 覆写：
  1. 秋风广告规则（GitHub TG-Twilight/AWAvenue-Ads-Rule，Clash 完整版）：只写引用地址，
     Stash 每 24 小时自己去 GitHub 取最新名单，命中的广告域名直接拒绝（不需要证书）。
  2. 下列上游覆写（deezertidal/stash-override 转制，发布在 yfamilys.com）的当天快照合并：
     - 墨鱼「APP启动页去广告」：约 170 个 App 的开屏广告（不含 B 站）
     - 「哔哩哔哩去广告」：B 站开屏、信息流等
     只保留脚本来源可核实的：GitHub 仓库原文件，以及 blackmatrix7、ddgksf2013 两位作者的 gist；
     其余来源（如匿名的 Cloudflare Worker）的脚本连同引用一并去掉。

用法：<装了 PyYAML 的 python3> -I build_override.py [输出文件，默认 adblock.stoverride]
仓库里的 .github/workflows/build.yml 每天运行一次，内容有变化就提交；Stash 按网址自动更新。
"""
import collections
import datetime
import re
import sys
import urllib.request

import yaml

UPSTREAMS = [
    ('墨鱼启动页去广告', 'https://yfamilys.com/stoverride/startingad.stoverride'),
    ('B站去广告', 'https://yfamilys.com/stoverride/biliad.stoverride'),
]
QIUFENG = ('https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/'
           'Filters/AWAvenue-Ads-Rule-Clash-Classical.yaml')
TRUSTED_GIST_OWNERS = {'blackmatrix7', 'ddgksf2013'}
NAME = '去广告（秋风＋墨鱼去开屏＋B站）'


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Stash/3.3 Clash/1.11'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode('utf-8')


def source_of(url):
    """返回 (是否可核实, 来源说明)。"""
    m = re.match(r'https?://([^/]+)/([^/]+)', url or '')
    if not m:
        return False, '无法解析'
    host, owner = m.group(1).lower(), m.group(2)
    if host in ('raw.githubusercontent.com', 'github.com'):
        return True, f'GitHub:{owner}'
    if host == 'gist.githubusercontent.com':
        return owner in TRUSTED_GIST_OWNERS, f'gist:{owner}'
    return False, host


def add_unique(dst, items):
    seen = set(map(str, dst))
    for x in items or []:
        if str(x) not in seen:
            dst.append(x)
            seen.add(str(x))


def main(out_path):
    mitm, rewrite, body_rewrite, scripts, providers = [], [], [], [], {}
    report = []
    for label, url in UPSTREAMS:
        data = yaml.safe_load(fetch(url))
        http = data.get('http', {}) or {}
        src_count, dropped = collections.Counter(), set()
        rename = {}
        for name, conf in (data.get('script-providers', {}) or {}).items():
            ok, src = source_of((conf or {}).get('url'))
            src_count[src + ('' if ok else '（去掉）')] += 1
            if not ok:
                dropped.add(name)
                continue
            new = name
            while new in providers and providers[new] != conf:
                new = f'{label}-{new}'
            providers[new] = conf
            rename[name] = new
        kept = []
        for s in http.get('script', []) or []:
            if s.get('name') in dropped:
                continue
            s = dict(s)
            s['name'] = rename.get(s.get('name'), s.get('name'))
            kept.append(s)
        add_unique(mitm, http.get('mitm'))
        add_unique(rewrite, http.get('url-rewrite'))
        add_unique(rewrite, http.get('rewrite'))  # 上游用的旧键名，输出时改成 Stash 文档的 url-rewrite
        add_unique(body_rewrite, http.get('body-rewrite'))
        scripts.extend(kept)
        rw = http.get('rewrite', []) or []
        report.append(f'{label}: 解密 {len(http.get("mitm", []) or [])}，改写 {len(rw)} '
                      f'{dict(collections.Counter(r.split()[-1] for r in rw if isinstance(r, str) and r.split()))}，'
                      f'脚本保留 {len(kept)}、去掉 {len(http.get("script", []) or []) - len(kept)}，来源 {dict(src_count)}')

    today = datetime.date.today().isoformat()
    http_out = {'mitm': mitm, 'url-rewrite': rewrite}
    if body_rewrite:
        http_out['body-rewrite'] = body_rewrite
    http_out['script'] = scripts
    # 安装走「从 URL 安装」：剪贴板粘贴约 5000 字处会被截断（11-08 实测），整份文件不能靠粘贴
    out = {
        'name': NAME,
        'desc': f'秋风广告规则拦广告域名（Stash 每天自动更新）；墨鱼 APP 启动页去广告、B站去广告'
                f'（每天自动从上游重新生成，本版 {today}；已去掉来源无法核实的脚本）。',
        'rule-providers': {
            'AWAvenue-Ads': {'behavior': 'classical', 'format': 'yaml', 'url': QIUFENG, 'interval': 86400},
        },
        'rules': ['RULE-SET,AWAvenue-Ads,REJECT'],
        'http': http_out,
        'script-providers': providers,
    }
    redirects = [r for r in rewrite if isinstance(r, str) and r.split()[-1] in ('302', '307')]

    dumped = yaml.safe_dump(out, allow_unicode=True, sort_keys=False, width=4096)
    check = yaml.safe_load(dumped)  # 再读一遍，确认格式完好
    assert check['rules'] == ['RULE-SET,AWAvenue-Ads,REJECT']
    # 上游大改或抓取残缺时宁可这次不更新，也不提交一份残缺的覆写
    assert len(mitm) > 100 and len(rewrite) > 100 and len(scripts) > 50, f'数量异常：{len(mitm)}/{len(rewrite)}/{len(scripts)}'
    assert all(s.get('name') in check['script-providers'] for s in check['http']['script']), '有脚本引用了不存在的来源'
    assert not any(not source_of(c.get('url'))[0] for c in check['script-providers'].values()), '混进了来源无法核实的脚本'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(f'# 生成：{today}，生成器 build_override.py；上游 {"、".join(u for _, u in UPSTREAMS)}\n')
        f.write(dumped)

    try:
        qf = fetch(QIUFENG)
    except Exception as e:  # 只用于统计，取不到不影响生成
        qf = ''
        print('秋风名单暂时取不到:', e)
    print('输出:', out_path)
    for line in report:
        print(' ', line)
    print('合计: 解密主机', len(mitm), '| 改写', len(rewrite), '| 响应体改写', len(body_rewrite),
          '| 脚本', len(scripts), '| 脚本来源', len(providers))
    print('改写里的跳转（302/307）:', redirects[:5] if redirects else '无')
    print('秋风名单可取到:', qf.count('\n  - '), '条')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'adblock.stoverride')
