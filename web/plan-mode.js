/* MERRICK Plan Mode panel. Keeps plan presentation outside app.js. */
(() => {
  const $ = (id) => document.getElementById(id);
  const panel = $("plan-mode-panel");
  const title = $("plan-mode-title");
  const lede = $("plan-mode-lede");
  const closeBtn = $("plan-mode-close-btn");
  const form = $("plan-mode-form");
  const goalLabel = $("plan-mode-goal-label");
  const goalInput = $("plan-mode-goal");
  const createBtn = $("plan-mode-create-btn");
  const statusEl = $("plan-mode-status");
  const content = $("plan-mode-content");
  const actions = $("plan-mode-actions");
  const runNextBtn = $("plan-mode-run-next-btn");
  const runAllBtn = $("plan-mode-run-all-btn");
  const cancelBtn = $("plan-mode-cancel-btn");
  const trigger = $("plan-mode-btn");
  let language = "en";
  let plan = null;
  let origin = "manual";
  let renderedPlanId = "";

  const copy = {
    en: {
      title: "Plan a goal", lede: "Choose an approach, then run the next step or the full plan.", autoLede: "MERRICK identified this as a multi-step task. Review, revise, or run an approach.",
      goal: "Goal", placeholder: "What would you like MERRICK to accomplish?", create: "CREATE PLAN", replan: "REPLAN",
      planning: "MERRICK is preparing approaches…", choose: "Choose an approach before running it.",
      selected: "SELECTED", select: "CHOOSE THIS APPROACH", next: "RUN NEXT", all: "RUN ALL",
      cancel: "CANCEL", running: "Plan is running…", succeeded: "Plan complete.",
      failed: "A plan step failed.", cancelled: "Plan cancelled.", blocked: "Plan is blocked.",
      status: "STATUS", recommendation: "RECOMMENDED", noPlan: "Describe a goal to create a flexible execution plan.",
      parallel: "PARALLEL",
      dismiss: "Close Plan Mode",
    },
    zh: {
      title: "计划模式", lede: "选择一种方案，再执行下一步或完整计划。", autoLede: "MERRICK 判断这是一项分段任务。请审阅、修改目标重新规划，或执行方案。",
      goal: "目标", placeholder: "希望 MERRICK 完成什么？", create: "生成计划", replan: "重新规划",
      planning: "MERRICK 正在准备方案…", choose: "请先选择一种方案。",
      selected: "已选择", select: "选择此方案", next: "执行下一步", all: "执行全部",
      cancel: "取消", running: "计划正在执行…", succeeded: "计划已完成。",
      failed: "计划步骤执行失败。", cancelled: "计划已取消。", blocked: "计划已阻塞。",
      status: "状态", recommendation: "推荐", noPlan: "描述一个目标，MERRICK 会生成可选择的执行计划。",
      parallel: "并行",
      dismiss: "关闭计划模式",
    },
  };
  const t = (key) => copy[language][key] || copy.en[key] || key;
  const send = (detail) => window.dispatchEvent(new CustomEvent("merrick-plan-send", { detail }));

  function setVisible(visible) {
    if (!panel) return;
    panel.hidden = !visible;
    trigger?.setAttribute("aria-expanded", String(visible));
    if (visible) requestAnimationFrame(() => goalInput?.focus());
  }

  function statusCopy(status) {
    if (status === "planning") return t("planning");
    if (status === "running") return t("running");
    if (status === "succeeded") return t("succeeded");
    if (status === "failed") return t("failed");
    if (status === "cancelled") return t("cancelled");
    if (status === "blocked") return t("blocked");
    return plan?.selected_approach_id ? t("selected") : t("choose");
  }

  function render() {
    if (!panel) return;
    title.textContent = t("title");
    lede.textContent = origin === "auto" && plan ? t("autoLede") : t("lede");
    goalLabel.textContent = t("goal");
    goalInput.placeholder = t("placeholder");
    createBtn.textContent = plan ? t("replan") : t("create");
    closeBtn.setAttribute("aria-label", t("dismiss"));
    content.replaceChildren();
    const currentStatus = plan?.status || "draft";
    statusEl.textContent = statusCopy(currentStatus);
    statusEl.dataset.state = currentStatus;
    if (!plan) {
      const empty = document.createElement("p");
      empty.className = "plan-mode-empty";
      empty.textContent = t("noPlan");
      content.append(empty);
      actions.hidden = true;
      return;
    }
    if (plan.id !== renderedPlanId) {
      goalInput.value = plan.goal || "";
      renderedPlanId = plan.id;
    }
    const approaches = Array.isArray(plan.approaches) ? plan.approaches : [];
    approaches.forEach((approach) => {
      const card = document.createElement("article");
      const selected = approach.id === plan.selected_approach_id;
      card.className = `plan-approach${selected ? " selected" : ""}`;
      const heading = document.createElement("div");
      heading.className = "plan-approach-heading";
      const headingText = document.createElement("strong");
      headingText.textContent = approach.title || "Approach";
      heading.append(headingText);
      if (approach.recommended === true) {
        const badge = document.createElement("span");
        badge.className = "plan-badge";
        badge.textContent = t("recommendation");
        heading.append(badge);
      }
      if (approach.execution_mode === "parallel") {
        const modeBadge = document.createElement("span");
        modeBadge.className = "plan-badge parallel";
        modeBadge.textContent = t("parallel");
        heading.append(modeBadge);
      }
      const summary = document.createElement("p");
      summary.textContent = approach.summary || "";
      const steps = document.createElement("ol");
      steps.className = "plan-steps";
      (Array.isArray(approach.steps) ? approach.steps : []).forEach((step) => {
        const item = document.createElement("li");
        item.dataset.status = step.status || "planned";
        const stepTitle = document.createElement("strong");
        stepTitle.textContent = step.title || "Step";
        const detail = document.createElement("span");
        detail.textContent = step.result || step.detail || "";
        item.append(stepTitle, detail);
        steps.append(item);
      });
      const select = document.createElement("button");
      select.type = "button";
      select.className = "setup-action-btn secondary plan-select-btn";
      select.textContent = selected ? t("selected") : t("select");
      select.disabled = selected || ["running", "succeeded", "cancelled"].includes(plan.status);
      select.addEventListener("click", () => send({
        type: "plan_mode_select", plan_id: plan.id, approach_id: approach.id,
      }));
      card.append(heading, summary, steps, select);
      content.append(card);
    });
    const canRun = Boolean(plan.selected_approach_id) && ["ready", "running"].includes(plan.status);
    actions.hidden = !plan.selected_approach_id || ["succeeded", "failed", "cancelled", "blocked"].includes(plan.status);
    runNextBtn.textContent = t("next");
    runAllBtn.textContent = t("all");
    cancelBtn.textContent = t("cancel");
    runNextBtn.disabled = !canRun;
    runAllBtn.disabled = !canRun;
    cancelBtn.disabled = plan.status !== "running";
  }

  form?.addEventListener("submit", (event) => {
    event.preventDefault();
    const goal = goalInput?.value.trim() || "";
    if (!goal) {
      statusEl.textContent = t("noPlan");
      goalInput?.focus();
      return;
    }
    plan = null;
    renderedPlanId = "";
    statusEl.textContent = t("planning");
    statusEl.dataset.state = "planning";
    content.replaceChildren();
    actions.hidden = true;
    send({ type: "plan_mode_create", goal });
  });
  closeBtn?.addEventListener("click", () => { setVisible(false); send({ type: "plan_mode_dismiss" }); });
  trigger?.addEventListener("click", () => setVisible(panel?.hidden));
  runNextBtn?.addEventListener("click", () => plan && send({ type: "plan_mode_run", plan_id: plan.id, mode: "next" }));
  runAllBtn?.addEventListener("click", () => plan && send({ type: "plan_mode_run", plan_id: plan.id, mode: "all" }));
  cancelBtn?.addEventListener("click", () => plan && send({ type: "plan_mode_cancel", plan_id: plan.id }));
  panel?.addEventListener("click", (event) => { if (event.target === panel) setVisible(false); });

  window.MerrickPlanMode = {
    close: () => setVisible(false),
    setLanguage(nextLanguage) { language = nextLanguage === "zh" ? "zh" : "en"; render(); },
    handleMessage(message) {
      if (message.type === "plan_mode_state") {
        plan = message.plan && typeof message.plan === "object" ? message.plan : null;
        origin = message.origin === "auto" ? "auto" : "manual";
        setVisible(true);
        render();
      } else if (message.type === "plan_mode_step" && plan) {
        const approach = (plan.approaches || []).find((item) => item.id === plan.selected_approach_id);
        const step = approach?.steps?.find((item) => item.id === message.step_id);
        if (step) { step.status = message.status; step.result = message.result || ""; }
        render();
      } else if (message.type === "plan_mode_error") {
        setVisible(true);
        statusEl.textContent = typeof message.text === "string" ? message.text : t("failed");
        statusEl.dataset.state = "failed";
      }
    },
  };
  render();
})();
