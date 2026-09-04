import AppKit
import AVFoundation
import CoreMedia
import ImageIO
import ScreenCaptureKit
import UniformTypeIdentifiers

private enum CaptureMode: String {
    case screenshot
    case video
}

private struct CaptureArguments {
    let mode: CaptureMode
    let outputURL: URL
    let duration: TimeInterval
    let scale: CGFloat
    let captureAudio: Bool

    init(_ rawArguments: [String]) throws {
        guard rawArguments.count >= 3,
              let mode = CaptureMode(rawValue: rawArguments[1]) else {
            throw CaptureError.usage
        }

        self.mode = mode
        self.outputURL = URL(fileURLWithPath: rawArguments[2]).standardizedFileURL
        self.duration = rawArguments.count > 3 ? max(1, Double(rawArguments[3]) ?? 8) : 8
        self.scale = rawArguments.count > 4 ? max(1, CGFloat(Double(rawArguments[4]) ?? 2)) : 2
        self.captureAudio = rawArguments.count > 5 && rawArguments[5] == "audio"
    }
}

private enum CaptureError: LocalizedError {
    case usage
    case windowNotFound
    case imageUnavailable
    case imageWriteFailed
    case recordingFailed(String)

    var errorDescription: String? {
        switch self {
        case .usage:
            return "Usage: capture-jarvis-window screenshot|video OUTPUT [DURATION_SECONDS] [SCALE] [audio]"
        case .windowNotFound:
            return "No visible ai.jarvis.desktop window was found. Open MERRICK first."
        case .imageUnavailable:
            return "ScreenCaptureKit returned no image."
        case .imageWriteFailed:
            return "The PNG could not be written."
        case .recordingFailed(let message):
            return "Recording failed: \(message)"
        }
    }
}

@available(macOS 15.0, *)
private final class RecordingDelegate: NSObject, SCRecordingOutputDelegate {
    private let lock = NSLock()
    private var didStart = false
    private var result: Result<Void, Error>?

    func recordingOutputDidStartRecording(_ recordingOutput: SCRecordingOutput) {
        lock.withLock { didStart = true }
    }

    func recordingOutput(_ recordingOutput: SCRecordingOutput, didFailWithError error: Error) {
        lock.withLock { result = .failure(error) }
    }

    func recordingOutputDidFinishRecording(_ recordingOutput: SCRecordingOutput) {
        lock.withLock { result = .success(()) }
    }

    func waitUntilStarted(timeout: TimeInterval = 5) async throws {
        let deadline = Date().addingTimeInterval(timeout)
        while Date() < deadline {
            if let snapshot = lock.withLock({ (didStart, result) }) as (Bool, Result<Void, Error>?)? {
                if case .failure(let error) = snapshot.1 { throw error }
                if snapshot.0 { return }
            }
            try await Task.sleep(for: .milliseconds(50))
        }
        throw CaptureError.recordingFailed("timed out while starting")
    }

    func waitUntilFinished(timeout: TimeInterval = 15) async throws {
        let deadline = Date().addingTimeInterval(timeout)
        while Date() < deadline {
            if let snapshot = lock.withLock({ result }) {
                return try snapshot.get()
            }
            try await Task.sleep(for: .milliseconds(50))
        }
        throw CaptureError.recordingFailed("timed out while finalizing")
    }
}

@available(macOS 15.0, *)
@main
private struct MerrickWindowCapture {
    private static let bundleIdentifier = "ai.jarvis.desktop"

    static func main() async {
        do {
            // ScreenCaptureKit still needs a CoreGraphics/AppKit connection
            // when the utility is launched from a non-interactive build shell.
            // Keep the helper off the Dock while establishing that session.
            let application = NSApplication.shared
            application.setActivationPolicy(.accessory)
            application.finishLaunching()
            let arguments = try CaptureArguments(CommandLine.arguments)
            let (window, filter) = try await merrickWindow()
            let configuration = streamConfiguration(
                for: window,
                scale: arguments.scale,
                captureAudio: arguments.mode == .video && arguments.captureAudio
            )

            try FileManager.default.createDirectory(
                at: arguments.outputURL.deletingLastPathComponent(),
                withIntermediateDirectories: true
            )

            switch arguments.mode {
            case .screenshot:
                try await captureScreenshot(
                    filter: filter,
                    configuration: configuration,
                    outputURL: arguments.outputURL
                )
            case .video:
                try await captureVideo(
                    filter: filter,
                    configuration: configuration,
                    outputURL: arguments.outputURL,
                    duration: arguments.duration
                )
            }

            print("Captured \(Int(configuration.width))×\(Int(configuration.height)) to \(arguments.outputURL.path)")
        } catch {
            fputs("\(error.localizedDescription)\n", stderr)
            exit(1)
        }
    }

    private static func merrickWindow() async throws -> (SCWindow, SCContentFilter) {
        let content = try await SCShareableContent.excludingDesktopWindows(
            false,
            onScreenWindowsOnly: true
        )
        guard let window = content.windows
            .filter({
                $0.owningApplication?.bundleIdentifier == bundleIdentifier &&
                $0.frame.width >= 640 &&
                $0.frame.height >= 480
            })
            .max(by: { $0.frame.width * $0.frame.height < $1.frame.width * $1.frame.height }) else {
            throw CaptureError.windowNotFound
        }
        return (window, SCContentFilter(desktopIndependentWindow: window))
    }

    private static func streamConfiguration(
        for window: SCWindow,
        scale: CGFloat,
        captureAudio: Bool
    ) -> SCStreamConfiguration {
        let configuration = SCStreamConfiguration()
        configuration.width = Int(window.frame.width * scale)
        configuration.height = Int(window.frame.height * scale)
        configuration.minimumFrameInterval = CMTime(value: 1, timescale: 30)
        configuration.queueDepth = 6
        configuration.showsCursor = false
        configuration.capturesAudio = captureAudio
        configuration.excludesCurrentProcessAudio = true
        configuration.sampleRate = 48_000
        configuration.channelCount = 2
        configuration.pixelFormat = kCVPixelFormatType_32BGRA
        return configuration
    }

    private static func captureScreenshot(
        filter: SCContentFilter,
        configuration: SCStreamConfiguration,
        outputURL: URL
    ) async throws {
        let image = try await SCScreenshotManager.captureImage(
            contentFilter: filter,
            configuration: configuration
        )
        guard let destination = CGImageDestinationCreateWithURL(
            outputURL as CFURL,
            UTType.png.identifier as CFString,
            1,
            nil
        ) else {
            throw CaptureError.imageWriteFailed
        }
        CGImageDestinationAddImage(destination, image, nil)
        guard CGImageDestinationFinalize(destination) else {
            throw CaptureError.imageWriteFailed
        }
    }

    private static func captureVideo(
        filter: SCContentFilter,
        configuration: SCStreamConfiguration,
        outputURL: URL,
        duration: TimeInterval
    ) async throws {
        if FileManager.default.fileExists(atPath: outputURL.path) {
            try FileManager.default.removeItem(at: outputURL)
        }

        let outputConfiguration = SCRecordingOutputConfiguration()
        outputConfiguration.outputURL = outputURL
        outputConfiguration.videoCodecType = .h264
        outputConfiguration.outputFileType = .mp4

        let delegate = RecordingDelegate()
        let recordingOutput = SCRecordingOutput(
            configuration: outputConfiguration,
            delegate: delegate
        )
        let stream = SCStream(filter: filter, configuration: configuration, delegate: nil)
        try stream.addRecordingOutput(recordingOutput)
        try await stream.startCapture()
        try await delegate.waitUntilStarted()
        try await Task.sleep(for: .seconds(duration))
        try await stream.stopCapture()
        try await delegate.waitUntilFinished()
    }
}
