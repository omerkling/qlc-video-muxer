console.log("Preso remote loaded");
function onLoad() {
  var connectionPort = chrome.runtime.connect("fofjlmofilnhgaimkpaafphjdibnnohm", {name: "presoremote"});
  // var connectionPort = chrome.runtime.connect();

  console.log("Made remote connection", connectionPort);

  function createEvent(eventType) {
    var clickEvent = document.createEvent ('MouseEvents');
    clickEvent.initEvent (eventType, true, true);
    return clickEvent;
  }
  window.createEvent = createEvent;
  connectionPort.onMessage.addListener(function(message) {
    console.log("Received remote message:", message);
    var command = message.split(':');
    if (command[0] == "goto") {
      var page = parseInt(command[1]);
      var elementSelector = command[1] == 'next' ? 'right' : 'left';
      console.log('Going to ' + elementSelector);
      var element = window.top.document.querySelectorAll(".punch-present-iframe")[0].contentWindow.document.querySelectorAll('.punch-viewer-icon.punch-viewer-' + elementSelector)[0].parentNode;
      element.dispatchEvent(createEvent('mousedown'));
      element.dispatchEvent(createEvent('mouseup'));
    }
  });
}

var actualCode = '(' + onLoad + ')();';
var script = document.createElement('script');
script.textContent = actualCode;
(document.head||document.documentElement).appendChild(script);
script.remove();

// chrome.browserAction.onClicked.addListener(function (tab) { //Fired when User Clicks ICON
//   console.log("Clicked browser action");
//   if (tab.url.indexOf("https://docs.google.com/presentation") != -1) { // Inspect whether the place where user clicked matches with our list of URL
//     console.log("Found site!");
//     connectionPort = chrome.runtime.connect("clfdibnalkjlldallnplmafniggkcdjb", {name: "presoremote"});
//   }
// });