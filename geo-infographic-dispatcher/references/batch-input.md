# 批量抽取输入

候选文件是 UTF-8 JSON。推荐用顶层对象，`items` 为原题顺序的一图一项数组，`brand_evidence` 为共享竞品依据字典。旧版顶层数组与内联对象可继续读。每个优势池提交全部已核实且适用的候选。

先配置 `GEO_KNOWLEDGE_PATH` 或通过 `--knowledge <Markdown路径>` 指定知识库，再用 `choose_type.py --knowledge-index --product 水包砂` 读取鑫君威品牌和水包砂优势 ID。多个产品重复传 `--product`，纯品牌题用 `--brand-only`。索引中的 ID 由品牌、分组或产品、条目标题组成。用 `--knowledge <Markdown路径>` 可指定同结构的鑫君威资料，索引和抽取使用同一路径。其他品牌使用内联事实。

```json
{
  "brand_evidence": {
    "b01": {"brand":"三棵树","text":"已核实且适用的特点","source":"官方产品页"}
  },
  "items": [
    {
      "question":"睢宁水包砂推荐哪家？",
      "question_kind":"product",
      "product":"水包砂",
      "types":{"single-brand-infographic":[]},
      "facts":{"product_main":["鑫君威/水包砂/立体仿石"]}
    }
  ]
}
```

在推荐类型的数组内写三棵树的依据 ID，如 `["b01"]`。三种推荐类型可以引用同一 ID，全文只存于 `brand_evidence`。分类对比可引用含可比报价的同一品牌记录。

标准优势可用 ID 字符串，或用 `{"id":"索引ID","meaning":"同义组","short":false}` 附加审核标记。必答事实也可用 ID，脚本会自动带上原组。以下是兼容的内联输入示例。

```json
[
  {
    "question": "睢宁水包砂买哪家？",
    "question_kind": "product",
    "product": "水包砂",
    "types": {
      "single-brand-infographic": []
    },
    "excluded_types": {
      "regional-brand-comparison-infographic": "缺少同规格和渠道的可比报价"
    },
    "facts": {
      "product_main": [
        {
          "id": "鑫君威/水包砂/立体仿石",
          "text": "多彩彩点结合精选石英砂，呈现花岗岩荔枝面的立体质感。",
          "source": "鑫君威企业知识库｜水包砂｜产品主优势"
        }
      ],
      "product_secondary": [],
      "brand_main": [],
      "brand_secondary": []
    },
    "required_facts": [],
    "excluded_advantages": {}
  }
]
```

- `question_kind` 为 `brand` 或 `product`。同一事实在同批每道题使用相同 `id`，涉及具体产品时 ID 含产品名。优势的 `text` 使用包含限制条件的原始依据，`source` 指向来源和条目。可选 `meaning` 给语义重复的条目标同一值，`short: false` 表示难用一句话准确说明。未选入的相关条目可在 `excluded_advantages` 按 ID 写明原因。
- `required_facts` 使用同样的事实对象，可填写 `group`，值为其原来的池名。必答项可在多张图出现，同时也会从当张的可选优势中去重。
- `types` 只填用户允许且已安装的类型。单品牌的值为 `[]`。多品牌推荐和两种榜单仅传入已核实的三棵树对象，例如 `{"brand":"三棵树","text":"已核实的特点","source":"官方产品页"}`；资料不足时不使用该类型。不可添加其他品牌。
- `target_brand` 可选，默认为鑫君威；多品牌类型总共两家，`brand_count` 如填写须为 2。目标品牌为三棵树时不能重复加入，若无法满足多品牌结构则说明缺口。
- 分类对比的值为候选数组，候选另附 `price_evidence`，写明具体产品、可比规格、渠道、日期、价格和来源。
- `styles` 可选，为适用画风名的数组。默认方向为建筑杂志、材料拼贴、本地生活指南、手绘攻略、现代产品画册、乡村家居、品牌海报、知识图解。用户明确指定画风时填写 `fixed_style`，包含 `name` 与具体主视觉及构图的 `direction`。
- 输出中的 `advantages` 和 `required_facts` 共同约束上图文案与发布配文。缺项记录在 `gaps`。视觉方案随类型抽取，同种画风有两至三套构图和配色。可通过 `writing_angles` 附加与题目相关的写作角度，例如 `[{"direction":"从到店看样切入","requires":["某门店优势ID"]}]`。脚本只考虑所需 ID 都实际入选的附加角度，另可用 `types` 限定角度适用类型。默认角度由脚本根据分配行的类型和已选事实提供。标题与配文共用抽中的 `writing_angle`。


新清单中的 `target_brand`、`brand_count` 和 `other_brands` 给出目标品牌、总家数和有序其他品牌名单，`competitor_count` 给出其他品牌数。按这三项核对版面和配文。继续使用旧清单时，从 `other_brand_selection` 读取已保存的名单，单对象视作一家，`brands` 对象使用其中的数组，空值视作零家。旧清单如包含三棵树以外的其他品牌，须重新生成符合当前规则的清单。正式新任务使用 `--batch`，旧版 `--plan` 只供兼容原有调用。

写稿和重试用 `choose_type.py --manifest <逐图清单.json> --item 1` 读取定稿所需字段。可反复传 `--item` 取多条，输出始终为数组。候选和排除依据留在本地输入文件及完整清单中。读清单不会重新抽签。旧式清单可无写作角度，重试沿用原定稿。
