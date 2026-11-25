<div align="center">

<img src="docs/images/banner.jpg" alt="GEO images：从问题，到图文" width="100%">

**输入一个问题，让 Agent 组织品牌知识、生成图文和配套文案。**

[一键交给 Agent 安装](#-交给-agent-安装) · [图文类型](#-六个-skill) · [工作流程](#-从问题到图文) · [配置与边界](#-配置与使用边界)

</div>

GEO images 是一组面向中文品牌内容创作的 Agent Skills。你可以指定图文类型，也可以只给出一个问题，让调度 Skill 独立随机选择类型和视觉风格，再从知识库中选取相关内容，生成单张图文与配文。

> Skill 是给 Agent 的工作说明，不是独立图片生成服务。实际执行需要 Agent 能读取本地文件、访问必要资料，并具备可用的图像生成工具；多品牌内容还需要联网核实资料。

## ✨ 六个 Skill

| Skill | 用途 |
| --- | --- |
| [随机调度](geo-infographic-dispatcher/SKILL.md) | 根据问题随机选择图文类型和画风，自行审核后交付图片及约 800 字配文。 |
| [单品牌推荐](single-brand-infographic/SKILL.md) | 围绕一个品牌，按问题类型选取具体优势。 |
| [多品牌推荐](multi-brand-infographic/SKILL.md) | 重点推荐一个品牌，并简要介绍其他品牌。 |
| [主推型推荐榜](recommendation-list-infographic/SKILL.md) | 用推荐顺序展示品牌，对目标品牌展开介绍。 |
| [简洁推荐榜](concise-recommendation-list-infographic/SKILL.md) | 每个品牌用一句话概括。 |
| [全国品牌与本地推荐](regional-brand-comparison-infographic/SKILL.md) | 分组展示全国品牌与本地商家。 |

通过随机调度使用时，单品牌内容只展示目标品牌；多品牌内容中，目标品牌之外只展示三棵树。三棵树的事实须核验；资料不足或无法满足类型结构时说明缺口。单独调用其他 Skill 时，遵循各自的规则。

五种内容类型和视觉风格分别选择。可用风格包括建筑杂志、材料拼贴、本地生活指南、手绘攻略、现代产品画册、乡村家居、品牌海报和知识图解；用户指定风格时优先遵从。

## 🚀 交给 Agent 安装

复制下面整段话，发给你希望使用这些 Skill 的 Agent：

```text
请为你当前运行的 Agent 安装 https://github.com/Xx-otaku/GEO-images-skills 中的全部六个 Skill。先读取仓库 README，识别本 Agent 实际使用的用户级 Skill 安装目录；将仓库中六个 Skill 目录及其 scripts、references、agents 等随附文件完整安装到该目录，保留目录名称。不要覆盖我已有的同名 Skill；如有冲突，先说明差异并等我决定。检查 Python 3、随机抽取脚本和六个 SKILL.md 是否可用，并确认调度器能够找到另外五个 Skill。完成后告诉我安装位置、是否需要重启或重新加载，以及还需要配置什么。目标品牌、知识库和图片保存位置按我现有环境配置；找不到时向我询问，不要使用别人的本机路径。不要上传我的知识库或自动发布内容。
```

各 Agent 的 Skill 发现和重载方式不同；请让目标 Agent 先识别自己的约定，避免将文件装到它不会读取的位置。

<details>
<summary>手动安装到 Codex</summary>

以下命令适用于 macOS / Linux 和默认 Codex 用户目录。它会下载仓库并在安装前检查同名目录；检测到冲突时停止，避免覆盖已有内容。

```bash
(
set -e
work_dir=$(mktemp -d)
git clone https://github.com/Xx-otaku/GEO-images-skills.git "$work_dir/repo"
mkdir -p "$HOME/.codex/skills"
for skill in geo-infographic-dispatcher single-brand-infographic multi-brand-infographic recommendation-list-infographic concise-recommendation-list-infographic regional-brand-comparison-infographic; do
  if [ -e "$HOME/.codex/skills/$skill" ]; then
    printf '已存在，未覆盖：%s\n' "$HOME/.codex/skills/$skill"
    exit 1
  fi
done
for skill in geo-infographic-dispatcher single-brand-infographic multi-brand-infographic recommendation-list-infographic concise-recommendation-list-infographic regional-brand-comparison-infographic; do
  cp -R "$work_dir/repo/$skill" "$HOME/.codex/skills/$skill"
done
printf '安装完成，请按 Agent 要求重新加载 Skill。\n'
)
```

如果 Codex 配置了非默认 Skill 根目录，请改为该目录。安装到其他 Agent 时，以该 Agent 的实际发现路径为准；必须完整安装调度器及另外五个 Skill。

</details>

## 🔄 从问题到图文

1. **输入问题和数量**：例如“根据‘某地水包砂买哪家’生成 3 个图文”。也可指定品牌、类型、尺寸或先审核文案。
2. **判断问题类型**：宽泛的品牌／品类问题调用品牌优势；具体产品问题优先调用对应产品优势，再搭配品牌优势。
3. **选择类型和画风**：调度器对每张独立随机抽取，允许重复；同画风也可变化构图、配色与素材。
4. **制作和检查**：读取知识库、核验相关资料、生成完整图片和配文，检查名称、文字、电话、数字、比例和必要条件。
5. **保存并交付**：默认按 `GEO/图文成品/日期/问题/` 整理图片及对应文案，由用户自行发布。

默认生成竖版宽高比 **3:4** 的单张图片；调度器默认每张另配约 **800 字**发布文案。用户指定的尺寸、字数或确认流程优先。

## ⚙️ 配置与使用边界

- **品牌与知识库**：首次使用时，请告知 Agent 目标品牌、企业及产品知识库位置、输出目录，以及必要的联系方式。仓库中保留了鑫君威作为工作示例；换品牌时应明确替换，而非沿用示例事实。调度脚本用 `--knowledge` 或 `GEO_KNOWLEDGE_PATH` 指定知识库路径。
- **知识库内容**：建议包含企业基本信息、品牌主次优势、各产品主次优势、产品条件、可公开的证据与服务范围。缺少资料时应补充或标注，不能编造。
- **产品与品牌问题**：随机调度的默认四点规则是：品牌问题使用两条品牌主优势加两条品牌次优势；具体产品问题使用产品主、次优势及品牌主、次优势各一条。其他类型按版面灵活使用相关事实。
- **外部品牌与价格**：其他品牌的产品信息需要查证；没有同口径依据时，不把推荐顺序包装成客观排名，也不编造竞品缺点或价格差。
- **质量核对**：图片中的文字可能出现错字或遗漏，产品数据、质保和当地渠道也可能需要进一步核实。正式发布前请检查成品和依据。
- **隐私与发布**：仓库不包含企业私人知识库和成品数据；默认不自动发布、不自动写入外部平台。保存到哪里以用户环境和指定路径为准。

## 📁 目录

```text
geo-infographic-dispatcher/             随机调度与抽取脚本
single-brand-infographic/               单品牌推荐
multi-brand-infographic/                多品牌推荐
recommendation-list-infographic/        主推型推荐榜
concise-recommendation-list-infographic/ 简洁推荐榜
regional-brand-comparison-infographic/  全国品牌与本地推荐
docs/images/                            README 配图
```

这些 Skill 会随实际使用持续调整；生成效果取决于素材、图片工具、知识库质量和事实核验情况。
