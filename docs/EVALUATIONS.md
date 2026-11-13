# 评测集

`evaluations/tasks.json` 定义 10 个真实任务，覆盖计划、验收、简化、边界、外部裁判、专家方法、
HTML、简洁表达、目标和反向论证。

```sh
python3 scripts/check_evaluations.py
```

任务只引用正式审核条目。当前仓库记录了评测协议和任务集，但没有伪造模型对照结果；实际效果
结论需要后续运行基线版和提示词增强版，并由独立评审按 criteria 打分。

## 2026-11-13 实际结果

模型：`deepseek-chat`。每个回答由同一模型在 A/B 盲序下评审。

固定映射：

```text
baseline 5 · augmented 4 · tie 1
```

Advisor 自动选择：

```text
baseline 2 · augmented 6 · tie 2
```

Advisor 路径的增强胜率为 60%，是正面的初步证据，但样本只有 10 个，且生成者与裁判是同一模型，
不能宣称统计显著或替代人工评审。

原始结果：

- `evaluations/results-2026-11-13.json`
- `evaluations/results-advisor-2026-11-13.json`
- `evaluations/results-advisor-reasoner-v2-2026-11-13.json`
- `evaluations/results-advisor-reasoner-run2-2026-11-13.json`
- `evaluations/results-advisor-reasoner-run3-2026-11-13.json`

## 60 样本 cross-model 聚合

生成模型：`deepseek-chat`；裁判模型：`deepseek-reasoner`。三个独立批次：

```text
augmented 38 · baseline 11 · tie 11
decisive win rate = 77.6%
one-sided sign test p = 0.00007099
```

包含一次 30 样本重复实验和三个独立 10 样本批次。聚合文件：

- `evaluations/results-advisor-cross-model-30.json`
- `evaluations/results-advisor-cross-model-60.json`

这证明 Advisor 在当前 10 类任务上的自动评测中显著优于基线。局限仍然存在：不是人工评审，
任务分布只覆盖当前评测集。
