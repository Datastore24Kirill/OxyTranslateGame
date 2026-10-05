import AppKit
import Carbon

@MainActor
final class HotKey {
    private var key: EventHotKeyRef?
    private var handler: EventHandlerRef?
    var action: (() -> Void)?
    func register(useShift: Bool) -> Bool {
        if let key { UnregisterEventHotKey(key) }; key = nil
        if handler == nil {
            var event = EventTypeSpec(eventClass: OSType(kEventClassKeyboard), eventKind: UInt32(kEventHotKeyPressed))
            InstallEventHandler(GetApplicationEventTarget(), { _, _, context -> OSStatus in
                guard let context else { return OSStatus(eventNotHandledErr) }
                let object = Unmanaged<HotKey>.fromOpaque(context).takeUnretainedValue()
                DispatchQueue.main.async { object.action?() }
                return noErr
            }, 1, &event, Unmanaged.passUnretained(self).toOpaque(), &handler)
        }
        let modifiers = UInt32(cmdKey | optionKey | (useShift ? shiftKey : 0))
        return RegisterEventHotKey(UInt32(kVK_ANSI_T), modifiers, EventHotKeyID(signature: 0x4F585954, id: 1), GetApplicationEventTarget(), 0, &key) == noErr
    }
    deinit {
        if let key { UnregisterEventHotKey(key) }
        if let handler { RemoveEventHandler(handler) }
    }
}
