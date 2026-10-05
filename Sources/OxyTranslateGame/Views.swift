import SwiftUI
import Translation

struct MainView: View {
    @ObservedObject var model: AppModel
    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            HStack(spacing: 14) {
                Image(systemName: "character.bubble.fill").font(.system(size: 36)).foregroundStyle(.teal)
                VStack(alignment: .leading, spacing: 4) {
                    Text("OxyTranslateGame").font(.system(size: 25, weight: .bold))
                    Text("Перевод любой области экрана").foregroundStyle(.secondary)
                }
                Spacer()
            }
            HStack {
                Picker("С", selection: $model.source) {
                    ForEach(model.languages, id: \.0) { Text($0.1).tag($0.0) }
                }
                Image(systemName: "arrow.right")
                Picker("На", selection: $model.target) {
                    ForEach(model.languages, id: \.0) { Text($0.1).tag($0.0) }
                }
            }.disabled(model.busy || model.watching)
            HStack {
                Button(action: model.selectRegion) { Label("Выбрать область", systemImage: "viewfinder") }
                    .buttonStyle(.borderedProminent).tint(.teal)
                Button("Перевести снова", action: model.translateAgain).disabled(!model.hasRegion || model.busy)
                if model.watching || model.busy { Button("Остановить", action: model.stop) }
            }.controlSize(.large)
            GroupBox {
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Toggle("Следить за областью", isOn: Binding(get: { model.watching }, set: { $0 ? model.startWatching() : model.stop() }))
                            .toggleStyle(.switch).disabled(!model.hasRegion)
                        Spacer()
                        Picker("Интервал", selection: $model.interval) {
                            Text("1 с").tag(1.0); Text("2 с").tag(2.0); Text("4 с").tag(4.0)
                        }.frame(width: 160)
                    }
                    Picker("Выделить область", selection: $model.shiftShortcut) {
                        Text("⌥⌘T").tag(false); Text("⇧⌥⌘T").tag(true)
                    }.frame(width: 280)
                    Text("Горячая клавиша работает и в игре. После перемещения окна выберите область заново.")
                        .font(.caption).foregroundStyle(.secondary)
                }.padding(6)
            }
            HStack {
                if model.busy { ProgressView().controlSize(.small) }
                Text(model.status).font(.callout).textSelection(.enabled)
                Spacer()
            }.frame(minHeight: 35)
            Divider()
            HStack {
                Button("Доступ к экрану", action: model.requestAccess)
                Button("Подготовить языки", action: model.prepareLanguages).disabled(model.busy)
                Spacer()
                Text("На устройстве · без API-ключей").font(.caption).foregroundStyle(.secondary)
            }
            Text("Первый перевод может потребовать загрузки языков Apple. Приложение не сохраняет снимки экрана и текст на диск.")
                .font(.caption).foregroundStyle(.secondary)
        }
        .padding(26).frame(width: 620)
        .onChange(of: model.source) { model.changeLanguages() }
        .onChange(of: model.target) { model.changeLanguages() }
        .onChange(of: model.shiftShortcut) { model.updateShortcut() }
        .translationTask(model.configuration) { session in await model.translate(using: session) }
    }
}

struct ResultView: View {
    @ObservedObject var model: AppModel
    @State private var showOriginal = false
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "character.bubble").foregroundStyle(.teal)
                Text("OxyTranslateGame").font(.headline)
                Spacer()
                if model.watching { Text("Слежение").font(.caption).foregroundStyle(.teal) }
                Button(action: model.closeResult) { Image(systemName: "xmark") }.buttonStyle(.plain).help("Закрыть и остановить слежение (Esc)")
            }
            HStack {
                if model.busy { ProgressView().controlSize(.small) }
                Text(model.status).font(.caption).foregroundStyle(.secondary).lineLimit(3)
            }
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    Text(model.translated.isEmpty ? "Перевод появится здесь" : model.translated)
                        .font(.system(size: 19)).textSelection(.enabled).frame(maxWidth: .infinity, alignment: .leading)
                    if showOriginal {
                        Divider()
                        Text(model.original).font(.system(size: 14)).foregroundStyle(.secondary).textSelection(.enabled)
                    }
                }
            }
            HStack {
                Toggle("Оригинал", isOn: $showOriginal).toggleStyle(.checkbox)
                Spacer()
                Button("Копировать") {
                    NSPasteboard.general.clearContents(); NSPasteboard.general.setString(model.translated, forType: .string)
                }
                Button("Настройки") { model.showMain?() }
            }.font(.caption)
        }.padding(20).frame(minWidth: 360, minHeight: 180).background(.regularMaterial)
        .onExitCommand { model.closeResult() }
    }
}
