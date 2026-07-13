"""
link_hints.py
Vimium-style link hints, implemented as a self-contained content script that
runs inside every page (see Browser._install_link_hints_script). Press the
trigger key (Vim `f` by default) and every clickable element gets a short
letter label; type the label to click it. Escape cancels.

Running it in the page (rather than driving it from Qt) means it receives key
events directly from the web content, so it works regardless of whether the
Qt-level Vim event filter can see keys while the web view has focus.

`__TRIGGER_KEY__` is substituted with the user's configured link_hints key.
"""

from __future__ import annotations

LINK_HINTS_JS = r"""
(function () {
  if (window.__voidHints) return;
  window.__voidHints = true;

  var TRIGGER = "__TRIGGER_KEY__";
  var CHARS = "asdfghjklqwertyuiopzxcvbnm";
  var SEL = "a[href], button, input:not([type=hidden]):not([disabled]), " +
            "textarea, select, [onclick], [role=button], [role=link], " +
            "[contenteditable=true], [tabindex]:not([tabindex='-1'])";

  var state = { active: false, newtab: false, typed: "", hints: [], box: null };

  function editable(el) {
    if (!el) return false;
    var t = el.tagName;
    return el.isContentEditable || t === "INPUT" || t === "TEXTAREA" || t === "SELECT";
  }

  function visible(el) {
    var r = el.getBoundingClientRect();
    if (r.width <= 1 || r.height <= 1) return false;
    if (r.bottom < 0 || r.right < 0 || r.top > innerHeight || r.left > innerWidth) return false;
    var s = getComputedStyle(el);
    return !(s.visibility === "hidden" || s.display === "none" ||
             s.pointerEvents === "none" || parseFloat(s.opacity) === 0);
  }

  function makeLabels(n) {
    var out = [];
    if (n <= CHARS.length) {
      for (var i = 0; i < n; i++) out.push(CHARS[i]);
    } else {
      for (var i = 0; i < CHARS.length && out.length < n; i++)
        for (var j = 0; j < CHARS.length && out.length < n; j++)
          out.push(CHARS[i] + CHARS[j]);
    }
    return out;
  }

  function show() {
    var els = Array.prototype.slice.call(document.querySelectorAll(SEL)).filter(visible);
    if (!els.length) return;
    var labels = makeLabels(els.length);
    var box = document.createElement("div");
    box.id = "void-hints-overlay";
    box.style.cssText = "position:fixed;top:0;left:0;width:0;height:0;z-index:2147483647;";
    state.hints = [];
    for (var i = 0; i < els.length; i++) {
      var el = els[i], r = el.getBoundingClientRect(), label = labels[i];
      var tag = document.createElement("span");
      tag.textContent = label.toUpperCase();
      tag.style.cssText =
        "position:fixed;left:" + Math.max(0, r.left - 2) + "px;top:" + Math.max(0, r.top - 2) + "px;" +
        "background:#ffd76e;color:#101014;font:bold 11px/1.2 ui-monospace,monospace;" +
        "padding:1px 4px;border-radius:4px;border:1px solid #a67c00;" +
        "box-shadow:0 1px 3px rgba(0,0,0,.5);white-space:nowrap;pointer-events:none;";
      box.appendChild(tag);
      state.hints.push({ label: label, el: el, tag: tag });
    }
    document.documentElement.appendChild(box);
    state.box = box;
    state.active = true;
    state.typed = "";
    window.addEventListener("scroll", hide, true);
    window.addEventListener("resize", hide, true);
  }

  function hide() {
    if (state.box && state.box.parentNode) state.box.parentNode.removeChild(state.box);
    state.box = null;
    state.active = false;
    state.newtab = false;
    state.typed = "";
    state.hints = [];
    window.removeEventListener("scroll", hide, true);
    window.removeEventListener("resize", hide, true);
  }

  function activate(h) {
    var el = h.el, newtab = state.newtab;
    hide();
    if (editable(el)) { el.focus(); return; }
    if (newtab && el.tagName === "A" && el.href) { window.open(el.href, "_blank"); return; }
    try { el.focus({ preventScroll: true }); } catch (e) {}
    el.click();
  }

  function filter() {
    var matches = state.hints.filter(function (h) { return h.label.indexOf(state.typed) === 0; });
    if (matches.length === 0) { hide(); return; }
    if (matches.length === 1) { activate(matches[0]); return; }
    for (var i = 0; i < state.hints.length; i++) {
      var h = state.hints[i];
      h.tag.style.opacity = (h.label.indexOf(state.typed) === 0) ? "1" : "0.25";
    }
  }

  window.addEventListener("keydown", function (e) {
    if (!state.active) {
      if (e.ctrlKey || e.altKey || e.metaKey || editable(document.activeElement)) return;
      var lower = TRIGGER.toLowerCase(), upper = TRIGGER.toUpperCase();
      if (e.key === lower) {
        e.preventDefault(); e.stopImmediatePropagation();
        state.newtab = false; show();
      } else if (upper !== lower && e.key === upper && e.shiftKey) {
        // Shift + trigger => activate the chosen link in a NEW tab.
        e.preventDefault(); e.stopImmediatePropagation();
        state.newtab = true; show();
      }
      return;
    }
    e.preventDefault();
    e.stopImmediatePropagation();
    if (e.key === "Escape") { hide(); return; }
    if (e.key === "Backspace") { state.typed = state.typed.slice(0, -1); filter(); return; }
    var k = (e.key || "").toLowerCase();
    if (k.length !== 1 || CHARS.indexOf(k) === -1) return;
    state.typed += k;
    filter();
  }, true);
})();
"""
