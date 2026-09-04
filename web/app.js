/* MERRICK HUD frontend — 流式对话 + 全息点云 */

const $ = (id) => document.getElementById(id);
const reactor = $("reactor");
const stateLabel = $("state-label");
const interimEl = $("interim");
const chatEl = $("chat");
const syslogEl = $("syslog");
const micBtn = $("mic-btn");
const textInput = $("text-input");
const sendBtn = $("send-btn");
const ttsToggle = $("tts-toggle");
const autoToggle = $("auto-toggle");
const connDot = $("conn-dot");
const connText = $("conn-text");
const watchModeBtn = $("watch-mode-btn");
const meetingModeBtn = $("meeting-mode-btn");
const setupBtn = $("setup-btn");
const setupPanel = $("setup-panel");
const setupCloseBtn = $("setup-close-btn");
const openWorkspaceBtn = $("open-workspace-btn");
const openOpenClawDashboardBtn = $("open-openclaw-dashboard-btn");
const openClawDashboardStatus = $("openclaw-dashboard-status");
const voiceprintUnlockBtn = $("voiceprint-unlock-btn");
const voiceprintEnrollBtn = $("voiceprint-enroll-btn");
const voiceprintStatus = $("voiceprint-status");
const memoryExportBtn = $("memory-export-btn");
const memoryExportStatus = $("memory-export-status");
const uninstallBtn = $("uninstall-btn");
const automationAccessRoot = $("automation-access-root");
const automationAccessEnable = $("automation-access-enable");
const automationAccessChoose = $("automation-access-choose");
const automationAccessSave = $("automation-access-save");
const automationAuditOpen = $("automation-audit-open");
const automationAccessStatus = $("automation-access-status");
const automationAccessTitle = $("automation-access-title");
const automationAccessDescription = $("automation-access-description");
const automationAccessEnableLabel = $("automation-access-enable-label");
const providerOpenBtn = $("provider-open-btn");
const providerCurrent = $("provider-current");
const providerConnectionSummary = $("provider-connection-summary");
const providerActiveModel = $("provider-active-model");
const providerRuntimeLabel = $("provider-runtime-label");
const providerModelSelect = $("provider-model-select");
const providerModelsRefresh = $("provider-models-refresh");
const providerModelsStatus = $("provider-models-status");
const capabilitiesOpenBtn = $("capabilities-open-btn");
const capabilitiesSummary = $("capabilities-summary");
const capabilitiesPanel = $("capabilities-panel");
const capabilitiesCloseBtn = $("capabilities-close-btn");
const capabilitiesSearch = $("capabilities-search");
const capabilitiesRefreshBtn = $("capabilities-refresh-btn");
const capabilitiesDiagnoseBtn = $("capabilities-diagnose-btn");
const capabilitiesStatus = $("capabilities-status");
const harnessModeStatus = $("harness-mode-status");
const capabilityList = $("capability-list");
const capabilityDiagnostics = $("capabilities-diagnostics");
const capabilityReview = $("capability-review");
const capabilityReviewTitle = $("capability-review-title");
const capabilityReviewDescription = $("capability-review-description");
const capabilityReviewTrust = $("capability-review-trust");
const capabilityReviewSurfaces = $("capability-review-surfaces");
const capabilityReviewRequirements = $("capability-review-requirements");
const capabilityReviewCancel = $("capability-review-cancel");
const capabilityReviewConfirm = $("capability-review-confirm");
const openClawApproval = $("openclaw-approval");
const openClawApprovalTitle = $("openclaw-approval-title");
const openClawApprovalDescription = $("openclaw-approval-description");
const openClawApprovalMeta = $("openclaw-approval-meta");
const openClawApprovalActions = $("openclaw-approval-actions");
const pluginCount = $("plugin-count");
const catalogCount = $("catalog-count");
const skillCount = $("skill-count");
const onboardingPanel = $("onboarding-panel");
const providerDetail = $("provider-detail");
const providerModelInput = $("provider-model-input");
const providerBaseUrlRow = $("provider-base-url-row");
const providerBaseUrlInput = $("provider-base-url-input");
const providerKeyRow = $("provider-key-row");
const providerKeyInput = $("provider-key-input");
const providerSecurityNote = $("provider-security-note");
const providerConnectBtn = $("provider-connect-btn");
const providerSkipBtn = $("provider-skip-btn");
const providerCancelBtn = $("provider-cancel-btn");
const providerDeviceCode = $("provider-device-code");
const providerAuthCard = $("provider-auth-card");
const providerVerificationLink = $("provider-verification-link");
const providerSetupStatus = $("provider-setup-status");
const providerBackBtn = $("provider-back-btn");
const providerCloseBtn = $("provider-close-btn");
const speechLanguageSelect = $("speech-language-select");
const speechLanguageStatus = $("speech-language-status");
const settingsAddressEnglish = $("settings-address-english");
const settingsAddressChinese = $("settings-address-chinese");
const onboardingAddressEnglish = $("onboarding-address-english");
const onboardingAddressChinese = $("onboarding-address-chinese");
const saveAddressBtn = $("save-address-btn");
const addressStatus = $("address-status");
const displayBtn = $("display-btn");
const researchDisplay = $("research-display");
const researchCloseBtn = $("research-close-btn");
const researchQuery = $("research-query");
const researchQueryChoice = $("research-query-choice");
const researchQueryChoiceQuestion = $("research-query-choice-question");
const researchQueryChoiceOptions = $("research-query-choice-options");
const displayAnswer = $("display-answer");
const researchSources = $("research-sources");
const openAllSourcesBtn = $("open-all-sources-btn");
const organizerBtn = $("organizer-btn");
const organizerPanel = $("organizer-panel");
const organizerCloseBtn = $("organizer-close-btn");
const organizerRefreshBtn = $("organizer-refresh-btn");
const organizerFullscreenBtn = $("organizer-fullscreen-btn");
const organizerUpdated = $("organizer-updated");
const organizerStatus = $("organizer-status");
const organizerStats = $("organizer-stats");
const personalOperationsStatus = $("personal-operations-status");
const personalOperationsMode = $("personal-operations-mode");
const personalOperationsPolicy = $("personal-operations-policy");
const organizerTaskCount = $("organizer-task-count");
const organizerTaskList = $("organizer-task-list");
const organizerReminderList = $("organizer-reminder-list");
const organizerProjectList = $("organizer-project-list");
const organizerLatestBriefing = $("organizer-journal-feature");
const intelligenceTitleInput = $("intelligence-title-input");
const intelligencePromptInput = $("intelligence-prompt-input");
const intelligenceTimeInput = $("intelligence-time-input");
const intelligenceEnabledInput = $("intelligence-enabled-input");
const intelligenceSaveBtn = $("intelligence-save-btn");
const intelligenceGenerateBtn = $("intelligence-generate-btn");
const intelligenceSubscriptionList = $("intelligence-subscription-list");
const intelligenceEditionFeature = $("intelligence-edition-feature");
const intelligenceEditionList = $("intelligence-edition-list");
const journalMonthLabel = $("journal-month-label");
const journalCalendar = $("journal-calendar");
const journalPrevMonth = $("journal-prev-month");
const journalNextMonth = $("journal-next-month");
const journalToday = $("journal-today");
const organizerMeetingList = $("organizer-meeting-list");
const organizerSettingList = $("organizer-setting-list");
const organizerCommandGuide = $("organizer-command-guide");

const STATE_LABELS = {
  offline: "state_offline",
  booting: "state_booting",
  connecting: "state_connecting",
  idle: "state_idle",
  listening: "state_listening",
  thinking: "state_thinking",
  acting: "state_acting",
  speaking: "state_speaking",
};

let ws = null;
let reconnectAttempts = 0;
let reconnectTimer = null;
let serverState = "booting"; // 后端上报的状态
let uiState = "booting";     // 实际展示（listening/speaking 由本地决定）
let currentTurn = 0;         // 当前对话回合，用于丢弃过期音频
let activeAssistantText = "";
let assistantEchoGuardUntil = 0;
let responseComplete = true;
let bargeInMode = false;
let nativeTranscriptStabilityTimer = null;
let nativeTranscriptStabilityEpoch = 0;
let committedSpeech = "";
let bargeCandidate = "";
let bargeCandidateHits = 0;
let bargeCandidateSince = 0;
let bargeCandidateGrowth = 0;
let bargeCandidateNovelCount = 0;
let speechResumeBlockedUntil = 0;
let playbackStartedAt = 0;
let voiceLevel = 0;
let recentVoiceEvidenceAt = 0;
let bargeEchoCancellationActive = false;
let pendingNativeCleanVoiceActivity = false;
let pendingNativeCleanVoiceBaseline = "";
let nativeCleanVoiceActivityConfirmed = false;
let autoListenTimer = null;
let nativeActionInFlight = null;
let appClosing = false;
let watchModeEnabled = false;
let watchModeOwnerVerified = false;
let watchModeBufferedTranscript = null;
let watchCleanVoiceActive = false;
let watchVoiceVerificationRequested = false;
let watchVerificationTimeout = null;
let meetingModeEnabled = false;
let meetingLatestTranscript = "";
let meetingCommandActive = false;
let meetingCommandTranscript = "";
let meetingPendingTranscript = "";
let meetingTranscriptFlushTimer = null;
let meetingCleanVoiceActive = false;
let meetingCommandInterruptPending = false;
let voiceprintUnlocked = false;
let voiceprintRecording = false;
let onboardingRequired = false;
// The onboarding panel is also the normal connection manager. Keep a manual
// request open after receiving provider state; otherwise an already-complete
// first-run flag immediately hides it again when the user clicks “Manage
// model connection”.
let providerManagerRequested = false;
let selectedProvider = "codex";
let providerConnectionState = null;
let providerRuntimeState = null;
let providerAttempt = null;
let providerDraftInitialized = false;
let providerModelCatalog = { provider: "", models: [], status: "idle" };
let providerCatalogRequest = 0;
let automationAccessState = null;
// A saved CLI profile can become invalid after the provider refreshes or
// revokes its session. Keep that state visible in Settings, but never let it
// take over the active conversation, research display, or action progress.
let providerAuthRequired = false;
let conversationLanguage = "en";
let currentResearchSources = [];
let activeResearchChoiceId = "";
let capabilityInventory = { plugins: [], skills: [], summary: null, snapshot: null, harness: null };
let capabilityCatalog = [];
let capabilityCatalogMutationAllowed = false;
let capabilityTab = "plugins";
let capabilityBusy = false;
let pendingCapabilityReview = null;
let capabilitySearchTimer = null;
let organizerSnapshot = null;
let organizerView = "overview";
let selectedBriefingId = "";
let selectedIntelligenceEditionId = "";
let selectedJournalDate = new Date().toLocaleDateString("en-CA");
let journalVisibleMonth = new Date(new Date().getFullYear(), new Date().getMonth(), 1);
let newspaperFocusActive = false;
let newspaperFocusEditionId = "";
let newspaperFocusScrollTop = 0;
let newspaperFocusInvoker = null;
let newspaperFocusInertNodes = [];
let nativeWindowMode = "normal";
let nativeFullscreenRequestId = "";

function appendDisplayInline(element, text) {
  const pattern = /(\*\*[^*\n]+?\*\*|\$\$[\s\S]+?\$\$|\$[^$\n]+?\$)/g;
  let cursor = 0;
  for (const match of text.matchAll(pattern)) {
    if (match.index > cursor) element.append(document.createTextNode(text.slice(cursor, match.index)));
    const raw = match[0];
    if (raw.startsWith("**")) {
      const strong = document.createElement("strong");
      strong.textContent = raw.slice(2, -2);
      element.append(strong);
      cursor = match.index + raw.length;
      continue;
    }
    const formula = raw.slice(raw.startsWith("$$") ? 2 : 1, raw.endsWith("$$") ? -2 : -1);
    const node = document.createElement("span");
    node.className = raw.startsWith("$$") ? "math-display" : "math-inline";
    if (window.katex) {
      try { window.katex.render(formula, node, { displayMode: raw.startsWith("$$"), throwOnError: false }); }
      catch { node.textContent = raw; }
    } else node.textContent = raw;
    element.append(node);
    cursor = match.index + raw.length;
  }
  if (cursor < text.length) element.append(document.createTextNode(text.slice(cursor)));
}

function renderDisplayText(element, text) {
  if (!element) return;
  element.replaceChildren();
  let activeList = null;
  for (const rawLine of String(text || "").split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line) {
      activeList = null;
      continue;
    }
    const heading = line.match(/^(#{1,3})\s+(.+)$/);
    if (heading) {
      activeList = null;
      const node = document.createElement(heading[1].length === 1 ? "h2" : "h3");
      node.className = "display-report-heading";
      appendDisplayInline(node, heading[2]);
      element.append(node);
      continue;
    }
    const bullet = line.match(/^(?:[-*•]|\d+[.)])\s+(.+)$/);
    if (bullet) {
      if (!activeList) {
        activeList = document.createElement("ul");
        activeList.className = "display-report-list";
        element.append(activeList);
      }
      const item = document.createElement("li");
      appendDisplayInline(item, bullet[1]);
      activeList.append(item);
      continue;
    }
    activeList = null;
    const paragraph = document.createElement("p");
    paragraph.className = "display-report-paragraph";
    appendDisplayInline(paragraph, line);
    element.append(paragraph);
  }
}

function setResearchDisplayVisible(visible) {
  if (!researchDisplay) return;
  researchDisplay.hidden = !visible;
}

function clearResearchQueryChoice() {
  activeResearchChoiceId = "";
  if (researchQueryChoice) researchQueryChoice.hidden = true;
  if (researchQueryChoiceOptions) researchQueryChoiceOptions.replaceChildren();
}

function showResearchQueryChoice(message) {
  const choiceId = typeof message.choice_id === "string" ? message.choice_id : "";
  const options = Array.isArray(message.options)
    ? message.options.filter((option) => typeof option === "string" && option.length > 1).slice(0, 3)
    : [];
  if (!/^[0-9a-f]{32}$/i.test(choiceId) || options.length < 2 || !researchQueryChoiceOptions) return;
  activeResearchChoiceId = choiceId;
  if (researchQueryChoiceQuestion) {
    researchQueryChoiceQuestion.textContent = typeof message.question === "string" && message.question.trim()
      ? message.question.trim()
      : (conversationLanguage === "zh" ? "请选择要检索的话题" : "Choose the topic to search");
  }
  researchQueryChoiceOptions.replaceChildren();
  options.forEach((option, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.decision = decision;
    button.className = "research-query-choice-option";
    button.textContent = option;
    button.addEventListener("click", () => {
      if (!activeResearchChoiceId) return;
      const choiceButtons = researchQueryChoiceOptions.querySelectorAll("button");
      choiceButtons.forEach((item) => { item.disabled = true; });
      sendJson({ type: "select_research_query", choice_id: activeResearchChoiceId, index });
    });
    researchQueryChoiceOptions.appendChild(button);
  });
  if (displayAnswer) {
    displayAnswer.textContent = conversationLanguage === "zh"
      ? "语音识别得到多个合理的技术术语。请选择后，MERRICK 才会开始搜索。"
      : "Speech recognition produced more than one plausible technical term. MERRICK will search only after you choose.";
  }
  setResearchDisplayVisible(true);
  researchQueryChoice.hidden = false;
}

function renderResearchSources() {
  if (!researchSources) return;
  researchSources.replaceChildren();
  const hasSources = currentResearchSources.length > 0;
  const sourcePanel = researchSources.closest(".source-display");
  const grid = researchSources.closest(".research-grid");
  if (sourcePanel) sourcePanel.hidden = !hasSources;
  if (grid) grid.classList.toggle("report-only", !hasSources);
  for (const source of currentResearchSources) {
    const card = document.createElement("article"); card.className = "research-source";
    const title = document.createElement("strong"); title.textContent = source.title || source.url;
    const snippet = document.createElement("p"); snippet.textContent = source.snippet || source.url;
    const button = document.createElement("button"); button.type = "button"; button.className = "setup-action-btn"; button.textContent = t("open_in_merrick");
    button.addEventListener("click", () => nativePost("openResearchPages", { urls: [source.url] }));
    card.append(title, snippet, button); researchSources.append(card);
  }
  if (openAllSourcesBtn) openAllSourcesBtn.disabled = currentResearchSources.length === 0;
}

const PROVIDERS = Object.fromEntries(
  Object.entries(MERRICK_RUNTIME_CONTRACT.providers).map(([id, spec]) => [id, {
    title: spec.title,
    model: spec.defaultModel,
    auth: spec.authMode,
    custom: spec.baseUrlRequired === true,
    detail: spec.detail,
  }]),
);
const CONNECTION_FAILURES = MERRICK_RUNTIME_CONTRACT.connectionFailures;
const CONNECTION_STAGES = MERRICK_RUNTIME_CONTRACT.connectionStages;

function connectionFailureCopy(code, { short = false } = {}) {
  const failure = CONNECTION_FAILURES[code] || CONNECTION_FAILURES.PROVIDER_FAILED;
  if (conversationLanguage === "zh") return short ? failure.shortZh : failure.messageZh;
  return short ? failure.shortEn : failure.messageEn;
}

// The HUD has one interface language at a time. Keep this dictionary local so
// changing speech language is instantaneous and never requires a round trip to
// the model or a browser reload.
const UI_COPY = {
  en: {
    brand_sub: "Personal desktop assistant", connecting: "CONNECTING", system_log: "SYSTEM LOG",
    state_offline: "OFFLINE", state_booting: "BOOTING", state_connecting: "CONNECTING MODEL", state_idle: "STANDBY", state_listening: "LISTENING", state_thinking: "THINKING", state_acting: "ACTING", state_speaking: "SPEAKING",
    expand_title: "Expand or collapse the control panel", close_title: "Quit MERRICK completely", interrupt_title: "Click to interrupt MERRICK", mic_title: "Voice input (Space also works)", command_placeholder: "Instruction… (Enter to send)",
    send: "SEND", voice_reply: "VOICE REPLY", continuous_conversation: "CONTINUOUS CONVERSATION", watch_mode: "WATCH MODE", watch_mode_owner: "WATCH MODE · OWNER ONLY", watch_title: "Only a verified owner voice enters conversation", meeting_mode: "MEETING MODE", meeting_mode_notes: "MEETING MODE · NOTES ONLY", meeting_title: "Continuously transcribe; answer only when addressed as Merrick", organizer: "ASSISTANT", organizer_title: "Open the personal assistant dashboard", setup: "SETUP", setup_title: "Open MERRICK settings", display: "DISPLAY", display_title: "Open research and answer display",
    organizer_eyebrow: "MERRICK · PERSONAL OPERATIONS", organizer_heading: "Personal Assistant", organizer_lede: "Projects, commitments, reminders and briefings — one private operational view.", close_organizer: "Close personal assistant dashboard", organizer_overview: "OVERVIEW", organizer_intelligence: "INTELLIGENCE", organizer_journal: "JOURNAL", organizer_meetings: "MEETINGS", organizer_schedule: "SCHEDULE", organizer_now: "NOW", organizer_tasks: "Tasks", organizer_next: "NEXT", organizer_reminders: "Reminders", organizer_portfolio: "PORTFOLIO", organizer_projects: "Projects", organizer_operations: "OPERATIONS CONTROL", organizer_operations_heading: "What MERRICK can do safely", organizer_archive: "ARCHIVE", organizer_automation: "AUTOMATION", organizer_delivery_heading: "Choose what MERRICK prepares — and when.", organizer_delivery_lede: "Work-review editions are optional. Intelligence newspapers have their own schedule in the Intelligence studio.", organizer_commands: "VOICE & TEXT COMMANDS", organizer_commands_heading: "Speak naturally in Chinese or English.",
    intelligence_studio: "EDITORIAL STUDIO", intelligence_heading: "Describe any newspaper you want.", intelligence_lede: "Write the goal in your own words. MERRICK decides what to research and how to structure it; there is no fixed subject questionnaire.", intelligence_title: "Newspaper name", intelligence_goal: "Editorial goal", intelligence_time: "Daily delivery", intelligence_enable: "Enable daily edition", intelligence_save: "SAVE BRIEF", intelligence_save_generate: "SAVE & GENERATE NOW", intelligence_title_placeholder: "e.g. Global Markets Morning Paper", intelligence_prompt_placeholder: "Describe what you want to understand, compare, monitor, and why…", intelligence_archive: "Intelligence editions", journal_calendar: "WORK CALENDAR", journal_lede: "MERRICK records structured work automatically. Select a date to open that day as an operational newspaper.", journal_previous: "Previous month", journal_next: "Next month", journal_today: "TODAY",
    eyebrow_settings: "MERRICK · SETTINGS", settings_title: "MERRICK Settings", your_documents: "YOUR DOCUMENTS", your_documents_description: "Put PDFs, Word documents, and any material MERRICK should read in the Documents folder of this Workspace. MERRICK writes summaries there too.", open_workspace: "Open Workspace in Finder",
    model_connection: "MODEL CONNECTION", model_connection_description: "Choose the model MERRICK uses to think. Subscription sign-in is managed by MERRICK and never changes this Mac's Codex or OpenClaw login; API keys stay in macOS Keychain and never enter the Workspace, logs, or GitHub.", checking_connection: "Checking connection…", manage_model_connection: "Manage model connection",
    capabilities_title: "OPENCLAW WORKSPACE", capabilities_description: "OpenClaw is MERRICK's execution kernel. Discover, review, install and manage plugins and Skills directly here; the full Control UI remains available for advanced setup.", checking_capabilities: "Checking OpenClaw workspace…", open_openclaw_dashboard: "Open OpenClaw Control UI", manage_capabilities: "Manage extensions", opening_openclaw_dashboard: "Preparing a secure one-time OpenClaw session…", openclaw_dashboard_opened: "OpenClaw Control UI opened in your browser.", openclaw_dashboard_unavailable: "OpenClaw Control UI could not be opened.",
    voice_language: "VOICE LANGUAGE", voice_language_description: "Switching updates local speech recognition, conversation language, and voice output together. Both languages use the same local Merrick voice identity.", conversation_language: "Conversation language", language_english: "English · Merrick", language_chinese: "Chinese · Merrick", language_english_active: "ENGLISH · MERRICK ACTIVE", language_chinese_active: "中文 · MERRICK 已开启", address_title: "HOW MERRICK ADDRESSES YOU", address_description: "Set separate forms of address for English and Chinese. This remains only on this Mac.", address_english: "English address", address_chinese: "Chinese address", save_address: "Save forms of address", address_saved: "Forms of address saved locally.", address_invalid: "Enter two short forms of address.",
    voiceprint_vault: "VOICEPRINT VAULT", voiceprint_description: "Add a voice sample manually to recognise the owner and protect private memory. Audio is processed only in local memory and is never saved as a recording.", locked_mac_auth: "LOCKED · Mac authentication required", unlock_with_mac: "Unlock with Mac password", enroll_voice_sample: "Enroll a 4-second voice sample", voiceprint_hint: "After unlocking, enrol and read naturally: “Hello Merrick, this is my private voice profile.”",
    memory_export: "PRIVATE MEMORY EXPORT", memory_export_description: "Export MERRICK private memory, preferences, revisions, and meeting records as a timestamped ZIP. Mac password or Touch ID is required; API keys, model connections, voiceprints, and Workspace documents are excluded.", export_with_mac: "Export memory with Mac password", uninstall_title: "UNINSTALL", uninstall_description: "Stop every MERRICK process and remove local memory, Workspace files, settings, voiceprint, model credentials, and permission records.", uninstall_action: "Uninstall and erase local data",
    eyebrow_openclaw: "MERRICK · OPENCLAW CONTROL", skills_plugins: "Skills & Plugins", capabilities_lede: "Discover, review, install and manage OpenClaw plugins and Skills inside MERRICK. OpenClaw still performs every change and exposes source, integrity and permissions before installation.", capabilities_search: "Search name, capability, or ClawHub…", refresh: "REFRESH", run_diagnostics: "RUN DIAGNOSTICS", loading_inventory: "Loading capability inventory…", plugins: "INSTALLED", discover: "DISCOVER", skills: "SKILLS", capability_review_eyebrow: "OPENCLAW · SECURITY REVIEW", capability_review_enable: "Enable {name}", capability_review_disable: "Disable {name}", capability_review_install: "Install {name}", capability_review_upgrade: "Update {name}", capability_review_uninstall: "Remove {name}", capability_review_policy: "Security review for {name}", capability_review_capabilities: "Permissions requested by {name}", capability_review_trust: "OpenClaw review: {trust}", capability_review_none: "No additional capability surfaces were declared.", capability_review_requirements: "Setup still needed: {items}", capability_review_confirm_enable: "ENABLE", capability_review_confirm_disable: "DISABLE", capability_review_confirm_install: "INSTALL", capability_review_confirm_upgrade: "UPDATE", capability_review_confirm_uninstall: "REMOVE", capability_review_confirm_continue: "CONTINUE", capability_review_loading: "Asking OpenClaw to inspect this capability…", capability_review_applying: "Applying the approved change…", catalog_loading: "Loading OpenClaw catalog…", catalog_search_hint: "Type at least two characters to search verified ClawHub packages.", install: "INSTALL", update: "UPDATE", remove: "REMOVE", installed: "INSTALLED", official: "OFFICIAL", community: "COMMUNITY", local: "LOCAL", cancel: "CANCEL",
    eyebrow_research: "MERRICK · RESEARCH DISPLAY", live_answer: "Live answer", sources_local: "SOURCES · LOCAL WEB PANELS", open_all_sources: "Open all sources in MERRICK", display_caption: "Streaming captions appear here. Formulas render locally when available.",
    eyebrow_first_run: "MERRICK · FIRST RUN", connect_intelligence: "Connect your intelligence layer.", onboarding_lede: "Choose a provider now. You can change it later in SETUP. MERRICK remains a native desktop app and keeps provider secrets in your Mac Keychain.", step_provider: "01 · Provider", step_connect: "02 · Connect", step_ready: "03 · Ready", back_to_settings: "← Back to settings", provider_codex: "ChatGPT / Codex subscription", provider_claude: "Reuse local Claude CLI login", provider_openai: "Platform API key", provider_anthropic: "Claude API key", provider_gemini: "Google AI Studio key", provider_kimi: "Moonshot API key", provider_deepseek: "DeepSeek API key", provider_custom: "Custom", provider_custom_description: "OpenAI-compatible endpoint", model: "Model", base_url: "Base URL", api_key: "API key", api_key_placeholder: "Paste key — it is never shown again", connect_codex: "Connect Codex", use_existing_connection: "Use existing MERRICK connection",
    online: "ONLINE", offline: "OFFLINE", you: "YOU", open_in_merrick: "Open in MERRICK", preparing_answer: "MERRICK is preparing an answer…", research_sources: "Research sources", no_capability_matches: "No local capability matches that search.", no_capabilities: "No local capabilities found.", active: "ACTIVE", inactive: "OFF", ready: "READY", setup_needed: "SETUP NEEDED", core_locked: "CORE · LOCKED", disable: "DISABLE", enable: "ENABLE", requires: "Requires", readonly_diagnostics: "READ-ONLY DIAGNOSTICS", no_diagnostics: "No capability problems reported by OpenClaw.", lifecycle_ready: "Ready", lifecycle_disabled: "Disabled", lifecycle_dependency_missing: "Dependency missing", lifecycle_unhealthy: "Unavailable", lifecycle_core: "Core reviewed", lifecycle_unreviewed: "Not reviewed", lifecycle_not_assessed_connection: "Connection not assessed", lifecycle_not_assessed_authorization: "Authorization not assessed", lifecycle_policy_managed: "Policy managed", capability_candidate: "Candidate domains", risk_ceiling: "risk ceiling", domain_mail: "Mail", domain_calendar: "Calendar", domain_documents: "Documents", domain_desktop: "Desktop", domain_web: "Web", domain_media: "Media", capability_snapshot_stale: "Live discovery is unavailable. Showing the last safe capability snapshot.",
    close_settings: "Close settings", close_connection_setup: "Close connection setup", close_capabilities: "Close capability manager", close_display: "Close display", setup_progress: "Setup progress", setup_failed: "Provider setup could not be completed.", connecting_provider: "Connecting…", model_required: "Please enter a model ID.", base_url_required: "Please enter the provider’s HTTPS base URL.", api_key_required: "Please enter a valid API key.", saving_key: "Saving securely to macOS Keychain…", opening_sign_in: "Opening the local sign-in flow…", keeping_connection: "Keeping the current local MERRICK connection…", playback_blocked: "Audio playback was blocked. Click anywhere in the window and try again.", interrupt_sent: "Interrupt request sent.", plugin_changed: "Plugin updated and the local OpenClaw gateway is ready again.", skill_changed: "Skill preference updated; OpenClaw will refresh it on the next turn.", diagnostics_complete: "Read-only diagnostics completed.", capability_failed: "Capability management failed.", screen_desktop_only: "One-time screen viewing is available only in the MERRICK desktop app.",
  },
  zh: {
    brand_sub: "你的私人桌面助理", connecting: "正在连接", system_log: "系统日志",
    state_offline: "离线", state_booting: "启动中", state_connecting: "正在连接模型", state_idle: "待命", state_listening: "聆听中", state_thinking: "思考中", state_acting: "执行中", state_speaking: "回应中",
    expand_title: "展开或收起控制面板", close_title: "完全退出 MERRICK", interrupt_title: "点击打断 MERRICK", mic_title: "语音输入（空格键也可）", command_placeholder: "向 MERRICK 下达指令…（回车发送）",
    send: "发送", voice_reply: "语音回复", continuous_conversation: "连续对话", watch_mode: "观影模式", watch_mode_owner: "观影模式 · 仅主人", watch_title: "仅让已验证的主人声纹进入对话", meeting_mode: "会议模式", meeting_mode_notes: "会议模式 · 仅记录", meeting_title: "持续转录；仅称呼 Merrick 时回答", organizer: "助理", organizer_title: "打开个人助理工作台", setup: "设置", setup_title: "打开 MERRICK 设置", display: "展示", display_title: "打开研究与回答展示",
    organizer_eyebrow: "MERRICK · 个人工作中枢", organizer_heading: "个人助理", organizer_lede: "项目、承诺、提醒与简报，在一个私密清晰的工作视图中。", close_organizer: "关闭个人助理工作台", organizer_overview: "总览", organizer_intelligence: "情报报纸", organizer_journal: "工作日志", organizer_meetings: "会议", organizer_schedule: "计划", organizer_now: "当前", organizer_tasks: "任务", organizer_next: "接下来", organizer_reminders: "提醒", organizer_portfolio: "项目组合", organizer_projects: "项目", organizer_operations: "操作控制", organizer_operations_heading: "MERRICK 可以安全完成什么", organizer_archive: "归档", organizer_automation: "自动化", organizer_delivery_heading: "选择 MERRICK 何时为你准备哪些内容。", organizer_delivery_lede: "工作复盘版本可选开启；定制情报报纸可在“情报报纸”中单独设置时间。", organizer_commands: "语音与文字指令", organizer_commands_heading: "直接使用中文或英文自然表达。",
    intelligence_studio: "编辑部", intelligence_heading: "描述你想要的任何一份报纸。", intelligence_lede: "直接用自己的话写目标。MERRICK 会动态决定研究什么、如何组织，不使用固定领域问卷。", intelligence_title: "报纸名称", intelligence_goal: "编辑目标", intelligence_time: "每日送达", intelligence_enable: "开启每日版本", intelligence_save: "保存目标", intelligence_save_generate: "保存并立即生成", intelligence_title_placeholder: "例如：全球市场晨报", intelligence_prompt_placeholder: "写下你想理解、比较、跟踪的内容，以及为什么……", intelligence_archive: "情报报纸归档", journal_calendar: "工作日历", journal_lede: "MERRICK 自动记录结构化工作。选择日期，即可把当天内容作为工作报纸打开。", journal_previous: "上个月", journal_next: "下个月", journal_today: "今天",
    eyebrow_settings: "MERRICK · 设置", settings_title: "MERRICK 设置", your_documents: "你的文档", your_documents_description: "把 PDF、Word 文档和需要 MERRICK 读取的资料放在此工作区的 Documents 文件夹。MERRICK 写出的摘要也会保存在这里。", open_workspace: "在 Finder 中打开工作区",
    model_connection: "模型连接", model_connection_description: "选择 MERRICK 用来思考的模型。订阅登录由 MERRICK 单独管理，不会读取或修改这台 Mac 的 Codex / OpenClaw 登录；API 密钥只保存在 macOS 钥匙串，不会写入工作区、日志或 GitHub。", checking_connection: "正在检查连接…", manage_model_connection: "管理模型连接",
    capabilities_title: "OPENCLAW 工作台", capabilities_description: "OpenClaw 是 MERRICK 的执行内核。你可以在这里直接发现、审查、安装和管理插件与 Skills；高级设置仍可打开完整 Control UI。", checking_capabilities: "正在检查 OpenClaw 工作台…", open_openclaw_dashboard: "打开 OpenClaw Control UI", manage_capabilities: "管理扩展", opening_openclaw_dashboard: "正在准备安全的一次性 OpenClaw 会话…", openclaw_dashboard_opened: "OpenClaw Control UI 已在浏览器中打开。", openclaw_dashboard_unavailable: "无法打开 OpenClaw Control UI。",
    voice_language: "语音语言", voice_language_description: "切换会同时更新本机语音识别、对话语言和语音输出；中英文统一使用本地 Merrick 声纹。", conversation_language: "对话语言", language_english: "英语 · Merrick", language_chinese: "中文 · Merrick", language_english_active: "英语 · Merrick 已开启", language_chinese_active: "中文 · Merrick 已开启", address_title: "MERRICK 对你的称呼", address_description: "分别设置英文与中文称呼；它只保存在这台 Mac 上。", address_english: "英文称呼", address_chinese: "中文称呼", save_address: "保存称呼", address_saved: "称呼已保存到本机。", address_invalid: "请填写两个简短称呼。",
    voiceprint_vault: "声纹保险库", voiceprint_description: "手动加入声音样本，用于识别主人和保护私人记忆。原始音频只在本机内存中处理，不会保存为录音文件。", locked_mac_auth: "已锁定 · 需要 Mac 验证", unlock_with_mac: "使用 Mac 密码解锁", enroll_voice_sample: "录入 4 秒声音样本", voiceprint_hint: "解锁后，点击录入并自然朗读：“Hello Merrick, this is my private voice profile.”",
    memory_export: "私人记忆导出", memory_export_description: "导出 MERRICK 的私人记忆、偏好、修订记录和会议记录为带时间戳的 ZIP 文件。导出前需通过 Mac 密码或 Touch ID 验证；不会包含 API 密钥、模型连接、声纹或工作区文档。", export_with_mac: "使用 Mac 密码导出记忆", uninstall_title: "卸载", uninstall_description: "关闭所有 MERRICK 进程，并删除本机记忆、Workspace、设置、声纹、模型凭据和权限记录。", uninstall_action: "卸载并删除本机数据",
    eyebrow_openclaw: "MERRICK · OPENCLAW 控制", skills_plugins: "技能与插件", capabilities_lede: "在 MERRICK 内发现、审查、安装并管理 OpenClaw 插件与 Skills。所有变更仍由 OpenClaw 执行，并在安装前展示来源、完整性和权限。", capabilities_search: "搜索名称、能力或 ClawHub…", refresh: "刷新", run_diagnostics: "运行诊断", loading_inventory: "正在加载能力清单…", plugins: "已安装", discover: "发现", skills: "技能", capability_review_eyebrow: "OPENCLAW · 安全审查", capability_review_enable: "启用 {name}", capability_review_disable: "停用 {name}", capability_review_install: "安装 {name}", capability_review_upgrade: "升级 {name}", capability_review_uninstall: "移除 {name}", capability_review_policy: "审查 {name} 的安全提示", capability_review_capabilities: "{name} 请求的权限", capability_review_trust: "OpenClaw 审查：{trust}", capability_review_none: "没有声明额外的能力入口。", capability_review_requirements: "仍需配置：{items}", capability_review_confirm_enable: "确认启用", capability_review_confirm_disable: "确认停用", capability_review_confirm_install: "确认安装", capability_review_confirm_upgrade: "确认升级", capability_review_confirm_uninstall: "确认移除", capability_review_confirm_continue: "继续", capability_review_loading: "正在请求 OpenClaw 检查这项能力……", capability_review_applying: "正在应用已确认的更改……", catalog_loading: "正在读取 OpenClaw 插件目录……", catalog_search_hint: "输入至少两个字符，即可搜索经过 OpenClaw 验证的 ClawHub 插件。", install: "安装", update: "升级", remove: "移除", installed: "已安装", official: "官方", community: "社区", local: "本机", cancel: "取消",
    eyebrow_research: "MERRICK · 研究展示", live_answer: "实时回答", sources_local: "来源 · 本机网页面板", open_all_sources: "在 MERRICK 中打开全部来源", display_caption: "流式字幕会显示在这里；公式可在本机正确渲染。",
    eyebrow_first_run: "MERRICK · 初次设置", connect_intelligence: "连接你的智能层。", onboarding_lede: "现在选择模型提供方，之后可在“设置”中更改。MERRICK 保持原生桌面 App，提供方密钥会保存在 Mac 钥匙串。", step_provider: "01 · 提供方", step_connect: "02 · 连接", step_ready: "03 · 就绪", back_to_settings: "← 返回设置", provider_codex: "ChatGPT / Codex 订阅", provider_claude: "复用本机 Claude CLI 登录", provider_openai: "平台 API 密钥", provider_anthropic: "Claude API 密钥", provider_gemini: "Google AI Studio 密钥", provider_kimi: "Moonshot API 密钥", provider_deepseek: "DeepSeek API 密钥", provider_custom: "自定义", provider_custom_description: "兼容 OpenAI 的接口", model: "模型", base_url: "基础 URL", api_key: "API 密钥", api_key_placeholder: "粘贴密钥 — 之后不会再次显示", connect_codex: "连接 Codex", use_existing_connection: "使用现有 MERRICK 连接",
    online: "在线", offline: "离线", you: "你", open_in_merrick: "在 MERRICK 中打开", preparing_answer: "MERRICK 正在准备回答…", research_sources: "研究来源", no_capability_matches: "没有符合搜索条件的本机能力。", no_capabilities: "未找到本机能力。", active: "已启用", inactive: "已关闭", ready: "已就绪", setup_needed: "需要配置", core_locked: "核心 · 已锁定", disable: "停用", enable: "启用", requires: "需要", readonly_diagnostics: "只读诊断", no_diagnostics: "OpenClaw 未报告能力问题。", lifecycle_ready: "依赖就绪", lifecycle_disabled: "已停用", lifecycle_dependency_missing: "依赖缺失", lifecycle_unhealthy: "暂不可用", lifecycle_core: "核心已审查", lifecycle_unreviewed: "尚未审查", lifecycle_not_assessed_connection: "连接未评估", lifecycle_not_assessed_authorization: "授权未评估", lifecycle_policy_managed: "受策略管理", capability_candidate: "候选领域", risk_ceiling: "风险上限", domain_mail: "邮件", domain_calendar: "日历", domain_documents: "文档", domain_desktop: "桌面", domain_web: "网页", domain_media: "媒体", capability_snapshot_stale: "实时发现暂不可用，当前显示的是上一次安全能力快照。",
    close_settings: "关闭设置", close_connection_setup: "关闭连接设置", close_capabilities: "关闭能力管理", close_display: "关闭展示", setup_progress: "设置进度", setup_failed: "模型提供方配置未能完成。", connecting_provider: "正在连接…", model_required: "请输入模型 ID。", base_url_required: "请输入服务商的 HTTPS 基础 URL。", api_key_required: "请输入有效的 API 密钥。", saving_key: "正在安全保存到 macOS 钥匙串…", opening_sign_in: "正在打开本机登录流程…", keeping_connection: "正在保留当前本机 MERRICK 连接…", playback_blocked: "音频自动播放被阻止。请点击窗口任意处后重试。", interrupt_sent: "已发送打断指令。", plugin_changed: "插件已更新，本机 OpenClaw 网关已重新就绪。", skill_changed: "技能偏好已更新；OpenClaw 会在下一轮对话刷新。", diagnostics_complete: "只读诊断已完成。", capability_failed: "能力管理失败。", screen_desktop_only: "一次性查看屏幕仅能在 MERRICK 桌面 App 中使用。",
  },
};

function t(key, fallback = key) {
  const connectionCopy = {
    provider_code_instruction: ["Enter this code in the browser to authorize MERRICK.", "请在浏览器中输入以下验证码，授权 MERRICK。"],
    provider_open_signin: ["Open secure sign-in", "打开安全登录页面"],
    provider_code_wait: ["Keep this window open. MERRICK will verify the connection after approval.", "请保留此窗口。完成授权后，MERRICK 会自动验证连接。"],
  };
  if (connectionCopy[key]) return connectionCopy[key][conversationLanguage === "zh" ? 1 : 0];
  return UI_COPY[conversationLanguage]?.[key] || UI_COPY.en[key] || fallback;
}

function tf(key, values = {}) {
  return Object.entries(values).reduce(
    (copy, [name, value]) => copy.replaceAll(`{${name}}`, String(value)),
    t(key),
  );
}

function applyInterfaceLanguage(language) {
  conversationLanguage = language === "zh" ? "zh" : "en";
  document.documentElement.lang = conversationLanguage === "zh" ? "zh-CN" : "en";
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const key = element.dataset.i18n;
    if (key && element.dataset.i18nDynamic !== "true") element.textContent = t(key, element.textContent);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    const key = element.dataset.i18nPlaceholder;
    if (key) element.placeholder = t(key, element.placeholder);
  });
  document.querySelectorAll("[data-i18n-title]").forEach((element) => {
    const key = element.dataset.i18nTitle;
    if (key) element.title = t(key, element.title);
  });
  document.querySelectorAll("[data-i18n-aria-label]").forEach((element) => {
    const key = element.dataset.i18nAriaLabel;
    if (key) element.setAttribute("aria-label", t(key, element.getAttribute("aria-label") || ""));
  });
  refreshMicControl();
  setUiState(uiState);
  if (connText) connText.textContent = ws?.readyState === WebSocket.OPEN ? t("online") : serverState === "offline" ? t("offline") : t("connecting");
  if (watchModeBtn) watchModeBtn.textContent = t(watchModeEnabled ? "watch_mode_owner" : "watch_mode");
  if (meetingModeBtn) meetingModeBtn.textContent = t(meetingModeEnabled ? "meeting_mode_notes" : "meeting_mode");
  if (providerConnectionState) displayProviderConnection(providerConnectionState);
  updateCapabilitySummary(capabilityInventory.summary);
  renderHarnessStatus(capabilityInventory.harness);
  renderCapabilityInventory();
  renderProviderForm({ preserveStatus: true });
  if (automationAccessTitle) automationAccessTitle.textContent = language === "zh" ? "自动化与文件" : "AUTOMATION & FILES";
  if (automationAccessDescription) automationAccessDescription.textContent = language === "zh" ? "选择一个项目或用户文件夹。启用后，MERRICK 可直接读取和修改该文件夹内的文件；每一次更改都会在本机记录，方便审查。" : "Choose one project or user folder. Once enabled, MERRICK can directly read and change files in that folder; each change is recorded locally for review.";
  if (automationAccessEnableLabel) automationAccessEnableLabel.textContent = language === "zh" ? "启用直接自动化" : "Enable Direct Automation";
  if (automationAccessChoose) automationAccessChoose.textContent = language === "zh" ? "选择文件夹" : "Choose folder";
  if (automationAccessSave) automationAccessSave.textContent = language === "zh" ? "应用权限" : "Apply access";
  if (automationAuditOpen) automationAuditOpen.textContent = language === "zh" ? "打开审计记录" : "Open audit records";
  renderAutomationAccessState(automationAccessState);
  if (addressStatus?.dataset.state === "ready") addressStatus.textContent = t("address_saved");
  renderOrganizerSnapshot();
}

function renderAutomationAccessState(state) {
  if (!state || typeof state !== "object") return;
  if (automationAccessEnable) automationAccessEnable.checked = state.enabled === true;
  if (automationAccessRoot) {
    const root = typeof state.root === "string" && state.root ? state.root : "";
    automationAccessRoot.textContent = root
      ? (conversationLanguage === "zh" ? `已授权目录 · ${root}` : `AUTHORIZED ROOT · ${root}`)
      : (conversationLanguage === "zh" ? "尚未选择文件夹。" : "No folder selected.");
    automationAccessRoot.dataset.state = root ? "ready" : "pending";
  }
  if (automationAccessStatus && typeof state.message === "string") {
    automationAccessStatus.textContent = state.message;
    automationAccessStatus.dataset.state = state.ok === false ? "error" : state.ok === true ? "ready" : "";
  }
}

window.merrickNativeAutomationAccessState = function (state) {
  if (!state || typeof state !== "object") return;
  automationAccessState = state;
  renderAutomationAccessState(state);
};
// The microphone button is an explicit user override. It must win over the
// continuous-conversation preference and all automatic restart paths.
let listeningManuallyMuted = false;
const shockwaves = [];
const pageParams = new URLSearchParams(location.hash.slice(1));
const isDesktop = pageParams.has("desktop");
const bridgeToken = pageParams.get("bridge") || "";
const nativeBridge = window.webkit?.messageHandlers?.jarvis;

function nativePost(action, payload = {}) {
  if (!nativeBridge || !bridgeToken) return false;
  // The native bridge is privileged (microphone, window movement, research
  // windows), so every message is bound to this desktop-app launch. Put the
  // trusted fields last so callers cannot override them through `payload`.
  nativeBridge.postMessage({ ...payload, action, bridge: bridgeToken });
  return true;
}

function createNativeRequestId() {
  if (typeof crypto?.randomUUID === "function") return crypto.randomUUID();
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, (value) => value.toString(16).padStart(2, "0")).join("");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

function updateNativeFullscreenControl() {
  const transitional = nativeWindowMode === "entering" || nativeWindowMode === "exiting";
  const fullscreen = nativeWindowMode === "fullscreen" || nativeWindowMode === "exiting";
  document.querySelectorAll("[data-native-fullscreen-control]").forEach((control) => {
    if (!(control instanceof HTMLButtonElement)) return;
    control.hidden = !isDesktop;
    control.disabled = transitional;
    control.classList.toggle("is-active", fullscreen);
    control.setAttribute("aria-pressed", String(fullscreen));
    control.setAttribute("aria-busy", String(transitional));
    control.setAttribute("aria-label", fullscreen ? "Exit full screen" : "Enter full screen");
    const label = control.querySelector("span");
    if (label) label.textContent = transitional
      ? (nativeWindowMode === "entering" ? "ENTERING…" : "EXITING…")
      : (fullscreen ? "EXIT FULL SCREEN" : "FULL SCREEN");
  });
  document.body.classList.toggle("native-fullscreen", fullscreen);
}

function requestNativeFullscreen(mode = "toggle") {
  if (!isDesktop || !["enter", "exit", "toggle"].includes(mode)) return false;
  if (nativeWindowMode === "entering" || nativeWindowMode === "exiting") return false;
  const requestId = createNativeRequestId();
  if (!nativePost("setWindowFullscreen", { mode, requestId })) {
    setOrganizerStatus("Native full screen is unavailable in this preview.", "error");
    return false;
  }
  nativeFullscreenRequestId = requestId;
  nativeWindowMode = mode === "exit" || (mode === "toggle" && nativeWindowMode === "fullscreen")
    ? "exiting" : "entering";
  updateNativeFullscreenControl();
  return true;
}

window.merrickNativeFullscreenState = (state = {}) => {
  if (!state || !["normal", "entering", "fullscreen", "exiting"].includes(state.mode)) return;
  if (state.requestId && nativeFullscreenRequestId && state.requestId !== nativeFullscreenRequestId) return;
  nativeWindowMode = state.mode;
  if (state.mode === "normal" || state.mode === "fullscreen") nativeFullscreenRequestId = "";
  updateNativeFullscreenControl();
  if (state.error) setOrganizerStatus(state.error, "error");
};

updateNativeFullscreenControl();

const SUPPORTED_MEDIA_PLAYERS = new Set(["active", "music", "spotify"]);
const SUPPORTED_MEDIA_ACTIONS = new Set(["play", "pause", "toggle", "next", "previous"]);
const GUI_KEYS = new Set(["enter", "tab", "escape", "space", "up", "down", "left", "right", "pageup", "pagedown", "home", "end"]);

function hasExactKeys(value, expected) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const keys = Object.keys(value).sort();
  const wanted = [...expected].sort();
  return keys.length === wanted.length && keys.every((key, index) => key === wanted[index]);
}

function validNativeActionQuery(value, maximumLength) {
  return typeof value === "string" && value.length > 0 &&
    Array.from(value).length <= maximumLength && value === value.trim() &&
    !/[\u0000-\u001f\u007f]/.test(value);
}

function validNativeApplicationName(value) {
  return validNativeActionQuery(value, 80) && !/[\\/]/.test(value);
}

function validateNativeAction(value) {
  if (!value || typeof value !== "object" || Array.isArray(value) ||
      typeof value.type !== "string") return null;
  switch (value.type) {
    case "open_app":
      return hasExactKeys(value, ["type", "app"]) &&
        validNativeApplicationName(value.app)
        ? { type: value.type, app: value.app } : null;
    case "close_app":
      return hasExactKeys(value, ["type", "app"]) &&
        validNativeApplicationName(value.app)
        ? { type: value.type, app: value.app } : null;
    case "browser_search":
      return hasExactKeys(value, ["type", "browser", "query"]) &&
        (value.browser === "default" || validNativeApplicationName(value.browser)) &&
        validNativeActionQuery(value.query, 300)
        ? { type: value.type, browser: value.browser, query: value.query } : null;
    case "browser_open_url":
      return hasExactKeys(value, ["type", "browser", "url"]) &&
        (value.browser === "default" || validNativeApplicationName(value.browser)) &&
        validNativeActionQuery(value.url, 2048) && /^https?:\/\//i.test(value.url)
        ? { type: value.type, browser: value.browser, url: value.url } : null;
    case "maps_search":
      return hasExactKeys(value, ["type", "query"]) && validNativeActionQuery(value.query, 300)
        ? { type: value.type, query: value.query } : null;
    case "spotify_search":
      return hasExactKeys(value, ["type", "query"]) && validNativeActionQuery(value.query, 160)
        ? { type: value.type, query: value.query } : null;
    case "media_control":
      return hasExactKeys(value, ["type", "player", "action"]) &&
        typeof value.player === "string" && SUPPORTED_MEDIA_PLAYERS.has(value.player) &&
        typeof value.action === "string" && SUPPORTED_MEDIA_ACTIONS.has(value.action)
        && (value.player !== "active" || value.action === "pause")
        ? { type: value.type, player: value.player, action: value.action } : null;
    case "play_music":
      return hasExactKeys(value, ["type", "player", "query"]) &&
        value.player === "music" && validNativeActionQuery(value.query, 160)
        ? { type: value.type, player: value.player, query: value.query } : null;
    case "volume_control":
      return hasExactKeys(value, ["type", "action"]) &&
        (value.action === "up" || value.action === "down" ||
         value.action === "mute" || value.action === "unmute")
        ? { type: value.type, action: value.action } : null;
    case "gui_interaction": {
      if (!hasExactKeys(value, ["type", "steps"]) || !Array.isArray(value.steps) ||
          value.steps.length === 0 || value.steps.length > 6) return null;
      const steps = [];
      for (const step of value.steps) {
        if (!step || typeof step !== "object" || Array.isArray(step)) return null;
        if (step.op === "click" && hasExactKeys(step, ["op", "x", "y"]) &&
            Number.isInteger(step.x) && Number.isInteger(step.y) &&
            step.x >= 0 && step.x <= 1000 && step.y >= 0 && step.y <= 1000) {
          steps.push({ op: "click", x: step.x, y: step.y });
        } else if (step.op === "scroll" && hasExactKeys(step, ["op", "dy"]) &&
            Number.isInteger(step.dy) && step.dy >= -8 && step.dy <= 8 && step.dy !== 0) {
          steps.push({ op: "scroll", dy: step.dy });
        } else if (step.op === "key" && hasExactKeys(step, ["op", "key"]) && GUI_KEYS.has(step.key)) {
          steps.push({ op: "key", key: step.key });
        } else if (step.op === "type" && hasExactKeys(step, ["op", "text"]) &&
            validNativeActionQuery(step.text, 240)) {
          steps.push({ op: "type", text: step.text });
        } else return null;
      }
      return { type: value.type, steps };
    }
    default:
      return null;
  }
}

function rejectNativeAction(requestId, error) {
  sendJson({
    type: "native_action_result",
    request_id: requestId,
    ok: false,
    result: null,
    error: String(error || "The desktop action failed.").slice(0, 400),
  });
}

// ---------------- state / HUD ----------------
function setUiState(s) {
  uiState = s;
  // The compact HUD always retains one concise live status. Stale *progress*
  // copy is cleared separately when a task returns to idle.
  stateLabel.textContent = t(STATE_LABELS[s], s.toUpperCase());
  stateLabel.hidden = false;
}

function refreshUiState() {
  if (audioPlaying) return setUiState("speaking");
  // A native recognizer stop is asynchronous.  Once the server has accepted a
  // final utterance, its processing/action state must win immediately instead
  // of leaving the HUD on LISTENING until macOS reports that the microphone
  // request has fully torn down.
  if (serverState === "thinking" || serverState === "acting") return setUiState(serverState);
  if (recognizing) return setUiState("listening");
  setUiState(serverState);
}

function refreshMicControl() {
  micBtn.classList.toggle("muted", listeningManuallyMuted);
  micBtn.setAttribute("aria-pressed", String(!listeningManuallyMuted));
  micBtn.title = listeningManuallyMuted
    ? (conversationLanguage === "zh" ? "收听已关闭（点击开启）" : "Listening is off (click to enable)")
    : (conversationLanguage === "zh" ? "正在收听（点击关闭）" : "Listening is on (click to disable)");
}

function logLine(tag, text) {
  const div = document.createElement("div");
  div.className = "entry";
  const t = new Date().toTimeString().slice(0, 8);
  div.innerHTML = `<span class="t">${t}</span><span class="tag-${tag}"></span>`;
  div.querySelector(`.tag-${tag}`).textContent = text;
  syslogEl.appendChild(div);
  syslogEl.scrollTop = syslogEl.scrollHeight;
}

function addMsg(who, text) {
  // The Transcript panel is intentionally absent from the desktop HUD. Keep
  // this helper tolerant so the conversation/audio pipeline does not depend
  // on a visual history element.
  if (!chatEl) return null;
  const div = document.createElement("div");
  div.className = "msg " + (who === "user" ? "user" : "jarvis");
  const label = document.createElement("span");
  label.className = "who";
  label.textContent = who === "user" ? t("you") : "MERRICK";
  div.appendChild(label);
  const body = document.createElement("span");
  body.className = "body";
  body.textContent = text;
  div.appendChild(body);
  chatEl.appendChild(div);
  chatEl.scrollTop = chatEl.scrollHeight;
  return body;
}

// 流式气泡：增量文本追加到同一条消息里
let streamBody = null;
function appendDelta(text) {
  interimEl.textContent = "";
  activeAssistantText += text;
  if (!chatEl) return;
  if (!streamBody) streamBody = addMsg("jarvis", "");
  streamBody.textContent += text;
  chatEl.scrollTop = chatEl.scrollHeight;
}
function closeStreamBubble() { streamBody = null; }

// 时钟
setInterval(() => {
  $("clock").textContent = new Date().toLocaleString(conversationLanguage === "zh" ? "zh-CN" : "en-GB", { hour12: false });
}, 1000);

// ---------------- personal assistant dashboard ----------------
const ORGANIZER_COPY = {
  en: {
    open: "OPEN TASKS", overdue: "NEEDS ATTENTION", done: "COMPLETED", noTasks: "No open tasks. A suspiciously elegant state of affairs.",
    noReminders: "No reminders are scheduled.", noProjects: "Create a project by saying “Create a project called …”", noBriefings: "No briefings yet. Generate one below, or enable its schedule.",
    noMeetings: "No meeting sessions yet. Turn on Meeting Mode to begin a complete local session.", untitled: "Untitled", noDue: "No due time", due: "Due", project: "Project", task: "task", tasks: "tasks",
    pending: "PENDING", delivered: "DELIVERED", cancelled: "CANCELLED", completed: "COMPLETED", recording: "RECORDING", review: "REVIEW REQUIRED",
    generated: "Generated", updated: "Updated", briefingEmpty: "This briefing contains no items in the current period.", decisions: "DECISIONS", actions: "PROPOSED ACTIONS", noDecisions: "No explicit decisions detected.", noActions: "No action items detected.",
    editProject: "Edit", deleteProject: "Delete", saveProject: "Save", cancel: "Cancel", projectName: "Project name", projectUpdating: "Updating project…", projectDeleting: "Archiving project…", confirmDeleteProject: "Archive this project?", deleteProjectHint: "Its tasks and reminders will be kept.", confirmDelete: "Archive", editTask: "Edit", editReminder: "Edit", taskName: "Task", dueTime: "Due date & time", reminderTime: "Reminder date & time", saveTask: "Save task", saveReminder: "Save reminder", taskUpdating: "Saving task…", reminderUpdating: "Rescheduling reminder…",
    confirmSelected: "CONFIRM SELECTED → TASKS", confirmed: "Already added to tasks", transcriptLines: "transcript entries", morning: "Morning briefing", evening: "Evening review", weekly: "Weekly report",
    morningDescription: "Today’s deadlines, overdue commitments, and tomorrow’s horizon.", eveningDescription: "What closed today, what remains open, and what is waiting tomorrow.", weeklyDescription: "Progress, exposed commitments, and the next seven days.",
    enabled: "ENABLED", disabled: "OFF", deliveryTime: "DELIVERY TIME", deliveryDay: "DELIVERY DAY", save: "SAVE SCHEDULE", generate: "GENERATE NOW", settingsSaved: "Schedule saved locally.",
    refreshRequested: "Refreshing assistant data…", completeTask: "Mark task complete", meetingStarted: "Meeting session started. MERRICK is recording local notes.", meetingReady: "Meeting summary ready — review action items before adding them to tasks.", briefingReady: "Your scheduled briefing is ready.",
    notificationUnavailable: "Native macOS notifications require the MERRICK desktop app.", notificationDenied: "macOS notification permission is not available. You can enable it in System Settings.",
    dueToday: "Due today", overdueSection: "Overdue", tomorrowSection: "Tomorrow", completedToday: "Completed today", stillOpen: "Still open", completedWeek: "Completed this week", needsAttention: "Needs attention", nextSevenDays: "Next seven days",
    topLine: "TOP LINE", briefingAnalysis: "MERRICK ANALYSIS", briefingData: "DATA DESK", clarity: "Clarity", derived: "DERIVED", dataNote: "DATA NOTE", riskClear: "CLEAR", riskGuarded: "GUARDED", riskHigh: "HIGH", itemsLabel: "items",
    intelligenceNoSubscriptions: "No newspaper briefs yet. Describe one above in ordinary language.", intelligenceNoEdition: "No edition yet. Generate one from any saved brief.", intelligenceSaved: "Editorial goal saved locally.", intelligenceUpdating: "Saving newspaper changes…", intelligenceDeleting: "Deleting newspaper…", intelligencePlanning: "Planning a source strategy from your editorial goal…", intelligenceWorking: "MERRICK is researching this edition…", intelligenceReading: "Reading independent sources…", intelligenceSynthesizing: "Writing and typesetting the newspaper…", intelligenceEdit: "EDIT", intelligenceDelete: "DELETE", intelligenceSaveChanges: "SAVE CHANGES", intelligenceGenerate: "GENERATE NOW", intelligenceConfirmDelete: "Delete this newspaper and all of its editions?", intelligenceDeleteHint: "This cannot be undone.", intelligenceConfirmDeleteAction: "DELETE NEWSPAPER", intelligenceOn: "DAILY ON", intelligenceOff: "ON DEMAND", editorialGoal: "EDITORIAL GOAL", sourceDesk: "SOURCE DESK", readSource: "READ SOURCE", impact: "WHY IT MATTERS", analysisLabel: "ANALYSIS", watchlist: "WATCHLIST", noMetrics: "No quantitative desk was needed for this edition.", journalCreated: "Tasks created", journalCompleted: "Tasks completed", journalScheduled: "Due or scheduled", journalMeetings: "Meetings", journalReminders: "Reminders", journalProjects: "Projects started", journalActivity: "Recorded events", journalQuiet: "No structured work was recorded on this date.", journalHeadline: "A structured record of the day's work.", journalDataNote: "Derived from local MERRICK projects, tasks, reminders, and meeting sessions. No public data is used.",
    operationsGuarded: "GUARDED", operationsPolicy: "Read when connected · Sending and external changes require approval · Payment, identity and legal steps stay with you", operationsMail: "Mail", operationsMailDescription: "Read and prepare drafts; sending will require your approval.", operationsCalendar: "Calendar", operationsCalendarDescription: "Review schedules and prepare events; invitations will require approval.", operationsWork: "Work hub", operationsWorkDescription: "Local projects, tasks, reminders, meetings and briefings.", operationsTravel: "Travel", operationsTravelDescription: "Research and compare options; checkout remains in your hands.", operationsLocalReady: "LOCAL READY", operationsNotConnected: "NOT CONNECTED", operationsHandoffOnly: "HANDOFF ONLY", operationsUnknown: "UNAVAILABLE",
    sunday: "Sunday", monday: "Monday", tuesday: "Tuesday", wednesday: "Wednesday", thursday: "Thursday", friday: "Friday", saturday: "Saturday",
  },
  zh: {
    open: "未完成任务", overdue: "需要关注", done: "已完成", noTasks: "当前没有未完成任务，工作台很清爽。", noReminders: "目前没有已安排的提醒。", noProjects: "可以对MERRICK说：“新建项目……”", noBriefings: "还没有简报。你可以立即生成，或在计划中开启定时简报。",
    noMeetings: "还没有会议 session。开启会议模式即可开始完整的本机记录。", untitled: "未命名", noDue: "未设截止时间", due: "截止", project: "项目", task: "项任务", tasks: "项任务",
    pending: "待提醒", delivered: "已送达", cancelled: "已取消", completed: "已完成", recording: "记录中", review: "待确认",
    generated: "生成于", updated: "更新于", briefingEmpty: "本周期内这一栏暂无事项。", decisions: "会议决定", actions: "待确认行动项", noDecisions: "没有识别到明确决定。", noActions: "没有识别到行动项。",
    editProject: "编辑", deleteProject: "删除", saveProject: "保存", cancel: "取消", projectName: "项目名称", projectUpdating: "正在更新项目……", projectDeleting: "正在归档项目……", confirmDeleteProject: "确认删除这个项目？", deleteProjectHint: "其中的任务和提醒都会保留。", confirmDelete: "确认归档", editTask: "编辑", editReminder: "编辑", taskName: "任务内容", dueTime: "截止日期与时间", reminderTime: "提醒日期与时间", saveTask: "保存任务", saveReminder: "保存提醒", taskUpdating: "正在保存任务……", reminderUpdating: "正在重新安排提醒……",
    confirmSelected: "确认所选项 → 加入任务", confirmed: "已加入任务", transcriptLines: "条转录记录", morning: "晨间简报", evening: "晚间复盘", weekly: "周报",
    morningDescription: "今天的截止事项、逾期承诺，以及明天的安排。", eveningDescription: "今天完成了什么、尚未完成什么、明天有什么。", weeklyDescription: "本周进展、需要关注的承诺，以及未来七天。",
    enabled: "已开启", disabled: "已关闭", deliveryTime: "推送时间", deliveryDay: "推送日期", save: "保存计划", generate: "立即生成", settingsSaved: "计划已保存在本机。",
    refreshRequested: "正在刷新个人助理数据……", completeTask: "标记任务完成", meetingStarted: "会议 session 已开始，MERRICK 正在本机记录。", meetingReady: "会议摘要已完成，请确认行动项后再写入任务。", briefingReady: "定时简报已经准备好。",
    notificationUnavailable: "macOS 原生通知需要在 MERRICK 桌面 App 中使用。", notificationDenied: "macOS 通知权限不可用，可在“系统设置”中开启。",
    dueToday: "今天截止", overdueSection: "已经逾期", tomorrowSection: "明天", completedToday: "今天已完成", stillOpen: "仍未完成", completedWeek: "本周已完成", needsAttention: "需要关注", nextSevenDays: "未来七天",
    topLine: "头版导读", briefingAnalysis: "MERRICK 分析", briefingData: "数据台", clarity: "清晰度", derived: "派生指标", dataNote: "数据说明", riskClear: "清晰", riskGuarded: "留意", riskHigh: "高风险", itemsLabel: "项",
    intelligenceNoSubscriptions: "还没有定制报纸。请在上方直接用自然语言描述。", intelligenceNoEdition: "还没有生成版本。可以从任意已保存目标立即生成。", intelligenceSaved: "编辑目标已保存在本机。", intelligenceUpdating: "正在保存报纸设置……", intelligenceDeleting: "正在删除报纸……", intelligencePlanning: "正在根据编辑目标规划来源策略……", intelligenceWorking: "MERRICK 正在研究这一期……", intelligenceReading: "正在读取并交叉核对独立来源……", intelligenceSynthesizing: "正在撰写并排版报纸……", intelligenceEdit: "编辑", intelligenceDelete: "删除", intelligenceSaveChanges: "保存更改", intelligenceGenerate: "立即生成", intelligenceConfirmDelete: "确认删除这份报纸及其全部历史版本？", intelligenceDeleteHint: "删除后无法恢复。", intelligenceConfirmDeleteAction: "确认删除报纸", intelligenceOn: "每日开启", intelligenceOff: "按需生成", editorialGoal: "编辑目标", sourceDesk: "来源台", readSource: "阅读来源", impact: "为何重要", analysisLabel: "分析", watchlist: "观察清单", noMetrics: "本期内容不需要使用量化数据台。", journalCreated: "新建任务", journalCompleted: "完成任务", journalScheduled: "到期或计划", journalMeetings: "会议", journalReminders: "提醒", journalProjects: "新建项目", journalActivity: "记录事件", journalQuiet: "这一天没有记录到结构化工作。", journalHeadline: "当天工作的结构化记录。", journalDataNote: "数据来自本机 MERRICK 项目、任务、提醒与会议 session，不使用公开网络数据。",
    operationsGuarded: "受控模式", operationsPolicy: "连接后可自动读取 · 发送与外部变更需要确认 · 付款、身份与法律步骤由你接管", operationsMail: "邮件", operationsMailDescription: "读取并准备草稿；发送前会请求你的确认。", operationsCalendar: "日历", operationsCalendarDescription: "查看日程并准备事件；发送邀请前需要确认。", operationsWork: "工作中枢", operationsWorkDescription: "本机项目、任务、提醒、会议与简报。", operationsTravel: "旅行", operationsTravelDescription: "搜索与比较选项；最终结账仍由你完成。", operationsLocalReady: "本机已就绪", operationsNotConnected: "尚未连接", operationsHandoffOnly: "仅交接执行", operationsUnknown: "不可用",
    sunday: "周日", monday: "周一", tuesday: "周二", wednesday: "周三", thursday: "周四", friday: "周五", saturday: "周六",
  },
};

function oc(key, fallback = key) {
  return ORGANIZER_COPY[conversationLanguage]?.[key] || ORGANIZER_COPY.en[key] || fallback;
}

function organizerNode(tag, className = "", text = "") {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== "") node.textContent = String(text);
  return node;
}

function organizerArray(value, limit = 150) {
  return Array.isArray(value) ? value.filter((item) => item && typeof item === "object").slice(0, limit) : [];
}

function organizerDate(value, options = {}) {
  if (typeof value !== "string" || !value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString(conversationLanguage === "zh" ? "zh-CN" : "en-GB", {
    dateStyle: options.dateOnly ? "medium" : "medium",
    ...(options.dateOnly ? {} : { timeStyle: "short" }),
  });
}

function setOrganizerStatus(text = "", state = "") {
  if (!organizerStatus) return;
  organizerStatus.textContent = text;
  organizerStatus.dataset.state = state;
}

function setOrganizerView(view) {
  if (!["overview", "intelligence", "journal", "meetings", "settings"].includes(view)) view = "overview";
  if (newspaperFocusActive && view !== "intelligence") exitNewspaperFocus();
  organizerView = view;
  document.querySelectorAll("[data-organizer-view]").forEach((button) => {
    const active = button.dataset.organizerView === view;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
    button.tabIndex = active ? 0 : -1;
  });
  document.querySelectorAll("[data-organizer-page]").forEach((page) => {
    page.hidden = page.dataset.organizerPage !== view;
  });
}

function setOrganizerVisible(visible, focus = organizerView) {
  if (!organizerPanel) return;
  if (!visible && newspaperFocusActive) exitNewspaperFocus();
  organizerPanel.hidden = !visible;
  if (visible) {
    // A voice command can arrive while the floating HUD is collapsed. The
    // organizer is an internal MERRICK surface, so expand the host window here
    // instead of asking macOS to find an app named "Assistant Dashboard".
    if (isDesktop && !document.body.classList.contains("expanded")) {
      document.body.classList.add("expanded");
      nativePost("resize", { expanded: true });
    }
    setResearchDisplayVisible(false);
    closeSetupPanel();
    setOrganizerView(focus);
    if (!organizerSnapshot) sendJson({ type: "organizer_snapshot_request" });
  }
}

function organizerEmpty(text) {
  return organizerNode("div", "organizer-empty", text);
}

function renderOrganizerStats(snapshot) {
  if (!organizerStats) return;
  organizerStats.replaceChildren();
  const stats = snapshot?.stats && typeof snapshot.stats === "object" ? snapshot.stats : {};
  const values = [
    [Number(stats.open_tasks) || 0, oc("open"), ""],
    [Number(stats.overdue_tasks) || 0, oc("overdue"), "alert"],
    [Number(stats.completed_tasks) || 0, oc("done"), "done"],
  ];
  for (const [value, label, tone] of values) {
    const card = organizerNode("article", `organizer-stat ${tone}`.trim());
    card.append(organizerNode("strong", "", value), organizerNode("span", "", label));
    organizerStats.append(card);
  }
}

function renderPersonalOperations(snapshot) {
  if (!personalOperationsStatus) return;
  personalOperationsStatus.replaceChildren();
  const operations = snapshot?.personal_operations;
  const capabilities = organizerArray(operations?.capabilities, 8);
  const copy = {
    mail: ["operationsMail", "operationsMailDescription"],
    calendar: ["operationsCalendar", "operationsCalendarDescription"],
    work: ["operationsWork", "operationsWorkDescription"],
    travel: ["operationsTravel", "operationsTravelDescription"],
  };
  const statusCopy = {
    local_ready: "operationsLocalReady",
    not_connected: "operationsNotConnected",
    handoff_only: "operationsHandoffOnly",
  };
  for (const capability of capabilities) {
    const id = typeof capability.id === "string" ? capability.id : "";
    if (!copy[id]) continue;
    const card = organizerNode("article", `personal-operation ${String(capability.status || "unknown").replace(/[^a-z_]/g, "")}`);
    card.setAttribute("role", "listitem");
    const head = organizerNode("div", "personal-operation-head");
    head.append(
      organizerNode("strong", "", oc(copy[id][0])),
      organizerNode("span", "personal-operation-risk", String(capability.max_risk || "R0")),
    );
    const status = organizerNode("span", "personal-operation-status", oc(statusCopy[capability.status] || "operationsUnknown"));
    card.append(head, status, organizerNode("p", "", oc(copy[id][1])));
    personalOperationsStatus.append(card);
  }
  if (!capabilities.length) personalOperationsStatus.append(organizerEmpty(oc("operationsUnknown")));
  if (personalOperationsMode) personalOperationsMode.textContent = oc("operationsGuarded");
  if (personalOperationsPolicy) personalOperationsPolicy.textContent = oc("operationsPolicy");
}

function organizerDateTimeLocalValue(value) {
  if (typeof value !== "string" || !value) return "";
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) return "";
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 16);
}

function organizerDateTimeIsoValue(value) {
  if (!value) return null;
  const date = new Date(value);
  return Number.isFinite(date.getTime()) ? date.toISOString() : undefined;
}

function organizerEditorField(label, input) {
  const field = organizerNode("label", "organizer-edit-field");
  field.append(organizerNode("span", "", label), input);
  return field;
}

function renderOrganizerTasks(snapshot) {
  if (!organizerTaskList) return;
  organizerTaskList.replaceChildren();
  const tasks = organizerArray(snapshot?.tasks).filter((task) => task.status === "open").slice(0, 36);
  if (organizerTaskCount) organizerTaskCount.textContent = String(tasks.length);
  if (!tasks.length) {
    organizerTaskList.append(organizerEmpty(oc("noTasks")));
    return;
  }
  const now = Date.now();
  for (const task of tasks) {
    const dueTime = typeof task.due_at === "string" ? new Date(task.due_at).getTime() : NaN;
    const taskId = typeof task.id === "string" && /^[a-z0-9][a-z0-9._:-]{0,95}$/i.test(task.id) ? task.id : "";
    const item = organizerNode("article", `organizer-item organizer-editable-item ${Number.isFinite(dueTime) && dueTime < now ? "overdue" : ""}`.trim());
    const row = organizerNode("div", "organizer-item-row");
    const complete = organizerNode("button", "task-complete", "✓");
    complete.type = "button";
    complete.title = oc("completeTask");
    complete.setAttribute("aria-label", `${oc("completeTask")}: ${String(task.title || "")}`);
    complete.addEventListener("click", () => {
      if (!taskId) return;
      complete.disabled = true;
      sendJson({ type: "organizer_complete_task", task_id: taskId });
    });
    const copy = organizerNode("div", "organizer-item-copy");
    copy.append(organizerNode("div", "organizer-item-title", task.title || oc("untitled")));
    const meta = [];
    if (task.project_title) meta.push(`${oc("project")}: ${task.project_title}`);
    if (task.due_at) meta.push(`${oc("due")}: ${organizerDate(task.due_at)}`);
    else meta.push(oc("noDue"));
    copy.append(organizerNode("div", "organizer-item-meta", meta.join(" · ")));
    const actions = organizerNode("div", "organizer-project-actions");
    const edit = organizerNode("button", "organizer-project-action", oc("editTask"));
    edit.type = "button";
    edit.setAttribute("aria-label", `${oc("editTask")}: ${String(task.title || "")}`);
    edit.addEventListener("click", () => {
      if (!taskId || item.querySelector(".organizer-task-editor")) return;
      actions.hidden = true;
      const editor = organizerNode("div", "organizer-task-editor");
      const title = organizerNode("input", "organizer-project-input");
      title.type = "text";
      title.maxLength = 300;
      title.value = String(task.title || "");
      title.setAttribute("aria-label", oc("taskName"));
      const dueAt = organizerNode("input", "organizer-project-input");
      dueAt.type = "datetime-local";
      dueAt.value = organizerDateTimeLocalValue(task.due_at);
      dueAt.setAttribute("aria-label", oc("dueTime"));
      const controls = organizerNode("div", "organizer-project-editor-actions");
      const save = organizerNode("button", "organizer-project-action primary", oc("saveTask"));
      const cancel = organizerNode("button", "organizer-project-action", oc("cancel"));
      save.type = cancel.type = "button";
      const closeEditor = () => { editor.remove(); actions.hidden = false; edit.focus(); };
      const submit = () => {
        const nextTitle = title.value.trim();
        const nextDueAt = organizerDateTimeIsoValue(dueAt.value);
        if (!nextTitle || nextTitle.length > 300) return title.focus();
        if (nextDueAt === undefined) return dueAt.focus();
        if (nextTitle === String(task.title || "") && nextDueAt === (task.due_at || null)) return closeEditor();
        save.disabled = cancel.disabled = true;
        setOrganizerStatus(oc("taskUpdating"), "working");
        sendJson({ type: "organizer_update_task", task_id: taskId, title: nextTitle, due_at: nextDueAt });
      };
      save.addEventListener("click", submit);
      cancel.addEventListener("click", closeEditor);
      [title, dueAt].forEach((control) => control.addEventListener("keydown", (event) => {
        if (event.key === "Enter") submit();
        else if (event.key === "Escape") closeEditor();
      }));
      controls.append(save, cancel);
      editor.append(organizerEditorField(oc("taskName"), title), organizerEditorField(oc("dueTime"), dueAt), controls);
      item.append(editor);
      editor.scrollIntoView({ block: "nearest" });
      title.focus();
      title.select();
    });
    actions.append(edit);
    row.append(complete, copy, actions);
    item.append(row);
    organizerTaskList.append(item);
  }
}

function renderOrganizerReminders(snapshot) {
  if (!organizerReminderList) return;
  organizerReminderList.replaceChildren();
  const reminders = organizerArray(snapshot?.reminders).filter((item) => item.status === "pending").slice(0, 12);
  if (!reminders.length) {
    organizerReminderList.append(organizerEmpty(oc("noReminders")));
    return;
  }
  for (const reminder of reminders) {
    const reminderId = typeof reminder.id === "string" && /^[a-z0-9][a-z0-9._:-]{0,95}$/i.test(reminder.id) ? reminder.id : "";
    const item = organizerNode("article", "organizer-item organizer-editable-item");
    const row = organizerNode("div", "organizer-item-row");
    const copy = organizerNode("div", "organizer-item-copy");
    copy.append(organizerNode("div", "organizer-item-title", reminder.title || oc("untitled")));
    copy.append(organizerNode("div", "organizer-item-meta", `${organizerDate(reminder.fire_at)} · ${oc(reminder.status || "pending")}`));
    const actions = organizerNode("div", "organizer-project-actions");
    const edit = organizerNode("button", "organizer-project-action", oc("editReminder"));
    edit.type = "button";
    edit.setAttribute("aria-label", `${oc("editReminder")}: ${String(reminder.title || "")}`);
    edit.addEventListener("click", () => {
      if (!reminderId || item.querySelector(".organizer-reminder-editor")) return;
      actions.hidden = true;
      const editor = organizerNode("div", "organizer-reminder-editor");
      const fireAt = organizerNode("input", "organizer-project-input");
      fireAt.type = "datetime-local";
      fireAt.value = organizerDateTimeLocalValue(reminder.fire_at);
      fireAt.setAttribute("aria-label", oc("reminderTime"));
      const controls = organizerNode("div", "organizer-project-editor-actions");
      const save = organizerNode("button", "organizer-project-action primary", oc("saveReminder"));
      const cancel = organizerNode("button", "organizer-project-action", oc("cancel"));
      save.type = cancel.type = "button";
      const closeEditor = () => { editor.remove(); actions.hidden = false; edit.focus(); };
      const submit = () => {
        const nextFireAt = organizerDateTimeIsoValue(fireAt.value);
        if (!nextFireAt) return fireAt.focus();
        if (nextFireAt === reminder.fire_at) return closeEditor();
        save.disabled = cancel.disabled = true;
        setOrganizerStatus(oc("reminderUpdating"), "working");
        sendJson({ type: "organizer_update_reminder", reminder_id: reminderId, fire_at: nextFireAt });
      };
      save.addEventListener("click", submit);
      cancel.addEventListener("click", closeEditor);
      fireAt.addEventListener("keydown", (event) => {
        if (event.key === "Enter") submit();
        else if (event.key === "Escape") closeEditor();
      });
      controls.append(save, cancel);
      editor.append(organizerEditorField(oc("reminderTime"), fireAt), controls);
      item.append(editor);
      editor.scrollIntoView({ block: "nearest" });
      fireAt.focus();
    });
    actions.append(edit);
    row.append(copy, actions);
    item.append(row);
    organizerReminderList.append(item);
  }
}

function renderOrganizerProjects(snapshot) {
  if (!organizerProjectList) return;
  organizerProjectList.replaceChildren();
  const projects = organizerArray(snapshot?.projects).filter((item) => item.status === "active").slice(0, 20);
  if (!projects.length) {
    organizerProjectList.append(organizerEmpty(oc("noProjects")));
    return;
  }
  for (const project of projects) {
    const card = organizerNode("article", "organizer-project");
    const open = Number(project.open_tasks) || 0;
    const projectId = typeof project.id === "string" && /^[a-z0-9][a-z0-9._:-]{0,95}$/i.test(project.id)
      ? project.id : "";
    const title = String(project.title || oc("untitled"));
    const head = organizerNode("div", "organizer-project-head");
    const copy = organizerNode("div", "organizer-project-copy");
    const name = organizerNode("strong", "", title);
    copy.append(name, organizerNode("span", "", `${open} ${open === 1 ? oc("task") : oc("tasks")}`));
    const actions = organizerNode("div", "organizer-project-actions");
    const edit = organizerNode("button", "organizer-project-action", oc("editProject"));
    edit.type = "button";
    edit.setAttribute("aria-label", `${oc("editProject")}: ${title}`);
    const remove = organizerNode("button", "organizer-project-action danger", oc("deleteProject"));
    remove.type = "button";
    remove.setAttribute("aria-label", `${oc("deleteProject")}: ${title}`);
    actions.append(edit, remove);
    head.append(copy, actions);
    card.append(head);

    edit.addEventListener("click", () => {
      if (!projectId || card.querySelector(".organizer-project-editor")) return;
      actions.hidden = true;
      const editor = organizerNode("div", "organizer-project-editor");
      const input = organizerNode("input", "organizer-project-input");
      input.type = "text";
      input.maxLength = 200;
      input.value = title;
      input.setAttribute("aria-label", oc("projectName"));
      const controls = organizerNode("div", "organizer-project-editor-actions");
      const save = organizerNode("button", "organizer-project-action primary", oc("saveProject"));
      const cancel = organizerNode("button", "organizer-project-action", oc("cancel"));
      save.type = cancel.type = "button";
      const closeEditor = () => { editor.remove(); actions.hidden = false; };
      const submit = () => {
        const nextTitle = input.value.trim();
        if (!nextTitle || nextTitle.length > 200) return input.focus();
        if (nextTitle === title) return closeEditor();
        save.disabled = cancel.disabled = true;
        setOrganizerStatus(oc("projectUpdating"));
        sendJson({ type: "organizer_rename_project", project_id: projectId, title: nextTitle });
      };
      save.addEventListener("click", submit);
      cancel.addEventListener("click", closeEditor);
      input.addEventListener("keydown", (event) => {
        if (event.key === "Enter") submit();
        else if (event.key === "Escape") closeEditor();
      });
      controls.append(save, cancel);
      editor.append(input, controls);
      card.append(editor);
      card.scrollIntoView({ block: "nearest" });
      input.focus();
      input.select();
    });

    remove.addEventListener("click", () => {
      if (!projectId || card.querySelector(".organizer-project-delete-confirm")) return;
      actions.hidden = true;
      const confirmation = organizerNode("div", "organizer-project-delete-confirm");
      const message = organizerNode("div", "organizer-project-delete-copy");
      message.append(
        organizerNode("strong", "", oc("confirmDeleteProject")),
        organizerNode("span", "", oc("deleteProjectHint")),
      );
      const controls = organizerNode("div", "organizer-project-editor-actions");
      const confirm = organizerNode("button", "organizer-project-action danger", oc("confirmDelete"));
      const cancel = organizerNode("button", "organizer-project-action", oc("cancel"));
      confirm.type = cancel.type = "button";
      cancel.addEventListener("click", () => { confirmation.remove(); actions.hidden = false; });
      confirm.addEventListener("click", () => {
        confirm.disabled = cancel.disabled = true;
        setOrganizerStatus(oc("projectDeleting"));
        sendJson({ type: "organizer_archive_project", project_id: projectId, confirmed: true });
      });
      controls.append(confirm, cancel);
      confirmation.append(message, controls);
      card.append(confirmation);
      card.scrollIntoView({ block: "nearest" });
    });
    organizerProjectList.append(card);
  }
}

function briefingForDisplay(briefings) {
  if (selectedBriefingId) {
    const selected = briefings.find((item) => item.id === selectedBriefingId);
    if (selected) return selected;
  }
  return briefings[0] || null;
}

function briefingLocalized(record, key, fallback = "") {
  if (!record || typeof record !== "object") return fallback;
  const localized = conversationLanguage === "zh" ? record[`${key}_zh`] : record[key];
  const base = record[key];
  return typeof localized === "string" && localized.trim()
    ? localized.trim()
    : (typeof base === "string" && base.trim() ? base.trim() : fallback);
}

function briefingRiskLabel(value) {
  if (value === "high") return oc("riskHigh");
  if (value === "guarded") return oc("riskGuarded");
  return oc("riskClear");
}

function briefingMetricLabels(kind) {
  if (kind === "journal") return [oc("journalCompleted"), oc("journalCreated"), oc("journalMeetings")];
  return kind === "morning"
    ? [oc("dueToday"), oc("overdueSection"), oc("tomorrowSection")]
    : kind === "evening"
      ? [oc("completedToday"), oc("stillOpen"), oc("tomorrowSection")]
      : [oc("completedWeek"), oc("needsAttention"), oc("nextSevenDays")];
}

function renderBriefingVisual(visual, metricLabels) {
  const figure = organizerNode("figure", "briefing-data-figure");
  const score = Math.max(0, Math.min(100, Number(visual?.score) || 0));
  const risk = ["clear", "guarded", "high"].includes(visual?.risk) ? visual.risk : "clear";
  const label = briefingLocalized(visual, "label", `${oc("clarity")} · ${oc("derived")}`);
  const art = organizerNode("div", `briefing-score-art risk-${risk}`);
  art.setAttribute("role", "img");
  art.setAttribute("aria-label", `${label}: ${score} out of 100. ${briefingRiskLabel(risk)}.`);
  const ring = organizerNode("div", "briefing-score-ring");
  ring.style.setProperty("--briefing-score", `${score * 3.6}deg`);
  const center = organizerNode("div", "briefing-score-center");
  center.append(organizerNode("strong", "", score), organizerNode("span", "", "/ 100"));
  ring.append(center);
  const caption = organizerNode("figcaption", "briefing-score-caption");
  caption.append(
    organizerNode("span", "briefing-data-label", oc("briefingData")),
    organizerNode("strong", "", label),
    organizerNode("span", `briefing-risk risk-${risk}`, briefingRiskLabel(risk)),
  );
  art.append(ring, caption);
  figure.append(art);

  const values = organizerArray(visual?.series, 3);
  const maxValue = Math.max(1, ...values.map((item) => Number(item.value) || 0));
  const chart = organizerNode("div", "briefing-bar-chart");
  values.forEach((item, index) => {
    const value = Math.max(0, Number(item.value) || 0);
    const row = organizerNode("div", "briefing-bar-row");
    const copy = organizerNode("div", "briefing-bar-copy");
    copy.append(
      organizerNode("span", "", metricLabels[index] || item.label || ""),
      organizerNode("strong", "", value),
    );
    const track = organizerNode("div", "briefing-bar-track");
    const fill = organizerNode("span", `briefing-bar-fill series-${item.key || index}`);
    fill.style.width = `${Math.max(value ? 8 : 0, Math.round(value / maxValue * 100))}%`;
    track.append(fill);
    row.append(copy, track);
    chart.append(row);
  });
  figure.append(chart);
  return figure;
}

function renderBriefingFeature(briefing, target = organizerLatestBriefing) {
  if (!target) return;
  target.replaceChildren();
  if (!briefing) {
    target.append(organizerEmpty(oc("noBriefings")));
    return;
  }
  const content = briefing.content && typeof briefing.content === "object" ? briefing.content : {};
  const metrics = content.metrics && typeof content.metrics === "object" ? content.metrics : {};
  const publication = content.publication && typeof content.publication === "object" ? content.publication : {};
  const analysis = content.analysis && typeof content.analysis === "object" ? content.analysis : {};
  const metricLabels = briefingMetricLabels(briefing.kind);
  const masthead = briefingLocalized(publication, "masthead", conversationLanguage === "zh" ? "MERRICK 每日简报" : "The Daily MERRICK");
  const edition = briefingLocalized(publication, "edition", oc(briefing.kind));
  const leadHeadline = briefingLocalized(analysis, "title", briefingLocalized(content, "headline", oc(briefing.kind)));
  const deck = briefingLocalized(content, "headline", "");
  const risk = ["clear", "guarded", "high"].includes(analysis.risk) ? analysis.risk : "clear";

  const article = organizerNode("article", `briefing-newspaper briefing-${briefing.kind}`);
  const mast = organizerNode("header", "briefing-masthead");
  const mastMeta = organizerNode("div", "briefing-mast-meta");
  mastMeta.append(
    organizerNode("span", "", edition),
    organizerNode("span", "", organizerDate(briefing.generated_at)),
  );
  mast.append(mastMeta, organizerNode("h2", "", masthead), organizerNode("div", "briefing-mast-rule"));

  const front = organizerNode("div", "briefing-front-page");
  const lead = organizerNode("section", "briefing-lead-story");
  lead.append(
    organizerNode("span", "briefing-section-label", oc("topLine")),
    organizerNode("h3", "", leadHeadline),
    organizerNode("p", "briefing-deck", deck),
    organizerNode("div", `briefing-risk-line risk-${risk}`, `${briefingRiskLabel(risk)} · ${oc("derived")}`),
  );
  const visual = content.visual && typeof content.visual === "object"
    ? content.visual
    : { score: Number(metrics.clarity) || 100, risk, series: [] };
  front.append(lead, renderBriefingVisual(visual, metricLabels));

  const metricGrid = organizerNode("section", "briefing-metrics");
  metricGrid.setAttribute("aria-label", oc("briefingData"));
  [["primary", metricLabels[0]], ["attention", metricLabels[1]], ["upcoming", metricLabels[2]], ["clarity", `${oc("clarity")} · ${oc("derived")}`]].forEach(([key, label]) => {
    const card = organizerNode("div", `briefing-metric metric-${key}`);
    const value = key === "primary" ? (metrics.primary ?? metrics.completed) : metrics[key];
    card.append(organizerNode("strong", "", Number(value) || 0), organizerNode("span", "", label));
    metricGrid.append(card);
  });

  const editorial = organizerNode("div", "briefing-editorial-grid");
  const sectionGrid = organizerNode("main", "briefing-sections");
  for (const section of organizerArray(content.sections, 6)) {
    const card = organizerNode("section", "briefing-section");
    const items = organizerArray(section.items, 10);
    const heading = organizerNode("header", "briefing-section-head");
    heading.append(
      organizerNode("h4", "", typeof section.key === "string" ? oc(section.key, section.title || "") : (section.title || "")),
      organizerNode("span", "", `${items.length} ${oc("itemsLabel")}`),
    );
    const list = organizerNode("ol", "briefing-news-list");
    if (!items.length) list.append(organizerNode("li", "briefing-empty-edition", oc("briefingEmpty")));
    items.forEach((item, index) => {
      const row = organizerNode("li", "briefing-news-item");
      const number = organizerNode("span", "briefing-news-number", String(index + 1).padStart(2, "0"));
      const copy = organizerNode("div", "briefing-news-copy");
      copy.append(organizerNode("strong", "", item.title || oc("untitled")));
      const meta = [];
      if (item.project_title) meta.push(`${oc("project")}: ${item.project_title}`);
      if (item.due_at) meta.push(`${oc("due")}: ${organizerDate(item.due_at)}`);
      if (meta.length) copy.append(organizerNode("span", "", meta.join(" · ")));
      row.append(number, copy);
      list.append(row);
    });
    card.append(heading, list);
    sectionGrid.append(card);
  }

  const analysisPanel = organizerNode("aside", "briefing-analysis-panel");
  const analysisHead = organizerNode("header", "briefing-analysis-head");
  analysisHead.append(
    organizerNode("span", "briefing-section-label", oc("briefingAnalysis")),
    organizerNode("span", `briefing-risk risk-${risk}`, briefingRiskLabel(risk)),
  );
  analysisPanel.append(analysisHead, organizerNode("h3", "", leadHeadline));
  for (const item of organizerArray(analysis.items, 5)) {
    const note = organizerNode("section", `briefing-analysis-note tone-${item.tone || "system"}`);
    note.append(
      organizerNode("h4", "", briefingLocalized(item, "label", "")),
      organizerNode("p", "", briefingLocalized(item, "text", "")),
    );
    analysisPanel.append(note);
  }
  editorial.append(sectionGrid, analysisPanel);

  const footer = organizerNode("footer", "briefing-footer");
  footer.append(
    organizerNode("strong", "", oc("dataNote")),
    organizerNode("span", "", briefingLocalized(content, "data_note", `${oc("generated")} ${organizerDate(briefing.generated_at)}`)),
  );
  article.append(mast, front, metricGrid, editorial, footer);
  target.append(article);
}

function localDateKey(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function intelligenceEditionForDisplay(editions) {
  if (selectedIntelligenceEditionId) {
    const selected = editions.find((item) => item.id === selectedIntelligenceEditionId);
    if (selected) return selected;
  }
  return editions[0] || null;
}

function newspaperReaderCopy(key) {
  const copy = conversationLanguage === "zh" ? {
    focus: "专注阅读",
    close: "退出阅读",
    edition: "完整报纸",
    hint: "全屏阅读完整内容、分析与来源",
  } : {
    focus: "Focus reader",
    close: "Close reader",
    edition: "Complete edition",
    hint: "Read the full paper, analysis and sources",
  };
  return copy[key] || "";
}

function setReaderBackgroundInert(active) {
  if (!organizerPanel) return;
  if (active) {
    newspaperFocusInertNodes = Array.from(document.body.children).filter((node) => node !== organizerPanel && !node.inert);
    newspaperFocusInertNodes.forEach((node) => { node.inert = true; });
    return;
  }
  newspaperFocusInertNodes.forEach((node) => { node.inert = false; });
  newspaperFocusInertNodes = [];
}

function enterNewspaperFocus(edition, invoker) {
  if (!organizerPanel || !intelligenceEditionFeature || !edition) return;
  setOrganizerView("intelligence");
  newspaperFocusActive = true;
  newspaperFocusEditionId = edition.id || selectedIntelligenceEditionId || "current";
  const intelligencePage = document.querySelector('[data-organizer-page="intelligence"]');
  newspaperFocusScrollTop = intelligencePage?.scrollTop || 0;
  newspaperFocusInvoker = invoker instanceof HTMLElement ? invoker : document.activeElement;
  organizerPanel.classList.add("newspaper-focus");
  organizerPanel.dataset.readerMode = "newspaper-focus";
  setReaderBackgroundInert(true);
  const focusButton = intelligenceEditionFeature.querySelector(".intelligence-reader-toggle");
  if (focusButton) {
    focusButton.textContent = newspaperReaderCopy("close");
    focusButton.setAttribute("aria-pressed", "true");
  }
  requestAnimationFrame(() => {
    if (intelligencePage) intelligencePage.scrollTop = 0;
    const heading = intelligenceEditionFeature.querySelector(".briefing-masthead h2");
    heading?.focus({ preventScroll: true });
  });
}

function exitNewspaperFocus() {
  if (!newspaperFocusActive || !organizerPanel) return;
  newspaperFocusActive = false;
  newspaperFocusEditionId = "";
  organizerPanel.classList.remove("newspaper-focus");
  organizerPanel.dataset.readerMode = "organizer";
  setReaderBackgroundInert(false);
  const focusButton = intelligenceEditionFeature?.querySelector(".intelligence-reader-toggle");
  if (focusButton) {
    focusButton.textContent = newspaperReaderCopy("focus");
    focusButton.setAttribute("aria-pressed", "false");
  }
  const intelligencePage = document.querySelector('[data-organizer-page="intelligence"]');
  requestAnimationFrame(() => {
    if (intelligencePage) intelligencePage.scrollTop = newspaperFocusScrollTop;
    if (newspaperFocusInvoker instanceof HTMLElement && newspaperFocusInvoker.isConnected) {
      newspaperFocusInvoker.focus({ preventScroll: true });
    }
    newspaperFocusInvoker = null;
  });
}

function renderIntelligenceEdition(edition) {
  if (!intelligenceEditionFeature) return;
  intelligenceEditionFeature.replaceChildren();
  if (!edition) {
    if (newspaperFocusActive) exitNewspaperFocus();
    intelligenceEditionFeature.append(organizerEmpty(oc("intelligenceNoEdition")));
    return;
  }
  const content = edition.content && typeof edition.content === "object" ? edition.content : {};
  const publication = content.publication && typeof content.publication === "object" ? content.publication : {};
  const metrics = organizerArray(content.metrics, 6);
  const stories = organizerArray(content.stories, 10);
  const analysis = organizerArray(content.analysis, 6);
  const watchlist = organizerArray(content.watchlist, 8);
  const sources = organizerArray(edition.sources, 12);
  const readerToolbar = organizerNode("div", "intelligence-reader-toolbar");
  const readerIdentity = organizerNode("div", "intelligence-reader-identity");
  readerIdentity.append(
    organizerNode("span", "briefing-section-label", newspaperReaderCopy("edition")),
    organizerNode("strong", "", newspaperReaderCopy("hint")),
  );
  const readerToggle = organizerNode("button", "intelligence-reader-toggle", newspaperFocusActive ? newspaperReaderCopy("close") : newspaperReaderCopy("focus"));
  readerToggle.type = "button";
  readerToggle.setAttribute("aria-pressed", String(newspaperFocusActive));
  readerToggle.addEventListener("click", () => {
    if (newspaperFocusActive) exitNewspaperFocus();
    else enterNewspaperFocus(edition, readerToggle);
  });
  const readerActions = organizerNode("div", "intelligence-reader-actions");
  const readerFullscreen = organizerNode("button", "organizer-window-btn intelligence-reader-fullscreen");
  readerFullscreen.type = "button";
  readerFullscreen.setAttribute("data-native-fullscreen-control", "");
  readerFullscreen.setAttribute("aria-pressed", "false");
  readerFullscreen.setAttribute("aria-label", "Enter full screen");
  readerFullscreen.innerHTML = '<svg aria-hidden="true" viewBox="0 0 20 20" width="15" height="15"><path d="M7 3H3v4M13 3h4v4M7 17H3v-4M13 17h4v-4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg><span>FULL SCREEN</span>';
  readerFullscreen.addEventListener("click", () => requestNativeFullscreen("toggle"));
  readerActions.append(readerFullscreen, readerToggle);
  readerToolbar.append(readerIdentity, readerActions);
  updateNativeFullscreenControl();

  const article = organizerNode("article", "briefing-newspaper intelligence-newspaper");

  const mast = organizerNode("header", "briefing-masthead");
  const mastMeta = organizerNode("div", "briefing-mast-meta");
  mastMeta.append(
    organizerNode("span", "", publication.edition || edition.title || "MERRICK Intelligence"),
    organizerNode("span", "", organizerDate(edition.generated_at)),
  );
  const mastheadTitle = organizerNode("h2", "", publication.masthead || "MERRICK Intelligence");
  mastheadTitle.tabIndex = -1;
  mast.append(mastMeta, mastheadTitle, organizerNode("div", "briefing-mast-rule"));

  const lead = organizerNode("section", "intelligence-lead");
  lead.append(
    organizerNode("span", "briefing-section-label", oc("topLine")),
    organizerNode("h3", "", content.headline || edition.title || ""),
    organizerNode("p", "briefing-deck", content.deck || ""),
  );
  article.append(mast, lead);

  const metricDesk = organizerNode("section", "intelligence-metric-desk");
  if (!metrics.length) metricDesk.append(organizerNode("p", "intelligence-no-metrics", oc("noMetrics")));
  metrics.forEach((metric) => {
    const card = organizerNode("article", "intelligence-metric");
    card.append(
      organizerNode("span", "", metric.label || ""),
      organizerNode("strong", "", metric.value ?? "—"),
      organizerNode("small", "", [metric.direction && metric.direction !== "na" ? metric.direction : "", metric.context].filter(Boolean).join(" · ")),
    );
    metricDesk.append(card);
  });
  article.append(metricDesk);
  const chartValues = metrics.map((metric) => {
    const match = String(metric.value ?? "").replaceAll(",", "").match(/-?\d+(?:\.\d+)?/);
    return { label: metric.label || "", display: metric.value ?? "—", value: match ? Math.abs(Number(match[0])) : NaN };
  }).filter((item) => Number.isFinite(item.value));
  if (chartValues.length >= 2) {
    const chart = organizerNode("figure", "intelligence-data-graphic");
    chart.append(organizerNode("figcaption", "briefing-section-label", oc("briefingData")));
    const maximum = Math.max(1, ...chartValues.map((item) => item.value));
    chartValues.forEach((item, index) => {
      const row = organizerNode("div", "intelligence-data-row");
      const copy = organizerNode("div", "intelligence-data-copy");
      copy.append(organizerNode("span", "", item.label), organizerNode("strong", "", item.display));
      const track = organizerNode("div", "intelligence-data-track");
      const fill = organizerNode("span", `series-${index % 3}`);
      fill.style.width = `${Math.max(4, Math.round(item.value / maximum * 100))}%`;
      track.append(fill); row.append(copy, track); chart.append(row);
    });
    article.append(chart);
  }

  const body = organizerNode("div", "intelligence-editorial-body");
  const storyColumn = organizerNode("main", "intelligence-stories");
  stories.forEach((story, index) => {
    const storyNode = organizerNode("article", `intelligence-story ${index === 0 ? "lead-story" : ""}`.trim());
    storyNode.append(
      organizerNode("span", "briefing-section-label", story.kicker || `${String(index + 1).padStart(2, "0")} · REPORT`),
      organizerNode("h3", "", story.title || ""),
      organizerNode("p", "intelligence-story-summary", story.summary || ""),
    );
    if (story.analysis) {
      const block = organizerNode("div", "intelligence-story-analysis");
      block.append(organizerNode("strong", "", oc("analysisLabel")), organizerNode("p", "", story.analysis));
      storyNode.append(block);
    }
    if (story.impact) {
      const block = organizerNode("div", "intelligence-story-impact");
      block.append(organizerNode("strong", "", oc("impact")), organizerNode("p", "", story.impact));
      storyNode.append(block);
    }
    const citations = organizerNode("div", "intelligence-citations");
    (Array.isArray(story.source_indices) ? story.source_indices : []).forEach((sourceIndex) => {
      const source = sources[Number(sourceIndex) - 1];
      if (!source?.url) return;
      const cite = organizerNode("button", "", `[${sourceIndex}]`);
      cite.type = "button";
      cite.title = source.title || source.url;
      cite.addEventListener("click", () => nativePost("openResearchPages", { urls: [source.url] }));
      citations.append(cite);
    });
    if (citations.childElementCount) storyNode.append(citations);
    storyColumn.append(storyNode);
  });

  const desk = organizerNode("aside", "intelligence-analysis-desk");
  desk.append(organizerNode("span", "briefing-section-label", oc("briefingAnalysis")));
  analysis.forEach((item) => {
    const note = organizerNode("section", `briefing-analysis-note tone-${item.tone || "system"}`);
    note.append(organizerNode("h4", "", item.label || ""), organizerNode("p", "", item.text || ""));
    desk.append(note);
  });
  if (watchlist.length) {
    desk.append(organizerNode("h3", "intelligence-watch-heading", oc("watchlist")));
    watchlist.forEach((item) => {
      const note = organizerNode("section", "intelligence-watch-item");
      note.append(organizerNode("strong", "", item.label || ""), organizerNode("p", "", item.text || ""));
      desk.append(note);
    });
  }
  body.append(storyColumn, desk);
  article.append(body);

  const sourceDesk = organizerNode("section", "intelligence-source-desk");
  sourceDesk.append(organizerNode("h3", "", oc("sourceDesk")));
  const sourceGrid = organizerNode("div", "intelligence-source-grid");
  sources.forEach((source, index) => {
    const card = organizerNode("button", "intelligence-source-card");
    card.type = "button";
    card.append(
      organizerNode("span", "", String(index + 1).padStart(2, "0")),
      organizerNode("strong", "", source.title || source.url || ""),
      organizerNode("small", "", oc("readSource")),
    );
    if (source.url) card.addEventListener("click", () => nativePost("openResearchPages", { urls: [source.url] }));
    sourceGrid.append(card);
  });
  sourceDesk.append(sourceGrid);
  const footer = organizerNode("footer", "briefing-footer");
  footer.append(organizerNode("strong", "", oc("dataNote")), organizerNode("span", "", content.data_note || ""));
  article.append(sourceDesk, footer);
  intelligenceEditionFeature.append(readerToolbar, article);
}

function renderIntelligenceSubscriptions(snapshot) {
  if (!intelligenceSubscriptionList) return;
  intelligenceSubscriptionList.replaceChildren();
  const subscriptions = organizerArray(snapshot?.intelligence_subscriptions, 50);
  if (!subscriptions.length) {
    intelligenceSubscriptionList.append(organizerEmpty(oc("intelligenceNoSubscriptions")));
    return;
  }
  subscriptions.forEach((subscription) => {
    const card = organizerNode("article", `intelligence-subscription ${Number(subscription.enabled) ? "enabled" : ""}`.trim());
    const heading = organizerNode("div", "intelligence-subscription-head");
    const copy = organizerNode("div", "intelligence-subscription-copy");
    copy.append(
      organizerNode("span", "organizer-kicker", Number(subscription.enabled) ? oc("intelligenceOn") : oc("intelligenceOff")),
      organizerNode("h3", "", subscription.title || oc("untitled")),
      organizerNode("p", "", subscription.prompt || ""),
    );
    heading.append(copy, organizerNode("span", "intelligence-delivery-time", `${subscription.local_time || "08:00"} · ${Number(subscription.edition_count) || 0} ${oc("itemsLabel")}`));
    const actions = organizerNode("div", "intelligence-subscription-actions");
    const edit = organizerNode("button", "intelligence-small-btn", oc("intelligenceEdit"));
    const generate = organizerNode("button", "intelligence-small-btn primary", oc("intelligenceGenerate"));
    const remove = organizerNode("button", "intelligence-small-btn danger", oc("intelligenceDelete"));
    edit.type = generate.type = remove.type = "button";
    generate.addEventListener("click", () => {
      generate.disabled = true;
      setOrganizerStatus(oc("intelligenceWorking"), "working");
      sendJson({ type: "organizer_generate_intelligence", subscription_id: subscription.id });
    });
    edit.addEventListener("click", () => {
      if (card.querySelector(".intelligence-inline-editor, .intelligence-delete-confirm")) return;
      actions.hidden = true;
      const editor = organizerNode("div", "intelligence-inline-editor");
      const titleField = organizerNode("label", "intelligence-editor-field");
      const title = document.createElement("input");
      title.value = subscription.title || "";
      title.maxLength = 140;
      title.setAttribute("aria-label", t("intelligence_title"));
      titleField.append(organizerNode("span", "", t("intelligence_title")), title);
      const promptField = organizerNode("label", "intelligence-editor-field intelligence-editor-goal");
      const prompt = document.createElement("textarea");
      prompt.value = subscription.prompt || "";
      prompt.maxLength = 3000;
      prompt.rows = 5;
      prompt.setAttribute("aria-label", t("intelligence_goal"));
      promptField.append(organizerNode("span", "", t("intelligence_goal")), prompt);
      const timeField = organizerNode("label", "intelligence-editor-field");
      const time = document.createElement("input");
      time.type = "time";
      time.value = subscription.local_time || "08:00";
      time.setAttribute("aria-label", t("intelligence_time"));
      timeField.append(organizerNode("span", "", t("intelligence_time")), time);
      const enabledLabel = organizerNode("label", "intelligence-enable-field");
      const enabled = document.createElement("input"); enabled.type = "checkbox"; enabled.checked = Boolean(Number(subscription.enabled));
      enabledLabel.append(enabled, organizerNode("span", "", t("intelligence_enable")));
      const controls = organizerNode("div", "intelligence-editor-actions");
      const save = organizerNode("button", "intelligence-small-btn primary", oc("intelligenceSaveChanges"));
      const cancel = organizerNode("button", "intelligence-small-btn", oc("cancel"));
      save.type = cancel.type = "button";
      cancel.addEventListener("click", () => {
        editor.remove();
        actions.hidden = false;
        edit.focus();
      });
      save.addEventListener("click", () => {
        if (!title.value.trim() || !prompt.value.trim()) {
          setOrganizerStatus(conversationLanguage === "zh" ? "报纸名称和编辑目标不能为空。" : "A newspaper name and editorial goal are required.", "error");
          (!title.value.trim() ? title : prompt).focus();
          return;
        }
        save.disabled = cancel.disabled = true;
        setOrganizerStatus(oc("intelligenceUpdating"), "working");
        sendJson({ type: "organizer_update_intelligence", subscription_id: subscription.id, title: title.value, prompt: prompt.value, enabled: enabled.checked, local_time: time.value });
      });
      controls.append(save, cancel);
      editor.append(titleField, promptField, timeField, enabledLabel, controls);
      card.append(editor);
      requestAnimationFrame(() => {
        editor.scrollIntoView({ behavior: "smooth", block: "nearest" });
        title.focus({ preventScroll: true });
        title.select();
      });
    });
    remove.addEventListener("click", () => {
      if (card.querySelector(".intelligence-inline-editor, .intelligence-delete-confirm")) return;
      actions.hidden = true;
      const confirmation = organizerNode("div", "intelligence-delete-confirm");
      const message = organizerNode("div", "intelligence-delete-copy");
      message.append(
        organizerNode("strong", "", oc("intelligenceConfirmDelete")),
        organizerNode("span", "", oc("intelligenceDeleteHint")),
      );
      const controls = organizerNode("div", "intelligence-editor-actions");
      const confirm = organizerNode("button", "intelligence-small-btn danger filled", oc("intelligenceConfirmDeleteAction"));
      const cancel = organizerNode("button", "intelligence-small-btn", oc("cancel"));
      confirm.type = cancel.type = "button";
      cancel.addEventListener("click", () => {
        confirmation.remove();
        actions.hidden = false;
        remove.focus();
      });
      confirm.addEventListener("click", () => {
        confirm.disabled = cancel.disabled = true;
        setOrganizerStatus(oc("intelligenceDeleting"), "working");
        sendJson({ type: "organizer_delete_intelligence", subscription_id: subscription.id, confirmed: true });
      });
      controls.append(confirm, cancel);
      confirmation.append(message, controls);
      card.append(confirmation);
      confirmation.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
    actions.append(edit, generate, remove);
    card.append(heading, actions);
    intelligenceSubscriptionList.append(card);
  });
}

function renderOrganizerIntelligence(snapshot) {
  const editions = organizerArray(snapshot?.intelligence_editions, 50);
  renderIntelligenceSubscriptions(snapshot);
  renderIntelligenceEdition(intelligenceEditionForDisplay(editions));
  if (!intelligenceEditionList) return;
  intelligenceEditionList.replaceChildren();
  if (!editions.length) {
    intelligenceEditionList.append(organizerEmpty(oc("intelligenceNoEdition")));
    return;
  }
  editions.forEach((edition) => {
    const card = organizerNode("button", "briefing-archive-item");
    card.type = "button";
    card.append(organizerNode("strong", "", edition.title || oc("untitled")), organizerNode("span", "", organizerDate(edition.generated_at)));
    card.addEventListener("click", () => {
      selectedIntelligenceEditionId = edition.id || "";
      renderIntelligenceEdition(edition);
      intelligenceEditionFeature?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    intelligenceEditionList.append(card);
  });
}

function journalBriefing(day, dateKey) {
  const metrics = day?.metrics && typeof day.metrics === "object" ? day.metrics : {};
  const date = new Date(`${dateKey}T12:00:00`);
  const label = date.toLocaleDateString(conversationLanguage === "zh" ? "zh-CN" : "en-GB", { weekday: "long", year: "numeric", month: "long", day: "numeric" });
  const activity = Number(metrics.activity) || 0;
  const completed = Number(metrics.completed) || 0;
  const created = Number(metrics.created) || 0;
  const meetings = Number(metrics.meetings) || 0;
  const attention = Math.max(0, (Number(metrics.scheduled) || 0) - completed);
  const clarity = activity ? Math.max(25, Math.min(100, Math.round((completed + meetings + 1) / (activity + 1) * 100))) : 100;
  const sections = [
    { key: "journalCompleted", title: oc("journalCompleted"), items: organizerArray(day?.completed_tasks, 30) },
    { key: "journalCreated", title: oc("journalCreated"), items: organizerArray(day?.created_tasks, 30) },
    { key: "journalMeetings", title: oc("journalMeetings"), items: organizerArray(day?.meetings, 30).map((item) => ({ ...item, due_at: item.started_at })) },
    { key: "journalReminders", title: oc("journalReminders"), items: organizerArray(day?.reminders, 30).map((item) => ({ ...item, due_at: item.fire_at })) },
    { key: "journalScheduled", title: oc("journalScheduled"), items: organizerArray(day?.scheduled_tasks, 30) },
    { key: "journalProjects", title: oc("journalProjects"), items: organizerArray(day?.projects, 30) },
  ];
  return {
    id: `journal-${dateKey}`, kind: "journal", generated_at: `${dateKey}T23:59:00`, title: label,
    content: {
      schema_version: 2,
      publication: { masthead: conversationLanguage === "zh" ? "MERRICK 工作日志" : "The MERRICK Work Journal", edition: label },
      headline: activity ? oc("journalHeadline") : oc("journalQuiet"),
      metrics: { primary: completed, attention: created, upcoming: meetings, clarity },
      analysis: {
        title: activity ? `${activity} ${oc("journalActivity").toLocaleLowerCase()}` : oc("journalQuiet"),
        risk: attention > 2 ? "guarded" : "clear",
        items: [
          { tone: "system", label: oc("journalCompleted"), text: `${completed}` },
          { tone: "horizon", label: oc("journalCreated"), text: `${created}` },
          { tone: "priority", label: oc("journalMeetings"), text: `${meetings}` },
        ],
      },
      visual: { label: oc("journalActivity"), score: clarity, risk: attention > 2 ? "guarded" : "clear", series: [
        { key: "primary", value: completed }, { key: "attention", value: created }, { key: "upcoming", value: meetings },
      ] },
      sections,
      data_note: oc("journalDataNote"),
    },
  };
}

function renderWorkJournal(snapshot) {
  if (!journalCalendar) return;
  const dayMap = new Map(organizerArray(snapshot?.work_journal_days, 730).map((day) => [day.date, day]));
  const year = journalVisibleMonth.getFullYear();
  const month = journalVisibleMonth.getMonth();
  if (journalMonthLabel) journalMonthLabel.textContent = journalVisibleMonth.toLocaleDateString(conversationLanguage === "zh" ? "zh-CN" : "en-GB", { year: "numeric", month: "long" });
  journalCalendar.replaceChildren();
  const weekdays = conversationLanguage === "zh" ? ["一", "二", "三", "四", "五", "六", "日"] : ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"];
  weekdays.forEach((weekday) => journalCalendar.append(organizerNode("span", "journal-weekday", weekday)));
  const firstOffset = (new Date(year, month, 1).getDay() + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  for (let index = 0; index < firstOffset; index += 1) journalCalendar.append(organizerNode("span", "journal-day-spacer"));
  for (let dayNumber = 1; dayNumber <= daysInMonth; dayNumber += 1) {
    const date = new Date(year, month, dayNumber);
    const dateKey = localDateKey(date);
    const record = dayMap.get(dateKey);
    const activity = Number(record?.metrics?.activity) || 0;
    const button = organizerNode("button", `journal-day ${dateKey === selectedJournalDate ? "selected" : ""} ${dateKey === localDateKey(new Date()) ? "today" : ""} ${activity ? "has-activity" : ""}`.trim());
    button.type = "button";
    button.style.setProperty("--journal-activity", String(Math.min(1, activity / 8)));
    button.append(organizerNode("strong", "", dayNumber));
    if (activity) button.append(organizerNode("span", "", `${activity} ${oc("itemsLabel")}`));
    button.addEventListener("click", () => {
      selectedJournalDate = dateKey;
      renderWorkJournal(snapshot);
      organizerLatestBriefing?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    journalCalendar.append(button);
  }
  renderBriefingFeature(journalBriefing(dayMap.get(selectedJournalDate), selectedJournalDate), organizerLatestBriefing);
}

function renderOrganizerMeetings(snapshot) {
  if (!organizerMeetingList) return;
  organizerMeetingList.replaceChildren();
  const meetings = organizerArray(snapshot?.meetings, 20);
  if (!meetings.length) {
    organizerMeetingList.append(organizerEmpty(oc("noMeetings")));
    return;
  }
  for (const meeting of meetings) {
    const card = organizerNode("article", "organizer-card meeting-card");
    const head = organizerNode("div", "organizer-card-head");
    const headCopy = organizerNode("div");
    headCopy.append(
      organizerNode("span", "organizer-kicker", oc(meeting.status || "review")),
      organizerNode("h3", "", meeting.title || oc("untitled")),
    );
    head.append(headCopy, organizerNode("span", "meeting-meta", `${organizerDate(meeting.started_at)} · ${Number(meeting.transcript_count) || 0} ${oc("transcriptLines")}`));
    card.append(head);
    if (meeting.summary) card.append(organizerNode("div", "meeting-summary", meeting.summary));
    const columns = organizerNode("div", "meeting-columns");
    const decisions = organizerNode("section", "meeting-column");
    decisions.append(organizerNode("h4", "", oc("decisions")));
    const decisionList = organizerNode("ul");
    const decisionItems = organizerArray(meeting.decisions, 30);
    if (!decisionItems.length) decisionList.append(organizerNode("li", "", oc("noDecisions")));
    for (const decision of decisionItems) decisionList.append(organizerNode("li", "", decision.text || ""));
    decisions.append(decisionList);
    const actions = organizerNode("section", "meeting-column");
    actions.append(organizerNode("h4", "", oc("actions")));
    const actionList = organizerNode("div", "meeting-actions");
    const actionItems = organizerArray(meeting.action_items, 30);
    const proposed = actionItems.filter((item) => item.status === "proposed");
    if (!actionItems.length) actionList.append(organizerEmpty(oc("noActions")));
    for (const action of actionItems) {
      const row = organizerNode("label", `meeting-action ${action.status === "confirmed" ? "confirmed" : ""}`.trim());
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = action.status === "proposed";
      checkbox.disabled = action.status !== "proposed";
      checkbox.dataset.position = String(Number(action.position) || 0);
      const copy = organizerNode("span", "meeting-action-copy");
      copy.append(organizerNode("strong", "", action.title || oc("untitled")));
      const meta = [action.owner, action.due_text || organizerDate(action.due_at), action.status === "confirmed" ? oc("confirmed") : ""].filter(Boolean);
      if (meta.length) copy.append(organizerNode("span", "", meta.join(" · ")));
      row.append(checkbox, copy); actionList.append(row);
    }
    actions.append(actionList);
    if (proposed.length && typeof meeting.id === "string") {
      const confirm = organizerNode("button", "meeting-confirm-btn", oc("confirmSelected"));
      confirm.type = "button";
      confirm.addEventListener("click", () => {
        const positions = [...actionList.querySelectorAll("input:checked")].map((input) => Number(input.dataset.position)).filter(Number.isInteger);
        if (!positions.length) return;
        confirm.disabled = true;
        sendJson({ type: "organizer_confirm_meeting_actions", session_id: meeting.id, positions });
      });
      actions.append(confirm);
    }
    columns.append(decisions, actions); card.append(columns); organizerMeetingList.append(card);
  }
}

function weekdayOptions(selected) {
  const dayKeys = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];
  const select = organizerNode("select");
  dayKeys.forEach((key, value) => {
    const option = organizerNode("option", "", oc(key));
    option.value = String(value); option.selected = value === Number(selected); select.append(option);
  });
  return select;
}

function renderOrganizerSettings(snapshot) {
  if (!organizerSettingList) return;
  organizerSettingList.replaceChildren();
  const settings = organizerArray(snapshot?.briefing_settings, 3);
  for (const setting of settings) {
    if (!["morning", "evening", "weekly"].includes(setting.kind)) continue;
    const card = organizerNode("article", `schedule-card ${Number(setting.enabled) ? "enabled" : ""}`.trim());
    const head = organizerNode("div", "schedule-card-head");
    const copy = organizerNode("div");
    copy.append(organizerNode("h3", "", oc(setting.kind)), organizerNode("p", "", oc(`${setting.kind}Description`)));
    const toggle = organizerNode("label", "schedule-toggle");
    const enabled = document.createElement("input"); enabled.type = "checkbox"; enabled.checked = Boolean(Number(setting.enabled));
    toggle.append(enabled, organizerNode("span")); head.append(copy, toggle); card.append(head);
    const fields = organizerNode("div", "schedule-fields");
    const timeField = organizerNode("label", "schedule-field");
    timeField.append(organizerNode("span", "", oc("deliveryTime")));
    const time = document.createElement("input"); time.type = "time"; time.value = typeof setting.local_time === "string" ? setting.local_time : "09:00"; timeField.append(time); fields.append(timeField);
    let weekday = null;
    if (setting.kind === "weekly") {
      const dayField = organizerNode("label", "schedule-field");
      dayField.append(organizerNode("span", "", oc("deliveryDay")));
      weekday = weekdayOptions(setting.weekday); dayField.append(weekday); fields.append(dayField);
    }
    card.append(fields);
    const actions = organizerNode("div", "schedule-actions");
    const save = organizerNode("button", "meeting-confirm-btn", oc("save")); save.type = "button";
    save.addEventListener("click", () => {
      save.disabled = true;
      sendJson({ type: "organizer_update_briefing", kind: setting.kind, enabled: enabled.checked, local_time: time.value, weekday: weekday ? Number(weekday.value) : Number(setting.weekday || 0) });
      setOrganizerStatus(oc("settingsSaved"));
    });
    const generate = organizerNode("button", "briefing-generate-btn", oc("generate")); generate.type = "button";
    generate.addEventListener("click", () => {
      generate.disabled = true;
      sendJson({ type: "organizer_generate_briefing", kind: setting.kind });
    });
    actions.append(save, generate); card.append(actions); organizerSettingList.append(card);
  }
}

function renderOrganizerCommandGuide() {
  if (!organizerCommandGuide) return;
  organizerCommandGuide.replaceChildren();
  const examples = [
    ["PROJECT", "新建项目叫产品发布", "Create a project called Product launch"],
    ["TASK", "把确认场地加入项目产品发布", "Add confirm the venue to the Product launch project"],
    ["REMINDER", "明早九点提醒我提交周报", "Remind me tomorrow at 9 a.m. to submit the weekly report"],
    ["COMPLETE", "完成任务提交周报", "Complete task submit the weekly report"],
    ["BRIEFING", "开启晨间简报，每天八点", "Enable the morning briefing at 8 a.m."],
    ["MEETING", "确认最近会议的行动项", "Confirm the latest meeting actions"],
  ];
  for (const [label, chinese, english] of examples) {
    const card = organizerNode("article", "command-example");
    card.append(organizerNode("span", "", label), organizerNode("code", "", `中文 · ${chinese}`), organizerNode("code", "", `EN · ${english}`));
    organizerCommandGuide.append(card);
  }
}

function renderOrganizerSnapshot() {
  renderOrganizerCommandGuide();
  if (!organizerSnapshot) return;
  renderOrganizerStats(organizerSnapshot);
  renderPersonalOperations(organizerSnapshot);
  renderOrganizerTasks(organizerSnapshot);
  renderOrganizerReminders(organizerSnapshot);
  renderOrganizerProjects(organizerSnapshot);
  renderOrganizerIntelligence(organizerSnapshot);
  renderWorkJournal(organizerSnapshot);
  renderOrganizerMeetings(organizerSnapshot);
  renderOrganizerSettings(organizerSnapshot);
  if (organizerUpdated) organizerUpdated.textContent = `${oc("updated")} ${organizerDate(organizerSnapshot.generated_at)}`;
}

function receiveOrganizerSnapshot(message) {
  if (!message?.snapshot || typeof message.snapshot !== "object" || Array.isArray(message.snapshot)) return;
  organizerSnapshot = message.snapshot;
  renderOrganizerSnapshot();
  if (intelligenceSaveBtn) intelligenceSaveBtn.disabled = false;
  if (intelligenceGenerateBtn) intelligenceGenerateBtn.disabled = false;
  setOrganizerStatus("");
  if (message.open) setOrganizerVisible(true, typeof message.focus === "string" ? message.focus : "overview");
}

function closeOpenClawApproval(approvalId = null) {
  if (!openClawApproval) return;
  if (approvalId && openClawApproval.dataset.approvalId !== approvalId) return;
  openClawApproval.hidden = true;
  delete openClawApproval.dataset.approvalId;
  openClawApprovalActions?.replaceChildren();
}

function showOpenClawApproval(message) {
  if (!openClawApproval || !openClawApprovalActions) return;
  const approvalId = typeof message.approval_id === "string"
    ? message.approval_id : (typeof message.id === "string" ? message.id : "");
  const decisions = Array.isArray(message.allowed_decisions)
    ? [...new Set(message.allowed_decisions.filter((decision) =>
      ["allow-once", "allow-always", "deny"].includes(decision)
    ))] : [];
  if (!approvalId || !decisions.length) return;
  openClawApproval.dataset.approvalId = approvalId;
  openClawApproval.dataset.severity = ["info", "warning", "critical"].includes(message.severity)
    ? message.severity : "warning";
  openClawApprovalTitle.textContent = typeof message.title === "string" && message.title.trim()
    ? message.title.trim() : (conversationLanguage === "zh" ? "允许这项操作？" : "Allow this action?");
  openClawApprovalDescription.textContent = typeof message.description === "string"
    ? message.description : "";
  openClawApprovalMeta.textContent = message.kind === "exec"
    ? (conversationLanguage === "zh" ? "命令执行 · 需要你的授权" : "COMMAND EXECUTION · YOUR APPROVAL IS REQUIRED")
    : (conversationLanguage === "zh" ? "应用或插件权限 · 需要你的授权" : "APP OR PLUGIN ACCESS · YOUR APPROVAL IS REQUIRED");
  openClawApprovalActions.replaceChildren();
  const labels = conversationLanguage === "zh"
    ? { "allow-once": "仅本次允许", "allow-always": "始终允许", deny: "拒绝" }
    : { "allow-once": "ALLOW ONCE", "allow-always": "ALWAYS ALLOW", deny: "DENY" };
  const ordered = ["deny", "allow-always", "allow-once"].filter((decision) => decisions.includes(decision));
  ordered.forEach((decision) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `setup-action-btn ${decision === "deny" ? "danger" : decision === "allow-always" ? "secondary" : ""}`.trim();
    button.textContent = labels[decision];
    button.addEventListener("click", () => {
      for (const control of openClawApprovalActions.querySelectorAll("button")) control.disabled = true;
      sendJson({
        type: "openclaw_approval_response",
        approval_id: approvalId,
        decision,
      });
      closeOpenClawApproval(approvalId);
    });
    openClawApprovalActions.append(button);
  });
  openClawApproval.hidden = false;
  openClawApprovalActions.querySelector('button[data-decision="allow-once"]')?.focus();
  (openClawApprovalActions.lastElementChild || openClawApprovalTitle)?.focus?.();
}

// ---------------- WebSocket ----------------
function nextReconnectDelay() {
  const delay = Math.min(30000, 3000 * (2 ** reconnectAttempts));
  reconnectAttempts = Math.min(reconnectAttempts + 1, 4);
  return delay;
}

function connect() {
  if (appClosing) return;
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const wsUrl = new URL(`${proto}://${location.host}${MERRICK_RUNTIME_CONTRACT.localServices.backend.websocketPath}`);
  const protocols = bridgeToken ? ["jarvis-v1", bridgeToken] : [];
  ws = new WebSocket(wsUrl.toString(), protocols);

  ws.onopen = () => {
    displayProviderConnection(providerConnectionState);
    if (onboardingRequired || providerManagerRequested) requestProviderModels();
    connDot.className = "conn-dot online";
    connText.textContent = t("online");
    serverState = "connecting";
    refreshUiState();
    sendJson({ type: "set_tts_streaming", enabled: supportsIncrementalTtsAudio() });
    sendJson({ type: "multi_agent_refresh" });
    logLine("info", conversationLanguage === "zh" ? "已连接到 MERRICK 核心" : "Connected to the MERRICK core.");
  };

  ws.onclose = () => {
    providerRuntimeState = null;
    displayProviderConnection(providerConnectionState);
    connDot.className = "conn-dot offline";
    connText.textContent = t("offline");
    if (isDesktop) {
      if (nativeActionInFlight) {
        nativePost("cancelAction", { requestId: nativeActionInFlight });
        nativeActionInFlight = null;
      }
    }
    serverState = "offline";
    closeOpenClawApproval();
    refreshUiState();
    if (!appClosing) {
      const delay = nextReconnectDelay();
      const seconds = Math.ceil(delay / 1000);
      logLine("err", conversationLanguage === "zh"
        ? `连接已断开，${seconds} 秒后重连…`
        : `Connection lost; reconnecting in ${seconds} seconds…`);
      if (reconnectTimer) clearTimeout(reconnectTimer);
      reconnectTimer = setTimeout(() => {
        reconnectTimer = null;
        connect();
      }, delay);
    }
  };

  ws.onmessage = (ev) => {
    let msg;
    try { msg = JSON.parse(ev.data); } catch { return; }
    switch (msg.type) {
      case "ready":
        reconnectAttempts = 0;
        logLine("info", conversationLanguage === "zh" ? "MERRICK 已就绪。" : "MERRICK is ready.");
        if (isDesktop) {
          autoToggle.checked = true;
          nativePost("webReady");
          nativePost("getProviderSetupState");
        }
        break;
      case "organizer_snapshot":
        receiveOrganizerSnapshot(msg);
        break;
      case "organizer_intelligence_progress": {
        const stageCopy = msg.stage === "planning" ? oc("intelligencePlanning")
          : msg.stage === "reading" ? oc("intelligenceReading")
          : msg.stage === "synthesizing" ? oc("intelligenceSynthesizing")
            : oc("intelligenceWorking");
        setOrganizerStatus(stageCopy, "working");
        break;
      }
      case "meeting_summary_ready":
        receiveOrganizerSnapshot(msg);
        setOrganizerStatus(oc("meetingReady"));
        logLine("info", oc("meetingReady"));
        break;
      case "briefing_ready":
        receiveOrganizerSnapshot(msg);
        setOrganizerStatus(oc("briefingReady"));
        logLine("info", oc("briefingReady"));
        break;
      case "meeting_session_started":
        setOrganizerStatus(oc("meetingStarted"));
        logLine("info", oc("meetingStarted"));
        break;
      case "plan_mode_state":
      case "plan_mode_step":
      case "plan_mode_error":
        window.MerrickPlanMode?.handleMessage(msg);
        break;
      case "multi_agent_state":
      case "multi_agent_error":
        if (window.MerrickAgentBoard) window.MerrickAgentBoard.handleMessage(msg);
        else window.__merrickPendingMultiAgentMessage = msg;
        break;
      case "organizer_error":
        setOrganizerStatus(typeof msg.text === "string" ? msg.text : "MERRICK organizer error.", "error");
        break;
      case "local_notification_schedule": {
        const id = typeof msg.id === "string" ? msg.id : "";
        const title = typeof msg.title === "string" ? msg.title : "";
        const body = typeof msg.body === "string" ? msg.body : "";
        const fireAt = typeof msg.fire_at === "string" ? msg.fire_at : "";
        if (!id || !nativePost("scheduleLocalNotification", { id, title, body, fireAt })) {
          sendJson({ type: "local_notification_result", id, ok: false });
          setOrganizerStatus(oc("notificationUnavailable"), "error");
        }
        break;
      }
      case "local_notification_cancel":
        if (typeof msg.id === "string") nativePost("cancelLocalNotification", { id: msg.id });
        break;
      case "voice_identity":
        if (msg.status === "owner") logLine("info", conversationLanguage === "zh" ? "已验证主人声纹。" : "Owner voice verified.");
        else if (msg.status === "guest") logLine("info", conversationLanguage === "zh" ? "检测到访客声纹；私人记忆仍保持锁定。" : "Guest voice detected; private memory remains locked.");
        handleWatchModeIdentity(msg);
        break;
      case "voiceprint_management_status":
        updateVoiceprintManagementStatus(msg);
        break;
      case "capabilities_inventory":
        receiveCapabilityInventory(msg);
        break;
      case "capabilities_catalog":
        receivePluginCatalog(msg);
        break;
      case "capability_review":
        capabilityBusy = false;
        renderCapabilityReview(msg);
        setCapabilityStatus(conversationLanguage === "zh" ? "OpenClaw 能力审查已就绪。" : "OpenClaw capability review is ready.", "ready");
        break;
      case "plugin_operation_review":
        capabilityBusy = false;
        renderCapabilityReview(msg);
        setCapabilityStatus(conversationLanguage === "zh" ? "OpenClaw 插件安全审查已就绪。" : "OpenClaw plugin security review is ready.", "ready");
        break;
      case "capability_changed":
        closeCapabilityReview();
        receiveCapabilityInventory(msg, msg.restarted
          ? t("plugin_changed")
          : t("skill_changed"));
        break;
      case "plugin_operation_changed":
        closeCapabilityReview();
        receiveCapabilityInventory(msg, t("plugin_changed"));
        receivePluginCatalog(msg);
        break;
      case "capabilities_diagnostics":
        renderCapabilityDiagnostics(Array.isArray(msg.findings) ? msg.findings : []);
        setCapabilityStatus(t("diagnostics_complete"), "ready");
        break;
      case "capabilities_error":
        capabilityBusy = false;
        if (capabilityReviewConfirm) capabilityReviewConfirm.disabled = false;
        setCapabilityStatus(typeof msg.text === "string" ? msg.text : t("capability_failed"), "error");
        renderCapabilityInventory();
        break;
      case "openclaw_approval_request":
        showOpenClawApproval(msg);
        break;
      case "openclaw_approval_closed":
        closeOpenClawApproval(typeof msg.approval_id === "string" ? msg.approval_id : null);
        break;
      case "status":
        serverState = msg.state === "booting" && ws?.readyState === WebSocket.OPEN
          ? "connecting" : msg.state;
        if (isDesktop && (msg.state === "thinking" || msg.state === "acting") && recognizing) {
          // Close the current recognition request before any response audio can
          // reach the speakers. This resets the accumulated transcript and
          // prevents MERRICK from recursively answering his own TTS.
          nativePost("stopListening");
        }
        if (msg.state === "idle") {
          // A research/action run can return to idle without a later `done`
          // event (for example after a provider fallback). Never leave its
          // yellow progress copy on the transparent desktop HUD.
          closeStreamBubble();
          interimEl.textContent = "";
          document.body.dataset.streaming = "false";
        }
        refreshUiState();
        if (msg.state === "idle" && !audioPlaying) maybeAutoListen();
        break;
      case "turn":
        currentTurn = msg.n;
        activeAssistantText = "";
        currentResearchSources = [];
        if (researchQuery) {
          delete researchQuery.dataset.i18nDynamic;
          researchQuery.textContent = t("live_answer");
        }
        renderResearchSources();
        responseComplete = false;
        committedSpeech = "";
        break;
      case "assistant_delta":
        appendDelta(msg.text);
        if (displayAnswer) renderDisplayText(displayAnswer, activeAssistantText);
        break;
      case "research_query_choice":
        // Search is intentionally paused here.  The server only emits this
        // when local speech correction found more than one credible technical
        // term, so the user—not a guess—chooses the public query.
        showResearchQueryChoice(msg);
        break;
      case "research_query_resolved": {
        // The backend emits this before requesting any search provider.  It is
        // the exact, locally corrected query—not an inferred title—so the
        // user can immediately verify what MERRICK will actually search for.
        const query = typeof msg.query === "string" ? msg.query.trim() : "";
        if (!query) break;
        clearResearchQueryChoice();
        currentResearchSources = [];
        if (researchQuery) {
          researchQuery.dataset.i18nDynamic = "true";
          researchQuery.textContent = conversationLanguage === "zh"
            ? `检索：${query}`
            : `Search: ${query}`;
        }
        if (displayAnswer) {
          displayAnswer.textContent = t("preparing_answer");
        }
        renderResearchSources();
        setResearchDisplayVisible(true);
        break;
      }
      case "research_sources": {
        clearResearchQueryChoice();
        const sources = Array.isArray(msg.sources) ? msg.sources.filter((source) => source &&
          typeof source.url === "string" && /^https?:\/\//i.test(source.url) &&
          typeof source.title === "string" && typeof source.snippet === "string").slice(0, 5) : [];
        currentResearchSources = sources;
        if (researchQuery) {
          researchQuery.dataset.i18nDynamic = "true";
          researchQuery.textContent = typeof msg.query === "string" ? msg.query : t("research_sources");
        }
        renderResearchSources();
        setResearchDisplayVisible(true);
        break;
      }
      case "research_open_pages": {
        const urls = Array.isArray(msg.urls) ? msg.urls.filter((url) =>
          typeof url === "string" && /^https?:\/\//i.test(url) && url.length <= 2048
        ).slice(0, 8) : [];
        if (!urls.length) break;
        setResearchDisplayVisible(true);
        if (!nativePost("openResearchPages", { urls })) {
          logLine("err", conversationLanguage === "zh" ? "研究页面只能在 MERRICK 桌面 App 中打开。" : "Research pages can be opened only in the MERRICK desktop app.");
        }
        break;
      }
      case "assistant_block_done":
        closeStreamBubble();
        break;
      case "assistant_text": // 非流式回退路径
        closeStreamBubble();
        addMsg("jarvis", msg.text);
        break;
      case "tool_use":
        closeStreamBubble();
        logLine("tool", `${msg.label}: ${msg.detail}`);
        break;
      case "speech_ack":
        document.body.dataset.streaming = msg.chars ? "true" : "false";
        break;
      case "screen_capture_request": {
        const requestId = typeof msg.request_id === "string" ? msg.request_id : "";
        if (!/^[0-9a-f]{32}$/.test(requestId)) break;
        if (!isDesktop || !nativePost("captureScreen", { requestId })) {
          sendJson({
            type: "screen_capture_result",
            request_id: requestId,
            data: "",
            mime: "",
            error: t("screen_desktop_only"),
          });
        }
        break;
      }
      case "native_action_request": {
        const requestId = typeof msg.request_id === "string" ? msg.request_id : "";
        if (!/^[0-9a-f]{32}$/.test(requestId)) break;
        const action = validateNativeAction(msg.action);
        if (!action) {
          rejectNativeAction(requestId, "The requested desktop action did not match the bridge protocol.");
          break;
        }
        if (!isDesktop || !nativeBridge || !bridgeToken) {
          rejectNativeAction(requestId, "Desktop actions are available only in the MERRICK app.");
          break;
        }
        if (nativeActionInFlight) {
          rejectNativeAction(requestId, "Another desktop action is still in progress.");
          break;
        }
        nativeActionInFlight = requestId;
        try {
          if (!nativePost("performAction", { requestId, nativeAction: action })) {
            nativeActionInFlight = null;
            rejectNativeAction(requestId, "The trusted desktop action bridge is unavailable.");
          }
        } catch {
          nativeActionInFlight = null;
          rejectNativeAction(requestId, "The trusted desktop action bridge rejected the request.");
        }
        break;
      }
      case "native_action_cancel": {
        const requestId = typeof msg.request_id === "string" ? msg.request_id : "";
        if (!/^[0-9a-f]{32}$/.test(requestId) || requestId !== nativeActionInFlight) break;
        nativeActionInFlight = null;
        if (isDesktop) nativePost("cancelAction", { requestId });
        break;
      }
      case "audio":
        if (msg.turn === undefined || msg.turn === currentTurn)
          enqueueAudio(msg.data, msg.mime || "audio/mpeg", msg.role || "answer");
        break;
      case "audio_stream_start":
        if (msg.turn === undefined || msg.turn === currentTurn)
          enqueueAudioStreamStart(msg);
        break;
      case "audio_stream_chunk":
        if (msg.turn === undefined || msg.turn === currentTurn)
          enqueueAudioStreamChunk(msg);
        break;
      case "audio_stream_end":
        if (msg.turn === undefined || msg.turn === currentTurn)
          enqueueAudioStreamEnd(msg);
        break;
      case "audio_cancelled":
        currentTurn = msg.turn;
        stopAudio();
        // An interruption can arrive while a streamed MP3 segment is still
        // open. Do not wait for an obsolete `done` event to remove the
        // STREAMING state: the cancelled turn will never legitimately finish.
        responseComplete = true;
        closeStreamBubble();
        document.body.dataset.streaming = "false";
        interimEl.textContent = "";
        refreshUiState();
        maybeAutoListen();
        if (meetingCommandInterruptPending && meetingCommandTranscript) {
          // The backend has now invalidated the old answer. Submit only the
          // already-recognised “Merrick …” command, then allow cumulative
          // follow-up callbacks to replace this speculative draft normally.
          meetingCommandInterruptPending = false;
          forwardNativeTranscript(meetingCommandTranscript, false);
        }
        break;
      case "done":
        responseComplete = true;
        closeStreamBubble();
        interimEl.textContent = "";
        chatEl?.replaceChildren();
        maybeAutoListen();
        break;
      case "input_cleared":
        debounceSent = "";
        committedSpeech = "";
        interimEl.textContent = "";
        document.body.dataset.streaming = "false";
        break;
      case "notice":
        logLine("info", msg.text);
        break;
      case "action_progress":
        if (typeof msg.text !== "string") break;
        serverState = "acting";
        interimEl.textContent = msg.text;
        logLine("tool", msg.text);
        refreshUiState();
        break;
      case "provider_auth_required": {
        const message = connectionFailureCopy("AUTH_REJECTED");
        closeStreamBubble();
        logLine("err", message);
        interimEl.textContent = message;
        providerAuthRequired = true;
        nativePost("markProviderConnectionFailed", { code: "AUTH_REJECTED" });
        displayProviderConnection(providerConnectionState);
        setProviderSetupStatus(message, "error");
        break;
      }
      case "provider_connection_issue": {
        const code = typeof msg.code === "string" ? msg.code : "PROVIDER_FAILED";
        const reconnectRequired = msg.reconnectRequired === true;
        const localized = connectionFailureCopy(code);
        closeStreamBubble();
        logLine("err", localized);
        interimEl.textContent = localized;
        if (reconnectRequired) {
          providerAuthRequired = true;
          nativePost("markProviderConnectionFailed", { code });
          displayProviderConnection(providerConnectionState);
          setProviderSetupStatus(localized, "error");
        }
        break;
      }
      case "provider_models": {
        if (msg.request_id !== providerCatalogRequest || msg.provider !== selectedProvider) break;
        providerModelCatalog = {provider: msg.provider, models: Array.isArray(msg.models) ? msg.models : [], status: msg.status};
        renderProviderModels();
        break;
      }
      case "model_runtime_status": {
        providerRuntimeState = {
          ready: msg.ready === true,
          message: typeof msg.message === "string" ? msg.message : "",
        };
        displayProviderConnection(providerConnectionState);
        if (providerRuntimeState.message) {
          logLine(providerRuntimeState.ready ? "info" : "err", providerRuntimeState.message);
        }
        break;
      }
      case "error":
        closeStreamBubble();
        logLine("err", msg.text);
        addMsg("jarvis", "⚠ " + msg.text);
        break;
    }
  };
}

function sendJson(obj) {
  if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(obj));
}

window.addEventListener("merrick-plan-send", (event) => {
  if (event.detail && typeof event.detail.type === "string") sendJson(event.detail);
});

window.addEventListener("merrick-agent-board-send", (event) => {
  if (event.detail && typeof event.detail.type === "string") sendJson(event.detail);
});

function submitText(text, showUser = true) {
  text = text.trim();
  if (!text) return;
  stopAudio(); // 新指令打断当前播报
  closeStreamBubble();
  if (showUser) addMsg("user", text);
  sendJson({ type: "user_text", text, typed: true });
}

// ---------------- audio playback queue ----------------
const audioQueue = [];
const streamAudioItems = new Map();
let audioPlaying = false;
let currentAudio = null;
let currentAudioItem = null;
let playbackDrainTimer = null;
let audioOutputContext = null;
let audioOutputNeedsWarmup = true;
const PCM_INITIAL_BUFFER_SECONDS = 0.36;
const PCM_SCHEDULE_LEAD_SECONDS = 0.06;
const PCM_UNDERRUN_FADE_SECONDS = 0.008;

async function warmAudioOutput() {
  if (!audioOutputNeedsWarmup) return;
  audioOutputNeedsWarmup = false;
  try {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return;
    if (!audioOutputContext) audioOutputContext = new AudioContextClass();
    if (audioOutputContext.state === "suspended") await audioOutputContext.resume();
    const oscillator = audioOutputContext.createOscillator();
    const gain = audioOutputContext.createGain();
    // A practically silent signal opens the WebKit/CoreAudio output path. The
    // real MP3 then starts from its first frame instead of donating its first
    // phoneme to device wake-up.
    gain.gain.value = 0.000001;
    oscillator.frequency.value = 20;
    oscillator.connect(gain);
    gain.connect(audioOutputContext.destination);
    oscillator.start();
    oscillator.stop(audioOutputContext.currentTime + 0.12);
    await new Promise((resolve) => setTimeout(resolve, 125));
    sendJson({ type: "client_event", event: "audio_output_warmed", detail: "duration_ms=125" });
  } catch (error) {
    sendJson({ type: "client_event", event: "audio_output_warm_failed", detail: String(error?.name || "failed") });
  }
}

function supportsMpegStreamAudio() {
  try {
    return Boolean(window.MediaSource && MediaSource.isTypeSupported("audio/mpeg"));
  } catch {
    return false;
  }
}

function supportsIncrementalTtsAudio() {
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  return Boolean(AudioContextClass || supportsMpegStreamAudio());
}

function isPcmStreamMime(mime) {
  return mime === "audio/pcm;format=s16le";
}

function streamAudioKey(turn, sequence) {
  return `${Number(turn)}:${Number(sequence)}`;
}

function base64ToBytes(value) {
  const raw = atob(String(value || ""));
  const bytes = new Uint8Array(raw.length);
  for (let index = 0; index < raw.length; index += 1) bytes[index] = raw.charCodeAt(index);
  return bytes;
}

function markStreamAudioFailed(item, detail) {
  if (!item || item.streamFailed) return;
  item.streamFailed = true;
  sendJson({ type: "client_event", event: "audio_stream_fallback", detail: String(detail || "unknown").slice(0, 120) });
}

function flushStreamAudio(item) {
  if (!item?.sourceBuffer || item.sourceBuffer.updating || item.streamFailed) return;
  if (item.appendIndex < item.chunks.length) {
    const next = item.chunks[item.appendIndex];
    item.appendIndex += 1;
    try {
      item.sourceBuffer.appendBuffer(next);
    } catch (error) {
      markStreamAudioFailed(item, `append:${error?.name || "failed"}`);
    }
    return;
  }
  if (item.ended && item.mediaSource?.readyState === "open") {
    try { item.mediaSource.endOfStream(); }
    catch (error) { markStreamAudioFailed(item, `end:${error?.name || "failed"}`); }
  }
}

function prepareStreamingAudio(item) {
  if (!item || item.audio || !supportsMpegStreamAudio()) return item?.audio || null;
  const mediaSource = new MediaSource();
  const audio = new Audio();
  const objectUrl = URL.createObjectURL(mediaSource);
  item.mediaSource = mediaSource;
  item.objectUrl = objectUrl;
  audio.preload = "auto";
  audio.volume = 1.0;
  audio.src = objectUrl;
  mediaSource.addEventListener("sourceopen", () => {
    if (item.streamFailed || item.mediaSource !== mediaSource) return;
    try {
      const sourceBuffer = mediaSource.addSourceBuffer(item.mime);
      sourceBuffer.mode = "sequence";
      item.sourceBuffer = sourceBuffer;
      sourceBuffer.addEventListener("updateend", () => flushStreamAudio(item));
      sourceBuffer.addEventListener("error", () => markStreamAudioFailed(item, "source_buffer_error"));
      flushStreamAudio(item);
    } catch (error) {
      markStreamAudioFailed(item, `source_open:${error?.name || "failed"}`);
    }
  }, { once: true });
  item.audio = audio;
  return audio;
}

function prepareAudioItem(item) {
  if (!item || item.audio) return item?.audio || null;
  if (item.kind === "pcm-stream") return null;
  if (item.kind === "stream") return prepareStreamingAudio(item);
  const audio = new Audio(item.src);
  audio.preload = "auto";
  audio.volume = 1.0;
  audio.load();
  item.audio = audio;
  return audio;
}

function primeNextAudio() {
  if (audioQueue.length) prepareAudioItem(audioQueue[0]);
}

function disposeAudio(audio) {
  if (!audio) return;
  audio.onended = null;
  audio.onerror = null;
  audio.pause();
  audio.removeAttribute("src");
}

function disposeAudioItem(item) {
  if (!item) return;
  if (item.kind === "stream" || item.kind === "pcm-stream") {
    streamAudioItems.delete(item.key);
  }
  if (item.kind === "pcm-stream" && item.sources) {
    for (const source of item.sources) {
      try { source.stop(); } catch {}
      try { source.disconnect(); } catch {}
      try { source.merrickOutputGain?.disconnect(); } catch {}
    }
    item.sources.clear();
  }
  if (item.objectUrl) URL.revokeObjectURL(item.objectUrl);
  disposeAudio(item.audio);
}

function promoteStreamFallback(item) {
  if (!item || !item.streamFailed || !item.ended || item.fallbackPromoted) return;
  item.fallbackPromoted = true;
  const wasCurrent = currentAudioItem === item;
  streamAudioItems.delete(item.key);
  if (item.objectUrl) URL.revokeObjectURL(item.objectUrl);
  disposeAudio(item.audio);
  item.kind = "blob";
  item.objectUrl = URL.createObjectURL(new Blob(item.chunks, { type: item.mime }));
  item.src = item.objectUrl;
  item.audio = null;
  if (wasCurrent) {
    currentAudio = null;
    currentAudioItem = null;
    audioQueue.unshift(item);
    playNext();
  }
}

function resetBargeCandidate() {
  bargeCandidate = "";
  bargeCandidateHits = 0;
  bargeCandidateSince = 0;
  bargeCandidateGrowth = 0;
  bargeCandidateNovelCount = 0;
}

function enqueueAudio(b64, mime, role = "answer") {
  if (!ttsToggle.checked) return;
  sendJson({ type: "client_event", event: "audio_received", detail: `chars=${b64.length}` });
  audioQueue.push({ src: `data:${mime};base64,${b64}`, audio: null, role });
  primeNextAudio();
  // If a new streamed segment arrives during the short end-of-segment drain,
  // continue immediately instead of briefly declaring playback finished.
  if (playbackDrainTimer) {
    clearTimeout(playbackDrainTimer);
    playbackDrainTimer = null;
    playNext();
  } else if (!audioPlaying) playNext();
}

function enqueueAudioStreamStart(msg) {
  if (!ttsToggle.checked || !supportsIncrementalTtsAudio()) return;
  const sequence = Number(msg.seq);
  const turn = Number(msg.turn);
  if (!Number.isInteger(sequence) || !Number.isInteger(turn)) return;
  const key = streamAudioKey(turn, sequence);
  if (streamAudioItems.has(key)) return;
  const pcm = isPcmStreamMime(msg.mime);
  if (!pcm && !supportsMpegStreamAudio()) return;
  const sampleRate = Number(msg.sample_rate);
  const channels = Number(msg.channels);
  if (pcm && (!Number.isInteger(sampleRate) || sampleRate < 8_000 || sampleRate > 192_000 ||
      !Number.isInteger(channels) || channels < 1 || channels > 2)) return;
  const item = pcm ? {
    kind: "pcm-stream", key, mime: msg.mime, sampleRate, channels,
    chunks: [], appendIndex: 0, ended: false, streamFailed: false,
    sources: new Set(), nextStartAt: 0, ready: false, playbackSignalled: false,
    audio: null, objectUrl: "",
  } : {
    kind: "stream", key, mime: msg.mime === "audio/mpeg" ? msg.mime : "audio/mpeg",
    chunks: [], appendIndex: 0, ended: false, streamFailed: false,
    audio: null, mediaSource: null, sourceBuffer: null, objectUrl: "",
  };
  streamAudioItems.set(key, item);
  audioQueue.push(item);
  primeNextAudio();
  if (playbackDrainTimer) {
    clearTimeout(playbackDrainTimer);
    playbackDrainTimer = null;
    playNext();
  } else if (!audioPlaying) {
    playNext();
  }
}

function enqueueAudioStreamChunk(msg) {
  const item = streamAudioItems.get(streamAudioKey(msg.turn, msg.seq));
  if (!item || item.streamFailed || typeof msg.data !== "string") return;
  if (item.kind === "pcm-stream") {
    enqueuePcmAudioStreamChunk(item, msg.data);
    return;
  }
  try {
    item.chunks.push(base64ToBytes(msg.data));
    flushStreamAudio(item);
  } catch (error) {
    markStreamAudioFailed(item, `decode:${error?.name || "failed"}`);
  }
}

function enqueueAudioStreamEnd(msg) {
  const item = streamAudioItems.get(streamAudioKey(msg.turn, msg.seq));
  if (!item) return;
  item.ended = true;
  if (item.kind === "pcm-stream") {
    schedulePcmAudioChunks(item);
    maybeFinishPcmAudioStream(item);
    return;
  }
  if (item.streamFailed) {
    promoteStreamFallback(item);
    return;
  }
  flushStreamAudio(item);
}

function markAssistantPlaybackStarted(detail) {
  sendJson({ type: "client_event", event: "audio_play_started", detail });
  if (!isDesktop) return;
  const startingBargeSession = !bargeInMode;
  bargeInMode = true;
  if (startingBargeSession) {
    resetBargeCandidate();
    recentVoiceEvidenceAt = 0;
  }
  if (!listeningManuallyMuted && !recognizing)
    nativePost("startListening", { echoCancel: false });
  setTimeout(() => {
    if (!listeningManuallyMuted && audioPlaying && bargeInMode && !recognizing)
      nativePost("startListening", { echoCancel: false });
  }, 180);
}

function maybeFinishPcmAudioStream(item) {
  if (!item?.ended || item.appendIndex < item.chunks.length || item.sources.size) return;
  if (currentAudioItem !== item) return;
  currentAudioItem = null;
  currentAudio = null;
  sendJson({ type: "client_event", event: "audio_segment_ended", detail: `remaining=${audioQueue.length} pcm=true` });
  disposeAudioItem(item);
  playNext();
}

function pendingPcmDurationSeconds(item) {
  if (!item || !item.sampleRate || !item.channels) return 0;
  let pendingBytes = 0;
  for (let index = item.appendIndex; index < item.chunks.length; index += 1) {
    pendingBytes += item.chunks[index].byteLength;
  }
  return pendingBytes / (item.channels * 2 * item.sampleRate);
}

function schedulePcmAudioChunks(item) {
  if (!item?.ready || item.streamFailed || currentAudioItem !== item) return;
  const context = audioOutputContext;
  if (!context) return;
  const pendingDuration = pendingPcmDurationSeconds(item);
  if (!item.playbackSignalled && !item.ended &&
      pendingDuration < PCM_INITIAL_BUFFER_SECONDS) return;
  while (item.appendIndex < item.chunks.length) {
    const bytes = item.chunks[item.appendIndex++];
    const frameBytes = item.channels * 2;
    const frames = Math.floor(bytes.byteLength / frameBytes);
    if (!frames) continue;
    const buffer = context.createBuffer(item.channels, frames, item.sampleRate);
    const view = new DataView(bytes.buffer, bytes.byteOffset, frames * frameBytes);
    for (let channel = 0; channel < item.channels; channel += 1) {
      const samples = buffer.getChannelData(channel);
      for (let frame = 0; frame < frames; frame += 1) {
        samples[frame] = view.getInt16((frame * item.channels + channel) * 2, true) / 32768;
      }
    }
    const source = context.createBufferSource();
    source.buffer = buffer;
    const earliest = context.currentTime + PCM_SCHEDULE_LEAD_SECONDS;
    const underrun = item.playbackSignalled && item.nextStartAt > 0 &&
      item.nextStartAt < earliest;
    const startAt = Math.max(earliest, item.nextStartAt || earliest);
    if (underrun) {
      const outputGain = context.createGain();
      outputGain.gain.setValueAtTime(0, startAt);
      outputGain.gain.linearRampToValueAtTime(
        1,
        startAt + Math.min(PCM_UNDERRUN_FADE_SECONDS, buffer.duration / 4),
      );
      source.connect(outputGain);
      outputGain.connect(context.destination);
      source.merrickOutputGain = outputGain;
    } else {
      source.connect(context.destination);
    }
    item.nextStartAt = startAt + buffer.duration;
    item.sources.add(source);
    source.onended = () => {
      item.sources.delete(source);
      try { source.disconnect(); } catch {}
      try { source.merrickOutputGain?.disconnect(); } catch {}
      maybeFinishPcmAudioStream(item);
    };
    source.start(startAt);
    if (!item.playbackSignalled) {
      item.playbackSignalled = true;
      markAssistantPlaybackStarted(`role=${item.role || "answer"} remaining=${audioQueue.length} pcm=true`);
    }
  }
  maybeFinishPcmAudioStream(item);
}

function enqueuePcmAudioStreamChunk(item, encoded) {
  try {
    const bytes = base64ToBytes(encoded);
    if (bytes.byteLength % (item.channels * 2) !== 0) throw new Error("unaligned_pcm");
    item.chunks.push(bytes);
    schedulePcmAudioChunks(item);
  } catch (error) {
    markStreamAudioFailed(item, `pcm_decode:${error?.message || error?.name || "failed"}`);
    if (currentAudioItem === item) {
      currentAudioItem = null;
      disposeAudioItem(item);
      playNext();
    }
  }
}

async function activatePcmAudioStream(item, firstSegmentAfterIdle) {
  try {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) throw new Error("audio_context_unavailable");
    if (!audioOutputContext) audioOutputContext = new AudioContextClass();
    if (audioOutputContext.state === "suspended") await audioOutputContext.resume();
    if (firstSegmentAfterIdle) await warmAudioOutput();
    if (currentAudioItem !== item || !audioPlaying) return;
    item.ready = true;
    schedulePcmAudioChunks(item);
  } catch (error) {
    markStreamAudioFailed(item, `pcm_context:${error?.name || "failed"}`);
    if (currentAudioItem === item) {
      currentAudioItem = null;
      disposeAudioItem(item);
      playNext();
    }
  }
}

function playNext() {
  const item = audioQueue.shift();
  if (!item) {
    currentAudio = null;
    currentAudioItem = null;
    // Keep a tiny drain window. It preserves the final phoneme on CoreAudio and
    // prevents rapid speaking/listening state changes between streamed clips.
    clearTimeout(playbackDrainTimer);
    playbackDrainTimer = setTimeout(() => {
      playbackDrainTimer = null;
      if (audioQueue.length) return playNext();
      audioPlaying = false;
      audioOutputNeedsWarmup = true;
      // An AEC candidate that never became a text-verified owner
      // interruption was speaker leakage, not a user instruction.
      if (watchModeEnabled && !watchVoiceVerificationRequested) {
        cleanBargeTranscriptBaseline = "";
        watchCleanVoiceActive = false;
      }
      if (isDesktop) nativePost("assistantAudioState", { playing: false });
      playbackStartedAt = 0;
      if (isDesktop && bargeInMode) {
        bargeInMode = false;
        nativePost("stopListening");
      }
      resetBargeCandidate();
      assistantEchoGuardUntil = Date.now() + 3000;
      sendJson({ type: "client_event", event: "audio_play_finished", detail: "queue_drained" });
      refreshUiState();
      if (responseComplete) maybeAutoListen();
    }, 180);
    return;
  }
  const firstSegmentAfterIdle = !audioPlaying;
  if (firstSegmentAfterIdle) playbackStartedAt = Date.now();
  audioPlaying = true;
  // A new assistant response begins a fresh recognizer/acoustic context. Any
  // prefix saved for the prior interrupted response must not affect it.
  cleanBargeTranscriptBaseline = "";
  playbackTranscriptBaseline = "";
  watchCleanVoiceActive = false;
  watchVoiceVerificationRequested = false;
  clearTimeout(watchVerificationTimeout);
  watchVerificationTimeout = null;
  if (isDesktop) nativePost("assistantAudioState", { playing: true });
  refreshUiState();
  if (item.kind === "pcm-stream") {
    currentAudio = null;
    currentAudioItem = item;
    primeNextAudio();
    void activatePcmAudioStream(item, firstSegmentAfterIdle);
    return;
  }
  const audio = prepareAudioItem(item);
  if (!audio) {
    markStreamAudioFailed(item, "media_source_unsupported");
    return playNext();
  }
  currentAudio = audio;
  currentAudioItem = item;
  primeNextAudio();
  audio.onended = () => {
    if (currentAudio !== audio) return;
    currentAudio = null;
    currentAudioItem = null;
    sendJson({ type: "client_event", event: "audio_segment_ended", detail: `remaining=${audioQueue.length} next_ready=${audioQueue[0]?.audio?.readyState || 0}` });
    disposeAudioItem(item);
    playNext();
  };
  audio.onerror = () => {
    if (currentAudio !== audio) return;
    // MediaSource fallback is deliberately held until the stream has ended;
    // its initial capability test normally prevents this branch on desktop.
    if (item.kind === "stream" && !item.ended) {
      markStreamAudioFailed(item, "audio_element_error");
      return;
    }
    currentAudio = null;
    currentAudioItem = null;
    sendJson({ type: "client_event", event: "audio_segment_error", detail: `remaining=${audioQueue.length}` });
    disposeAudioItem(item);
    playNext();
  };
  // CoreAudio/WebKit can discard the onset when a MediaSource element is told
  // to play before it has decoded its first MP3 frame. Wait only for actual
  // decodable data (not an arbitrary timeout), retaining incremental TTS while
  // protecting the first phoneme.
  let playbackRequested = false;
  const beginPlayback = async () => {
    if (playbackRequested || currentAudio !== audio || !audioPlaying) return;
    playbackRequested = true;
    if (firstSegmentAfterIdle) await warmAudioOutput();
    if (currentAudio !== audio || !audioPlaying) return;
    audio.play().then(() => {
    if (currentAudio !== audio || !audioPlaying) return;
    markAssistantPlaybackStarted(`role=${item.role || "answer"} remaining=${audioQueue.length} ready=${audio.readyState}`);
    }).catch(() => {
      if (currentAudio !== audio) return;
      if (item.kind === "stream" && !item.ended) {
        markStreamAudioFailed(item, "play_rejected");
        return;
      }
      sendJson({ type: "client_event", event: "audio_play_blocked", detail: "WKWebView play() rejected" });
      logLine("err", t("playback_blocked"));
      stopAudio();
    });
  };
  if (audio.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) beginPlayback();
  else audio.addEventListener("canplay", beginPlayback, { once: true });
}

function stopAudio() {
  const wasActive = audioPlaying || audioQueue.length > 0 || !!currentAudio;
  clearTimeout(playbackDrainTimer);
  playbackDrainTimer = null;
  const queuedAudio = audioQueue.splice(0);
  if (currentAudioItem) {
    const item = currentAudioItem;
    currentAudio = null;
    currentAudioItem = null;
    disposeAudioItem(item);
  }
  for (const item of queuedAudio) disposeAudioItem(item);
  audioPlaying = false;
  audioOutputNeedsWarmup = true;
  if (isDesktop) nativePost("assistantAudioState", { playing: false });
  playbackStartedAt = 0;
  bargeInMode = false;
  resetBargeCandidate();
  if (wasActive)
    sendJson({ type: "client_event", event: "audio_stopped", detail: "local_stop" });
  refreshUiState();
}

// Native app termination can arrive while streamed TTS, a reconnect timer, or
// a research status line is still alive.  Stop all of those synchronously so
// the transparent desktop HUD never leaves stale words/audio behind during a
// close or relaunch.
function clearForNativeAppExit() {
  appClosing = true;
  clearTimeout(nativeTranscriptStabilityTimer);
  nativeTranscriptStabilityTimer = null;
  clearTimeout(autoListenTimer);
  autoListenTimer = null;
  clearTimeout(interimTimer);
  interimTimer = null;
  clearTimeout(meetingTranscriptFlushTimer);
  meetingTranscriptFlushTimer = null;
  clearTimeout(watchVerificationTimeout);
  watchVerificationTimeout = null;
  stopAudio();
  clearResearchQueryChoice();
  if (recognition) {
    try { recognition.abort(); } catch {}
  }
  recognizing = false;
  interimEl.textContent = "";
  chatEl?.replaceChildren();
  document.body.dataset.streaming = "false";
  if (ws && ws.readyState < WebSocket.CLOSING) {
    try { ws.close(1000, "app quitting"); } catch {}
  }
}

window.merrickNativeAppClosing = clearForNativeAppExit;
window.addEventListener("pagehide", clearForNativeAppExit, { once: true });

// ---------------- speech recognition ----------------
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let recognizing = false;
let interimTimer = null;   // 稳定 900ms 的中间结果立即发送，减少等待
let debounceSent = "";
let playbackTranscriptBaseline = "";
let cleanBargeTranscriptBaseline = "";
let systemPlaybackActive = false;
let externalPlaybackGateForTurn = false;
let externalPlaybackCommandActive = false;
let externalPlaybackTranscriptBaseline = "";

function externalPlaybackCommandFromTranscript(text) {
  const current = String(text || "").replace(/\s+/g, " ").trim();
  if (!current) return "";
  const wakePrefix = /^(?:(?:hey|hello|okay|ok|please|请|麻烦|喂)[\s,，]*)*(?:merrick|梅里克|jarvis|贾维斯|chavez|jervis|jarviz|javis)(?=$|[\s,，.!?。！？:：])/i;
  return wakePrefix.test(current) ? current : "";
}

function transcriptSuffixAfterBaseline(currentText, baselineText) {
  const current = String(currentText || "").replace(/\s+/g, " ").trim();
  const baseline = String(baselineText || "").replace(/\s+/g, " ").trim();
  if (!baseline) return current;
  if (current.startsWith(baseline)) return current.slice(baseline.length).trim();
  const currentWords = current.split(" ");
  const baselineWords = baseline.split(" ");
  let common = 0;
  while (common < currentWords.length && common < baselineWords.length &&
         wordsNearlyEqual(currentWords[common].toLowerCase(), baselineWords[common].toLowerCase())) {
    common += 1;
  }
  // Speech.framework can revise a word inside its long cumulative result.
  // A substantial matching prefix still safely isolates the new user suffix.
  if (common >= Math.min(3, baselineWords.length)) {
    return currentWords.slice(common).join(" ").trim();
  }
  return "";
}

// A clean AEC edge already means that a person, not MERRICK's speaker, has
// begun talking. Speech.framework can still rewrite the beginning of its
// cumulative transcript so heavily that a positional suffix cannot be found.
// Keep only the words that were not in the interrupted answer and immediately
// start a fresh turn instead of holding every later user phrase indefinitely.
function novelTranscriptWordsAfterBaseline(currentText, baselineText) {
  const currentWords = normalizeSpeech(currentText).split(" ").filter(Boolean);
  const baselineWords = normalizeSpeech(baselineText).split(" ").filter(Boolean);
  const novel = currentWords.filter((word) => !baselineWords.some((baselineWord) =>
    wordsNearlyEqual(word, baselineWord)
  ));
  return novel.length >= 2 ? novel.join(" ") : "";
}

function recoverTranscriptAfterPlaybackStops(currentText, baselineText) {
  const current = String(currentText || "").trim();
  if (!current || systemPlaybackActive) return "";
  return transcriptSuffixAfterBaseline(current, baselineText) ||
    novelTranscriptWordsAfterBaseline(current, baselineText);
}

function looksLikeAssistantEchoText(text) {
  const candidateWords = normalizeSpeech(text).split(" ").filter(Boolean);
  const assistantWords = new Set(normalizeSpeech(activeAssistantText).split(" ").filter(Boolean));
  if (!candidateWords.length || !assistantWords.size) return false;
  const echoedWords = candidateWords.filter((word) => assistantWords.has(word)).length;
  return echoedWords / candidateWords.length >= 0.70;
}

function confirmPendingNativeCleanVoice(currentText) {
  if (!pendingNativeCleanVoiceActivity || !audioPlaying) return false;
  const candidate = transcriptSuffixAfterBaseline(
    currentText, pendingNativeCleanVoiceBaseline,
  ) || novelTranscriptWordsAfterBaseline(
    currentText, pendingNativeCleanVoiceBaseline,
  );
  if (!candidate) return false;
  const explicitInterrupt = /^(?:stop|wait|pause|cancel|quiet|hold on|停一下|停止|别说了|暂停|安静|等等)[.!?。！？]*$/i
    .test(candidate.trim());
  const candidateWords = normalizeSpeech(candidate).split(" ").filter(Boolean);
  if (!explicitInterrupt &&
      (candidateWords.length < 2 || looksLikeAssistantEchoText(candidate))) return false;
  pendingNativeCleanVoiceActivity = false;
  cleanBargeTranscriptBaseline = pendingNativeCleanVoiceBaseline;
  nativeCleanVoiceActivityConfirmed = true;
  sendJson({ type: "voice_activity", active: true, source: "native_aec" });
  sendJson({
    type: "client_event",
    event: "native_clean_voice_confirmed",
    detail: `chars=${candidate.length}`,
  });
  return true;
}

// Called by the native macOS speech recognizer. It starts uploading partial
// transcripts on the first words, before the utterance has finished.
window.merrickNativeTranscript = function (text, isFinal) {
  sendJson({ type: "client_event", event: "native_transcript", detail: `final=${isFinal} chars=${text.length}` });
  // After an actual barge-in, discard the short acoustic tail from the stopped
  // speaker. Without this gate, that residue can become a bogus new question.
  if (Date.now() < speechResumeBlockedUntil) return;
  const rawTranscript = String(text || "").trim();
  if (isDesktop && externalPlaybackGateForTurn && !audioPlaying &&
      !watchModeEnabled && !meetingModeEnabled) {
    const command = externalPlaybackCommandFromTranscript(rawTranscript);
    if (!externalPlaybackCommandActive && command) {
      externalPlaybackCommandActive = true;
    } else if (!externalPlaybackCommandActive) {
      const recovered = recoverTranscriptAfterPlaybackStops(
        rawTranscript,
        externalPlaybackTranscriptBaseline,
      );
      if (recovered) {
        externalPlaybackGateForTurn = false;
        externalPlaybackTranscriptBaseline = "";
        text = recovered;
        sendJson({
          type: "client_event",
          event: "external_playback_gate_recovered",
          detail: `chars=${recovered.length}`,
        });
        // The deterministic local recovery lets this turn proceed immediately.
        // In parallel, ask the bounded OpenClaw health layer to verify that a
        // second upstream stall is not hiding behind the voice-pipeline fault.
        sendJson({
          type: "runtime_stall",
          subsystem: "voice_pipeline",
          code: "external_playback_gate_stalled",
        });
      } else {
        externalPlaybackTranscriptBaseline = rawTranscript;
        if (isFinal) {
          sendJson({
            type: "client_event",
            event: "external_playback_transcript_blocked",
            detail: `chars=${rawTranscript.length}`,
          });
        }
        interimEl.textContent = "";
        return;
      }
    }
    if (externalPlaybackCommandActive) text = command || rawTranscript;
  }
  if (isDesktop && pendingNativeCleanVoiceActivity && audioPlaying) {
    if (confirmPendingNativeCleanVoice(rawTranscript)) return;
    // Keep advancing the echo baseline while the assistant is the only
    // audible speaker. A later real phrase is then measured only against the
    // latest speaker transcript, not the beginning of a long answer.
    pendingNativeCleanVoiceBaseline = rawTranscript;
    playbackTranscriptBaseline = rawTranscript;
    return;
  }
  if (isDesktop && audioPlaying && bargeInMode && bargeEchoCancellationActive) {
    playbackTranscriptBaseline = rawTranscript;
  }
  if (cleanBargeTranscriptBaseline) {
    const suffix = transcriptSuffixAfterBaseline(rawTranscript, cleanBargeTranscriptBaseline);
    if (!suffix) {
      const recovered = novelTranscriptWordsAfterBaseline(
        rawTranscript, cleanBargeTranscriptBaseline,
      );
      if (recovered) {
        text = recovered;
      } else return;
    } else {
      text = suffix;
    }
    if (isFinal) cleanBargeTranscriptBaseline = "";
  }
  if (watchModeEnabled && audioPlaying && watchCleanVoiceActive &&
      !watchVoiceVerificationRequested) {
    const candidateWords = normalizeSpeech(text).split(" ").filter(Boolean);
    // AEC provides the acoustic candidate; require a small novel transcript
    // before capturing a voiceprint. This prevents MERRICK's own TTS from
    // arming the Watch Mode owner gate.
    if (candidateWords.length >= 2 && !looksLikeAssistantEchoText(text)) {
      watchVoiceVerificationRequested = nativePost("beginWatchVoiceVerification");
      if (!watchVoiceVerificationRequested) return;
    }
  }
  if (meetingModeEnabled) {
    const fullTranscript = String(text || "").trim();
    // When MERRICK is speaking, preserve only AEC-confirmed human speech.
    // Otherwise his own words would be written into meeting notes or falsely
    // interpreted as a wake command.
    const trustedForMeeting = !audioPlaying || meetingCleanVoiceActive;
    const delta = consumeMeetingTranscript(fullTranscript);
    if (trustedForMeeting && delta) queueMeetingTranscript(delta, isFinal);
    const command = trustedForMeeting ? meetingCommandFromTranscript(fullTranscript) : "";
    if (!meetingCommandActive && command) {
      meetingCommandActive = true;
      meetingCommandTranscript = command;
      sendJson({ type: "client_event", event: "meeting_wake_detected", detail: "recent_wake_word" });
    } else if (meetingCommandActive && delta) {
      // Prefer the newest full reconstruction while its wake word is still in
      // the recent window; after that, append only the new suffix.
      meetingCommandTranscript = command || [meetingCommandTranscript, delta].join(" ").trim();
    } else if (!meetingCommandActive) {
      return;
    }
    text = meetingCommandTranscript;
    if (audioPlaying && !meetingCommandInterruptPending &&
        command && command.split(/\s+/).filter(Boolean).length >= 2) {
      meetingCommandInterruptPending = true;
      sendJson({ type: "meeting_command_interrupt", text: command });
      return;
    }
  }
  const heard = normalizeSpeech(text);
  const spoken = normalizeSpeech(activeAssistantText);
  if (watchModeEnabled && !watchModeOwnerVerified) {
    holdWatchModeTranscript(text, isFinal);
    return;
  }
  // On desktop, a confirmed clean-speech edge from the native AEC path is
  // routed through the backend Pipecat turn controller.  Do not run a second
  // competing transcript matcher there: it was the source of self-cancels and
  // stuck STREAMING states. Keep the browser/raw-audio matcher as fallback
  // until native AEC has actually supplied its first processed frame.
  if (audioPlaying && bargeInMode &&
      (!isDesktop || !bargeEchoCancellationActive)) {
    const spokenWords = spoken.split(" ").filter(Boolean);
    const heardWords = heard.split(" ").filter(Boolean);
    const fillerWords = new Set([
      "a", "an", "the", "and", "or", "but", "to", "of", "in", "on", "at",
      "for", "uh", "um",
    ]);
    // macOS commonly transcribes loudspeaker echo with a one-character error.
    // Treat those near-matches as echo instead of a new command.
    // Recognition results are cumulative. Judge only the newest suffix so a
    // few scattered transcription errors across a long spoken answer cannot
    // accumulate into a false interruption.
    const recentHeardWords = heardWords.slice(-14);
    const recentContentWords = recentHeardWords.filter(word => !fillerWords.has(word));
    // Require a consecutive run of new words. Scattered recognition mistakes
    // across the speaker echo must not add up to a fake replacement question.
    let novelWords = [];
    let novelRun = [];
    for (const word of recentContentWords) {
      if (spokenWords.some(spokenWord => wordsNearlyEqual(word, spokenWord))) {
        if (novelRun.length >= novelWords.length) novelWords = novelRun;
        novelRun = [];
      } else {
        novelRun.push(word);
      }
    }
    if (novelRun.length >= novelWords.length) novelWords = novelRun;
    // Measure the entire suffix as well as the longest new run.  A speaker
    // echo often has one or two mistranscribed words, but the rest of its
    // suffix still closely matches the text MERRICK is currently speaking.
    // That is materially different from someone beginning a new sentence.
    const matchedWordCount = recentContentWords.filter(word =>
      spokenWords.some(spokenWord => wordsNearlyEqual(word, spokenWord))
    ).length;
    const echoDensity = matchedWordCount / Math.max(recentContentWords.length, 1);
    const stopWords = new Set([
      "stop", "wait", "quiet", "cancel", "pause", "enough", "silence",
    ]);
    const chineseStopCommand = /(?:停一下|停止|别说了|别讲了|打断|暂停|安静|闭嘴|等等)/.test(String(text || ""));
    const stopCommand = chineseStopCommand || novelWords.some(word => stopWords.has(word)) ||
      novelWords.slice(-2).join(" ") === "hold on" ||
      novelWords.slice(-2).join(" ") === "shut up";
    const wakeCommand = novelWords.some((word) => word === "merrick" || word === "jarvis" || word === "梅里克");
    const signature = novelWords.slice(-5).join(" ");
    const now = Date.now();
    if (!signature) {
      resetBargeCandidate();
      return;
    }
    if (!bargeCandidate) {
      bargeCandidate = signature;
      bargeCandidateHits = 1;
      bargeCandidateSince = now;
      bargeCandidateGrowth = 1;
      bargeCandidateNovelCount = novelWords.length;
    } else if (signaturesOverlap(signature, bargeCandidate)) {
      bargeCandidateHits += 1;
      // Cumulative macOS partials repeat the same transcript many times. Only
      // count a candidate when genuinely new non-echo words have appeared.
      if (novelWords.length > bargeCandidateNovelCount) {
        bargeCandidateGrowth += 1;
        bargeCandidateNovelCount = novelWords.length;
      }
      // Keep the most complete accumulated recognition result.
      if (signature.length > bargeCandidate.length) bargeCandidate = signature;
    } else {
      bargeCandidate = signature;
      bargeCandidateHits = 1;
      bargeCandidateSince = now;
      bargeCandidateGrowth = 1;
      bargeCandidateNovelCount = novelWords.length;
    }
    const playbackAge = now - playbackStartedAt;
    const candidateAge = now - bargeCandidateSince;
    // The raw microphone stays stable while transcript matching rejects speaker
    // echo. Three growing content words are enough for a natural interruption;
    // explicit stop words and "Merrick …" use still faster paths.
    const recentAcousticEvidence = hasRecentBargeAudio(
      voiceLevel, recentVoiceEvidenceAt, now, isFinal ? 1800 : 650,
    );
    const independentSpeechRatio = novelWords.length / Math.max(recentContentWords.length, 1);
    // A speaker echo often has a handful of recognition differences, so do
    // not let those differences become an interrupt while most of the text
    // still matches MERRICK's own active response. A clearly independent
    // phrase still cuts in promptly.
    const echoDominated = echoDensity >= 0.62 &&
      (independentSpeechRatio < 0.45 || novelWords.length < 4);
    // The desktop host deliberately keeps a stable raw input format while
    // speaking because dynamically changing CoreAudio voice processing can
    // crash the microphone. With no hardware AEC, a mixed transcript that is
    // still substantially MERRICK's own speech must not interrupt merely from
    // a few ASR substitutions. A wholly unrelated user phrase still passes.
    const unsafeMixedEcho = !bargeEchoCancellationActive &&
      echoDensity >= 0.45 && independentSpeechRatio < 0.60;
    // A direct "stop" should remain fast, while a word accidentally heard
    // from MERRICK's own speaker needs a second recognition result.
    const confirmedStop = stopCommand && recentAcousticEvidence &&
      playbackAge >= 160 && !echoDominated &&
      ((independentSpeechRatio >= 0.50 &&
        (voiceLevel >= 0.025 || isFinal || bargeCandidateHits >= 2)) ||
        (candidateAge >= 120 && bargeCandidateHits >= 2));
    const confirmedWake = wakeCommand && recentAcousticEvidence &&
      playbackAge >= 200 && candidateAge >= 70 && !echoDominated &&
      novelWords.length >= 1 &&
      (independentSpeechRatio >= 0.50 || novelWords.length >= 3) &&
      (voiceLevel >= 0.025 || bargeCandidateHits >= 2 || isFinal);
    // Raw speaker echo is loud enough to satisfy the level threshold. When
    // voice processing is unavailable, also require the candidate to dominate
    // the recent content instead of being a tiny run of ASR mistakes inside a
    // much longer, correctly matched copy of MERRICK's answer.
    const acousticEvidence = voiceLevel >= 0.008 || recentAcousticEvidence ||
      (isFinal && novelWords.length >= 5);
    // Once the native host has supplied a live playback reference, WebRTC AEC
    // has already removed the principal self-echo path. Prefer a human's new
    // phrase here instead of holding it behind the old raw-microphone guard.
    // Two stable content words keep this from treating a lone recognition
    // glitch as a barge-in while restoring natural conversational interruption.
    const aecFastIndependentPhrase = bargeEchoCancellationActive &&
      novelWords.length >= 2 && independentSpeechRatio >= 0.45 &&
      candidateAge >= 60 && (recentAcousticEvidence || bargeCandidateHits >= 2 || isFinal);
    // Let a clearly independent two-word phrase interrupt promptly.  Other
    // phrases retain the extra stability requirement so speaker echo cannot
    // win merely because its transcription contains a small error.
    const fastIndependentPhrase = novelWords.length >= 2 &&
      independentSpeechRatio >= 0.55 && candidateAge >= 80 &&
      (voiceLevel >= 0.025 || isFinal || bargeCandidateHits >= 2);
    const stableNovelPhrase = novelWords.length >= 2 &&
      (bargeCandidateHits >= 2 || isFinal) &&
      independentSpeechRatio >= 0.42 && echoDensity < 0.62;
    const stableLoudWord = novelWords.length >= 2 &&
      independentSpeechRatio >= 0.50 && echoDensity < 0.55 &&
      voiceLevel >= 0.08 && candidateAge >= 180 && bargeCandidateHits >= 3;
    const confirmedQuestion = !echoDominated && !unsafeMixedEcho && acousticEvidence &&
      playbackAge >= 280 && candidateAge >= 80 &&
      (aecFastIndependentPhrase || fastIndependentPhrase || stableNovelPhrase || stableLoudWord);
    if (!confirmedStop && !confirmedWake && !confirmedQuestion) return;
    sendJson({
      type: "client_event", event: "barge_interrupt",
      detail: `stop=${confirmedStop} wake=${confirmedWake} aec=${bargeEchoCancellationActive} novel=${novelWords.length} ratio=${independentSpeechRatio.toFixed(2)} echo=${echoDensity.toFixed(2)} growth=${bargeCandidateGrowth} hits=${bargeCandidateHits} level=${voiceLevel.toFixed(2)} playback_ms=${playbackAge}`,
    });
    speechResumeBlockedUntil = Date.now() + 420;
    assistantEchoGuardUntil = Date.now() + 3000;
    bargeInMode = false;
    resetBargeCandidate();
    nativePost("stopListening");
    stopAudio();
    sendJson({ type: "interrupt" });
    responseComplete = true;
    committedSpeech = "";
    // Do not submit the mixed barge-in transcript. Start a clean recognizer and
    // wait for the user's complete replacement question.
    setTimeout(() => {
      if (!listeningManuallyMuted && !recognizing && !audioPlaying)
        nativePost("startListening");
    }, 460);
    return;
  }
  if (isDesktop && audioPlaying && bargeInMode && bargeEchoCancellationActive) {
    // The native AEC/Pipecat path owns every desktop interruption once its
    // reference stream is live. Speech.framework still transcribes speaker
    // playback, so never let the old text matcher cancel the answer here.
    // After the native clean-voice edge cancels playback, the continuing
    // cumulative recognizer result is forwarded as the replacement request.
    return;
  }
  if (Date.now() < assistantEchoGuardUntil && heard && spoken &&
      (spoken.includes(heard) || heard.includes(spoken))) return;
  // Speech.framework can keep one recognition task open indefinitely after a
  // person has stopped speaking.  Previously that left a growing `partial`
  // transcript continuously replacing its own speculative request, with no
  // turn ever committed.  Keep the recognizer live for natural continuation,
  // but synthesize a local endpoint after a stable quiet interval.  It enters
  // the same backend debounce path as a native final result; it does not make
  // browser or desktop actions fire earlier than their normal safeguards.
  const stableText = String(text || "").trim();
  if (nativeTranscriptStabilityTimer) {
    clearTimeout(nativeTranscriptStabilityTimer);
    nativeTranscriptStabilityTimer = null;
  }
  if (isFinal) {
    nativeTranscriptStabilityEpoch += 1;
    forwardNativeTranscript(stableText, true);
    return;
  }
  forwardNativeTranscript(stableText, false);
  if (!stableText || audioPlaying || Date.now() < speechResumeBlockedUntil) return;
  const epoch = ++nativeTranscriptStabilityEpoch;
  nativeTranscriptStabilityTimer = setTimeout(() => {
    if (epoch !== nativeTranscriptStabilityEpoch || audioPlaying || !stableText) return;
    nativeTranscriptStabilityTimer = null;
    sendJson({ type: "client_event", event: "speech_stability_endpoint", detail: `chars=${stableText.length}` });
    cleanBargeTranscriptBaseline = "";
    forwardNativeTranscript(stableText, true);
  }, 2200);
};

// Native AEC emits only clean speech that survived cancellation against the
// actual macOS speaker mix. Pipecat owns turn edges and atomically cancels the
// server's model/TTS work; this bridge intentionally does not stop playback or
// restart Speech.framework itself.
window.merrickNativeVoiceActivity = function (active) {
  if (!isDesktop) return;
  if (active) {
    // Preserve the mixed recognizer's already-heard speaker portion. After
    // Pipecat cancels playback, only its newly appended suffix is the user's
    // replacement question; forwarding the whole cumulative string caused
    // stale replies to be misrouted as GUI tasks.
    pendingNativeCleanVoiceActivity = true;
    pendingNativeCleanVoiceBaseline = playbackTranscriptBaseline;
    committedSpeech = "";
  } else {
    pendingNativeCleanVoiceActivity = false;
    pendingNativeCleanVoiceBaseline = "";
  }
  if (watchModeEnabled) {
    // The native AEC edge is only an acoustic candidate. Wait for a novel
    // transcript before native code collects a voiceprint, otherwise the
    // speaker output can verify itself.
    watchCleanVoiceActive = Boolean(active);
    if (!active && !watchVoiceVerificationRequested) {
      cleanBargeTranscriptBaseline = "";
    }
    return;
  }
  if (meetingModeEnabled) {
    meetingCleanVoiceActive = Boolean(active);
    return;
  }
  if (!active && nativeCleanVoiceActivityConfirmed) {
    nativeCleanVoiceActivityConfirmed = false;
    sendJson({ type: "voice_activity", active: false, source: "native_aec" });
  }
};
// Compatibility for an already-running native binary while an updated app is
// being installed. New native code calls merrickNativeVoiceActivity directly.
window.merrickNativeCleanBargeIn = function () {
  window.merrickNativeVoiceActivity(true);
};

function forwardNativeTranscript(text, isFinal) {
  interimEl.textContent = "";
  const segment = text.trim();
  if (!segment) return;
  const combined = [committedSpeech, segment].filter(Boolean).join(" ");
  sendJson({ type: "speech_partial", text: combined, final: Boolean(isFinal) });
  // A macOS final result now marks only the end of one acoustic segment, not
  // the end of the user's whole thought. The next recognizer task continues it.
  if (isFinal) committedSpeech = combined;
}

function consumeMeetingTranscript(text) {
  const current = String(text || "").trim();
  if (!current) return "";
  const previous = meetingLatestTranscript;
  meetingLatestTranscript = current;
  if (!previous) return current;
  if (current.startsWith(previous)) return current.slice(previous.length).trim();
  if (previous.startsWith(current)) return "";
  // macOS occasionally revises a prior word. Treat the changed portion as a
  // fresh local note rather than risking a missed spoken instruction.
  return current;
}

function emitMeetingTranscript(text) {
  const sentence = String(text || "").replace(/\s+/g, " ").trim();
  if (sentence) sendJson({ type: "meeting_transcript", text: sentence });
}

function flushMeetingTranscript(force = true) {
  clearTimeout(meetingTranscriptFlushTimer);
  meetingTranscriptFlushTimer = null;
  const pending = meetingPendingTranscript.trim();
  if (!pending) return;
  meetingPendingTranscript = "";
  if (force) emitMeetingTranscript(pending);
}

function queueMeetingTranscript(fragment, isFinal) {
  const incoming = String(fragment || "").replace(/\s+/g, " ").trim();
  if (!incoming) return;
  const pending = meetingPendingTranscript;
  // Most native callbacks are suffixes. When macOS revises a partial and
  // sends its full current reconstruction instead, replace the matching
  // pending prefix rather than persisting the same words twice.
  if (!pending) meetingPendingTranscript = incoming;
  else if (incoming.startsWith(pending)) meetingPendingTranscript = incoming;
  else if (!pending.endsWith(incoming)) meetingPendingTranscript = `${pending} ${incoming}`;

  // Persist only complete sentences. A recognizer that omits punctuation still
  // gets a bounded short paragraph, then a natural-pause flush below.
  let completed;
  while ((completed = meetingPendingTranscript.match(/^([\s\S]*?[.!?])(?:\s+|$)/))) {
    emitMeetingTranscript(completed[1]);
    meetingPendingTranscript = meetingPendingTranscript.slice(completed[0].length).trim();
  }
  if (isFinal || meetingPendingTranscript.length >= 260) {
    flushMeetingTranscript(true);
    return;
  }
  clearTimeout(meetingTranscriptFlushTimer);
  meetingTranscriptFlushTimer = setTimeout(() => {
    // A brief silence is a useful sentence boundary when on-device ASR has
    // not supplied punctuation.
    if (meetingModeEnabled) flushMeetingTranscript(true);
  }, 1250);
}

function meetingCommandFromTranscript(text) {
  const current = String(text || "").trim();
  if (!current) return "";
  // Constrain matching to the active tail. This accepts a user interruption
  // after background dialogue but does not let a name mentioned much earlier
  // in a meeting keep re-triggering later speech.
  const tailStart = Math.max(0, current.length - 280);
  const tail = current.slice(tailStart);
  const wake = /(?:\b(?:merrick|jarvis|chavez|jervis|jarviz|javis)\b|梅里克|贾维斯)/gi;
  let match;
  let lastMatch = null;
  while ((match = wake.exec(tail)) !== null) lastMatch = match;
  return lastMatch ? tail.slice(lastMatch.index).trim() : "";
}

function holdWatchModeTranscript(text, isFinal) {
  const segment = String(text || "").trim();
  if (!segment) return;
  const prior = watchModeBufferedTranscript?.text || "";
  // Speech.framework normally sends a growing cumulative phrase, but can
  // occasionally revise its final callback to a shorter fragment. Keep the
  // furthest complete phrase while local voice verification is in progress so
  // owner checking never removes the first half of a spoken request.
  let merged = segment;
  if (prior) {
    if (segment.startsWith(prior)) merged = segment;
    else if (prior.startsWith(segment)) merged = prior;
    else {
      const previousWords = prior.split(/\s+/).filter(Boolean);
      const incomingWords = segment.split(/\s+/).filter(Boolean);
      let overlap = 0;
      const maxOverlap = Math.min(previousWords.length, incomingWords.length);
      for (let size = maxOverlap; size > 0; size -= 1) {
        if (previousWords.slice(-size).join(" ").toLowerCase() ===
            incomingWords.slice(0, size).join(" ").toLowerCase()) {
          overlap = size;
          break;
        }
      }
      merged = overlap
        ? [...previousWords, ...incomingWords.slice(overlap)].join(" ")
        : segment.length >= prior.length ? segment : prior;
    }
  }
  watchModeBufferedTranscript = {
    text: merged,
    isFinal: Boolean(isFinal) || Boolean(watchModeBufferedTranscript?.isFinal),
  };
  interimEl.textContent = "VERIFYING OWNER VOICE…";
}

function flushWatchModeTranscript() {
  const buffered = watchModeBufferedTranscript;
  watchModeBufferedTranscript = null;
  if (!watchModeEnabled || !watchModeOwnerVerified || !buffered) return;
  if (audioPlaying) {
    // In watch mode an interruption is allowed only after completed owner
    // verification; television dialogue cannot cut MERRICK off.
    stopAudio();
    sendJson({ type: "interrupt" });
  }
  forwardNativeTranscript(buffered.text, buffered.isFinal);
}

function handleWatchModeIdentity(msg) {
  if (!watchModeEnabled) return;
  // Watch mode has its own full-sample owner gate. Private-memory access is
  // intentionally stricter, so do not make a valid owner wait forever just
  // because their voice is slightly different from the enrollment session.
  if (msg.watch_owner === true) {
    clearTimeout(watchVerificationTimeout);
    watchVerificationTimeout = null;
    watchModeOwnerVerified = true;
    flushWatchModeTranscript();
    return;
  }
  // Only a full sample can close the owner gate. A short clip is useful for
  // presentation, but not sufficiently robust against dialogue on speakers.
  // Give the longer retry sample a chance before dropping the held phrase.
  // The native capture remains live, so this does not restart Speech.framework
  // or remove any part of the owner's current request.
  if (msg.tier === "full_retry" && !watchModeOwnerVerified) {
    watchModeBufferedTranscript = null;
    interimEl.textContent = "";
    watchVoiceVerificationRequested = false;
    cleanBargeTranscriptBaseline = "";
    nativePost("restartListening");
  } else if (msg.tier === "full" && !watchModeOwnerVerified) {
    // Natural playback completion can end native capture before full_retry
    // fires. Clear this failed candidate instead of leaving VERIFYING OWNER
    // VOICE on screen forever; the next phrase starts a fresh check.
    clearTimeout(watchVerificationTimeout);
    watchVerificationTimeout = setTimeout(() => {
      if (!watchModeOwnerVerified) {
        watchModeBufferedTranscript = null;
        watchVoiceVerificationRequested = false;
        cleanBargeTranscriptBaseline = "";
        interimEl.textContent = "";
      }
    }, 1400);
  }
}

window.merrickNativeVoiceTurn = function (generation) {
  if (!Number.isInteger(generation) || generation < 0) return;
  if (meetingModeEnabled) flushMeetingTranscript(true);
  watchModeOwnerVerified = false;
  watchModeBufferedTranscript = null;
  watchCleanVoiceActive = false;
  watchVoiceVerificationRequested = false;
  clearTimeout(watchVerificationTimeout);
  watchVerificationTimeout = null;
  meetingLatestTranscript = "";
  meetingCommandActive = false;
  meetingCommandTranscript = "";
  meetingCleanVoiceActive = false;
  meetingCommandInterruptPending = false;
  externalPlaybackGateForTurn = systemPlaybackActive && !audioPlaying &&
    !watchModeEnabled && !meetingModeEnabled;
  externalPlaybackCommandActive = false;
  externalPlaybackTranscriptBaseline = "";
  sendJson({ type: "voice_turn", generation });
};

window.merrickNativeSystemAudioActivity = function (active) {
  systemPlaybackActive = Boolean(active);
};

window.merrickNativeVoiceSample = function (base64Wav, tier) {
  if (typeof base64Wav !== "string" || !base64Wav) return;
  if (tier !== "fast" && tier !== "full" && tier !== "full_retry") return;
  sendJson({ type: "voice_sample", data: base64Wav, tier });
};

// These callbacks originate only from the authenticated native host. The
// backend additionally permits enrollment for a short-lived management window.
window.merrickNativeVoiceprintAuthorized = function () {
  voiceprintUnlocked = true;
  voiceprintRecording = false;
  setVoiceprintStatus(conversationLanguage === "zh" ? "已解锁 · 可以录入本机声音样本。" : "UNLOCKED · Ready to record a local sample.", "ready");
  if (voiceprintUnlockBtn) voiceprintUnlockBtn.disabled = true;
  if (voiceprintEnrollBtn) voiceprintEnrollBtn.disabled = false;
  sendJson({ type: "voiceprint_management_authorized" });
};

window.merrickNativeVoiceprintAuthorizationFailed = function (message) {
  voiceprintUnlocked = false;
  voiceprintRecording = false;
  setVoiceprintStatus(`${conversationLanguage === "zh" ? "已锁定" : "LOCKED"} · ${String(message || (conversationLanguage === "zh" ? "验证未完成。" : "Authentication was not completed."))}`, "locked");
  if (voiceprintUnlockBtn) voiceprintUnlockBtn.disabled = false;
  if (voiceprintEnrollBtn) voiceprintEnrollBtn.disabled = true;
};

window.merrickNativeVoiceprintCaptureStarted = function () {
  setVoiceprintStatus(conversationLanguage === "zh" ? "录音中 · 请自然朗读四秒…" : "RECORDING · Read the phrase naturally for four seconds…", "recording");
};

window.merrickNativeVoiceprintSample = function (base64Wav) {
  if (typeof base64Wav !== "string" || !base64Wav) {
    window.merrickNativeVoiceprintCaptureFailed("The recording was empty. Please try again.");
    return;
  }
  setVoiceprintStatus(conversationLanguage === "zh" ? "正在本机处理 · 创建声纹向量…" : "PROCESSING LOCALLY · Creating voice vector…", "pending");
  sendJson({ type: "voiceprint_enroll", data: base64Wav });
};

window.merrickNativeVoiceprintCaptureFailed = function (message) {
  voiceprintRecording = false;
  setVoiceprintStatus(`${conversationLanguage === "zh" ? "就绪" : "READY"} · ${String(message || (conversationLanguage === "zh" ? "请重试。" : "Please try again."))}`, "error");
  if (voiceprintEnrollBtn) voiceprintEnrollBtn.disabled = !voiceprintUnlocked;
};

window.merrickNativeMemoryExportStatus = function (message, state) {
  if (!memoryExportStatus) return;
  memoryExportStatus.textContent = String(message || (conversationLanguage === "zh" ? "记忆导出未完成。" : "Memory export was not completed."));
  memoryExportStatus.dataset.state = typeof state === "string" ? state : "";
  if (memoryExportBtn) memoryExportBtn.disabled = state === "pending";
};

window.merrickNativeWorkspaceOpenFailed = function (message) {
  logLine("err", `${conversationLanguage === "zh" ? "无法打开工作区" : "Unable to open Workspace"}: ${String(message || (conversationLanguage === "zh" ? "未知错误" : "unknown error"))}`);
};

window.merrickNativeOpenClawDashboardStatus = function (ok, message) {
  if (openOpenClawDashboardBtn) openOpenClawDashboardBtn.disabled = false;
  if (!openClawDashboardStatus) return;
  openClawDashboardStatus.textContent = ok
    ? t("openclaw_dashboard_opened")
    : String(message || t("openclaw_dashboard_unavailable"));
  openClawDashboardStatus.dataset.state = ok ? "ready" : "error";
};

function normalizeSpeech(text) {
  // Keep CJK ideographs as individual comparison tokens. The former
  // English-only normalizer discarded Mandarin completely, leaving Chinese
  // barge-in with no candidate words despite a live microphone.
  return ((text || "").toLowerCase().match(/[a-z0-9]+|[\u3400-\u9fff]/g) || []).join(" ");
}

function hasRecentBargeAudio(level, lastEvidenceAt, now, retentionMs = 650) {
  return level >= 0.012 ||
    (lastEvidenceAt > 0 && now >= lastEvidenceAt && now - lastEvidenceAt <= retentionMs);
}

function signaturesOverlap(a, b) {
  return a === b || a.startsWith(b + " ") || b.startsWith(a + " ") ||
    a.endsWith(" " + b) || b.endsWith(" " + a);
}

function wordsNearlyEqual(a, b) {
  if (a === b) return true;
  if (a.length < 4 || b.length < 4 || Math.abs(a.length - b.length) > 1) return false;
  let i = 0, j = 0, edits = 0;
  while (i < a.length && j < b.length) {
    if (a[i] === b[j]) { i += 1; j += 1; continue; }
    if (++edits > 1) return false;
    if (a.length > b.length) i += 1;
    else if (b.length > a.length) j += 1;
    else { i += 1; j += 1; }
  }
  if (i < a.length || j < b.length) edits += 1;
  return edits <= 1;
}
window.merrickNativeSpeechState = function (
  active, requestedRestartDelay = 280, echoCancellationActive = false,
) {
  recognizing = active;
  bargeEchoCancellationActive = Boolean(active && echoCancellationActive);
  micBtn.classList.toggle("recording", active);
  refreshMicControl();
  refreshUiState();
  if (!active && isDesktop && !listeningManuallyMuted && audioPlaying && bargeInMode) {
    // A recognition task can naturally finalise while a long audio segment is
    // still playing. Start a fresh task and never carry a stale echo candidate
    // across recognizer generations.
    resetBargeCandidate();
    const restartDelay = Math.max(
      180, Number(requestedRestartDelay) || 0,
      speechResumeBlockedUntil - Date.now() + 50,
    );
    setTimeout(() => {
      if (!recognizing && audioPlaying && bargeInMode)
        nativePost("startListening", { echoCancel: false });
    }, restartDelay);
    return;
  }
  if (!active && isDesktop && !listeningManuallyMuted && autoToggle.checked && !audioPlaying && serverState === "idle") {
    // Native recognition tasks naturally end after a final phrase and may also
    // be ended by macOS. Recreate the raw, sensitive listener promptly; waiting
    // more than a second here made an immediate follow-up sentence disappear.
    maybeAutoListen(Math.max(280, Number(requestedRestartDelay) || 0));
  }
};
window.merrickNativeError = function (message) {
  logLine("err", message);
  interimEl.textContent = message;
};
window.merrickNativeNotificationStatus = function (id, ok, message) {
  const safeId = typeof id === "string" && /^[a-z0-9][a-z0-9._:-]{0,95}$/i.test(id) ? id : "";
  if (!safeId) return;
  sendJson({ type: "local_notification_result", id: safeId, ok: ok === true });
  if (ok !== true) {
    const nativeDenied = message === "Enable notifications for MERRICK in System Settings.";
    const safeMessage = nativeDenied ? oc("notificationDenied") :
      (typeof message === "string" && message.length <= 300 ? message : oc("notificationDenied"));
    setOrganizerStatus(safeMessage, "error");
    logLine("err", safeMessage);
  }
};
window.merrickNativeScreenCaptureResult = function (requestId, data, mime, error) {
  if (!/^[0-9a-f]{32}$/.test(requestId || "")) return;
  const safeData = typeof data === "string" ? data : "";
  const safeMime = mime === "image/jpeg" || mime === "image/png" ? mime : "";
  const safeError = typeof error === "string" ? error.slice(0, 600) : "";
  // A 4 MB image expands to about 5.34 MB in base64. Refuse anything larger
  // before it reaches the local backend, and never persist the image in JS.
  if (safeData.length > 5_400_000) {
    sendJson({
      type: "screen_capture_result",
      request_id: requestId,
      data: "",
      mime: "",
      error: "The one-time screen image exceeded the private 4 MB limit.",
    });
    return;
  }
  sendJson({
    type: "screen_capture_result",
    request_id: requestId,
    data: safeData,
    mime: safeMime,
    error: safeError,
  });
};
window.merrickNativeActionResult = function (requestId, ok, result, error) {
  if (!/^[0-9a-f]{32}$/.test(requestId || "") || requestId !== nativeActionInFlight) return;
  nativeActionInFlight = null;
  const validResult = ok === true && hasExactKeys(result, ["status", "detail"]) &&
    (result.status === "opened" || result.status === "focused" || result.status === "completed") &&
    typeof result.detail === "string" && result.detail.length <= 400 &&
    !/[\u0000-\u001f\u007f]/.test(result.detail);
  const safeError = typeof error === "string" && error.length > 0 && error.length <= 400 &&
    !/[\u0000-\u001f\u007f]/.test(error) ? error : "The native desktop action failed.";
  sendJson({
    type: "native_action_result",
    request_id: requestId,
    ok: validResult,
    result: validResult ? { status: result.status, detail: result.detail } : null,
    error: validResult ? "" : safeError,
  });
};
window.merrickNativeAudioLevel = function (level) {
  const amount = Math.max(0, Math.min(1, Number(level) || 0));
  voiceLevel = amount;
  if (amount >= 0.012) recentVoiceEvidenceAt = Date.now();
  reactor.style.setProperty("--voice-scale", (1 + amount * 0.065).toFixed(3));
  reactor.classList.toggle("hearing", amount > 0.045);
};
window.merrickNativeTranscriptDetected = function () {
  reactor.classList.remove("transcript-hit");
  void reactor.offsetWidth;
  reactor.classList.add("transcript-hit");
  shockwaves.push(performance.now());
  if (shockwaves.length > 4) shockwaves.shift();
  setTimeout(() => reactor.classList.remove("transcript-hit"), 420);
};

if (SR) {
  recognition = new SR();
  recognition.lang = "en-GB";
  recognition.continuous = false;
  recognition.interimResults = true;

  recognition.onstart = () => {
    recognizing = true;
    debounceSent = "";
    micBtn.classList.add("recording");
    refreshUiState();
  };
  recognition.onend = () => {
    recognizing = false;
    clearTimeout(interimTimer);
    micBtn.classList.remove("recording");
    interimEl.textContent = "";
    refreshUiState();
  };
  recognition.onerror = (e) => {
    if (e.error === "not-allowed") logLine("err", conversationLanguage === "zh" ? "麦克风权限被拒绝" : "Microphone permission was denied.");
    else if (e.error !== "aborted" && e.error !== "no-speech")
      logLine("err", (conversationLanguage === "zh" ? "语音识别错误: " : "Speech recognition error: ") + e.error);
  };
  recognition.onresult = (e) => {
    let finalText = "", interim = "";
    for (const res of e.results) {
      if (res.isFinal) finalText += res[0].transcript;
      else interim += res[0].transcript;
    }
    interimEl.textContent = "";

    if (finalText) {
      clearTimeout(interimTimer);
      interimEl.textContent = "";
      if (finalText.trim() !== debounceSent) submitText(finalText, false);
      return;
    }

    // 快速触发：中间结果停顿 900ms 视为说完，立即上传
    clearTimeout(interimTimer);
    const snapshot = interim.trim();
    if (snapshot) {
      sendJson({ type: "speech_partial", text: snapshot });
      interimTimer = setTimeout(() => {
        debounceSent = snapshot;
        try { recognition.abort(); } catch {}
        interimEl.textContent = "";
        submitText(snapshot, false);
      }, 900);
    }
  };
} else {
  if (!isDesktop) {
    micBtn.disabled = true;
    micBtn.title = conversationLanguage === "zh" ? "此浏览器不支持语音识别，请使用 Chrome 或 Edge" : "This browser does not support speech recognition; use Chrome or Edge.";
  }
}

function startListening() {
  if (listeningManuallyMuted || (!recognition && !isDesktop) || recognizing) return;
  // 插话即打断：MERRICK在说或在想时开麦，先让它停下
  if (audioPlaying || serverState === "thinking" || serverState === "acting") {
    stopAudio();
    sendJson({ type: "interrupt" });
  }
  if (isDesktop && nativePost("startListening")) return;
  try { recognition.start(); } catch { /* already started */ }
}

function stopListening() {
  if (isDesktop && nativePost("stopListening")) return;
  if (recognition && recognizing) recognition.stop();
}

function maybeAutoListen(delay = 280) {
  // Resume the raw microphone promptly after speech. Use one replaceable timer
  // because "done", "idle", queue drain and native stop can arrive in different
  // orders for the same turn.
  clearTimeout(autoListenTimer);
  autoListenTimer = null;
  if (listeningManuallyMuted || !autoToggle.checked || !responseComplete) return;
  const restartDelay = Math.max(delay, speechResumeBlockedUntil - Date.now() + 50);
  autoListenTimer = setTimeout(() => {
    autoListenTimer = null;
    if (listeningManuallyMuted || !autoToggle.checked || !responseComplete || audioPlaying || recognizing || serverState !== "idle")
      return;
    if (isDesktop) nativePost("startListening", { echoCancel: false });
    else startListening();
  }, restartDelay);
}

// ---------------- UI events ----------------
micBtn.addEventListener("click", () => {
  if (recognizing) {
    listeningManuallyMuted = true;
    clearTimeout(autoListenTimer);
    autoListenTimer = null;
    stopListening();
  } else {
    listeningManuallyMuted = false;
    refreshMicControl();
    startListening();
  }
  refreshMicControl();
});

sendBtn.addEventListener("click", () => {
  submitText(textInput.value);
  textInput.value = "";
});

textInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    submitText(textInput.value);
    textInput.value = "";
  }
});

const SPACE_SHORTCUT_INTERACTIVE_SELECTOR = [
  "input",
  "textarea",
  "select",
  "option",
  "button",
  "a[href]",
  "summary",
  '[contenteditable]:not([contenteditable="false"])',
  '[role="textbox"]',
  '[role="button"]',
  '[role="option"]',
  '[role="tab"]',
  '[role="switch"]',
  '[role="checkbox"]',
  '[role="radio"]',
  '[role="slider"]',
  '[tabindex]:not([tabindex="-1"])',
].join(", ");

function shouldStartListeningFromSpace(event) {
  if (
    event.code !== "Space" ||
    event.defaultPrevented ||
    event.repeat ||
    event.isComposing ||
    event.metaKey ||
    event.ctrlKey ||
    event.altKey
  ) return false;

  const target = event.target instanceof Element ? event.target : document.activeElement;
  return !(target instanceof Element && target.closest(SPACE_SHORTCUT_INTERACTIVE_SELECTOR));
}

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && newspaperFocusActive) {
    event.preventDefault();
    event.stopImmediatePropagation();
    exitNewspaperFocus();
    return;
  }
  if (isDesktop && event.code === "KeyF" && event.ctrlKey && event.metaKey && !event.altKey) {
    event.preventDefault();
    requestNativeFullscreen("toggle");
    return;
  }
  if (shouldStartListeningFromSpace(event) && !recognizing) {
    event.preventDefault();
    listeningManuallyMuted = false;
    refreshMicControl();
    startListening();
  }
});

let desktopDrag = null;
let suppressReactorClickUntil = 0;

function focusOrganizerEditableFromPointer(event) {
  if (!(event.target instanceof Element)) return;
  const editable = event.target.closest(
    'input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [contenteditable]:not([contenteditable="false"])'
  );
  if (!editable || !organizerPanel?.contains(editable)) return;

  // Keep a form click entirely inside the dashboard. This prevents both the
  // HUD drag listener and AppKit's borderless-window behavior from treating a
  // click intended for a WKWebView editor as window movement.
  desktopDrag = null;
  event.stopPropagation();
  if (document.activeElement !== editable) editable.focus({ preventScroll: true });
}

organizerPanel?.addEventListener("pointerdown", focusOrganizerEditableFromPointer);

function isDesktopDragTarget(target) {
  if (!isDesktop || !(target instanceof Element)) return false;
  if (target.closest("button, input, textarea, select, a, label, .panel, .hud-footer"))
    return false;
  return !!target.closest(".reactor, .reactor-zone, .hud-main, .hud-header, [data-drag-region]");
}

function finishDesktopDrag(event) {
  if (!desktopDrag || (event?.pointerId !== undefined && event.pointerId !== desktopDrag.pointerId))
    return;
  if (desktopDrag.moved) {
    suppressReactorClickUntil = Date.now() + 350;
    nativePost("endWindowDrag");
    event?.preventDefault?.();
  }
  document.body.classList.remove("window-dragging");
  desktopDrag = null;
}

if (isDesktop) {
  document.addEventListener("pointerdown", (event) => {
    if (event.button !== 0 || !isDesktopDragTarget(event.target)) return;
    desktopDrag = {
      pointerId: event.pointerId,
      startX: event.screenX,
      startY: event.screenY,
      lastX: event.screenX,
      lastY: event.screenY,
      moved: false,
    };
    event.target.setPointerCapture?.(event.pointerId);
  });

  document.addEventListener("pointermove", (event) => {
    if (!desktopDrag || event.pointerId !== desktopDrag.pointerId) return;
    const totalX = event.screenX - desktopDrag.startX;
    const totalY = event.screenY - desktopDrag.startY;
    if (!desktopDrag.moved && Math.hypot(totalX, totalY) < 5) return;
    const dx = event.screenX - desktopDrag.lastX;
    const dy = event.screenY - desktopDrag.lastY;
    desktopDrag.lastX = event.screenX;
    desktopDrag.lastY = event.screenY;
    desktopDrag.moved = true;
    document.body.classList.add("window-dragging");
    nativePost("moveWindow", { dx, dy });
    event.preventDefault();
  }, { passive: false });

  document.addEventListener("pointerup", finishDesktopDrag);
  document.addEventListener("pointercancel", finishDesktopDrag);
  window.addEventListener("blur", () => finishDesktopDrag());
}

reactor.addEventListener("click", () => {
  if (Date.now() < suppressReactorClickUntil) return;
  if (isDesktop && !recognizing && !audioPlaying &&
      serverState !== "thinking" && serverState !== "acting") {
    listeningManuallyMuted = false;
    refreshMicControl();
    startListening();
    return;
  }
  stopAudio();
  sendJson({ type: "interrupt" });
  if (isDesktop && !listeningManuallyMuted) setTimeout(startListening, 120);
  logLine("info", t("interrupt_sent"));
});

$("expand-btn")?.addEventListener("click", () => {
  document.body.classList.toggle("expanded");
  if (!document.body.classList.contains("expanded")) {
    closeSetupPanel();
    setOrganizerVisible(false);
    window.MerrickPlanMode?.close();
  }
  nativePost("resize", { expanded: document.body.classList.contains("expanded") });
});
function setSetupPanelVisible(visible) {
  if (!setupPanel) return;
  setupPanel.hidden = !visible;
  setupPanel.classList.toggle("visible", visible);
}

function closeSetupPanel() {
  setSetupPanelVisible(false);
}

function setCapabilitiesVisible(visible) {
  if (!capabilitiesPanel) return;
  capabilitiesPanel.hidden = !visible;
  if (!visible) closeCapabilityReview();
  if (visible) requestCapabilityInventory();
}

function closeCapabilityReview() {
  pendingCapabilityReview = null;
  if (capabilityReview) capabilityReview.hidden = true;
  if (capabilityReviewConfirm) capabilityReviewConfirm.disabled = false;
  capabilityBusy = false;
  renderCapabilityInventory();
}

function renderCapabilityReview(review) {
  if (!capabilityReview || !review || typeof review.operation_id !== "string") return;
  // A plugin install can produce a second OpenClaw capability review after the
  // identity review. Re-enable the same confirmation control for every stage;
  // the previous stage deliberately disables it while its request is pending.
  capabilityBusy = false;
  capabilityReviewConfirm.disabled = false;
  pendingCapabilityReview = review;
  const action = typeof review.action === "string"
    ? review.action : (review.enabled === true ? "enable" : "disable");
  const titleKey = review.stage === "policy" ? "capability_review_policy"
    : review.stage === "capabilities" ? "capability_review_capabilities"
      : `capability_review_${action}`;
  capabilityReviewTitle.textContent = tf(titleKey, { name: review.name || review.id });
  capabilityReviewDescription.textContent = review.description || "";
  const sourceInfo = review.source_info && typeof review.source_info === "object" ? review.source_info : null;
  const sourceParts = [
    review.trust || review.channel || review.source || "OpenClaw",
    sourceInfo?.package_name || sourceInfo?.spec || review.identity || "",
    sourceInfo?.integrity ? `${sourceInfo.integrity_kind || "integrity"}: ${sourceInfo.integrity}` : "",
    review.version ? `v${review.version}` : "",
  ].filter(Boolean);
  capabilityReviewTrust.textContent = tf("capability_review_trust", { trust: sourceParts.join(" · ") });
  capabilityReviewSurfaces.replaceChildren();
  const surfaces = Array.isArray(review.surfaces) ? review.surfaces : [];
  const grants = Array.isArray(review.grants) ? review.grants : [];
  const findings = Array.isArray(review.findings) ? review.findings : [];
  if (!surfaces.length && !grants.length && !findings.length) {
    const empty = document.createElement("p"); empty.textContent = t("capability_review_none");
    capabilityReviewSurfaces.append(empty);
  } else {
    for (const surface of surfaces) {
      const row = document.createElement("div"); row.className = "capability-review-surface";
      const title = document.createElement("strong");
      title.textContent = `${surface.label || surface.key} · ${Number(surface.count) || 0}`;
      const detail = document.createElement("span");
      detail.textContent = Array.isArray(surface.items) ? surface.items.join(" · ") : "";
      row.append(title, detail); capabilityReviewSurfaces.append(row);
    }
    for (const grant of grants) {
      const row = document.createElement("div"); row.className = "capability-review-surface";
      const title = document.createElement("strong");
      title.textContent = grant.label || grant.key || "Permission";
      const detail = document.createElement("span");
      detail.textContent = grant.effective
        ? (conversationLanguage === "zh" ? "允许" : "ALLOWED")
        : (conversationLanguage === "zh" ? "关闭" : "OFF");
      row.dataset.state = grant.effective ? "warning" : "safe";
      row.append(title, detail); capabilityReviewSurfaces.append(row);
    }
    for (const finding of findings) {
      const row = document.createElement("div"); row.className = "capability-review-surface";
      row.dataset.state = finding.severity || "warning";
      const title = document.createElement("strong");
      title.textContent = String(finding.severity || "warning").toUpperCase();
      const detail = document.createElement("span");
      detail.textContent = `${finding.message || ""}${finding.file ? ` · ${finding.file}${finding.line ? `:${finding.line}` : ""}` : ""}`;
      row.append(title, detail); capabilityReviewSurfaces.append(row);
    }
  }
  const requirements = Array.isArray(review.requirements) ? review.requirements : [];
  capabilityReviewRequirements.hidden = !requirements.length;
  capabilityReviewRequirements.textContent = requirements.length
    ? tf("capability_review_requirements", { items: requirements.join(" · ") }) : "";
  const confirmKey = review.stage === "policy" ? "capability_review_confirm_continue"
    : `capability_review_confirm_${action}`;
  capabilityReviewConfirm.textContent = t(confirmKey);
  capabilityReviewConfirm.dataset.action = action;
  capabilityReview.hidden = false;
  capabilityReviewConfirm.focus();
}

function setCapabilityStatus(text, state = "") {
  if (!capabilitiesStatus) return;
  capabilitiesStatus.textContent = text;
  capabilitiesStatus.dataset.state = state;
}

function updateCapabilitySummary(summary) {
  if (!capabilitiesSummary || !summary) return;
  const plugins = Number.isInteger(summary.plugins_enabled) ? summary.plugins_enabled : 0;
  const pluginsTotal = Number.isInteger(summary.plugins_total) ? summary.plugins_total : 0;
  const skills = Number.isInteger(summary.skills_ready) ? summary.skills_ready : 0;
  const skillsTotal = Number.isInteger(summary.skills_total) ? summary.skills_total : 0;
  capabilitiesSummary.textContent = conversationLanguage === "zh"
    ? `${plugins}/${pluginsTotal} 个插件已启用 · ${skills}/${skillsTotal} 个技能已在本机就绪`
    : `${plugins}/${pluginsTotal} plugins active · ${skills}/${skillsTotal} skills ready locally`;
  capabilitiesSummary.dataset.state = "ready";
}

function requestCapabilityInventory() {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    setCapabilityStatus(conversationLanguage === "zh" ? "MERRICK 正在重连；能力清单会自动刷新。" : "MERRICK is reconnecting; capability inventory will refresh automatically.", "pending");
    return;
  }
  setCapabilityStatus(conversationLanguage === "zh" ? "正在读取本机 OpenClaw 能力清单…" : "Reading the local OpenClaw inventory…", "pending");
  sendJson({ type: "capabilities_inventory" });
  requestPluginCatalog(capabilitiesSearch?.value || "");
}

function requestPluginCatalog(query = "") {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  if (capabilityTab === "discover") setCapabilityStatus(t("catalog_loading"), "pending");
  sendJson({ type: "capabilities_catalog", query: String(query).trim().slice(0, 120) });
}

function capabilityMatches(item, query) {
  if (!query) return true;
  const haystack = [item.id, item.name, item.description, item.origin, item.source,
    ...Object.values(item.lifecycle || {}),
    ...(item.execution_profile?.candidate_domains || []),
    ...(item.surfaces || []), ...(item.requirements || [])].join(" ").toLocaleLowerCase();
  return haystack.includes(query);
}

function capabilityLifecycleLabel(stage, value) {
  const labels = {
    readiness: {
      ready: "lifecycle_ready",
      disabled: "lifecycle_disabled",
      dependency_missing: "lifecycle_dependency_missing",
      unhealthy: "lifecycle_unhealthy",
    },
    review: { core: "lifecycle_core", unreviewed: "lifecycle_unreviewed" },
    connection: { not_assessed: "lifecycle_not_assessed_connection" },
    authorization: {
      policy_managed: "lifecycle_policy_managed",
      not_assessed: "lifecycle_not_assessed_authorization",
    },
  };
  const key = labels[stage]?.[value];
  return key ? t(key) : "";
}

function renderCapabilityLifecycle(item) {
  const lifecycle = item.lifecycle && typeof item.lifecycle === "object" ? item.lifecycle : null;
  if (!lifecycle) return null;
  const row = document.createElement("div");
  row.className = "capability-lifecycle";
  for (const stage of ["readiness", "review", "connection", "authorization"]) {
    const value = typeof lifecycle[stage] === "string" ? lifecycle[stage] : "";
    const label = capabilityLifecycleLabel(stage, value);
    if (!label) continue;
    const token = document.createElement("span");
    token.textContent = label;
    token.dataset.state = /^[a-z_]+$/.test(value) ? value : "unknown";
    row.append(token);
  }
  return row.childElementCount ? row : null;
}

function renderCapabilityRisk(item) {
  const profile = item.execution_profile && typeof item.execution_profile === "object"
    ? item.execution_profile : null;
  const domains = Array.isArray(profile?.candidate_domains)
    ? profile.candidate_domains.filter((value) => /^[a-z_]+$/.test(value)).slice(0, 4)
    : [];
  const risk = typeof profile?.max_risk === "string" && /^R[0-3]$/.test(profile.max_risk)
    ? profile.max_risk : "";
  if (!domains.length || !risk) return null;
  const row = document.createElement("small");
  row.className = "capability-risk";
  const labels = domains.map((domain) => t(`domain_${domain}`, domain));
  row.textContent = `${t("capability_candidate")}: ${labels.join(" · ")} · ${t("risk_ceiling")} ${risk}`;
  row.dataset.risk = risk;
  return row;
}

function pluginOperationButton(item, action, labelKey, danger = false) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = `capability-toggle${danger ? " danger" : ""}`;
  button.textContent = t(labelKey);
  button.dataset.pluginOperation = action;
  button.dataset.pluginSource = item.install_source || (action === "uninstall" ? "" : "clawhub");
  button.dataset.pluginIdentity = action === "uninstall"
    ? item.plugin_id : (item.install_identity || item.plugin_id);
  button.disabled = capabilityBusy || !capabilityCatalogMutationAllowed || !button.dataset.pluginIdentity;
  button.setAttribute("aria-label", `${button.textContent} ${item.name}`);
  return button;
}

function renderPluginCatalog() {
  const query = (capabilitiesSearch?.value || "").trim().toLocaleLowerCase();
  const items = capabilityCatalog.filter((item) => {
    if (!query) return true;
    return [item.name, item.description, item.plugin_id, item.install_identity, item.channel]
      .join(" ").toLocaleLowerCase().includes(query);
  });
  capabilityList.replaceChildren();
  if (catalogCount) catalogCount.textContent = String(capabilityCatalog.length || 0);
  if (!items.length) {
    const empty = document.createElement("p"); empty.className = "capability-empty";
    empty.textContent = query.length < 2 ? t("catalog_search_hint") : t("no_capability_matches");
    capabilityList.append(empty); return;
  }
  for (const item of items) {
    const card = document.createElement("article");
    card.className = "capability-card capability-catalog-card";
    const head = document.createElement("div"); head.className = "capability-card-head";
    const label = document.createElement("div");
    const name = document.createElement("strong"); name.textContent = `◇ ${item.name}`;
    const meta = document.createElement("span");
    const provenance = item.official ? t("official")
      : item.installed && item.origin === "global" ? t("local") : t("community");
    meta.textContent = [provenance, item.version ? `v${item.version}` : "", item.verification || "",
      item.downloads ? `${item.downloads.toLocaleString()} ↓` : ""].filter(Boolean).join(" · ");
    label.append(name, meta);
    const actions = document.createElement("div"); actions.className = "capability-card-actions";
    if (item.installed) {
      const installed = document.createElement("span"); installed.className = "capability-installed";
      installed.textContent = t("installed"); actions.append(installed);
      if (item.install_identity) actions.append(pluginOperationButton(item, "upgrade", "update"));
    } else if (item.install_identity) {
      actions.append(pluginOperationButton(item, "install", "install"));
    }
    head.append(label, actions);
    const description = document.createElement("p"); description.textContent = item.description || item.install_identity;
    card.append(head, description);
    const tags = document.createElement("div"); tags.className = "capability-tags";
    for (const tag of [item.category, item.channel, item.install_source].filter(Boolean)) {
      const token = document.createElement("span"); token.textContent = tag; tags.append(token);
    }
    if (tags.childElementCount) card.append(tags);
    capabilityList.append(card);
  }
}

function renderCapabilityInventory() {
  if (!capabilityList) return;
  if (pluginCount) pluginCount.textContent = String(capabilityInventory.plugins.length || 0);
  if (skillCount) skillCount.textContent = String(capabilityInventory.skills.length || 0);
  if (capabilityTab === "discover") {
    renderPluginCatalog();
    return;
  }
  const query = (capabilitiesSearch?.value || "").trim().toLocaleLowerCase();
  const items = (capabilityInventory[capabilityTab] || []).filter((item) => capabilityMatches(item, query));
  capabilityList.replaceChildren();
  if (!items.length) {
    const empty = document.createElement("p"); empty.className = "capability-empty";
    empty.textContent = query ? t("no_capability_matches") : t("no_capabilities");
    capabilityList.append(empty); return;
  }
  for (const item of items) {
    const card = document.createElement("article"); card.className = "capability-card";
    const head = document.createElement("div"); head.className = "capability-card-head";
    const label = document.createElement("div");
    const name = document.createElement("strong"); name.textContent = `${item.emoji || "◈"} ${item.name}`;
    const meta = document.createElement("span");
    const status = capabilityTab === "plugins"
      ? `${item.enabled ? t("active") : t("inactive")} · ${item.origin || "local"}${item.version ? ` · ${item.version}` : ""}`
      : `${item.eligible ? t("ready") : t("setup_needed")} · ${item.source || "local"}`;
    meta.textContent = status;
    label.append(name, meta);
    const actions = document.createElement("div"); actions.className = "capability-card-actions";
    const control = document.createElement("button"); control.type = "button"; control.className = "capability-toggle";
    const enabled = item.enabled === true;
    const coreProtected = item.locked === true && enabled;
    control.textContent = coreProtected ? t("core_locked") : (enabled ? t("disable") : t("enable"));
    control.dataset.enabled = String(enabled);
    control.dataset.capabilityAction = "review";
    control.dataset.capabilityKind = capabilityTab === "plugins" ? "plugin" : "skill";
    control.dataset.capabilityId = item.id;
    control.disabled = capabilityBusy || coreProtected;
    control.setAttribute("aria-label", `${control.textContent} ${item.name}`);
    actions.append(control);
    if (capabilityTab === "plugins" && !item.locked) {
      const managed = capabilityCatalog.find((entry) => entry.plugin_id === item.id && entry.installed);
      if (managed?.install_identity) actions.append(pluginOperationButton(managed, "upgrade", "update"));
      if (managed?.removable) actions.append(pluginOperationButton(managed, "uninstall", "remove", true));
    }
    head.append(label, actions);
    const description = document.createElement("p"); description.textContent = item.description;
    card.append(head, description);
    const lifecycle = renderCapabilityLifecycle(item);
    if (lifecycle) card.append(lifecycle);
    const risk = renderCapabilityRisk(item);
    if (risk) card.append(risk);
    const tags = capabilityTab === "plugins" ? item.surfaces : item.requirements;
    if (Array.isArray(tags) && tags.length) {
      const tagRow = document.createElement("div"); tagRow.className = "capability-tags";
      for (const tag of tags) { const token = document.createElement("span"); token.textContent = tag; tagRow.append(token); }
      card.append(tagRow);
    }
    if (capabilityTab === "skills" && !item.eligible && Array.isArray(item.requirements) && item.requirements.length) {
      const needs = document.createElement("small"); needs.className = "capability-needs";
      needs.textContent = `${t("requires")}：${item.requirements.join(", ")}`; card.append(needs);
    }
    capabilityList.append(card);
  }
}

function renderHarnessStatus(harness) {
  if (!harnessModeStatus) return;
  const state = typeof harness?.status === "string" ? harness.status : "disabled";
  harnessModeStatus.dataset.state = state;
  if (state === "ready") {
    const generation = Number.isInteger(harness.active_generation) ? harness.active_generation : 0;
    harnessModeStatus.textContent = conversationLanguage === "zh"
      ? `HARNESS LAB 已就绪 · 私有插件库代际 ${generation} · 生产激活仍锁定`
      : `HARNESS LAB READY · Private vault generation ${generation} · Production activation locked`;
  } else if (state === "unavailable") {
    harnessModeStatus.textContent = conversationLanguage === "zh"
      ? "HARNESS LAB 不可用 · 插件执行保持锁定；OpenClaw 其他能力不受影响"
      : "HARNESS LAB UNAVAILABLE · Plugin execution stays locked; other OpenClaw capabilities remain available";
  } else {
    harnessModeStatus.textContent = conversationLanguage === "zh"
      ? "HARNESS LAB 尚未启用 · 不会运行用户生成代码"
      : "HARNESS LAB DISABLED · No user-generated code can run";
  }
}

function receiveCapabilityInventory(msg, notice = conversationLanguage === "zh" ? "本机能力清单已更新。" : "Local capability inventory is up to date.") {
  capabilityBusy = false;
  capabilityInventory = {
    plugins: Array.isArray(msg.plugins) ? msg.plugins : [],
    skills: Array.isArray(msg.skills) ? msg.skills : [],
    summary: msg.summary && typeof msg.summary === "object" ? msg.summary : null,
    snapshot: msg.snapshot && typeof msg.snapshot === "object" ? msg.snapshot : null,
    harness: msg.harness && typeof msg.harness === "object" ? msg.harness : null,
  };
  updateCapabilitySummary(capabilityInventory.summary);
  renderHarnessStatus(capabilityInventory.harness);
  const stale = capabilityInventory.snapshot?.stale === true;
  setCapabilityStatus(stale ? t("capability_snapshot_stale") : notice, stale ? "warning" : "ready");
  renderCapabilityInventory();
}

function receivePluginCatalog(msg) {
  capabilityCatalog = Array.isArray(msg.catalog) ? msg.catalog : [];
  capabilityCatalogMutationAllowed = msg.mutation_allowed === true;
  if (catalogCount) catalogCount.textContent = String(capabilityCatalog.length || 0);
  if (capabilityTab === "discover") {
    setCapabilityStatus(conversationLanguage === "zh"
      ? `OpenClaw 目录已更新 · ${capabilityCatalog.length} 项`
      : `OpenClaw catalog ready · ${capabilityCatalog.length} items`, "ready");
  }
  renderCapabilityInventory();
}

function renderCapabilityDiagnostics(findings) {
  if (!capabilityDiagnostics) return;
  capabilityDiagnostics.replaceChildren();
  capabilityDiagnostics.hidden = false;
  const title = document.createElement("div"); title.className = "setup-section-title"; title.textContent = t("readonly_diagnostics");
  capabilityDiagnostics.append(title);
  if (!findings.length) {
    const ok = document.createElement("p"); ok.textContent = t("no_diagnostics"); capabilityDiagnostics.append(ok); return;
  }
  for (const finding of findings) {
    const row = document.createElement("p"); row.className = "capability-diagnostic";
    row.textContent = `${String(finding.severity || "info").toUpperCase()} · ${finding.message || "OpenClaw diagnostic"}`;
    capabilityDiagnostics.append(row);
  }
}

function setOnboardingVisible(visible) {
  if (!onboardingPanel) return;
  onboardingPanel.hidden = !visible;
  onboardingPanel.classList.toggle("visible", visible);
}

function setProviderSetupStatus(text, state = "") {
  if (!providerSetupStatus) return;
  providerSetupStatus.textContent = text;
  providerSetupStatus.dataset.state = state;
}

function renderProviderForm({ preserveStatus = false, resetInputs = false } = {}) {
  const provider = PROVIDERS[selectedProvider] || PROVIDERS.codex;
  document.querySelectorAll(".provider-choice").forEach((button) => {
    button.classList.toggle("selected", button.dataset.provider === selectedProvider);
  });
  if (providerDetail) providerDetail.textContent = conversationLanguage === "zh"
    ? ({
      codex: "使用你的 ChatGPT / Codex 订阅，但登录只保存给 MERRICK 的本机模型层。它不会读取、覆盖或修改这台 Mac 的 Codex / OpenClaw 登录。若需要完成登录，系统会打开浏览器。",
      "claude-code": "使用已安装的 Claude Code CLI 及其本机登录。MERRICK 不会取得你的 Claude 密码或订阅令牌。",
      openai: "连接付费的 OpenAI Platform API 密钥；这与 ChatGPT 订阅不同。",
      anthropic: "连接 Anthropic Console API 密钥，直接使用 Claude API。",
      gemini: "连接 Google AI Studio 的 Gemini API 密钥。",
      kimi: "连接 Moonshot 开放平台 API 密钥。Kimi Coding 需要不同端点，请使用“自定义”。",
      deepseek: "连接 DeepSeek API 密钥；MERRICK 使用其兼容 OpenAI 的聊天接口。",
      custom: "用于兼容 OpenAI 的 API。请输入服务商提供的 HTTPS 基础 URL 与模型 ID。",
    }[selectedProvider] || provider.detail)
    : provider.detail;
  if (resetInputs) {
    if (providerModelInput) providerModelInput.value = provider.model;
    if (providerBaseUrlInput) providerBaseUrlInput.value = "";
    if (providerKeyInput) providerKeyInput.value = "";
  }
  if (providerBaseUrlRow) providerBaseUrlRow.hidden = !provider.custom;
  if (providerKeyRow) providerKeyRow.hidden = provider.auth === "cli";
  if (providerSecurityNote) {
    providerSecurityNote.textContent = provider.auth === "cli"
      ? (selectedProvider === "codex"
        ? (conversationLanguage === "zh" ? "一个 MERRICK 专属 OAuth 配置文件保存在本机的受保护应用状态中；设置和实际运行时使用完全同一份配置。不会读取或改写 ~/.codex。" : "One MERRICK-only OAuth profile is stored in protected local app state. Settings and the runtime use exactly that same profile; ~/.codex is never read or changed.")
        : (conversationLanguage === "zh" ? "MERRICK 只检查本机 CLI 登录是否有效；订阅凭据始终由对应 CLI 保存。" : "MERRICK checks only whether the local CLI login succeeds. Your subscription credential stays with its CLI."))
      : (conversationLanguage === "zh" ? "MERRICK 会先隔离验证服务商、模型和密钥；只有验证成功才写入 macOS 钥匙串。密钥不会进入 App 文件、浏览器存储、日志或 GitHub 备份。" : "MERRICK first verifies the provider, model, and key in isolation. Only a successful connection is committed to macOS Keychain; the key never enters app files, browser storage, logs, or GitHub backup.");
  }
  if (providerConnectBtn) providerConnectBtn.textContent = provider.auth === "cli"
      ? (providerAuthRequired && selectedProvider === "codex"
      ? (conversationLanguage === "zh" ? "重新连接 MERRICK 模型" : "Reconnect MERRICK model")
      : (selectedProvider === "codex"
        ? (conversationLanguage === "zh" ? "连接 MERRICK 模型" : "Connect MERRICK model")
        : (conversationLanguage === "zh" ? `连接 ${provider.title}` : `Connect ${provider.title}`)))
    : (conversationLanguage === "zh" ? `验证并连接 ${provider.title}` : `Verify & connect ${provider.title}`);
  if (providerSkipBtn) {
    const usableExistingConnection = providerConnectionState?.configured === true
      && providerConnectionState?.requiresReconnect !== true;
    providerSkipBtn.hidden = !usableExistingConnection;
  }
  if (!preserveStatus) setProviderSetupStatus("");
  const busy = providerAttempt?.status === "connecting";
  for (const input of [providerConnectBtn, providerModelInput, providerModelSelect, providerBaseUrlInput, providerKeyInput]) {
    if (input) input.disabled = busy;
  }
  document.querySelectorAll(".provider-choice").forEach(button => { button.disabled = busy; });
  const reusableKey = provider.auth === "api" && providerConnectionState?.configured === true
    && providerConnectionState.provider === selectedProvider;
  if (reusableKey && providerConnectBtn) providerConnectBtn.textContent = conversationLanguage === "zh" ? "验证并切换模型" : "Verify & switch model";
  if (busy && providerConnectBtn) providerConnectBtn.textContent = conversationLanguage === "zh" ? "正在连接…" : "Connecting…";
  if (reusableKey && providerSecurityNote) providerSecurityNote.textContent = conversationLanguage === "zh"
    ? "密钥留空可复用此连接的钥匙串凭据。切换前先验证，失败不改变当前模型。"
    : "Leave the key blank to reuse this connection’s Keychain credential. Switching is verified first; failure keeps the active model.";
  renderProviderModels();
}

function requestProviderModels() {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    providerModelCatalog = {provider: selectedProvider, models: [], status: "error"};
  } else {
    providerModelCatalog = {provider: selectedProvider, models: [], status: "loading"};
    sendJson({type: "provider_models_request", provider: selectedProvider, request_id: ++providerCatalogRequest});
  }
  renderProviderModels();
}

function renderProviderModels() {
  if (!providerModelSelect) return;
  const zh = conversationLanguage === "zh";
  const catalog = providerModelCatalog.provider === selectedProvider ? providerModelCatalog : {models: [], status: "idle"};
  providerModelSelect.replaceChildren();
  const add = (value, label) => {
    const option = document.createElement("option"); option.value = value; option.textContent = label;
    providerModelSelect.append(option);
  };
  add("", zh ? "选择目录模型，或在下方输入 ID" : "Choose a catalog model, or enter an ID below");
  const ids = new Set();
  const current = providerConnectionState?.configured && providerConnectionState.provider === selectedProvider ? providerConnectionState.model : "";
  if (current) { add(current, `${current} · ${zh ? "当前使用" : "Active"}`); ids.add(current); }
  for (const model of catalog.models) {
    if (!ids.has(model.id)) { add(model.id, model.name === model.id ? model.id : `${model.name} · ${model.id}`); ids.add(model.id); }
  }
  providerModelSelect.value = ids.has(providerModelInput?.value) ? providerModelInput.value : "";
  if (providerModelsRefresh) {
    providerModelsRefresh.disabled = catalog.status === "loading" || providerAttempt?.status === "connecting";
    providerModelsRefresh.textContent = zh ? "刷新列表" : "Refresh list";
  }
  if (providerModelsStatus) {
    providerModelsStatus.textContent = catalog.status === "loading"
      ? (zh ? "正在读取 OpenClaw 模型目录…" : "Loading the OpenClaw model catalog…")
      : catalog.status === "error"
        ? (zh ? "目录暂不可用，可重试或手动输入模型 ID。" : "Catalog unavailable. Retry or enter a model ID manually.")
        : (zh ? `OpenClaw 目录 · ${catalog.models.length} 个候选模型；账号可用性以连接验证为准。` : `OpenClaw catalog · ${catalog.models.length} candidates; account access is checked when connecting.`);
  }
  const label = document.querySelector("label[for='provider-model-select']");
  if (label) label.textContent = zh ? "可选择的模型" : "Model catalog";
}

function displayProviderConnection(state) {
  const provider = PROVIDERS[state?.provider] || null;
  const displays = [providerCurrent, providerConnectionSummary].filter(Boolean);
  if (!displays.length) return;
  providerConnectionState = state || null;
  const updateDisplays = (text, status) => {
    for (const display of displays) {
      display.textContent = text;
      display.dataset.state = status;
    }
  };
  const zh = conversationLanguage === "zh";
  const online = ws?.readyState === WebSocket.OPEN;
  if (providerActiveModel) providerActiveModel.textContent = state?.configured
    ? `${zh ? "当前使用" : "ACTIVE MODEL"} · ${provider?.title || state.provider} · ${state?.model || "—"}`
    : (zh ? "当前使用 · 尚无已验证模型" : "ACTIVE MODEL · No verified model");
  if (providerRuntimeLabel) providerRuntimeLabel.textContent = !online
    ? (zh ? "本地服务 · 已断开" : "Local service · Disconnected")
    : providerRuntimeState?.ready === true
      ? (zh ? "本地服务 · 就绪（不代表模型授权）" : "Local service · Ready (not model authorization)")
      : (zh ? "本地服务 · 连接中" : "Local service · Connecting");
  if (providerAttempt) {
    const connecting = providerAttempt.status === "connecting";
    const label = connecting ? (zh ? "连接中" : "CONNECTING") : (zh ? "连接失败" : "CONNECTION FAILED");
    updateDisplays(`${label} · ${PROVIDERS[providerAttempt.provider]?.title || ""} · ${providerAttempt.model || ""}`, connecting ? "pending" : "error");
    return;
  }
  if ((providerAuthRequired || state?.requiresReconnect === true) && provider) {
    const stage = state?.connectionStage;
    const code = state?.connectionErrorCode;
    const reason = connectionFailureCopy(code, { short: true });
    const label = stage === CONNECTION_STAGES.failed
      ? (conversationLanguage === "zh" ? "连接失败" : "CONNECTION FAILED")
      : (conversationLanguage === "zh" ? "需要验证" : "VERIFICATION REQUIRED");
    updateDisplays(`${label} · ${provider.title}${state?.model ? ` · ${state.model}` : ""} · ${reason}`, "error");
    return;
  }
  if (!state?.configured && provider) {
    updateDisplays(`${conversationLanguage === "zh" ? "未连接" : "NOT CONNECTED"} · ${provider.title}`, "pending");
    return;
  }
  if (!online && state?.configured) {
    updateDisplays(zh ? "连接中断 · 已保留配置" : "DISCONNECTED · Configuration retained", "error");
    return;
  }
  if (providerRuntimeState?.ready === true && provider) {
    const scope = conversationLanguage === "zh" ? "已连接 · 授权已验证" : "CONNECTED · Credential verified";
    updateDisplays(`${scope} · ${provider.title}${state?.model ? ` · ${state.model}` : ""}`, "ready");
    return;
  }
  if (providerRuntimeState?.ready === false && provider) {
    const scope = conversationLanguage === "zh" ? "运行层不可用" : "RUNTIME UNAVAILABLE";
    updateDisplays(`${scope} · ${provider.title}${state?.model ? ` · ${state.model}` : ""}`, "error");
    return;
  }
  if (state?.configured && provider) {
    const scope = state.connectionScope === "jarvis"
      ? (conversationLanguage === "zh" ? "MERRICK 本机配置" : "MERRICK LOCAL PROFILE")
      : (conversationLanguage === "zh" ? "已连接" : "CONNECTED");
    updateDisplays(`${scope} · ${provider.title}${state.model ? ` · ${state.model}` : ""}`, "ready");
  } else if (provider) {
    const scope = state?.legacyLocalConnection
      ? (conversationLanguage === "zh" ? "本机连接迁移中" : "LOCAL CONNECTION MIGRATING")
      : (conversationLanguage === "zh" ? "等待连接验证" : "AWAITING VERIFICATION");
    updateDisplays(`${scope} · ${provider.title}${state?.model ? ` · ${state.model}` : ""}`, "pending");
  } else {
    updateDisplays(
      conversationLanguage === "zh" ? "未选择提供方" : "NO PROVIDER SELECTED",
      "pending",
    );
  }
}

function applyProviderConnectionState(state, { preserveDraft = false } = {}) {
  if (!state || typeof state !== "object") return false;
  onboardingRequired = state.onboardingRequired === true;
  providerAuthRequired = state.requiresReconnect === true;
  applyAddressPreferences(state.addressEnglish, state.addressChinese);
  const initialize = !providerDraftInitialized && !preserveDraft;
  if (initialize && typeof state.provider === "string" && PROVIDERS[state.provider]) selectedProvider = state.provider;
  displayProviderConnection(state);
  renderProviderForm({ preserveStatus: true, resetInputs: initialize });
  if (initialize) {
    if (state.model) providerModelInput.value = state.model;
    providerBaseUrlInput.value = state.baseURL || "";
    providerDraftInitialized = true;
    requestProviderModels();
  }
  return true;
}

window.merrickNativeProviderSetupState = function (state) {
  if (!applyProviderConnectionState(state)) return;
  setOnboardingVisible(onboardingRequired || providerManagerRequested);
};

function applyAddressPreferences(english, chinese) {
  const en = typeof english === "string" && english.trim() ? english.trim() : "sir";
  const zh = typeof chinese === "string" && chinese.trim() ? chinese.trim() : "先生";
  for (const input of [settingsAddressEnglish, onboardingAddressEnglish]) {
    if (input) input.value = en;
  }
  for (const input of [settingsAddressChinese, onboardingAddressChinese]) {
    if (input) input.value = zh;
  }
  sendJson({ type: "set_owner_addresses", english: en, chinese: zh });
}

function saveAddressPreferences() {
  const englishInput = onboardingRequired ? onboardingAddressEnglish : settingsAddressEnglish;
  const chineseInput = onboardingRequired ? onboardingAddressChinese : settingsAddressChinese;
  const english = (englishInput?.value || "").trim();
  const chinese = (chineseInput?.value || "").trim();
  if (!english || !chinese || english.length > 32 || chinese.length > 32) {
    if (addressStatus) addressStatus.textContent = t("address_invalid");
    return false;
  }
  nativePost("saveAddressPreferences", { english, chinese });
  applyAddressPreferences(english, chinese);
  return true;
}

window.merrickNativeAddressPreferencesSaved = function (ok, message) {
  if (addressStatus) {
    addressStatus.textContent = ok ? t("address_saved") : (message || t("address_invalid"));
    addressStatus.dataset.state = ok ? "ready" : "error";
  }
};

window.merrickNativeProviderSetupResult = function (result) {
  const ok = result?.ok === true;
  const message = typeof result?.message === "string" ? result.message : t("setup_failed");
  const attempted = providerAttempt || {provider: selectedProvider, model: providerModelInput?.value};
  providerAttempt = ok ? null : {...attempted, status: "error"};
  // A failed sign-in can invalidate a stale saved selection. Apply the
  // native credential-backed state before returning so the HUD never keeps a
  // green “connected” label after the runtime reported missing auth.
  applyProviderConnectionState(result, {preserveDraft: true});
  setProviderSetupStatus(message, ok ? "ready" : "error");
  if (providerCancelBtn) providerCancelBtn.hidden = true;
  if (providerDeviceCode) providerDeviceCode.hidden = true;
  if (providerVerificationLink) providerVerificationLink.hidden = true;
  if (providerAuthCard) providerAuthCard.hidden = true;
  if (providerDeviceCode) providerDeviceCode.textContent = "";
  if (providerVerificationLink) providerVerificationLink.dataset.verificationURL = "";
  if (!ok) return;
  providerKeyInput && (providerKeyInput.value = "");
  onboardingRequired = false;
  providerAuthRequired = false;
  displayProviderConnection(result);
  requestProviderModels();
};

window.merrickNativeProviderSetupProgress = function (progress) {
  const state = typeof progress === "string" ? { message: progress } : (progress || {});
  if (state.provider && PROVIDERS[state.provider]) selectedProvider = state.provider;
  if (typeof state.model === "string" && providerModelInput) providerModelInput.value = state.model;
  const message = typeof state.message === "string" ? state.message : t("connecting_provider");
  providerAttempt = {provider: selectedProvider, model: providerModelInput?.value, status: "connecting"};
  displayProviderConnection(providerConnectionState);
  renderProviderForm({preserveStatus: true});
  setProviderSetupStatus(message, "pending");
  if (providerDeviceCode && typeof state.deviceCode === "string" && state.deviceCode.trim()) {
    const firstCode = providerDeviceCode.hidden;
    providerDeviceCode.textContent = state.deviceCode.trim();
    providerDeviceCode.hidden = false;
    if (providerAuthCard) {
      providerAuthCard.hidden = false;
      if (firstCode) providerAuthCard.scrollIntoView({block: "center", behavior: "auto"});
    }
  }
  if (providerVerificationLink && typeof state.verificationURL === "string" && state.verificationURL) {
    providerVerificationLink.hidden = false;
    providerVerificationLink.dataset.verificationURL = state.verificationURL;
  }
  if (providerCancelBtn) providerCancelBtn.hidden = selectedProvider !== "codex" || providerDeviceCode?.hidden !== false;
};

function setConversationLanguage(language, { notifyNative = false } = {}) {
  if (language !== "en" && language !== "zh") return;
  applyInterfaceLanguage(language);
  window.MerrickPlanMode?.setLanguage(language);
  window.MerrickAgentBoard?.setLanguage(language);
  if (speechLanguageSelect) speechLanguageSelect.value = language;
  if (speechLanguageStatus) {
    speechLanguageStatus.textContent = t(language === "zh" ? "language_chinese_active" : "language_english_active");
    speechLanguageStatus.dataset.state = "ready";
  }
  // The backend keeps language per WebSocket session, so resend after every
  // reconnect as well as on a direct user switch.
  sendJson({ type: "set_language", language });
  if (notifyNative) nativePost("setSpeechLanguage", { language });
}

window.merrickNativeSpeechLanguage = function (language) {
  setConversationLanguage(language === "zh" ? "zh" : "en");
};

function setVoiceprintStatus(text, state = "") {
  if (!voiceprintStatus) return;
  voiceprintStatus.textContent = text;
  voiceprintStatus.dataset.state = state;
}

function updateVoiceprintManagementStatus(msg) {
  voiceprintRecording = false;
  if (msg.status === "ready") {
    const count = Number.isInteger(msg.count) ? msg.count : 0;
    setVoiceprintStatus(conversationLanguage === "zh" ? `已解锁 · ${count} 个本机声纹向量` : `UNLOCKED · ${count} local voice vector${count === 1 ? "" : "s"}`, "ready");
    voiceprintUnlocked = true;
    if (voiceprintUnlockBtn) voiceprintUnlockBtn.disabled = true;
    if (voiceprintEnrollBtn) voiceprintEnrollBtn.disabled = false;
  } else if (msg.status === "saved") {
    const count = Number.isInteger(msg.count) ? msg.count : 0;
    setVoiceprintStatus(conversationLanguage === "zh" ? `已保存 · ${count} 个本机声纹向量` : `SAVED · ${count} local voice vector${count === 1 ? "" : "s"}`, "saved");
    if (voiceprintEnrollBtn) voiceprintEnrollBtn.disabled = false;
  } else if (msg.status === "locked") {
    voiceprintUnlocked = false;
    setVoiceprintStatus(msg.message || t("locked_mac_auth"), "locked");
    if (voiceprintUnlockBtn) voiceprintUnlockBtn.disabled = false;
    if (voiceprintEnrollBtn) voiceprintEnrollBtn.disabled = true;
  } else if (msg.status === "error") {
    setVoiceprintStatus(msg.message || (conversationLanguage === "zh" ? "声音样本无法保存。" : "The sample could not be saved."), "error");
    if (voiceprintEnrollBtn) voiceprintEnrollBtn.disabled = !voiceprintUnlocked;
  }
}

organizerBtn?.addEventListener("click", () => {
  setOrganizerVisible(true, "overview");
});
organizerCloseBtn?.addEventListener("click", () => setOrganizerVisible(false));
organizerFullscreenBtn?.addEventListener("click", () => requestNativeFullscreen("toggle"));
organizerPanel?.addEventListener("click", (event) => {
  if (event.target === organizerPanel) setOrganizerVisible(false);
});
organizerRefreshBtn?.addEventListener("click", () => {
  setOrganizerStatus(oc("refreshRequested"));
  sendJson({ type: "organizer_snapshot_request" });
});
function submitIntelligenceBrief(generate) {
  const prompt = intelligencePromptInput?.value.trim() || "";
  if (!prompt) {
    intelligencePromptInput?.focus();
    setOrganizerStatus(t("intelligence_prompt_placeholder"), "error");
    return;
  }
  if (intelligenceSaveBtn) intelligenceSaveBtn.disabled = true;
  if (intelligenceGenerateBtn) intelligenceGenerateBtn.disabled = true;
  setOrganizerStatus(generate ? oc("intelligenceWorking") : oc("intelligenceSaved"), generate ? "working" : "");
  sendJson({
    type: "organizer_create_intelligence",
    title: intelligenceTitleInput?.value.trim() || "",
    prompt,
    enabled: Boolean(intelligenceEnabledInput?.checked),
    local_time: intelligenceTimeInput?.value || "08:00",
    generate,
  });
}
intelligenceSaveBtn?.addEventListener("click", () => submitIntelligenceBrief(false));
intelligenceGenerateBtn?.addEventListener("click", () => submitIntelligenceBrief(true));
journalPrevMonth?.addEventListener("click", () => {
  journalVisibleMonth = new Date(journalVisibleMonth.getFullYear(), journalVisibleMonth.getMonth() - 1, 1);
  renderWorkJournal(organizerSnapshot);
});
journalNextMonth?.addEventListener("click", () => {
  journalVisibleMonth = new Date(journalVisibleMonth.getFullYear(), journalVisibleMonth.getMonth() + 1, 1);
  renderWorkJournal(organizerSnapshot);
});
journalToday?.addEventListener("click", () => {
  const today = new Date();
  selectedJournalDate = localDateKey(today);
  journalVisibleMonth = new Date(today.getFullYear(), today.getMonth(), 1);
  renderWorkJournal(organizerSnapshot);
});
document.querySelectorAll("[data-organizer-view]").forEach((button) => {
  button.addEventListener("click", () => setOrganizerView(button.dataset.organizerView || "overview"));
  button.addEventListener("keydown", (event) => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    const tabs = [...document.querySelectorAll("[data-organizer-view]")];
    const current = Math.max(0, tabs.indexOf(button));
    const targetIndex = event.key === "Home" ? 0
      : event.key === "End" ? tabs.length - 1
        : (current + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
    const target = tabs[targetIndex];
    if (!target) return;
    event.preventDefault();
    setOrganizerView(target.dataset.organizerView || "overview");
    target.focus();
  });
});

setupBtn?.addEventListener("click", () => {
  setSetupPanelVisible(true);
  nativePost("getProviderSetupState");
  nativePost("getAutomationAccessState");
  if (capabilityInventory.summary) updateCapabilitySummary(capabilityInventory.summary);
});
setupCloseBtn?.addEventListener("click", closeSetupPanel);
setupPanel?.addEventListener("click", (event) => {
  if (event.target === setupPanel) closeSetupPanel();
});
openWorkspaceBtn?.addEventListener("click", () => {
  if (!nativePost("openWorkspace")) {
    setVoiceprintStatus(conversationLanguage === "zh" ? "工作区文件夹只能在 MERRICK 桌面 App 中打开。" : "Workspace folders are available in the MERRICK desktop app.", "error");
  }
});
openOpenClawDashboardBtn?.addEventListener("click", () => {
  openOpenClawDashboardBtn.disabled = true;
  if (openClawDashboardStatus) {
    openClawDashboardStatus.textContent = t("opening_openclaw_dashboard");
    openClawDashboardStatus.dataset.state = "pending";
  }
  if (!nativePost("openOpenClawDashboard")) {
    window.merrickNativeOpenClawDashboardStatus(false, t("openclaw_dashboard_unavailable"));
  }
});
voiceprintUnlockBtn?.addEventListener("click", () => {
  setVoiceprintStatus(conversationLanguage === "zh" ? "正在等待 Mac 验证…" : "WAITING FOR MAC AUTHENTICATION…", "pending");
  if (!nativePost("authenticateVoiceprintManagement")) {
    setVoiceprintStatus(conversationLanguage === "zh" ? "声纹管理只能在 MERRICK 桌面 App 中使用。" : "Voiceprint management is available in the MERRICK desktop app.", "error");
  }
});
voiceprintEnrollBtn?.addEventListener("click", () => {
  if (!voiceprintUnlocked || voiceprintRecording) return;
  voiceprintRecording = true;
  voiceprintEnrollBtn.disabled = true;
  setVoiceprintStatus(conversationLanguage === "zh" ? "正在准备麦克风…" : "PREPARING MICROPHONE…", "pending");
  if (!nativePost("captureVoiceprintSample")) {
    voiceprintRecording = false;
    voiceprintEnrollBtn.disabled = false;
    setVoiceprintStatus(conversationLanguage === "zh" ? "声纹录入只能在 MERRICK 桌面 App 中使用。" : "Voiceprint capture is available in the MERRICK desktop app.", "error");
  }
});
memoryExportBtn?.addEventListener("click", () => {
  if (memoryExportBtn) memoryExportBtn.disabled = true;
  if (memoryExportStatus) {
    memoryExportStatus.textContent = conversationLanguage === "zh" ? "正在等待 Mac 验证…" : "WAITING FOR MAC AUTHENTICATION…";
    memoryExportStatus.dataset.state = "pending";
  }
  if (!nativePost("exportMemoryArchive")) {
    if (memoryExportBtn) memoryExportBtn.disabled = false;
    if (memoryExportStatus) {
      memoryExportStatus.textContent = conversationLanguage === "zh" ? "记忆导出只能在 MERRICK 桌面 App 中使用。" : "Memory export is available only in the MERRICK desktop app.";
      memoryExportStatus.dataset.state = "error";
    }
  }
});
uninstallBtn?.addEventListener("click", () => {
  nativePost("uninstall");
});
providerOpenBtn?.addEventListener("click", () => {
  providerManagerRequested = true;
  setSetupPanelVisible(false);
  setOnboardingVisible(true);
  nativePost("getProviderSetupState");
  requestProviderModels();
});
automationAccessChoose?.addEventListener("click", () => nativePost("chooseAutomationAccessRoot"));
automationAccessSave?.addEventListener("click", () => nativePost("saveAutomationAccessPolicy", { enabled: automationAccessEnable?.checked === true }));
automationAuditOpen?.addEventListener("click", () => nativePost("openAutomationAudit"));
capabilitiesOpenBtn?.addEventListener("click", () => setCapabilitiesVisible(true));
capabilitiesCloseBtn?.addEventListener("click", () => setCapabilitiesVisible(false));
capabilitiesPanel?.addEventListener("click", (event) => {
  if (event.target === capabilitiesPanel) setCapabilitiesVisible(false);
});
capabilitiesRefreshBtn?.addEventListener("click", requestCapabilityInventory);
capabilitiesDiagnoseBtn?.addEventListener("click", () => {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  if (capabilityDiagnostics) capabilityDiagnostics.hidden = true;
  setCapabilityStatus(conversationLanguage === "zh" ? "正在运行 OpenClaw 只读健康检查…" : "Running OpenClaw’s read-only health checks…", "pending");
  sendJson({ type: "capabilities_diagnostics" });
});
capabilityList?.addEventListener("click", (event) => {
  const operation = event.target instanceof Element
    ? event.target.closest("[data-plugin-operation]") : null;
  if (operation instanceof HTMLButtonElement && !operation.disabled && !capabilityBusy) {
    const action = operation.dataset.pluginOperation;
    const source = operation.dataset.pluginSource || "";
    const identity = operation.dataset.pluginIdentity;
    if (!["install", "upgrade", "uninstall"].includes(action) || !identity || !ws || ws.readyState !== WebSocket.OPEN) return;
    capabilityBusy = true;
    renderCapabilityInventory();
    setCapabilityStatus(t("capability_review_loading"), "pending");
    sendJson({ type: "plugin_operation_review_request", action, source, identity });
    return;
  }
  const button = event.target instanceof Element
    ? event.target.closest("[data-capability-action='review']") : null;
  if (!(button instanceof HTMLButtonElement) || button.disabled || capabilityBusy) return;
  const kind = button.dataset.capabilityKind;
  const id = button.dataset.capabilityId;
  if ((kind !== "plugin" && kind !== "skill") || !id || !ws || ws.readyState !== WebSocket.OPEN) return;
  capabilityBusy = true;
  renderCapabilityInventory();
  setCapabilityStatus(t("capability_review_loading"), "pending");
  sendJson({ type: "capability_review_request", kind, id, enabled: button.dataset.enabled !== "true" });
});
capabilityReviewCancel?.addEventListener("click", closeCapabilityReview);
capabilityReviewConfirm?.addEventListener("click", () => {
  const operationId = pendingCapabilityReview?.operation_id;
  if (!operationId || capabilityBusy || !ws || ws.readyState !== WebSocket.OPEN) return;
  capabilityBusy = true;
  capabilityReviewConfirm.disabled = true;
  setCapabilityStatus(t("capability_review_applying"), "pending");
  if (pendingCapabilityReview?.action) {
    sendJson({ type: "plugin_operation_apply", operation_id: operationId });
  } else {
    sendJson({ type: "capability_review_apply", operation_id: operationId });
  }
});
capabilitiesSearch?.addEventListener("input", () => {
  renderCapabilityInventory();
  if (capabilitySearchTimer) clearTimeout(capabilitySearchTimer);
  if (capabilityTab === "discover") {
    capabilitySearchTimer = setTimeout(() => requestPluginCatalog(capabilitiesSearch.value), 320);
  }
});
document.querySelectorAll(".capabilities-tab").forEach((button) => {
  button.addEventListener("click", () => {
    const next = button.dataset.capabilityTab;
    if (next !== "plugins" && next !== "discover" && next !== "skills") return;
    capabilityTab = next;
    document.querySelectorAll(".capabilities-tab").forEach((tab) => {
      const selected = tab.dataset.capabilityTab === next;
      tab.classList.toggle("active", selected); tab.setAttribute("aria-selected", String(selected));
    });
    renderCapabilityInventory();
    if (next === "discover") requestPluginCatalog(capabilitiesSearch?.value || "");
  });
});
providerBackBtn?.addEventListener("click", () => {
  // Keep the selected provider and form inputs alive in this document; the
  // user can inspect another setting and return without starting over.
  providerManagerRequested = false;
  setOnboardingVisible(false);
  setSetupPanelVisible(true);
});
providerCloseBtn?.addEventListener("click", () => {
  providerManagerRequested = false;
  setOnboardingVisible(false);
});
document.querySelectorAll(".provider-choice").forEach((button) => {
  button.addEventListener("click", () => {
    const next = button.dataset.provider;
    if (!next || !PROVIDERS[next]) return;
    if (providerAttempt?.status === "connecting") return;
    selectedProvider = next;
    providerDraftInitialized = true;
    providerAttempt = null;
    renderProviderForm({resetInputs: true});
    if (providerConnectionState?.provider === next) {
      providerModelInput.value = providerConnectionState.model || PROVIDERS[next].model;
      providerBaseUrlInput.value = providerConnectionState.baseURL || "";
    }
    displayProviderConnection(providerConnectionState);
    requestProviderModels();
  });
});
providerConnectBtn?.addEventListener("click", () => {
  if (providerAttempt?.status === "connecting") return;
  if (!saveAddressPreferences()) return;
  const provider = PROVIDERS[selectedProvider];
  if (!provider) return;
  const model = providerModelInput?.value.trim() || "";
  const baseUrl = provider.custom ? providerBaseUrlInput?.value.trim() || "" : "";
  if (!model) {
    setProviderSetupStatus(t("model_required"), "error");
    return;
  }
  if (provider.custom && !baseUrl) {
    setProviderSetupStatus(t("base_url_required"), "error");
    return;
  }
  if (provider.auth === "api") {
    const apiKey = providerKeyInput?.value || "";
    const reuseSavedKey = !apiKey.trim() && providerConnectionState?.configured === true
      && providerConnectionState.provider === selectedProvider;
    if (!reuseSavedKey && apiKey.trim().length < 8) {
      setProviderSetupStatus(t("api_key_required"), "error");
      return;
    }
    providerAttempt = {status: "connecting", provider: selectedProvider, model};
    setProviderSetupStatus(t("saving_key"), "pending");
    if (!nativePost("saveProviderAPIKey", { provider: selectedProvider, model, baseUrl, apiKey, reuseSavedKey })) {
      providerAttempt.status = "error";
      setProviderSetupStatus(conversationLanguage === "zh" ? "请在桌面 App 内连接模型。" : "Connect models inside the desktop app.", "error");
    }
  } else {
    providerAttempt = {status: "connecting", provider: selectedProvider, model};
    setProviderSetupStatus(t("opening_sign_in"), "pending");
    if (!nativePost("connectProviderCLI", { provider: selectedProvider, model })) {
      providerAttempt.status = "error";
      setProviderSetupStatus(conversationLanguage === "zh" ? "请在桌面 App 内连接模型。" : "Connect models inside the desktop app.", "error");
    }
  }
  displayProviderConnection(providerConnectionState);
  renderProviderForm({preserveStatus: true});
});
providerModelsRefresh?.addEventListener("click", requestProviderModels);
providerModelSelect?.addEventListener("change", () => {
  if (providerModelSelect.value) providerModelInput.value = providerModelSelect.value;
});
providerModelInput?.addEventListener("input", renderProviderModels);
providerCancelBtn?.addEventListener("click", () => nativePost("cancelProviderConnection"));
providerVerificationLink?.addEventListener("click", () => nativePost("openProviderVerificationURL"));
providerSkipBtn?.addEventListener("click", () => {
  if (!saveAddressPreferences()) return;
  setProviderSetupStatus(t("keeping_connection"), "pending");
  nativePost("finishOnboarding");
});
saveAddressBtn?.addEventListener("click", saveAddressPreferences);

function restoreRecentEditionResearchDisplay() {
  if (currentResearchSources.length || activeAssistantText.trim()) return "";
  const edition = organizerArray(organizerSnapshot?.intelligence_editions, 50)[0];
  if (!edition) return "";
  const sources = organizerArray(edition.sources, 8).filter((source) =>
    typeof source.url === "string" && /^https?:\/\//i.test(source.url) &&
    typeof source.title === "string" && typeof source.snippet === "string"
  );
  if (!sources.length) return "";

  currentResearchSources = sources;
  const content = edition.content && typeof edition.content === "object" ? edition.content : {};
  const headline = typeof content.headline === "string" ? content.headline.trim() : "";
  const deck = typeof content.deck === "string" ? content.deck.trim() : "";
  const storyNotes = organizerArray(content.stories, 2).map((story) => {
    const title = typeof story.headline === "string" ? story.headline.trim() : "";
    const summary = typeof story.summary === "string" ? story.summary.trim() : "";
    return [title, summary].filter(Boolean).join(" — ");
  }).filter(Boolean);
  if (researchQuery) {
    researchQuery.dataset.i18nDynamic = "true";
    const label = edition.title || headline || (conversationLanguage === "zh" ? "最近一期报纸" : "Latest newspaper edition");
    researchQuery.textContent = conversationLanguage === "zh"
      ? `最近一期证据 · ${label}`
      : `Latest edition evidence · ${label}`;
  }
  return [headline, deck, ...storyNotes].filter(Boolean).join("\n\n");
}

displayBtn?.addEventListener("click", () => {
  const restoredEditionText = restoreRecentEditionResearchDisplay();
  renderResearchSources();
  setResearchDisplayVisible(true);
  renderDisplayText(displayAnswer, restoredEditionText || activeAssistantText);
});
function closeResearchDisplay() {
  // Closing an unresolved technical-term chooser is an explicit decision to
  // abandon it. That is the only way a new spoken request can resume ASR
  // routing; merely speaking again must never re-run the same misheard term.
  if (activeResearchChoiceId) {
    sendJson({ type: "cancel_research_query_choice", choice_id: activeResearchChoiceId });
    clearResearchQueryChoice();
  }
  setResearchDisplayVisible(false);
}

researchCloseBtn?.addEventListener("click", closeResearchDisplay);
researchDisplay?.addEventListener("click", (event) => {
  if (event.target === researchDisplay) closeResearchDisplay();
});
openAllSourcesBtn?.addEventListener("click", () => {
  const urls = currentResearchSources.map((source) => source.url).slice(0, 8);
  if (urls.length) nativePost("openResearchPages", { urls });
});
speechLanguageSelect?.addEventListener("change", () => {
  const language = speechLanguageSelect.value === "zh" ? "zh" : "en";
  // Do not let an already queued sentence emerge in the old language after a
  // deliberate mode switch. The backend invalidates the same turn atomically.
  stopAudio();
  sendJson({ type: "interrupt" });
  setConversationLanguage(language, { notifyNative: true });
});
watchModeBtn?.addEventListener("click", () => {
  if (meetingModeEnabled) meetingModeBtn?.click();
  watchModeEnabled = !watchModeEnabled;
  watchModeOwnerVerified = false;
  watchModeBufferedTranscript = null;
  watchCleanVoiceActive = false;
  watchVoiceVerificationRequested = false;
  clearTimeout(watchVerificationTimeout);
  watchVerificationTimeout = null;
  meetingCleanVoiceActive = false;
  meetingCommandInterruptPending = false;
  watchModeBtn.classList.toggle("active", watchModeEnabled);
  watchModeBtn.setAttribute("aria-pressed", String(watchModeEnabled));
  watchModeBtn.textContent = t(watchModeEnabled ? "watch_mode_owner" : "watch_mode");
  interimEl.textContent = "";
  // Watch Mode intentionally keeps the known-good raw microphone path. On this
  // Mac, Voice Processing I/O accepted the change but stopped producing usable
  // speech recognition results. The backend owner-only verifier remains the
  // gate that keeps television dialogue out of the conversation.
  nativePost("setWatchAudioMode", { enabled: watchModeEnabled });
  sendJson({ type: "set_owner_only_mode", enabled: watchModeEnabled });
  logLine("info", watchModeEnabled
    ? (conversationLanguage === "zh" ? "观影模式已开启：只有已验证的主人声纹会进入 MERRICK。" : "Watch mode enabled: only your verified voice reaches MERRICK")
    : (conversationLanguage === "zh" ? "观影模式已关闭。" : "Watch mode disabled."));
});
meetingModeBtn?.addEventListener("click", () => {
  if (!meetingModeEnabled && watchModeEnabled) watchModeBtn?.click();
  if (meetingModeEnabled) flushMeetingTranscript(true);
  meetingModeEnabled = !meetingModeEnabled;
  meetingLatestTranscript = "";
  meetingCommandActive = false;
  meetingCommandTranscript = "";
  meetingPendingTranscript = "";
  meetingCleanVoiceActive = false;
  meetingCommandInterruptPending = false;
  meetingModeBtn.classList.toggle("active", meetingModeEnabled);
  meetingModeBtn.setAttribute("aria-pressed", String(meetingModeEnabled));
  meetingModeBtn.textContent = t(meetingModeEnabled ? "meeting_mode_notes" : "meeting_mode");
  interimEl.textContent = "";
  sendJson({ type: "set_meeting_mode", enabled: meetingModeEnabled });
  // In meeting mode computer audio is only a local AEC reference.  It does
  // not create a recording and it never enters the conversation transcript.
  nativePost("setMeetingAudioMode", { enabled: meetingModeEnabled });
  logLine("info", meetingModeEnabled
    ? (conversationLanguage === "zh" ? "会议模式已开启：内容会在本机记录；称呼 Merrick 才会获得回答。" : "Meeting mode enabled: recording locally; say Merrick to invite a reply.")
    : (conversationLanguage === "zh" ? "会议模式已关闭。" : "Meeting mode disabled."));
});
$("close-btn")?.addEventListener("click", () => {
  if (!isDesktop || appClosing) return;
  appClosing = true;
  // Ask the native host to terminate the complete app process. Closing the
  // socket prevents any reconnect/listening work while macOS runs cleanup.
  nativePost("quit");
  if (ws && ws.readyState < WebSocket.CLOSING) ws.close(1000, "app quitting");
});

if (isDesktop) document.body.classList.add("desktop");
refreshMicControl();

ttsToggle.addEventListener("change", () => {
  sendJson({ type: "set_tts", enabled: ttsToggle.checked });
  if (!ttsToggle.checked) stopAudio();
});

// ---------------- 全息点云 (golden hologram) ----------------
const holo = $("holo");
const hctx = holo.getContext("2d");
const HW = holo.width, HH = holo.height;
const CX = HW / 2, CY = HH / 2, R = HW * 0.36;

// 发光粒子贴图（预渲染，避免每帧 shadowBlur）
function makeSprite(r, g, b) {
  const c = document.createElement("canvas");
  c.width = c.height = 32;
  const g2 = c.getContext("2d");
  const grad = g2.createRadialGradient(16, 16, 0, 16, 16, 16);
  grad.addColorStop(0, "rgba(255,250,224,1)");
  grad.addColorStop(0.24, `rgba(${r},${g},${b},0.94)`);
  grad.addColorStop(0.58, `rgba(${r},${g},${b},0.3)`);
  grad.addColorStop(1, `rgba(${r},${g},${b},0)`);
  g2.fillStyle = grad;
  g2.fillRect(0, 0, 32, 32);
  return c;
}
const spriteGold = makeSprite(255, 180, 70);
const spriteBright = makeSprite(255, 220, 140);

// —— 粒子集合 ——
const spherePts = [];   // primary shell
const innerPts = [];    // counter-rotating inner shell
const corePts = [];     // dense energy core
const dustPts = [];     // sparse outer halo
const rings = [];       // articulated orbital planes
const satellites = [];  // bright data packets travelling on rings
const spatialArcs = []; // incomplete mechanical/circuit fragments
const shellFacets = []; // translucent triangular hologram shards
const spokeAnchors = [];// radial energy skeleton

function seeded01(seed) {
  const value = Math.sin(seed * 12.9898 + 78.233) * 43758.5453;
  return value - Math.floor(value);
}

(function buildCloud() {
  const N = 860, GA = Math.PI * (3 - Math.sqrt(5));
  for (let i = 0; i < N; i++) {
    const y = 1 - (i / (N - 1)) * 2;
    const rr = Math.sqrt(1 - y * y);
    const th = GA * i;
    spherePts.push({
      x: Math.cos(th) * rr, y, z: Math.sin(th) * rr,
      s: 0.5 + Math.random() * 0.9, ph: Math.random() * 6.28,
    });
  }
  for (let i = 0; i < 280; i++) {
    const y = 1 - (i / 279) * 2;
    const rr = Math.sqrt(1 - y * y);
    const th = GA * i + 0.7;
    const radius = 0.5 + Math.random() * 0.13;
    innerPts.push({
      x: Math.cos(th) * rr * radius, y: y * radius,
      z: Math.sin(th) * rr * radius, s: 0.4 + Math.random() * 0.8,
      ph: Math.random() * Math.PI * 2,
    });
  }
  for (let i = 0; i < 210; i++) {
    const g = () => (Math.random() + Math.random() + Math.random() - 1.5) * 0.24;
    corePts.push({ x: g(), y: g(), z: g(), s: 0.7 + Math.random(), ph: Math.random() * 6.28 });
  }
  for (let i = 0; i < 150; i++) {
    const y = Math.random() * 2 - 1;
    const rr = Math.sqrt(1 - y * y);
    const th = Math.random() * Math.PI * 2;
    const radius = 1.08 + Math.random() * 0.34;
    dustPts.push({ x: Math.cos(th) * rr * radius, y: y * radius,
      z: Math.sin(th) * rr * radius, s: Math.random(), ph: Math.random() * 6.28 });
  }
  const ringCfg = [
    // Each orbital layer has its own mechanical language. shellWidth extends
    // along the plane normal, so the module faces point out from the orb.
    { name: "gear-crown", tiltX: 0.5, tiltZ: 0.2, r: 1.01, n: 128,
      speed: 0.35, shellWidth: 0.088, moduleCount: 23, seed: 11,
      kinds: [0, 5, 0, 1, 4], rails: [-0.72, 0.64], railDash: [18, 7, 3, 6],
      railWidth: 1.7, railEvery: 1, cloudDensity: 1.05, dotScale: 1.0, cloudAlpha: 0.62,
      fill: "rgba(255,132,18,1)", edge: "rgba(255,219,139,1)" },
    { name: "twin-coupler", tiltX: -0.9, tiltZ: 0.5, r: 0.89, n: 112,
      speed: -0.22, shellWidth: 0.112, moduleCount: 17, seed: 29,
      kinds: [2, 1, 2, 5, 3], rails: [-0.82, 0, 0.78], railDash: [9, 5],
      railWidth: 1.15, railEvery: 2, cloudDensity: 0.86, dotScale: 1.14, cloudAlpha: 0.56,
      fill: "rgba(255,157,35,1)", edge: "rgba(255,198,91,1)" },
    { name: "circuit-comb", tiltX: 0.15, tiltZ: -0.75, r: 0.73, n: 104,
      speed: 0.5, shellWidth: 0.075, moduleCount: 29, seed: 47,
      kinds: [3, 5, 3, 0, 1], rails: [0], railDash: [4, 3, 13, 5],
      railWidth: 1.05, railEvery: 1, cloudDensity: 0.7, dotScale: 0.78, cloudAlpha: 0.7,
      fill: "rgba(255,175,50,1)", edge: "rgba(255,230,163,1)" },
    { name: "keyed-shutters", tiltX: 1.18, tiltZ: -0.18, r: 0.58, n: 88,
      speed: -0.7, shellWidth: 0.098, moduleCount: 13, seed: 73,
      kinds: [4, 1, 4, 0, 5], rails: [-0.46, 0.52], railDash: [24, 11],
      railWidth: 1.35, railEvery: 2, cloudDensity: 1.18, dotScale: 1.04, cloudAlpha: 0.66,
      fill: "rgba(255,118,12,1)", edge: "rgba(255,205,110,1)" },
    { name: "outer-exoskeleton", tiltX: -0.35, tiltZ: 1.05, r: 1.13, n: 120,
      speed: 0.16, shellWidth: 0.128, moduleCount: 15, seed: 101,
      kinds: [1, 2, 0, 4, 3, 5], rails: [-0.9, 0.86], railDash: [31, 10, 6, 12],
      railWidth: 2.0, railEvery: 2, cloudDensity: 0.78, dotScale: 1.28, cloudAlpha: 0.48,
      fill: "rgba(255,145,24,1)", edge: "rgba(255,224,143,1)" },
  ];
  for (const cfg of ringCfg) {
    // 环平面的正交基
    const n = norm3(rot3({ x: 0, y: 1, z: 0 }, cfg.tiltX, 0, cfg.tiltZ));
    const u = norm3(cross3(n, { x: 1, y: 0.3, z: 0.2 }));
    const v = cross3(n, u);
    const pts = [];
    for (let i = 0; i < cfg.n; i++) {
      pts.push({ th: (i / cfg.n) * Math.PI * 2, s: 0.45 + Math.random() * 0.7 });
    }
    const modules = [];
    const step = Math.PI * 2 / cfg.moduleCount;
    for (let i = 0; i < cfg.moduleCount; i++) {
      const base = cfg.seed + i * 9.173;
      const spanVariation = 0.5 + seeded01(base + 1) * 0.36;
      const kindIndex = (i + Math.floor(seeded01(base + 2) * cfg.kinds.length)) % cfg.kinds.length;
      modules.push({
        index: i,
        th: i * step + (seeded01(base + 3) - 0.5) * step * 0.28,
        span: step * spanVariation,
        kind: cfg.kinds[kindIndex],
        widthScale: 0.68 + seeded01(base + 4) * 0.42,
        normalShift: (seeded01(base + 5) - 0.5) * cfg.shellWidth * 0.42,
        radialLift: 0.006 + seeded01(base + 6) * 0.025,
        thickness: 0.012 + seeded01(base + 7) * 0.026,
        skew: (seeded01(base + 8) - 0.5) * 0.16,
        mirror: seeded01(base + 9) > 0.5,
        detail: Math.floor(seeded01(base + 10) * 4),
        pulse: seeded01(base + 11) * Math.PI * 2,
      });
    }
    rings.push({ ...cfg, normal: n, u, v, pts, modules,
      angle: seeded01(cfg.seed * 1.31) * Math.PI * 2 });
  }
  for (let i = 0; i < 14; i++) {
    satellites.push({ ring: i % rings.length, th: Math.random() * 6.28,
      speed: 0.35 + Math.random() * 0.8, size: 5 + Math.random() * 5 });
  }
  for (let i = 0; i < 34; i++) {
    const normal = norm3({ x: Math.random() * 2 - 1, y: Math.random() * 2 - 1,
      z: Math.random() * 2 - 1 });
    const axis = Math.abs(normal.y) < 0.86 ? { x: 0, y: 1, z: 0 } : { x: 1, y: 0, z: 0 };
    const u = norm3(cross3(normal, axis));
    const v = cross3(normal, u);
    const start = Math.random() * Math.PI * 2;
    const span = 0.35 + Math.random() * 2.15;
    const radius = 0.32 + Math.random() * 0.83;
    const pts = [];
    for (let j = 0; j <= 18; j++) {
      const th = start + span * j / 18;
      pts.push({ x: (u.x * Math.cos(th) + v.x * Math.sin(th)) * radius,
        y: (u.y * Math.cos(th) + v.y * Math.sin(th)) * radius,
        z: (u.z * Math.cos(th) + v.z * Math.sin(th)) * radius });
    }
    spatialArcs.push({ pts, speed: (Math.random() - 0.5) * 0.16,
      alpha: 0.14 + Math.random() * 0.24, ph: Math.random() * 6.28 });
  }
  for (let i = 0; i < 96; i++) {
    const n = norm3({ x: Math.random() * 2 - 1, y: Math.random() * 2 - 1,
      z: Math.random() * 2 - 1 });
    const axis = Math.abs(n.y) < 0.88 ? { x: 0, y: 1, z: 0 } : { x: 1, y: 0, z: 0 };
    const u = norm3(cross3(n, axis));
    const v = cross3(n, u);
    const radius = 0.84 + Math.random() * 0.2;
    const size = 0.025 + Math.random() * 0.07;
    const verts = [];
    for (let j = 0; j < 3; j++) {
      const a = j * Math.PI * 2 / 3 + Math.random() * 0.35;
      verts.push({ x: n.x * radius + (u.x * Math.cos(a) + v.x * Math.sin(a)) * size,
        y: n.y * radius + (u.y * Math.cos(a) + v.y * Math.sin(a)) * size,
        z: n.z * radius + (u.z * Math.cos(a) + v.z * Math.sin(a)) * size });
    }
    shellFacets.push({ verts, ph: Math.random() * 6.28, alpha: 0.065 + Math.random() * 0.13 });
  }
  for (let i = 0; i < 38; i++) spokeAnchors.push(spherePts[(i * 23 + 7) % spherePts.length]);
})();

// 随机"电路"细丝：球面上距离近的点对，闪烁连线
const filaments = [];
(function buildFilaments() {
  let guard = 0;
  while (filaments.length < 125 && guard++ < 12000) {
    const a = spherePts[(Math.random() * spherePts.length) | 0];
    const b = spherePts[(Math.random() * spherePts.length) | 0];
    const d = Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
    if (d > 0.08 && d < 0.55) filaments.push({ a, b, ph: Math.random() * 6.28, sp: 0.5 + Math.random() * 2 });
  }
})();

function cross3(a, b) {
  return { x: a.y * b.z - a.z * b.y, y: a.z * b.x - a.x * b.z, z: a.x * b.y - a.y * b.x };
}
function norm3(a) {
  const l = Math.hypot(a.x, a.y, a.z) || 1;
  return { x: a.x / l, y: a.y / l, z: a.z / l };
}
function rot3(p, ax, ay, az) {
  let { x, y, z } = p;
  if (ay) { const c = Math.cos(ay), s = Math.sin(ay); [x, z] = [x * c + z * s, -x * s + z * c]; }
  if (ax) { const c = Math.cos(ax), s = Math.sin(ax); [y, z] = [y * c - z * s, y * s + z * c]; }
  if (az) { const c = Math.cos(az), s = Math.sin(az); [x, y] = [x * c - y * s, x * s + y * c]; }
  return { x, y, z };
}

// Orthogonal, deliberately asymmetric outlines. Each face lives on the
// tangent shell of its orbit: X follows the orbit, Y follows the orbit normal,
// and the face itself points radially away from the hologram centre.
const MODULE_PROFILES = [
  // Heavy gear tooth with a stepped crown and offset shoulder.
  [[[-0.50, -0.50], [-0.18, -0.50], [-0.18, -0.72], [0.08, -0.72],
    [0.08, -0.50], [0.50, -0.50], [0.50, 0.10], [0.31, 0.10],
    [0.31, 0.50], [-0.50, 0.50]]],
  // L-shaped locking bracket.
  [[[-0.50, -0.50], [0.14, -0.50], [0.14, -0.18], [0.50, -0.18],
    [0.50, 0.50], [-0.09, 0.50], [-0.09, 0.20], [-0.50, 0.20]]],
  // Two separate plates held by an off-centre coupler.
  [[[-0.50, -0.54], [0.36, -0.54], [0.36, -0.28], [0.50, -0.28],
    [0.50, -0.08], [-0.18, -0.08], [-0.18, -0.22], [-0.50, -0.22]],
   [[-0.38, 0.10], [0.50, 0.10], [0.50, 0.48], [0.08, 0.48],
    [0.08, 0.64], [-0.18, 0.64], [-0.18, 0.48], [-0.38, 0.48]],
   [[-0.08, -0.17], [0.18, -0.17], [0.18, 0.25], [-0.08, 0.25]]],
  // Comb bus with separate right-angle contacts.
  [[[-0.50, -0.20], [-0.28, -0.20], [-0.28, -0.45], [-0.08, -0.45],
    [-0.08, -0.20], [0.20, -0.20], [0.20, -0.36], [0.48, -0.36],
    [0.48, 0.20], [0.08, 0.20], [0.08, 0.43], [-0.18, 0.43],
    [-0.18, 0.20], [-0.50, 0.20]]],
  // Keyed shutter: broad on one side, narrow on the other.
  [[[-0.50, -0.46], [-0.06, -0.46], [-0.06, -0.22], [0.50, -0.22],
    [0.50, 0.46], [0.18, 0.46], [0.18, 0.25], [-0.25, 0.25],
    [-0.25, 0.05], [-0.50, 0.05]]],
  // Forked block with an inset tongue.
  [[[-0.50, -0.50], [0.50, -0.50], [0.50, -0.14], [0.15, -0.14],
    [0.15, 0.14], [0.50, 0.14], [0.50, 0.50], [-0.12, 0.50],
    [-0.12, 0.25], [-0.50, 0.25]],
   [[-0.34, 0.30], [-0.18, 0.30], [-0.18, 0.62], [-0.34, 0.62]]],
];

const MODULE_DETAILS = [
  [[-0.34, -0.05], [0.16, -0.05], [0.16, 0.24], [0.36, 0.24]],
  [[-0.31, -0.24], [-0.06, -0.24], [-0.06, 0.18], [0.29, 0.18]],
  [[-0.35, 0.24], [0.03, 0.24], [0.03, -0.16], [0.31, -0.16]],
  [[-0.29, -0.28], [-0.29, 0.08], [0.08, 0.08], [0.08, 0.31], [0.31, 0.31]],
];

function pointInPolygon(x, y, polygon) {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [xi, yi] = polygon[i], [xj, yj] = polygon[j];
    const crosses = (yi > y) !== (yj > y) &&
      x < (xj - xi) * (y - yi) / ((yj - yi) || 1e-9) + xi;
    if (crosses) inside = !inside;
  }
  return inside;
}

// Pre-sample every mechanical part once. The outline dots preserve the hard
// right-angle silhouette, interior dots reveal the face, and recessed copies
// on selected edges describe thickness without a single solid polygon.
(function buildMechanicalPointClouds() {
  rings.forEach((ring, ringIndex) => {
    ring.modules.forEach(module => {
      const cloud = [];
      const baseSeed = ring.seed * 101 + module.index * 37.7 + module.kind * 13;
      let serial = 0;
      for (const outline of MODULE_PROFILES[module.kind]) {
        for (let edge = 0; edge < outline.length; edge++) {
          const a = outline[edge], b = outline[(edge + 1) % outline.length];
          const edgeLength = Math.hypot(b[0] - a[0], b[1] - a[1]);
          const count = Math.max(1, Math.ceil(edgeLength * (3.4 + ring.cloudDensity * 1.45)));
          for (let dot = 0; dot < count; dot++) {
            const jitter = seeded01(baseSeed + serial * 0.731);
            const along = (dot + jitter * 0.24) / count;
            const x = a[0] + (b[0] - a[0]) * along;
            const y = a[1] + (b[1] - a[1]) * along;
            cloud.push({ x, y, depth: 0, kind: 1,
              size: 0.68 + seeded01(baseSeed + serial * 1.17 + 2) * 0.74,
              phase: seeded01(baseSeed + serial * 1.91 + 3) * Math.PI * 2 });
            // Sparse recessed companions make the cloud volumetric when the
            // shell turns edge-on; their depths differ for every module.
            if ((serial + edge + module.detail) % 6 === 0) {
              cloud.push({ x, y, depth: 0.3 + seeded01(baseSeed + serial + 5) * 0.7,
                kind: 2, size: 0.5 + seeded01(baseSeed + serial + 7) * 0.48,
                phase: seeded01(baseSeed + serial + 9) * Math.PI * 2 });
            }
            serial += 1;
          }
        }

        const xs = outline.map(p => p[0]), ys = outline.map(p => p[1]);
        const minX = Math.min(...xs), maxX = Math.max(...xs);
        const minY = Math.min(...ys), maxY = Math.max(...ys);
        const target = Math.max(2, Math.round((3.2 + seeded01(baseSeed + serial) * 4.2) *
          ring.cloudDensity));
        let accepted = 0;
        for (let attempt = 0; accepted < target && attempt < target * 20; attempt++) {
          const x = minX + (maxX - minX) * seeded01(baseSeed + serial + attempt * 2.13);
          const y = minY + (maxY - minY) * seeded01(baseSeed + serial + attempt * 3.71 + 1);
          if (!pointInPolygon(x, y, outline)) continue;
          cloud.push({ x, y, depth: seeded01(baseSeed + serial + attempt * 4.17) * 0.16,
            kind: 0, size: 0.56 + seeded01(baseSeed + serial + attempt * 5.31) * 0.66,
            phase: seeded01(baseSeed + serial + attempt * 6.23) * Math.PI * 2 });
          accepted += 1;
        }
        serial += target + 1;
      }

      // The former etched line is now a brighter dotted circuit path.
      const detail = MODULE_DETAILS[(module.detail + module.kind) % MODULE_DETAILS.length];
      for (let segment = 0; segment < detail.length - 1; segment++) {
        const a = detail[segment], b = detail[segment + 1];
        const count = 2 + ((segment + module.detail) % 3);
        for (let dot = 0; dot <= count; dot++) {
          const along = dot / count;
          cloud.push({ x: a[0] + (b[0] - a[0]) * along,
            y: a[1] + (b[1] - a[1]) * along, depth: -0.1, kind: 3,
            size: 0.8 + seeded01(baseSeed + serial * 1.43) * 0.7,
            phase: seeded01(baseSeed + serial * 2.07) * Math.PI * 2 });
          serial += 1;
        }
      }
      module.cloud = cloud;
    });
  });
})();

function ringSurfacePoint(ring, th, normalOffset = 0, radialOffset = 0) {
  const c = Math.cos(th), s = Math.sin(th);
  const radial = { x: ring.u.x * c + ring.v.x * s,
    y: ring.u.y * c + ring.v.y * s, z: ring.u.z * c + ring.v.z * s };
  return {
    x: radial.x * (ring.r + radialOffset) + ring.normal.x * normalOffset,
    y: radial.y * (ring.r + radialOffset) + ring.normal.y * normalOffset,
    z: radial.z * (ring.r + radialOffset) + ring.normal.z * normalOffset,
  };
}

function projectModuleSample(ring, module, sample, ax, ay) {
  const x = module.mirror ? -sample.x : sample.x;
  const th = ring.angle + module.th + x * module.span +
    sample.y * module.skew * module.span;
  const normalOffset = module.normalShift + sample.y * ring.shellWidth * 1.7 *
    module.widthScale;
  const radialOffset = module.radialLift - module.thickness * sample.depth;
  return project(ringSurfacePoint(ring, th, normalOffset, radialOffset), ax, ay);
}

let gAngle = 0;
let lastT = performance.now();

function project(p, ax, ay) {
  const q = rot3(p, ax, ay, 0);
  const persp = 1 / (1 - q.z * 0.32);
  return { sx: CX + q.x * R * persp, sy: CY + q.y * R * persp, z: q.z, persp };
}

function drawSprite(img, sx, sy, size, alpha) {
  hctx.globalAlpha = alpha;
  hctx.drawImage(img, sx - size / 2, sy - size / 2, size, size);
}

function drawOrbitalPath(points, ax, ay, alpha, width = 1) {
  hctx.beginPath();
  points.forEach((p, i) => {
    const pr = project(p, ax, ay);
    if (i === 0) hctx.moveTo(pr.sx, pr.sy); else hctx.lineTo(pr.sx, pr.sy);
  });
  hctx.closePath();
  hctx.globalAlpha = alpha;
  hctx.lineWidth = width;
  hctx.strokeStyle = "rgba(255,183,70,1)";
  hctx.stroke();
}

function drawSphereGrid(ax, ay, t, dim, intensity) {
  // Latitude bands form a rotating technical wireframe under the point shell.
  for (const y of [-0.72, -0.38, 0, 0.38, 0.72]) {
    const rr = Math.sqrt(1 - y * y);
    const pts = [];
    for (let i = 0; i < 72; i++) {
      const th = i / 72 * Math.PI * 2;
      pts.push({ x: Math.cos(th) * rr, y, z: Math.sin(th) * rr });
    }
    drawOrbitalPath(pts, ax, ay + t * 0.025, (0.025 + intensity * 0.055) * dim);
  }
  // Three meridians counter-rotate, creating the nested gyroscope appearance.
  for (let m = 0; m < 3; m++) {
    const pts = [];
    const offset = m * Math.PI / 3 + t * 0.035;
    for (let i = 0; i < 72; i++) {
      const th = i / 72 * Math.PI * 2;
      pts.push({ x: Math.cos(th) * Math.cos(offset), y: Math.sin(th),
        z: Math.cos(th) * Math.sin(offset) });
    }
    drawOrbitalPath(pts, ax, ay, (0.03 + intensity * 0.06) * dim);
  }
}

function drawCoreIris(t, coreBoost, dim) {
  hctx.save();
  hctx.translate(CX, CY);
  hctx.globalCompositeOperation = "lighter";
  const stateRate = uiState === "thinking" ? 3.2 : uiState === "speaking" ? 1.7 : 0.7;
  for (let layer = 0; layer < 5; layer++) {
    const radius = R * (0.07 + layer * 0.035);
    const phase = t * stateRate * (layer % 2 ? -1 : 1) + layer * 0.9;
    hctx.lineWidth = layer < 2 ? 2.4 : 1.1;
    hctx.strokeStyle = layer < 2 ? "rgba(255,235,174,1)" : "rgba(255,170,42,1)";
    hctx.globalAlpha = (0.18 + coreBoost * 0.19) * dim;
    for (let seg = 0; seg < 4; seg++) {
      const start = phase + seg * Math.PI / 2;
      hctx.beginPath();
      hctx.arc(0, 0, radius, start, start + 0.72);
      hctx.stroke();
    }
  }
  const pulseR = R * (0.025 + coreBoost * 0.018);
  const coreGlow = hctx.createRadialGradient(0, 0, 0, 0, 0, pulseR * 3.8);
  coreGlow.addColorStop(0, "rgba(255,255,226,.98)");
  coreGlow.addColorStop(.22, "rgba(255,204,104,.82)");
  coreGlow.addColorStop(1, "rgba(255,142,20,0)");
  hctx.globalAlpha = dim;
  hctx.fillStyle = coreGlow;
  hctx.beginPath(); hctx.arc(0, 0, pulseR * 4, 0, Math.PI * 2); hctx.fill();
  hctx.restore();
}

function renderHolo(now) {
  const dt = Math.min((now - lastT) / 1000, 0.05);
  lastT = now;
  const t = now / 1000;

  // 状态驱动参数
  let rotSpeed = 0.18, jitter = 0, coreBoost = 0.55 + 0.2 * Math.sin(t * 1.2), lineAlpha = 0.10;
  if (uiState === "listening") { rotSpeed = 0.3 + voiceLevel * 0.28; coreBoost = 0.7 + voiceLevel * 0.55 + 0.2 * Math.sin(t * 4); }
  else if (uiState === "thinking") { rotSpeed = 0.9; jitter = 0.012; lineAlpha = 0.2; coreBoost = 0.8 + 0.2 * Math.sin(t * 6); }
  else if (uiState === "speaking") { rotSpeed = 0.35; coreBoost = 0.75 + 0.45 * Math.abs(Math.sin(t * 9)); lineAlpha = 0.16; }
  // Connection status is deliberately not a visual power state. During a
  // relaunch the WebSocket can briefly alternate between OFFLINE and BOOTING;
  // dimming the canvas for only one of those states produced a visible full
  // palette flash. Keep the hologram's idle energy stable and use the text
  // status/connection dot to communicate connectivity instead.

  gAngle += rotSpeed * dt;
  const ax = 0.42 + Math.sin(t * 0.13) * 0.06; // 固定倾角 + 缓慢摆动
  const ay = gAngle;
  const dim = 1;

  hctx.clearRect(0, 0, HW, HH);
  hctx.globalCompositeOperation = "lighter";

  // 中心辉光
  const glow = hctx.createRadialGradient(CX, CY, 0, CX, CY, R * 0.85);
  glow.addColorStop(0, `rgba(255,190,90,${0.22 * coreBoost * dim})`);
  glow.addColorStop(1, "rgba(255,190,90,0)");
  hctx.globalAlpha = 1;
  hctx.fillStyle = glow;
  hctx.fillRect(0, 0, HW, HH);

  drawSphereGrid(ax, ay, t, dim, lineAlpha * 5);

  // Outer halo: sparse, slow particles create scale beyond the main shell.
  for (const p of dustPts) {
    const drift = 1 + 0.018 * Math.sin(t * 0.45 + p.ph);
    const pr = project({ x: p.x * drift, y: p.y * drift, z: p.z * drift }, ax * 0.7, -ay * 0.28);
    const tw = 0.25 + 0.75 * Math.max(0, Math.sin(t * 0.8 + p.ph));
    drawSprite(spriteGold, pr.sx, pr.sy, 2.2 + p.s * 2.8, tw * 0.24 * dim);
  }

  // Broken spatial arcs: incomplete geometry reads as assembled machinery,
  // rather than a set of simple complete circles.
  hctx.lineWidth = 1.05;
  for (const arc of spatialArcs) {
    hctx.beginPath();
    arc.pts.forEach((p, i) => {
      const pr = project(p, ax, ay + t * arc.speed);
      if (i === 0) hctx.moveTo(pr.sx, pr.sy); else hctx.lineTo(pr.sx, pr.sy);
    });
    hctx.strokeStyle = "rgba(255,189,78,1)";
    hctx.globalAlpha = arc.alpha * (0.55 + 0.45 * Math.sin(t * 1.2 + arc.ph)) * dim;
    hctx.stroke();
  }

  // Semi-transparent facets create fragmented volume between the point layers.
  for (const facet of shellFacets) {
    const projected = facet.verts.map(p => project(p, ax, ay * 0.93));
    const avgZ = projected.reduce((sum, p) => sum + p.z, 0) / 3;
    const flicker = 0.55 + 0.45 * Math.sin(t * 0.7 + facet.ph);
    hctx.beginPath(); hctx.moveTo(projected[0].sx, projected[0].sy);
    hctx.lineTo(projected[1].sx, projected[1].sy);
    hctx.lineTo(projected[2].sx, projected[2].sy); hctx.closePath();
    hctx.fillStyle = "rgba(255,157,34,1)";
    hctx.globalAlpha = facet.alpha * flicker * (0.45 + (avgZ + 1) * 0.3) * dim;
    hctx.fill();
    hctx.strokeStyle = "rgba(255,202,108,1)";
    hctx.globalAlpha *= 1.45; hctx.lineWidth = 0.55; hctx.stroke();
  }

  // Radial skeleton and moving pulses connect the core to selected shell nodes.
  for (let i = 0; i < spokeAnchors.length; i++) {
    const p = spokeAnchors[i];
    const inner = project({ x: p.x * 0.12, y: p.y * 0.12, z: p.z * 0.12 }, ax, ay);
    const outer = project(p, ax, ay);
    const energy = 0.5 + 0.5 * Math.sin(t * (uiState === "thinking" ? 6 : 1.8) + i * 1.7);
    hctx.beginPath(); hctx.moveTo(inner.sx, inner.sy); hctx.lineTo(outer.sx, outer.sy);
    hctx.strokeStyle = "rgba(255,171,44,1)";
    hctx.globalAlpha = (0.045 + energy * (uiState === "thinking" ? 0.2 : 0.105)) * dim;
    hctx.lineWidth = energy > 0.82 ? 1.25 : 0.55; hctx.stroke();
    const travel = (t * 0.32 + i * 0.137) % 1;
    drawSprite(spriteBright, inner.sx + (outer.sx - inner.sx) * travel,
      inner.sy + (outer.sy - inner.sy) * travel, 3.5 + energy * 3,
      energy * 0.38 * dim);
  }

  // 细丝（闪烁的电路线）
  hctx.lineWidth = 1;
  for (const f of filaments) {
    const k = Math.sin(t * f.sp + f.ph);
    if (k < 0.35) continue;
    const pa = project(f.a, ax, ay), pb = project(f.b, ax, ay);
    hctx.globalAlpha = (k - 0.35) * 0.5 * dim;
    hctx.strokeStyle = "rgba(255,200,110,1)";
    hctx.beginPath(); hctx.moveTo(pa.sx, pa.sy); hctx.lineTo(pb.sx, pb.sy); hctx.stroke();
  }

  // Tangent-shell mechanical modules. Unlike the former flat annular bands,
  // these faces sit on the orbit's outer shell: their normals point away from
  // the centre, and their thickness sinks back into the sphere.
  for (const ring of rings) {
    ring.angle += ring.speed * rotSpeed * 3 * dt;
    const orderedModules = ring.modules.map(module => ({
      module,
      depth: project(ringSurfacePoint(ring, ring.angle + module.th,
        module.normalShift, module.radialLift), ax, ay).z,
    })).sort((a, b) => a.depth - b.depth);

    for (const { module, depth } of orderedModules) {
      const flicker = 0.82 + 0.18 * Math.sin(t * 1.15 + module.pulse);
      const stateBoost = uiState === "thinking" ? 1.18 :
        uiState === "listening" ? 1 + voiceLevel * 0.24 : 1;
      let mount = null;

      // Draw recessed depth, face scatter, hard silhouette and circuit points
      // as separate light buckets. No filled or stroked module polygons remain.
      for (const group of [2, 0, 1, 3]) {
        hctx.beginPath();
        for (const sample of module.cloud) {
          if (sample.kind !== group) continue;
          const pr = projectModuleSample(ring, module, sample, ax, ay);
          const pointPulse = 0.88 + 0.12 * Math.sin(t * 1.8 + sample.phase);
          const groupScale = group === 2 ? 0.7 : group === 0 ? 0.86 :
            group === 3 ? 1.28 : 1.16;
          const radius = Math.max(0.42, sample.size * ring.dotScale * pr.persp *
            0.88 * groupScale * pointPulse);
          hctx.moveTo(pr.sx + radius, pr.sy);
          hctx.arc(pr.sx, pr.sy, radius, 0, Math.PI * 2);
          if (group === 3 && !mount) mount = pr;
        }
        hctx.fillStyle = group === 3 ? "rgba(255,245,207,1)" :
          group === 1 ? ring.edge : ring.fill;
        const groupAlpha = group === 2 ? 0.24 : group === 0 ? 0.46 :
          group === 1 ? 0.88 : 1;
        const depthLight = 0.62 + 0.38 * (depth + 1) / 2;
        hctx.globalAlpha = ring.cloudAlpha * groupAlpha * flicker * stateBoost *
          depthLight * dim;
        hctx.fill();
      }

      if (mount && (module.index + module.detail) % 2 === 0) {
        drawSprite(spriteBright, mount.sx, mount.sy,
          (3.2 + module.detail * 0.65) * mount.persp,
          (0.26 + lineAlpha) * flicker * dim);
      }
    }

    // Rails are assembled only across selected modules. Their offsets, dash
    // grammar and cadence differ for every orbit, avoiding five cloned circles.
    ring.rails.forEach((railOffset, railIndex) => {
      hctx.beginPath();
      ring.modules.forEach((module, moduleIndex) => {
        if ((moduleIndex + railIndex) % ring.railEvery !== 0) return;
        for (let sample = 0; sample <= 6; sample++) {
          const along = (sample / 6 - 0.5) * module.span * 0.78;
          const th = ring.angle + module.th + along;
          const normalOffset = module.normalShift * 0.24 +
            railOffset * ring.shellWidth * module.widthScale;
          const pr = project(ringSurfacePoint(ring, th, normalOffset,
            module.radialLift + 0.007), ax, ay);
          if (sample === 0) hctx.moveTo(pr.sx, pr.sy); else hctx.lineTo(pr.sx, pr.sy);
        }
      });
      hctx.strokeStyle = railIndex % 2 ? ring.fill : ring.edge;
      hctx.globalAlpha = (0.14 + lineAlpha * 1.05) * dim;
      hctx.lineWidth = Math.max(0.7, ring.railWidth - railIndex * 0.22);
      hctx.setLineDash(ring.railDash);
      hctx.lineDashOffset = (railIndex % 2 ? -1 : 1) * (ring.angle * 24 + railIndex * 7);
      hctx.stroke();
    });
    hctx.setLineDash([]);
  }

  // Fast luminous packets and short trails show active data movement.
  for (const sat of satellites) {
    const ring = rings[sat.ring];
    sat.th += sat.speed * (0.25 + rotSpeed) * dt;
    let head = null;
    hctx.beginPath();
    for (let j = 9; j >= 0; j--) {
      const th = sat.th - j * 0.022;
      const p = {
        x: (ring.u.x * Math.cos(th) + ring.v.x * Math.sin(th)) * ring.r,
        y: (ring.u.y * Math.cos(th) + ring.v.y * Math.sin(th)) * ring.r,
        z: (ring.u.z * Math.cos(th) + ring.v.z * Math.sin(th)) * ring.r,
      };
      const pr = project(p, ax, ay);
      if (j === 9) hctx.moveTo(pr.sx, pr.sy); else hctx.lineTo(pr.sx, pr.sy);
      if (j === 0) head = pr;
    }
    hctx.strokeStyle = "rgba(255,220,145,1)";
    hctx.globalAlpha = 0.24 * dim;
    hctx.lineWidth = 1.8; hctx.stroke();
    if (head) drawSprite(spriteBright, head.sx, head.sy, sat.size * head.persp,
      (uiState === "thinking" ? 0.95 : 0.62) * dim);
  }

  // 球壳粒子
  for (const p of spherePts) {
    const jx = jitter ? Math.sin(t * 7 + p.ph) * jitter : 0;
    const listenWave = uiState === "listening"
      ? 1 + voiceLevel * 0.065 * Math.sin(t * 9 + p.y * 8 + p.ph) : 1;
    const pr = project({ x: (p.x + jx) * listenWave, y: (p.y - jx) * listenWave,
      z: p.z * listenWave }, ax, ay);
    const tw = 0.6 + 0.4 * Math.sin(t * 2 + p.ph); // 闪烁
    const a = (0.16 + 0.66 * (pr.z + 1) / 2) * tw * dim;
    drawSprite(spriteGold, pr.sx, pr.sy, (2.6 + p.s * 2.6) * pr.persp, a);
  }

  // Inner shell moves against the outer sphere and becomes energetic while thinking.
  for (const p of innerPts) {
    const q = uiState === "thinking" ? 1 + 0.035 * Math.sin(t * 12 + p.ph) : 1;
    const pr = project({ x: p.x * q, y: p.y * q, z: p.z * q }, -ax * 0.7, -ay * 1.35);
    const tw = 0.25 + 0.75 * Math.max(0, Math.sin(t * 2.7 + p.ph));
    drawSprite(spriteGold, pr.sx, pr.sy, (2 + p.s * 2.8) * pr.persp,
      tw * (uiState === "thinking" ? 0.5 : 0.25) * dim);
  }

  // 核心团
  for (const p of corePts) {
    const pr = project(p, ax, ay * 1.6);
    const tw = 0.5 + 0.5 * Math.sin(t * 3 + p.ph);
    drawSprite(spriteBright, pr.sx, pr.sy, (3 + p.s * 4) * pr.persp, coreBoost * tw * dim);
  }


  drawCoreIris(t, coreBoost, dim);

  // Transcript acknowledgement: a short energy wave expands through the orb.
  for (let i = shockwaves.length - 1; i >= 0; i--) {
    const age = (now - shockwaves[i]) / 720;
    if (age >= 1) { shockwaves.splice(i, 1); continue; }
    const radius = R * (0.08 + age * 1.03);
    hctx.beginPath(); hctx.arc(CX, CY, radius, 0, Math.PI * 2);
    hctx.strokeStyle = "rgba(255,225,155,1)";
    hctx.lineWidth = 1.5 + (1 - age) * 2;
    hctx.globalAlpha = Math.sin(age * Math.PI) * 0.42 * dim;
    hctx.stroke();
  }

  hctx.globalCompositeOperation = "source-over";
  hctx.globalAlpha = 1;
  requestAnimationFrame(renderHolo);
}

// ---------------- boot ----------------
applyInterfaceLanguage(conversationLanguage);
setUiState("booting");
logLine("info", conversationLanguage === "zh" ? "HUD 初始化完成" : "HUD initialised.");
connect();
requestAnimationFrame(renderHolo);
