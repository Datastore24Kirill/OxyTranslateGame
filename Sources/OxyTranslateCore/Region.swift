import Foundation
import CoreGraphics

public enum RegionGeometry {
    /// AppKit local coordinates (bottom-left) to ScreenCaptureKit points (top-left).
    public static func captureRect(selection: CGRect, displaySize: CGSize) -> CGRect {
        let bounded = selection.standardized.intersection(CGRect(origin: .zero, size: displaySize))
        guard !bounded.isNull, bounded.width >= 12, bounded.height >= 12 else { return .zero }
        return CGRect(x: bounded.minX, y: displaySize.height - bounded.maxY,
                      width: bounded.width, height: bounded.height)
    }
}

public enum TextIdentity {
    public static func normalized(_ text: String) -> String {
        text.split(whereSeparator: \.isWhitespace).joined(separator: " ")
    }
}

public struct TranslationCache {
    private var values: [String: String] = [:]
    private var order: [String] = []
    public let limit: Int
    public init(limit: Int = 100) { self.limit = max(1, limit) }
    private func key(_ text: String, _ source: String, _ target: String) -> String {
        "\(source)\u{0}\(target)\u{0}\(TextIdentity.normalized(text))"
    }
    public func value(for text: String, source: String, target: String) -> String? {
        values[key(text, source, target)]
    }
    public mutating func insert(_ value: String, for text: String, source: String, target: String) {
        let k = key(text, source, target)
        if values[k] == nil { order.append(k) }
        values[k] = value
        while order.count > limit { values.removeValue(forKey: order.removeFirst()) }
    }
}
