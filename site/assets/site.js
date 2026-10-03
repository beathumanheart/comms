// Small conveniences. The site works without this file.
(function () {
  "use strict";

  // Home page: show the next four planned posts, counted from today.
  var agenda = document.getElementById("agenda");
  if (agenda) {
    var now = new Date();
    var today = now.getFullYear() + "-" + String(now.getMonth() + 1).padStart(2, "0") +
      "-" + String(now.getDate()).padStart(2, "0");
    var shown = 0;
    Array.prototype.forEach.call(agenda.children, function (item) {
      var upcoming = item.getAttribute("data-date") >= today && shown < 4;
      item.hidden = !upcoming;
      if (upcoming) { shown += 1; }
    });
    var empty = document.getElementById("agenda-empty");
    if (empty) { empty.hidden = shown > 0; }
  }

  // Lines meant to be copied (table rows in the how-to pages) get a Copy button.
  Array.prototype.forEach.call(document.querySelectorAll(".prose pre"), function (pre) {
    var button = document.createElement("button");
    button.type = "button";
    button.className = "copy";
    button.textContent = "Copy";
    button.addEventListener("click", function () {
      var text = pre.querySelector("code").textContent.replace(/\n$/, "");
      var done = function () {
        button.textContent = "Copied";
        setTimeout(function () { button.textContent = "Copy"; }, 2000);
      };
      var select = function () {
        var range = document.createRange();
        range.selectNodeContents(pre.querySelector("code"));
        var selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
        button.textContent = "Selected — now copy";
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, select);
      } else {
        select();
      }
    });
    pre.appendChild(button);
  });
})();
