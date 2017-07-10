chrome.app.runtime.onLaunched.addListener(function() {
  console.log('Extension loaded');
  startServer();
});
function $(id) {
  return document.getElementById(id);
}

function log(text) {
  console.log(text);
}

function startServer() {
  var port = 9999;
  var isServer = false;
  if (http.Server && http.WebSocketServer) {
    // Listen for HTTP connections.
    var server = new http.Server();
    var wsServer = new http.WebSocketServer(server);
    server.listen(port);

    server.addEventListener('request', function(req) {
      var url = req.headers.url;
      if (url == '/')
        url = '/index.html';
      // Serve the pages of this chrome application.
      req.serveUrl(url);
      return true;
    });

    // A list of connected websockets.
    var connectedSockets = [];
    var connectedMessagePorts = [];

    wsServer.addEventListener('request', function(req) {
      log('Client connected');
      var socket = req.accept();
      connectedSockets.push(socket);

      // When a message is received on one socket, rebroadcast it on all
      // connected sockets.
      socket.addEventListener('message', function(e) {
        console.log("Received message", e);
        for (var i = 0; i < connectedMessagePorts.length; i++) {
          var port = connectedMessagePorts[i];
          port.postMessage(e.data);
        }
      });

      // When a socket is closed, remove it from the list of connected sockets.
      socket.addEventListener('close', function() {
        log('Client disconnected');
        for (var i = 0; i < connectedSockets.length; i++) {
          if (connectedSockets[i] == socket) {
            connectedSockets.splice(i, 1);
            break;
          }
        }
      });
      return true;
    });
    chrome.runtime.onMessageExternal.addListener(
      function(msg) {
        console.log("Received external message", msg);
      }
    );
    chrome.runtime.onConnectExternal.addListener(
      function(port) {
        console.log("Connection from port", port);
        connectedMessagePorts.push(port);
        port.onDisconnect.addListener(function() {
          connectedMessagePorts.splice(connectedMessagePorts.indexOf(port), 1);
        });
        port.onMessage.addListener(function(msg) {
          console.log("Received message", msg);
        });
      }
    );
  }
}
