# 07 · 独立克隆后的练习指南

原五套 v1 labs 的 starter、solution、tests 均未收录；下面复用仓库已有材料，**不是原 labs 的恢复版**。历史日程的 lab 编号按本表替换。所有命令均从 **仓库根目录**执行，不需要个人目录、API key 或网络。

## 主题与替代范围

| 原主题 | 仓库现有材料 | 怎么练 / 限时 | 范围限制 |
|---|---|---|---|
| 01 raw tool agent | [现有 agent 实现](../1acre3points_crawl/practice/anthropic/agent_tool_use/agent.py)、[C1 题解](05_questions/solutions/C1_stock_agent_loop.md) | 55–75 min 闭卷写 loop，再用 fake client 思路对照 | 现有测试验证现有实现；不证明覆盖原 lab 的 budget/resume 全部要求 |
| 02 repo review | [C12 Plan–Build–Review](05_questions/solutions/C12_plan_build_review.md)、[C13 Draft PR](05_questions/solutions/C13_draft_pr_round.md) | 60 min：自选本仓库一个小改动，先写验收标准，再实现、review、运行有关测试 | 没有原缺陷 starter，也没有原六类 bug 的自动评分 |
| 03 durable harness | [现有 durable cache](../1acre3points_crawl/practice/anthropic/durable_function_call_cache.py)、[C2 题解](05_questions/solutions/C2_durable_cache.md) | 60–90 min：推演写 intent、执行、写 result 的 crash window，再读代码与测试 | 这是函数缓存练习，不是外部 job start/poll/cancel harness；有副作用场景仍需 provider 幂等键 |
| 04 multi-agent memory | [B3 shared workspace](05_questions/solutions/B3_shared_workspace.md)、[multi-agent 核心](01_core/04_multi_agent.md) | 45–60 min 白板讲 proposal/reducer、CAS、provenance/TTL，再自行写匿名 fake worker | 仓库没有原 lab 的可运行实现或验收测试；白板练习不能记作通过原 lab |
| 05 eval harness | [B5 eval harness](05_questions/solutions/B5_eval_harness.md)、[eval/security](01_core/06_eval_security.md) | 30–60 min 写匿名任务表，分别定义 outcome/policy/process grader 与 held-out split | 没有原 lab 自动 grader；只读或白板练习应如实记录 |
| GRPO debug | [已有 GRPO/PPO drill](../online_resource/drills/04_grpo_ppo.py)、[C6 题解](05_questions/solutions/C6_grpo_debug.md) | 先限时 10 min 找 bug，再运行 drill 内测试 | 可选 PyTorch 依赖，默认 CI 不安装 |
| weighted batcher | [现有实现](../1acre3points_crawl/practice/anthropic/weighted_data_batcher.py)、[C8 题解](05_questions/solutions/C8_weighted_batcher.md) | 55 min 盲写，再对照类型、权重、异常处理 | 复用现有实现及其测试，不代表 v1 JSON rubric |

## 可执行离线验证

以下测试使用 fake client / 临时目录和合成数据，仅验证仓库已有参考实现。闭卷练习后需自己接入被测实现，不能把参考实现的通过当成自己的成绩。

以下现有测试从 `practice` 导入模块，先在当前 shell 设置：

```bash
export PYTHONPATH="$PWD/1acre3points_crawl${PYTHONPATH:+:$PYTHONPATH}"
```


```bash
python3 -m unittest discover -s 1acre3points_crawl/tests -p test_claude_stock_agent.py -v
python3 -m unittest discover -s 1acre3points_crawl/tests -p test_durable_function_call_cache.py -v
python3 -m unittest discover -s 1acre3points_crawl/tests -p test_weighted_data_batcher.py -v
```

可选 GRPO（若环境未安装 torch，先在自己的虚拟环境安装 PyTorch）：

```bash
python3 online_resource/drills/04_grpo_ppo.py
```

## Valkai / Mirendil 与原 rubric

两套公司专属项目未发布，无从验证原题和实现。默认路线：Valkai 的 60 min live build 改做 [C4 Build an agent](05_questions/solutions/C4_build_an_agent.md)，按 [02 playbook](02_playbook.md) 时间盒自定验收；Mirendil take-home 时段改做 [A7 ChatGPT 设计](05_questions/solutions/A7_design_chatgpt.md) 与 [streaming 专题](03_gaps/streaming.md)。这些是通用练习，不是公司原题或等价交付。若必须做原项目，需自行取得有权使用的原始材料；仓库不提供下载位置或私人文件。

完整 v1 JSON rubric、company provenance 表和 QUESTION_GUIDE 也未发布。当前题库及题解保留的 `q-*` 只是历史标识，不可据此核验原评分表。使用当前各题的验收标准，并给每个自评分配证据句，不重建未知原文。

## 一题三练与验收

1. 白板版：20 min 讲 requirements / API / main flow / failure / eval。
2. Coding 版：只实现最危险的 state transition 或 tool runtime，用 fake clients 打桩。
3. Review 版：针对自己的改动检查 authority、idempotency、recovery、eval。

每项结论附测试、trace 或明确的推演证据；没运行的测试标“未运行”。隔天盲写再次达标才算稳定掌握。

保留原主题的口述重点：同回合并行 tool results 的消息边界；authority 来自认证上下文；外部副作用需要幂等与 reconcile；worker proposal 由 reducer 验证提交；outcome grader 检查环境状态。它们是学习目标，不是本仓库替代测试已经全部验证的断言。
