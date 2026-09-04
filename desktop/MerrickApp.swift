import AppKit
import WebKit
import Speech
import AVFoundation
import ObjectiveC
import CryptoKit
import CoreGraphics
import ScreenCaptureKit
import Darwin
import LocalAuthentication
import ApplicationServices
import Security
import UserNotifications

/// A generic "Contents/Resources/runtime" path is not a product identity.
/// The caller supplies the kernel's executable path, never command arguments.
private func merrickOwnsRuntimeExecutable(
    _ executablePath: String, currentRuntimePath: String, bundleID: String
) -> Bool {
    let executable = URL(fileURLWithPath: executablePath).resolvingSymlinksInPath().path
    let current = URL(fileURLWithPath: currentRuntimePath).resolvingSymlinksInPath().path
    if executable.hasPrefix(current + "/") { return true }
    guard let marker = executable.range(of: "/Contents/Resources/runtime/") else { return false }
    let appURL = URL(fileURLWithPath: String(executable[..<marker.lowerBound]))
    return Bundle(url: appURL)?.bundleIdentifier == bundleID
}

private func merrickRuntimeExecutablePath(_ pid: pid_t) -> String? {
    // proc_info.h defines PROC_PIDPATHINFO_MAXSIZE as 4 * MAXPATHLEN;
    // Swift cannot import that expression macro directly.
    var buffer = [CChar](repeating: 0, count: 4 * Int(MAXPATHLEN))
    guard proc_pidpath(pid, &buffer, UInt32(buffer.count)) > 0 else { return nil }
    return String(cString: buffer)
}

/// All native entry points use the app's private state, even when launched
/// from a shell configured for a user's independent OpenClaw installation.
private func merrickApplyOpenClawIsolation(
    _ environment: inout [String: String], stateDirectory: URL, workspaceDirectory: URL
) {
    for key in Array(environment.keys) where key.hasPrefix("OPENCLAW_") {
        environment.removeValue(forKey: key)
    }
    environment["OPENCLAW_STATE_DIR"] = stateDirectory.path
    environment["OPENCLAW_CONFIG_PATH"] = stateDirectory.appendingPathComponent("openclaw.json").path
    environment["OPENCLAW_TOKEN_FILE"] = stateDirectory.appendingPathComponent(".gateway-token").path
    environment["OPENCLAW_ACTION_SECRET_FILE"] = stateDirectory.appendingPathComponent(".action-secret").path
    environment["JARVIS_WORKSPACE_DIR"] = workspaceDirectory.path
}

/// Small local bridge to the Python WebRTC audio processor.  The process has
/// no network access in this design: it receives PCM over stdin and returns
/// PCM over stdout.  Keeping it out of the CoreAudio callback is essential;
/// file-pipe writes can block and must never run on the real-time audio thread.
private final class AudioIsolationWorker {
    struct Result {
        let generation: Int
        let session: Int
        let samples: [Int16]
        let speechProbability: Double
        let farRMS: Double
        let nearRMS: Double
        let cleanRMS: Double
        let playbackSuppressed: Bool
        let doubleTalkRestored: Bool
        let doubleTalkGain: Double
    }

    private let queue = DispatchQueue(label: "ai.jarvis.audio-isolation")
    private var process: Process?
    private var input: FileHandle?
    private var outputBuffer = Data()
    private var pendingFrames = 0
    private var resultHandler: ((Result) -> Void)?
    private var failureHandler: ((String) -> Void)?
    private(set) var isReady = false

    func start(python: URL, script: URL, result: @escaping (Result) -> Void, failure: @escaping (String) -> Void) {
        queue.async { [weak self] in
            guard let self, self.process == nil else { return }
            guard FileManager.default.isExecutableFile(atPath: python.path),
                  FileManager.default.fileExists(atPath: script.path) else {
                failure("local_audio_worker_missing")
                return
            }
            let stdin = Pipe()
            let stdout = Pipe()
            let process = Process()
            process.executableURL = python
            process.arguments = [script.path]
            process.standardInput = stdin
            process.standardOutput = stdout
            process.standardError = Pipe()
            self.resultHandler = result
            self.failureHandler = failure
            stdout.fileHandleForReading.readabilityHandler = { [weak self] handle in
                let data = handle.availableData
                guard !data.isEmpty else { return }
                self?.consumeOutput(data)
            }
            process.terminationHandler = { [weak self] process in
                self?.queue.async {
                    guard let self else { return }
                    self.isReady = false
                    self.process = nil
                    self.input = nil
                    self.pendingFrames = 0
                    self.failureHandler?("local_audio_worker_exit_\(process.terminationStatus)")
                }
            }
            do {
                try process.run()
                self.process = process
                self.input = stdin.fileHandleForWriting
                self.isReady = true
            } catch {
                self.failureHandler?("local_audio_worker_start_failed")
            }
        }
    }

    func stop() {
        // Application termination cannot leave this queued behind the process
        // exit. Drain it synchronously and keep the wait strictly bounded.
        queue.sync {
            self.isReady = false
            self.input?.closeFile()
            if let process = self.process, process.isRunning {
                process.terminate()
                let deadline = Date().addingTimeInterval(0.75)
                while process.isRunning && Date() < deadline {
                    Thread.sleep(forTimeInterval: 0.025)
                }
                if process.isRunning {
                    self.failureHandler?("audio_worker_force_kill")
                    Darwin.kill(process.processIdentifier, SIGKILL)
                    process.waitUntilExit()
                }
            }
            self.process = nil
            self.input = nil
            self.pendingFrames = 0
        }
    }

    /// Returns false before a write if the worker would accumulate more than
    /// about 250 ms of backlog.  The caller disables isolation for that turn
    /// and immediately falls back to the proven raw path instead of adding
    /// speech latency.
    func submit(
        kind: String,
        samples: [Int16],
        generation: Int,
        session: Int,
        assistantAudioPlaying: Bool = false
    ) -> Bool {
        guard !samples.isEmpty else { return false }
        queue.async { [weak self] in
            guard let self, self.isReady, let input = self.input else { return }
            if kind == "near" && self.pendingFrames >= 12 {
                self.isReady = false
                self.failureHandler?("local_audio_worker_backlog")
                return
            }
            if kind == "near" { self.pendingFrames += 1 }
            let pcm = samples.withUnsafeBufferPointer { Data(buffer: $0) }.base64EncodedString()
            let message: [String: Any] = [
                "kind": kind, "generation": generation, "session": session, "pcm": pcm,
                "assistant_audio_playing": assistantAudioPlaying,
            ]
            guard let data = try? JSONSerialization.data(withJSONObject: message) else { return }
            input.write(data)
            input.write(Data([0x0A]))
        }
        return isReady
    }

    private func consumeOutput(_ data: Data) {
        queue.async { [weak self] in
            guard let self else { return }
            self.outputBuffer.append(data)
            while let newline = self.outputBuffer.firstIndex(of: 0x0A) {
                let line = self.outputBuffer.prefix(upTo: newline)
                self.outputBuffer.removeSubrange(...newline)
                guard let object = try? JSONSerialization.jsonObject(with: line) as? [String: Any],
                      object["kind"] as? String == "near_result",
                      let encoded = object["pcm"] as? String,
                      let pcm = Data(base64Encoded: encoded) else { continue }
                self.pendingFrames = max(0, self.pendingFrames - 1)
                let samples = pcm.withUnsafeBytes { raw -> [Int16] in
                    Array(raw.bindMemory(to: Int16.self))
                }
                self.resultHandler?(Result(
                    generation: object["generation"] as? Int ?? -1,
                    session: object["session"] as? Int ?? -1,
                    samples: samples,
                    speechProbability: object["speech_probability"] as? Double ?? 0,
                    farRMS: object["far_rms"] as? Double ?? 0,
                    nearRMS: object["near_rms"] as? Double ?? 0,
                    cleanRMS: object["clean_rms"] as? Double ?? 0,
                    playbackSuppressed: object["playback_suppressed"] as? Bool ?? false,
                    doubleTalkRestored: object["double_talk_restored"] as? Bool ?? false,
                    doubleTalkGain: object["double_talk_gain"] as? Double ?? 1
                ))
            }
        }
    }
}

private struct ProviderProfile: Codable {
    let provider: String
    let model: String
    let baseURL: String?
    let authMode: String
    let updatedAt: Date
}

private struct AutomationAccessProfile: Codable {
    let enabled: Bool
    let root: String?
    let updatedAt: Date
}

private enum GUIInteractionStep {
    case click(x: Int, y: Int)
    case scroll(dy: Int)
    case key(String)
    case type(String)
}

private enum NativeAction {
    case openApp(alias: String)
    case closeApp(alias: String)
    case browserSearch(browser: String, query: String)
    case browserOpenURL(browser: String, url: URL)
    case mapsSearch(query: String)
    case spotifySearch(query: String)
    case mediaControl(player: String, action: String)
    case playMusic(query: String)
    case volumeControl(action: String)
    case guiInteraction(steps: [GUIInteractionStep])
}

private final class ResearchPageDelegate: NSObject, WKNavigationDelegate {
    func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        guard let url = navigationAction.request.url,
              ["https", "http"].contains(url.scheme?.lowercased() ?? "") else {
            decisionHandler(.cancel); return
        }
        decisionHandler(.allow)
    }
}

/// Borderless AppKit windows do not become key or main by default. MERRICK
/// must opt in so a mouse click can hand first-responder status to WKWebView
/// form controls and accept keyboard input immediately.
private final class MerrickHUDWindow: NSWindow {
    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { true }
}

private enum MerrickWindowFullscreenMode: String {
    case normal
    case entering
    case fullscreen
    case exiting
}

final class MerrickController: NSObject, NSApplicationDelegate, NSWindowDelegate, WKScriptMessageHandler, WKNavigationDelegate, SCStreamOutput, SCStreamDelegate, UNUserNotificationCenterDelegate {
    private var window: NSWindow!
    private var webView: WKWebView!
    private var windowFullscreenMode: MerrickWindowFullscreenMode = .normal
    private var pendingFullscreenRequestID: String?
    private var fullscreenRestoreLevel: NSWindow.Level = .floating
    private var fullscreenRestoreCollectionBehavior: NSWindow.CollectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
    // en-US currently has broader on-device/runtime availability than en-GB.
    // This affects recognition only; MERRICK still speaks with a British voice.
    private var recognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
    private let speechLanguagePreferenceKey = "JarvisSpeechLanguage"
    private let ownerAddressEnglishKey = "JarvisOwnerAddressEnglish"
    private let ownerAddressChineseKey = "JarvisOwnerAddressChinese"
    private var speechLanguage = UserDefaults.standard.string(forKey: "JarvisSpeechLanguage") == "zh" ? "zh" : "en"
    // Keep one input engine alive for the lifetime of the app. The engine's
    // voice-processing mode is changed only while it is stopped: CoreAudio
    // rejects dynamic changes and can otherwise leave the input format stale.
    private let audioEngine = AVAudioEngine()
    private var request: SFSpeechAudioBufferRecognitionRequest?
    private var task: SFSpeechRecognitionTask?
    private var restartingSpeech = false
    private var lastLevelUpdate: CFAbsoluteTime = 0
    private var recognitionGeneration = 0
    private let audioFrameLock = NSLock()
    private var audioFrameGenerations = Set<Int>()
    private let voiceSampleLock = NSLock()
    private var voiceSamples: [Float] = []
    private var voiceResampleCursor: Double = 0
    // A first short capture can become too short after local VAD removes
    // silence. Send a fast presentation sample followed by two longer,
    // in-memory snapshots for each recognition generation. The backend keeps
    // the best full-verification score, so a brief vocal variation does not
    // make a later sample undo a valid owner match.
    private var voiceSampleEmissionCount = 0
    private let voiceSampleEmissionThresholds: [(seconds: Double, tier: String)] = [
        (0.8, "fast"),
        (2.4, "full"),
        (3.8, "full_retry"),
    ]
    // Samples are armed only after the recognizer first detects this utterance;
    // otherwise an idle rolling buffer makes background sound look like speech.
    private var voiceSampleCaptureArmedGeneration = -1
    private var voiceSampleSuppressedGeneration = -1
    private var voiceTurnSentGeneration = -1
    // Manual enrollment is deliberately separate from the conversational
    // recognizer.  During this short capture no transcript or live sample is
    // sent, so reading the enrollment phrase cannot accidentally start a turn.
    private var manualVoiceprintCaptureRequested = false
    private var manualVoiceprintCaptureGeneration = -1
    private var manualVoiceprintCaptureWorkItem: DispatchWorkItem?
    private var voiceprintManagementAuthorizedUntil: Date?
    private var assistantAudioPlaying = false
    // Local full-duplex audio path.  ScreenCaptureKit provides a *playback
    // reference*, never a recording.  That reference is paired with the mic
    // inside WebRTC AEC3 so speaker output/music is not mistaken for a user
    // interruption.  If it is unavailable, recognition immediately keeps the
    // existing raw-input behaviour rather than becoming silent.
    private let audioIsolation = AudioIsolationWorker()
    private let playbackReferenceQueue = DispatchQueue(label: "ai.jarvis.playback-reference")
    private var playbackReferenceStream: SCStream?
    private var playbackReferenceRequested = false
    // Normal conversation needs the same system-output reference as Watch and
    // Meeting modes. Activate it after the first authorised listening request
    // and keep it warm for this app session so media between turns cannot slip
    // through a capture restart window. Set JARVIS_SYSTEM_AUDIO_FILTER_V1=0
    // only as an emergency rollback on a machine with an incompatible driver.
    private var systemAudioFilterActivated = false
    private let systemAudioFilterAllowed =
        ProcessInfo.processInfo.environment["JARVIS_SYSTEM_AUDIO_FILTER_V1"] != "0"
    private var watchAudioModeEnabled = false
    private var meetingAudioModeEnabled = false
    private var watchVoiceVerificationGeneration = -1
    private var playbackReferenceStarting = false
    private var audioIsolationEnabled = false
    private var audioIsolationReadyForBarge = false
    private var audioIsolationSession = 0
    private var screenAudioPermissionPrompted = false
    private var audioIsolationResultCount = 0
    private var audioIsolationSuppressedFrameCount = 0
    private var audioIsolationRestoredFrameCount = 0
    private var systemPlaybackActive = false
    private var systemPlaybackLoudFrames = 0
    private var systemPlaybackQuietFrames = 0
    private var audioIsolationFallbackTracedSession = -1
    private var audioIsolationNearSubmittedSession = -1
    private var cleanBargeCandidateFrames = 0
    private var cleanVoiceQuietFrames = 0
    private var cleanVoiceActivityActive = false
    private let voiceSampleRate = 16_000.0
    private let voiceSampleRetention = 8 * 16_000
    private var audioWatchdogRetries = 0
    private var audioStartFailures = 0
    private var inputTapInstalled = false
    private var backend: Process?
    private var backendProcessGroup: pid_t?
    private var projectRoot: URL!
    private var webReady = false
    private var hudLoadStarted = false
    private var webLoadAttempts = 0
    private var backendHealthTask: URLSessionDataTask?
    private var backendStartupDeadline: Date?
    private var backendStartupAttempts = 0
    private var backendRecoveryScheduled = false
    private var backendRecoveryHistory: [Date] = []
    private var webReadyTimeoutWorkItem: DispatchWorkItem?
    private var startupErrorLabel: NSTextField?
    private var appTerminating = false
    private var terminationCleanupStarted = false
    private let bridgeToken = UUID().uuidString.replacingOccurrences(of: "-", with: "")
    private let bridgeChallenge = UUID().uuidString.replacingOccurrences(of: "-", with: "").lowercased()
    private let backendStartupTimeout: TimeInterval = 30
    private let maximumBackendStartupAttempts = 2
    private let maximumBackendRecoveriesPerWindow = 3
    private let backendRecoveryWindow: TimeInterval = 300
    private let webReadyTimeout: TimeInterval = 15
    private let maximumWebLoadAttempts = 2
    private let providerKeychainService = "ai.jarvis.desktop.provider-credentials"
    private let providerProfileFilename = "provider-profile.json"
    private let providerConnectionFilename = "provider-connection.json"
    private let automationAccessFilename = "automation-access.json"
    private let onboardingCompletedKey = "JarvisProviderOnboardingCompleted"
    private var providerLoginProcess: Process?
    private var providerLoginProcessGroup: pid_t?
    private var providerValidationProcess: Process?
    private var providerValidationProcessGroup: pid_t?
    private var openClawDashboardProcess: Process?
    private var openClawDashboardProcessGroup: pid_t?
    private var uninstallerProcess: Process?
    private var providerLoginOutput = ""
    private var providerVerificationURL: URL?
    private var providerPresentedDeviceCode: String?
    private var providerPendingSelection: (provider: String, model: String)?
    private var researchWindows: [NSWindow] = []
    private var researchDelegates: [ResearchPageDelegate] = []
    private var memoryExportInProgress = false
    private let windowPositionXKey = "JarvisWindowPositionX"
    private let windowPositionYKey = "JarvisWindowPositionY"
    private let maximumScreenCaptureBytes = 4_000_000
    private let maximumScreenCaptureDimension = 1_600
    private var screenCaptureInFlight: String?
    private var nativeActionInFlight: String?
    private var nativeActionProcess: Process?
    private var nativeActionTimeoutWorkItem: DispatchWorkItem?
    private var nativeActionKillWorkItem: DispatchWorkItem?
    private let nativeActionTimeout: TimeInterval = 20
    private var lastExternalFrontmostPID: pid_t?

    private let knownApplicationBundleIDs = [
        "calendar": "com.apple.iCal",
        "chatgpt": "com.openai.codex",
        "chrome": "com.google.Chrome",
        "claude": "com.anthropic.claudefordesktop",
        "maps": "com.apple.Maps",
        "messages": "com.apple.MobileSMS",
        "music": "com.apple.Music",
        "notes": "com.apple.Notes",
        "outlook": "com.microsoft.Outlook",
        "safari": "com.apple.Safari",
        "spotify": "com.spotify.client",
    ]
    private let applicationNameAliases = [
        "apple maps": "maps",
        "map": "maps",
        "google chrome": "chrome",
        "apple music": "music",
        "imessage": "messages",
        "vs code": "visual studio code",
        "vscode": "visual studio code",
        "keynote": "keynote creator studio",
        "numbers": "numbers creator studio",
        "pages": "pages creator studio",
    ]

    private let mediaScripts = [
        "music": [
            "play": "tell application \"Music\" to play",
            "pause": "tell application \"Music\" to pause",
            "toggle": "tell application \"Music\" to playpause",
            "next": "tell application \"Music\" to next track",
            "previous": "tell application \"Music\" to previous track",
        ],
        "spotify": [
            "play": "tell application \"Spotify\" to play",
            "pause": "tell application \"Spotify\" to pause",
            "toggle": "tell application \"Spotify\" to playpause",
            "next": "tell application \"Spotify\" to next track",
            "previous": "tell application \"Spotify\" to previous track",
        ],
    ]
    private let pauseActiveMediaScript = """
    if application "Spotify" is running then
      tell application "Spotify"
        if player state is playing then
          pause
          return
        end if
      end tell
    end if
    if application "Music" is running then
      tell application "Music"
        if player state is playing then pause
      end tell
    end if
    """

    private let playMusicByNameScript = """
    on run argv
      set requestedName to item 1 of argv
      tell application "Music"
        set matchingTracks to search library playlist 1 for requestedName only songs
        if (count of matchingTracks) is 0 then error "No matching song was found in the Music library."
        play item 1 of matchingTracks
      end tell
    end run
    """
    private let volumeScripts = [
        "up": "set currentVolume to output volume of (get volume settings)\nset volume output volume (currentVolume + 10)",
        "down": "set currentVolume to output volume of (get volume settings)\nset volume output volume (currentVolume - 10)",
        "mute": "set volume with output muted",
        "unmute": "set volume without output muted",
    ]

    private func nativeTrace(_ event: String) {
        let line = "\(ISO8601DateFormatter().string(from: Date())) \(event)\n"
        let url = URL(fileURLWithPath: "/tmp/jarvis-native.log")
        if !FileManager.default.fileExists(atPath: url.path) {
            try? line.write(to: url, atomically: true, encoding: .utf8)
        } else if let handle = try? FileHandle(forWritingTo: url) {
            defer { try? handle.close() }
            _ = try? handle.seekToEnd()
            try? handle.write(contentsOf: Data(line.utf8))
        }
    }

    // Keep a short, local-only 16 kHz rolling window.  It shares the existing
    // microphone tap and never touches disk; a clipped WAV is sent only to the
    // loopback backend for the enrolled-owner verifier.
    private func captureVoiceSamples(_ buffer: AVAudioPCMBuffer) {
        guard let channel = buffer.floatChannelData?[0] else { return }
        let sourceRate = buffer.format.sampleRate
        let frameCount = Int(buffer.frameLength)
        guard sourceRate >= 8_000, frameCount > 0 else { return }
        let step = sourceRate / voiceSampleRate
        voiceSampleLock.lock()
        var cursor = voiceResampleCursor
        while cursor < Double(frameCount) {
            voiceSamples.append(channel[min(Int(cursor), frameCount - 1)])
            cursor += step
        }
        voiceResampleCursor = cursor - Double(frameCount)
        if voiceSamples.count > voiceSampleRetention * 2 {
            voiceSamples.removeFirst(voiceSamples.count - voiceSampleRetention)
        }
        voiceSampleLock.unlock()
    }

    private func appendLittleEndian<T: FixedWidthInteger>(_ value: T, to data: inout Data) {
        var littleEndian = value.littleEndian
        withUnsafeBytes(of: &littleEndian) { data.append(contentsOf: $0) }
    }

    private func currentVoiceSampleBase64(minimumSeconds: Double) -> String? {
        voiceSampleLock.lock()
        let frameCount = min(voiceSamples.count, Int(voiceSampleRate * 4.5))
        let samples = frameCount > 0 ? Array(voiceSamples.suffix(frameCount)) : []
        voiceSampleLock.unlock()
        guard samples.count >= Int(voiceSampleRate * minimumSeconds) else { return nil }
        var wav = Data()
        let pcmBytes = samples.count * MemoryLayout<Int16>.size
        wav.append("RIFF".data(using: .ascii)!)
        appendLittleEndian(UInt32(36 + pcmBytes), to: &wav)
        wav.append("WAVEfmt ".data(using: .ascii)!)
        appendLittleEndian(UInt32(16), to: &wav)
        appendLittleEndian(UInt16(1), to: &wav)
        appendLittleEndian(UInt16(1), to: &wav)
        appendLittleEndian(UInt32(voiceSampleRate), to: &wav)
        appendLittleEndian(UInt32(voiceSampleRate * 2), to: &wav)
        appendLittleEndian(UInt16(2), to: &wav)
        appendLittleEndian(UInt16(16), to: &wav)
        wav.append("data".data(using: .ascii)!)
        appendLittleEndian(UInt32(pcmBytes), to: &wav)
        for sample in samples {
            let scaled = max(-1.0, min(1.0, sample)) * Float(Int16.max)
            appendLittleEndian(Int16(scaled.rounded()), to: &wav)
        }
        return wav.base64EncodedString()
    }

    private func emitVoiceSample(for generation: Int, emissionIndex: Int) {
        let allowCleanWatchVerification = watchAudioModeEnabled &&
            watchVoiceVerificationGeneration == generation
        guard generation == recognitionGeneration,
              (!assistantAudioPlaying || allowCleanWatchVerification),
              voiceSampleSuppressedGeneration != generation,
              voiceSampleCaptureArmedGeneration == generation,
              emissionIndex < voiceSampleEmissionThresholds.count,
              voiceSampleEmissionCount <= emissionIndex else { return }
        let emission = voiceSampleEmissionThresholds[emissionIndex]
        guard let sample = currentVoiceSampleBase64(minimumSeconds: emission.seconds) else { return }
        voiceSampleEmissionCount = max(voiceSampleEmissionCount, emissionIndex + 1)
        nativeTrace("voice.sample_sent generation=\(generation) attempt=\(emissionIndex + 1) tier=\(emission.tier) seconds=\(emission.seconds)")
        js("window.merrickNativeVoiceSample(\(jsString(sample)), \(jsString(emission.tier)))")
    }

    private func beginWatchVoiceVerification(for generation: Int) {
        guard watchAudioModeEnabled,
              generation == recognitionGeneration,
              watchVoiceVerificationGeneration != generation else { return }
        watchVoiceVerificationGeneration = generation
        voiceTurnSentGeneration = generation
        voiceSampleLock.lock()
        // This is called only after AEC has confirmed nearby clean speech.
        // Discard the preceding speaker/reference audio and enrol the verifier
        // from the following cleaned microphone frames only.
        voiceSamples.removeAll(keepingCapacity: true)
        voiceResampleCursor = 0
        voiceSampleEmissionCount = 0
        voiceSampleCaptureArmedGeneration = generation
        voiceSampleSuppressedGeneration = -1
        voiceSampleLock.unlock()
        nativeTrace("watch.voice_verification_started generation=\(generation)")
        js("window.merrickNativeVoiceTurn(\(generation))")
        scheduleVoiceSampleEmissions(for: generation)
    }

    private func scheduleVoiceSampleEmissions(for generation: Int) {
        for (index, emission) in voiceSampleEmissionThresholds.enumerated() {
            // Recognition callbacks can pause after the final word in a short
            // greeting, while the microphone tap continues. Schedule from
            // speech detection so this does not depend on another ASR event.
            DispatchQueue.main.asyncAfter(deadline: .now() + emission.seconds + 0.05) { [weak self] in
                self?.emitVoiceSample(for: generation, emissionIndex: index)
            }
        }
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        // A Finder DMG deliberately contains a runnable app so users can drag
        // it to Applications, but double-clicking that source copy must never
        // start a second private runtime. Hand off to the verified installed
        // bundle before acquiring the singleton or creating local state.
        if redirectInstallerVolumeLaunchIfNeeded() {
            NSApp.terminate(nil)
            return
        }
        // A user can easily have both the DMG/staging copy and the copy in
        // Applications.  They share private state and the fixed loopback port,
        // so a second host must focus the first rather than starting a second
        // backend which immediately dies with address-in-use.
        if redirectToExistingInstanceIfNeeded() {
            NSApp.terminate(nil)
            return
        }
        UNUserNotificationCenter.current().delegate = self
        rememberFrontmostApplication()
        NSWorkspace.shared.notificationCenter.addObserver(
            self,
            selector: #selector(workspaceApplicationActivated(_:)),
            name: NSWorkspace.didActivateApplicationNotification,
            object: nil
        )
        // Release builds carry the complete local runtime inside the app
        // bundle. Keep the parent-directory fallback only for developers who
        // run the app directly from this source checkout.
        let bundledRuntime = Bundle.main.resourceURL?.appendingPathComponent("runtime", isDirectory: true)
        if let bundledRuntime, FileManager.default.fileExists(atPath: bundledRuntime.path) {
            projectRoot = bundledRuntime
        } else {
            projectRoot = Bundle.main.bundleURL
                .deletingLastPathComponent().deletingLastPathComponent()
        }
        // The Gateway profile is application-owned and intentionally contains
        // no credentials.  Refresh it before the backend starts so capability
        // upgrades ship with the app rather than waiting for a later provider
        // change to recreate the private runtime configuration.
        synchronizeProviderGatewayTemplate()
        synchronizeOpenClawWorkspaceIdentity()
        migrateLegacyUserWorkspaceArtifacts()
        reclaimOrphanedRuntimeProcesses()
        buildWindow()
        startBackend()
        requestPermissions()
    }

    private func redirectInstallerVolumeLaunchIfNeeded() -> Bool {
        let currentPath = Bundle.main.bundleURL.standardizedFileURL.path
        guard currentPath.hasPrefix("/Volumes/") else { return false }

        let installedURL = URL(
            fileURLWithPath: "/Applications/MERRICK.app",
            isDirectory: true
        )
        guard FileManager.default.fileExists(atPath: installedURL.path),
              let installedBundle = Bundle(url: installedURL),
              installedBundle.bundleIdentifier == Bundle.main.bundleIdentifier else {
            let alert = NSAlert()
            alert.alertStyle = .informational
            alert.messageText = "Install MERRICK first"
            alert.informativeText = "Drag MERRICK to Applications, then open the copy in Applications."
            alert.addButton(withTitle: "Show Installer")
            alert.runModal()
            NSWorkspace.shared.activateFileViewerSelecting([Bundle.main.bundleURL])
            nativeTrace("installer_launch_blocked installed_copy_missing")
            return true
        }

        // Wait for this source process to complete its normal termination so
        // Launch Services cannot coalesce the installed launch back into the
        // DMG instance. The helper is bounded to five seconds and then execs
        // `open`, so it never becomes a persistent gateway or background job.
        let currentPID = ProcessInfo.processInfo.processIdentifier
        let launcher = Process()
        launcher.executableURL = URL(fileURLWithPath: "/bin/zsh")
        launcher.arguments = [
            "-c",
            "for _ in {1..100}; do /bin/kill -0 \(currentPID) >/dev/null 2>&1 || break; /bin/sleep 0.05; done; exec /usr/bin/open '/Applications/MERRICK.app'",
        ]
        launcher.standardOutput = FileHandle.nullDevice
        launcher.standardError = FileHandle.nullDevice
        do {
            try launcher.run()
            nativeTrace("installer_launch_redirected target=Applications")
        } catch {
            let alert = NSAlert()
            alert.alertStyle = .warning
            alert.messageText = "Open MERRICK from Applications"
            alert.informativeText = error.localizedDescription
            alert.addButton(withTitle: "OK")
            alert.runModal()
            nativeTrace("installer_launch_redirect_failed error=\(error.localizedDescription)")
        }
        return true
    }

    /// Launch Services normally coalesces same-bundle launches, but that is
    /// not guaranteed while a user opens a second copy directly from a mounted
    /// image or development folder.  Redirect before creating a window,
    /// prompting for permissions, or reserving the backend port.
    private func redirectToExistingInstanceIfNeeded() -> Bool {
        guard let bundleIdentifier = Bundle.main.bundleIdentifier else { return false }
        let currentPID = ProcessInfo.processInfo.processIdentifier
        let existing = NSRunningApplication
            .runningApplications(withBundleIdentifier: bundleIdentifier)
            .first { application in
                application.processIdentifier != currentPID && !application.isTerminated
            }
        guard let existing else { return false }
        _ = existing.activate(options: [.activateAllWindows])
        nativeTrace("app.duplicate_launch_redirected existing_pid=\(existing.processIdentifier)")
        return true
    }

    private func rememberFrontmostApplication() {
        guard let application = NSWorkspace.shared.frontmostApplication,
              application.processIdentifier != ProcessInfo.processInfo.processIdentifier else {
            return
        }
        lastExternalFrontmostPID = application.processIdentifier
    }

    @objc private func workspaceApplicationActivated(_ notification: Notification) {
        guard let application = notification.userInfo?[NSWorkspace.applicationUserInfoKey]
                as? NSRunningApplication,
              application.processIdentifier != ProcessInfo.processInfo.processIdentifier else {
            return
        }
        lastExternalFrontmostPID = application.processIdentifier
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        bringHUDToPrimaryScreen()
        NSApp.activate(ignoringOtherApps: true)
        nativeTrace("app.reopen_focused visible_before=\(flag)")
        return true
    }

    func applicationDidBecomeActive(_ notification: Notification) {
        guard window != nil else { return }
        bringHUDToPrimaryScreen()
    }

    private func startBackend() {
        guard !appTerminating else { return }
        backendStartupAttempts += 1
        let process = Process()
        process.currentDirectoryURL = projectRoot
        // Launch Uvicorn directly from the project virtual environment. Using
        // `uv run` here leaves a wrapper process between the app and Uvicorn;
        // when the wrapper is terminated during Quit, its OpenClaw descendant
        // can survive as an orphan and block the next launch.
        let venvPython = projectRoot.appendingPathComponent(".venv/bin/python")
        let uvicornArguments = [
            "-m", "uvicorn", "main:app", "--app-dir", "server",
            "--host", RuntimeContract.backendHost,
            "--port", String(RuntimeContract.backendPort),
        ]
        if FileManager.default.isExecutableFile(atPath: venvPython.path) {
            process.executableURL = venvPython
            process.arguments = uvicornArguments
        } else {
            // Keep a setup-time fallback for a freshly cloned project before
            // its local virtual environment has been created.
            process.executableURL = URL(fileURLWithPath: "/usr/bin/env")
            process.arguments = ["uv", "run"] + uvicornArguments
        }
        var env = ProcessInfo.processInfo.environment
        env["PATH"] = NSHomeDirectory() + "/.local/bin:/opt/homebrew/bin:/usr/local/bin:" + (env["PATH"] ?? "")
        // The release backend runs from the signed application bundle.  Python
        // must never write __pycache__ files there, or a normal conversation
        // would mutate sealed resources and invalidate the app signature.
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        // The capability adapter is additive and read-only in its first
        // release. Keep its code-level default off so emergency rollback can
        // remove the enriched catalog without changing the OpenClaw runtime.
        env["JARVIS_CAPABILITY_ADAPTER_V1"] = "true"
        // M0 exposes only a private, persistent Harness vault status. Generated
        // plugin execution remains locked behind a separate future runtime flag.
        env["JARVIS_HARNESS_MODE_V1"] = "true"
        // A developer running dist/ from this checkout keeps the existing
        // private Git memory backup. A distributed app has no surrounding Git
        // repository, so the backup script falls back to Application Support
        // instead of ever writing private memory into the signed bundle.
        let checkoutRoot = Bundle.main.bundleURL
            .deletingLastPathComponent().deletingLastPathComponent()
        if FileManager.default.fileExists(atPath: checkoutRoot.appendingPathComponent(".git").path) {
            env["JARVIS_MEMORY_BACKUP_REPOSITORY"] = checkoutRoot.path
        }
        let bundledNodeDirectory = projectRoot.appendingPathComponent("node/bin", isDirectory: true)
        if FileManager.default.isExecutableFile(atPath: bundledNodeDirectory.appendingPathComponent("node").path) {
            // OpenClaw's ownership verifier must fingerprint the same embedded
            // Node executable that the runtime launcher selects. The managed
            // Codex app-server is a JavaScript executable with an
            // `/usr/bin/env node` shebang, so NODE_BIN_DIR alone is not
            // sufficient: its child environment must also resolve `node`.
            env["NODE_BIN_DIR"] = bundledNodeDirectory.path
            env["PATH"] = bundledNodeDirectory.path + ":" + projectRoot
                .appendingPathComponent("node_modules/.bin").path + ":" + (env["PATH"] ?? "")
        }
        env["JARVIS_BRIDGE_TOKEN"] = bridgeToken
        // Let the backend terminate itself if the native HUD crashes instead
        // of leaving an orphan process that prevents the next launch.
        env["JARVIS_APP_PARENT_PID"] = String(ProcessInfo.processInfo.processIdentifier)
        applyProviderEnvironment(&env)
        process.environment = env
        process.terminationHandler = { [weak self] finished in
            DispatchQueue.main.async {
                guard let self, !self.appTerminating, self.backend === finished else { return }
                self.backendHealthTask?.cancel()
                self.backendHealthTask = nil
                let detail = finished.terminationReason == .exit
                    ? "exit status \(finished.terminationStatus)"
                    : "signal \(finished.terminationStatus)"
                self.nativeTrace("backend.terminated \(detail)")
                self.recoverBackendStartup(reason: "terminated_\(finished.terminationStatus)")
            }
        }
        do {
            try process.run()
            // Keep every backend descendant inside one native-owned process
            // group. OpenClaw and the TTS worker inherit this group, giving
            // Quit a final bounded cleanup boundary even if graceful FastAPI
            // shutdown itself is interrupted.
            if Darwin.getpgid(process.processIdentifier) != process.processIdentifier {
                _ = Darwin.setpgid(process.processIdentifier, process.processIdentifier)
            }
            if Darwin.getpgid(process.processIdentifier) == process.processIdentifier {
                backendProcessGroup = process.processIdentifier
            } else {
                backendProcessGroup = nil
                nativeTrace("backend.process_group_unavailable pid=\(process.processIdentifier)")
            }
            backend = process
            nativeTrace("backend.started pid=\(process.processIdentifier)")
            let deadline = Date().addingTimeInterval(backendStartupTimeout)
            backendStartupDeadline = deadline
            pollBackendHealth(until: deadline)
        } catch {
            backend = nil
            nativeTrace("backend.launch_failed error=\(error.localizedDescription)")
            recoverBackendStartup(reason: "launch_failed")
        }
    }

    /// A hard crash can prevent `applicationWillTerminate` from running.  The
    /// backend does watch its native parent, but this narrow launch-time sweep
    /// also handles the short window before that watcher wakes up.  It only
    /// touches a same-user process which is already orphaned (PPID 1) and
    /// whose exact command belongs to this bundled MERRICK runtime.
    /// Independent OpenClaw/Codex processes can never match these paths.
    private func reclaimOrphanedRuntimeProcesses() {
        guard projectRoot != nil else { return }
        let backendPython = projectRoot.appendingPathComponent(".venv/bin/python").path
        let workerScript = projectRoot.appendingPathComponent("server/audio_isolation_worker.py").path
        let task = Process()
        let output = Pipe()
        task.executableURL = URL(fileURLWithPath: "/bin/ps")
        task.arguments = ["-axo", "pid=,ppid=,uid=,command="]
        task.standardOutput = output
        task.standardError = Pipe()
        do {
            try task.run()
            // Drain before waiting: a full pipe would otherwise leave `ps`
            // blocked and prevent the HUD from ever reaching its backend.
            let data = output.fileHandleForReading.readDataToEndOfFile()
            task.waitUntilExit()
            let text = String(data: data, encoding: .utf8) ?? ""
            let userID = getuid()
            var recovered: [pid_t] = []
            for line in text.split(whereSeparator: \.isNewline) {
                let fields = line.split(maxSplits: 3, whereSeparator: \.isWhitespace)
                guard fields.count == 4,
                      let pid = pid_t(fields[0]),
                      let parentPID = pid_t(fields[1]),
                      let uid = uid_t(fields[2]),
                      pid > 1, parentPID == 1, uid == userID else { continue }
                let command = String(fields[3])
                guard let executablePath = merrickRuntimeExecutablePath(pid) else { continue }
                guard merrickOwnsRuntimeExecutable(
                    executablePath, currentRuntimePath: projectRoot.path,
                    bundleID: Bundle.main.bundleIdentifier ?? "ai.jarvis.desktop"
                ) else { continue }
                let belongsToCurrentRuntime = command.contains(backendPython)
                let belongsToInstalledBundle = executablePath.contains("/Contents/Resources/runtime/")
                let isBackend = (belongsToCurrentRuntime || belongsToInstalledBundle) &&
                    command.contains("-m uvicorn main:app") &&
                    command.contains("--port \(RuntimeContract.backendPort)")
                let isAudioWorker = (
                    (belongsToCurrentRuntime && command.contains(workerScript)) ||
                    (belongsToInstalledBundle && command.contains("server/audio_isolation_worker.py"))
                )
                let isTTSWorker = belongsToInstalledBundle &&
                    command.contains("steadfast_tts_worker.py")
                guard isBackend || isAudioWorker || isTTSWorker else { continue }
                // Refresh the executable immediately before signalling, since
                // the process may have exited while the snapshot was checked.
                guard merrickRuntimeExecutablePath(pid) == executablePath else { continue }
                if Darwin.kill(pid, SIGTERM) == 0 { recovered.append(pid) }
            }
            guard !recovered.isEmpty else { return }
            nativeTrace("runtime.orphans_reclaimed pids=\(recovered.map(String.init).joined(separator: ","))")
            // Do not delay launch indefinitely, but give the reclaimed listener a
            // moment to release the contract-owned loopback listener before restart.
            Thread.sleep(forTimeInterval: 0.25)
        } catch {
            nativeTrace("runtime.orphan_scan_failed")
            return
        }
    }

    private func buildWindow() {
        let config = WKWebViewConfiguration()
        config.userContentController.add(self, name: "jarvis")
        config.mediaTypesRequiringUserActionForPlayback = []
        webView = WKWebView(frame: .zero, configuration: config)
        webView.navigationDelegate = self
        webView.setValue(false, forKey: "drawsBackground")

        window = MerrickHUDWindow(contentRect: NSRect(x: 0, y: 0, width: 500, height: 560),
                                 styleMask: [.borderless, .resizable], backing: .buffered, defer: false)
        window.title = "MERRICK"
        window.isOpaque = false
        window.backgroundColor = .clear
        window.level = .floating
        window.hasShadow = false
        window.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        // WKWebView form controls must receive the first mouse-down so inputs,
        // textareas, selects, and buttons can become first responder. Window
        // movement is handled by the bounded JS drag regions below instead.
        window.isMovableByWindowBackground = false
        window.delegate = self
        window.contentView = webView
        restoreWindowPosition()
        window.makeKeyAndOrderFront(nil)
    }

    private func recoverBackendStartup(reason: String) {
        guard !appTerminating, !backendRecoveryScheduled else { return }
        let now = Date()
        backendRecoveryHistory.removeAll {
            now.timeIntervalSince($0) > backendRecoveryWindow
        }
        guard backendRecoveryHistory.count < maximumBackendRecoveriesPerWindow else {
            nativeTrace("backend.recovery_circuit_open reason=\(reason)")
            showStartupError(
                "MERRICK stopped repeatedly, so automatic restart has paused.\nQuit and reopen the app from Applications."
            )
            return
        }
        backendRecoveryHistory.append(now)
        backendRecoveryScheduled = true
        backendHealthTask?.cancel()
        backendHealthTask = nil
        backendStartupDeadline = nil
        nativeTrace("backend.startup_recovery reason=\(reason) attempt=\(backendStartupAttempts)")
        terminateBackend(gracePeriod: 2.0)
        reclaimOrphanedRuntimeProcesses()
        guard backendStartupAttempts < maximumBackendStartupAttempts else {
            backendRecoveryScheduled = false
            showStartupError(
                "MERRICK could not start its local core after automatic recovery.\nQuit and reopen the app from Applications."
            )
            return
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { [weak self] in
            guard let self, !self.appTerminating else { return }
            self.backendRecoveryScheduled = false
            self.startBackend()
        }
    }

    private func pollBackendHealth(until deadline: Date) {
        guard !appTerminating, !backendRecoveryScheduled else { return }
        guard Date() < deadline else {
            backendStartupDeadline = nil
            nativeTrace("backend.health_timeout")
            recoverBackendStartup(reason: "health_timeout")
            return
        }
        guard backend?.isRunning == true else {
            nativeTrace("backend.health_aborted process_running=false")
            recoverBackendStartup(reason: "process_exited")
            return
        }

        let healthURL = URL(
            string: "http://\(RuntimeContract.backendHost):\(RuntimeContract.backendPort)\(RuntimeContract.backendHealthPath)"
        )!
        var request = URLRequest(url: healthURL)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.timeoutInterval = 1.0
        request.setValue(bridgeChallenge, forHTTPHeaderField: "X-Jarvis-Bridge-Challenge")
        let task = URLSession.shared.dataTask(with: request) { [weak self] _, response, _ in
            DispatchQueue.main.async {
                guard let self, !self.appTerminating, !self.hudLoadStarted else { return }
                self.backendHealthTask = nil
                if self.isAuthenticatedBackendResponse(response, requireStatusOK: true) {
                    self.backendStartupDeadline = nil
                    self.backendStartupAttempts = 0
                    self.nativeTrace("backend.healthy")
                    self.startupErrorLabel?.removeFromSuperview()
                    self.startupErrorLabel = nil
                    if !self.hudLoadStarted { self.loadHUDOnce() }
                    return
                }
                let remainingDeadline = self.backendStartupDeadline ?? deadline
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.25) { [weak self] in
                    self?.pollBackendHealth(until: remainingDeadline)
                }
            }
        }
        backendHealthTask = task
        task.resume()
    }

    private func loadHUDOnce() {
        guard !hudLoadStarted, backend?.isRunning == true else { return }
        hudLoadStarted = true
        webLoadAttempts += 1
        startupErrorLabel?.removeFromSuperview()
        startupErrorLabel = nil
        var components = URLComponents(
            string: "http://\(RuntimeContract.backendHost):\(RuntimeContract.backendPort)/"
        )!
        // Keep the per-launch bridge token in the URL fragment. Fragments are
        // not sent in HTTP requests or access logs.
        components.fragment = "desktop=1&bridge=\(bridgeToken)"
        nativeTrace("hud.load_started")
        var request = URLRequest(url: components.url!)
        // Every launch has a new bridge key. A cached document would carry the
        // previous launch's HMAC proof and must never be reused.
        request.cachePolicy = .reloadIgnoringLocalAndRemoteCacheData
        request.setValue("no-store", forHTTPHeaderField: "Cache-Control")
        request.setValue(bridgeChallenge, forHTTPHeaderField: "X-Jarvis-Bridge-Challenge")
        webView.load(request)
        scheduleWebReadyTimeout()
    }

    /// A healthy loopback backend does not prove WebKit loaded the signed HUD
    /// or that its authenticated bridge came up.  Without this bound a broken
    /// static page left a perfectly live app permanently saying BOOTING.
    private func scheduleWebReadyTimeout() {
        webReadyTimeoutWorkItem?.cancel()
        let workItem = DispatchWorkItem { [weak self] in
            guard let self, !self.appTerminating, !self.webReady else { return }
            self.nativeTrace("interface.bridge_timeout")
            if self.webLoadAttempts < self.maximumWebLoadAttempts,
               self.backend?.isRunning == true {
                self.nativeTrace("interface.bridge_reload attempt=\(self.webLoadAttempts + 1)")
                self.webView.stopLoading()
                self.hudLoadStarted = false
                self.loadHUDOnce()
                return
            }
            self.showStartupError(
                "The MERRICK interface did not finish loading.\nQuit and reopen MERRICK from Applications."
            )
        }
        webReadyTimeoutWorkItem = workItem
        DispatchQueue.main.asyncAfter(deadline: .now() + webReadyTimeout, execute: workItem)
    }

    private var expectedBridgeProof: String {
        let key = SymmetricKey(data: Data(bridgeToken.utf8))
        let digest = HMAC<SHA256>.authenticationCode(
            for: Data(bridgeChallenge.utf8),
            using: key
        )
        return digest.map { String(format: "%02x", $0) }.joined()
    }

    private func isAuthenticatedBackendResponse(_ response: URLResponse?, requireStatusOK: Bool) -> Bool {
        guard let http = response as? HTTPURLResponse,
              (!requireStatusOK || http.statusCode == 200),
              let proof = http.value(forHTTPHeaderField: "X-Jarvis-Bridge-Proof") else {
            return false
        }
        let expected = Array(expectedBridgeProof.utf8)
        let supplied = Array(proof.lowercased().utf8)
        guard expected.count == supplied.count else { return false }
        var difference: UInt8 = 0
        for (left, right) in zip(expected, supplied) { difference |= left ^ right }
        return difference == 0
    }

    private func showStartupError(_ message: String) {
        DispatchQueue.main.async { [weak self] in
            guard let self, self.window != nil else { return }
            let label: NSTextField
            if let existing = self.startupErrorLabel {
                label = existing
            } else {
                label = NSTextField(wrappingLabelWithString: "")
                label.translatesAutoresizingMaskIntoConstraints = false
                label.alignment = .center
                label.font = NSFont.monospacedSystemFont(ofSize: 13, weight: .medium)
                label.textColor = NSColor(calibratedRed: 0.95, green: 0.61, blue: 0.16, alpha: 1)
                label.maximumNumberOfLines = 0
                self.webView.addSubview(label, positioned: .above, relativeTo: nil)
                NSLayoutConstraint.activate([
                    label.centerXAnchor.constraint(equalTo: self.webView.centerXAnchor),
                    label.centerYAnchor.constraint(equalTo: self.webView.centerYAnchor),
                    label.widthAnchor.constraint(lessThanOrEqualToConstant: 410),
                ])
                self.startupErrorLabel = label
            }
            label.stringValue = message
        }
    }

    private func requestPermissions() {
        SFSpeechRecognizer.requestAuthorization { [weak self] speechStatus in
            guard let self else { return }
            guard speechStatus == .authorized else {
                if speechStatus != .notDetermined {
                    self.js("window.merrickNativeError('请在系统设置 → 隐私与安全性 → 语音识别中允许 MERRICK')")
                }
                return
            }
            AVCaptureDevice.requestAccess(for: .audio) { [weak self] allowed in
                guard let self else { return }
                if allowed {
                    if self.webReady {
                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.25) { self.startListening() }
                    }
                } else {
                    self.js("window.merrickNativeError('请在系统设置 → 隐私与安全性 → 麦克风中允许 MERRICK')")
                }
            }
        }
    }

    private func isValidNotificationIdentifier(_ value: String) -> Bool {
        guard 1...96 ~= value.count else { return false }
        return value.range(
            of: "^[A-Za-z0-9][A-Za-z0-9._:-]{0,95}$",
            options: .regularExpression
        ) != nil
    }

    private func notificationDate(_ value: String) -> Date? {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withColonSeparatorInTimeZone]
        return formatter.date(from: value)
    }

    private func sendNotificationStatus(id: String, ok: Bool, message: String = "") {
        DispatchQueue.main.async { [weak self] in
            guard let self else { return }
            self.js(
                "window.merrickNativeNotificationStatus && " +
                "window.merrickNativeNotificationStatus(\(self.jsString(id)), \(ok), \(self.jsString(message)))"
            )
        }
    }

    private func scheduleLocalNotification(_ body: [String: Any]) {
        guard let identifier = body["id"] as? String,
              let title = body["title"] as? String,
              let notificationBody = body["body"] as? String,
              let fireAt = body["fireAt"] as? String,
              isValidNotificationIdentifier(identifier),
              !title.isEmpty, title.count <= 80,
              !notificationBody.isEmpty, notificationBody.count <= 280,
              let date = notificationDate(fireAt),
              date.timeIntervalSinceNow > -2 else {
            nativeTrace("notification.schedule_rejected")
            if let identifier = body["id"] as? String,
               isValidNotificationIdentifier(identifier) {
                sendNotificationStatus(id: identifier, ok: false, message: "Invalid reminder notification.")
            }
            return
        }
        let center = UNUserNotificationCenter.current()
        center.requestAuthorization(options: [.alert, .sound, .badge]) { [weak self] allowed, error in
            guard let self else { return }
            guard allowed, error == nil else {
                self.nativeTrace("notification.permission_denied")
                self.sendNotificationStatus(
                    id: identifier,
                    ok: false,
                    message: "Enable notifications for MERRICK in System Settings."
                )
                return
            }
            let content = UNMutableNotificationContent()
            content.title = title
            content.body = notificationBody
            content.sound = .default
            content.userInfo = ["jarvisNotificationID": identifier]
            let delay = max(1, date.timeIntervalSinceNow)
            let trigger = UNTimeIntervalNotificationTrigger(timeInterval: delay, repeats: false)
            let request = UNNotificationRequest(
                identifier: identifier,
                content: content,
                trigger: trigger
            )
            center.add(request) { error in
                if let error {
                    self.nativeTrace("notification.schedule_failed")
                    self.sendNotificationStatus(id: identifier, ok: false, message: error.localizedDescription)
                    return
                }
                self.nativeTrace("notification.scheduled id=\(identifier)")
                self.sendNotificationStatus(id: identifier, ok: true)
            }
        }
    }

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        completionHandler([.banner, .sound])
    }

    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard let body = message.body as? [String: Any],
              let action = body["action"] as? String,
              isTrustedBridgeMessage(message, body: body) else {
            nativeTrace("bridge.rejected")
            return
        }
        switch action {
        case "webReady":
            webReady = true
            webLoadAttempts = 0
            webReadyTimeoutWorkItem?.cancel()
            webReadyTimeoutWorkItem = nil
            nativeTrace("web.ready")
            startListening()
            sendSpeechLanguageState()
            sendFullscreenState(reason: "native")
        case "startListening":
            let echoCancel = body["echoCancel"] as? Bool ?? false
            startListening(useVoiceProcessing: echoCancel)
        case "stopListening": stopListening(final: true)
        case "restartListening":
            stopListening(final: false)
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.16) { [weak self] in
                self?.startListening()
            }
        case "beginWatchVoiceVerification":
            // A transcript-aware frontend guard rejects MERRICK's own words
            // before it asks native code to capture a local owner sample.
            beginWatchVoiceVerification(for: recognitionGeneration)
        case "setSpeechLanguage":
            setSpeechLanguage(body)
        case "openWorkspace":
            openWorkspaceDirectory()
        case "openOpenClawDashboard":
            openOpenClawDashboard()
        case "openOpenClawSession":
            guard let rawURL = body["url"] as? String else { return }
            openOpenClawSession(rawURL)
        case "getAutomationAccessState":
            sendAutomationAccessState()
        case "chooseAutomationAccessRoot":
            chooseAutomationAccessRoot()
        case "saveAutomationAccessPolicy":
            saveAutomationAccessPolicy(body)
        case "openAutomationAudit":
            openAutomationAudit()
        case "exportMemoryArchive":
            exportMemoryArchive()
        case "uninstall":
            confirmAndUninstall()
        case "openResearchPages":
            guard let rawURLs = body["urls"] as? [String] else { return }
            openResearchPages(rawURLs)
        case "getProviderSetupState":
            sendProviderSetupState()
        case "markProviderConnectionFailed":
            markProviderConnectionFailed(body)
        case "saveAddressPreferences":
            saveAddressPreferences(body)
        case "saveProviderAPIKey":
            saveProviderAPIKey(body)
        case "connectProviderCLI":
            connectProviderCLI(body)
        case "cancelProviderConnection":
            cancelProviderConnection()
        case "openProviderVerificationURL":
            openProviderVerificationURL()
        case "finishOnboarding":
            finishProviderOnboarding()
        case "authenticateVoiceprintManagement":
            authenticateVoiceprintManagement()
        case "captureVoiceprintSample":
            captureVoiceprintSample()
        case "setWatchAudioMode":
            let enabled = body["enabled"] as? Bool ?? false
            // Do not toggle AVAudioEngine Voice Processing I/O here: on this
            // Mac it can leave Speech.framework alive but without usable
            // results.  The ScreenCaptureKit/WebRTC reference path below is
            // device-independent and keeps the raw-input fallback intact.
            watchAudioModeEnabled = enabled
            if enabled { meetingAudioModeEnabled = false }
            if !enabled { watchVoiceVerificationGeneration = -1 }
            playbackReferenceRequested = enabled || meetingAudioModeEnabled
            nativeTrace("watch.audio_isolation requested=\(enabled)")
            updatePlaybackIsolation()
        case "setMeetingAudioMode":
            let enabled = body["enabled"] as? Bool ?? false
            meetingAudioModeEnabled = enabled
            if enabled { watchAudioModeEnabled = false }
            if enabled { watchVoiceVerificationGeneration = -1 }
            playbackReferenceRequested = enabled || watchAudioModeEnabled
            nativeTrace("meeting.audio_isolation requested=\(enabled)")
            updatePlaybackIsolation()
        case "scheduleLocalNotification":
            scheduleLocalNotification(body)
        case "cancelLocalNotification":
            guard let identifier = body["id"] as? String,
                  isValidNotificationIdentifier(identifier) else {
                nativeTrace("notification.cancel_rejected")
                return
            }
            UNUserNotificationCenter.current().removePendingNotificationRequests(
                withIdentifiers: [identifier]
            )
            nativeTrace("notification.cancelled id=\(identifier)")
        case "assistantAudioState":
            guard let playing = body["playing"] as? Bool else {
                nativeTrace("audio_state.rejected")
                return
            }
            assistantAudioPlaying = playing
            if playing {
                // Never turn MERRICK's own loudspeaker output into a voiceprint.
                voiceSampleSuppressedGeneration = recognitionGeneration
                voiceSampleLock.lock()
                voiceSamples.removeAll(keepingCapacity: true)
                voiceResampleCursor = 0
                voiceSampleEmissionCount = 0
                voiceSampleCaptureArmedGeneration = -1
                voiceSampleLock.unlock()
            } else if watchAudioModeEnabled &&
                        voiceSampleSuppressedGeneration == recognitionGeneration {
                // A reply can end while Speech.framework keeps the same
                // recognition generation alive.  Leaving this stale flag in
                // place made Watch Mode transcribe the owner but never send a
                // voice sample for verification.  Playback has fully stopped;
                // the next detected phrase may safely arm a fresh local clip.
                voiceSampleSuppressedGeneration = -1
                nativeTrace("watch.voice_sample_gate_released generation=\(recognitionGeneration)")
            }
            nativeTrace("audio_state playing=\(playing)")
            updatePlaybackIsolation()
        case "captureScreen":
            guard let requestID = body["requestId"] as? String,
                  isValidScreenCaptureRequestID(requestID) else {
                nativeTrace("screen_capture.rejected invalid_request_id")
                return
            }
            captureScreen(requestID: requestID)
        case "performAction":
            guard let requestID = body["requestId"] as? String,
                  isValidNativeActionRequestID(requestID) else {
                nativeTrace("native_action.rejected invalid_request_id")
                return
            }
            guard let nativeAction = parseNativeAction(body["nativeAction"]) else {
                nativeTrace("native_action.rejected invalid_schema")
                rejectNativeActionRequest(
                    requestID: requestID,
                    error: "The requested desktop action was not in the approved format."
                )
                return
            }
            performNativeAction(requestID: requestID, action: nativeAction)
        case "cancelAction":
            guard let requestID = body["requestId"] as? String,
                  isValidNativeActionRequestID(requestID) else {
                nativeTrace("native_action.cancel_rejected invalid_request_id")
                return
            }
            cancelNativeAction(requestID: requestID)
        case "quit":
            nativeTrace("app.quit_requested source=hud")
            NSApp.terminate(nil)
        case "moveWindow":
            let dx = (body["dx"] as? NSNumber)?.doubleValue ?? 0
            let dy = (body["dy"] as? NSNumber)?.doubleValue ?? 0
            moveWindow(dx: dx, dy: dy)
        case "endWindowDrag": saveWindowPosition()
        case "resize":
            let expanded = body["expanded"] as? Bool ?? false
            resize(expanded: expanded)
        case "setWindowFullscreen":
            setWindowFullscreen(body)
        default: break
        }
    }

    /// Open the one user-facing workspace, rather than exposing MERRICK's
    /// operational state, logs, credentials, or voiceprint-vector directory.
    private func openWorkspaceDirectory() {
        let documents = FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Application Support/JarvisStark/Workspace/Documents", isDirectory: true)
        do {
            try FileManager.default.createDirectory(at: documents, withIntermediateDirectories: true)
            migrateLegacyUserWorkspaceArtifacts()
            NSWorkspace.shared.open(documents)
            nativeTrace("workspace.opened")
        } catch {
            nativeTrace("workspace.open_failed error=\(error.localizedDescription)")
            js("window.merrickNativeWorkspaceOpenFailed(\(jsString(error.localizedDescription)))")
        }
    }

    /// Ask OpenClaw itself for a short-lived Control UI pairing URL, then open
    /// it natively. The secret URL never crosses into the WebKit HUD or logs.
    /// Bind the CLI to the exact app-owned ephemeral Gateway recorded by the
    /// Python supervisor so it can never attach to an unrelated local daemon.
    private func openOpenClawDashboard() {
        openAuthenticatedOpenClawControl(route: nil, traceName: "openclaw.dashboard") {
            [weak self] ok, message in
            self?.sendOpenClawDashboardStatus(ok: ok, message: message)
        }
    }

    /// Ask OpenClaw for a short-lived browser bootstrap token, then optionally
    /// apply one already-validated session route. This is the only native path
    /// that opens Control UI, keeping dashboard and per-agent authentication on
    /// one contract without exposing the Gateway token to WebKit.
    private func openAuthenticatedOpenClawControl(
        route: URL?,
        traceName: String,
        completion: @escaping (Bool, String) -> Void
    ) {
        guard openClawDashboardProcess?.isRunning != true,
              let cli = merrickOpenClawCLI() else {
            completion(false, "OpenClaw is not ready yet.")
            return
        }
        let ownerURL = merrickApplicationSupportDirectory
            .appendingPathComponent("OpenClaw/.gateway-owner.json")
        let tokenURL = merrickApplicationSupportDirectory
            .appendingPathComponent("OpenClaw/.gateway-token")
        guard let ownerData = try? Data(contentsOf: ownerURL),
              let owner = try? JSONSerialization.jsonObject(with: ownerData) as? [String: Any],
              let ownerPort = (owner["port"] as? NSNumber)?.intValue,
              let ownerPID = (owner["pid"] as? NSNumber)?.int32Value,
              let rawGatewayToken = try? String(contentsOf: tokenURL, encoding: .utf8),
              case let gatewayToken = rawGatewayToken.trimmingCharacters(in: .whitespacesAndNewlines),
              gatewayToken.count == 64,
              gatewayToken.allSatisfy({ $0.isHexDigit }),
              ownerPort > 0, ownerPort <= 65_535,
              ownerPID > 1, Darwin.kill(ownerPID, 0) == 0 else {
            completion(false, "MERRICK's OpenClaw Gateway is still starting.")
            return
        }

        var environment = merrickOpenClawEnvironment()
        environment["OPENCLAW_GATEWAY_URL"] = "ws://127.0.0.1:\(ownerPort)"
        environment["OPENCLAW_GATEWAY_PORT"] = String(ownerPort)
        environment["OPENCLAW_GATEWAY_TOKEN"] = gatewayToken
        environment["JARVIS_OPENCLAW_PUBLIC_ORIGIN"] = "http://127.0.0.1:\(ownerPort)"
        let output = Pipe()
        let process = Process()
        process.executableURL = cli.node
        process.arguments = [cli.entry.path] + ["dashboard", "--json", "--no-open"]
        process.environment = environment
        process.standardInput = FileHandle.nullDevice
        process.standardOutput = output
        process.standardError = FileHandle.nullDevice

        do {
            try process.run()
            openClawDashboardProcess = process
            if Darwin.setpgid(process.processIdentifier, process.processIdentifier) == 0 ||
                Darwin.getpgid(process.processIdentifier) == process.processIdentifier {
                openClawDashboardProcessGroup = process.processIdentifier
            } else {
                openClawDashboardProcessGroup = nil
            }
        } catch {
            completion(false, "OpenClaw Control UI could not be started.")
            return
        }

        let timeout = DispatchWorkItem { [weak self, weak process] in
            guard let self, let process, process.isRunning else { return }
            self.terminateOwnedProviderProcess(process, processGroup: self.openClawDashboardProcessGroup)
        }
        DispatchQueue.global(qos: .utility).asyncAfter(deadline: .now() + 12, execute: timeout)
        DispatchQueue.global(qos: .userInitiated).async { [weak self, weak process] in
            guard let self, let process else { return }
            let data = (try? output.fileHandleForReading.readToEnd()) ?? Data()
            process.waitUntilExit()
            timeout.cancel()
            guard process.terminationStatus == 0,
                  let payload = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  payload["ok"] as? Bool == true,
                  let dashboardPort = (payload["port"] as? NSNumber)?.intValue,
                  ownerPort == dashboardPort,
                  let rawBrowserURL = payload["browserUrl"] as? String,
                  let browserURL = URL(string: rawBrowserURL),
                  let scheme = browserURL.scheme?.lowercased(),
                  scheme == "http" || scheme == "https",
                  let host = browserURL.host?.lowercased(),
                  host == "127.0.0.1" || host == "localhost",
                  browserURL.port == ownerPort,
                  var destination = URLComponents(url: browserURL, resolvingAgainstBaseURL: false) else {
                DispatchQueue.main.async {
                    self.openClawDashboardProcess = nil
                    self.openClawDashboardProcessGroup = nil
                    self.nativeTrace("\(traceName)_handoff_failed")
                    completion(false, "OpenClaw did not return a verified local Control UI session.")
                }
                return
            }
            if let route {
                destination.path = route.path
                destination.query = route.query
            }
            guard let destinationURL = destination.url else {
                DispatchQueue.main.async {
                    self.openClawDashboardProcess = nil
                    self.openClawDashboardProcessGroup = nil
                    self.nativeTrace("\(traceName)_handoff_failed")
                    completion(false, "OpenClaw did not return a verified local Control UI session.")
                }
                return
            }
            DispatchQueue.main.async {
                self.openClawDashboardProcess = nil
                self.openClawDashboardProcessGroup = nil
                self.nativeTrace("\(traceName)_opened")
                NSWorkspace.shared.open(destinationURL)
                completion(true, "")
            }
        }
    }

    private func sendOpenClawDashboardStatus(ok: Bool, message: String = "") {
        js("window.merrickNativeOpenClawDashboardStatus(\(ok ? "true" : "false"), \(jsString(message)))")
    }

    /// Open only a session URL produced by this app-owned OpenClaw Gateway.
    /// A Gateway restart changes its random port, so preserve the receipt's
    /// exact route while rebasing only its loopback origin to the live owner.
    /// The HUD cannot turn this bridge into a general URL launcher.
    private func openOpenClawSession(_ rawURL: String) {
        let ownerURL = merrickApplicationSupportDirectory
            .appendingPathComponent("OpenClaw/.gateway-owner.json")
        guard rawURL.count <= 2_048,
              let ownerData = try? Data(contentsOf: ownerURL),
              let owner = try? JSONSerialization.jsonObject(with: ownerData) as? [String: Any],
              let ownerPort = (owner["port"] as? NSNumber)?.intValue,
              let ownerPID = (owner["pid"] as? NSNumber)?.int32Value,
              ownerPort > 0, ownerPort <= 65_535,
              ownerPID > 1, Darwin.kill(ownerPID, 0) == 0,
              let sessionURL = URL(string: rawURL),
              let scheme = sessionURL.scheme?.lowercased(),
              scheme == "http" || scheme == "https",
              let host = sessionURL.host?.lowercased(),
              host == "127.0.0.1" || host == "localhost",
              let receiptPort = sessionURL.port,
              receiptPort > 0, receiptPort <= 65_535,
              sessionURL.path.hasPrefix("/chat/"),
              sessionURL.user == nil, sessionURL.password == nil else {
            nativeTrace("openclaw.session_open_rejected")
            js("window.MerrickAgentBoard?.handleTerminalOpenResult(false, \(jsString("OpenClaw did not return a verified local agent terminal.")))")
            return
        }
        openAuthenticatedOpenClawControl(route: sessionURL, traceName: "openclaw.session") {
            [weak self] ok, message in
            guard let self else { return }
            let detail = message.isEmpty
                ? "OpenClaw did not return a verified local agent terminal."
                : message
            self.js("window.MerrickAgentBoard?.handleTerminalOpenResult(\(ok ? "true" : "false"), \(self.jsString(ok ? "" : detail)))")
        }
    }

    /// Older builds used the user-facing Documents directory as OpenClaw's
    /// bootstrap workspace.  OpenClaw consequently seeded policy and identity
    /// templates next to the user's PDFs and summaries.  Preserve those
    /// internal files in the private runtime rather than deleting them, while
    /// keeping the Documents directory a clear, user-owned file surface.
    private func migrateLegacyUserWorkspaceArtifacts() {
        let fileManager = FileManager.default
        let documents = fileManager.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Application Support/JarvisStark/Workspace/Documents", isDirectory: true)
        let privateArchive = merrickApplicationSupportDirectory
            .appendingPathComponent("OpenClaw/legacy-user-workspace-bootstrap", isDirectory: true)
        let internalNames: Set<String> = [
            "agents.md", "identity.md", "soul.md", "tools.md", "knowledge.md",
            "openclaw-workspace-state.json", "jarvis-codex-ready.md",
        ]
        guard fileManager.fileExists(atPath: documents.path) else { return }
        do {
            try fileManager.createDirectory(at: privateArchive, withIntermediateDirectories: true,
                                            attributes: [.posixPermissions: 0o700])
            for url in try fileManager.contentsOfDirectory(at: documents, includingPropertiesForKeys: nil) {
                guard internalNames.contains(url.lastPathComponent.lowercased()) else { continue }
                let destination = privateArchive.appendingPathComponent(url.lastPathComponent)
                if fileManager.fileExists(atPath: destination.path) {
                    try? fileManager.removeItem(at: destination)
                }
                try fileManager.moveItem(at: url, to: destination)
                nativeTrace("workspace.internal_artifact_migrated name=\(url.lastPathComponent)")
            }
            // OpenClaw's current workspace attestation requires these two
            // generated markers to remain in place. Keep them out of normal
            // Finder views instead of moving them and tripping that integrity
            // guard; they are not user documents and remain private metadata.
            for marker in ["HEARTBEAT.md", "USER.md"] {
                var url = documents.appendingPathComponent(marker)
                guard fileManager.fileExists(atPath: url.path) else { continue }
                var values = URLResourceValues()
                values.isHidden = true
                try? url.setResourceValues(values)
            }
        } catch {
            nativeTrace("workspace.internal_artifact_migration_failed error=\(error.localizedDescription)")
        }
    }

    private func confirmAndUninstall() {
        let chinese = speechLanguage == "zh"
        let alert = NSAlert()
        alert.alertStyle = .critical
        alert.messageText = chinese ? "卸载 MERRICK？" : "Uninstall MERRICK?"
        alert.informativeText = chinese
            ? "这将关闭 MERRICK，删除本机记忆、Workspace、设置、声纹、OpenClaw 数据、模型凭据和权限记录。此操作无法撤销。"
            : "This closes MERRICK and permanently removes its local memory, Workspace, settings, voiceprint, OpenClaw data, model credentials, and permission records. This cannot be undone."
        alert.addButton(withTitle: chinese ? "卸载并删除全部数据" : "Uninstall and erase all data")
        alert.addButton(withTitle: chinese ? "取消" : "Cancel")
        guard alert.runModal() == .alertFirstButtonReturn else {
            nativeTrace("uninstall.cancelled")
            return
        }
        launchConfirmedUninstaller()
    }

    private func launchConfirmedUninstaller() {
        let source = projectRoot.appendingPathComponent("scripts/uninstall-merrick.sh")
        let temporary = FileManager.default.temporaryDirectory
            .appendingPathComponent("jarvis-uninstall-\(UUID().uuidString).sh")
        do {
            try FileManager.default.copyItem(at: source, to: temporary)
            try FileManager.default.setAttributes(
                [.posixPermissions: 0o700],
                ofItemAtPath: temporary.path
            )
            let process = Process()
            process.executableURL = URL(fileURLWithPath: "/bin/zsh")
            process.arguments = [
                temporary.path,
                "--app", Bundle.main.bundleURL.path,
                "--parent-pid", String(ProcessInfo.processInfo.processIdentifier),
            ]
            process.standardOutput = FileHandle.nullDevice
            process.standardError = FileHandle.nullDevice
            try process.run()
            uninstallerProcess = process
            UNUserNotificationCenter.current().removeAllPendingNotificationRequests()
            UNUserNotificationCenter.current().removeAllDeliveredNotifications()
            nativeTrace("uninstall.started pid=\(process.processIdentifier)")
            NSApp.terminate(nil)
        } catch {
            try? FileManager.default.removeItem(at: temporary)
            nativeTrace("uninstall.launch_failed error=\(error.localizedDescription)")
            let alert = NSAlert()
            alert.alertStyle = .warning
            alert.messageText = "MERRICK could not start the uninstaller."
            alert.informativeText = error.localizedDescription
            alert.runModal()
        }
    }

    private var privateMemoryDirectory: URL {
        merrickApplicationSupportDirectory
            .appendingPathComponent("OpenClaw/memory", isDirectory: true)
    }

    private func sendMemoryExportStatus(_ message: String, state: String) {
        js("window.merrickNativeMemoryExportStatus(\(jsString(message)), \(jsString(state)))")
    }

    /// Export is intentionally protected by a fresh device-owner challenge on
    /// every use. The archive contains private memory records only; provider
    /// profiles, Keychain credentials, voice vectors, Workspace files, logs,
    /// and the OpenClaw runtime are outside this directory and are excluded.
    private func exportMemoryArchive() {
        guard !memoryExportInProgress else { return }
        guard FileManager.default.fileExists(atPath: privateMemoryDirectory.path) else {
            nativeTrace("memory.export_failed reason=directory_missing")
            sendMemoryExportStatus("No private memory archive is available yet.", state: "error")
            return
        }
        memoryExportInProgress = true
        let context = LAContext()
        var authError: NSError?
        guard context.canEvaluatePolicy(.deviceOwnerAuthentication, error: &authError) else {
            memoryExportInProgress = false
            let reason = authError?.localizedDescription ?? "Mac authentication is unavailable."
            nativeTrace("memory.export_auth_unavailable")
            sendMemoryExportStatus(reason, state: "error")
            return
        }
        context.evaluatePolicy(
            .deviceOwnerAuthentication,
            localizedReason: "Export MERRICK private memory archive"
        ) { [weak self] success, error in
            DispatchQueue.main.async {
                guard let self else { return }
                guard success else {
                    self.memoryExportInProgress = false
                    let reason = error?.localizedDescription ?? "Authentication was cancelled."
                    self.nativeTrace("memory.export_auth_failed")
                    self.sendMemoryExportStatus(reason, state: "error")
                    return
                }
                self.presentMemoryExportSavePanel()
            }
        }
    }

    private func presentMemoryExportSavePanel() {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.dateFormat = "yyyy-MM-dd-HHmmss"
        let panel = NSSavePanel()
        panel.title = "Export MERRICK Private Memory"
        panel.message = "This ZIP contains MERRICK private memory and meeting records only."
        panel.nameFieldStringValue = "MERRICK-memory-\(formatter.string(from: Date())).zip"
        panel.allowedFileTypes = ["zip"]
        panel.canCreateDirectories = true
        panel.isExtensionHidden = false
        panel.beginSheetModal(for: window) { [weak self] response in
            guard let self else { return }
            guard response == .OK, let destination = panel.url else {
                self.memoryExportInProgress = false
                self.sendMemoryExportStatus("Memory export was cancelled.", state: "idle")
                return
            }
            self.sendMemoryExportStatus("EXPORTING PRIVATE MEMORY ZIP…", state: "pending")
            let source = self.privateMemoryDirectory
            DispatchQueue.global(qos: .userInitiated).async {
                let result = self.createMemoryArchive(from: source, to: destination)
                DispatchQueue.main.async {
                    self.memoryExportInProgress = false
                    switch result {
                    case .success:
                        self.nativeTrace("memory.export_completed")
                        self.sendMemoryExportStatus("EXPORTED · \(destination.lastPathComponent)", state: "ready")
                    case .failure(let error):
                        self.nativeTrace("memory.export_failed error=\(error.localizedDescription)")
                        self.sendMemoryExportStatus("Export failed: \(error.localizedDescription)", state: "error")
                    }
                }
            }
        }
    }

    private func createMemoryArchive(from source: URL, to destination: URL) -> Result<Void, Error> {
        do {
            let process = Process()
            let output = Pipe()
            process.executableURL = URL(fileURLWithPath: "/usr/bin/ditto")
            process.arguments = [
                "-c", "-k", "--sequesterRsrc", "--keepParent",
                source.path, destination.path,
            ]
            process.standardOutput = output
            process.standardError = output
            try process.run()
            process.waitUntilExit()
            guard process.terminationStatus == 0 else {
                let detail = String(data: output.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
                throw NSError(
                    domain: "JARVISMemoryExport",
                    code: Int(process.terminationStatus),
                    userInfo: [NSLocalizedDescriptionKey: detail.trimmingCharacters(in: .whitespacesAndNewlines).prefix(180)]
                )
            }
            try FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: destination.path)
            return .success(())
        } catch {
            return .failure(error)
        }
    }

    /// Open a small set of public research sources inside MERRICK rather than
    /// delegating the user's research flow to Chrome or Safari. These webviews
    /// have no script bridge, no access to local files, and accept HTTPS/HTTP
    /// navigation only.
    private func tileResearchWindows(_ windows: [NSWindow]) {
        guard !windows.isEmpty else { return }
        let screen = windows.first?.screen ?? NSScreen.main ?? NSScreen.screens.first
        guard let screen else { return }

        // Work inside the usable desktop area, leaving room for the menu bar,
        // Dock, and a small visual gutter between independent source panels.
        let margin: CGFloat = 24
        let gap: CGFloat = 14
        let usable = screen.visibleFrame.insetBy(dx: margin, dy: margin)
        let count = windows.count
        let minimumReadableWidth: CGFloat = 360
        let availableColumns = max(1, Int((usable.width + gap) / (minimumReadableWidth + gap)))
        let columns = min(count, availableColumns)
        let rows = Int(ceil(Double(count) / Double(columns)))
        let width = floor((usable.width - gap * CGFloat(columns - 1)) / CGFloat(columns))
        let height = floor((usable.height - gap * CGFloat(rows - 1)) / CGFloat(rows))

        for (index, panel) in windows.enumerated() {
            let row = index / columns
            let column = index % columns
            // AppKit coordinates grow upward. Start from the top-left cell so
            // sources follow normal reading order and never cascade on top of
            // one another merely because they were opened together.
            let x = usable.minX + CGFloat(column) * (width + gap)
            let y = usable.maxY - CGFloat(row + 1) * height - CGFloat(row) * gap
            panel.setFrame(
                NSRect(x: x, y: y, width: width, height: height),
                display: true,
                animate: true
            )
        }
        nativeTrace("research.display_tiled pages=\(count) columns=\(columns) rows=\(rows)")
    }

    private func openResearchPages(_ rawURLs: [String]) {
        // Deep research may open a broader source set.  Eight panels fit on
        // the current desktop grid without reverting to overlapping cascades.
        guard rawURLs.count > 0 && rawURLs.count <= 8 else {
            nativeTrace("research.display_rejected count=\(rawURLs.count)")
            return
        }
        let urls = rawURLs.compactMap { raw -> URL? in
            guard raw.count <= 2048,
                  let url = URL(string: raw),
                  ["https", "http"].contains(url.scheme?.lowercased() ?? ""),
                  url.host != nil, url.user == nil, url.password == nil else { return nil }
            return url
        }
        guard urls.count == rawURLs.count else {
            nativeTrace("research.display_rejected invalid_url")
            return
        }
        for url in urls {
            let configuration = WKWebViewConfiguration()
            configuration.websiteDataStore = .nonPersistent()
            let page = WKWebView(frame: .zero, configuration: configuration)
            let delegate = ResearchPageDelegate()
            page.navigationDelegate = delegate
            let panel = NSWindow(
                contentRect: NSRect(x: 0, y: 0, width: 760, height: 640),
                styleMask: [.titled, .closable, .miniaturizable, .resizable],
                backing: .buffered,
                defer: false
            )
            panel.title = "MERRICK Research · \(url.host ?? "Source")"
            // Research pages are normal working windows, rather than HUD
            // overlays.  Move them onto the user's current Space so an
            // automatic opening is immediately visible even when MERRICK is
            // floating across every desktop.
            panel.collectionBehavior = [.moveToActiveSpace]
            panel.contentView = page
            panel.isReleasedWhenClosed = false
            page.load(URLRequest(url: url, cachePolicy: .reloadRevalidatingCacheData))
            // A newly-created NSWindow is not visible until explicitly
            // ordered front.  Previously we filtered for visible panels
            // before doing this, so every new source window was excluded
            // from tiling and remained hidden.
            panel.makeKeyAndOrderFront(nil)
            researchWindows.append(panel)
            researchDelegates.append(delegate)
        }
        // Include any still-visible research panels from the same workspace:
        // opening another source set should make a best effort to keep all
        // research windows accessible rather than covering an older one.
        let visiblePanels = researchWindows.filter(\.isVisible)
        tileResearchWindows(visiblePanels)
        for panel in visiblePanels {
            panel.makeKeyAndOrderFront(nil)
        }
        NSApp.activate(ignoringOtherApps: true)
        nativeTrace("research.display_opened pages=\(urls.count)")
    }

    // MARK: - Conversation language

    private var speechRecognizerLocaleIdentifier: String {
        speechLanguage == "zh" ? "zh-CN" : "en-US"
    }

    private func sendSpeechLanguageState() {
        js("window.merrickNativeSpeechLanguage(\(jsString(speechLanguage)))")
    }

    private func setSpeechLanguage(_ body: [String: Any]) {
        guard let requested = body["language"] as? String,
              ["en", "zh"].contains(requested) else {
            nativeTrace("speech.language_rejected")
            return
        }
        guard requested != speechLanguage else {
            sendSpeechLanguageState()
            return
        }
        let wasListening = audioEngine.isRunning
        speechLanguage = requested
        UserDefaults.standard.set(requested, forKey: speechLanguagePreferenceKey)
        nativeTrace("speech.language_changed language=\(requested)")
        sendSpeechLanguageState()
        // SFSpeechRecognizer binds its locale to each recognition request.
        // Recreate only the request, never the audio engine, to retain the
        // stable microphone path and keep the language switch perceptibly fast.
        guard wasListening else { return }
        stopListening(final: false)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.16) { [weak self] in
            self?.startListening()
        }
    }

    // MARK: - Provider onboarding and credential storage

    private var merrickApplicationSupportDirectory: URL {
        FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Application Support/JarvisStark", isDirectory: true)
    }

    private var providerProfileURL: URL {
        merrickApplicationSupportDirectory.appendingPathComponent(providerProfileFilename)
    }

    private var providerConnectionURL: URL {
        merrickApplicationSupportDirectory.appendingPathComponent(providerConnectionFilename)
    }

    private var automationAccessProfileURL: URL {
        merrickApplicationSupportDirectory.appendingPathComponent(automationAccessFilename)
    }

    private func automationAccessProfile() -> AutomationAccessProfile {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        guard let data = try? Data(contentsOf: automationAccessProfileURL),
              let profile = try? decoder.decode(AutomationAccessProfile.self, from: data) else {
            return AutomationAccessProfile(enabled: false, root: nil, updatedAt: Date())
        }
        return profile
    }

    private func writeAutomationAccessProfile(_ profile: AutomationAccessProfile) throws {
        try FileManager.default.createDirectory(at: merrickApplicationSupportDirectory,
                                                withIntermediateDirectories: true,
                                                attributes: [.posixPermissions: 0o700])
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        try encoder.encode(profile).write(to: automationAccessProfileURL, options: [.atomic])
        try FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: automationAccessProfileURL.path)
    }

    private func automationWorkspaceDirectory() -> URL {
        let profile = automationAccessProfile()
        if profile.enabled, let root = profile.root {
            let candidate = URL(fileURLWithPath: root).standardizedFileURL
            if FileManager.default.fileExists(atPath: candidate.path) { return candidate }
        }
        return merrickApplicationSupportDirectory
            .appendingPathComponent("Workspace/Documents", isDirectory: true)
    }

    private func sendAutomationAccessState(message: String? = nil, ok: Bool? = nil) {
        let profile = automationAccessProfile()
        var payload: [String: Any] = [
            "enabled": profile.enabled,
            "root": profile.root ?? "",
            "auditPath": merrickApplicationSupportDirectory.appendingPathComponent("FileAudit/operations.jsonl").path,
        ]
        if let message { payload["message"] = message }
        if let ok { payload["ok"] = ok }
        js("window.merrickNativeAutomationAccessState(\(jsObject(payload)))")
    }

    private func chooseAutomationAccessRoot() {
        let panel = NSOpenPanel()
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = false
        panel.canCreateDirectories = false
        panel.prompt = "Use this folder"
        panel.message = "MERRICK can directly read and change files only inside this chosen folder. Every change is recorded locally."
        panel.beginSheetModal(for: window) { [weak self] response in
            guard let self, response == .OK, let url = panel.url else { return }
            let root = url.standardizedFileURL
            guard root.path != "/", !root.path.hasPrefix(self.merrickApplicationSupportDirectory.path) else {
                self.sendAutomationAccessState(message: "Choose a normal project or user folder, not MERRICK private state.", ok: false)
                return
            }
            let current = self.automationAccessProfile()
            do {
                try self.writeAutomationAccessProfile(AutomationAccessProfile(
                    enabled: current.enabled, root: root.path, updatedAt: Date()
                ))
                self.sendAutomationAccessState(message: "Folder selected. Enable Direct Automation to use it.", ok: true)
            } catch {
                self.sendAutomationAccessState(message: "MERRICK could not save that folder selection.", ok: false)
            }
        }
    }

    private func saveAutomationAccessPolicy(_ body: [String: Any]) {
        let enabled = body["enabled"] as? Bool ?? false
        let current = automationAccessProfile()
        guard !enabled || current.root != nil else {
            sendAutomationAccessState(message: "Choose a project or user folder before enabling Direct Automation.", ok: false)
            return
        }
        do {
            try writeAutomationAccessProfile(AutomationAccessProfile(
                enabled: enabled, root: current.root, updatedAt: Date()
            ))
            sendAutomationAccessState(
                message: enabled ? "Direct Automation is enabled. MERRICK will restart its local model layer to apply this folder." : "Direct Automation is disabled; MERRICK returned to its private Workspace.",
                ok: true
            )
            restartBackendForProviderChange()
        } catch {
            sendAutomationAccessState(message: "MERRICK could not update Direct Automation.", ok: false)
        }
    }

    private func openAutomationAudit() {
        let directory = merrickApplicationSupportDirectory.appendingPathComponent("FileAudit", isDirectory: true)
        do {
            try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true,
                                                    attributes: [.posixPermissions: 0o700])
            NSWorkspace.shared.activateFileViewerSelecting([directory])
        } catch {
            sendAutomationAccessState(message: "MERRICK could not open its local audit records.", ok: false)
        }
    }

    private func readProviderProfile() -> ProviderProfile? {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        guard let data = try? Data(contentsOf: providerProfileURL),
              let profile = try? decoder.decode(ProviderProfile.self, from: data),
              isValidProvider(profile.provider),
              isValidProviderModel(profile.model) else { return nil }
        return profile
    }

    private func writeProviderProfile(_ profile: ProviderProfile) throws {
        try FileManager.default.createDirectory(at: merrickApplicationSupportDirectory,
                                                withIntermediateDirectories: true,
                                                attributes: [.posixPermissions: 0o700])
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        let data = try encoder.encode(profile)
        try data.write(to: providerProfileURL, options: [.atomic])
        try FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: providerProfileURL.path)
    }

    private func readProviderConnectionRecord() -> ProviderConnectionRecord? {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        guard let data = try? Data(contentsOf: providerConnectionURL),
              let record = try? decoder.decode(ProviderConnectionRecord.self, from: data) else {
            return nil
        }
        return record
    }

    private func writeProviderConnectionRecord(_ record: ProviderConnectionRecord) throws {
        try FileManager.default.createDirectory(
            at: merrickApplicationSupportDirectory,
            withIntermediateDirectories: true,
            attributes: [.posixPermissions: 0o700]
        )
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        try encoder.encode(record).write(to: providerConnectionURL, options: [.atomic])
        try FileManager.default.setAttributes(
            [.posixPermissions: 0o600],
            ofItemAtPath: providerConnectionURL.path
        )
    }

    private func connectionRecord(
        for profile: ProviderProfile,
        outcome: ProviderProbeOutcome
    ) -> ProviderConnectionRecord {
        ProviderConnectionRecord(
            provider: profile.provider,
            model: profile.model,
            authMode: profile.authMode,
            profileUpdatedAt: profile.updatedAt,
            validatedAt: Date(),
            stage: outcome.ready ? .ready : .failed,
            code: outcome.code,
            message: outcome.message
        )
    }

    private func connectionRecordMatches(
        _ record: ProviderConnectionRecord,
        profile: ProviderProfile
    ) -> Bool {
        record.provider == profile.provider &&
            record.model == profile.model &&
            record.authMode == profile.authMode &&
            abs(record.profileUpdatedAt.timeIntervalSince(profile.updatedAt)) < 1.0
    }

    private func isValidProvider(_ value: String) -> Bool {
        RuntimeContract.providers[value] != nil
    }

    private func isValidProviderModel(_ value: String) -> Bool {
        guard !value.isEmpty, value.count <= 120 else { return false }
        return value.unicodeScalars.allSatisfy { scalar in
            scalar.value >= 0x21 && scalar.value <= 0x7e && scalar.value != 0x5c && scalar.value != 0x22
        }
    }

    private func validatedBaseURL(_ value: String?, required: Bool) -> String? {
        guard let raw = value?.trimmingCharacters(in: .whitespacesAndNewlines), !raw.isEmpty else {
            return required ? nil : nil
        }
        guard raw.count <= 300,
              let url = URL(string: raw),
              url.scheme?.lowercased() == "https",
              url.host != nil,
              url.user == nil,
              url.password == nil,
              url.fragment == nil else { return nil }
        return url.absoluteString
    }

    private func providerKeychainAccount(_ provider: String) -> String {
        "provider.\(provider)"
    }

    private func saveProviderCredential(_ secret: String, provider: String) -> OSStatus {
        let account = providerKeychainAccount(provider)
        let data = Data(secret.utf8)
        let query: [CFString: Any] = [
            kSecClass: kSecClassGenericPassword,
            kSecAttrService: providerKeychainService,
            kSecAttrAccount: account,
        ]
        let updates: [CFString: Any] = [kSecValueData: data]
        let updateStatus = SecItemUpdate(query as CFDictionary, updates as CFDictionary)
        if updateStatus == errSecSuccess { return updateStatus }
        guard updateStatus == errSecItemNotFound else { return updateStatus }
        var item = query
        item[kSecValueData] = data
        item[kSecAttrAccessible] = kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        return SecItemAdd(item as CFDictionary, nil)
    }

    private func providerCredential(for provider: String) -> String? {
        let query: [CFString: Any] = [
            kSecClass: kSecClassGenericPassword,
            kSecAttrService: providerKeychainService,
            kSecAttrAccount: providerKeychainAccount(provider),
            kSecReturnData: true,
            kSecMatchLimit: kSecMatchLimitOne,
        ]
        var result: CFTypeRef?
        guard SecItemCopyMatching(query as CFDictionary, &result) == errSecSuccess,
              let data = result as? Data,
              let secret = String(data: data, encoding: .utf8),
              !secret.isEmpty else { return nil }
        return secret
    }

    @discardableResult
    private func deleteProviderCredential(for provider: String) -> OSStatus {
        let query: [CFString: Any] = [
            kSecClass: kSecClassGenericPassword,
            kSecAttrService: providerKeychainService,
            kSecAttrAccount: providerKeychainAccount(provider),
        ]
        let status = SecItemDelete(query as CFDictionary)
        return status == errSecItemNotFound ? errSecSuccess : status
    }

    /// Commit a connection only after its live provider probe succeeds. If
    /// Keychain or either metadata write fails, restore the previous usable
    /// connection rather than stranding the user on a half-saved selection.
    private func commitValidatedProviderConnection(
        profile: ProviderProfile,
        apiKey: String?,
        outcome: ProviderProbeOutcome
    ) -> Bool {
        guard outcome.ready else { return false }
        let oldCredential = providerCredential(for: profile.provider)
        let oldProfileData = try? Data(contentsOf: providerProfileURL)
        let oldConnectionData = try? Data(contentsOf: providerConnectionURL)

        if let apiKey {
            let status = saveProviderCredential(apiKey, provider: profile.provider)
            guard status == errSecSuccess else {
                nativeTrace("provider.keychain_save_failed status=\(status)")
                return false
            }
        }

        do {
            try writeProviderProfile(profile)
            try writeProviderConnectionRecord(connectionRecord(for: profile, outcome: outcome))
            return true
        } catch {
            nativeTrace("provider.commit_rollback error=\(error.localizedDescription)")
            if let oldCredential {
                _ = saveProviderCredential(oldCredential, provider: profile.provider)
            } else if apiKey != nil {
                _ = deleteProviderCredential(for: profile.provider)
            }
            restoreProviderMetadata(oldProfileData, at: providerProfileURL)
            restoreProviderMetadata(oldConnectionData, at: providerConnectionURL)
            return false
        }
    }

    private func restoreProviderMetadata(_ data: Data?, at url: URL) {
        if let data {
            try? data.write(to: url, options: [.atomic])
            try? FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: url.path)
        } else {
            try? FileManager.default.removeItem(at: url)
        }
    }

    private func applyProviderEnvironment(_ environment: inout [String: String]) {
        merrickApplyOpenClawIsolation(
            &environment,
            stateDirectory: merrickApplicationSupportDirectory.appendingPathComponent("OpenClaw", isDirectory: true),
            workspaceDirectory: automationWorkspaceDirectory()
        )
        let address = ownerAddressPreferences()
        environment["JARVIS_OWNER_ADDRESS_EN"] = address.english
        environment["JARVIS_OWNER_ADDRESS_ZH"] = address.chinese
        environment["JARVIS_PROJECT_ROOT"] = projectRoot.path
        let profile = readProviderProfile() ?? ProviderProfile(
            provider: RuntimeContract.defaultProvider.id,
            model: RuntimeContract.defaultProvider.defaultModel,
            baseURL: nil,
            authMode: RuntimeContract.defaultProvider.profileAuthMode,
            updatedAt: Date()
        )
        let apiKey = profile.authMode == "api"
            ? providerCredential(for: profile.provider)
            : nil
        // Keep the backend, Gateway, doctor, and one-off probes on one
        // effective provider contract, including legacy installs that predate
        // provider-profile.json. Credentials remain child-process-only.
        configureProviderEnvironment(&environment, profile: profile, apiKey: apiKey)
    }

    /// MERRICK does not borrow a global `~/.codex` login.  Subscription OAuth
    /// is instead placed in the application-owned OpenClaw agent store.  This
    /// supplies the same paths to the one-off connection flow as the gateway
    /// receives after it starts.
    private func merrickOpenClawEnvironment(
        profile: ProviderProfile? = nil,
        apiKey: String? = nil
    ) -> [String: String] {
        let stateDirectory = merrickApplicationSupportDirectory.appendingPathComponent("OpenClaw", isDirectory: true)
        let workspaceDirectory = automationWorkspaceDirectory()
        var environment = ProcessInfo.processInfo.environment
        merrickApplyOpenClawIsolation(
            &environment, stateDirectory: stateDirectory, workspaceDirectory: workspaceDirectory
        )
        environment["JARVIS_PROJECT_ROOT"] = projectRoot.path
        // The template is also rendered by one-off validation and connection
        // probes, before a random live Gateway port exists.  Those callers need
        // a valid loopback origin; the live dashboard/gateway paths replace it
        // with the owner-file port.
        environment["JARVIS_OPENCLAW_PUBLIC_ORIGIN"] = "http://127.0.0.1:18789"
        configureProviderEnvironment(
            &environment,
            profile: profile ?? ProviderProfile(
                provider: RuntimeContract.defaultProvider.id,
                model: RuntimeContract.defaultProvider.defaultModel,
                baseURL: nil,
                authMode: RuntimeContract.defaultProvider.profileAuthMode,
                updatedAt: Date()
            ),
            apiKey: apiKey
        )
        let bundledNodeDirectory = projectRoot.appendingPathComponent("node/bin", isDirectory: true)
        let cachedNodeDirectory = URL(fileURLWithPath: NSHomeDirectory())
            .appendingPathComponent(".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin", isDirectory: true)
        let nodeDirectory = FileManager.default.isExecutableFile(atPath: bundledNodeDirectory.appendingPathComponent("node").path)
            ? bundledNodeDirectory : cachedNodeDirectory
        environment["NODE_BIN_DIR"] = nodeDirectory.path
        environment["PATH"] = nodeDirectory.path + ":" + projectRoot.appendingPathComponent("node_modules/.bin").path + ":/opt/homebrew/bin:/usr/local/bin:" + (environment["PATH"] ?? "")
        return environment
    }

    private func configureProviderEnvironment(
        _ environment: inout [String: String],
        profile: ProviderProfile,
        apiKey: String?
    ) {
        for name in [
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY",
            "GOOGLE_API_KEY", "MOONSHOT_API_KEY", "DEEPSEEK_API_KEY",
            "JARVIS_MODEL_API_KEY",
        ] {
            environment.removeValue(forKey: name)
        }

        environment["JARVIS_SELECTED_PROVIDER"] = profile.provider
        environment["JARVIS_SELECTED_MODEL"] = profile.model
        guard let contract = RuntimeContract.providers[profile.provider] else { return }
        environment["JARVIS_OPENAI_RUNTIME"] = contract.openAIRuntime
        environment["JARVIS_ANTHROPIC_RUNTIME"] = contract.anthropicRuntime
        environment["JARVIS_MAIN_MODEL"] = "\(contract.runtimeRoute)/\(profile.model)"
        environment["JARVIS_CONVERSATION_MODEL"] = contract.conversationModel
            ?? "\(contract.runtimeRoute)/\(profile.model)"
        environment["JARVIS_SELECTED_BASE_URL"] = profile.baseURL ?? contract.defaultBaseURL
        environment["JARVIS_CODEX_COMPUTER_USE_MARKETPLACE_PATH"] = projectRoot
            .appendingPathComponent("openclaw/codex-computer-use-marketplace/.agents/plugins/marketplace.json")
            .path

        // The shared OpenClaw template declares every supported API route.
        // OAuth does not use this value, but OpenClaw 2.0 still resolves the
        // inactive routes while loading auth commands and requires the SecretRef.
        environment["JARVIS_MODEL_API_KEY"] = apiKey ?? "unused"
        guard let apiKey else { return }
        for name in contract.credentialEnvironmentNames {
            environment[name] = apiKey
        }
    }

    private func merrickOpenClawCLI() -> (node: URL, entry: URL)? {
        let entry = projectRoot.appendingPathComponent("node_modules/openclaw/openclaw.mjs")
        guard FileManager.default.fileExists(atPath: entry.path) else { return nil }
        let bundled = projectRoot.appendingPathComponent("node/bin/node")
        if FileManager.default.isExecutableFile(atPath: bundled.path) { return (bundled, entry) }
        let cached = URL(fileURLWithPath: NSHomeDirectory())
            .appendingPathComponent(".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")
        guard FileManager.default.isExecutableFile(atPath: cached.path) else { return nil }
        return (cached, entry)
    }

    /// OpenClaw 2.0 gives one process exclusive ownership of a state directory.
    /// A local model probe therefore cannot run beside MERRICK's own Gateway.
    /// Stopping the native-owned backend group is the narrow ownership-safe
    /// boundary; no global OpenClaw service or unrelated process is touched.
    private func pauseBackendForOAuthProbe() -> Bool {
        guard backend?.isRunning == true else { return false }
        backendHealthTask?.cancel()
        backendHealthTask = nil
        webReadyTimeoutWorkItem?.cancel()
        webReadyTimeoutWorkItem = nil
        terminateBackend(gracePeriod: 3.0)
        nativeTrace("provider.oauth_probe_gateway_paused")
        return true
    }

    private func restoreBackendAfterOAuthProbe(_ wasPaused: Bool, outcome: ProviderProbeOutcome) {
        guard wasPaused, !outcome.ready, backend == nil, !appTerminating else { return }
        nativeTrace("provider.oauth_probe_gateway_restoring code=\(outcome.code)")
        startBackend()
    }

    private func validateCandidateProviderConnection(
        profile: ProviderProfile,
        apiKey: String? = nil,
        expectedProfileID: String? = nil,
        completion: @escaping (ProviderProbeOutcome) -> Void
    ) {
        guard providerValidationProcess?.isRunning != true else {
            completion(.failure("VALIDATION_IN_PROGRESS", "Another provider check is already running."))
            return
        }
        guard let cli = merrickOpenClawCLI(),
              let probeProvider = ProviderProbeParser.probeProvider(for: profile.provider) else {
            completion(.failure("CONNECTOR_MISSING", "MERRICK’s provider connector is unavailable."))
            return
        }

        let fileManager = FileManager.default
        var cleanupDirectory: URL?
        var environment: [String: String]
        var backendPausedForProbe = false
        if profile.authMode == "jarvis-oauth" {
            synchronizeProviderGatewayTemplate()
            environment = merrickOpenClawEnvironment(profile: profile)
            sendProviderSetupProgress(message: "Checking the authorized account and selected model…")
            backendPausedForProbe = pauseBackendForOAuthProbe()
        } else {
            let root = fileManager.temporaryDirectory
                .appendingPathComponent("jarvis-provider-probe-\(UUID().uuidString)", isDirectory: true)
            let config = root.appendingPathComponent("openclaw.json")
            let workspace = root.appendingPathComponent("workspace", isDirectory: true)
            let source = projectRoot.appendingPathComponent("openclaw/openclaw.template.json5")
            do {
                try fileManager.createDirectory(
                    at: workspace,
                    withIntermediateDirectories: true,
                    attributes: [.posixPermissions: 0o700]
                )
                try fileManager.copyItem(at: source, to: config)
            } catch {
                completion(.failure("VALIDATION_SETUP_FAILED", "MERRICK could not prepare the provider check."))
                return
            }
            cleanupDirectory = root
            environment = merrickOpenClawEnvironment(profile: profile, apiKey: apiKey)
            merrickApplyOpenClawIsolation(
                &environment, stateDirectory: root, workspaceDirectory: workspace
            )
            environment["HOME"] = root.appendingPathComponent("native-home", isDirectory: true).path
            environment["XDG_CONFIG_HOME"] = root.appendingPathComponent("native-home/config", isDirectory: true).path
            environment["XDG_CACHE_HOME"] = root.appendingPathComponent("native-home/cache", isDirectory: true).path
            environment["XDG_DATA_HOME"] = root.appendingPathComponent("native-home/data", isDirectory: true).path
            environment["OPENCLAW_GATEWAY_TOKEN"] = String(repeating: "0", count: 64)
        }

        let output = Pipe()
        let process = Process()
        process.executableURL = cli.node
        process.arguments = [
            cli.entry.path, "models", "status", "--agent", "main",
            "--probe", "--probe-provider", probeProvider,
            "--probe-timeout", "12000", "--probe-max-tokens", "1", "--json",
        ] + (expectedProfileID.map { ["--probe-profile", $0] } ?? [])
        process.environment = environment
        process.standardInput = FileHandle.nullDevice
        process.standardOutput = output
        process.standardError = output

        do {
            try process.run()
            providerValidationProcess = process
            if Darwin.setpgid(process.processIdentifier, process.processIdentifier) == 0 ||
                Darwin.getpgid(process.processIdentifier) == process.processIdentifier {
                providerValidationProcessGroup = process.processIdentifier
            } else {
                providerValidationProcessGroup = nil
            }
        } catch {
            try? cleanupDirectory.map { try fileManager.removeItem(at: $0) }
            let outcome = ProviderProbeOutcome.failure(
                "CONNECTOR_LAUNCH_FAILED", "MERRICK could not start the provider check."
            )
            restoreBackendAfterOAuthProbe(backendPausedForProbe, outcome: outcome)
            completion(outcome)
            return
        }

        if !backendPausedForProbe {
            sendProviderSetupProgress(message: "Checking the selected provider and model…")
        }
        let timeoutLock = NSLock()
        var didTimeout = false
        let timeout = DispatchWorkItem { [weak self, weak process] in
            guard let self, let process, process.isRunning else { return }
            timeoutLock.lock()
            didTimeout = true
            timeoutLock.unlock()
            self.terminateProviderValidationProcessGroup()
        }
        DispatchQueue.global(qos: .utility).asyncAfter(deadline: .now() + 18, execute: timeout)
        DispatchQueue.global(qos: .utility).async { [weak self, weak process] in
            guard let self, let process else { return }
            let data = (try? output.fileHandleForReading.readToEnd()) ?? Data()
            process.waitUntilExit()
            timeout.cancel()
            let text = String(data: data, encoding: .utf8) ?? ""
            timeoutLock.lock()
            let timedOut = didTimeout
            timeoutLock.unlock()
            DispatchQueue.main.async { [weak self, weak process] in
                guard let self, let process else { return }
                if self.providerValidationProcess === process {
                    self.providerValidationProcess = nil
                    self.providerValidationProcessGroup = nil
                }
                if let cleanupDirectory {
                    try? fileManager.removeItem(at: cleanupDirectory)
                }
                if timedOut {
                    let outcome = ProviderProbeParser.failureOutcome("PROBE_TIMEOUT")
                    self.restoreBackendAfterOAuthProbe(backendPausedForProbe, outcome: outcome)
                    completion(outcome)
                    return
                }
                let outcome = ProviderProbeParser.parse(
                    text,
                    expectedProvider: probeProvider,
                    expectedProfileID: expectedProfileID
                )
                self.nativeTrace(
                    "provider.probe_completed provider=\(profile.provider) code=\(outcome.code) status=\(process.terminationStatus)"
                )
                self.restoreBackendAfterOAuthProbe(backendPausedForProbe, outcome: outcome)
                completion(outcome)
            }
        }
    }

    private func terminateProviderLoginProcessGroup() {
        terminateOwnedProviderProcess(
            providerLoginProcess,
            processGroup: providerLoginProcessGroup
        )
    }

    private func terminateProviderValidationProcessGroup() {
        terminateOwnedProviderProcess(
            providerValidationProcess,
            processGroup: providerValidationProcessGroup
        )
    }

    private func terminateOwnedProviderProcess(_ process: Process?, processGroup: pid_t?) {
        guard let process, process.isRunning else { return }
        if let processGroup, processGroup > 1,
           Darwin.getpgid(process.processIdentifier) == processGroup {
            _ = Darwin.kill(-processGroup, SIGTERM)
            let deadline = Date().addingTimeInterval(0.5)
            while Darwin.kill(-processGroup, 0) == 0 && Date() < deadline {
                Thread.sleep(forTimeInterval: 0.025)
            }
            if Darwin.kill(-processGroup, 0) == 0 {
                _ = Darwin.kill(-processGroup, SIGKILL)
            }
        } else {
            process.terminate()
            let deadline = Date().addingTimeInterval(0.5)
            while process.isRunning && Date() < deadline {
                Thread.sleep(forTimeInterval: 0.025)
            }
            if process.isRunning { _ = Darwin.kill(process.processIdentifier, SIGKILL) }
        }
    }

    private func merrickCodexOAuthProfileExists() -> Bool {
        guard let cli = merrickOpenClawCLI() else { return false }
        let contract = RuntimeContract.defaultProvider
        let process = Process()
        let output = Pipe()
        process.executableURL = cli.node
        process.arguments = [
            cli.entry.path, "models", "auth", "--agent", "main", "list",
            "--provider", contract.probeRoute, "--json",
        ]
        process.environment = merrickOpenClawEnvironment()
        process.standardOutput = output
        process.standardError = FileHandle.nullDevice
        do {
            try process.run()
            process.waitUntilExit()
            guard process.terminationStatus == 0,
                  let data = try? output.fileHandleForReading.readToEnd(),
                  let root = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let profiles = root["profiles"] as? [[String: Any]] else { return false }
            return profiles.contains { ($0["id"] as? String) == contract.probeProfileID }
        } catch {
            return false
        }
    }

    private func providerConnectionIsUsable(_ profile: ProviderProfile?) -> Bool {
        guard let profile,
              let contract = RuntimeContract.providers[profile.provider],
              profile.authMode == contract.profileAuthMode,
              let record = readProviderConnectionRecord(),
              connectionRecordMatches(record, profile: profile),
              record.isReady else { return false }
        if contract.authMode == "api" {
            return providerCredential(for: profile.provider) != nil
        }
        return contract.authMode == "cli"
    }

    private func completeMerrickCodexConnection(
        model: String,
        startLoginOnAuthFailure: Bool = false
    ) {
        guard providerValidationProcess?.isRunning != true else { return }
        if let login = providerLoginProcess, login.isRunning {
            let group = providerLoginProcessGroup
            providerLoginProcess = nil
            providerLoginProcessGroup = nil
            terminateOwnedProviderProcess(login, processGroup: group)
        }
        let contract = RuntimeContract.defaultProvider
        let profile = ProviderProfile(
            provider: contract.id,
            model: model,
            baseURL: nil,
            authMode: contract.profileAuthMode,
            updatedAt: Date()
        )
        validateCandidateProviderConnection(
            profile: profile,
            expectedProfileID: contract.probeProfileID
        ) { [weak self] outcome in
            guard let self else { return }
            guard outcome.ready else {
                if startLoginOnAuthFailure && outcome.code == "AUTH_REJECTED" {
                    self.startMerrickCodexDeviceConnection(model: model)
                    return
                }
                self.sendProviderFailure(outcome)
                return
            }
            guard self.commitValidatedProviderConnection(
                profile: profile,
                apiKey: nil,
                outcome: outcome
            ) else {
                self.sendProviderSetupResult(
                    ok: false,
                    message: "The verified connection could not be saved; the previous connection was restored."
                )
                return
            }
            UserDefaults.standard.set(true, forKey: self.onboardingCompletedKey)
            self.nativeTrace("provider.jarvis_oauth_verified")
            self.sendProviderSetupResult(ok: true, message: "Connection verified. Restarting MERRICK’s local model layer…")
            self.restartBackendForProviderChange()
        }
    }

    private func monitorMerrickCodexLogin(model: String) {
        guard let monitoredProcess = providerLoginProcess else { return }
        // The bundled OpenClaw flow owns a 15-minute device approval window.
        // This outer watchdog also allows startup and token exchange; keep its
        // contract test in sync when upgrading the bundled connector.
        DispatchQueue.main.asyncAfter(deadline: .now() + 16 * 60) { [weak self, weak monitoredProcess] in
            guard let self, let monitoredProcess,
                  self.providerLoginProcess === monitoredProcess,
                  monitoredProcess.isRunning else { return }
            let group = self.providerLoginProcessGroup
            self.providerLoginProcess = nil
            self.providerLoginProcessGroup = nil
            self.terminateOwnedProviderProcess(monitoredProcess, processGroup: group)
            self.nativeTrace("provider.jarvis_oauth_timeout")
            self.sendProviderSetupResult(ok: false, message: "The MERRICK model sign-in timed out and was closed. You can safely try Connect again.")
        }
    }

    private func hasExistingOpenClawUserState() -> Bool {
        let root = merrickApplicationSupportDirectory.appendingPathComponent("OpenClaw", isDirectory: true)
        let evidence = [
            root.appendingPathComponent("agents/main/agent/openclaw-agent.sqlite"),
            root.appendingPathComponent("agents/main/sessions/sessions.json"),
            root.appendingPathComponent("state/openclaw.sqlite"),
        ]
        return evidence.contains { FileManager.default.fileExists(atPath: $0.path) }
    }

    private func providerStatePayload(message: String? = nil, success: Bool? = nil) -> [String: Any] {
        let profile = readProviderProfile()
        let usable = providerConnectionIsUsable(profile)
        let existingOpenClawState = hasExistingOpenClawUserState()
        let onboardingCompleted = UserDefaults.standard.bool(forKey: onboardingCompletedKey)
        let onboardingRequired = profile == nil && !existingOpenClawState && !onboardingCompleted
        let effectiveProfile = profile ?? ProviderProfile(
            provider: RuntimeContract.defaultProvider.id,
            model: RuntimeContract.defaultProvider.defaultModel,
            baseURL: nil,
            authMode: RuntimeContract.defaultProvider.profileAuthMode,
            updatedAt: Date()
        )
        let address = ownerAddressPreferences()
        var payload: [String: Any] = [
            "configured": usable,
            "onboardingRequired": onboardingRequired,
            "provider": effectiveProfile.provider,
            "model": effectiveProfile.model,
            "baseURL": effectiveProfile.baseURL ?? "",
            "authMode": effectiveProfile.authMode,
            "connectionStage": usable
                ? ProviderConnectionStage.ready.rawValue
                : (existingOpenClawState
                    ? ProviderConnectionStage.validating.rawValue
                    : ProviderConnectionStage.notConfigured.rawValue),
            "connectionErrorCode": usable
                ? "READY"
                : (existingOpenClawState ? "VALIDATION_REQUIRED" : "NOT_CONFIGURED"),
            "addressEnglish": address.english,
            "addressChinese": address.chinese,
        ]
        if existingOpenClawState && profile == nil {
            payload["legacyLocalConnection"] = true
            payload["connectionScope"] = "jarvis"
            payload["connectionMessage"] = "Existing MERRICK local model state detected; runtime verification is in progress."
        }
        if let profile {
            if RuntimeContract.providers[profile.provider]?.probeProfileID != nil {
                payload["connectionScope"] = "jarvis"
            }
            // A saved selection is not a connection. Report ready only when
            // its credential exists in the same app-owned store the runtime
            // uses; stale and legacy profiles must reopen setup.
            payload["requiresReconnect"] = !usable
            if let record = readProviderConnectionRecord(),
               connectionRecordMatches(record, profile: profile) {
                payload["connectionStage"] = record.stage.rawValue
                payload["connectionErrorCode"] = record.code
                payload["connectionMessage"] = record.message
            } else {
                payload["connectionStage"] = ProviderConnectionStage.credentialStored.rawValue
                payload["connectionErrorCode"] = "VALIDATION_REQUIRED"
                payload["connectionMessage"] = "Reconnect once so MERRICK can verify this provider and model."
            }
        }
        if let message { payload["message"] = message }
        if let success { payload["ok"] = success }
        return payload
    }

    private func jsObject(_ value: [String: Any]) -> String {
        guard JSONSerialization.isValidJSONObject(value),
              let data = try? JSONSerialization.data(withJSONObject: value),
              let source = String(data: data, encoding: .utf8) else { return "{}" }
        return source
    }

    private func sendProviderSetupState() {
        js("window.merrickNativeProviderSetupState(\(jsObject(providerStatePayload())))")
        // Reopening/reloading Settings must recover the still-active device
        // prompt, not require a second sign-in or discard its one-time code.
        if providerLoginProcess?.isRunning == true {
            sendProviderSetupProgress(
                message: "Enter the code shown in MERRICK on the secure sign-in page. Waiting for your approval…",
                deviceCode: providerPresentedDeviceCode,
                verificationURL: providerVerificationURL
            )
        } else if providerValidationProcess?.isRunning == true {
            sendProviderSetupProgress(message: "Verifying the selected model connection…")
        }
    }

    private func markProviderConnectionFailed(_ body: [String: Any]) {
        guard let code = body["code"] as? String,
              let failure = RuntimeContract.connectionFailures[code],
              failure.reconnectRequired,
              let profile = readProviderProfile() else { return }
        let outcome = ProviderProbeOutcome(
            ready: false,
            code: code,
            message: failure.messageEnglish,
            latencyMilliseconds: nil
        )
        do {
            try writeProviderConnectionRecord(connectionRecord(for: profile, outcome: outcome))
            nativeTrace("provider.runtime_connection_invalid code=\(code)")
            sendProviderSetupState()
        } catch {
            nativeTrace("provider.runtime_connection_state_failed error=\(error.localizedDescription)")
        }
    }

    private func ownerAddressPreferences() -> (english: String, chinese: String) {
        let defaults = UserDefaults.standard
        let english = defaults.string(forKey: ownerAddressEnglishKey)?.trimmingCharacters(in: .whitespacesAndNewlines)
        let chinese = defaults.string(forKey: ownerAddressChineseKey)?.trimmingCharacters(in: .whitespacesAndNewlines)
        return (
            english: (english?.isEmpty == false ? english! : "sir"),
            chinese: (chinese?.isEmpty == false ? chinese! : "先生")
        )
    }

    private func isValidOwnerAddress(_ value: String) -> Bool {
        let text = value.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, text.count <= 32,
              !text.unicodeScalars.contains(where: { $0.value < 0x20 || $0.value == 0x7F }) else { return false }
        return true
    }

    private func saveAddressPreferences(_ body: [String: Any]) {
        guard let english = body["english"] as? String,
              let chinese = body["chinese"] as? String,
              isValidOwnerAddress(english), isValidOwnerAddress(chinese) else {
            js("window.merrickNativeAddressPreferencesSaved(false, 'Please enter two short forms of address.')")
            return
        }
        UserDefaults.standard.set(english.trimmingCharacters(in: .whitespacesAndNewlines), forKey: ownerAddressEnglishKey)
        UserDefaults.standard.set(chinese.trimmingCharacters(in: .whitespacesAndNewlines), forKey: ownerAddressChineseKey)
        js("window.merrickNativeAddressPreferencesSaved(true, '')")
    }

    private func sendProviderSetupResult(ok: Bool, message: String) {
        providerPendingSelection = nil
        js("window.merrickNativeProviderSetupResult(\(jsObject(providerStatePayload(message: message, success: ok))))")
    }

    private func sendProviderFailure(_ outcome: ProviderProbeOutcome) {
        providerPendingSelection = nil
        var payload = providerStatePayload(message: outcome.message, success: false)
        payload["connectionStage"] = ProviderConnectionStage.failed.rawValue
        payload["connectionErrorCode"] = outcome.code
        payload["connectionMessage"] = outcome.message
        js("window.merrickNativeProviderSetupResult(\(jsObject(payload)))")
    }

    private func sendProviderSetupProgress(
        message: String,
        deviceCode: String? = nil,
        verificationURL: URL? = nil
    ) {
        var payload: [String: Any] = ["message": message]
        if let pending = providerPendingSelection {
            payload["provider"] = pending.provider
            payload["model"] = pending.model
        }
        if let deviceCode { payload["deviceCode"] = deviceCode }
        if let verificationURL { payload["verificationURL"] = verificationURL.absoluteString }
        js("window.merrickNativeProviderSetupProgress(\(jsObject(payload)))")
    }

    private func consumeProviderLoginOutput(_ data: Data, from process: Process) {
        guard let chunk = String(data: data, encoding: .utf8), !chunk.isEmpty else { return }
        DispatchQueue.main.async { [weak self] in
            guard let self, self.providerLoginProcess === process,
                  process.isRunning else { return }
            self.providerLoginOutput = String((self.providerLoginOutput + chunk).suffix(12_000))
            let prompt = ProviderLoginParser.parse(self.providerLoginOutput)
            let verification = prompt.verificationURL
            let deviceCode = prompt.deviceCode
            guard verification != nil || deviceCode != nil else { return }
            let nextVerification = verification ?? self.providerVerificationURL
            let nextDeviceCode = deviceCode ?? self.providerPresentedDeviceCode
            guard nextVerification != self.providerVerificationURL ||
                    nextDeviceCode != self.providerPresentedDeviceCode else { return }
            self.providerPresentedDeviceCode = nextDeviceCode
            self.nativeTrace("provider.jarvis_oauth_prompt url=\(verification != nil) code=\(deviceCode != nil)")
            if let verification, verification.scheme?.lowercased() == "https", verification.host != nil {
                self.providerVerificationURL = verification
                self.sendProviderSetupProgress(
                    message: "Enter the code shown in MERRICK on the secure sign-in page. Waiting for your approval…",
                    deviceCode: nextDeviceCode,
                    verificationURL: nextVerification
                )
            } else if let deviceCode {
                self.sendProviderSetupProgress(
                    message: "Enter this code in the browser to connect MERRICK.",
                    deviceCode: deviceCode,
                    verificationURL: nextVerification
                )
            }
        }
    }

    private func startMerrickCodexDeviceConnection(model: String) {
        guard let cli = merrickOpenClawCLI() else {
            sendProviderSetupResult(ok: false, message: "MERRICK’s bundled model connector is unavailable. Reinstall MERRICK and try again.")
            return
        }
        synchronizeProviderGatewayTemplate()
        let output = Pipe()
        let process = Process()
        // OpenClaw intentionally requires an interactive terminal even for
        // device-code OAuth. A GUI-launched Process has no TTY, so run the
        // signed bundled CLI inside macOS's PTY wrapper. Without this the CLI
        // exits before displaying the consent URL or saving a credential.
        process.executableURL = URL(fileURLWithPath: "/usr/bin/script")
        let contract = RuntimeContract.defaultProvider
        guard let profileID = contract.probeProfileID else {
            sendProviderSetupResult(ok: false, message: "The MERRICK sign-in profile is unavailable.")
            return
        }
        process.arguments = [
            "-q", "/dev/null", cli.node.path, cli.entry.path,
            "models", "auth", "--agent", "main", "login", "--provider", contract.probeRoute,
            "--profile-id", profileID, "--device-code",
        ]
        process.environment = merrickOpenClawEnvironment()
        process.standardInput = FileHandle.nullDevice
        process.standardOutput = output
        process.standardError = output
        providerLoginOutput = ""
        providerVerificationURL = nil
        providerPresentedDeviceCode = nil
        output.fileHandleForReading.readabilityHandler = { [weak self, weak process] handle in
            let data = handle.availableData
            guard let process, !data.isEmpty else { return }
            self?.consumeProviderLoginOutput(data, from: process)
        }
        process.terminationHandler = { [weak self, weak process] completed in
            output.fileHandleForReading.readabilityHandler = nil
            DispatchQueue.main.async {
                guard let self, let process, self.providerLoginProcess === process else { return }
                self.providerLoginProcess = nil
                self.providerLoginProcessGroup = nil
                if self.merrickCodexOAuthProfileExists() {
                    self.completeMerrickCodexConnection(model: model)
                } else if completed.terminationStatus == 0 {
                    self.sendProviderSetupResult(ok: false, message: "The sign-in finished but MERRICK could not verify its local connection. Try Connect again.")
                } else {
                    self.nativeTrace("provider.jarvis_oauth_failed status=\(completed.terminationStatus)")
                    self.sendProviderSetupResult(ok: false, message: "The MERRICK sign-in did not complete, so MERRICK is still not connected. Try Connect again.")
                }
            }
        }
        do {
            try process.run()
            providerLoginProcess = process
            if Darwin.setpgid(process.processIdentifier, process.processIdentifier) == 0 ||
                Darwin.getpgid(process.processIdentifier) == process.processIdentifier {
                providerLoginProcessGroup = process.processIdentifier
            } else {
                providerLoginProcessGroup = nil
            }
            nativeTrace("provider.jarvis_oauth_in_app_started")
            sendProviderSetupProgress(message: "Creating a secure browser connection…")
            monitorMerrickCodexLogin(model: model)
        } catch {
            output.fileHandleForReading.readabilityHandler = nil
            nativeTrace("provider.jarvis_oauth_in_app_launch_failed error=\(error.localizedDescription)")
            sendProviderSetupResult(ok: false, message: "MERRICK could not start its local sign-in connector, and no connection was saved.")
        }
    }

    private func cancelProviderConnection() {
        guard let process = providerLoginProcess, process.isRunning else { return }
        let group = providerLoginProcessGroup
        providerLoginProcess = nil
        providerLoginProcessGroup = nil
        terminateOwnedProviderProcess(process, processGroup: group)
        providerVerificationURL = nil
        providerPresentedDeviceCode = nil
        nativeTrace("provider.connection_cancelled")
        sendProviderSetupResult(ok: false, message: "The connection was cancelled. No new MERRICK connection was saved.")
    }

    private func openProviderVerificationURL() {
        guard let url = providerVerificationURL else { return }
        _ = NSWorkspace.shared.open(url)
    }

    private func saveProviderAPIKey(_ body: [String: Any]) {
        guard let provider = body["provider"] as? String,
              let contract = RuntimeContract.providers[provider], contract.authMode == "api",
              let model = body["model"] as? String, isValidProviderModel(model) else {
            nativeTrace("provider.api_key_rejected")
            sendProviderSetupResult(ok: false, message: "The provider details were invalid. The key was not saved.")
            return
        }
        let rawBaseURL = body["baseUrl"] as? String
        guard !contract.baseURLRequired || validatedBaseURL(rawBaseURL, required: true) != nil,
              contract.baseURLRequired || rawBaseURL == nil || rawBaseURL?.isEmpty == true || validatedBaseURL(rawBaseURL, required: false) != nil else {
            sendProviderSetupResult(ok: false, message: "Use a valid HTTPS base URL, or leave it blank for this provider.")
            return
        }
        let baseURL = validatedBaseURL(rawBaseURL, required: contract.baseURLRequired)
        var apiKey = body["apiKey"] as? String ?? ""
        if apiKey.isEmpty && body["reuseSavedKey"] as? Bool == true {
            // Never send a saved credential to a different provider or endpoint.
            guard let current = readProviderProfile(),
                  current.provider == provider, current.baseURL == baseURL,
                  providerConnectionIsUsable(current),
                  let stored = providerCredential(for: provider) else {
                sendProviderSetupResult(ok: false, message: "To change the provider or endpoint, enter its API key. The current connection was kept.")
                return
            }
            apiKey = stored
        }
        guard apiKey.count >= 8, apiKey.count <= 1024,
              !apiKey.contains(where: { $0.isNewline || $0.isWhitespace }) else {
            sendProviderSetupResult(ok: false, message: "Enter a valid API key. The current connection was kept.")
            return
        }
        let profile = ProviderProfile(
            provider: provider,
            model: model,
            baseURL: baseURL,
            authMode: contract.profileAuthMode,
            updatedAt: Date()
        )
        providerPendingSelection = (provider, model)
        validateCandidateProviderConnection(profile: profile, apiKey: apiKey) { [weak self] outcome in
            guard let self else { return }
            guard outcome.ready else {
                self.nativeTrace("provider.api_probe_failed provider=\(provider) code=\(outcome.code)")
                self.sendProviderFailure(outcome)
                return
            }
            guard self.commitValidatedProviderConnection(
                profile: profile,
                apiKey: apiKey,
                outcome: outcome
            ) else {
                self.sendProviderSetupResult(
                    ok: false,
                    message: "The credential was verified but could not be saved; the previous connection was restored."
                )
                return
            }
            UserDefaults.standard.set(true, forKey: self.onboardingCompletedKey)
            self.nativeTrace("provider.api_connection_verified provider=\(provider)")
            self.sendProviderSetupResult(ok: true, message: "Connection verified. Restarting MERRICK’s local model layer…")
            self.restartBackendForProviderChange()
        }
    }

    private func finishProviderOnboarding() {
        guard let profile = readProviderProfile() else {
            sendProviderSetupResult(ok: false, message: "Connect a model before completing setup.")
            return
        }
        guard providerConnectionIsUsable(profile) else {
            sendProviderSetupResult(ok: false, message: "This saved model selection has no usable credential. Reconnect the MERRICK model first.")
            return
        }
        UserDefaults.standard.set(true, forKey: onboardingCompletedKey)
        nativeTrace("provider.onboarding_finished existing_connection=true")
        sendProviderSetupResult(ok: true, message: "Using MERRICK’s current local connection.")
    }

    private func validateClaudeCLIConnection(
        model: String,
        completion: @escaping (ProviderProbeOutcome) -> Void
    ) {
        guard providerValidationProcess?.isRunning != true else {
            completion(.failure("VALIDATION_IN_PROGRESS", "Another provider check is already running."))
            return
        }
        let output = Pipe()
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/env")
        process.arguments = [
            "claude", "-p", "Reply with OK only.",
            "--model", model,
            "--output-format", "json",
            "--max-turns", "1",
        ]
        var environment = ProcessInfo.processInfo.environment
        environment["PATH"] = NSHomeDirectory() + "/.local/bin:/opt/homebrew/bin:/usr/local/bin:" + (environment["PATH"] ?? "")
        process.environment = environment
        process.standardInput = FileHandle.nullDevice
        process.standardOutput = output
        process.standardError = output
        do {
            try process.run()
            providerValidationProcess = process
            if Darwin.setpgid(process.processIdentifier, process.processIdentifier) == 0 ||
                Darwin.getpgid(process.processIdentifier) == process.processIdentifier {
                providerValidationProcessGroup = process.processIdentifier
            } else {
                providerValidationProcessGroup = nil
            }
        } catch {
            completion(.failure("CLI_NOT_INSTALLED", "Claude Code CLI is not installed or could not be started."))
            return
        }

        sendProviderSetupProgress(message: "Checking Claude Code with a short live response…")
        let timeoutLock = NSLock()
        var didTimeout = false
        let timeout = DispatchWorkItem { [weak self, weak process] in
            guard let self, let process, process.isRunning else { return }
            timeoutLock.lock()
            didTimeout = true
            timeoutLock.unlock()
            self.terminateProviderValidationProcessGroup()
        }
        DispatchQueue.global(qos: .utility).asyncAfter(deadline: .now() + 25, execute: timeout)
        DispatchQueue.global(qos: .utility).async { [weak self, weak process] in
            guard let self, let process else { return }
            let data = (try? output.fileHandleForReading.readToEnd()) ?? Data()
            process.waitUntilExit()
            timeout.cancel()
            let detail = String(data: data, encoding: .utf8) ?? ""
            timeoutLock.lock()
            let timedOut = didTimeout
            timeoutLock.unlock()
            DispatchQueue.main.async { [weak self, weak process] in
                guard let self, let process else { return }
                if self.providerValidationProcess === process {
                    self.providerValidationProcess = nil
                    self.providerValidationProcessGroup = nil
                }
                if timedOut {
                    completion(ProviderProbeParser.failureOutcome("PROBE_TIMEOUT"))
                } else if process.terminationStatus == 0 && !detail.isEmpty {
                    completion(ProviderProbeOutcome(
                        ready: true,
                        code: "READY",
                        message: "Connection verified.",
                        latencyMilliseconds: nil
                    ))
                } else {
                    completion(ProviderProbeParser.classifyFailureText(detail))
                }
            }
        }
    }

    private func connectProviderCLI(_ body: [String: Any]) {
        guard let provider = body["provider"] as? String,
              let contract = RuntimeContract.providers[provider], contract.authMode == "cli",
              let model = body["model"] as? String, isValidProviderModel(model) else {
            sendProviderSetupResult(ok: false, message: "The local CLI connection request was invalid.")
            return
        }
        guard providerLoginProcess?.isRunning != true,
              providerValidationProcess?.isRunning != true else {
            sendProviderSetupResult(ok: false, message: "A provider sign-in is already in progress.")
            return
        }
        if provider == RuntimeContract.defaultProvider.id {
            providerPendingSelection = (provider, model)
            if merrickCodexOAuthProfileExists() {
                completeMerrickCodexConnection(model: model, startLoginOnAuthFailure: true)
                return
            }
            startMerrickCodexDeviceConnection(model: model)
            return
        }
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/env")
        process.arguments = ["claude", "auth", "login"]
        providerPendingSelection = (provider, model)
        var environment = ProcessInfo.processInfo.environment
        environment["PATH"] = NSHomeDirectory() + "/.local/bin:/opt/homebrew/bin:/usr/local/bin:" + (environment["PATH"] ?? "")
        process.environment = environment
        process.standardOutput = FileHandle.nullDevice
        process.standardError = FileHandle.nullDevice
        providerLoginProcess = process
        let progress = "Complete the sign-in in the browser window, then return to MERRICK."
        js("window.merrickNativeProviderSetupProgress(\(jsString(progress)))")
        process.terminationHandler = { [weak self] completed in
            DispatchQueue.main.async {
                guard let self else { return }
                self.providerLoginProcess = nil
                self.providerLoginProcessGroup = nil
                guard completed.terminationStatus == 0 else {
                    self.nativeTrace("provider.cli_login_failed provider=\(provider) status=\(completed.terminationStatus)")
                    self.sendProviderSetupResult(ok: false, message: "The local sign-in did not complete.")
                    return
                }
                self.validateClaudeCLIConnection(model: model) { [weak self] outcome in
                    guard let self else { return }
                    guard outcome.ready else {
                        self.sendProviderFailure(outcome)
                        return
                    }
                    let profile = ProviderProfile(
                        provider: provider,
                        model: model,
                        baseURL: nil,
                        authMode: contract.profileAuthMode,
                        updatedAt: Date()
                    )
                    guard self.commitValidatedProviderConnection(
                        profile: profile,
                        apiKey: nil,
                        outcome: outcome
                    ) else {
                        self.sendProviderSetupResult(ok: false, message: "The verified local connection could not be saved.")
                        return
                    }
                    UserDefaults.standard.set(true, forKey: self.onboardingCompletedKey)
                    self.nativeTrace("provider.cli_connection_verified provider=\(provider)")
                    self.sendProviderSetupResult(ok: true, message: "Connection verified. Restarting MERRICK…")
                    self.restartBackendForProviderChange()
                }
            }
        }
        do {
            try process.run()
            if Darwin.setpgid(process.processIdentifier, process.processIdentifier) == 0 ||
                Darwin.getpgid(process.processIdentifier) == process.processIdentifier {
                providerLoginProcessGroup = process.processIdentifier
            } else {
                providerLoginProcessGroup = nil
            }
        } catch {
            providerLoginProcess = nil
            providerLoginProcessGroup = nil
            nativeTrace("provider.cli_login_launch_failed provider=\(provider) error=\(error.localizedDescription)")
            sendProviderSetupResult(ok: false, message: "The required CLI could not be started. Install it and try again.")
        }
    }

    private func restartBackendForProviderChange() {
        guard !appTerminating else { return }
        // The gateway config is application-managed and contains no provider
        // credential. Refresh it from the signed project template so its model
        // routing matches the selected Keychain-backed provider. OAuth tokens,
        // session memory, and gateway secrets remain in separate files.
        synchronizeProviderGatewayTemplate()
        webReady = false
        webReadyTimeoutWorkItem?.cancel()
        webReadyTimeoutWorkItem = nil
        hudLoadStarted = false
        backendHealthTask?.cancel()
        backendHealthTask = nil
        webReadyTimeoutWorkItem?.cancel()
        webReadyTimeoutWorkItem = nil
        terminateBackend()
        startBackend()
    }

    private func synchronizeProviderGatewayTemplate() {
        guard let projectRoot else { return }
        let source = projectRoot.appendingPathComponent("openclaw/openclaw.template.json5")
        let target = merrickApplicationSupportDirectory
            .appendingPathComponent("OpenClaw/openclaw.json")
        guard FileManager.default.fileExists(atPath: source.path) else {
            nativeTrace("provider.config_template_missing")
            return
        }
        do {
            try FileManager.default.createDirectory(at: target.deletingLastPathComponent(),
                                                    withIntermediateDirectories: true,
                                                    attributes: [.posixPermissions: 0o700])
            let temporary = target.deletingLastPathComponent()
                .appendingPathComponent(".openclaw.json.provider-update")
            try? FileManager.default.removeItem(at: temporary)
            try FileManager.default.copyItem(at: source, to: temporary)
            try FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: temporary.path)
            if FileManager.default.fileExists(atPath: target.path) {
                _ = try FileManager.default.replaceItemAt(target, withItemAt: temporary)
            } else {
                try FileManager.default.moveItem(at: temporary, to: target)
            }
            nativeTrace("provider.config_template_refreshed")
        } catch {
            nativeTrace("provider.config_template_refresh_failed error=\(error.localizedDescription)")
        }
    }

    /// Refresh only app-owned OpenClaw identity instructions.  User memory,
    /// conversations, credentials, and user workspace files stay untouched.
    /// This makes MERRICK's product identity survive guest/isolated sessions
    /// and prevents OpenClaw's generic first-run templates from resurfacing.
    private func synchronizeOpenClawWorkspaceIdentity() {
        guard let projectRoot else { return }
        let fileManager = FileManager.default
        let stateRoot = merrickApplicationSupportDirectory
            .appendingPathComponent("OpenClaw", isDirectory: true)
        let workspaces = ["workspace", "action-planner-workspace"]
        let staticFiles = ["AGENTS.md", "IDENTITY.md", "SOUL.md"]

        do {
            for workspace in workspaces {
                let sourceDirectory = projectRoot
                    .appendingPathComponent("openclaw/\(workspace)", isDirectory: true)
                let targetDirectory = stateRoot
                    .appendingPathComponent(workspace, isDirectory: true)
                try fileManager.createDirectory(
                    at: targetDirectory,
                    withIntermediateDirectories: true,
                    attributes: [.posixPermissions: 0o700]
                )

                for filename in staticFiles {
                    let source = sourceDirectory.appendingPathComponent(filename)
                    guard fileManager.fileExists(atPath: source.path) else { continue }
                    let target = targetDirectory.appendingPathComponent(filename)
                    let temporary = targetDirectory.appendingPathComponent(".\(filename).jarvis-refresh")
                    try? fileManager.removeItem(at: temporary)
                    try fileManager.copyItem(at: source, to: temporary)
                    try fileManager.setAttributes([.posixPermissions: 0o600], ofItemAtPath: temporary.path)
                    if fileManager.fileExists(atPath: target.path) {
                        _ = try fileManager.replaceItemAt(target, withItemAt: temporary)
                    } else {
                        try fileManager.moveItem(at: temporary, to: target)
                    }
                }
            }
            nativeTrace("openclaw.global_identity_refreshed")
        } catch {
            nativeTrace("openclaw.global_identity_refresh_failed error=\(error.localizedDescription)")
        }
    }

    private func voiceprintManagementIsAuthorized() -> Bool {
        guard let expiry = voiceprintManagementAuthorizedUntil else { return false }
        return expiry > Date()
    }

    /// This uses macOS device-owner authentication. It accepts the Mac account
    /// password and, where enabled, Touch ID; MERRICK never receives or stores
    /// the password itself.
    private func authenticateVoiceprintManagement() {
        let context = LAContext()
        var authError: NSError?
        guard context.canEvaluatePolicy(.deviceOwnerAuthentication, error: &authError) else {
            let reason = authError?.localizedDescription ?? "Mac authentication is unavailable."
            nativeTrace("voiceprint.auth_unavailable")
            js("window.merrickNativeVoiceprintAuthorizationFailed(\(jsString(reason)))")
            return
        }
        context.evaluatePolicy(
            .deviceOwnerAuthentication,
            localizedReason: "Unlock MERRICK voiceprint management"
        ) { [weak self] success, error in
            DispatchQueue.main.async {
                guard let self else { return }
                guard success else {
                    let reason = error?.localizedDescription ?? "Authentication was cancelled."
                    self.nativeTrace("voiceprint.auth_failed")
                    self.js("window.merrickNativeVoiceprintAuthorizationFailed(\(self.jsString(reason)))")
                    return
                }
                self.voiceprintManagementAuthorizedUntil = Date().addingTimeInterval(180)
                self.nativeTrace("voiceprint.auth_granted")
                self.js("window.merrickNativeVoiceprintAuthorized()")
            }
        }
    }

    /// Capture a fixed, local 4.2-second sample after the user explicitly
    /// unlocks the vault. The WAV exists only in memory and is discarded after
    /// the backend derives an embedding.
    private func captureVoiceprintSample() {
        guard voiceprintManagementIsAuthorized() else {
            js("window.merrickNativeVoiceprintAuthorizationFailed(\(jsString("Please unlock voiceprint management first.")))")
            return
        }
        guard !assistantAudioPlaying else {
            js("window.merrickNativeVoiceprintCaptureFailed(\(jsString("Please wait for MERRICK to finish speaking.")))")
            return
        }
        manualVoiceprintCaptureWorkItem?.cancel()
        manualVoiceprintCaptureRequested = true
        manualVoiceprintCaptureGeneration = -1
        stopListening(final: false)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.18) { [weak self] in
            guard let self, self.manualVoiceprintCaptureRequested else { return }
            self.startListening()
        }
    }

    private func scheduleManualVoiceprintCaptureCompletion(for generation: Int) {
        let work = DispatchWorkItem { [weak self] in
            guard let self, self.manualVoiceprintCaptureGeneration == generation else { return }
            self.manualVoiceprintCaptureGeneration = -1
            self.manualVoiceprintCaptureWorkItem = nil
            let sample = self.currentVoiceSampleBase64(minimumSeconds: 3.5)
            self.stopListening(final: false)
            if let sample {
                self.nativeTrace("voiceprint.capture_completed generation=\(generation)")
                self.js("window.merrickNativeVoiceprintSample(\(self.jsString(sample)))")
            } else {
                self.nativeTrace("voiceprint.capture_too_short generation=\(generation)")
                self.js("window.merrickNativeVoiceprintCaptureFailed(\(self.jsString("No usable microphone sample was captured. Please try again.")))")
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.16) { [weak self] in
                self?.startListening()
            }
        }
        manualVoiceprintCaptureWorkItem = work
        DispatchQueue.main.asyncAfter(deadline: .now() + 4.2, execute: work)
    }

    private func isTrustedHUDURL(_ url: URL?) -> Bool {
        guard let url,
              url.scheme?.lowercased() == "http",
              url.host?.lowercased() == RuntimeContract.backendHost,
              url.port == RuntimeContract.backendPort,
              url.user == nil,
              url.password == nil else { return false }
        return true
    }

    private func isTrustedBridgeMessage(_ message: WKScriptMessage, body: [String: Any]) -> Bool {
        guard message.frameInfo.isMainFrame,
              isTrustedHUDURL(message.frameInfo.request.url) else { return false }
        let origin = message.frameInfo.securityOrigin
        guard origin.protocol.lowercased() == "http",
              origin.host.lowercased() == RuntimeContract.backendHost,
              origin.port == RuntimeContract.backendPort else { return false }
        return (body["bridge"] as? String) == bridgeToken
    }

    func webView(_ webView: WKWebView,
                 decidePolicyFor navigationAction: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        // The privileged script-message handler lives only on the HUD view.
        // Never let that view carry its native bridge to another origin, and
        // reject navigation from any unexpected WebView.
        let targetsMainFrame = navigationAction.targetFrame?.isMainFrame ?? true
        let trusted = webView === self.webView && targetsMainFrame &&
            isTrustedHUDURL(navigationAction.request.url)
        decisionHandler(trusted ? .allow : .cancel)
    }

    func webView(_ webView: WKWebView,
                 decidePolicyFor navigationResponse: WKNavigationResponse,
                 decisionHandler: @escaping (WKNavigationResponsePolicy) -> Void) {
        guard let url = navigationResponse.response.url else {
            decisionHandler(.cancel)
            return
        }
        // A local endpoint could redirect after the navigation-action check;
        // reject the response before foreign content is committed.
        let trusted = webView === self.webView &&
            navigationResponse.isForMainFrame &&
            isTrustedHUDURL(url) &&
            isAuthenticatedBackendResponse(navigationResponse.response, requireStatusOK: true)
        if !trusted { nativeTrace("hud.response_auth_rejected") }
        decisionHandler(trusted ? .allow : .cancel)
    }

    private func js(_ source: String) {
        DispatchQueue.main.async {
            self.webView.evaluateJavaScript(source) { _, error in
                if let error {
                    self.nativeTrace("hud.javascript_error error=\(error.localizedDescription)")
                }
            }
        }
    }
    private func jsString(_ value: String) -> String {
        let data = try! JSONSerialization.data(withJSONObject: [value])
        let array = String(data: data, encoding: .utf8)!
        return String(array.dropFirst().dropLast())
    }

    private func isValidScreenCaptureRequestID(_ requestID: String) -> Bool {
        let bytes = Array(requestID.utf8)
        return bytes.count == 32 && bytes.allSatisfy {
            (UInt8(ascii: "0")...UInt8(ascii: "9")).contains($0) ||
            (UInt8(ascii: "a")...UInt8(ascii: "f")).contains($0)
        }
    }

    private func isValidNativeActionRequestID(_ requestID: String) -> Bool {
        isValidScreenCaptureRequestID(requestID)
    }

    private func hasExactKeys(_ dictionary: [String: Any], _ keys: Set<String>) -> Bool {
        Set(dictionary.keys) == keys
    }

    private func isValidActionQuery(_ query: String, maximumLength: Int) -> Bool {
        guard !query.isEmpty,
              query.count <= maximumLength,
              query == query.trimmingCharacters(in: .whitespacesAndNewlines) else {
            return false
        }
        return !query.unicodeScalars.contains { scalar in
            scalar.value < 32 || scalar.value == 127
        }
    }

    private func isValidPublicWebURL(_ value: String) -> URL? {
        guard isValidActionQuery(value, maximumLength: 2_048),
              let components = URLComponents(string: value),
              let scheme = components.scheme?.lowercased(),
              scheme == "http" || scheme == "https",
              let host = components.host?.lowercased(),
              !host.isEmpty,
              components.user == nil,
              components.password == nil,
              let url = components.url else {
            return nil
        }
        // A result may only lead to the public web, never a loopback or local
        // network address. The host selects it from public search results.
        let blockedHosts = ["localhost", "::1", "0.0.0.0"]
        guard !blockedHosts.contains(host),
              !host.hasSuffix(".local"),
              !host.hasPrefix("127."),
              !host.hasPrefix("10."),
              !host.hasPrefix("192.168."),
              !host.hasPrefix("172.16.") else {
            return nil
        }
        return url
    }

    private func isValidApplicationName(_ name: String) -> Bool {
        return isValidActionQuery(name, maximumLength: 80) &&
            !name.contains("/") && !name.contains("\\")
    }

    private func parseGUIInteractionSteps(_ value: Any?) -> [GUIInteractionStep]? {
        guard let rawSteps = value as? [[String: Any]], !rawSteps.isEmpty, rawSteps.count <= 6 else {
            return nil
        }
        let keys: Set<String> = ["enter", "tab", "escape", "space", "up", "down", "left", "right", "pageup", "pagedown", "home", "end"]
        var steps: [GUIInteractionStep] = []
        for raw in rawSteps {
            guard let op = raw["op"] as? String else { return nil }
            switch op {
            case "click":
                guard hasExactKeys(raw, ["op", "x", "y"]),
                      let x = raw["x"] as? NSNumber,
                      let y = raw["y"] as? NSNumber,
                      x.intValue >= 0, x.intValue <= 1_000,
                      y.intValue >= 0, y.intValue <= 1_000 else { return nil }
                steps.append(.click(x: x.intValue, y: y.intValue))
            case "scroll":
                guard hasExactKeys(raw, ["op", "dy"]),
                      let dy = raw["dy"] as? NSNumber,
                      dy.intValue != 0, dy.intValue >= -8, dy.intValue <= 8 else { return nil }
                steps.append(.scroll(dy: dy.intValue))
            case "key":
                guard hasExactKeys(raw, ["op", "key"]),
                      let key = raw["key"] as? String,
                      keys.contains(key) else { return nil }
                steps.append(.key(key))
            case "type":
                guard hasExactKeys(raw, ["op", "text"]),
                      let text = raw["text"] as? String,
                      isValidActionQuery(text, maximumLength: 240) else { return nil }
                steps.append(.type(text))
            default:
                return nil
            }
        }
        return steps
    }

    private func normalizedApplicationName(_ name: String) -> String {
        let folded = name.folding(
            options: [.caseInsensitive, .diacriticInsensitive, .widthInsensitive],
            locale: Locale(identifier: "en_US_POSIX")
        )
        let words = folded
            .components(separatedBy: CharacterSet.alphanumerics.inverted)
            .filter { !$0.isEmpty && $0 != "the" && $0 != "app" && $0 != "application" }
        return words.joined(separator: " ")
    }

    private func installedApplicationURL(named requestedName: String) -> URL? {
        let normalizedRequest = normalizedApplicationName(requestedName)
        let targetName = applicationNameAliases[normalizedRequest] ?? normalizedRequest
        if let bundleID = knownApplicationBundleIDs[targetName],
           let url = NSWorkspace.shared.urlForApplication(withBundleIdentifier: bundleID) {
            return url
        }
        let homeApplications = FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Applications", isDirectory: true)
        let roots = [
            URL(fileURLWithPath: "/Applications", isDirectory: true),
            URL(fileURLWithPath: "/Applications/Utilities", isDirectory: true),
            URL(fileURLWithPath: "/System/Applications", isDirectory: true),
            URL(fileURLWithPath: "/System/Applications/Utilities", isDirectory: true),
            homeApplications,
        ]
        for root in roots {
            guard let entries = try? FileManager.default.contentsOfDirectory(
                at: root,
                includingPropertiesForKeys: [.isDirectoryKey],
                options: [.skipsHiddenFiles]
            ) else { continue }
            for url in entries where url.pathExtension.caseInsensitiveCompare("app") == .orderedSame {
                var names = [url.deletingPathExtension().lastPathComponent]
                if let bundle = Bundle(url: url) {
                    if let displayName = bundle.object(
                        forInfoDictionaryKey: "CFBundleDisplayName"
                    ) as? String { names.append(displayName) }
                    if let bundleName = bundle.object(
                        forInfoDictionaryKey: "CFBundleName"
                    ) as? String { names.append(bundleName) }
                }
                if names.contains(where: { normalizedApplicationName($0) == targetName }) {
                    return url
                }
            }
        }
        return nil
    }

    private func parseNativeAction(_ value: Any?) -> NativeAction? {
        guard let dictionary = value as? [String: Any],
              let type = dictionary["type"] as? String else {
            return nil
        }
        switch type {
        case "open_app":
            guard hasExactKeys(dictionary, ["type", "app"]),
                  let alias = dictionary["app"] as? String,
                  isValidApplicationName(alias) else { return nil }
            return .openApp(alias: alias)
        case "close_app":
            guard hasExactKeys(dictionary, ["type", "app"]),
                  let alias = dictionary["app"] as? String,
                  isValidApplicationName(alias) else { return nil }
            return .closeApp(alias: alias)
        case "browser_search":
            guard hasExactKeys(dictionary, ["type", "browser", "query"]),
                  let browser = dictionary["browser"] as? String,
                  (browser == "default" || isValidApplicationName(browser)),
                  let query = dictionary["query"] as? String,
                  isValidActionQuery(query, maximumLength: 300) else { return nil }
            return .browserSearch(browser: browser, query: query)
        case "browser_open_url":
            guard hasExactKeys(dictionary, ["type", "browser", "url"]),
                  let browser = dictionary["browser"] as? String,
                  (browser == "default" || isValidApplicationName(browser)),
                  let rawURL = dictionary["url"] as? String,
                  let url = isValidPublicWebURL(rawURL) else { return nil }
            return .browserOpenURL(browser: browser, url: url)
        case "maps_search":
            guard hasExactKeys(dictionary, ["type", "query"]),
                  let query = dictionary["query"] as? String,
                  isValidActionQuery(query, maximumLength: 300) else { return nil }
            return .mapsSearch(query: query)
        case "spotify_search":
            guard hasExactKeys(dictionary, ["type", "query"]),
                  let query = dictionary["query"] as? String,
                  isValidActionQuery(query, maximumLength: 160) else { return nil }
            return .spotifySearch(query: query)
        case "media_control":
            guard hasExactKeys(dictionary, ["type", "player", "action"]),
                  let player = dictionary["player"] as? String,
                  let action = dictionary["action"] as? String else { return nil }
            if player == "active" {
                guard action == "pause" else { return nil }
            } else {
                guard mediaScripts[player]?[action] != nil else { return nil }
            }
            return .mediaControl(player: player, action: action)
        case "play_music":
            guard hasExactKeys(dictionary, ["type", "player", "query"]),
                  dictionary["player"] as? String == "music",
                  let query = dictionary["query"] as? String,
                  isValidActionQuery(query, maximumLength: 160) else { return nil }
            return .playMusic(query: query)
        case "volume_control":
            guard hasExactKeys(dictionary, ["type", "action"]),
                  let action = dictionary["action"] as? String,
                  volumeScripts[action] != nil else { return nil }
            return .volumeControl(action: action)
        case "gui_interaction":
            guard hasExactKeys(dictionary, ["type", "steps"]),
                  let steps = parseGUIInteractionSteps(dictionary["steps"]) else { return nil }
            return .guiInteraction(steps: steps)
        default:
            return nil
        }
    }

    private func performNativeAction(requestID: String, action: NativeAction) {
        guard nativeActionInFlight == nil else {
            rejectNativeActionRequest(
                requestID: requestID,
                error: "Another desktop action is still in progress."
            )
            return
        }
        nativeActionInFlight = requestID
        let timeoutWorkItem = DispatchWorkItem { [weak self] in
            guard let self,
                  self.nativeActionInFlight == requestID else { return }
            if let process = self.nativeActionProcess, process.isRunning {
                process.terminate()
                DispatchQueue.global(qos: .utility).asyncAfter(deadline: .now() + 2) {
                    if process.isRunning {
                        Darwin.kill(process.processIdentifier, SIGKILL)
                    }
                }
            }
            self.finishNativeAction(
                requestID: requestID,
                error: "The desktop action timed out before it completed."
            )
        }
        nativeActionTimeoutWorkItem = timeoutWorkItem
        DispatchQueue.main.asyncAfter(
            deadline: .now() + nativeActionTimeout,
            execute: timeoutWorkItem
        )
        nativeTrace("native_action.started")
        switch action {
        case .openApp(let alias):
            openOrFocusApplication(alias: alias) { [weak self] status, detail, error in
                self?.finishNativeAction(
                    requestID: requestID,
                    status: status,
                    detail: detail,
                    error: error
                )
            }
        case .closeApp(let alias):
            closeApplication(alias: alias) { [weak self] status, detail, error in
                self?.finishNativeAction(
                    requestID: requestID,
                    status: status,
                    detail: detail,
                    error: error
                )
            }
        case .browserSearch(let browser, let query):
            // Open the visible Google results page that the user requested.
            // Host-side public-result reading remains separately bounded and
            // never relies on browser-session data.
            guard var components = URLComponents(string: "https://www.google.com/search") else {
                finishNativeAction(requestID: requestID, error: "The browser search URL could not be created.")
                return
            }
            components.queryItems = [URLQueryItem(name: "q", value: query)]
            guard let url = components.url else {
                finishNativeAction(requestID: requestID, error: "The browser search URL could not be created.")
                return
            }
            if browser == "default" {
                let opened = NSWorkspace.shared.open(url)
                finishNativeAction(
                    requestID: requestID,
                    status: opened ? "opened" : nil,
                    detail: opened ? "Search opened in the default browser." : nil,
                    error: opened ? nil : "The default browser could not open the search."
                )
            } else {
                openURL(url, inApplication: browser) { [weak self] status, detail, error in
                    self?.finishNativeAction(
                        requestID: requestID,
                        status: status,
                        detail: detail,
                        error: error
                    )
                }
            }
        case .browserOpenURL(let browser, let url):
            if browser == "default" {
                let opened = NSWorkspace.shared.open(url)
                finishNativeAction(
                    requestID: requestID,
                    status: opened ? "opened" : nil,
                    detail: opened ? "Public result opened in the default browser." : nil,
                    error: opened ? nil : "The default browser could not open the public result."
                )
            } else {
                openURL(url, inApplication: browser) { [weak self] status, detail, error in
                    self?.finishNativeAction(
                        requestID: requestID,
                        status: status,
                        detail: detail,
                        error: error
                    )
                }
            }
        case .mapsSearch(let query):
            var components = URLComponents()
            components.scheme = "maps"
            components.host = ""
            components.queryItems = [URLQueryItem(name: "q", value: query)]
            guard let url = components.url else {
                finishNativeAction(requestID: requestID, error: "The Maps search URL could not be created.")
                return
            }
            openURL(url, inApplication: "maps") { [weak self] status, detail, error in
                self?.finishNativeAction(
                    requestID: requestID,
                    status: status,
                    detail: detail,
                    error: error
                )
            }
        case .spotifySearch(let query):
            var allowed = CharacterSet.urlPathAllowed
            allowed.remove(charactersIn: "/?#:%")
            guard let encoded = query.addingPercentEncoding(withAllowedCharacters: allowed),
                  let url = URL(string: "https://open.spotify.com/search/\(encoded)") else {
                finishNativeAction(requestID: requestID, error: "The Spotify search URL could not be created.")
                return
            }
            openURL(url, inApplication: "spotify") { [weak self] status, detail, error in
                self?.finishNativeAction(
                    requestID: requestID,
                    status: status,
                    detail: detail,
                    error: error
                )
            }
        case .mediaControl(let player, let action):
            let script = player == "active" && action == "pause"
                ? pauseActiveMediaScript
                : mediaScripts[player]?[action]
            guard let script else {
                finishNativeAction(requestID: requestID, error: "The media operation is unsupported by this adapter.")
                return
            }
            // On a cold start Spotify may not yet accept an Apple event. Open
            // or focus it through macOS first, then run the fixed action.
            if player == "spotify" {
                openOrFocusApplication(alias: "spotify") { [weak self] _, _, launchError in
                    guard let self else { return }
                    guard launchError == nil else {
                        self.finishNativeAction(requestID: requestID, error: launchError)
                        return
                    }
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.75) { [weak self] in
                        self?.runFixedAppleScript(script, arguments: []) { [weak self] error in
                            self?.finishNativeAction(
                                requestID: requestID,
                                status: error == nil ? "completed" : nil,
                                detail: error == nil ? "Spotify playback control completed." : nil,
                                error: error
                            )
                        }
                    }
                }
                return
            }
            runFixedAppleScript(script, arguments: []) { [weak self] error in
                self?.finishNativeAction(
                    requestID: requestID,
                    status: error == nil ? "completed" : nil,
                    detail: error == nil ? "Media control completed." : nil,
                    error: error
                )
            }
        case .playMusic(let query):
            runFixedAppleScript(playMusicByNameScript, arguments: [query]) { [weak self] error in
                self?.finishNativeAction(
                    requestID: requestID,
                    status: error == nil ? "completed" : nil,
                    detail: error == nil ? "Music playback started." : nil,
                    error: error
                )
            }
        case .volumeControl(let action):
            guard let script = volumeScripts[action] else {
                finishNativeAction(requestID: requestID, error: "The volume operation is unsupported by this adapter.")
                return
            }
            runFixedAppleScript(script, arguments: []) { [weak self] error in
                self?.finishNativeAction(
                    requestID: requestID,
                    status: error == nil ? "completed" : nil,
                    detail: error == nil ? "System volume adjusted." : nil,
                    error: error
                )
            }
        case .guiInteraction(let steps):
            performGUIInteraction(steps) { [weak self] error in
                self?.finishNativeAction(
                    requestID: requestID,
                    status: error == nil ? "completed" : nil,
                    detail: error == nil ? "Visible interface interaction completed." : nil,
                    error: error
                )
            }
        }
    }

    private func frontmostExternalWindowBounds() -> CGRect? {
        let ownPID = ProcessInfo.processInfo.processIdentifier
        let liveFrontmostPID = NSWorkspace.shared.frontmostApplication?.processIdentifier
        let targetPID = liveFrontmostPID != nil && liveFrontmostPID != ownPID
            ? liveFrontmostPID
            : lastExternalFrontmostPID
        guard let targetPID,
              let windowInfo = CGWindowListCopyWindowInfo(
                [.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID
              ) as? [[String: Any]] else { return nil }
        for entry in windowInfo {
            guard let owner = entry[kCGWindowOwnerPID as String] as? NSNumber,
                  owner.int32Value == targetPID,
                  let layer = entry[kCGWindowLayer as String] as? NSNumber,
                  layer.intValue == 0,
                  let bounds = entry[kCGWindowBounds as String] as? [String: Any],
                  let x = bounds["X"] as? NSNumber,
                  let y = bounds["Y"] as? NSNumber,
                  let width = bounds["Width"] as? NSNumber,
                  let height = bounds["Height"] as? NSNumber,
                  width.doubleValue >= 120, height.doubleValue >= 80 else { continue }
            return CGRect(x: x.doubleValue, y: y.doubleValue,
                          width: width.doubleValue, height: height.doubleValue)
        }
        return nil
    }

    private func accessibilityIsTrusted() -> Bool {
        let prompt = [kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: true] as CFDictionary
        return AXIsProcessTrustedWithOptions(prompt)
    }

    private func performGUIInteraction(
        _ steps: [GUIInteractionStep],
        completion: @escaping (String?) -> Void
    ) {
        guard accessibilityIsTrusted() else {
            completion("Allow MERRICK in System Settings → Privacy & Security → Accessibility, then try again.")
            return
        }
        guard let bounds = frontmostExternalWindowBounds() else {
            completion("No external frontmost window is available for the visible interface operation.")
            return
        }
        DispatchQueue.global(qos: .userInitiated).async {
            for step in steps {
                switch step {
                case .click(let x, let y):
                    let point = CGPoint(
                        x: bounds.minX + bounds.width * CGFloat(x) / 1_000,
                        y: bounds.minY + bounds.height * CGFloat(y) / 1_000
                    )
                    CGEvent(mouseEventSource: nil, mouseType: .leftMouseDown,
                            mouseCursorPosition: point, mouseButton: .left)?.post(tap: .cghidEventTap)
                    CGEvent(mouseEventSource: nil, mouseType: .leftMouseUp,
                            mouseCursorPosition: point, mouseButton: .left)?.post(tap: .cghidEventTap)
                case .scroll(let dy):
                    CGEvent(scrollWheelEvent2Source: nil, units: .line,
                            wheelCount: 1, wheel1: Int32(dy), wheel2: 0, wheel3: 0)?.post(tap: .cghidEventTap)
                case .key(let key):
                    let keyCodes: [String: CGKeyCode] = [
                        "enter": 36, "tab": 48, "escape": 53, "space": 49,
                        "up": 126, "down": 125, "left": 123, "right": 124,
                        "pageup": 116, "pagedown": 121, "home": 115, "end": 119,
                    ]
                    guard let keyCode = keyCodes[key] else {
                        DispatchQueue.main.async { completion("The GUI key was invalid.") }
                        return
                    }
                    CGEvent(keyboardEventSource: nil, virtualKey: keyCode, keyDown: true)?.post(tap: .cghidEventTap)
                    CGEvent(keyboardEventSource: nil, virtualKey: keyCode, keyDown: false)?.post(tap: .cghidEventTap)
                case .type(let text):
                    let utf16 = Array(text.utf16)
                    let down = CGEvent(keyboardEventSource: nil, virtualKey: 0, keyDown: true)
                    down?.keyboardSetUnicodeString(stringLength: utf16.count, unicodeString: utf16)
                    down?.post(tap: .cghidEventTap)
                    let up = CGEvent(keyboardEventSource: nil, virtualKey: 0, keyDown: false)
                    up?.keyboardSetUnicodeString(stringLength: utf16.count, unicodeString: utf16)
                    up?.post(tap: .cghidEventTap)
                }
                Thread.sleep(forTimeInterval: 0.14)
            }
            DispatchQueue.main.async { completion(nil) }
        }
    }

    private func openOrFocusApplication(
        alias: String,
        completion: @escaping (String?, String?, String?) -> Void
    ) {
        guard let applicationURL = installedApplicationURL(named: alias) else {
            completion(nil, nil, "That application is not installed or its name was not recognised.")
            return
        }
        let bundleID = Bundle(url: applicationURL)?.bundleIdentifier
        if let bundleID,
           let running = NSRunningApplication.runningApplications(
               withBundleIdentifier: bundleID
           ).first(where: { !$0.isTerminated }) {
            focusRunningApplication(running, successStatus: "focused", completion: completion)
            return
        }
        let configuration = NSWorkspace.OpenConfiguration()
        configuration.activates = true
        configuration.addsToRecentItems = false
        configuration.createsNewApplicationInstance = false
        NSWorkspace.shared.openApplication(
            at: applicationURL,
            configuration: configuration
        ) { application, error in
            if let error {
                completion(nil, nil, "The application could not be opened: \(error.localizedDescription)")
            } else if let application {
                // NSWorkspace reports a successful launch before macOS has
                // necessarily made the new app frontmost. Verify that final
                // state just as we do for an app that was already running.
                self.focusRunningApplication(
                    application,
                    successStatus: "opened",
                    // Spotify and other Electron applications can report a
                    // successful launch well before their first window is
                    // ready. Wait for a real foreground state on cold start.
                    maximumFocusAttempts: 80,
                    completion: completion
                )
            } else {
                completion(nil, nil, "The application could not be opened.")
            }
        }
    }

    private func closeApplication(
        alias: String,
        completion: @escaping (String?, String?, String?) -> Void
    ) {
        let requestedName = applicationNameAliases[normalizedApplicationName(alias)]
            ?? normalizedApplicationName(alias)
        let applications = NSWorkspace.shared.runningApplications.filter { application in
            guard !application.isTerminated,
                  let name = application.localizedName else { return false }
            let normalizedName = normalizedApplicationName(name)
            let knownName = applicationNameAliases[normalizedName] ?? normalizedName
            return knownName == requestedName
        }
        guard !applications.isEmpty else {
            completion("completed", "Application was already closed.", nil)
            return
        }
        guard applications.allSatisfy({ $0.terminate() }) else {
            completion(nil, nil, "macOS did not accept the normal quit request.")
            return
        }
        confirmApplicationTermination(applications, completion: completion)
    }

    private func confirmApplicationTermination(
        _ applications: [NSRunningApplication],
        attempt: Int = 0,
        completion: @escaping (String?, String?, String?) -> Void
    ) {
        if applications.allSatisfy(\.isTerminated) {
            completion("completed", "Application closed normally.", nil)
            return
        }
        guard attempt < 15 else {
            completion(nil, nil, "The application did not close. It may be waiting for a macOS confirmation.")
            return
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.12) { [weak self] in
            self?.confirmApplicationTermination(
                applications,
                attempt: attempt + 1,
                completion: completion
            )
        }
    }

    /// `activate` only means the request was accepted. Do not report success
    /// until macOS confirms the requested application is actually frontmost.
    private func focusRunningApplication(
        _ application: NSRunningApplication,
        successStatus: String,
        maximumFocusAttempts: Int = 12,
        completion: @escaping (String?, String?, String?) -> Void
    ) {
        guard !application.isTerminated else {
            completion(nil, nil, "The application closed before it could be brought to the front.")
            return
        }
        if isFrontmost(application) {
            completion(successStatus, "Application is in front.", nil)
            return
        }
        guard application.activate(options: [.activateAllWindows]) else {
            completion(nil, nil, "macOS rejected the request to bring the application to the front.")
            return
        }
        confirmApplicationFocus(
            application,
            successStatus: successStatus,
            maximumAttempts: maximumFocusAttempts,
            completion: completion
        )
    }

    private func isFrontmost(_ application: NSRunningApplication) -> Bool {
        NSWorkspace.shared.frontmostApplication?.processIdentifier == application.processIdentifier
    }

    private func confirmApplicationFocus(
        _ application: NSRunningApplication,
        successStatus: String,
        attempt: Int = 0,
        maximumAttempts: Int = 12,
        completion: @escaping (String?, String?, String?) -> Void
    ) {
        if isFrontmost(application) {
            completion(successStatus, "Application is in front.", nil)
            return
        }
        guard !application.isTerminated else {
            completion(nil, nil, "The application closed before it could be brought to the front.")
            return
        }
        guard attempt < maximumAttempts else {
            completion(nil, nil, "macOS accepted the activation request, but the application did not come to the front.")
            return
        }

        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) { [weak self] in
            self?.confirmApplicationFocus(
                application,
                successStatus: successStatus,
                attempt: attempt + 1,
                maximumAttempts: maximumAttempts,
                completion: completion
            )
        }
    }

    private func openURL(
        _ url: URL,
        inApplication alias: String,
        completion: @escaping (String?, String?, String?) -> Void
    ) {
        guard let applicationURL = installedApplicationURL(named: alias) else {
            completion(nil, nil, "That application is not installed.")
            return
        }
        let bundleID = Bundle(url: applicationURL)?.bundleIdentifier
        let wasRunning = NSWorkspace.shared.runningApplications.contains { application in
            guard !application.isTerminated else { return false }
            if let bundleID { return application.bundleIdentifier == bundleID }
            return application.bundleURL?.standardizedFileURL == applicationURL.standardizedFileURL
        }
        let configuration = NSWorkspace.OpenConfiguration()
        configuration.activates = true
        configuration.addsToRecentItems = false
        configuration.createsNewApplicationInstance = false
        NSWorkspace.shared.open(
            [url],
            withApplicationAt: applicationURL,
            configuration: configuration
        ) { application, error in
            if let error {
                completion(nil, nil, "The requested search could not be opened: \(error.localizedDescription)")
            } else if application != nil {
                completion(
                    wasRunning ? "focused" : "opened",
                    wasRunning ? "Search opened in the running application." : "Application opened with the search.",
                    nil
                )
            } else {
                completion(nil, nil, "The requested search could not be opened.")
            }
        }
    }

    private func runFixedAppleScript(
        _ script: String,
        arguments: [String],
        completion: @escaping (String?) -> Void
    ) {
        let process = Process()
        let errorPipe = Pipe()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/osascript")
        process.arguments = ["-e", script] + arguments
        process.standardInput = FileHandle.nullDevice
        process.standardOutput = FileHandle.nullDevice
        process.standardError = errorPipe
        nativeActionProcess = process
        process.terminationHandler = { process in
            let data = errorPipe.fileHandleForReading.readDataToEndOfFile()
            let rawError = String(data: data, encoding: .utf8) ?? ""
            DispatchQueue.main.async {
                if process.terminationStatus == 0 {
                    completion(nil)
                } else {
                    completion(rawError.isEmpty ? "The media action failed." : rawError)
                }
            }
        }
        do {
            try process.run()
        } catch {
            nativeActionProcess = nil
            completion("The media action could not start: \(error.localizedDescription)")
        }
    }

    private func cancelNativeAction(requestID: String) {
        guard nativeActionInFlight == requestID else { return }
        if let process = nativeActionProcess, process.isRunning {
            process.terminate()
            nativeActionKillWorkItem?.cancel()
            let killWorkItem = DispatchWorkItem { [weak self] in
                guard let self,
                      self.nativeActionInFlight == requestID,
                      process.isRunning else { return }
                Darwin.kill(process.processIdentifier, SIGKILL)
            }
            nativeActionKillWorkItem = killWorkItem
            DispatchQueue.main.asyncAfter(
                deadline: .now() + 2,
                execute: killWorkItem
            )
            nativeTrace("native_action.cancellation_requested")
            return
        }
        nativeActionTimeoutWorkItem?.cancel()
        nativeActionTimeoutWorkItem = nil
        nativeActionKillWorkItem?.cancel()
        nativeActionKillWorkItem = nil
        nativeActionProcess = nil
        nativeActionInFlight = nil
        nativeTrace("native_action.cancelled")
    }

    private func boundedNativeActionMessage(_ message: String) -> String {
        let printable = message.unicodeScalars.map { scalar -> Character in
            (scalar.value < 32 || scalar.value == 127) ? " " : Character(scalar)
        }
        let cleaned = String(printable).trimmingCharacters(in: .whitespacesAndNewlines)
        return String(cleaned.prefix(400))
    }

    private func finishNativeAction(
        requestID: String,
        status: String? = nil,
        detail: String? = nil,
        error: String? = nil
    ) {
        DispatchQueue.main.async { [weak self] in
            guard let self else { return }
            guard self.nativeActionInFlight == requestID else { return }
            self.nativeActionTimeoutWorkItem?.cancel()
            self.nativeActionTimeoutWorkItem = nil
            self.nativeActionKillWorkItem?.cancel()
            self.nativeActionKillWorkItem = nil
            self.nativeActionProcess = nil
            self.nativeActionInFlight = nil
            let ok = error == nil && status != nil
            let safeStatus = ok ? (status ?? "completed") : ""
            let safeDetail = ok ? self.boundedNativeActionMessage(detail ?? "Action completed.") : ""
            let boundedError = self.boundedNativeActionMessage(error ?? "The desktop action failed.")
            let safeError = ok ? "" : (boundedError.isEmpty ? "The desktop action failed." : boundedError)
            let okLiteral = ok ? "true" : "false"
            self.nativeTrace(ok ? "native_action.completed" : "native_action.failed")
            self.js(
                "window.merrickNativeActionResult(" +
                "\(self.jsString(requestID))," +
                "\(okLiteral)," +
                "{status:\(self.jsString(safeStatus)),detail:\(self.jsString(safeDetail))}," +
                "\(self.jsString(safeError)))"
            )
        }
    }

    private func rejectNativeActionRequest(requestID: String, error: String) {
        let safeError = boundedNativeActionMessage(error)
        let finalError = safeError.isEmpty ? "The desktop action was rejected." : safeError
        nativeTrace("native_action.rejected")
        js(
            "window.merrickNativeActionResult(" +
            "\(jsString(requestID)),false," +
            "{status:'',detail:''}," +
            "\(jsString(finalError)))"
        )
    }

    private func frontmostWindowID(for processID: pid_t) -> CGWindowID? {
        guard let windowInfo = CGWindowListCopyWindowInfo(
            [.optionOnScreenOnly, .excludeDesktopElements],
            kCGNullWindowID
        ) as? [[String: Any]] else {
            return nil
        }
        for entry in windowInfo {
            guard let owner = entry[kCGWindowOwnerPID as String] as? NSNumber,
                  owner.int32Value == processID,
                  let layer = entry[kCGWindowLayer as String] as? NSNumber,
                  layer.intValue == 0,
                  let number = entry[kCGWindowNumber as String] as? NSNumber,
                  let bounds = entry[kCGWindowBounds as String] as? [String: Any],
                  let width = bounds["Width"] as? NSNumber,
                  let height = bounds["Height"] as? NSNumber,
                  width.doubleValue >= 120,
                  height.doubleValue >= 80 else {
                continue
            }
            return CGWindowID(number.uint32Value)
        }
        return nil
    }

    private func captureScreen(requestID: String) {
        guard screenCaptureInFlight == nil else {
            finishScreenCapture(
                requestID: requestID,
                error: "Another one-time screen view is already in progress."
            )
            return
        }
        screenCaptureInFlight = requestID
        nativeTrace("screen_capture.requested")

        // Screen Recording is separate from Accessibility. This request grants
        // pixels only; MERRICK never requests mouse or keyboard control.
        guard CGPreflightScreenCaptureAccess() || CGRequestScreenCaptureAccess() else {
            finishScreenCapture(
                requestID: requestID,
                error: "Screen Recording permission was not granted. Allow MERRICK in System Settings → Privacy & Security → Screen & System Audio Recording, then reopen the app and ask again."
            )
            return
        }

        guard #available(macOS 14.0, *) else {
            finishScreenCapture(
                requestID: requestID,
                error: "One-time screen viewing requires macOS 14 or later."
            )
            return
        }

        let ownPID = ProcessInfo.processInfo.processIdentifier
        let liveFrontmostPID = NSWorkspace.shared.frontmostApplication?.processIdentifier
        let targetPID = liveFrontmostPID != nil && liveFrontmostPID != ownPID
            ? liveFrontmostPID
            : lastExternalFrontmostPID
        guard let targetPID else {
            finishScreenCapture(
                requestID: requestID,
                error: "No external frontmost window is available for the one-time view."
            )
            return
        }
        guard let targetWindowID = frontmostWindowID(for: targetPID) else {
            finishScreenCapture(
                requestID: requestID,
                error: "The frontmost application has no readable on-screen window."
            )
            return
        }

        SCShareableContent.getExcludingDesktopWindows(
            true,
            onScreenWindowsOnly: true
        ) { [weak self] content, error in
            guard let self else { return }
            if let error {
                self.finishScreenCapture(
                    requestID: requestID,
                    error: "Screen content is unavailable: \(error.localizedDescription)"
                )
                return
            }
            guard let content else {
                self.finishScreenCapture(
                    requestID: requestID,
                    error: "No shareable content is available for the one-time window view."
                )
                return
            }

            guard let targetWindow = content.windows.first(where: { candidate in
                candidate.windowID == targetWindowID &&
                    candidate.owningApplication?.processID == targetPID &&
                    candidate.owningApplication?.processID != ownPID &&
                    candidate.windowLayer == 0 &&
                    candidate.frame.width >= 120 &&
                    candidate.frame.height >= 80
            }) else {
                self.finishScreenCapture(
                    requestID: requestID,
                    error: "The selected frontmost window is no longer available."
                )
                return
            }

            let filter = SCContentFilter(desktopIndependentWindow: targetWindow)
            let longestSide = max(targetWindow.frame.width, targetWindow.frame.height)
            let scale = min(1.0, Double(self.maximumScreenCaptureDimension) /
                Double(max(longestSide, 1.0)))
            let configuration = SCStreamConfiguration()
            configuration.width = max(1, Int((Double(targetWindow.frame.width) * scale).rounded()))
            configuration.height = max(1, Int((Double(targetWindow.frame.height) * scale).rounded()))
            configuration.showsCursor = false
            configuration.capturesAudio = false

            SCScreenshotManager.captureImage(
                contentFilter: filter,
                configuration: configuration
            ) { [weak self] image, error in
                guard let self else { return }
                if let error {
                    self.finishScreenCapture(
                        requestID: requestID,
                        error: "The one-time screen view failed: \(error.localizedDescription)"
                    )
                    return
                }
                guard let image,
                      let jpeg = self.jpegDataWithinLimit(from: image) else {
                    self.finishScreenCapture(
                        requestID: requestID,
                        error: "The screen image could not be compressed within the private 4 MB limit."
                    )
                    return
                }
                self.finishScreenCapture(requestID: requestID, data: jpeg)
            }
        }
    }

    private func jpegDataWithinLimit(from image: CGImage) -> Data? {
        let representation = NSBitmapImageRep(cgImage: image)
        for quality in [0.72, 0.58, 0.44, 0.32] {
            guard let data = representation.representation(
                using: .jpeg,
                properties: [.compressionFactor: quality]
            ) else { continue }
            if data.count <= maximumScreenCaptureBytes { return data }
        }
        return nil
    }

    private func finishScreenCapture(
        requestID: String,
        data: Data? = nil,
        error: String? = nil
    ) {
        DispatchQueue.main.async { [weak self] in
            guard let self else { return }
            if self.screenCaptureInFlight == requestID {
                self.screenCaptureInFlight = nil
            }
            let encoded = data?.base64EncodedString() ?? ""
            let mime = data == nil ? "" : "image/jpeg"
            let message = error ?? ""
            let failureReason: String
            let lowerMessage = message.lowercased()
            if lowerMessage.contains("permission") || lowerMessage.contains("not granted") {
                failureReason = "permission"
            } else if lowerMessage.contains("frontmost") || lowerMessage.contains("window") {
                failureReason = "window"
            } else if lowerMessage.contains("compress") {
                failureReason = "compression"
            } else {
                failureReason = "capture"
            }
            self.nativeTrace(
                data == nil
                    ? "screen_capture.failed reason=\(failureReason)"
                    : "screen_capture.completed bytes=\(data!.count)"
            )
            self.js(
                "window.merrickNativeScreenCaptureResult(" +
                "\(self.jsString(requestID))," +
                "\(self.jsString(encoded))," +
                "\(self.jsString(mime))," +
                "\(self.jsString(message)))"
            )
        }
    }

    // MARK: - local playback-reference isolation

    private func updatePlaybackIsolation() {
        let shouldRun = systemAudioFilterActivated || assistantAudioPlaying || playbackReferenceRequested
        if shouldRun {
            startPlaybackIsolationIfPossible()
        } else {
            stopPlaybackIsolation()
        }
    }

    private func activateSystemAudioFilterIfNeeded() {
        guard systemAudioFilterAllowed, !systemAudioFilterActivated else { return }
        systemAudioFilterActivated = true
        nativeTrace("audio_isolation.system_filter_activated")
        updatePlaybackIsolation()
    }

    private func startPlaybackIsolationIfPossible() {
        guard #available(macOS 13.0, *) else {
            nativeTrace("audio_isolation.unavailable reason=macos_version")
            return
        }
        guard playbackReferenceStream == nil, !playbackReferenceStarting else { return }
        guard CGPreflightScreenCaptureAccess() else {
            // Prompt once and remain explicitly fail-open.  The normal
            // microphone recognizer continues immediately if permission is
            // declined, so this enhancement can never mute the assistant.
            if !screenAudioPermissionPrompted {
                screenAudioPermissionPrompted = true
                let granted = CGRequestScreenCaptureAccess()
                nativeTrace("audio_isolation.permission_requested")
                if granted {
                    DispatchQueue.main.async { [weak self] in
                        self?.startPlaybackIsolationIfPossible()
                    }
                }
            }
            nativeTrace("audio_isolation.raw_fallback reason=screen_audio_permission")
            return
        }
        playbackReferenceStarting = true
        let python = projectRoot.appendingPathComponent(".venv/bin/python")
        let worker = projectRoot.appendingPathComponent("server/audio_isolation_worker.py")
        audioIsolation.start(
            python: python,
            script: worker,
            result: { [weak self] result in
                DispatchQueue.main.async { self?.appendIsolatedSpeechFrame(result) }
            },
            failure: { [weak self] reason in
                DispatchQueue.main.async { self?.disablePlaybackIsolation(reason: reason) }
            }
        )
        SCShareableContent.getExcludingDesktopWindows(true, onScreenWindowsOnly: true) { [weak self] content, error in
            DispatchQueue.main.async {
                guard let self else { return }
                self.playbackReferenceStarting = false
                guard let content, error == nil, let display = content.displays.first else {
                    self.disablePlaybackIsolation(reason: "screen_audio_source_unavailable")
                    return
                }
                let filter = SCContentFilter(display: display, excludingApplications: [], exceptingWindows: [])
                let config = SCStreamConfiguration()
                config.capturesAudio = true
                // MERRICK's own WebKit/Edge TTS output is precisely the echo
                // reference AEC needs, so do not exclude this process.
                config.excludesCurrentProcessAudio = false
                config.sampleRate = 48_000
                config.channelCount = 1
                config.queueDepth = 3
                let stream = SCStream(filter: filter, configuration: config, delegate: self)
                do {
                    try stream.addStreamOutput(self, type: .audio, sampleHandlerQueue: self.playbackReferenceQueue)
                    self.playbackReferenceStream = stream
                    Task {
                        do {
                            try await stream.startCapture()
                            await MainActor.run {
                                self.audioIsolationEnabled = true
                                self.audioIsolationReadyForBarge = false
                                self.audioIsolationSession += 1
                                self.audioIsolationResultCount = 0
                                self.audioIsolationSuppressedFrameCount = 0
                                self.audioIsolationRestoredFrameCount = 0
                                self.audioIsolationFallbackTracedSession = -1
                                self.audioIsolationNearSubmittedSession = -1
                                self.cleanBargeCandidateFrames = 0
                                self.cleanVoiceQuietFrames = 0
                                self.cleanVoiceActivityActive = false
                                self.nativeTrace("audio_isolation.enabled local=true")
                            }
                        } catch {
                            await MainActor.run { self.disablePlaybackIsolation(reason: "screen_audio_start_failed") }
                        }
                    }
                } catch {
                    self.disablePlaybackIsolation(reason: "screen_audio_output_failed")
                }
            }
        }
    }

    private func stopPlaybackIsolation() {
        if cleanVoiceActivityActive {
            js("window.merrickNativeVoiceActivity(false)")
        }
        audioIsolationEnabled = false
        audioIsolationReadyForBarge = false
        cleanBargeCandidateFrames = 0
        cleanVoiceQuietFrames = 0
        cleanVoiceActivityActive = false
        resetSystemPlaybackActivity()
        audioIsolationSession += 1
        if let stream = playbackReferenceStream {
            playbackReferenceStream = nil
            Task { try? await stream.stopCapture() }
        }
        // Keep the worker warm between short TTS segments.  This avoids a
        // process launch in the middle of a barge-in and it receives no audio
        // while the reference stream is stopped.
        nativeTrace("audio_isolation.paused")
    }

    private func disablePlaybackIsolation(reason: String) {
        if cleanVoiceActivityActive {
            js("window.merrickNativeVoiceActivity(false)")
        }
        audioIsolationEnabled = false
        audioIsolationReadyForBarge = false
        cleanBargeCandidateFrames = 0
        cleanVoiceQuietFrames = 0
        cleanVoiceActivityActive = false
        resetSystemPlaybackActivity()
        audioIsolationSession += 1
        if let stream = playbackReferenceStream {
            playbackReferenceStream = nil
            Task { try? await stream.stopCapture() }
        }
        nativeTrace("audio_isolation.raw_fallback reason=\(reason)")
        if audioEngine.isRunning {
            js("window.merrickNativeSpeechState(true, 280, \(inputVoiceProcessingEnabled()))")
        }
    }

    func stream(_ stream: SCStream, didOutputSampleBuffer sampleBuffer: CMSampleBuffer, of type: SCStreamOutputType) {
        guard type == .audio, audioIsolationEnabled, let samples = pcm16Samples(from: sampleBuffer) else { return }
        _ = audioIsolation.submit(kind: "far", samples: samples, generation: recognitionGeneration, session: audioIsolationSession)
    }

    func stream(_ stream: SCStream, didStopWithError error: Error) {
        DispatchQueue.main.async { [weak self] in self?.disablePlaybackIsolation(reason: "screen_audio_stopped") }
    }

    private func pcm16Samples(from sampleBuffer: CMSampleBuffer) -> [Int16]? {
        guard let description = CMSampleBufferGetFormatDescription(sampleBuffer) else { return nil }
        let format = AVAudioFormat(cmAudioFormatDescription: description)
        guard abs(format.sampleRate - 48_000) < 100,
              let pcm = AVAudioPCMBuffer(
                pcmFormat: format,
                frameCapacity: AVAudioFrameCount(CMSampleBufferGetNumSamples(sampleBuffer))
              ) else { return nil }
        pcm.frameLength = pcm.frameCapacity
        let status = CMSampleBufferCopyPCMDataIntoAudioBufferList(
            sampleBuffer,
            at: 0,
            frameCount: Int32(pcm.frameLength),
            into: pcm.mutableAudioBufferList
        )
        guard status == noErr, let channel = pcm.floatChannelData?[0] else { return nil }
        return (0..<Int(pcm.frameLength)).map { index in
            Int16(max(-1, min(1, channel[index])) * Float(Int16.max))
        }
    }

    private func appendIsolatedSpeechFrame(_ result: AudioIsolationWorker.Result) {
        guard audioIsolationEnabled,
              result.generation == recognitionGeneration,
              result.session == audioIsolationSession,
              let request,
              !result.samples.isEmpty else { return }
        updateSystemPlaybackActivity(farRMS: result.farRMS)
        audioIsolationResultCount += 1
        if result.playbackSuppressed {
            audioIsolationSuppressedFrameCount += 1
        }
        if result.doubleTalkRestored {
            audioIsolationRestoredFrameCount += 1
        }
        if !audioIsolationReadyForBarge {
            audioIsolationReadyForBarge = true
            nativeTrace(String(
                format: "audio_isolation.first_result far_rms=%.1f near_rms=%.1f clean_rms=%.1f",
                result.farRMS, result.nearRMS, result.cleanRMS
            ))
            js("window.merrickNativeSpeechState(true, 280, true)")
        }
        if audioIsolationResultCount.isMultiple(of: 100) {
            nativeTrace(String(
                format: "audio_isolation.frames=%d suppressed=%d restored=%d far_rms=%.1f near_rms=%.1f clean_rms=%.1f vad=%.2f gain=%.2f",
                audioIsolationResultCount,
                audioIsolationSuppressedFrameCount,
                audioIsolationRestoredFrameCount,
                result.farRMS,
                result.nearRMS,
                result.cleanRMS,
                result.speechProbability,
                result.doubleTalkGain
            ))
        }
        // Text overlap is a poor final arbiter when the recognizer is still
        // revising a sentence.  Use the signal after AEC instead: a real
        // nearby speaker leaves sustained voiced energy in the cleaned signal,
        // while MERRICK's own speaker output is normally attenuated by AEC.
        // Requiring eight consecutive ~21 ms buffers makes this a 160 ms
        // acoustic confirmation, not a single loud transient.
        let cleanRatio = result.cleanRMS / max(result.nearRMS, 1)
        // Real barge-in captured on this Mac reached clean_rms≈511 with a
        // 0.83 post-AEC ratio and VAD 1.00, while the simultaneous speaker
        // echo was clean_rms≈101 / ratio 0.08. The former fixed 900 threshold
        // therefore rejected the user before Pipecat could see a turn edge.
        // Keep the stronger relative-energy, VAD, and eight-frame checks so a
        // loudspeaker echo still cannot become an interruption by itself.
        let isConfirmedCleanSpeech = assistantAudioPlaying &&
            result.farRMS >= 500 &&
            result.nearRMS >= 280 &&
            result.cleanRMS >= 300 &&
            cleanRatio >= 0.45 &&
            result.speechProbability >= 0.72
        cleanBargeCandidateFrames = isConfirmedCleanSpeech
            ? min(cleanBargeCandidateFrames + 1, 20)
            : max(cleanBargeCandidateFrames - 1, 0)
        if isConfirmedCleanSpeech {
            cleanVoiceQuietFrames = 0
        } else if cleanVoiceActivityActive {
            cleanVoiceQuietFrames = min(cleanVoiceQuietFrames + 1, 20)
        }
        if cleanBargeCandidateFrames >= 8, !cleanVoiceActivityActive {
            cleanVoiceActivityActive = true
            nativeTrace(String(
                format: "audio_isolation.clean_voice_started far_rms=%.1f near_rms=%.1f clean_rms=%.1f ratio=%.2f vad=%.2f",
                result.farRMS, result.nearRMS, result.cleanRMS, cleanRatio, result.speechProbability
            ))
            js("window.merrickNativeVoiceActivity(true)")
        } else if cleanVoiceActivityActive && cleanVoiceQuietFrames >= 12 {
            // About 250 ms of post-AEC quiet closes the external Pipecat turn
            // without affecting the still-running macOS recognizer.
            cleanVoiceActivityActive = false
            cleanVoiceQuietFrames = 0
            nativeTrace("audio_isolation.clean_voice_stopped")
            js("window.merrickNativeVoiceActivity(false)")
        }
        let format = AVAudioFormat(standardFormatWithSampleRate: 48_000, channels: 1)!
        guard let buffer = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: AVAudioFrameCount(result.samples.count)),
              let channel = buffer.floatChannelData?[0] else { return }
        buffer.frameLength = AVAudioFrameCount(result.samples.count)
        for (index, sample) in result.samples.enumerated() {
            channel[index] = Float(sample) / Float(Int16.max)
        }
        request.append(buffer)
        captureVoiceSamples(buffer)
    }

    private func updateSystemPlaybackActivity(farRMS: Double) {
        if farRMS >= 350 {
            systemPlaybackLoudFrames = min(systemPlaybackLoudFrames + 1, 20)
            systemPlaybackQuietFrames = 0
        } else if farRMS <= 120 {
            systemPlaybackQuietFrames = min(systemPlaybackQuietFrames + 1, 30)
            systemPlaybackLoudFrames = 0
        }
        if !systemPlaybackActive && systemPlaybackLoudFrames >= 2 {
            systemPlaybackActive = true
            nativeTrace("audio_isolation.system_playback active=true")
            js("window.merrickNativeSystemAudioActivity(true)")
        } else if systemPlaybackActive && systemPlaybackQuietFrames >= 12 {
            systemPlaybackActive = false
            nativeTrace("audio_isolation.system_playback active=false")
            js("window.merrickNativeSystemAudioActivity(false)")
        }
    }

    private func resetSystemPlaybackActivity() {
        systemPlaybackLoudFrames = 0
        systemPlaybackQuietFrames = 0
        guard systemPlaybackActive else { return }
        systemPlaybackActive = false
        js("window.merrickNativeSystemAudioActivity(false)")
    }

    private func submitMicrophoneFrame(_ buffer: AVAudioPCMBuffer, generation: Int, request: SFSpeechAudioBufferRecognitionRequest) {
        guard audioIsolationEnabled,
              abs(buffer.format.sampleRate - 48_000) < 100,
              let channel = buffer.floatChannelData?[0] else {
            if audioIsolationEnabled && !audioIsolationReadyForBarge &&
               audioIsolationFallbackTracedSession != audioIsolationSession {
                audioIsolationFallbackTracedSession = audioIsolationSession
                nativeTrace(String(
                    format: "audio_isolation.raw_fallback input_rate=%.0f", buffer.format.sampleRate
                ))
            }
            request.append(buffer)
            captureVoiceSamples(buffer)
            return
        }
        let samples = (0..<Int(buffer.frameLength)).map { index in
            Int16(max(-1, min(1, channel[index])) * Float(Int16.max))
        }
        if !audioIsolation.submit(
            kind: "near",
            samples: samples,
            generation: generation,
            session: audioIsolationSession,
            assistantAudioPlaying: assistantAudioPlaying
        ) {
            request.append(buffer)
            captureVoiceSamples(buffer)
        } else if audioIsolationNearSubmittedSession != audioIsolationSession {
            audioIsolationNearSubmittedSession = audioIsolationSession
            nativeTrace(String(
                format: "audio_isolation.near_submitted input_rate=%.0f frames=%d",
                buffer.format.sampleRate, buffer.frameLength
            ))
        }
    }

    private func startListening(useVoiceProcessing requestedVoiceProcessing: Bool = false) {
        guard !audioEngine.isRunning else {
            // The permission callback may have opened the engine before the web
            // view finished loading. Always resynchronise the JS state.
            let processingActive = inputVoiceProcessingEnabled()
            js("window.merrickNativeSpeechState(true, 280, \(processingActive || audioIsolationReadyForBarge))")
            nativeTrace("speech.resync already_running=true voice_processing=\(processingActive)")
            return
        }
        let speechStatus = SFSpeechRecognizer.authorizationStatus()
        guard speechStatus == .authorized else {
            if speechStatus == .notDetermined { requestPermissions() }
            else { js("window.merrickNativeError('请允许 MERRICK 使用语音识别')") }
            return
        }
        let micStatus = AVCaptureDevice.authorizationStatus(for: .audio)
        guard micStatus == .authorized else {
            if micStatus == .notDetermined { requestPermissions() }
            else { js("window.merrickNativeError('请允许 MERRICK 使用麦克风')") }
            return
        }
        activateSystemAudioFilterIfNeeded()
        restartingSpeech = false
        recognitionGeneration += 1
        let generation = recognitionGeneration
        let isManualVoiceprintCapture = manualVoiceprintCaptureRequested
        if isManualVoiceprintCapture {
            manualVoiceprintCaptureRequested = false
            manualVoiceprintCaptureGeneration = generation
            nativeTrace("voiceprint.capture_started generation=\(generation)")
        }
        task?.cancel()
        task = nil
        recognizer = SFSpeechRecognizer(locale: Locale(identifier: speechRecognizerLocaleIdentifier))
        // The frontend always requests raw input.  macOS Voice Processing I/O
        // is retained as a guarded helper for a future compatible device, but
        // is never enabled automatically because it suppressed speech on the
        // current microphone when Watch Mode was active.
        let wantsVoiceProcessing = requestedVoiceProcessing
        let processingActive = configureInputVoiceProcessing(enabled: wantsVoiceProcessing)
        nativeTrace("speech.start generation=\(generation) language=\(speechLanguage) voice_processing=\(processingActive) requested=\(wantsVoiceProcessing)")
        let req = SFSpeechAudioBufferRecognitionRequest()
        req.shouldReportPartialResults = true
        req.taskHint = .dictation
        // Bias recognition toward the current product name in both languages.
        // Keep the former wake word as an input alias for existing users.
        req.contextualStrings = speechLanguage == "zh"
            ? ["Merrick", "MERRICK", "梅里克", "Jarvis", "贾维斯"]
            : ["Merrick", "MERRICK", "Jarvis"]
        if #available(macOS 13.0, *) { req.addsPunctuation = true }
        request = req
        let input = audioEngine.inputNode
        voiceSampleLock.lock()
        voiceSamples.removeAll(keepingCapacity: true)
        voiceResampleCursor = 0
        voiceSampleEmissionCount = 0
        voiceSampleCaptureArmedGeneration = -1
        voiceTurnSentGeneration = -1
        watchVoiceVerificationGeneration = -1
        if assistantAudioPlaying { voiceSampleSuppressedGeneration = generation }
        voiceSampleLock.unlock()
        if inputTapInstalled {
            input.removeTap(onBus: 0)
            inputTapInstalled = false
        }
        // Let AVAudioEngine bind the tap to the node's current native format.
        // Supplying a cached explicit format can become invalid if macOS changes
        // the active input device between format lookup and tap installation.
        input.installTap(onBus: 0, bufferSize: 1024, format: nil) { [weak self] buffer, _ in
            guard let self else { return }
            self.submitMicrophoneFrame(buffer, generation: generation, request: req)
            self.audioFrameLock.lock()
            let isFirstFrame = self.audioFrameGenerations.insert(generation).inserted
            self.audioFrameLock.unlock()
            if isFirstFrame {
                DispatchQueue.main.async { [weak self] in
                    guard let self, self.recognitionGeneration == generation else { return }
                    self.nativeTrace("speech.first_audio_frame generation=\(generation)")
                    self.audioWatchdogRetries = 0
                    self.audioStartFailures = 0
                }
            }
            guard let channel = buffer.floatChannelData?[0] else { return }
            let now = CFAbsoluteTimeGetCurrent()
            guard now - self.lastLevelUpdate > 0.075 else { return }
            self.lastLevelUpdate = now
            let count = Int(buffer.frameLength)
            var sum: Float = 0
            for i in 0..<count { sum += channel[i] * channel[i] }
            let rms = sqrt(sum / Float(max(count, 1)))
            let level = min(1.0, max(0.0, (Double(rms) - 0.008) * 12.0))
            self.js(String(format: "window.merrickNativeAudioLevel(%.3f)", level))
        }
        inputTapInstalled = true
        audioEngine.prepare()
        do {
            try audioEngine.start()
            nativeTrace("speech.engine_started voice_processing=\(processingActive)")
        } catch {
            nativeTrace("speech.engine_start_failed error=\(error.localizedDescription)")
            if inputTapInstalled {
                input.removeTap(onBus: 0)
                inputTapInstalled = false
            }
            req.endAudio()
            request = nil
            recognitionGeneration += 1
            audioStartFailures += 1
            let retryDelay = min(2500, 500 + audioStartFailures * 250)
            if audioStartFailures >= 3 {
                let message = jsString("Microphone is reconnecting: \(error.localizedDescription)")
                js("window.merrickNativeError(\(message))")
            }
            js("window.merrickNativeSpeechState(false, \(retryDelay))")
            return
        }
        // engine.start() alone does not prove that the input tap is alive. If no
        // audio buffer arrives at all, rebuild once instead of leaving a false
        // LISTENING state on screen indefinitely.
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) { [weak self] in
            guard let self, self.recognitionGeneration == generation else { return }
            self.audioFrameLock.lock()
            let hasFrames = self.audioFrameGenerations.contains(generation)
            self.audioFrameLock.unlock()
            guard !hasFrames else { return }
            self.nativeTrace("speech.audio_watchdog generation=\(generation) no_frames=true")
            if self.audioWatchdogRetries < 1 {
                self.audioWatchdogRetries += 1
                self.stopListening(final: false)
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { [weak self] in
                    self?.startListening()
                }
            } else {
                self.js("window.merrickNativeError('Microphone input stalled. Please check the selected input device.')")
            }
        }
        js("window.merrickNativeSpeechState(true, 280, \(processingActive || audioIsolationReadyForBarge))")
        if isManualVoiceprintCapture {
            js("window.merrickNativeVoiceprintCaptureStarted()")
            scheduleManualVoiceprintCaptureCompletion(for: generation)
        }
        task = recognizer?.recognitionTask(with: req) { [weak self] result, error in
            guard let self else { return }
            guard generation == self.recognitionGeneration else { return }
            // A manual enrollment phrase is not a conversational command and
            // must not trigger the live voice-verification path either.
            if self.manualVoiceprintCaptureGeneration == generation { return }
            if let result {
                self.nativeTrace("speech.result generation=\(generation) final=\(result.isFinal) chars=\(result.bestTranscription.formattedString.count)")
                if !self.assistantAudioPlaying,
                   self.voiceTurnSentGeneration != generation {
                    self.voiceTurnSentGeneration = generation
                    self.js("window.merrickNativeVoiceTurn(\(generation))")
                }
                if !self.assistantAudioPlaying,
                   self.voiceSampleSuppressedGeneration != generation,
                   self.voiceSampleCaptureArmedGeneration != generation {
                    // Start the identity clip at actual speech detection, not
                    // from the microphone's previous idle window.
                    self.voiceSampleLock.lock()
                    self.voiceSamples.removeAll(keepingCapacity: true)
                    self.voiceResampleCursor = 0
                    self.voiceSampleEmissionCount = 0
                    self.voiceSampleCaptureArmedGeneration = generation
                    self.voiceSampleLock.unlock()
                    self.nativeTrace("voice.capture_armed generation=\(generation)")
                    self.scheduleVoiceSampleEmissions(for: generation)
                }
                let text = self.jsString(result.bestTranscription.formattedString)
                self.js("window.merrickNativeTranscriptDetected()")
                self.js("window.merrickNativeTranscript(\(text), \(result.isFinal))")
                if result.isFinal { self.stopListening(final: false) }
            } else if let error {
                let message = self.jsString("Speech recognition: \(error.localizedDescription)")
                self.js("window.merrickNativeError(\(message))")
                self.stopListening(final: false)
            }
        }
    }

    private func inputVoiceProcessingEnabled() -> Bool {
        guard #available(macOS 10.15, *) else { return false }
        return audioEngine.inputNode.isVoiceProcessingEnabled
    }

    /// Voice Processing I/O reduces device-output echo and steady background
    /// noise before Speech.framework sees the signal. Apple requires this API
    /// to be called while the engine is stopped, so callers must restart a
    /// recognition turn rather than attempt a live toggle.
    @discardableResult
    private func configureInputVoiceProcessing(enabled: Bool) -> Bool {
        guard #available(macOS 10.15, *) else {
            nativeTrace("speech.voice_processing unavailable requested=\(enabled)")
            return false
        }
        guard !audioEngine.isRunning else {
            let active = audioEngine.inputNode.isVoiceProcessingEnabled
            nativeTrace("speech.voice_processing deferred requested=\(enabled) active=\(active)")
            return active
        }
        let input = audioEngine.inputNode
        guard input.isVoiceProcessingEnabled != enabled else { return enabled }
        do {
            try input.setVoiceProcessingEnabled(enabled)
            let active = input.isVoiceProcessingEnabled
            nativeTrace("speech.voice_processing configured requested=\(enabled) active=\(active)")
            return active
        } catch {
            let active = input.isVoiceProcessingEnabled
            nativeTrace("speech.voice_processing failed requested=\(enabled) active=\(active) error=\(error.localizedDescription)")
            return active
        }
    }

    private func stopListening(final: Bool) {
        if !Thread.isMainThread {
            DispatchQueue.main.async { [weak self] in self?.stopListening(final: final) }
            return
        }
        guard audioEngine.isRunning || inputTapInstalled || request != nil || task != nil else {
            js("window.merrickNativeSpeechState(false)")
            return
        }
        recognitionGeneration += 1
        nativeTrace("speech.stop next_generation=\(recognitionGeneration)")
        if audioEngine.isRunning { audioEngine.stop() }
        if inputTapInstalled {
            audioEngine.inputNode.removeTap(onBus: 0)
            inputTapInstalled = false
        }
        request?.endAudio()
        request = nil
        task?.cancel()
        task = nil
        nativeTrace("speech.engine_stopped retained=true")
        js("window.merrickNativeAudioLevel(0)")
        js("window.merrickNativeSpeechState(false)")
    }

    private func resize(expanded: Bool) {
        guard windowFullscreenMode == .normal,
              !window.styleMask.contains(.fullScreen) else { return }
        let size = expanded ? NSSize(width: 980, height: 700) : NSSize(width: 500, height: 560)
        var frame = window.frame
        frame.origin.y += frame.height - size.height
        frame.size = size
        if let targetScreen = window.screen ?? NSScreen.main {
            frame.origin = fullyVisibleOrigin(frame.origin, size: size, on: targetScreen)
        }
        window.setFrame(frame, display: true, animate: true)
    }

    private func sendFullscreenState(reason: String, error: String? = nil) {
        var payload: [String: Any] = [
            "mode": windowFullscreenMode.rawValue,
            "requestId": pendingFullscreenRequestID ?? NSNull(),
            "reason": reason,
            "error": error ?? NSNull(),
        ]
        payload["updatedAt"] = ISO8601DateFormatter().string(from: Date())
        guard let data = try? JSONSerialization.data(withJSONObject: payload),
              let json = String(data: data, encoding: .utf8) else {
            nativeTrace("window.fullscreen_state_encoding_failed")
            return
        }
        js("window.merrickNativeFullscreenState && window.merrickNativeFullscreenState(\(json))")
    }

    private func restoreHUDWindowBehavior() {
        window.level = fullscreenRestoreLevel
        window.collectionBehavior = fullscreenRestoreCollectionBehavior
    }

    private func setWindowFullscreen(_ body: [String: Any]) {
        guard let requestedMode = body["mode"] as? String,
              ["enter", "exit", "toggle"].contains(requestedMode),
              let requestID = body["requestId"] as? String,
              requestID.count == 36,
              UUID(uuidString: requestID) != nil else {
            nativeTrace("window.fullscreen_rejected invalid_request")
            sendFullscreenState(reason: "failed", error: "The full-screen request was invalid.")
            return
        }
        guard windowFullscreenMode != .entering && windowFullscreenMode != .exiting else {
            nativeTrace("window.fullscreen_rejected transition_busy")
            sendFullscreenState(reason: "failed", error: "A full-screen transition is already in progress.")
            return
        }

        let isFullscreen = window.styleMask.contains(.fullScreen) || windowFullscreenMode == .fullscreen
        let shouldEnter = requestedMode == "enter" || (requestedMode == "toggle" && !isFullscreen)
        if (shouldEnter && isFullscreen) || (!shouldEnter && !isFullscreen) {
            pendingFullscreenRequestID = requestID
            windowFullscreenMode = isFullscreen ? .fullscreen : .normal
            sendFullscreenState(reason: "web")
            pendingFullscreenRequestID = nil
            return
        }

        pendingFullscreenRequestID = requestID
        if shouldEnter {
            fullscreenRestoreLevel = window.level
            fullscreenRestoreCollectionBehavior = window.collectionBehavior
            var fullscreenBehavior = window.collectionBehavior
            fullscreenBehavior.remove(.canJoinAllSpaces)
            fullscreenBehavior.remove(.fullScreenAuxiliary)
            fullscreenBehavior.remove(.fullScreenNone)
            fullscreenBehavior.insert(.fullScreenPrimary)
            window.collectionBehavior = fullscreenBehavior
            window.level = .normal
            windowFullscreenMode = .entering
        } else {
            windowFullscreenMode = .exiting
        }
        nativeTrace("window.fullscreen_requested mode=\(requestedMode)")
        sendFullscreenState(reason: "web")
        window.toggleFullScreen(nil)
    }

    private func fullyVisibleOrigin(_ origin: NSPoint, size: NSSize, on screen: NSScreen) -> NSPoint {
        let visibleFrame = screen.visibleFrame
        let maximumX = max(visibleFrame.minX, visibleFrame.maxX - size.width)
        let maximumY = max(visibleFrame.minY, visibleFrame.maxY - size.height)
        return NSPoint(
            x: min(maximumX, max(visibleFrame.minX, origin.x)),
            y: min(maximumY, max(visibleFrame.minY, origin.y))
        )
    }

    /// A persisted HUD position can belong to an external display that has
    /// since been disconnected, or simply to a display the user is no longer
    /// looking at.  A Dock/icon reopen is an explicit request to see MERRICK,
    /// so recover it on the primary display where macOS presents the Dock.
    private func bringHUDToPrimaryScreen() {
        let targetScreen = NSScreen.main ?? NSScreen.screens.first
        guard let targetScreen else {
            window.makeKeyAndOrderFront(nil)
            return
        }

        let center = NSPoint(x: window.frame.midX, y: window.frame.midY)
        if !NSMouseInRect(center, targetScreen.frame, false) {
            let visible = targetScreen.visibleFrame
            let centered = NSPoint(
                x: visible.midX - window.frame.width / 2,
                y: visible.midY - window.frame.height / 2
            )
            window.setFrameOrigin(constrainedOrigin(centered, on: targetScreen))
            saveWindowPosition()
            nativeTrace("app.window_relocated_to_primary_screen")
        }
        window.makeKeyAndOrderFront(nil)
    }

    private func constrainedOrigin(_ origin: NSPoint, on screen: NSScreen) -> NSPoint {
        let visibleFrame = screen.visibleFrame
        let minimumVisible: CGFloat = 80
        return NSPoint(
            x: min(visibleFrame.maxX - minimumVisible,
                   max(visibleFrame.minX - window.frame.width + minimumVisible, origin.x)),
            y: min(visibleFrame.maxY - minimumVisible,
                   max(visibleFrame.minY - window.frame.height + minimumVisible, origin.y))
        )
    }

    private func moveWindow(dx: Double, dy: Double) {
        guard windowFullscreenMode == .normal,
              !window.styleMask.contains(.fullScreen) else { return }
        guard dx.isFinite, dy.isFinite, abs(dx) < 500, abs(dy) < 500 else { return }
        let mouse = NSEvent.mouseLocation
        let targetScreen = NSScreen.screens.first {
            NSMouseInRect(mouse, $0.frame, false)
        } ?? window.screen ?? NSScreen.main
        guard let targetScreen else { return }
        let proposed = NSPoint(
            x: window.frame.origin.x + CGFloat(dx),
            y: window.frame.origin.y - CGFloat(dy)
        )
        window.setFrameOrigin(constrainedOrigin(proposed, on: targetScreen))
    }

    private func saveWindowPosition() {
        guard windowFullscreenMode == .normal,
              !window.styleMask.contains(.fullScreen) else { return }
        UserDefaults.standard.set(Double(window.frame.origin.x), forKey: windowPositionXKey)
        UserDefaults.standard.set(Double(window.frame.origin.y), forKey: windowPositionYKey)
    }

    private func restoreWindowPosition() {
        let defaults = UserDefaults.standard
        guard defaults.object(forKey: windowPositionXKey) != nil,
              defaults.object(forKey: windowPositionYKey) != nil else {
            window.center()
            return
        }
        let saved = NSPoint(
            x: defaults.double(forKey: windowPositionXKey),
            y: defaults.double(forKey: windowPositionYKey)
        )
        let savedFrame = NSRect(origin: saved, size: window.frame.size)
        let targetScreen = NSScreen.screens.max { lhs, rhs in
            lhs.visibleFrame.intersection(savedFrame).width * lhs.visibleFrame.intersection(savedFrame).height <
            rhs.visibleFrame.intersection(savedFrame).width * rhs.visibleFrame.intersection(savedFrame).height
        } ?? NSScreen.main
        guard let targetScreen else {
            window.center()
            return
        }
        window.setFrameOrigin(constrainedOrigin(saved, on: targetScreen))
    }

    func windowShouldClose(_ sender: NSWindow) -> Bool {
        nativeTrace("app.quit_requested source=window")
        NSApp.terminate(nil)
        return false
    }

    func windowWillEnterFullScreen(_ notification: Notification) {
        windowFullscreenMode = .entering
        nativeTrace("window.fullscreen_will_enter")
        sendFullscreenState(reason: pendingFullscreenRequestID == nil ? "native" : "web")
    }

    func windowDidEnterFullScreen(_ notification: Notification) {
        windowFullscreenMode = .fullscreen
        nativeTrace("window.fullscreen_did_enter")
        sendFullscreenState(reason: pendingFullscreenRequestID == nil ? "native" : "web")
        pendingFullscreenRequestID = nil
    }

    func windowWillExitFullScreen(_ notification: Notification) {
        windowFullscreenMode = .exiting
        nativeTrace("window.fullscreen_will_exit")
        sendFullscreenState(reason: pendingFullscreenRequestID == nil ? "native" : "web")
    }

    func windowDidExitFullScreen(_ notification: Notification) {
        restoreHUDWindowBehavior()
        windowFullscreenMode = .normal
        nativeTrace("window.fullscreen_did_exit")
        sendFullscreenState(reason: pendingFullscreenRequestID == nil ? "native" : "web")
        pendingFullscreenRequestID = nil
    }

    func windowDidFailToEnterFullScreen(_ window: NSWindow) {
        restoreHUDWindowBehavior()
        windowFullscreenMode = .normal
        nativeTrace("window.fullscreen_enter_failed")
        sendFullscreenState(reason: "failed", error: "MERRICK could not enter full screen on this display.")
        pendingFullscreenRequestID = nil
    }

    func windowDidFailToExitFullScreen(_ window: NSWindow) {
        windowFullscreenMode = .fullscreen
        nativeTrace("window.fullscreen_exit_failed")
        sendFullscreenState(reason: "failed", error: "MERRICK is still in full screen. Try Control–Command–F again.")
        pendingFullscreenRequestID = nil
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        true
    }

    private func terminateBackend(gracePeriod: TimeInterval = 8.0) {
        guard let backend else {
            terminateBackendProcessGroup()
            return
        }
        // Clear ownership before signalling an intentional stop. The process
        // termination callback only auto-recovers a process still owned here,
        // so provider verification, restart, quit and uninstall cannot be
        // mistaken for a crash while this bounded shutdown is in progress.
        self.backend = nil
        if backend.isRunning { backend.terminate() }

        // Give FastAPI enough time to close the WebSocket and terminate the
        // OpenClaw child it owns. Keep the wait bounded so Quit can never hang.
        // A normal exit persists the final owner-memory turn and pushes the
        // user-approved private backup before closing the backend.
        let deadline = Date().addingTimeInterval(gracePeriod)
        while backend.isRunning && Date() < deadline {
            Thread.sleep(forTimeInterval: 0.025)
        }
        if backend.isRunning {
            nativeTrace("backend.force_kill pid=\(backend.processIdentifier)")
            Darwin.kill(backend.processIdentifier, SIGKILL)
            backend.waitUntilExit()
        }
        nativeTrace("backend.stopped status=\(backend.terminationStatus)")
        terminateBackendProcessGroup()
    }

    private func terminateBackendProcessGroup() {
        guard let group = backendProcessGroup, group > 1 else { return }
        backendProcessGroup = nil
        guard Darwin.kill(-group, 0) == 0 else { return }
        nativeTrace("backend.process_group_terminate pgid=\(group)")
        _ = Darwin.kill(-group, SIGTERM)
        let deadline = Date().addingTimeInterval(1.0)
        while Darwin.kill(-group, 0) == 0 && Date() < deadline {
            Thread.sleep(forTimeInterval: 0.025)
        }
        if Darwin.kill(-group, 0) == 0 {
            nativeTrace("backend.process_group_force_kill pgid=\(group)")
            _ = Darwin.kill(-group, SIGKILL)
        }
    }

    /// Make termination visually and acoustically final before the process
    /// exits.  This prevents stale streamed speech/text from briefly living
    /// on in an existing WebKit surface and ensures all MERRICK-owned windows
    /// leave the desktop together.
    private func clearTransientDesktopState() {
        guard !terminationCleanupStarted else { return }
        terminationCleanupStarted = true
        webView?.evaluateJavaScript("window.merrickNativeAppClosing && window.merrickNativeAppClosing()")
        for panel in researchWindows {
            panel.orderOut(nil)
            panel.close()
        }
        researchWindows.removeAll()
        researchDelegates.removeAll()
        window?.orderOut(nil)
    }

    func applicationWillTerminate(_ notification: Notification) {
        appTerminating = true
        nativeTrace("app.will_terminate")
        NSWorkspace.shared.notificationCenter.removeObserver(self)
        backendHealthTask?.cancel()
        backendHealthTask = nil
        clearTransientDesktopState()
        stopListening(final: false)
        systemAudioFilterActivated = false
        playbackReferenceRequested = false
        stopPlaybackIsolation()
        audioIsolation.stop()
        terminateProviderLoginProcessGroup()
        terminateProviderValidationProcessGroup()
        terminateOwnedProviderProcess(
            openClawDashboardProcess,
            processGroup: openClawDashboardProcessGroup
        )
        if let process = nativeActionProcess, process.isRunning {
            Darwin.kill(process.processIdentifier, SIGKILL)
        }
        if let requestID = nativeActionInFlight {
            cancelNativeAction(requestID: requestID)
        }
        terminateBackend()
    }
}

@main
struct MerrickApplicationMain {
    private static func installApplicationMenu(on app: NSApplication) {
        let mainMenu = NSMenu()
        let applicationItem = NSMenuItem()
        let applicationMenu = NSMenu()
        applicationMenu.addItem(
            withTitle: "Quit MERRICK",
            action: #selector(NSApplication.terminate(_:)),
            keyEquivalent: "q"
        )
        applicationItem.submenu = applicationMenu
        mainMenu.addItem(applicationItem)
        app.mainMenu = mainMenu
    }

    static func main() {
        let app = NSApplication.shared
        let controller = MerrickController()
        app.delegate = controller
        app.setActivationPolicy(.regular)
        installApplicationMenu(on: app)
        app.run()
    }
}
