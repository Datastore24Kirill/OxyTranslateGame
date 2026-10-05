import AppKit

final class SelectionPanel: NSPanel {
    override var canBecomeKey: Bool { true }
}

@MainActor
final class RegionSelector {
    private var panels: [NSPanel] = []
    private var completion: ((SelectedRegion?) -> Void)?

    func begin(completion: @escaping (SelectedRegion?) -> Void) {
        cancel()
        self.completion = completion
        for screen in NSScreen.screens {
            let panel = SelectionPanel(contentRect: screen.frame, styleMask: [.borderless], backing: .buffered, defer: false)
            panel.level = .screenSaver
            panel.isOpaque = false
            panel.backgroundColor = .clear
            panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
            panel.hasShadow = false
            let view = SelectionView(frame: CGRect(origin: .zero, size: screen.frame.size))
            view.onSelect = { [weak self] rect in
                guard let id = screen.deviceDescription[NSDeviceDescriptionKey("NSScreenNumber")] as? UInt32 else { self?.cancel(); return }
                self?.finish(SelectedRegion(displayID: id, localRect: rect, screenFrame: screen.frame, scale: screen.backingScaleFactor))
            }
            view.onCancel = { [weak self] in self?.cancel() }
            panel.contentView = view
            panels.append(panel)
            panel.orderFrontRegardless()
        }
        NSApp.activate(ignoringOtherApps: true)
        panels.first(where: { $0.frame.contains(NSEvent.mouseLocation) })?.makeKey()
    }
    func cancel() { finish(nil) }
    private func finish(_ value: SelectedRegion?) {
        for panel in panels { panel.orderOut(nil) }
        panels.removeAll()
        let callback = completion
        completion = nil
        callback?(value)
    }
}

final class SelectionView: NSView {
    var onSelect: ((CGRect) -> Void)?
    var onCancel: (() -> Void)?
    private var start: CGPoint?
    private var selection = CGRect.zero
    override var acceptsFirstResponder: Bool { true }
    override func resetCursorRects() { addCursorRect(bounds, cursor: .crosshair) }
    override func draw(_ dirtyRect: NSRect) {
        NSColor.black.withAlphaComponent(0.30).setFill()
        bounds.fill()
        if !selection.isEmpty {
            NSColor.white.withAlphaComponent(0.20).setFill()
            selection.fill()
            NSColor.systemTeal.setStroke()
            let path = NSBezierPath(rect: selection); path.lineWidth = 2; path.stroke()
        }
        let title = "Выделите область с текстом · Esc — отмена"
        let attrs: [NSAttributedString.Key: Any] = [.font: NSFont.systemFont(ofSize: 22, weight: .semibold), .foregroundColor: NSColor.white]
        title.draw(at: CGPoint(x: 32, y: bounds.height - 70), withAttributes: attrs)
    }
    override func mouseDown(with event: NSEvent) { start = convert(event.locationInWindow, from: nil) }
    override func mouseDragged(with event: NSEvent) {
        guard let start else { return }
        let end = convert(event.locationInWindow, from: nil)
        selection = CGRect(x: min(start.x, end.x), y: min(start.y, end.y), width: abs(end.x - start.x), height: abs(end.y - start.y)).intersection(bounds)
        needsDisplay = true
    }
    override func mouseUp(with event: NSEvent) {
        mouseDragged(with: event)
        if selection.width >= 12 && selection.height >= 12 { onSelect?(selection) }
        else { onCancel?() }
    }
    override func keyDown(with event: NSEvent) {
        if event.keyCode == 53 { onCancel?() } else { super.keyDown(with: event) }
    }
}
