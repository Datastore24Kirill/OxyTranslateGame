import AppKit
import SwiftUI
import Vision

final class TranslationPanel: NSPanel {
    override var canBecomeKey: Bool { true }
    override func cancelOperation(_ sender: Any?) { onClose?() }
    var onClose: (() -> Void)?
}

@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate, NSWindowDelegate {
    private let model = AppModel()
    private var window: NSWindow!
    private var result: TranslationPanel!
    private var statusItem: NSStatusItem!
    func applicationDidFinishLaunching(_ notification: Notification) {
        buildMenu()
        window = NSWindow(contentRect: CGRect(x: 0, y: 0, width: 672, height: 480), styleMask: [.titled, .closable, .miniaturizable], backing: .buffered, defer: false)
        window.title = "OxyTranslateGame"
        window.isReleasedWhenClosed = false; window.delegate = self
        window.contentView = NSHostingView(rootView: MainView(model: model))
        if let size = window.contentView?.fittingSize { window.setContentSize(size) }
        window.center()
        result = TranslationPanel(contentRect: CGRect(x: 0, y: 0, width: 480, height: 300), styleMask: [.titled, .resizable, .nonactivatingPanel], backing: .buffered, defer: false)
        result.title = "Перевод"; result.titleVisibility = .hidden; result.titlebarAppearsTransparent = true
        result.isFloatingPanel = true; result.level = .floating; result.hidesOnDeactivate = false
        result.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        result.isReleasedWhenClosed = false; result.minSize = NSSize(width: 380, height: 230)
        result.contentView = NSHostingView(rootView: ResultView(model: model))
        result.onClose = { [weak self] in self?.model.closeResult() }
        model.showMain = { [weak self] in self?.showSettings() }
        model.hideMain = { [weak self] in self?.window.orderOut(nil) }
        model.hideResult = { [weak self] in self?.result.orderOut(nil) }
        model.showResult = { [weak self] in self?.presentResult() }
        showSettings()
    }
    private func presentResult() {
        if !result.isVisible {
            let screen = NSScreen.screens.first(where: { $0.frame == model.region?.screenFrame }) ?? NSScreen.main
            if let frame = screen?.visibleFrame {
                let selected = model.region?.globalRect ?? frame
                let x = min(max(selected.minX, frame.minX), frame.maxX - result.frame.width)
                let below = selected.minY - result.frame.height - 12
                let y = max(frame.minY, min(below, frame.maxY - result.frame.height))
                result.setFrameOrigin(NSPoint(x: x, y: y))
            }
            result.makeKeyAndOrderFront(nil)
        } else { result.orderFrontRegardless() }
    }
    @objc private func showSettings() { window.makeKeyAndOrderFront(nil); NSApp.activate(ignoringOtherApps: true) }
    @objc private func selectArea() { model.selectRegion() }
    @objc private func stop() { model.closeResult() }
    @objc private func quit() { model.stop(); NSApp.terminate(nil) }
    private func buildMenu() {
        let menu = NSMenu()
        let appMenu = NSMenu()
        let root = NSMenuItem(); root.submenu = appMenu; menu.addItem(root)
        appMenu.addItem(withTitle: "OxyTranslateGame", action: #selector(showSettings), keyEquivalent: ",").target = self
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: "Завершить OxyTranslateGame", action: #selector(quit), keyEquivalent: "q").target = self
        let edit = NSMenuItem(title: "Правка", action: nil, keyEquivalent: "")
        let editMenu = NSMenu(title: "Правка")
        editMenu.addItem(withTitle: "Копировать", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
        editMenu.addItem(withTitle: "Выбрать всё", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")
        edit.submenu = editMenu; menu.addItem(edit); NSApp.mainMenu = menu
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        statusItem.button?.image = NSImage(systemSymbolName: "character.bubble", accessibilityDescription: "OxyTranslateGame")
        let tray = NSMenu()
        for (title, action) in [("Выбрать область", #selector(selectArea)), ("Остановить / скрыть перевод", #selector(stop)), ("Настройки", #selector(showSettings)), ("Завершить", #selector(quit))] {
            tray.addItem(withTitle: title, action: action, keyEquivalent: "").target = self
        }
        statusItem.menu = tray
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { false }
    func applicationWillTerminate(_ notification: Notification) { model.stop() }
}

@main
struct OxyTranslateGame {
    @MainActor static func main() {
        // Offline OCR check for development/CI; never captures a live screen.
        if let index = CommandLine.arguments.firstIndex(of: "--ocr-test"), CommandLine.arguments.count > index + 1 {
            let path = CommandLine.arguments[index + 1]
            DispatchQueue.global(qos: .userInitiated).async {
                do {
                    let url = URL(fileURLWithPath: path)
                    guard let image = NSImage(contentsOf: url)?.cgImage(forProposedRect: nil, context: nil, hints: nil) else { throw CaptureFailure.noText }
                    print(try ScreenReader.recognize(image, language: "en")); exit(0)
                } catch { fputs("OCR test failed: \(error)\n", stderr); exit(1) }
            }
            RunLoop.main.run()
            return
        }

        let app = NSApplication.shared
        app.setActivationPolicy(.regular)
        let delegate = AppDelegate()
        app.delegate = delegate
        withExtendedLifetime(delegate) { app.run() }
    }
}
