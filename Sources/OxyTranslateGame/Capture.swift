import AppKit
import ScreenCaptureKit
import Vision
import OxyTranslateCore

struct SelectedRegion {
    let displayID: CGDirectDisplayID
    let localRect: CGRect
    let screenFrame: CGRect
    let scale: CGFloat
    var captureRect: CGRect { RegionGeometry.captureRect(selection: localRect, displaySize: screenFrame.size) }
    var globalRect: CGRect { localRect.offsetBy(dx: screenFrame.minX, dy: screenFrame.minY) }
}

enum CaptureFailure: LocalizedError {
    case displayMissing, noText
    var errorDescription: String? {
        switch self {
        case .displayMissing: return "Экран отключён или область изменилась. Выберите область заново."
        case .noText: return "Текст не найден. Выделите текст крупнее и дождитесь завершения анимации."
        }
    }
}

struct ScreenReader {
    static func read(_ region: SelectedRegion, language: String) async throws -> String {
        let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)
        guard let display = content.displays.first(where: { $0.displayID == region.displayID }) else {
            throw CaptureFailure.displayMissing
        }
        // Exclude our control, selection and translation windows to avoid translating the overlay.
        let ownWindows = content.windows.filter { $0.owningApplication?.processID == ProcessInfo.processInfo.processIdentifier }
        let filter = SCContentFilter(display: display, excludingWindows: ownWindows)
        let config = SCStreamConfiguration()
        config.sourceRect = region.captureRect
        config.width = max(1, Int(region.captureRect.width * region.scale))
        config.height = max(1, Int(region.captureRect.height * region.scale))
        config.showsCursor = false
        let image = try await SCScreenshotManager.captureImage(contentFilter: filter, configuration: config)
        return try await Task.detached(priority: .userInitiated) {
            try recognize(image, language: language)
        }.value
    }

    static func recognize(_ image: CGImage, language: String) throws -> String {
        let request = VNRecognizeTextRequest()
        request.recognitionLevel = .accurate
        request.usesLanguageCorrection = true
        request.recognitionLanguages = [language]
        request.automaticallyDetectsLanguage = true
        try VNImageRequestHandler(cgImage: image).perform([request])
        let text = (request.results ?? []).compactMap { observation in
            guard let candidate = observation.topCandidates(1).first, candidate.confidence > 0.25 else { return nil as String? }
            return candidate.string
        }.joined(separator: "\n")
        guard !TextIdentity.normalized(text).isEmpty else { throw CaptureFailure.noText }
        return text
    }
}
