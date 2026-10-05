// swift-tools-version: 6.0
import PackageDescription
let package = Package(
    name: "OxyTranslateGame",
    platforms: [.macOS(.v15)],
    products: [.executable(name: "OxyTranslateGame", targets: ["OxyTranslateGame"])],
    targets: [
        .target(name: "OxyTranslateCore"),
        .executableTarget(name: "OxyTranslateGame", dependencies: ["OxyTranslateCore"]),
        .testTarget(name: "OxyTranslateCoreTests", dependencies: ["OxyTranslateCore"])
    ],
    swiftLanguageModes: [.v5]
)
