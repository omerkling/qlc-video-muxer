console.log("Background script loaded");
chrome.runtime.onConnect.addListener(function(port) {
  console.log("Background script connection from", port);
});
var connectionPort = chrome.runtime.connect("clfdibnalkjlldallnplmafniggkcdjb", {name: "presoremote"});
console.log("Background page made connection to remote extension", connectionPort);
