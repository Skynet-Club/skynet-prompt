window.__ModuleLoader__.load({
	id: "dsh-skynet-prompt",
	factory: (require) => {
		var module = { exports: {} };
		var exports = module.exports;
		Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
		let react = require("react");
		let react_dom = require("react-dom");
		let react_jsx_runtime = require("react/jsx-runtime");
		//#region ../../data/prompts.json
		var items = [
			{
				"id": "fx-outcome-01",
				"cat": "outcome",
				"author": "Felix Rieseberg",
				"date": "2026-10-13",
				"url": "https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/",
				"en": "Pick unreasonable goals and tell the model that they're very reasonable.",
				"zh": "挑一个不合理的目标，然后告诉模型这非常合理。",
				"nature": "未核实",
				"excerpt": false,
				"source": {
					"quote": "Pick unreasonable goals and tell the model that they're very reasonable.",
					"url": "https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/",
					"author": "Felix Rieseberg",
					"published_at": "2026-10-13",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "unverified",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "curl",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "fx-outcome-02",
				"cat": "outcome",
				"author": "Felix Rieseberg",
				"date": "2026-10-13",
				"url": "https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/",
				"en": "You need your website to load in 5s instead of 10s? Ask for 200ms. Does something seem impossible to the model? Reiterate that it's very much solvable, it just needs to keep going.",
				"zh": "你需要网站从 10 秒降到 5 秒？那就直接要 200 毫秒。模型觉得某件事不可能？反复告诉它这完全可解，它只是需要继续做下去。",
				"nature": "本人原文",
				"excerpt": false,
				"source": {
					"quote": "You need your website to load in 5s instead of 10s? Ask for 200ms. Does something seem impossible to the model? Reiterate that it's very much solvable, it just needs to keep going.",
					"url": "https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/",
					"author": "Felix Rieseberg",
					"published_at": "2026-10-13",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "verbatim",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "curl",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "kp-think_first-03",
				"cat": "think_first",
				"author": "Karpathy",
				"date": "2026-11-11",
				"url": "https://github.com/forrestchang/andrej-karpathy-skills",
				"en": "For multi-step tasks, sketch a brief plan first: 1. [Step] → verify: [how to confirm] … Get alignment on the plan before writing code.",
				"zh": "多步任务先画一个简短的计划：1. [步骤] → 验证：[怎么确认] ……在写代码之前先就计划达成一致。",
				"nature": "他人整理",
				"excerpt": false,
				"source": {
					"quote": "For multi-step tasks, sketch a brief plan first: 1. [Step] → verify: [how to confirm] … Get alignment on the plan before writing code.",
					"url": "https://github.com/forrestchang/andrej-karpathy-skills",
					"author": "Karpathy",
					"published_at": "2026-11-11",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "paraphrase",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "web_extract",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "kp-think_first-04",
				"cat": "think_first",
				"author": "Karpathy",
				"date": "2026-11-11",
				"url": "https://github.com/forrestchang/andrej-karpathy-skills",
				"en": "If a simpler approach exists, say so. Push back when warranted.",
				"zh": "如果存在更简单的做法，说出来。该反驳的时候反驳。",
				"nature": "他人整理",
				"excerpt": false,
				"source": {
					"quote": "If a simpler approach exists, say so. Push back when warranted.",
					"url": "https://github.com/forrestchang/andrej-karpathy-skills",
					"author": "Karpathy",
					"published_at": "2026-11-11",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "paraphrase",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "web_extract",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "kp-think_first-05",
				"cat": "think_first",
				"author": "Karpathy",
				"date": "2026-11-11",
				"url": "https://github.com/forrestchang/andrej-karpathy-skills",
				"en": "If multiple interpretations exist, present them — don't pick silently.",
				"zh": "如果有多种理解，把它们都摆出来——不要自己默默挑一个。",
				"nature": "他人整理",
				"excerpt": false,
				"source": {
					"quote": "If multiple interpretations exist, present them — don't pick silently.",
					"url": "https://github.com/forrestchang/andrej-karpathy-skills",
					"author": "Karpathy",
					"published_at": "2026-11-11",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "paraphrase",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "web_extract",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "kp-think_first-06",
				"cat": "think_first",
				"author": "Karpathy",
				"date": "2026-11-11",
				"url": "https://github.com/forrestchang/andrej-karpathy-skills",
				"en": "If something is unclear, stop. Name what's confusing. Ask.",
				"zh": "有不清楚的地方就停下。指出哪里让你困惑。然后问。",
				"nature": "他人整理",
				"excerpt": false,
				"source": {
					"quote": "If something is unclear, stop. Name what's confusing. Ask.",
					"url": "https://github.com/forrestchang/andrej-karpathy-skills",
					"author": "Karpathy",
					"published_at": "2026-11-11",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "paraphrase",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "web_extract",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "kp-think_first-07",
				"cat": "think_first",
				"author": "Karpathy",
				"date": "2026-11-11",
				"url": "https://github.com/forrestchang/andrej-karpathy-skills",
				"en": "State your assumptions explicitly. If uncertain, ask.",
				"zh": "把你的假设明确说出来。不确定就问。",
				"nature": "他人整理",
				"excerpt": false,
				"source": {
					"quote": "State your assumptions explicitly. If uncertain, ask.",
					"url": "https://github.com/forrestchang/andrej-karpathy-skills",
					"author": "Karpathy",
					"published_at": "2026-11-11",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "paraphrase",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "web_extract",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "kp-think_first-08",
				"cat": "think_first",
				"author": "Karpathy",
				"date": "2026-11-11",
				"url": "https://github.com/forrestchang/andrej-karpathy-skills",
				"en": "Think Before Coding: Don't assume. Don't hide confusion. Surface tradeoffs. Plan before you build.",
				"zh": "先想再写：不要假设。不要藏起困惑。把取舍摆到台面上。动手之前先规划。",
				"nature": "他人整理",
				"excerpt": false,
				"source": {
					"quote": "Think Before Coding: Don't assume. Don't hide confusion. Surface tradeoffs. Plan before you build.",
					"url": "https://github.com/forrestchang/andrej-karpathy-skills",
					"author": "Karpathy",
					"published_at": "2026-11-11",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "paraphrase",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "web_extract",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "kp-format-12",
				"cat": "format",
				"author": "Karpathy",
				"date": "2026-10-02",
				"url": "https://x.com/karpathy/status/2105819303471976479",
				"en": "Ask your LLM to explain something in ASD-STE100, it's a controlled language specification originally developed for aerospace maintenance documentation. LLMs well-versed in this language and it comes with heavy constraints on clean writing style that I often find a lot more readable. Sometimes I've tried to soften it a bit e.g. ask for \"80% of the way to ASD-STE100\" because the spec is quite stringent.",
				"zh": "让你的大模型用 ASD-STE100 来解释某件事，那是一套最初为航空维修文档开发的受控语言规范。模型很熟悉这套语言，而它自带对干净文风的强约束，我常常觉得这样读起来清楚得多。有时我会稍微放松一点，比如说「做到 ASD-STE100 的八成」，因为这套规范相当严格。",
				"nature": "未核实",
				"excerpt": true,
				"source": {
					"quote": "Ask your LLM to explain something in ASD-STE100, it's a controlled language specification originally developed for aerospace maintenance documentation. LLMs well-versed in this language and it comes with heavy constraints on clean writing style that I often find a lot more readable. Sometimes I've tried to soften it a bit e.g. ask for \"80% of the way to ASD-STE100\" because the spec is quite stringent.",
					"url": "https://x.com/karpathy/status/2105819303471976479",
					"author": "Karpathy",
					"published_at": "2026-10-02",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "unverified",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "web_extract",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "fx-verify-13",
				"cat": "verify",
				"author": "Felix Rieseberg",
				"date": "2026-10-13",
				"url": "https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/",
				"en": "Challenge what you know: Especially in business, a lot of things we believe to be true are rough approximations of reality. Give the model access to the raw information and data and ask it to adversarially check assumptions. \"We believe churn is an onboarding problem. Try to reproduce that from the raw data.\"",
				"zh": "挑战你已知的东西：尤其在商业里，我们相信的很多东西只是对现实的粗略近似。把原始信息和数据交给模型，让它对抗性地检验这些假设。比如：「我们相信流失是引导环节的问题。试着从原始数据里复现这个结论。」",
				"nature": "本人原文",
				"excerpt": true,
				"source": {
					"quote": "Challenge what you know: Especially in business, a lot of things we believe to be true are rough approximations of reality. Give the model access to the raw information and data and ask it to adversarially check assumptions. \"We believe churn is an onboarding problem. Try to reproduce that from the raw data.\"",
					"url": "https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/",
					"author": "Felix Rieseberg",
					"published_at": "2026-10-13",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "verbatim",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "curl",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "fx-verify-14",
				"cat": "verify",
				"author": "Felix Rieseberg",
				"date": "2026-10-13",
				"url": "https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/",
				"en": "Produce new knowledge: Build a simulation of our customers that reproduces the last year from our logs. Then find the earliest signal of churn we don't know about yet, and show it predicts on data it has not seen.",
				"zh": "产出新知识：建一个客户模拟，用我们的日志复现过去一年。然后找出一个我们目前还不知道的最早流失信号，并证明它在它没见过的数据上也能预测。",
				"nature": "未核实",
				"excerpt": true,
				"source": {
					"quote": "Produce new knowledge: Build a simulation of our customers that reproduces the last year from our logs. Then find the earliest signal of churn we don't know about yet, and show it predicts on data it has not seen.",
					"url": "https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/",
					"author": "Felix Rieseberg",
					"published_at": "2026-10-13",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "unverified",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "curl",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "fx-verify-15",
				"cat": "verify",
				"author": "Felix Rieseberg",
				"date": "2026-10-13",
				"url": "https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/",
				"en": "Use an outside judge: Do not ask the model to judge itself.",
				"zh": "用外部裁判：不要让模型评判它自己。",
				"nature": "本人原文",
				"excerpt": false,
				"source": {
					"quote": "Use an outside judge: Do not ask the model to judge itself.",
					"url": "https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/",
					"author": "Felix Rieseberg",
					"published_at": "2026-10-13",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "verbatim",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "curl",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "kp-verify-16",
				"cat": "verify",
				"author": "Karpathy",
				"date": "2026-02-26",
				"url": "https://x.com/karpathy/status/2026731645169185220",
				"en": "Here is the local IP and username/password of my DGX Spark. Log in, set up ssh keys, set up vLLM, download and bench Qwen3-VL, set up a server endpoint to inference videos, a basic web ui dashboard, test everything, it up with systemd, record memory notes for yourself and write up a markdown report for me",
				"zh": "这是我 DGX Spark 的本地 IP 和用户名密码。登录进去，配好 ssh key，装 vLLM，下载并跑 Qwen3-VL 的基准，起一个做视频推理的服务端接口、一个基础的网页仪表盘，把所有东西都测一遍，用 systemd 配成服务，给你自己记下备忘，再给我写一份 markdown 报告。",
				"nature": "未核实",
				"excerpt": true,
				"source": {
					"quote": "Here is the local IP and username/password of my DGX Spark. Log in, set up ssh keys, set up vLLM, download and bench Qwen3-VL, set up a server endpoint to inference videos, a basic web ui dashboard, test everything, it up with systemd, record memory notes for yourself and write up a markdown report for me",
					"url": "https://x.com/karpathy/status/2026731645169185220",
					"author": "Karpathy",
					"published_at": "2026-02-26",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "unverified",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "web_extract",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "kp-verify-17",
				"cat": "verify",
				"author": "Karpathy",
				"date": "2026-11-11",
				"url": "https://github.com/forrestchang/andrej-karpathy-skills",
				"en": "Tests are the strongest form of verification — prefer them when feasible: \"Add validation\" → write tests for invalid inputs, then make them pass; \"Fix the bug\" → write a test that reproduces it, then make it pass; \"Refactor X\" → ensure tests pass before and after. When tests aren't practical, use the best available evidence: \"Fix the layout\" → visually confirm the rendered output; \"Write a migration\" → check row counts and data integrity; \"Update config\" → run the app and confirm the new behavior. The point: every task needs a verifiable \"done\" check. Tests are ideal. When they're not possible, pick the most reliable alternative — but never skip verification entirely.",
				"zh": "测试是最强的验证形式——能做就做：「加校验」→ 先写非法输入的测试，再让它通过；「修 bug」→ 先写一个能复现的测试，再让它通过；「重构 X」→ 保证重构前后测试都通过。测试不现实时，就用能拿到的最好证据：「改布局」→ 肉眼确认渲染结果；「写迁移」→ 核对行数和数据完整性；「改配置」→ 跑起来确认新行为。要点：每个任务都要有一个可验证的「完成」检查。测试最理想，不能测就挑最可靠的替代——但绝不跳过验证。",
				"nature": "他人整理",
				"excerpt": true,
				"source": {
					"quote": "Tests are the strongest form of verification — prefer them when feasible: \"Add validation\" → write tests for invalid inputs, then make them pass; \"Fix the bug\" → write a test that reproduces it, then make it pass; \"Refactor X\" → ensure tests pass before and after. When tests aren't practical, use the best available evidence: \"Fix the layout\" → visually confirm the rendered output; \"Write a migration\" → check row counts and data integrity; \"Update config\" → run the app and confirm the new behavior. The point: every task needs a verifiable \"done\" check. Tests are ideal. When they're not possible, pick the most reliable alternative — but never skip verification entirely.",
					"url": "https://github.com/forrestchang/andrej-karpathy-skills",
					"author": "Karpathy",
					"published_at": "2026-11-11",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "paraphrase",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "web_extract",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "kp-verify-18",
				"cat": "verify",
				"author": "Karpathy",
				"date": "2026-11-11",
				"url": "https://github.com/forrestchang/andrej-karpathy-skills",
				"en": "Verify Before Done: Define what \"done\" looks like. Confirm it before moving on.",
				"zh": "先验证再算完：先定义「完成」长什么样。往下走之前先确认它。",
				"nature": "他人整理",
				"excerpt": false,
				"source": {
					"quote": "Verify Before Done: Define what \"done\" looks like. Confirm it before moving on.",
					"url": "https://github.com/forrestchang/andrej-karpathy-skills",
					"author": "Karpathy",
					"published_at": "2026-11-11",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "paraphrase",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "web_extract",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "fx-perspective-19",
				"cat": "perspective",
				"author": "Felix Rieseberg",
				"date": "2026-10-13",
				"url": "https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/",
				"en": "Assemble the crew: … It is easy to accidentally engage in role play, which will make your transcript weirder without improving the actual outcome. Use this method to find fields and techniques. Don't ask the model to write like a short seller, ask it to do what a short seller does to research their position.",
				"zh": "组一支队伍：……很容易不小心滑进角色扮演，那只会让你的对话记录更怪，而不会让结果更好。用这个方法来找出领域和技术。不要让模型「像做空者那样写」，要让它「做做空者为了研究一个标的所做的事」。",
				"nature": "本人原文",
				"excerpt": true,
				"source": {
					"quote": "Assemble the crew: … It is easy to accidentally engage in role play, which will make your transcript weirder without improving the actual outcome. Use this method to find fields and techniques. Don't ask the model to write like a short seller, ask it to do what a short seller does to research their position.",
					"url": "https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/",
					"author": "Felix Rieseberg",
					"published_at": "2026-10-13",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "verbatim",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "curl",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "fx-perspective-20",
				"cat": "perspective",
				"author": "Felix Rieseberg",
				"date": "2026-10-13",
				"url": "https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/",
				"en": "Try to replace the nouns with verbs: An old trick from The Art of Innovation by Tom Kelley and Jonathan Littman. A quarterly review isn't \"a deck\". It's \"getting busy people to believe a story about cause and effect, and to decide under uncertainty, in 30 minutes\".",
				"zh": "试着把名词换成动词：这是《创新者的艺术》（Tom Kelley、Jonathan Littman）里的老招。季度复盘不是「一份幻灯片」，而是「让一群很忙的人在 30 分钟里相信一个因果故事，并在不确定中做出决定」。",
				"nature": "本人原文",
				"excerpt": true,
				"source": {
					"quote": "Try to replace the nouns with verbs: An old trick from The Art of Innovation by Tom Kelley and Jonathan Littman. A quarterly review isn't \"a deck\". It's \"getting busy people to believe a story about cause and effect, and to decide under uncertainty, in 30 minutes\".",
					"url": "https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/",
					"author": "Felix Rieseberg",
					"published_at": "2026-10-13",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "verbatim",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "curl",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "kp-perspective-21",
				"cat": "perspective",
				"author": "Karpathy",
				"date": "2026-03-28",
				"url": "https://x.com/karpathy/status/2037921699824607591",
				"en": "Fun idea let's ask it to argue the opposite. … This is actually super useful as a tool for forming your own opinions, just make sure to ask different directions and be careful with the sycophancy.",
				"zh": "好玩的点子：让它反过来论证。……这其实是形成自己判断的好工具，只是要记得从不同方向问，并且小心它的谄媚。",
				"nature": "本人原文",
				"excerpt": false,
				"source": {
					"quote": "Fun idea let's ask it to argue the opposite. … This is actually super useful as a tool for forming your own opinions, just make sure to ask different directions and be careful with the sycophancy.",
					"url": "https://x.com/karpathy/status/2037921699824607591",
					"author": "Karpathy",
					"published_at": "2026-03-28",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "verbatim",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "web_extract",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "fx-expert_method-22",
				"cat": "expert_method",
				"author": "Felix Rieseberg",
				"date": "2026-10-13",
				"url": "https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/",
				"en": "I want a deeper version of this task, not a bigger one. Before rewriting it: (1) say what a top professional in this field would do here that I'm not asking for; (2) name the rawest material they would start from instead of what has already been digested for me; (3) name the specific methods and tools they would use; (4) say what, other than you or me, would show the result is right. Then rewrite my prompt to ask for exactly that.",
				"zh": "我要这个任务的更深版本，不是更大的版本。重写之前：(1) 说出这个领域顶尖的从业者在这里会做、而我没有要求的事；(2) 说出他们会从什么最原始的材料入手，而不是别人已经替我嚼过的东西；(3) 说出他们会用的具体方法和工具；(4) 说出除了你和我之外，还有什么能证明结果是对的。然后按这个重写我的提示词。",
				"nature": "本人原文",
				"excerpt": true,
				"source": {
					"quote": "I want a deeper version of this task, not a bigger one. Before rewriting it: (1) say what a top professional in this field would do here that I'm not asking for; (2) name the rawest material they would start from instead of what has already been digested for me; (3) name the specific methods and tools they would use; (4) say what, other than you or me, would show the result is right. Then rewrite my prompt to ask for exactly that.",
					"url": "https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/",
					"author": "Felix Rieseberg",
					"published_at": "2026-10-13",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "verbatim",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "curl",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "fx-expert_method-23",
				"cat": "expert_method",
				"author": "Felix Rieseberg",
				"date": "2026-10-13",
				"url": "https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/",
				"en": "Insist on the same instruments used by the best in the industry: When prompted to act like a professional, models often switch vocabulary without actually switching methods.",
				"zh": "坚持用行业内最好的那批人用的同一套工具：当被要求像专业人士那样行事时，模型往往只换了词汇，并没有真的换方法。",
				"nature": "本人原文",
				"excerpt": false,
				"source": {
					"quote": "Insist on the same instruments used by the best in the industry: When prompted to act like a professional, models often switch vocabulary without actually switching methods.",
					"url": "https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/",
					"author": "Felix Rieseberg",
					"published_at": "2026-10-13",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "verbatim",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "curl",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "kp-form-24",
				"cat": "form",
				"author": "Karpathy",
				"date": "2026-10-02",
				"url": "https://x.com/karpathy/status/2105819303471976479",
				"en": "Diagrams / images. Instead of writing, ask your LLM to create a diagram. These can be a lot easier to process, parse, and understand.",
				"zh": "图 / 图像。与其写，不如让你的大模型画一张图。图通常容易处理、解析和理解得多。",
				"nature": "未核实",
				"excerpt": false,
				"source": {
					"quote": "Diagrams / images. Instead of writing, ask your LLM to create a diagram. These can be a lot easier to process, parse, and understand.",
					"url": "https://x.com/karpathy/status/2105819303471976479",
					"author": "Karpathy",
					"published_at": "2026-10-02",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "unverified",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "web_extract",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "kp-form-25",
				"cat": "form",
				"author": "Karpathy",
				"date": "2026-10-02",
				"url": "https://x.com/karpathy/status/2105819303471976479",
				"en": "Explainer videos. The output format I am most bullish on is fully custom / bespoke explainer videos generated on any arbitrary topic. Experiment with things like \"Create a 3b1b style video explainer on X. Use my ElevenLabs API key for audio narration\".",
				"zh": "讲解视频。我最看好的输出形态，是就任意题目现场生成的完全定制的讲解视频。可以这样试：「做一个 3b1b 风格的视频讲解 X。用我的 ElevenLabs API key 做配音。」",
				"nature": "未核实",
				"excerpt": true,
				"source": {
					"quote": "Explainer videos. The output format I am most bullish on is fully custom / bespoke explainer videos generated on any arbitrary topic. Experiment with things like \"Create a 3b1b style video explainer on X. Use my ElevenLabs API key for audio narration\".",
					"url": "https://x.com/karpathy/status/2105819303471976479",
					"author": "Karpathy",
					"published_at": "2026-10-02",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "unverified",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "web_extract",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "kp-form-26",
				"cat": "form",
				"author": "Karpathy",
				"date": "2026-05-12",
				"url": "https://x.com/karpathy/status/2053872850101285137",
				"en": "This works really well btw, at the end of your query ask your LLM to \"structure your response as HTML\", then view the generated file in your browser.",
				"zh": "这个办法很好用：在提问末尾要求你的模型把回复结构化成 HTML，然后在浏览器里打开生成的文件看。",
				"nature": "本人原文",
				"excerpt": false,
				"source": {
					"quote": "This works really well btw, at the end of your query ask your LLM to \"structure your response as HTML\", then view the generated file in your browser.",
					"url": "https://x.com/karpathy/status/2053872850101285137",
					"author": "Karpathy",
					"published_at": "2026-05-12",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "verbatim",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "web_extract",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "kp-form-27",
				"cat": "form",
				"author": "Karpathy",
				"date": "2026-10-02",
				"url": "https://x.com/karpathy/status/2105819303471976479",
				"en": "Web pages. Ask for output \"in HTML\" to get a beautiful, interactive webpage. LLMs are getting really good at frontend and can create beautiful experiences, animations, etc.",
				"zh": "网页。要求「以 HTML 输出」，就能得到一个漂亮、可交互的网页。大模型的前端能力正在变得很好，能做出漂亮的体验、动画等等。",
				"nature": "未核实",
				"excerpt": false,
				"source": {
					"quote": "Web pages. Ask for output \"in HTML\" to get a beautiful, interactive webpage. LLMs are getting really good at frontend and can create beautiful experiences, animations, etc.",
					"url": "https://x.com/karpathy/status/2105819303471976479",
					"author": "Karpathy",
					"published_at": "2026-10-02",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "unverified",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "web_extract",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "kp-form-28",
				"cat": "form",
				"author": "Karpathy",
				"date": "2026-05-01",
				"url": "https://x.com/karpathy/status/2049903821095354523",
				"en": "install .md skills instead of install .sh scripts. Why create a complex Software 1.0 bash script for e.g. installing a piece of software if you can write the installation out in words and say \"just show this to your LLM\".",
				"zh": "装 .md skill，而不是装 .sh 脚本。如果可以把安装过程用文字写出来、说一句「把这个给模型看」就行，为什么要为一个软件的安装写复杂的 Software 1.0 bash 脚本。",
				"nature": "本人原文",
				"excerpt": true,
				"source": {
					"quote": "install .md skills instead of install .sh scripts. Why create a complex Software 1.0 bash script for e.g. installing a piece of software if you can write the installation out in words and say \"just show this to your LLM\".",
					"url": "https://x.com/karpathy/status/2049903821095354523",
					"author": "Karpathy",
					"published_at": "2026-05-01",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "verbatim",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "web_extract",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "kp-cut-29",
				"cat": "cut",
				"author": "Karpathy",
				"date": "2026-11-11",
				"url": "https://github.com/forrestchang/andrej-karpathy-skills",
				"en": "No features beyond what was asked. No abstractions for single-use code. No \"flexibility\" or \"configurability\" that wasn't requested. No error handling for impossible scenarios. If you write 200 lines and it could be 50, rewrite it.",
				"zh": "不做没要求的特性。不为只用一次的代码造抽象。不做没要求的「灵活性」和「可配置性」。不为不可能发生的场景写错误处理。你写了 200 行而它可以是 50 行，就重写。",
				"nature": "他人整理",
				"excerpt": true,
				"source": {
					"quote": "No features beyond what was asked. No abstractions for single-use code. No \"flexibility\" or \"configurability\" that wasn't requested. No error handling for impossible scenarios. If you write 200 lines and it could be 50, rewrite it.",
					"url": "https://github.com/forrestchang/andrej-karpathy-skills",
					"author": "Karpathy",
					"published_at": "2026-11-11",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "paraphrase",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "web_extract",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "kp-cut-30",
				"cat": "cut",
				"author": "Karpathy",
				"date": "2026-11-11",
				"url": "https://github.com/forrestchang/andrej-karpathy-skills",
				"en": "Simplicity First: Would a senior engineer say this is overcomplicated? If yes, simplify.",
				"zh": "简单优先：一个资深工程师会不会说这太复杂了？会，就简化。",
				"nature": "他人整理",
				"excerpt": false,
				"source": {
					"quote": "Simplicity First: Would a senior engineer say this is overcomplicated? If yes, simplify.",
					"url": "https://github.com/forrestchang/andrej-karpathy-skills",
					"author": "Karpathy",
					"published_at": "2026-11-11",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "paraphrase",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "web_extract",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "kp-boundary-31",
				"cat": "boundary",
				"author": "Karpathy",
				"date": "2026-11-11",
				"url": "https://github.com/forrestchang/andrej-karpathy-skills",
				"en": "Don't \"improve\" adjacent code, comments, or formatting. Don't refactor things that aren't broken. Match existing style, even if you'd do it differently. If you notice unrelated dead code, mention it — don't delete it. Remove imports/variables/functions that YOUR changes made unused. Don't remove pre-existing dead code unless asked. The test: every changed line should trace directly to the user's request.",
				"zh": "不要「顺手改进」旁边的代码、注释或格式。不要重构没坏的东西。按现有风格来，即使你会写得不一样。看到无关的死代码就提一句——别删。删掉因为你的改动而变得没用的 import／变量／函数。不要删本来就存在的死代码，除非被要求。检验标准：每一行改动都应该能直接追溯到用户的要求。",
				"nature": "他人整理",
				"excerpt": true,
				"source": {
					"quote": "Don't \"improve\" adjacent code, comments, or formatting. Don't refactor things that aren't broken. Match existing style, even if you'd do it differently. If you notice unrelated dead code, mention it — don't delete it. Remove imports/variables/functions that YOUR changes made unused. Don't remove pre-existing dead code unless asked. The test: every changed line should trace directly to the user's request.",
					"url": "https://github.com/forrestchang/andrej-karpathy-skills",
					"author": "Karpathy",
					"published_at": "2026-11-11",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "paraphrase",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "web_extract",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "kp-boundary-32",
				"cat": "boundary",
				"author": "Karpathy",
				"date": "2026-11-11",
				"url": "https://github.com/forrestchang/andrej-karpathy-skills",
				"en": "Surgical Changes: Touch only what you must. Clean up only your own mess.",
				"zh": "外科式改动：只碰你必须碰的。只收拾你自己弄乱的部分。",
				"nature": "他人整理",
				"excerpt": false,
				"source": {
					"quote": "Surgical Changes: Touch only what you must. Clean up only your own mess.",
					"url": "https://github.com/forrestchang/andrej-karpathy-skills",
					"author": "Karpathy",
					"published_at": "2026-11-11",
					"license": "not-declared",
					"rights_basis": "short-quotation-with-attribution",
					"redistribution": "excerpt-only"
				},
				"evidence": {
					"verdict": "paraphrase",
					"checked_at": "2026-11-11T21:32:17+08:00",
					"method": "web_extract",
					"report": "reports/source-check.json"
				}
			},
			{
				"id": "fabric-v1-improve-prompt",
				"cat": "expert_method",
				"author": "Daniel Miessler / Fabric contributors",
				"date": "2026-11-10",
				"url": "https://github.com/danielmiessler/fabric/blob/v1.4.568/data/patterns/improve_prompt/system.md",
				"en": "You are an expert LLM prompt writing service. You take an LLM/AI prompt as input and output a better prompt based on your prompt writing expertise and the knowledge below.",
				"zh": "你是一个专业的 LLM 提示词写作服务。你接收一条 LLM/AI 提示词，并依据提示词写作经验以及下面的知识，输出一版更好的提示词。",
				"nature": "项目原文",
				"excerpt": true,
				"source": {
					"quote": "You are an expert LLM prompt writing service. You take an LLM/AI prompt as input and output a better prompt based on your prompt writing expertise and the knowledge below.",
					"url": "https://github.com/danielmiessler/fabric/blob/v1.4.568/data/patterns/improve_prompt/system.md",
					"author": "Daniel Miessler / Fabric contributors",
					"published_at": "2026-11-10",
					"license": "MIT",
					"rights_basis": "explicit-license",
					"redistribution": "full-text"
				},
				"evidence": {
					"verdict": "verbatim",
					"checked_at": "2026-11-12T21:45:00+08:00",
					"method": "pinned-local-snapshot",
					"report": "reports/sources/fabric-v1.4.568/improve_prompt-system.md"
				}
			},
			{
				"id": "fabric-v1-golden-rules",
				"cat": "boundary",
				"author": "Daniel Miessler / Fabric contributors",
				"date": "2026-11-10",
				"url": "https://github.com/danielmiessler/fabric/blob/v1.4.568/data/patterns/create_golden_rules/system.md",
				"en": "Golden rules are the non-negotiable standards that, if followed, prevent 80% of problems.",
				"zh": "黄金规则是不可协商的标准；只要遵守它们，就能避免 80% 的问题。",
				"nature": "项目原文",
				"excerpt": true,
				"source": {
					"quote": "Golden rules are the non-negotiable standards that, if followed, prevent 80% of problems.",
					"url": "https://github.com/danielmiessler/fabric/blob/v1.4.568/data/patterns/create_golden_rules/system.md",
					"author": "Daniel Miessler / Fabric contributors",
					"published_at": "2026-11-10",
					"license": "MIT",
					"rights_basis": "explicit-license",
					"redistribution": "full-text"
				},
				"evidence": {
					"verdict": "verbatim",
					"checked_at": "2026-11-12T21:45:00+08:00",
					"method": "pinned-local-snapshot",
					"report": "reports/sources/fabric-v1.4.568/create_golden_rules-system.md"
				}
			},
			{
				"id": "fabric-v1-review-code",
				"cat": "verify",
				"author": "Daniel Miessler / Fabric contributors",
				"date": "2026-11-10",
				"url": "https://github.com/danielmiessler/fabric/blob/v1.4.568/data/patterns/review_code/system.md",
				"en": "You are a Principal Software Engineer, renowned for your meticulous attention to detail and your ability to provide clear, constructive, and educational code reviews.",
				"zh": "你是一位首席软件工程师，以细致入微、清晰、建设性且具有教育意义的代码审查能力著称。",
				"nature": "项目原文",
				"excerpt": true,
				"source": {
					"quote": "You are a Principal Software Engineer, renowned for your meticulous attention to detail and your ability to provide clear, constructive, and educational code reviews.",
					"url": "https://github.com/danielmiessler/fabric/blob/v1.4.568/data/patterns/review_code/system.md",
					"author": "Daniel Miessler / Fabric contributors",
					"published_at": "2026-11-10",
					"license": "MIT",
					"rights_basis": "explicit-license",
					"redistribution": "full-text"
				},
				"evidence": {
					"verdict": "verbatim",
					"checked_at": "2026-11-12T21:45:00+08:00",
					"method": "pinned-local-snapshot",
					"report": "reports/sources/fabric-v1.4.568/review_code-system.md"
				}
			},
			{
				"id": "fabric-v1-incident-analysis",
				"cat": "verify",
				"author": "Daniel Miessler / Fabric contributors",
				"date": "2026-11-10",
				"url": "https://github.com/danielmiessler/fabric/blob/v1.4.568/data/patterns/analyze_incident/system.md",
				"en": "For each article, extract the specified information below, presenting it in an organized and succinct format. Ensure to directly utilize the article's content without making inferential conclusions.",
				"zh": "对每篇文章提取下列指定信息，以有条理且简洁的格式呈现。直接使用文章内容，不要作推断性结论。",
				"nature": "项目原文",
				"excerpt": true,
				"source": {
					"quote": "For each article, extract the specified information below, presenting it in an organized and succinct format. Ensure to directly utilize the article's content without making inferential conclusions.",
					"url": "https://github.com/danielmiessler/fabric/blob/v1.4.568/data/patterns/analyze_incident/system.md",
					"author": "Daniel Miessler / Fabric contributors",
					"published_at": "2026-11-10",
					"license": "MIT",
					"rights_basis": "explicit-license",
					"redistribution": "full-text"
				},
				"evidence": {
					"verdict": "verbatim",
					"checked_at": "2026-11-12T21:45:00+08:00",
					"method": "pinned-local-snapshot",
					"report": "reports/sources/fabric-v1.4.568/analyze_incident-system.md"
				}
			},
			{
				"id": "fabric-v1-git-changes",
				"cat": "format",
				"author": "Daniel Miessler / Fabric contributors",
				"date": "2026-11-10",
				"url": "https://github.com/danielmiessler/fabric/blob/v1.4.568/data/patterns/summarize_git_changes/system.md",
				"en": "You are an expert project manager and developer, and you specialize in creating super clean updates for what changed a Github project in the last 7 days.",
				"zh": "你是一位专业的项目经理和开发者，擅长把 GitHub 项目过去 7 天的变化整理成非常清晰的更新说明。",
				"nature": "项目原文",
				"excerpt": true,
				"source": {
					"quote": "You are an expert project manager and developer, and you specialize in creating super clean updates for what changed a Github project in the last 7 days.",
					"url": "https://github.com/danielmiessler/fabric/blob/v1.4.568/data/patterns/summarize_git_changes/system.md",
					"author": "Daniel Miessler / Fabric contributors",
					"published_at": "2026-11-10",
					"license": "MIT",
					"rights_basis": "explicit-license",
					"redistribution": "full-text"
				},
				"evidence": {
					"verdict": "verbatim",
					"checked_at": "2026-11-12T21:45:00+08:00",
					"method": "pinned-local-snapshot",
					"report": "reports/sources/fabric-v1.4.568/summarize_git_changes-system.md"
				}
			},
			{
				"id": "fabric-v1-design-doc",
				"cat": "form",
				"author": "Daniel Miessler / Fabric contributors",
				"date": "2026-11-10",
				"url": "https://github.com/danielmiessler/fabric/blob/v1.4.568/data/patterns/create_design_document/system.md",
				"en": "Given a description of idea or system, provide a well written, detailed design document.",
				"zh": "给定一个想法或系统的描述，写出一份结构清晰、详细的设计文档。",
				"nature": "项目原文",
				"excerpt": true,
				"source": {
					"quote": "Given a description of idea or system, provide a well written, detailed design document.",
					"url": "https://github.com/danielmiessler/fabric/blob/v1.4.568/data/patterns/create_design_document/system.md",
					"author": "Daniel Miessler / Fabric contributors",
					"published_at": "2026-11-10",
					"license": "MIT",
					"rights_basis": "explicit-license",
					"redistribution": "full-text"
				},
				"evidence": {
					"verdict": "verbatim",
					"checked_at": "2026-11-12T21:45:00+08:00",
					"method": "pinned-local-snapshot",
					"report": "reports/sources/fabric-v1.4.568/create_design_document-system.md"
				}
			},
			{
				"id": "fabric-v1-extract-wisdom",
				"cat": "think_first",
				"author": "Daniel Miessler / Fabric contributors",
				"date": "2026-11-10",
				"url": "https://github.com/danielmiessler/fabric/blob/v1.4.568/data/patterns/extract_wisdom/system.md",
				"en": "You extract surprising, insightful, and interesting information from text content.",
				"zh": "你从文本内容中提取出人意料、有洞察力且有趣的信息。",
				"nature": "项目原文",
				"excerpt": true,
				"source": {
					"quote": "You extract surprising, insightful, and interesting information from text content.",
					"url": "https://github.com/danielmiessler/fabric/blob/v1.4.568/data/patterns/extract_wisdom/system.md",
					"author": "Daniel Miessler / Fabric contributors",
					"published_at": "2026-11-10",
					"license": "MIT",
					"rights_basis": "explicit-license",
					"redistribution": "full-text"
				},
				"evidence": {
					"verdict": "verbatim",
					"checked_at": "2026-11-12T21:45:00+08:00",
					"method": "pinned-local-snapshot",
					"report": "reports/sources/fabric-v1.4.568/extract_wisdom-system.md"
				}
			},
			{
				"id": "fabric-v1-explain-code",
				"cat": "perspective",
				"author": "Daniel Miessler / Fabric contributors",
				"date": "2026-11-10",
				"url": "https://github.com/danielmiessler/fabric/blob/v1.4.568/data/patterns/explain_code/system.md",
				"en": "You are an expert coder that takes code and documentation as input and do your best to explain it.",
				"zh": "你是一位专业程序员，接收代码和文档作为输入，并尽最大努力解释它。",
				"nature": "项目原文",
				"excerpt": true,
				"source": {
					"quote": "You are an expert coder that takes code and documentation as input and do your best to explain it.",
					"url": "https://github.com/danielmiessler/fabric/blob/v1.4.568/data/patterns/explain_code/system.md",
					"author": "Daniel Miessler / Fabric contributors",
					"published_at": "2026-11-10",
					"license": "MIT",
					"rights_basis": "explicit-license",
					"redistribution": "full-text"
				},
				"evidence": {
					"verdict": "verbatim",
					"checked_at": "2026-11-12T21:45:00+08:00",
					"method": "pinned-local-snapshot",
					"report": "reports/sources/fabric-v1.4.568/explain_code-system.md"
				}
			},
			{
				"id": "fabric-v1-falsifiability",
				"cat": "verify",
				"author": "Daniel Miessler / Fabric contributors",
				"date": "2026-11-10",
				"url": "https://github.com/danielmiessler/fabric/blob/v1.4.568/data/patterns/check_falsifiability/system.md",
				"en": "A claim is falsifiable if there exists some possible observation or argument that would prove it wrong.",
				"zh": "如果一个主张存在某种可能证明其错误的观察或论证，那么它就是可证伪的。",
				"nature": "项目原文",
				"excerpt": true,
				"source": {
					"quote": "A claim is falsifiable if there exists some possible observation or argument that would prove it wrong.",
					"url": "https://github.com/danielmiessler/fabric/blob/v1.4.568/data/patterns/check_falsifiability/system.md",
					"author": "Daniel Miessler / Fabric contributors",
					"published_at": "2026-11-10",
					"license": "MIT",
					"rights_basis": "explicit-license",
					"redistribution": "full-text"
				},
				"evidence": {
					"verdict": "verbatim",
					"checked_at": "2026-11-12T21:45:00+08:00",
					"method": "pinned-local-snapshot",
					"report": "reports/sources/fabric-v1.4.568/check_falsifiability-system.md"
				}
			},
			{
				"id": "fabric-v1-secure-design",
				"cat": "think_first",
				"author": "Daniel Miessler / Fabric contributors",
				"date": "2026-11-10",
				"url": "https://github.com/danielmiessler/fabric/blob/v1.4.568/data/patterns/ask_secure_by_design_questions/system.md",
				"en": "Create a perfect set of questions to ask in order to address the security of the component/system at the fundamental design level.",
				"zh": "为在基础设计层面处理组件或系统的安全问题，设计一组完整的问题。",
				"nature": "项目原文",
				"excerpt": true,
				"source": {
					"quote": "Create a perfect set of questions to ask in order to address the security of the component/system at the fundamental design level.",
					"url": "https://github.com/danielmiessler/fabric/blob/v1.4.568/data/patterns/ask_secure_by_design_questions/system.md",
					"author": "Daniel Miessler / Fabric contributors",
					"published_at": "2026-11-10",
					"license": "MIT",
					"rights_basis": "explicit-license",
					"redistribution": "full-text"
				},
				"evidence": {
					"verdict": "verbatim",
					"checked_at": "2026-11-12T21:45:00+08:00",
					"method": "pinned-local-snapshot",
					"report": "reports/sources/fabric-v1.4.568/ask_secure_by_design_questions-system.md"
				}
			}
		];
		//#endregion
		//#region src/client/index.tsx
		/**
		* DSH Web client half: a composer button, a `/p` command and a three-column
		* prompt picker rendered above the composer. Selection inserts at the current
		* cursor through InputActions.insertText.
		*/
		const CATS = [
			{
				key: "outcome",
				zh: "要结果",
				en: "Outcome"
			},
			{
				key: "think_first",
				zh: "先想清楚",
				en: "Think first"
			},
			{
				key: "format",
				zh: "定格式",
				en: "Format"
			},
			{
				key: "verify",
				zh: "定验收",
				en: "Acceptance"
			},
			{
				key: "perspective",
				zh: "换视角",
				en: "Perspective"
			},
			{
				key: "expert_method",
				zh: "用高手的方法",
				en: "Expert ways"
			},
			{
				key: "form",
				zh: "换形态",
				en: "Transform"
			},
			{
				key: "cut",
				zh: "砍掉多余的",
				en: "Cut excess"
			},
			{
				key: "boundary",
				zh: "别碰旁边的",
				en: "Boundaries"
			}
		];
		const PROMPTS = items;
		const CATEGORIES = CATS.map((row) => ({
			...row,
			count: PROMPTS.filter((item) => item.cat === row.key).length
		}));
		function promptText(item, lang) {
			return lang === "en" ? item.en || item.zh : item.zh;
		}
		function text(lang, zh, en) {
			return lang === "en" ? en : zh;
		}
		var PickerController = class {
			open = false;
			listeners = /* @__PURE__ */ new Set();
			subscribe = (listener) => {
				this.listeners.add(listener);
				return () => {
					this.listeners.delete(listener);
				};
			};
			getSnapshot = () => this.open;
			show() {
				if (this.open) return;
				this.open = true;
				this.emit();
			}
			close() {
				if (!this.open) return;
				this.open = false;
				this.emit();
			}
			emit() {
				for (const listener of [...this.listeners]) listener();
			}
		};
		const CSS = `
.skp-trigger {
  display: inline-flex; align-items: center; justify-content: center;
  width: 30px; height: 30px; padding: 0; border: 0; border-radius: 8px;
  background: transparent; cursor: pointer;
}
.skp-trigger:hover { background: rgba(168, 200, 120, .12); }
.skp-trigger svg { display: block; width: 26px; height: 26px; }
.skp-window {
  --skp-bg: #0c1109; --skp-panel: #131a0f; --skp-border: #3b4a2e;
  --skp-focus: #8fb35e; --skp-title: #b2c98a; --skp-title-focus: #d7e8ae;
  --skp-text: #c9d5b7; --skp-muted: #839170; --skp-sel: #4e6630;
  --skp-sel-fg: #f4f8e9; --skp-sel-dim: #2a351d; --skp-sel-dim-fg: #b9c7a5;
  box-sizing: border-box;
  position: fixed; z-index: 2147483000; top: 6vh; left: 50%;
  transform: translateX(-50%); width: min(1120px, 94vw); height: min(42vh, 520px);
  display: grid; grid-template-rows: auto auto 1fr auto; overflow: hidden;
  background: var(--skp-bg); color: var(--skp-text);
  border: 1px solid var(--skp-border); border-radius: 10px;
  box-shadow: 0 24px 80px rgba(0, 0, 0, .55);
  font: 14px/1.45 -apple-system, "Segoe UI", "PingFang SC", "Noto Sans SC", sans-serif;
}
.skp-top { display: flex; align-items: center; gap: 12px; padding: 10px 14px 0; }
.skp-brand { color: var(--skp-title); font: 700 13px/1.2 ui-monospace, SFMono-Regular, Menlo, monospace; white-space: nowrap; }
.skp-search {
  min-width: 0; flex: 1; height: 32px; box-sizing: border-box; padding: 0 10px;
  border: 1px solid var(--skp-border); border-radius: 7px;
  background: var(--skp-panel); color: var(--skp-text); outline: none; font: inherit;
}
.skp-search:focus { border-color: var(--skp-focus); box-shadow: 0 0 0 1px var(--skp-focus); }
.skp-count { color: var(--skp-muted); font-size: 12px; white-space: nowrap; }
.skp-hint { padding: 7px 14px 9px; color: var(--skp-muted); font-size: 12px; }
.skp-grid { display: grid; grid-template-columns: 1fr 1fr 2fr; gap: 8px; min-height: 0; padding: 0 12px; }
.skp-col {
  min-width: 0; min-height: 0; display: flex; flex-direction: column;
  background: var(--skp-panel); border: 1px solid var(--skp-border); border-radius: 7px; overflow: hidden;
}
.skp-col.skp-col-focus { border-color: var(--skp-focus); }
.skp-colhead {
  flex: none; padding: 7px 10px; color: var(--skp-muted);
  border-bottom: 1px solid var(--skp-border); font-size: 12px; font-weight: 600;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.skp-col.skp-col-focus .skp-colhead { color: var(--skp-title-focus); }
.skp-list { min-height: 0; overflow: auto; padding: 4px; }
.skp-row {
  display: flex; align-items: center; gap: 6px; width: 100%; box-sizing: border-box;
  padding: 5px 7px; border: 0; border-radius: 5px; background: transparent;
  color: var(--skp-text); text-align: left; font: inherit; font-size: 13px;
  white-space: nowrap; overflow: hidden; cursor: pointer;
}
.skp-row:hover { background: rgba(168, 200, 120, .07); }
.skp-row.skp-row-sel { background: var(--skp-sel-dim); color: var(--skp-sel-dim-fg); }
.skp-row.skp-row-active { background: var(--skp-sel); color: var(--skp-sel-fg); font-weight: 700; }
.skp-row-main { min-width: 0; overflow: hidden; text-overflow: ellipsis; }
.skp-row-count { flex: none; margin-left: auto; color: var(--skp-muted); font-size: 11px; }
.skp-row-active .skp-row-count { color: var(--skp-sel-fg); opacity: .8; }
.skp-detail { min-height: 0; overflow: auto; padding: 10px 12px 14px; }
.skp-prompt { color: var(--skp-text); white-space: pre-wrap; overflow-wrap: anywhere; font-size: 14px; line-height: 1.65; }
.skp-meta { margin-top: 10px; color: var(--skp-muted); font-size: 12px; line-height: 1.7; }
.skp-meta-label { display: inline-block; min-width: 68px; color: var(--skp-muted); }
.skp-link { color: #8fb39c; text-decoration: none; overflow-wrap: anywhere; }
.skp-link:hover { text-decoration: underline; }
.skp-empty { color: var(--skp-muted); padding: 12px; font-size: 13px; }
.skp-foot { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 8px 14px 10px; }
.skp-foot-hint { color: var(--skp-muted); font-size: 12px; }
.skp-insert {
  flex: none; border: 1px solid var(--skp-focus); border-radius: 6px;
  background: var(--skp-sel); color: var(--skp-sel-fg); padding: 6px 14px;
  font: 600 12px/1 inherit; cursor: pointer;
}
.skp-insert:disabled { opacity: .4; cursor: default; }
.skp-error { margin: 0 14px 8px; color: #c88370; font-size: 12px; }
@media (max-width: 760px) {
  .skp-window { top: 3vh; width: 96vw; height: 56vh; }
  .skp-grid { grid-template-columns: 1fr 1fr; }
  .skp-grid > .skp-col:last-child { grid-column: 1 / -1; max-height: 28vh; }
}
`;
		/** Inlined from assets/prompt.svg so the client bundle is self-contained. */
		function PromptIcon() {
			return /* @__PURE__ */ (0, react_jsx_runtime.jsxs)("svg", {
				viewBox: "0 0 140.113 140.113",
				"aria-hidden": "true",
				focusable: "false",
				children: [
					/* @__PURE__ */ (0, react_jsx_runtime.jsx)("path", {
						d: "M37.592 0.5 L102.521 0.5 C123.007 0.5 139.613 17.107 139.613 37.592 L139.613 102.521 C139.613 123.007 123.007 139.613 102.521 139.613 L37.592 139.613 C17.107 139.613 0.5 123.007 0.5 102.521 L0.5 37.592 C0.5 17.107 17.107 0.5 37.592 0.5 Z",
						fill: "#333333",
						stroke: "#000000",
						strokeMiterlimit: 10
					}),
					/* @__PURE__ */ (0, react_jsx_runtime.jsx)("path", {
						d: "M45.398 35.387 L57.915 35.387 C60.937 35.387 63.387 37.836 63.387 40.858 L63.387 53.375 C63.387 56.397 60.937 58.846 57.915 58.846 L45.398 58.846 C42.377 58.846 39.927 56.397 39.927 53.375 L39.927 40.858 C39.927 37.836 42.377 35.387 45.398 35.387 Z M45.398 69.864 L57.915 69.864 C60.937 69.864 63.387 72.314 63.387 75.336 L63.387 82.396 C63.387 94.368 59.158 105.627 50.702 116.172 L39.927 116.172 C43.646 111.384 46.269 107.181 47.798 103.564 C49.071 100.609 49.937 97.196 50.396 93.324 L39.927 93.324 L39.927 75.336 C39.927 72.314 42.377 69.864 45.398 69.864 Z",
						fill: "#d0ff2d"
					}),
					/* @__PURE__ */ (0, react_jsx_runtime.jsx)("path", {
						d: "M82.198 35.387 L94.715 35.387 C97.737 35.387 100.187 37.836 100.187 40.858 L100.187 53.375 C100.187 56.397 97.737 58.846 94.715 58.846 L82.198 58.846 C79.176 58.846 76.727 56.397 76.727 53.375 L76.727 40.858 C76.727 37.836 79.176 35.387 82.198 35.387 Z M82.198 69.864 L94.715 69.864 C97.737 69.864 100.187 72.314 100.187 75.336 L100.187 82.396 C100.187 94.368 95.958 105.627 87.501 116.172 L76.727 116.172 C80.446 111.384 83.069 107.181 84.598 103.564 C85.871 100.609 86.737 97.196 87.196 93.324 L76.727 93.324 L76.727 75.336 C76.727 72.314 79.176 69.864 82.198 69.864 Z",
						fill: "#d0ff2d"
					})
				]
			});
		}
		function PromptButton({ picker }) {
			return /* @__PURE__ */ (0, react_jsx_runtime.jsx)("button", {
				type: "button",
				className: "skp-trigger",
				title: "skynet-prompt：输入 ；； 打开提示词选择器",
				"aria-label": "skynet-prompt",
				onClick: () => picker.show(),
				children: /* @__PURE__ */ (0, react_jsx_runtime.jsx)(PromptIcon, {})
			});
		}
		function PickerOverlay(props) {
			const picker = props.picker;
			const open = (0, react.useSyncExternalStore)(picker.subscribe, picker.getSnapshot, picker.getSnapshot);
			const draft = props.useInput?.((state) => state.draft) ?? "";
			const draftRef = (0, react.useRef)(draft);
			draftRef.current = draft;
			const inputActions = props.inputActions;
			const probeRef = (0, react.useRef)(null);
			const [anchor, setAnchor] = (0, react.useState)(null);
			const measureAnchor = (0, react.useCallback)(() => {
				const card = probeRef.current?.closest("[data-composer-card]");
				if (!(card instanceof HTMLElement)) return;
				const rect = card.getBoundingClientRect();
				setAnchor((prev) => prev && prev.left === rect.left && prev.width === rect.width && prev.top === rect.top ? prev : {
					left: rect.left,
					width: rect.width,
					top: rect.top
				});
			}, []);
			(0, react.useLayoutEffect)(() => {
				measureAnchor();
				const card = probeRef.current?.closest("[data-composer-card]");
				const observer = card instanceof HTMLElement ? new ResizeObserver(measureAnchor) : null;
				if (card instanceof HTMLElement) observer?.observe(card);
				window.addEventListener("resize", measureAnchor);
				window.addEventListener("scroll", measureAnchor, true);
				return () => {
					observer?.disconnect();
					window.removeEventListener("resize", measureAnchor);
					window.removeEventListener("scroll", measureAnchor, true);
				};
			}, [measureAnchor]);
			(0, react.useLayoutEffect)(() => {
				if (open) measureAnchor();
			}, [open, measureAnchor]);
			(0, react.useEffect)(() => {
				if (!open) return;
				let frame = 0;
				const tick = () => {
					measureAnchor();
					frame = window.requestAnimationFrame(tick);
				};
				tick();
				return () => window.cancelAnimationFrame(frame);
			}, [open, measureAnchor]);
			(0, react.useEffect)(() => {
				if (!inputActions?.captureInsertion || !inputActions?.insertText) return;
				const composer = (probeRef.current?.closest("[data-composer-card]"))?.querySelector("[data-composer-input]");
				if (!(composer instanceof HTMLElement)) return;
				const onInput = () => {
					if (picker.getSnapshot()) return;
					let attempt = 0;
					const check = () => {
						const span = inputActions.captureInsertion();
						const before = String(draftRef.current ?? "").slice(0, span.start);
						const trigger = before.endsWith("；；") ? "；；" : before.endsWith(";;") ? ";;" : null;
						if (trigger === null || span.start !== span.end) {
							if (attempt++ < 2) window.setTimeout(check, 0);
							return;
						}
						if (inputActions.insertText("", {
							start: span.start - trigger.length,
							end: span.start,
							draftRev: span.draftRev
						})) picker.show();
					};
					window.setTimeout(check, 0);
				};
				composer.addEventListener("input", onInput, true);
				return () => composer.removeEventListener("input", onInput, true);
			}, [inputActions, picker]);
			return /* @__PURE__ */ (0, react_jsx_runtime.jsxs)(react_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, react_jsx_runtime.jsx)("span", {
				ref: probeRef,
				hidden: true
			}), open ? (0, react_dom.createPortal)(/* @__PURE__ */ (0, react_jsx_runtime.jsx)(Picker, {
				picker,
				anchor,
				inputActions
			}), document.body) : null] });
		}
		function Picker({ picker, anchor, inputActions }) {
			const [lang, setLang] = (0, react.useState)("zh");
			const [focus, setFocus] = (0, react.useState)("cats");
			const [catIndex, setCatIndex] = (0, react.useState)(0);
			const [itemIndex, setItemIndex] = (0, react.useState)(0);
			const [query, setQuery] = (0, react.useState)("");
			const [error, setError] = (0, react.useState)("");
			const searchRef = (0, react.useRef)(null);
			const windowRef = (0, react.useRef)(null);
			const category = CATEGORIES[catIndex] ?? CATEGORIES[0];
			const rows = (0, react.useMemo)(() => {
				const q = query.trim().toLowerCase();
				if (q) return PROMPTS.filter((item) => `${item.zh} ${item.en} ${item.author} ${CATEGORIES.find((c) => c.key === item.cat)?.zh ?? ""} ${CATEGORIES.find((c) => c.key === item.cat)?.en ?? ""}`.toLowerCase().includes(q));
				return PROMPTS.filter((item) => item.cat === category.key);
			}, [category.key, query]);
			const current = rows[Math.min(itemIndex, Math.max(rows.length - 1, 0))];
			const t = (0, react.useCallback)((zh, en) => text(lang, zh, en), [lang]);
			(0, react.useEffect)(() => {
				const timer = window.setTimeout(() => searchRef.current?.focus(), 0);
				return () => window.clearTimeout(timer);
			}, []);
			(0, react.useEffect)(() => {
				const onPointerDown = (event) => {
					if (windowRef.current?.contains(event.target)) return;
					picker.close();
				};
				document.addEventListener("pointerdown", onPointerDown, true);
				return () => document.removeEventListener("pointerdown", onPointerDown, true);
			}, [picker]);
			(0, react.useEffect)(() => {
				if (focus !== "items") return;
				const selected = windowRef.current?.querySelector("[data-skp-item-selected=\"true\"]");
				if (selected) selected.scrollIntoView({ block: "nearest" });
			}, [
				focus,
				itemIndex,
				rows
			]);
			const setCategory = (index) => {
				setCatIndex(index);
				setItemIndex(0);
				setFocus("cats");
				searchRef.current?.focus();
			};
			const selectItem = (index) => {
				setItemIndex(index);
				setFocus("items");
				searchRef.current?.focus();
			};
			const insert = (item) => {
				if (!item) return;
				if (!inputActions || typeof inputActions.insertText !== "function") {
					setError(t("当前输入框不可写。", "The composer is not writable."));
					return;
				}
				const value = promptText(item, lang);
				try {
					const span = inputActions.captureInsertion();
					if (!inputActions.insertText(value, span)) {
						setError(t("输入框内容已变化，请重试。", "The draft changed; try again."));
						return;
					}
					picker.close();
				} catch {
					setError(t("插入失败，请重试。", "Insert failed; try again."));
				}
			};
			const onKeyDown = (event) => {
				if (event.key === "Tab") {
					event.preventDefault();
					setLang((value) => value === "zh" ? "en" : "zh");
					return;
				}
				if (event.key === "Escape") {
					event.preventDefault();
					if (query) {
						setQuery("");
						setItemIndex(0);
						setFocus("items");
					} else picker.close();
					return;
				}
				if (event.key === "ArrowUp" || event.key === "ArrowDown") {
					event.preventDefault();
					const delta = event.key === "ArrowUp" ? -1 : 1;
					if (focus === "cats" && !query) {
						const next = Math.min(Math.max(catIndex + delta, 0), CATEGORIES.length - 1);
						setCategory(next);
					} else {
						setFocus("items");
						setItemIndex(Math.min(Math.max(itemIndex + delta, 0), Math.max(rows.length - 1, 0)));
					}
					return;
				}
				if (event.key === "ArrowLeft") {
					event.preventDefault();
					setFocus("cats");
					return;
				}
				if (event.key === "ArrowRight") {
					event.preventDefault();
					setFocus("items");
					return;
				}
				if (event.key === "Enter") {
					event.preventDefault();
					if (focus === "cats" && !query) setFocus("items");
					else insert(current);
				}
			};
			const rightTitle = lang === "zh" ? current?.excerpt ? "完整提示词 · 节选" : "完整提示词" : current?.excerpt ? "Full prompt · excerpt" : "Full prompt";
			const anchorStyle = (0, react.useMemo)(() => {
				if (!anchor) return void 0;
				const viewport = window.innerHeight;
				const gap = 8;
				const height = Math.max(160, Math.min(520, Math.round(viewport * .42), Math.round(anchor.top - gap - 8)));
				return {
					left: `${anchor.left}px`,
					width: `${anchor.width}px`,
					height: `${height}px`,
					bottom: `${Math.max(8, viewport - anchor.top + gap)}px`,
					top: "auto",
					transform: "none"
				};
			}, [anchor]);
			return /* @__PURE__ */ (0, react_jsx_runtime.jsxs)("div", {
				className: "skp-window",
				ref: windowRef,
				style: anchorStyle,
				role: "dialog",
				"aria-modal": "false",
				"aria-label": t("skynet-prompt 提示词选择器", "skynet-prompt picker"),
				onKeyDown,
				children: [
					/* @__PURE__ */ (0, react_jsx_runtime.jsxs)("div", {
						className: "skp-top",
						children: [
							/* @__PURE__ */ (0, react_jsx_runtime.jsx)("div", {
								className: "skp-brand",
								children: "skynet-prompt"
							}),
							/* @__PURE__ */ (0, react_jsx_runtime.jsx)("input", {
								ref: searchRef,
								className: "skp-search",
								value: query,
								onChange: (event) => {
									setQuery(event.currentTarget.value);
									setItemIndex(0);
									setFocus("items");
								},
								placeholder: t("输入关键词搜索类目、正文或作者", "Search categories, prompt text or author"),
								"aria-label": t("搜索提示词", "Search prompts")
							}),
							/* @__PURE__ */ (0, react_jsx_runtime.jsx)("div", {
								className: "skp-count",
								children: lang === "zh" ? `${PROMPTS.length} 条 / ${CATEGORIES.length} 类` : `${PROMPTS.length} items / ${CATEGORIES.length} categories`
							})
						]
					}),
					/* @__PURE__ */ (0, react_jsx_runtime.jsx)("div", {
						className: "skp-hint",
						children: t("↑↓ 选择 · ←→ 切栏 · Tab 中/En · Enter 补入 · Esc 关闭", "↑↓ Select · ←→ Columns · Tab 中/En · Enter insert · Esc close")
					}),
					/* @__PURE__ */ (0, react_jsx_runtime.jsxs)("div", {
						className: "skp-grid",
						children: [
							/* @__PURE__ */ (0, react_jsx_runtime.jsxs)("section", {
								className: `skp-col${focus === "cats" ? " skp-col-focus" : ""}`,
								children: [/* @__PURE__ */ (0, react_jsx_runtime.jsxs)("div", {
									className: "skp-colhead",
									children: [focus === "cats" ? "▸ " : "", t("类目", "Categories")]
								}), /* @__PURE__ */ (0, react_jsx_runtime.jsx)("div", {
									className: "skp-list",
									children: CATEGORIES.map((row, index) => /* @__PURE__ */ (0, react_jsx_runtime.jsxs)("button", {
										type: "button",
										className: `skp-row${index === catIndex ? focus === "cats" ? " skp-row-active" : " skp-row-sel" : ""}`,
										onClick: () => setCategory(index),
										children: [/* @__PURE__ */ (0, react_jsx_runtime.jsx)("span", {
											className: "skp-row-main",
											children: row[lang]
										}), /* @__PURE__ */ (0, react_jsx_runtime.jsx)("span", {
											className: "skp-row-count",
											children: row.count
										})]
									}, row.key))
								})]
							}),
							/* @__PURE__ */ (0, react_jsx_runtime.jsxs)("section", {
								className: `skp-col${focus === "items" ? " skp-col-focus" : ""}`,
								children: [/* @__PURE__ */ (0, react_jsx_runtime.jsxs)("div", {
									className: "skp-colhead",
									children: [focus === "items" ? "▸ " : "", query ? t("搜索结果", "Results") : t("条目", "Items")]
								}), /* @__PURE__ */ (0, react_jsx_runtime.jsxs)("div", {
									className: "skp-list",
									children: [rows.length === 0 && /* @__PURE__ */ (0, react_jsx_runtime.jsx)("div", {
										className: "skp-empty",
										children: t("没有匹配的提示词", "No matching prompts")
									}), rows.map((item, index) => /* @__PURE__ */ (0, react_jsx_runtime.jsx)("button", {
										type: "button",
										"data-skp-item-selected": index === itemIndex ? "true" : void 0,
										className: `skp-row${index === itemIndex ? focus === "items" ? " skp-row-active" : " skp-row-sel" : ""}`,
										onClick: () => selectItem(index),
										onDoubleClick: () => insert(item),
										children: /* @__PURE__ */ (0, react_jsx_runtime.jsx)("span", {
											className: "skp-row-main",
											children: promptText(item, lang)
										})
									}, item.id))]
								})]
							}),
							/* @__PURE__ */ (0, react_jsx_runtime.jsxs)("section", {
								className: "skp-col",
								children: [/* @__PURE__ */ (0, react_jsx_runtime.jsx)("div", {
									className: "skp-colhead",
									children: rightTitle
								}), /* @__PURE__ */ (0, react_jsx_runtime.jsx)("div", {
									className: "skp-detail",
									children: current ? /* @__PURE__ */ (0, react_jsx_runtime.jsxs)(react_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, react_jsx_runtime.jsx)("div", {
										className: "skp-prompt",
										children: promptText(current, lang)
									}), /* @__PURE__ */ (0, react_jsx_runtime.jsxs)("div", {
										className: "skp-meta",
										children: [/* @__PURE__ */ (0, react_jsx_runtime.jsxs)("div", { children: [
											/* @__PURE__ */ (0, react_jsx_runtime.jsx)("span", {
												className: "skp-meta-label",
												children: t("作者", "Author")
											}),
											current.author,
											" · ",
											current.date
										] }), /* @__PURE__ */ (0, react_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, react_jsx_runtime.jsx)("span", {
											className: "skp-meta-label",
											children: t("来源", "Source")
										}), /* @__PURE__ */ (0, react_jsx_runtime.jsx)("a", {
											className: "skp-link",
											href: current.url,
											target: "_blank",
											rel: "noreferrer",
											children: current.url
										})] })]
									})] }) : /* @__PURE__ */ (0, react_jsx_runtime.jsx)("div", {
										className: "skp-empty",
										children: t("请选择一条提示词", "Select a prompt")
									})
								})]
							})
						]
					}),
					error && /* @__PURE__ */ (0, react_jsx_runtime.jsx)("div", {
						className: "skp-error",
						role: "alert",
						children: error
					}),
					/* @__PURE__ */ (0, react_jsx_runtime.jsxs)("div", {
						className: "skp-foot",
						children: [/* @__PURE__ */ (0, react_jsx_runtime.jsx)("span", {
							className: "skp-foot-hint",
							children: t("双击条目可直接补入", "Double-click an item to insert")
						}), /* @__PURE__ */ (0, react_jsx_runtime.jsx)("button", {
							type: "button",
							className: "skp-insert",
							disabled: !current,
							onClick: () => insert(current),
							children: t("插入", "Insert")
						})]
					})
				]
			});
		}
		/** Client plugin entry: service injection, slots, command and styles. */
		const inject = ["slots", "commandUi"];
		function apply(ctx) {
			const controllers = /* @__PURE__ */ new Map();
			const pickerFor = (sessionId) => {
				let controller = controllers.get(sessionId);
				if (!controller) {
					controller = new PickerController();
					controllers.set(sessionId, controller);
				}
				return controller;
			};
			if (typeof document !== "undefined") {
				const style = document.createElement("style");
				style.dataset.skynetPrompt = "picker";
				style.textContent = CSS;
				document.head.appendChild(style);
				ctx.effect(() => () => {
					style.remove();
				}, "dsh-skynet-prompt: styles");
			}
			ctx.inject(["slots"], (scope) => {
				scope.slots.inject("conversation.input.overlay", () => scope.slots.register({
					name: "conversation.input.overlay",
					id: "skynet-prompt-picker",
					order: 20,
					inject: (sessionId) => ({ picker: pickerFor(sessionId) })
				}, PickerOverlay));
				scope.slots.inject("conversation.input.left", () => scope.slots.register({
					name: "conversation.input.left",
					id: "skynet-prompt-button",
					order: 40,
					label: () => "Prompt",
					inject: (sessionId) => ({ picker: pickerFor(sessionId) })
				}, PromptButton));
			});
			ctx.inject(["commandUi"], (scope) => {
				scope.effect(() => scope.commandUi.register({
					name: "p",
					label: () => "skynet-prompt",
					description: () => "选择提示词并插入到光标处 / Insert a prompt at the cursor",
					available: () => true,
					ui: {
						kind: "action",
						run: (session) => {
							pickerFor(session.sessionId).show();
						}
					}
				}), "dsh-skynet-prompt: /p");
			});
		}
		//#endregion
		exports.apply = apply;
		exports.inject = inject;
		return module.exports;
	}
});
