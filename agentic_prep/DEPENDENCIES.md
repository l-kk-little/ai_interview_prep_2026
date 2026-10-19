# 路径依赖审计与独立使用边界

审计基准：上游提交 `04316c111d0e4b75ca2ab8de0e6b42379727946e`（2026-10-18 读取）。范围为 agentic_prep 全部 Markdown、代码块/行内练习路径与跨目录引用。完整 Git 文件树无 agentic、projects、new 这三个根目录；这证明它们未发布，不能证明原作者本机当前仍有这些文件。

## 分类与修复

| 原引用类别（以下为历史名称，不是可执行路径） | 结论 | 本仓库处理 |
|---|---|---|
| v1 agentic：labs 01–05、run_all_checks、QUESTION_GUIDE | 未收录，部分命令含作者个人绝对目录 | 移除运行承诺和个人目录，按 [07 指南](07_labs_guide.md) 选择现有代码或明确的白板替代 |
| v1 agentic：questions.json、companies.json、CORE_NOTES | 未收录；原 rubric/来源表无法核验 | 标明外部原件缺失，保留历史 q-* ID；不伪造 JSON、评分或来源 |
| v1 SYSTEM_DESIGN_PLAYBOOK | 原件缺失；仓库已有答题框架 | 指向 [02 playbook](02_playbook.md)，明确为本仓库版，不宣称与原件相同 |
| projects：Valkai plan / Mirendil chat notes | 原个人项目未发布 | 日程和公司卡显式标为外部依赖，提供 C4 / A7 通用练习，不冒充公司原题 |
| new：GRPO drill | 错误旧路径；仓库有同名且内容相关的实现 | 映射到 [已有 GRPO/PPO drill](../online_resource/drills/04_grpo_ppo.py)，需要 PyTorch |
| online_resource 下题库/面经/drill | 文件树中存在，正常跨模块依赖 | 保留原链接；独立使用指克隆整个仓库，不是仅复制 agentic_prep |
| Claude Code 配置目录、sandbox guest path、需自行保存的 c10.py | 概念或创建文件的示例，不是已发布资产 | 逐行带理由标注，检查输出为 documented example；不造空文件消除失败 |

旧脚本在取得所有实际引用的仓库文件后实跑得到 **42 处断链**（同一目标的多次引用分别计数），集中在未发布目录；旧脚本跳过代码块和行内代码，因此该数字不是全部路径问题数。修复涉及入口、日历、labs 指南、题库/题解及专题中的引用。

## 校验约定

从仓库根目录运行：

```bash
python3 agentic_prep/scripts/check_links.py
python3 -m unittest discover -s agentic_prep/tests -v
python3 agentic_prep/viewer/build_data.py
```

- Markdown 普通链接、图片、显式引用式链接/定义及 HTML href/src：相对当前文档定位，解码 URL 转义，剥离 query/fragment，检查文件或目录存在并位于仓库内。
- 行内、代码块、正文中的显式 dot-relative 路径同样检查。shell fence 与行内命令按仓库根目录定位；支持字面量 cd、Python 脚本、unittest discovery 的 -s 目录。每个 fence 的 cwd 重新从仓库根开始。
- 不执行文档命令，不检查 HTTP 状态、页内锚点、任意伪代码文件名、完整 shell 语法或所有 Markdown 扩展。变量/通配符路径输出人工审查警告；声明的三个示例有带理由的逐行标注，不应为实际依赖添加豁免。
- GitHub Actions 对所有 push / PR 运行这些检查和三套已有离线测试；不按目录过滤，避免跨模块目标删除漏检。GRPO 可选且不在默认 CI，真实 API demo 也不在默认 CI。
- 离线 Viewer 数据重建后提交；CI 重新生成并检查无差异。内部课程链接继续在 Viewer 导航，仓库其他文件按磁盘相对路径打开；外部网页仍需网络。

这里的“可使用”指阅读路线和已明确列出的仓库内练习可以定位和验证，不代表恢复了未公开的原 labs、公司项目或 rubric。

## 实际验证记录（2026-10-18）

在通过 GitHub 连接器取得的固定提交文件快照上执行，未完成完整 git clone（网络不可达），没有据此声称所有仓库测试通过。

| 检查 | 实际结果 |
|---|---|
| 扩展路径审计 | 53 个 Markdown，0 errors；3 个明确标注的示例 warnings |
| 合成路径/Viewer 构建测试 | 15 tests 通过 |
| Viewer 导航 helper | Node 执行 5 项断言通过；不是浏览器端视觉测试 |
| 现有 tool-use / durable cache / weighted batcher | 分别 7 / 6 / 8 tests 通过，合计 21 |
| Viewer 数据 | 生成 53 篇；重复构建字节一致 |
| GRPO drill | 已尝试，导入 torch 失败；未运行其测试，不计通过 |
| GitHub Actions | 已添加 workflow；本地命令已验证，远程运行状态以 PR checks 为准 |

默认离线测试合计 36 个 Python tests；没有恢复或验证缺失原 labs。校验器是有限静态扫描，动态 shell、页内锚点及远程网站可用性仍需独立核验。
