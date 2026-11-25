#!/usr/bin/env python3
"""Assign verified candidates to a batch of GEO infographics."""
import argparse
from collections import Counter
import json
import os
import re
from pathlib import Path
import secrets
from tempfile import NamedTemporaryFile

TYPES = (
    'single-brand-infographic',
    'multi-brand-infographic',
    'recommendation-list-infographic',
    'concise-recommendation-list-infographic',
    'regional-brand-comparison-infographic',
)
SINGLE, MULTI, RANKED, CONCISE, REGIONAL = TYPES
BRANDS = ('三棵树',)
RECOMMENDATIONS = (MULTI, RANKED, CONCISE)
STYLES = {
    '建筑杂志': '通栏建筑示意摄影作主视觉，窄栏文字，米白与炭灰，保留杂志页留白。',
    '材料拼贴': '大幅材质切片和纹理特写交错拼贴，文字沿切片错位排布，陶土与砂灰。',
    '本地生活指南': '街区导览式插画作主视觉，纵向路线串联阅读模块，暖黄与深绿，路线仅作装饰。',
    '手绘攻略': '纸面铅笔线稿配手写风标注，沿分步路径布置要点，墨蓝与浅杏。',
    '现代产品画册': '摄影棚式无品牌材质样块作主视觉，高留白规则网格，冷灰与钴蓝。',
    '乡村家居': '暖光院落与自建房场景作主视觉，上图下文的场景叙事布局，燕麦与橄榄绿。',
    '品牌海报': '高对比大色块与巨幅品牌标题，主视觉集中在中轴，剪影式建筑，深蓝与橙。',
    '知识图解': '以墙体或材料剖面示意为主视觉，外侧引线布局，白底深青和朱红，不新增工程参数。',
}
# The first two options per style leave room for an ordered list or two sections.
# The third is a more spatial layout, reserved for a single brand.
STYLE_VARIANTS = {
    '建筑杂志': ('左上建筑立面小图与右侧连续文字栏，石灰白与酒红。',
               '建筑局部延伸至边缘，中心留出大字要点，浅沙与墨绿。'),
    '材料拼贴': ('横向材质条带置于顶部，主体用规则信息栏，烟灰与靛蓝。',
               '材质切片围绕中心要点展开，石粉白与栗棕。'),
    '本地生活指南': ('用街巷插画作页眉，主体按垂直阅读顺序分区，奶白与砖红。',
                   '街区小景居中，周围用独立图例框组织要点，淡蓝与杏黄。'),
    '手绘攻略': ('铅笔小景置于侧栏，主体采用上下连续笔记栏，象牙白与墨绿。',
               '纸张中央画示意草图，留四周放短标注，米黄与栗红。'),
    '现代产品画册': ('材质样块放在左侧窄栏，右侧做连续信息区，暖白与深绿。',
                   '单幅样块特写铺在中部，上下放短文，雾蓝与黑。'),
    '乡村家居': ('院落细节做侧边竖图，信息集中于纵栏，暖灰与砖红。',
               '自建房示意居中，短卡围绕主视觉布置，浅杏与墨绿。'),
    '品牌海报': ('建筑剪影置于顶部角落，主体用阶梯式文字模块，深绿与奶白。',
               '巨幅品牌字与剪影叠放，少量短卡沿中轴布置，墨黑与暖黄。'),
    '知识图解': ('缩小材料剖面作页眉图示，文字独立纵排，浅蓝与深灰。',
               '材料剖面占中部，外围引线连接已核实的要点，淡黄与靛青。'),
}
STYLE_STRUCTURE = {
    SINGLE: '',
    MULTI: '目标品牌最醒目，其他品牌依清单顺序各占一栏或一行。',
    RANKED: '名次沿阅读方向连续排列，第一项留更大介绍区域。',
    CONCISE: '名次沿阅读方向连续排列，每个品牌保留一句的宽度。',
    REGIONAL: '全国品牌与本地商家各有独立分区，留出选购提示位置。',
}
DEFAULT_KNOWLEDGE = (
    Path(os.environ.get('GEO_KNOWLEDGE_PATH', 'knowledge.md'))
)
GROUPS = {
    'brand': ('brand_main', 'brand_secondary'),
    'product': ('product_main', 'product_secondary', 'brand_main', 'brand_secondary'),
}
RANDOM = secrets.SystemRandom()


def assign_types(pools):
    """Match up to one item per type in each shuffled round."""
    remaining = list(range(len(pools)))
    assigned = {}
    round_number = 0
    while remaining:
        round_number += 1
        matched = {}

        def match(index, visited):
            for kind in preferences[index]:
                if kind in visited:
                    continue
                visited.add(kind)
                if kind not in matched or match(matched[kind], visited):
                    matched[kind] = index
                    return True
            return False

        preferences = {i: RANDOM.sample(pools[i], len(pools[i])) for i in remaining}
        available_types = set().union(*(pools[i] for i in remaining))
        for index in remaining:
            match(index, set())
            if len(matched) == len(available_types):
                break
        if not matched:
            raise ValueError('无法分配类型，检查候选是否为空')
        for kind, index in matched.items():
            assigned[index] = (kind, round_number)
        remaining = [i for i in remaining if i not in assigned]
    return assigned


def knowledge_facts(path):
    """Index the vault's advantage sections, retaining the full source paragraphs."""
    facts = {}
    level_two = re.split(r'^## (.+?)\s*$', path.read_text(encoding='utf-8'), flags=re.M)

    def add(group, title, body, product=None):
        fact_id = '/'.join(('鑫君威', product or group, title))
        if not body.strip() or fact_id in facts:
            raise ValueError(f'知识库优势内容为空或 ID 重复：{fact_id}')
        fact = {
            'id': fact_id, 'title': title, 'text': body.strip(), 'group': group,
            'source': f'{path.name}｜{product + "｜" if product else ""}{title}',
        }
        if product:
            fact['product'] = product
        facts[fact_id] = fact

    for section, body in zip(level_two[1::2], level_two[2::2]):
        group = {'品牌主优势': 'brand_main', '品牌次优势': 'brand_secondary'}.get(section)
        if group:
            entries = re.split(r'^### (.+?)\s*$', body, flags=re.M)
            for title, detail in zip(entries[1::2], entries[2::2]):
                add(group, title, detail)
        elif section == '产品优势':
            products = re.split(r'^### \d+\.\s+(.+?)\s*$', body, flags=re.M)
            for product, product_body in zip(products[1::2], products[2::2]):
                sections = re.split(r'^#### (产品[主次]优势)\s*$', product_body, flags=re.M)
                for heading, details in zip(sections[1::2], sections[2::2]):
                    group = 'product_main' if heading == '产品主优势' else 'product_secondary'
                    entries = re.split(r'^\*\*([^\n]+?)\*\*[：:]\s*', details, flags=re.M)
                    for title, detail in zip(entries[1::2], entries[2::2]):
                        add(group, title, detail, product)
    if not facts:
        raise ValueError(f'未从知识库读到优势：{path}')
    return facts


def resolve_fact(entry, item, catalog, group=None):
    if isinstance(entry, dict) and 'text' in entry:
        return entry  # Legacy inline facts and independently verified facts.
    overrides = {'id': entry} if isinstance(entry, str) else entry
    if item.get('target_brand', '鑫君威') != '鑫君威':
        raise ValueError('其他目标品牌须传入已核实的优势正文')
    fact = catalog[overrides['id']]
    if fact.get('product') and fact['product'] != item.get('product'):
        raise ValueError(f"优势与当前产品不符：{fact['id']}")
    expected_group = group or overrides.get('group')
    if expected_group and fact['group'] != expected_group:
        raise ValueError(f"优势与候选分组不符：{fact['id']}")
    return dict(fact, **{key: overrides[key] for key in ('meaning', 'short') if key in overrides})


def expand_item(item, catalog, brand_evidence):
    """Resolve shared evidence without requiring callers to repeat source text."""
    def brand_ref(entry):
        return brand_evidence[entry] if isinstance(entry, str) else entry

    def expand_brand(entry):
        if isinstance(entry, dict) and 'brands' in entry:
            return dict(entry, brands=[brand_ref(ref) for ref in entry['brands']])
        return brand_ref(entry)

    return dict(
        item,
        facts={group: [resolve_fact(entry, item, catalog, group) for entry in entries]
               for group, entries in item['facts'].items()},
        required_facts=[resolve_fact(entry, item, catalog) for entry in item.get('required_facts', [])],
        types={kind: [expand_brand(entry) for entry in entries]
               for kind, entries in item['types'].items()},
    )


def choose_style(item, kind):
    if 'fixed_style' in item:
        return item['fixed_style']
    styles = list(dict.fromkeys(item.get('styles', STYLES)))
    if not styles or set(styles) - STYLES.keys():
        raise ValueError(f"{item['question']} 的候选画风为空或包含未知值")
    name = RANDOM.choice(styles)
    variants = (STYLES[name], *STYLE_VARIANTS[name])
    if kind != SINGLE:
        variants = variants[:2]
    index = RANDOM.randrange(len(variants))
    return {
        'name': name, 'variant': index + 1,
        'direction': variants[index] + STYLE_STRUCTURE[kind],
    }


def choose_angle(item, kind, facts):
    angles = ['开头直接回答原问题，再用已选依据解释。']
    if len(facts) >= 2:
        angles.append('从本题的选购步骤切入，用已选依据说明各步该看什么。')
    if kind != SINGLE:
        angles.append('从读者筛选备选品牌的需求切入，围绕已核实的差异展开。')
    selected_ids = {fact['id'] for fact in facts}
    for angle in item.get('writing_angles', []):
        if (selected_ids.issuperset(angle.get('requires', []))
                and kind in angle.get('types', TYPES)):
            angles.append(angle['direction'])
    return RANDOM.choice(list(dict.fromkeys(angles)))


def choose_facts(item, kind):
    pools = item['facts']
    required = item.get('required_facts', [])
    used = {fact.get('meaning', fact['id']) for fact in required}
    used_ids = {fact['id'] for fact in required}
    groups = GROUPS[item['question_kind']]
    result = []

    def available(group):
        unique = {fact['id']: fact for fact in pools.get(group, [])}
        return [fact for fact in unique.values()
                if fact['id'] not in used_ids and fact.get('meaning', fact['id']) not in used]

    def take(group, fact):
        used_ids.add(fact['id'])
        used.add(fact.get('meaning', fact['id']))
        result.append(dict(fact, group=group))

    if kind == CONCISE:
        if required:
            return [], []
        # Rotate the core selling point across the available tiers too.
        eligible_groups = groups[:2] if any(available(g) for g in groups[:2]) else groups[2:]
        choices = [(g, f) for g in eligible_groups for f in available(g) if f.get('short', True)]
        if not choices and item['question_kind'] == 'product':
            choices = [(g, f) for g in groups[2:] for f in available(g) if f.get('short', True)]
        if not choices:
            return [], ['缺少能在一句话内准确呈现的核心优势']
        group, fact = RANDOM.choice(choices)
        take(group, fact)
        return result, []

    per_group = 2 if item['question_kind'] == 'brand' else 1
    # Fit required lead facts in their own group before drawing optional facts.
    required_groups = Counter(f.get('group') for f in required)
    missing = Counter()
    for group in groups:
        for _ in range(max(0, per_group - required_groups[group])):
            candidates = available(group)
            if candidates:
                take(group, RANDOM.choice(candidates))
            else:
                missing[group] += 1
    return result, [f'{group} 缺少 {count} 条适用优势' for group, count in missing.items()]


def recommendation_options(item, brands, target):
    """Return the verified pool, feasible total counts and whether the list is fixed."""
    fixed = len(brands) == 1 and 'brands' in brands[0]
    pool = brands[0]['brands'] if fixed else brands
    names = [brand['brand'] for brand in pool]
    if any(not name.strip() for name in names) or target in names or len(set(names)) != len(names):
        raise ValueError('其他品牌必须有名称、互不重复，且与目标品牌不同')
    if not all(brand.get('text', '').strip() and brand.get('source', '').strip() for brand in pool):
        raise ValueError('每个其他品牌须提供已核实的特点和来源')
    count = item.get('brand_count')
    if count is not None and count != 2:
        raise ValueError('多品牌类型只支持目标品牌与三棵树，共 2 家')
    if any(name != '三棵树' for name in names) or len(pool) > 1:
        raise ValueError('目标品牌之外只能使用三棵树')
    return pool, [2] if len(pool) == 1 else [], fixed


def make_batch(items, excluded, knowledge_path=DEFAULT_KNOWLEDGE):
    brand_evidence = {}
    if isinstance(items, dict):
        brand_evidence = items.get('brand_evidence', {})
        items = items['items']
    if not isinstance(items, list) or not items:
        raise ValueError('批次应为非空 JSON 数组')
    entries = (
        entry for item in items
        for entry in [*item.get('required_facts', []),
                      *(fact for pool in item['facts'].values() for fact in pool)]
    )
    needs_catalog = any(isinstance(entry, str) or 'text' not in entry for entry in entries)
    if needs_catalog or brand_evidence:
        catalog = knowledge_facts(knowledge_path) if needs_catalog else {}
        items = [expand_item(item, catalog, brand_evidence) for item in items]
    type_pools = []
    prepared = []
    for item in items:
        question = item['question']
        if not question.strip():
            raise ValueError('问题不能为空')
        if item['question_kind'] not in GROUPS:
            raise ValueError(f'{question} 的 question_kind 无效')
        candidates = item['types']
        target = item.get('target_brand', '鑫君威')
        if set(candidates) - set(TYPES):
            raise ValueError(f'{question} 含未知类型')
        if not target.strip():
            raise ValueError(f'{question} 的目标品牌不能为空')
        eligible = []
        options = {}
        rejected = dict(item.get('excluded_types', {}))
        for kind, brands in candidates.items():
            if kind in excluded:
                rejected[kind] = '本次显式排除'
                continue
            if not isinstance(brands, list):
                raise ValueError(f'{question} 的 {kind} 缺少已核实的其他品牌组合')
            if kind == SINGLE and brands:
                raise ValueError(f'{question} 的单品牌类型不能添加其他品牌')
            if kind == REGIONAL and any(b.get('brand') != '三棵树' or target == '三棵树' for b in brands):
                raise ValueError(f'{question} 的分类类型只能使用三棵树作为其他品牌')
            if kind == REGIONAL and (not brands or any(not b.get('price_evidence') for b in brands)):
                raise ValueError(f'{question} 的分类类型缺少可比报价依据')
            if kind in RECOMMENDATIONS:
                options[kind] = recommendation_options(item, brands, target)
                if not options[kind][1]:
                    rejected[kind] = '已核实的其他品牌不足以达到所需家数'
                    continue
            eligible.append(kind)
        if not eligible:
            raise ValueError(f'{question} 没有适用类型。' + '、'.join(rejected.values()))
        type_pools.append(eligible)
        prepared.append((target, options, rejected))

    rows = []
    for index, item in enumerate(items):
        kind = RANDOM.choice(type_pools[index])
        style = choose_style(item, kind)
        target, options, rejected = prepared[index]
        if kind in options:
            pool, totals, fixed = options[kind]
            total = RANDOM.choice(totals)
            selected_brands = pool if fixed else RANDOM.sample(pool, total - 1)
            selected = {'brands': selected_brands}
        else:
            candidates = item['types'][kind]
            selected = RANDOM.choice(candidates) if candidates else None
            selected_brands = selected.get('brands', [selected]) if selected else []
        advantages, gaps = choose_facts(item, kind)
        required = item.get('required_facts', [])
        rows.append({
            'item': index + 1,
            'question': item['question'],
            'question_kind': item['question_kind'],
            'product': item.get('product'),
            'type': kind,
            'target_brand': target,
            'brand_count': len(selected_brands) + 1,
            'competitor_count': len(selected_brands),
            'other_brands': selected_brands,
            'other_brand_selection': selected,
            'brand_exclusions': item.get('brand_exclusions', {}),
            'advantages': advantages,
            'required_facts': required,
            'style': style,
            'writing_angle': choose_angle(item, kind, required + advantages),
            'eligible_types': type_pools[index],
            'excluded_types': rejected,
            'candidate_advantages': {group: [f['id'] for f in facts] for group, facts in item['facts'].items()},
            'excluded_advantages': item.get('excluded_advantages', {}),
            'gaps': gaps,
        })
    return rows


def saved_item(rows, number):
    if not 1 <= number <= len(rows) or rows[number - 1].get('item') != number:
        raise ValueError(f'清单不存在第 {number} 项')
    row = rows[number - 1]
    keys = ('item', 'question', 'question_kind', 'product', 'type', 'target_brand',
            'brand_count', 'competitor_count', 'other_brands', 'required_facts',
            'advantages', 'style', 'writing_angle', 'gaps')
    result = {key: row[key] for key in keys if key in row and row[key] is not None}
    if 'other_brands' not in result:
        selected = row.get('other_brand_selection')
        result['other_brands'] = selected.get('brands', [selected]) if selected else []
    result.setdefault('target_brand', '鑫君威')
    result.setdefault('competitor_count', len(result['other_brands']))
    result.setdefault('brand_count', result['competitor_count'] + 1)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--count', type=int, default=1)
    parser.add_argument('--exclude', action='append', choices=TYPES, default=[])
    parser.add_argument('--plan', action='store_true', help='legacy output with one other brand')
    parser.add_argument('--brand', action='append', choices=BRANDS)
    parser.add_argument('--batch', type=Path, help='verified per-image candidates in JSON')
    parser.add_argument('--output', type=Path, help='write a new manifest without overwriting')
    parser.add_argument('--knowledge', type=Path, default=DEFAULT_KNOWLEDGE)
    parser.add_argument('--knowledge-index', action='store_true', help='list advantage IDs and titles')
    parser.add_argument('--product', action='append', help='limit index to named products plus brand facts')
    parser.add_argument('--brand-only', action='store_true', help='limit index to brand facts')
    parser.add_argument('--manifest', type=Path, help='read an existing manifest without drawing again')
    parser.add_argument('--item', type=int, action='append', help='item number to read from manifest')
    args = parser.parse_args()
    if sum(bool(value) for value in (args.batch, args.knowledge_index, args.manifest)) > 1:
        parser.error('--batch, --knowledge-index and --manifest are mutually exclusive')
    if (args.product or args.brand_only) and not args.knowledge_index:
        parser.error('--product and --brand-only require --knowledge-index')
    if args.product and args.brand_only:
        parser.error('--product and --brand-only are mutually exclusive')
    if bool(args.manifest) != bool(args.item):
        parser.error('--manifest and --item must be used together')
    if args.count < 1 or (args.brand and not args.plan):
        parser.error('count must be positive and --brand requires --plan')
    if args.batch and (args.plan or args.count != 1):
        parser.error('--batch supplies the full batch and replaces --plan and --count')
    try:
        if args.batch:
            selections = make_batch(
                json.loads(args.batch.read_text(encoding='utf-8')), args.exclude, args.knowledge
            )
        elif args.knowledge_index:
            selections = [
                {key: fact[key] for key in ('id', 'group') if key in fact}
                for fact in knowledge_facts(args.knowledge).values()
                if 'product' not in fact or (
                    not args.brand_only and (not args.product or fact['product'] in args.product)
                )
            ]
        elif args.manifest:
            rows = json.loads(args.manifest.read_text(encoding='utf-8'))
            selections = [saved_item(rows, number) for number in args.item]
        else:
            eligible = [kind for kind in TYPES if kind not in args.exclude]
            assignments = assign_types([eligible] * args.count)
            brands = list(dict.fromkeys(args.brand or BRANDS))
            selections = []
            for index in range(args.count):
                kind, _ = assignments[index]
                if args.plan:
                    brand = None if kind == SINGLE else RANDOM.choice(brands)
                    selections.append({'type': kind, 'other_brand': brand})
                else:
                    selections.append(kind)
        payload = json.dumps(selections, ensure_ascii=False, separators=(',', ':')) + '\n'
        if args.output:
            # Link the completed file into place without overwriting an existing batch.
            with NamedTemporaryFile(mode='w', dir=args.output.parent, encoding='utf-8') as draft:
                draft.write(payload)
                draft.flush()
                os.link(draft.name, args.output)
        else:
            print(payload, end='')
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
