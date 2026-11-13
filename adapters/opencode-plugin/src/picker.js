export function createPicker({ psup, select, append, alert, toast, currentRoute }) {
  return async function openPicker() {
    const route = currentRoute?.()
    if (route?.type !== "session") {
      toast({
        title: "skynet-prompt",
        message: "请在会话中打开提示词选择器。",
        variant: "warning",
        duration: 3000,
      })
      return
    }

    let categories
    try {
      categories = psup("categories", "--json").filter((row) => row.count > 0)
    } catch (error) {
      await alert({
        title: "读取提示词类目失败",
        message: `psup categories --json 失败：${String(error)}`,
      })
      return
    }
    const category = await select({
      title: "skynet-prompt · 选择类目",
      placeholder: "搜索类目",
      options: categories.map((row) => ({
        title: `${row.name}  ${row.count}`,
        value: row.key,
      })),
    })
    if (!category) return

    const categoryName = categories.find((row) => row.key === category)?.name ?? category
    let items
    try {
      items = psup("list", "--json").filter((item) => item.cat === category)
    } catch (error) {
      await alert({
        title: "读取提示词失败",
        message: `psup list --json 失败：${String(error)}`,
      })
      return
    }
    const itemId = await select({
      title: `skynet-prompt · ${categoryName}`,
      placeholder: "搜索 id、中文或作者",
      options: items.map((item) => ({
        title: `${item.id}  ${item.zh.slice(0, 38)}  · ${item.author}`,
        value: item.id,
      })),
    })
    if (!itemId) return

    const item = items.find((row) => row.id === itemId)
    if (!item) return
    if (!(await append(item.zh))) {
      await alert({
        title: "无法追加到输入框",
        message: `opencode 未暴露 prompt.append API。\n\n${item.zh}`,
      })
      return
    }
    toast({
      title: `已补 ${item.id}`,
      message: `${categoryName} · ${item.zh.slice(0, 40)}`,
      variant: "success",
      duration: 4000,
    })
  }
}
