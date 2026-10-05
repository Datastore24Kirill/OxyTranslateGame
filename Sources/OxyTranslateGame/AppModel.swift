import AppKit
import SwiftUI
import Translation
import OxyTranslateCore
import OSLog

@MainActor
final class AppModel: ObservableObject {
    @Published var source = "en"
    @Published var target = "ru"
    @Published var status = "Выберите область экрана, которую нужно перевести"
    @Published var original = ""
    @Published var translated = ""
    @Published var busy = false
    @Published var watching = false
    @Published var interval = 2.0
    @Published var shiftShortcut = false
    @Published var hasRegion = false
    @Published var configuration: TranslationSession.Configuration?
    @Published var hasScreenAccess = CGPreflightScreenCaptureAccess()
    @Published var languagesReady = false
    let languages = [("en", "English"), ("ru", "Русский"), ("de", "Deutsch"), ("fr", "Français"), ("es", "Español"), ("it", "Italiano"), ("ja", "日本語"), ("ko", "한국어"), ("zh-Hans", "中文"), ("pt", "Português"), ("uk", "Українська")]
    var showMain: (() -> Void)?
    var hideMain: (() -> Void)?
    var showResult: (() -> Void)?
    var hideResult: (() -> Void)?
    private let selector = RegionSelector()
    let shortcut = HotKey()
    private(set) var region: SelectedRegion?
    private var watchTask: Task<Void, Never>?
    private var operation: Task<Void, Never>?
    private var generation = UUID()
    private var cache = TranslationCache()
    private var lastText = ""
    private var preparing = false
    private let logger = Logger(subsystem: "com.oxyfire.OxyTranslateGame", category: "translation")

    init() {
        shortcut.action = { [weak self] in self?.selectRegion() }
        updateShortcut()
    }
    func updateShortcut() {
        if !shortcut.register(useShift: shiftShortcut) { status = "Горячая клавиша занята. Выберите другое сочетание." }
    }
    func requestAccess() {
        if !CGPreflightScreenCaptureAccess() { _ = CGRequestScreenCaptureAccess() }
        hasScreenAccess = CGPreflightScreenCaptureAccess()
        if !hasScreenAccess {
            NSWorkspace.shared.open(URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture")!)
            status = "Разрешите запись экрана для OxyTranslateGame. Если доступ не обновился — перезапустите приложение."
        } else { status = "Доступ к экрану получен" }
    }
    func selectRegion() {
        stop()
        hasScreenAccess = CGPreflightScreenCaptureAccess()
        guard hasScreenAccess else { requestAccess(); return }
        hideResult?(); hideMain?()
        selector.begin { [weak self] region in
            guard let self else { return }
            guard let region else { self.status = "Выделение отменено"; return }
            self.region = region; self.hasRegion = true; self.lastText = ""
            self.operation = Task {
                try? await Task.sleep(for: .milliseconds(180))
                guard !Task.isCancelled else { return }
                await self.capture(force: true)
            }
        }
    }
    func translateAgain() {
        guard !busy else { return }
        if region == nil { selectRegion(); return }
        operation = Task { await capture(force: true) }
    }
    func startWatching() {
        guard region != nil, !watching else { return }
        watching = true
        watchTask = Task { [weak self] in
            while !Task.isCancelled {
                guard let self else { return }
                if !self.busy { await self.capture(force: false) }
                try? await Task.sleep(for: .seconds(self.interval))
            }
        }
    }
    func stop() {
        watchTask?.cancel(); watchTask = nil; watching = false
        operation?.cancel(); operation = nil
        generation = UUID(); configuration = nil; busy = false; preparing = false
        status = "Остановлено"
    }
    func changeLanguages() { stop(); lastText = ""; languagesReady = false }
    func closeResult() { stop(); hideResult?() }
    func prepareLanguages() {
        guard !busy else { return }
        guard source != target else { status = "Выберите разные языки"; return }
        busy = true; preparing = true; status = "Подготовка языков…"; showMain?()
        triggerTranslation()
    }
    private func triggerTranslation() {
        if configuration == nil {
            configuration = .init(source: Locale.Language(identifier: source), target: Locale.Language(identifier: target))
        } else { configuration?.invalidate() }
    }
    private func capture(force: Bool) async {
        guard let region, !busy else { return }
        guard source != target else { status = "Выберите разные языки"; return }
        let token = generation
        busy = true; status = "Распознаю текст…"; showResult?()
        do {
            let text = try await ScreenReader.read(region, language: source)
            guard token == generation, !Task.isCancelled else { return }
            let normalized = TextIdentity.normalized(text)
            if !force && normalized == lastText { busy = false; status = "Слежение: текст не изменился"; return }
            original = text
            if let saved = cache.value(for: text, source: source, target: target) {
                translated = saved; lastText = normalized; busy = false
                status = "Перевод готов"; showResult?(); return
            }
            status = "Перевожу…"
            if !languagesReady { showMain?() }
            triggerTranslation()
        } catch {
            guard token == generation else { return }
            busy = false; status = error.localizedDescription; showResult?()
            if !(error is CaptureFailure) { logger.error("Capture failed: \(error.localizedDescription, privacy: .public)"); stopWatchingOnError() }
        }
    }
    private func stopWatchingOnError() { watchTask?.cancel(); watchTask = nil; watching = false }
    func translate(using session: TranslationSession) async {
        let token = generation
        let text = original; let isPreparation = preparing
        let from = source; let to = target
        do {
            let availability = await LanguageAvailability().status(from: Locale.Language(identifier: from), to: Locale.Language(identifier: to))
            guard token == generation else { return }
            guard availability != .unsupported else {
                status = "Эта пара языков не поддерживается переводчиком Apple"; busy = false; preparing = false; stopWatchingOnError(); return
            }
            if isPreparation {
                try await session.prepareTranslation()
                guard token == generation else { return }
                languagesReady = true; preparing = false; busy = false; status = "Языки готовы. Теперь можно переводить без интернета."; return
            }
            let response = try await session.translate(text)
            guard token == generation, !Task.isCancelled else { return }
            translated = response.targetText; lastText = TextIdentity.normalized(text)
            cache.insert(translated, for: text, source: from, target: to)
            languagesReady = true; busy = false; status = "Перевод готов"; showResult?()
        } catch {
            guard token == generation else { return }
            preparing = false; busy = false; stopWatchingOnError()
            status = "Не удалось перевести: \(error.localizedDescription)"
            logger.error("Translation failed: \(error.localizedDescription, privacy: .public)")
        }
    }
}
