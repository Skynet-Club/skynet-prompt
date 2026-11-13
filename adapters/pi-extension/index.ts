/**
 * skynet-prompt 的 pi 抽屉。
 *
 *   ;;            打开：左类目 · 右条目 · 下方预览
 *   ↑↓            选类目 / 条目
 *   → / ←         进列表 / 回类目
 *   Enter         把当前条目的中文原文放进编辑器（不发送）
 *   Esc           关闭，不插入
 *
 * 数据直接读包内 content/，不经过网络，也不调用 psup。
 */

import { readFileSync } from "node:fs";import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import type {
	ExtensionAPI,
	ExtensionCommandContext,
	ExtensionContext,
	Theme,
} from "@earendil-works/pi-coding-agent";
import { CustomEditor } from "@earendil-works/pi-coding-agent";
import {
	matchesKey,
	truncateToWidth,
	visibleWidth,
	wrapTextWithAnsi,
	type Focusable,
} from "@earendil-works/pi-tui";

interface Item {
	id: string;
	cat: string;
	author: string;
	date: string;
	url: string;
	origin: string;
	excerpt: boolean;
	zh: string;
	en: string;
}

interface Cat {
	key: string;
	name: string;
	items: Item[];
}

const ORIGIN: Record<string, string> = {
	verbatim: "本人原话",
	compilation: "他人整理",
	unverified: "未核实",
};

function repoRoot(): string {
	try {
		return join(dirname(fileURLToPath(import.meta.url)), "..", "..");
	} catch {
		return process.cwd();
	}
}

function loadCats(): Cat[] {
	const root = repoRoot();
	const index = JSON.parse(readFileSync(join(root, "content", "index.json"), "utf8"));
	const names: Record<string, string> = index.cat_names ?? {};
	const items: Item[] = index.items.map((row: any) => {
		const base = join(root, "content", "items", row.id);
		return {
			id: row.id,
			cat: row.cat,
			author: row.author,
			date: row.date,
			url: row.url,
			origin: row.origin,
			excerpt: Boolean(row.excerpt),
			zh: readFileSync(join(base, "zh.txt"), "utf8"),
			en: readFileSync(join(base, "en.txt"), "utf8"),
		};
	});
	return Object.keys(index.cats).map((key) => ({
		key,
		name: names[key] ?? key,
		items: items.filter((item) => item.cat === key),
	}));
}

function cell(text: string, width: number): string {
	const clipped = truncateToWidth(text, width, "…");
	return clipped + " ".repeat(Math.max(0, width - visibleWidth(clipped)));
}

function originLabel(item: Item): string {
	const label = ORIGIN[item.origin] ?? item.origin;
	return item.excerpt ? `${label} · 节选` : label;
}

class Picker implements Focusable {
	focused = false;
	private col: 0 | 1 = 0;
	private catIndex = 0;
	private itemIndex = 0;

	constructor(
		private tui: any,
		private theme: Theme,
		private cats: Cat[],
		private done: (item: Item | null) => void,
	) {}

	private get cat(): Cat {
		return this.cats[this.catIndex];
	}

	private get item(): Item | undefined {
		return this.cat.items[this.itemIndex];
	}

	private changed(): void {
		this.tui.requestRender();
	}

	private move(delta: number): void {
		if (this.col === 0) {
			this.catIndex = (this.catIndex + delta + this.cats.length) % this.cats.length;
			this.itemIndex = 0;
		} else {
			const count = this.cat.items.length;
			this.itemIndex = (this.itemIndex + delta + count) % count;
		}
		this.changed();
	}

	handleInput(data: string): void {
		if (matchesKey(data, "escape")) {
			this.done(null);
			return;
		}
		if (matchesKey(data, "left")) {
			this.col = 0;
			this.changed();
			return;
		}
		if (matchesKey(data, "right")) {
			this.col = 1;
			this.changed();
			return;
		}
		if (matchesKey(data, "up")) {
			this.move(-1);
			return;
		}
		if (matchesKey(data, "down")) {
			this.move(1);
			return;
		}
		if (matchesKey(data, "return") || matchesKey(data, "enter")) {
			if (this.col === 0) {
				this.col = 1;
				this.changed();
				return;
			}
			const picked = this.item;
			if (picked) this.done(picked);
		}
	}

	invalidate(): void {}

	render(width: number): string[] {
		const w = Math.max(40, width);
		const leftW = Math.max(16, Math.min(24, Math.floor(w * 0.24)));
		const rightW = Math.max(12, w - leftW - 3);
		const th = this.theme;
		const total = this.cats.reduce((n, c) => n + c.items.length, 0);
		const lines: string[] = [];

		lines.push(truncateToWidth(
			th.fg("accent", "提示词补充") + th.fg("dim", ` · ${total} 条 / ${this.cats.length} 类 · 中文直译`),
			w,
			"",
		));
		lines.push(truncateToWidth(
			th.fg("dim", "↑↓ 选择 · → 进列表 · ← 回类目 · Enter 插入 · Esc 关闭"),
			w,
			"",
		));
		lines.push(th.fg("border", "─".repeat(w)));

		const rows = Math.max(this.cats.length, ...this.cats.map((c) => c.items.length));
		for (let i = 0; i < rows; i++) {
			let left = " ".repeat(leftW);
			if (i < this.cats.length) {
				const cat = this.cats[i]!;
				const selected = i === this.catIndex;
				const active = selected && this.col === 0;
				const name = active
					? th.fg("accent", cat.name)
					: th.fg(selected ? "text" : "muted", cat.name);
				left = cell(`${selected ? "▸ " : "  "}${name} ${th.fg("dim", String(cat.items.length))}`, leftW);
			}

			let right = " ".repeat(rightW);
			if (i < this.cat.items.length) {
				const item = this.cat.items[i]!;
				const selected = i === this.itemIndex;
				const active = selected && this.col === 1;
				const author = ` · ${item.author}`;
				const authorW = Math.min(visibleWidth(author), Math.max(8, Math.floor(rightW / 3)));
				const labelW = Math.max(6, rightW - 2 - authorW);
				const label = truncateToWidth(item.zh.replace(/\s+/g, " "), labelW, "…");
				const labelAnsi = active
					? th.fg("accent", label)
					: th.fg(selected ? "text" : "muted", label);
				right = cell(
					`${selected ? "▸ " : "  "}${labelAnsi}${th.fg("dim", truncateToWidth(author, authorW, ""))}`,
					rightW,
				);
			}

			lines.push(truncateToWidth(left + th.fg("border", " │ ") + right, w, ""));
		}

		const item = this.item;
		if (!item) return lines;

		lines.push(th.fg("border", "─".repeat(w)));
		lines.push(truncateToWidth(
			th.fg("dim", ` ${item.id} · ${this.cat.name} · ${originLabel(item)} · ${item.author} · ${item.date}`),
			w,
			"",
		));
		lines.push(th.fg("muted", " 中文"));
		for (const line of wrapTextWithAnsi(item.zh, Math.max(10, w - 2))) {
			lines.push(" " + line);
		}
		lines.push(th.fg("muted", " 原文"));
		const enLines = wrapTextWithAnsi(item.en, Math.max(10, w - 2));
		for (const line of enLines.slice(0, 3)) {
			lines.push(th.fg("dim", " " + line));
		}
		if (enLines.length > 3) lines.push(th.fg("dim", " …"));
		lines.push(truncateToWidth(th.fg("dim", ` ${item.url}`), w, ""));
		return lines;
	}
}

async function openPicker(
	ctx: ExtensionContext | ExtensionCommandContext,
	before: string,
	after: string,
	cancelText: string | null,
): Promise<void> {
	if (ctx.mode !== "tui") {
		ctx.ui.notify("提示词抽屉需要交互模式", "error");
		return;
	}

	let cats: Cat[];
	try {
		cats = loadCats();
	} catch (error) {
		ctx.ui.notify(`读取 content/ 失败：${String(error)}`, "error");
		return;
	}

	const picked = await ctx.ui.custom<Item | null>((tui, theme, _keybindings, done) =>
		new Picker(tui, theme, cats, done),
	);
	if (!picked) {
		if (cancelText !== null) ctx.ui.setEditorText(cancelText);
		return;
	}

	ctx.ui.setEditorText(before + picked.zh + after);
	ctx.ui.notify(`已补 ${picked.id} · ${cats.find((c) => c.key === picked.cat)?.name ?? ""}`, "info");
}

class SkynetEditor extends CustomEditor {
	private busy = false;

	constructor(
		tui: any,
		theme: any,
		keybindings: any,
		private ctx: ExtensionContext,
	) {
		super(tui, theme, keybindings);
	}

	handleInput(data: string): void {
		if (!this.busy && (data === ";" || data === "；")) {
			const { line, col } = this.getCursor();
			const lines = this.getLines();
			const current = lines[line] ?? "";
			const previous = current[col - 1] ?? "";
			if (col > 0 && (previous === ";" || previous === "；")) {
				const before = [...lines.slice(0, line), current.slice(0, col - 1)].join("\n");
				const after = [current.slice(col), ...lines.slice(line + 1)].join("\n");
				(this as any).cancelAutocomplete?.();
				this.busy = true;
				void openPicker(this.ctx, before, after, before + after)
					.catch((error) => this.ctx.ui.notify(`抽屉失败：${String(error)}`, "error"))
					.finally(() => {
						this.busy = false;
					});
				return;
			}
		}
		super.handleInput(data);
	}
}

export default function (pi: ExtensionAPI) {
	pi.registerCommand("psup", {
		description: "打开提示词抽屉（也可以输入 ;;）",
		handler: async (_args, ctx) => {
			const text = ctx.ui.getEditorText();
			const sep = text && !text.endsWith("\n") ? "\n\n" : "";
			await openPicker(ctx, text + sep, "", null);
		},
	});

	pi.on("input", async (event, ctx) => {
		if (event.source === "interactive" && /[;；]{2}$/.test(event.text)) {
			const before = event.text.slice(0, -2);
			await openPicker(ctx, before, "", before);
			return { action: "handled" };
		}
		return { action: "continue" };
	});

	pi.on("session_start", (_event, ctx) => {
		if (ctx.mode !== "tui") return;
		ctx.ui.setEditorComponent((tui, theme, keybindings) =>
			new SkynetEditor(tui, theme, keybindings, ctx),
		);
	});
}
