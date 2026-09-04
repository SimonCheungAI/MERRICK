/* Live control surface for persistent OpenClaw agent sessions. */
(() => {
  const $ = (id) => document.getElementById(id);
  const panel = $("agent-board-panel");
  const trigger = $("agent-board-btn");
  const closeBtn = $("agent-board-close-btn");
  const title = $("agent-board-title");
  const lede = $("agent-board-lede");
  const stateEl = $("agent-board-state");
  const progressCopy = $("agent-board-progress-copy");
  const count = $("agent-board-count");
  const progressBar = $("agent-board-progress-bar");
  const content = $("agent-board-content");
  const errorEl = $("agent-board-error");
  const refreshBtn = $("agent-board-refresh-btn");
  const newBtn = $("agent-board-new-btn");
  const cancelBtn = $("agent-board-cancel-btn");
  const createForm = $("agent-board-create-form");
  const nameLabel = $("agent-board-name-label");
  const taskLabel = $("agent-board-task-label");
  const nameInput = $("agent-board-name-input");
  const taskInput = $("agent-board-task-input");
  const createCancelBtn = $("agent-board-create-cancel-btn");
  const createSubmitBtn = $("agent-board-create-submit-btn");
  let language = "en";
  let run = null;
  let spawnPending = false;

  const copy = {
    en: {
      title: "Parallel operations",
      lede: "Live OpenClaw agents and their verified results.",
      idle: "IDLE", starting: "STARTING", running: "RUNNING", cancelling: "CANCELLING",
      synthesizing: "SYNTHESIZING", succeeded: "COMPLETE", partial: "PARTIAL",
      failed: "FAILED", cancelled: "CANCELLED",
      noRun: "No active run", noRunBody: "Parallel Plan Mode work will appear here as soon as MERRICK delegates it.",
      progress: (done, total) => `${done} of ${total} agents finished`,
      refresh: "REFRESH", newAgent: "+ NEW AGENT", cancel: "CANCEL RUN", close: "Close Agent Board",
      agentName: "AGENT NAME", agentTask: "TASK", namePlaceholder: "e.g. Security reviewer",
      taskPlaceholder: "Describe the result this agent should produce…", closeForm: "CLOSE",
      startAgent: "START AGENT", startingAgent: "STARTING…", openTerminal: "ENTER TERMINAL",
      closeAgent: "CLOSE", terminalUnavailable: "OpenClaw terminal is not available for this agent yet.",
      queued: "Queued", agentStarting: "Starting", agentRunning: "Working",
      agentCancelling: "Stopping", agentSucceeded: "Complete", agentFailed: "Failed", agentCancelled: "Cancelled",
      timedOut: "Timed out", result: "View result", noResult: "Waiting for a verified result…",
      invalidAgent: "Give the agent a name and a task.",
    },
    zh: {
      title: "并行任务",
      lede: "实时查看 OpenClaw 代理及其经过确认的执行结果。",
      idle: "待命", starting: "正在启动", running: "执行中", cancelling: "正在取消",
      synthesizing: "正在汇总", succeeded: "已完成", partial: "部分完成",
      failed: "失败", cancelled: "已取消",
      noRun: "当前没有运行", noRunBody: "MERRICK 通过计划模式分派并行工作后，代理会显示在这里。",
      progress: (done, total) => `${done} / ${total} 个代理已结束`,
      refresh: "刷新", newAgent: "+ 新建代理", cancel: "取消运行", close: "关闭代理面板",
      agentName: "代理名称", agentTask: "任务", namePlaceholder: "例如：安全审查",
      taskPlaceholder: "说明希望这个代理交付的结果…", closeForm: "关闭",
      startAgent: "启动代理", startingAgent: "正在启动…", openTerminal: "进入终端",
      closeAgent: "关闭", terminalUnavailable: "这个代理的 OpenClaw 终端尚未就绪。",
      queued: "等待中", agentStarting: "正在启动", agentRunning: "执行中",
      agentCancelling: "正在终止", agentSucceeded: "已完成", agentFailed: "失败", agentCancelled: "已取消",
      timedOut: "已超时", result: "查看结果", noResult: "正在等待经过确认的结果…",
      invalidAgent: "请填写代理名称和任务。",
    },
  };
  const t = (key) => copy[language][key] || copy.en[key] || key;
  const send = (detail) => window.dispatchEvent(new CustomEvent("merrick-agent-board-send", { detail }));

  function setVisible(visible) {
    if (!panel) return;
    panel.hidden = !visible;
    trigger?.setAttribute("aria-expanded", String(visible));
  }

  function stateCopy(value) {
    return t(value && Object.hasOwn(copy[language], value) ? value : "idle");
  }

  function childStateCopy(value) {
    const key = {
      queued: "queued", starting: "agentStarting", running: "agentRunning",
      cancelling: "agentCancelling",
      succeeded: "agentSucceeded", failed: "agentFailed", cancelled: "agentCancelled",
      timed_out: "timedOut",
    }[value] || "queued";
    return t(key);
  }

  function agentCard(child, index) {
    const card = document.createElement("article");
    card.className = "agent-card";
    card.dataset.state = child.status || "queued";

    const rail = document.createElement("span");
    rail.className = "agent-card-index";
    rail.textContent = String(index + 1).padStart(2, "0");
    const body = document.createElement("div");
    body.className = "agent-card-body";
    const head = document.createElement("div");
    head.className = "agent-card-head";
    const name = document.createElement("strong");
    name.textContent = child.label || `Agent ${index + 1}`;
    const status = document.createElement("span");
    status.className = "agent-card-status";
    status.textContent = childStateCopy(child.status);
    head.append(name, status);
    body.append(head);

    const actions = document.createElement("div");
    actions.className = "agent-card-actions";
    const terminal = document.createElement("button");
    terminal.className = "agent-card-terminal";
    terminal.type = "button";
    terminal.textContent = t("openTerminal");
    terminal.disabled = child.can_open !== true || typeof child.session_url !== "string";
    terminal.addEventListener("click", () => {
      const url = typeof child.session_url === "string" ? child.session_url : "";
      if (!url) {
        errorEl.textContent = t("terminalUnavailable");
        errorEl.hidden = false;
        return;
      }
      if (typeof nativePost === "function" && nativePost("openOpenClawSession", { url })) return;
      window.open(url, "_blank", "noopener,noreferrer");
    });
    const closeAgent = document.createElement("button");
    closeAgent.className = "agent-card-close";
    closeAgent.type = "button";
    closeAgent.textContent = t("closeAgent");
    closeAgent.disabled = child.status === "cancelling";
    closeAgent.addEventListener("click", () => {
      if (run?.id && child.id) {
        send({ type: "multi_agent_close_child", run_id: run.id, child_id: child.id });
      }
    });
    actions.append(terminal, closeAgent);
    body.append(actions);

    const resultText = typeof child.result === "string" && child.result.trim()
      ? child.result.trim()
      : (typeof child.error === "string" && child.error.trim() ? child.error.trim() : "");
    if (resultText) {
      const details = document.createElement("details");
      details.className = "agent-result";
      const summary = document.createElement("summary");
      summary.textContent = t("result");
      const result = document.createElement("p");
      result.textContent = resultText;
      details.append(summary, result);
      body.append(details);
    } else {
      const waiting = document.createElement("p");
      waiting.className = "agent-card-waiting";
      waiting.textContent = t("noResult");
      body.append(waiting);
    }
    card.append(rail, body);
    return card;
  }

  function render() {
    if (!panel) return;
    title.textContent = t("title");
    lede.textContent = t("lede");
    closeBtn.setAttribute("aria-label", t("close"));
    refreshBtn.textContent = t("refresh");
    newBtn.textContent = t("newAgent");
    cancelBtn.textContent = t("cancel");
    nameLabel.textContent = t("agentName");
    taskLabel.textContent = t("agentTask");
    nameInput.placeholder = t("namePlaceholder");
    taskInput.placeholder = t("taskPlaceholder");
    createCancelBtn.textContent = t("closeForm");
    createSubmitBtn.textContent = spawnPending ? t("startingAgent") : t("startAgent");
    createSubmitBtn.disabled = spawnPending;
    content.replaceChildren();
    errorEl.hidden = true;

    if (!run || typeof run !== "object") {
      stateEl.textContent = t("idle");
      stateEl.dataset.state = "idle";
      progressCopy.textContent = t("noRun");
      count.textContent = "0 / 0";
      progressBar.style.width = "0%";
      cancelBtn.disabled = true;
      newBtn.disabled = false;
      const empty = document.createElement("div");
      empty.className = "agent-board-empty";
      const strong = document.createElement("strong");
      strong.textContent = t("noRun");
      const paragraph = document.createElement("p");
      paragraph.textContent = t("noRunBody");
      empty.append(strong, paragraph);
      content.append(empty);
      return;
    }

    const allChildren = Array.isArray(run.children) ? run.children : [];
    const children = allChildren.filter((child) => child?.closed !== true);
    const total = Number(run.progress?.total) || children.length;
    const done = Number(run.progress?.completed) || 0;
    const state = typeof run.status === "string" ? run.status : "idle";
    stateEl.textContent = stateCopy(state);
    stateEl.dataset.state = state;
    progressCopy.textContent = run.goal || t("progress")(done, total);
    count.textContent = `${done} / ${total}`;
    progressBar.style.width = `${total ? Math.min(100, Math.round((done / total) * 100)) : 0}%`;
    cancelBtn.disabled = !["starting", "running", "synthesizing"].includes(state);
    newBtn.disabled = ["cancelling", "synthesizing"].includes(state)
      || (["starting", "running"].includes(state) && allChildren.length >= 8);
    children.forEach((child, index) => content.append(agentCard(child, index)));
    if (typeof run.error === "string" && run.error.trim()) {
      errorEl.textContent = run.error;
      errorEl.hidden = false;
    }
  }

  trigger?.addEventListener("click", () => {
    const opening = panel?.hidden;
    setVisible(opening);
    if (opening) send({ type: "multi_agent_refresh" });
  });
  closeBtn?.addEventListener("click", () => setVisible(false));
  refreshBtn?.addEventListener("click", () => send({ type: "multi_agent_refresh" }));
  newBtn?.addEventListener("click", () => {
    createForm.hidden = !createForm.hidden;
    if (!createForm.hidden) nameInput.focus();
  });
  createCancelBtn?.addEventListener("click", () => { createForm.hidden = true; });
  createForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    const label = nameInput.value.trim();
    const task = taskInput.value.trim();
    if (!label || !task) {
      errorEl.textContent = t("invalidAgent");
      errorEl.hidden = false;
      return;
    }
    const joinable = run && ["starting", "running"].includes(run.status) ? run.id : "";
    spawnPending = true;
    createSubmitBtn.disabled = true;
    createSubmitBtn.textContent = t("startingAgent");
    send({ type: "multi_agent_spawn", run_id: joinable, label, task });
  });
  cancelBtn?.addEventListener("click", () => {
    if (run?.id) send({ type: "multi_agent_cancel", run_id: run.id });
  });
  panel?.addEventListener("click", (event) => { if (event.target === panel) setVisible(false); });

  window.MerrickAgentBoard = {
    close: () => setVisible(false),
    setLanguage(nextLanguage) {
      language = nextLanguage === "zh" ? "zh" : "en";
      render();
    },
    handleMessage(message) {
      if (message.type === "multi_agent_state") {
        run = message.run && typeof message.run === "object" ? message.run : null;
        if (spawnPending) {
          spawnPending = false;
          nameInput.value = "";
          taskInput.value = "";
          createForm.hidden = true;
        }
        if (run && ["starting", "running", "cancelling", "synthesizing"].includes(run.status)) {
          window.MerrickPlanMode?.close();
          setVisible(true);
        }
        render();
      } else if (message.type === "multi_agent_error") {
        spawnPending = false;
        createSubmitBtn.disabled = false;
        createSubmitBtn.textContent = t("startAgent");
        setVisible(true);
        errorEl.textContent = typeof message.text === "string" ? message.text : t("failed");
        errorEl.hidden = false;
      }
    },
    handleTerminalOpenResult(ok, message) {
      if (ok) return;
      setVisible(true);
      errorEl.textContent = typeof message === "string" && message ? message : t("terminalUnavailable");
      errorEl.hidden = false;
    },
  };
  const pendingMessage = window.__merrickPendingMultiAgentMessage;
  delete window.__merrickPendingMultiAgentMessage;
  if (pendingMessage) window.MerrickAgentBoard.handleMessage(pendingMessage);
  else render();
  // app.js can receive the initial server snapshot before this deferred module is ready.
  // Request it again once the board owns its message handler so restored runs are visible.
  send({ type: "multi_agent_refresh" });
})();
