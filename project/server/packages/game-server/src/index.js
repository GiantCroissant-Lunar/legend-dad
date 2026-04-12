import { createServer } from "node:http";
import { WebSocketServer } from "ws";

const PORT = Number.parseInt(process.env.PORT || "3000", 10);

const server = createServer((req, res) => {
  res.writeHead(200, { "Content-Type": "text/plain" });
  res.end("legend-dad game server\n");
});

const wss = new WebSocketServer({ server });

wss.on("connection", (ws, req) => {
  console.log(`[ws] client connected from ${req.socket.remoteAddress}`);

  ws.on("message", (data) => {
    console.log(`[ws] received: ${data}`);
    ws.send(JSON.stringify({ type: "echo", payload: data.toString() }));
  });

  ws.on("close", () => {
    console.log("[ws] client disconnected");
  });
});

server.listen(PORT, () => {
  console.log(`[server] listening on http://localhost:${PORT}`);
  console.log(`[ws] WebSocket server ready on ws://localhost:${PORT}`);
});
