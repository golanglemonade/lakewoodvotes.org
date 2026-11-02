/* Lakewood Votes: practice sample ballot (my-ballot.html).
 * - Saves marked choices in this browser only (localStorage). Nothing is sent anywhere.
 * - Hides the state House/Senate contests that aren't yours once lookup.js has saved your districts
 *   (lookup.js marks them .not-mine; CSS hides those inside .ballot).
 * - Print button. Without JavaScript the page still prints with every district and empty bubbles.
 */
(function () {
  "use strict";
  var KEY = "lv-ballot-2026-v1";
  var DKEY = "lv-districts-v1";

  function get(k) { try { return JSON.parse(localStorage.getItem(k) || "null"); } catch (e) { return null; } }
  function put(k, v) { try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }

  function refreshDistricts() {
    var d = get(DKEY), label = document.getElementById("b-districts"), all = document.querySelector(".b-alldist");
    var ballot = document.getElementById("ballot");
    var has = !!(d && d.hd && d.sd);
    if (label) label.textContent = has
      ? "State House District " + d.hd + " · State Senate District " + d.sd
      : "All Lakewood state House and Senate districts shown";
    if (all) all.hidden = has;
    if (ballot) ballot.classList.toggle("has-districts", has);
  }

  function count() {
    var form = document.getElementById("ballot"), out = document.getElementById("b-count");
    if (!form || !out) return;
    var sets = form.querySelectorAll("fieldset.b-contest"), shown = 0, marked = 0;
    for (var i = 0; i < sets.length; i++) {
      if (sets[i].offsetParent === null) continue;  // hidden (not your district)
      shown++;
      if (sets[i].querySelector("input:checked")) marked++;
    }
    out.textContent = marked + " of " + shown + " marked";
  }

  document.addEventListener("DOMContentLoaded", function () {
    var ballot = document.getElementById("ballot");
    if (!ballot) return;
    var saved = get(KEY) || {};
    var inputs = ballot.querySelectorAll("input[type=radio]");
    for (var i = 0; i < inputs.length; i++) {
      if (saved[inputs[i].name] === inputs[i].value) inputs[i].checked = true;
    }
    ballot.addEventListener("change", function (ev) {
      var t = ev.target;
      if (!t || t.type !== "radio") return;
      var s = get(KEY) || {};
      s[t.name] = t.value;
      put(KEY, s);
      count();
    });
    // Click a marked bubble again to un-mark it (radios can't normally be cleared).
    ballot.addEventListener("click", function (ev) {
      var t = ev.target;
      if (!t || t.type !== "radio") return;
      if (t.dataset.was === "1") {
        t.checked = false; t.dataset.was = "";
        var s = get(KEY) || {}; delete s[t.name]; put(KEY, s); count();
      } else {
        var group = ballot.querySelectorAll("input[name='" + t.name + "']");
        for (var j = 0; j < group.length; j++) group[j].dataset.was = "";
        t.dataset.was = "1";
      }
    });
    for (var k = 0; k < inputs.length; k++) if (inputs[k].checked) inputs[k].dataset.was = "1";

    var pr = document.getElementById("b-print"), cl = document.getElementById("b-clear");
    if (pr) { pr.hidden = false; pr.addEventListener("click", function () { window.print(); }); }
    if (cl) {
      cl.hidden = false;
      cl.addEventListener("click", function () {
        put(KEY, null);
        for (var i = 0; i < inputs.length; i++) { inputs[i].checked = false; inputs[i].dataset.was = ""; }
        count();
      });
    }
    refreshDistricts();
    count();
    // lookup.js updates districts after a lookup; re-check when its result area changes.
    var res = document.getElementById("lookup-result");
    if (res && window.MutationObserver) {
      new MutationObserver(function () { setTimeout(function () { refreshDistricts(); count(); }, 0); })
        .observe(res, { childList: true });
    }
  });
})();
