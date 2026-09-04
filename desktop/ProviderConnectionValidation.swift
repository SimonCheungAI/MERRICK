import Foundation

struct ProviderConnectionRecord: Codable {
    let provider: String
    let model: String
    let authMode: String
    let profileUpdatedAt: Date
    let validatedAt: Date
    let stage: ProviderConnectionStage
    let code: String
    let message: String

    var isReady: Bool { stage == .ready && code == "READY" }
}

struct ProviderProbeOutcome {
    let ready: Bool
    let code: String
    let message: String
    let latencyMilliseconds: Int?

    static func failure(_ code: String, _ message: String) -> ProviderProbeOutcome {
        ProviderProbeOutcome(
            ready: false,
            code: code,
            message: message,
            latencyMilliseconds: nil
        )
    }
}

/// Parses OpenClaw's provider probes without trusting process exit status or a
/// different credential profile. OpenClaw may print warnings before its JSON,
/// so the parser deliberately extracts the first complete JSON object.
enum ProviderProbeParser {
    static func probeProvider(for provider: String) -> String? {
        RuntimeContract.providers[provider]?.probeRoute
    }

    static func parse(
        _ output: String,
        expectedProvider: String,
        expectedProfileID: String? = nil
    ) -> ProviderProbeOutcome {
        guard let root = firstJSONObject(in: output),
              let auth = root["auth"] as? [String: Any],
              let probes = auth["probes"] as? [String: Any],
              let results = probes["results"] as? [[String: Any]] else {
            return contractFailure("INVALID_PROBE_OUTPUT")
        }

        let providerResults = results.filter {
            normalized($0["provider"] as? String) == normalized(expectedProvider)
        }
        guard !providerResults.isEmpty else {
            return contractFailure("PROVIDER_NOT_PROBED")
        }

        let matchingResults: [[String: Any]]
        if let expectedProfileID {
            matchingResults = providerResults.filter {
                ($0["profileId"] as? String) == expectedProfileID
            }
            guard !matchingResults.isEmpty else {
                return contractFailure("PROFILE_NOT_PROBED")
            }
        } else {
            matchingResults = providerResults
        }

        if let success = matchingResults.first(where: {
            normalized($0["status"] as? String) == "ok"
        }) {
            return ProviderProbeOutcome(
                ready: true,
                code: "READY",
                message: "Connection verified.",
                latencyMilliseconds: success["latencyMs"] as? Int
            )
        }

        let failure = matchingResults.first ?? [:]
        let detail = [
            failure["error"] as? String,
            failure["message"] as? String,
            failure["status"] as? String,
        ].compactMap { $0 }.joined(separator: " ").lowercased()

        return classifyFailureText(detail)
    }

    static func classifyFailureText(_ detail: String) -> ProviderProbeOutcome {
        let detail = detail.lowercased()
        for matcher in RuntimeContract.failureMatchers {
            if detail.range(of: matcher.pattern, options: .regularExpression) != nil {
                return contractFailure(matcher.probeCode)
            }
        }
        return contractFailure("PROBE_FAILED")
    }

    static func failureOutcome(_ code: String) -> ProviderProbeOutcome {
        contractFailure(code)
    }

    private static func contractFailure(_ code: String) -> ProviderProbeOutcome {
        .failure(
            code,
            RuntimeContract.connectionFailures[code]?.messageEnglish
                ?? "The provider could not complete the connection check."
        )
    }

    private static func normalized(_ value: String?) -> String {
        (value ?? "").trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
    }

    private static func firstJSONObject(in output: String) -> [String: Any]? {
        let characters = Array(output)
        for start in characters.indices where characters[start] == "{" {
            var depth = 0
            var insideString = false
            var escaped = false
            for index in start..<characters.endIndex {
                let character = characters[index]
                if insideString {
                    if escaped {
                        escaped = false
                    } else if character == "\\" {
                        escaped = true
                    } else if character == "\"" {
                        insideString = false
                    }
                    continue
                }
                if character == "\"" {
                    insideString = true
                } else if character == "{" {
                    depth += 1
                } else if character == "}" {
                    depth -= 1
                    if depth == 0 {
                        let candidate = String(characters[start...index])
                        guard let data = candidate.data(using: .utf8) else { break }
                        if let object = try? JSONSerialization.jsonObject(with: data),
                           let dictionary = object as? [String: Any] {
                            return dictionary
                        }
                        break
                    }
                }
            }
        }
        return nil
    }
}
