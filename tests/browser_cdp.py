import itertools
import json
import time
import urllib.request


class CDP:
    def __init__(self, socket, process_id):
        self.socket = socket
        self.ids = itertools.count(1)
        self.process_id = process_id

    @classmethod
    def new_page(cls, port, url):
        request = urllib.request.Request(
            f"http://127.0.0.1:{port}/json/new?about:blank", method="PUT"
        )
        with urllib.request.urlopen(request) as response:
            target = json.load(response)
        import websocket
        socket = websocket.create_connection(target["webSocketDebuggerUrl"], timeout=10)
        cdp = cls(socket, target["id"])
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")
        cdp.call("Page.navigate", {"url": url})
        return cdp

    def call(self, method, params=None):
        call_id = next(self.ids)
        self.socket.send(json.dumps({"id": call_id, "method": method, "params": params or {}}))
        while True:
            message = json.loads(self.socket.recv())
            if message.get("id") == call_id:
                if "error" in message:
                    raise RuntimeError(message["error"])
                return message.get("result", {})

    def eval(self, expression):
        result = self.call("Runtime.evaluate", {
            "expression": expression, "awaitPromise": True, "returnByValue": True,
        })
        value = result["result"]
        if "exceptionDetails" in result:
            raise RuntimeError(result["exceptionDetails"])
        return value.get("value")

    def wait(self, expression, timeout=10):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.eval(f"Boolean({expression})"):
                return
            time.sleep(0.05)
        diagnostic = self.eval("""({
          url:location.href, state:document.readyState,
          text:document.body ? document.body.innerText : null,
          error:document.querySelector('#start-error')?.textContent
        })""")
        raise AssertionError(f"browser condition timed out: {expression}; {diagnostic}")

    def click(self, action):
        self.eval(f"document.querySelector('[data-action=\"{action}\"]').click()")

    def choose_and_click(self, name, action):
        self.wait(f"document.querySelector('input[name=\"{name}\"]')")
        self.eval(
            f"document.querySelector('input[name=\"{name}\"]').checked=true;"
            f"document.querySelector('[data-action=\"{action}\"]').click()"
        )
        time.sleep(0.03)

    def close(self):
        self.socket.close()
