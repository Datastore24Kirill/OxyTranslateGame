import XCTest
import CoreGraphics
@testable import OxyTranslateCore
final class CoreTests: XCTestCase {
    func testBottomLeftToTopLeftConversion() {
        XCTAssertEqual(RegionGeometry.captureRect(selection: CGRect(x: 10, y: 100, width: 200, height: 60), displaySize: CGSize(width: 1920, height: 1080)), CGRect(x: 10, y: 920, width: 200, height: 60))
    }
    func testBoundsAndSmallSelections() {
        XCTAssertEqual(RegionGeometry.captureRect(selection: CGRect(x: -20, y: 90, width: 50, height: 40), displaySize: CGSize(width: 100, height: 100)), .zero)
        XCTAssertEqual(RegionGeometry.captureRect(selection: CGRect(x: -20, y: 20, width: 50, height: 40), displaySize: CGSize(width: 100, height: 100)), CGRect(x: 0, y: 40, width: 30, height: 40))
    }
    func testCacheSeparatesLanguagePairsAndIgnoresWhitespace() {
        var cache = TranslationCache(limit: 2)
        cache.insert("Привет", for: "Hello\n world", source: "en", target: "ru")
        XCTAssertEqual(cache.value(for: "Hello world", source: "en", target: "ru"), "Привет")
        XCTAssertNil(cache.value(for: "Hello world", source: "en", target: "de"))
        cache.insert("B", for: "two", source: "en", target: "ru")
        cache.insert("C", for: "three", source: "en", target: "ru")
        XCTAssertNil(cache.value(for: "Hello world", source: "en", target: "ru"))
    }
}
