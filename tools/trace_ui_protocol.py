"""Attach to the running client and log packet I/O plus event vtable slots.

Usage: python tools/trace_ui_protocol.py
Output: state/ui-protocol-trace.jsonl (append)
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'pylibs'))
import frida

OUT = Path(__file__).resolve().parents[1] / 'state' / 'ui-protocol-trace.jsonl'
SEND_EVENT_RVA = 0x682D80

AGENT = r'''
const game = Process.enumerateModules().find(m => /x2_dx11/i.test(m.name)) ||
             Process.enumerateModules().find(m => /x2/i.test(m.name));
if (!game) { send({error: 'client module not found'}); } else {
  send({event: 'module', name: game.name, base: game.base.toString(), size: game.size});
  let dumped = false;
  Interceptor.attach(game.base.add(0x682D80), {
    onEnter(args) {
      const object = args[0];
      const event = args[1];
      let id = -1, kind = -1;
      try { id = event.add(16).readU32(); kind = event.add(0x34).readU16(); } catch (e) {}
      send({t: Date.now() / 1000, event: 'send_event', self: object.toString(), id, kind});
      if (dumped) return;
      dumped = true;
      try {
        const vtable = object.readPointer();
        const slots = [];
        for (let i = 0; i < 64; i++) {
          const slot = vtable.add(i * 8).readPointer();
          slots.push(slot.isNull() ? null : slot.toString());
        }
        send({t: Date.now() / 1000, event: 'vtable', self: object.toString(), vtable: vtable.toString(), slots});
      } catch (e) { send({t: Date.now() / 1000, event: 'vtable_error', error: String(e)}); }
    }
  });
}
'''

def main():
    deadline = time.time() + 900
    while True:
        processes = [p for p in frida.get_local_device().enumerate_processes()
                     if 'x2' in p.name.lower() or 'elsword' in p.name.lower()]
        if processes:
            break
        if time.time() > deadline:
            print('client process not running; start the game first')
            return 1
        time.sleep(2)
    process = processes[0]
    print('attaching to', process.name, process.pid)
    session = frida.attach(process.pid)
    stream = OUT.open('a', encoding='utf8')
    script = session.create_script(AGENT)
    def on_message(message, data):
        if message.get('type') == 'send':
            stream.write(json.dumps(message['payload'], ensure_ascii=False) + '\n')
            stream.flush()
        else:
            stream.write(json.dumps({'error': message}, ensure_ascii=False) + '\n')
            stream.flush()
    script.on('message', on_message)
    script.load()
    print('tracing to', OUT)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        stream.close()
        session.detach()
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
