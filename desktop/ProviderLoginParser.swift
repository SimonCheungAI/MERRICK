import Foundation

struct ProviderLoginPrompt {
    let verificationURL: URL?
    let deviceCode: String?
}

enum ProviderLoginParser {
    private static let verificationURLExpression = try! NSRegularExpression(
        pattern: "\\bURL:\\s*(https://[^\\s\\\"'<>]+)",
        options: [.caseInsensitive]
    )
    private static let deviceCodeExpression = try! NSRegularExpression(
        // Only publish a complete terminal line. A PTY chunk can end halfway
        // through a valid-looking code; publishing that prefix breaks sign-in.
        pattern: "\\bCode:[ \\t]*([A-Z0-9]{4,12}(?:-[A-Z0-9]{4,12})*)[ \\t│┃]*\\n",
        options: [.caseInsensitive]
    )

    private static func firstCapturedValue(
        _ expression: NSRegularExpression,
        in text: String
    ) -> String? {
        let range = NSRange(text.startIndex..., in: text)
        guard let match = expression.firstMatch(in: text, range: range),
              match.numberOfRanges > 1,
              let matchedRange = Range(match.range(at: 1), in: text) else { return nil }
        return String(text[matchedRange])
    }

    private static func stripTerminalEscapes(_ text: String) -> String {
        let scalars = Array(text.unicodeScalars)
        var readable = String.UnicodeScalarView()
        var index = 0
        while index < scalars.count {
            guard scalars[index].value == 0x1B else {
                readable.append(scalars[index])
                index += 1
                continue
            }
            index += 1
            guard index < scalars.count else { break }
            if scalars[index].value == 0x5B { // CSI: ESC [ ... final byte
                index += 1
                while index < scalars.count {
                    let value = scalars[index].value
                    index += 1
                    if value >= 0x40 && value <= 0x7E { break }
                }
            } else if scalars[index].value == 0x5D { // OSC: ESC ] ... BEL / ESC \
                index += 1
                while index < scalars.count {
                    if scalars[index].value == 0x07 {
                        index += 1
                        break
                    }
                    if scalars[index].value == 0x1B,
                       index + 1 < scalars.count,
                       scalars[index + 1].value == 0x5C {
                        index += 2
                        break
                    }
                    index += 1
                }
            } else {
                index += 1
            }
        }
        return String(readable)
    }

    static func parse(_ rawOutput: String) -> ProviderLoginPrompt {
        let readable = stripTerminalEscapes(rawOutput)
            .replacingOccurrences(of: "\r", with: "\n")
            .unicodeScalars
            .filter { scalar in
                scalar == "\n" || scalar == "\t" || scalar.value >= 0x20
            }
            .map(String.init)
            .joined()
        let rawURL = firstCapturedValue(verificationURLExpression, in: readable)
        let verificationURL = rawURL.flatMap(URL.init(string:)).flatMap { url in
            url.scheme?.lowercased() == "https" && url.host != nil ? url : nil
        }
        let deviceCode = firstCapturedValue(deviceCodeExpression, in: readable)
        return ProviderLoginPrompt(
            verificationURL: verificationURL,
            deviceCode: deviceCode
        )
    }
}
