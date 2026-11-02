/* Lakewood Votes: find your state House and Senate districts from your address.
 *
 * Uses the U.S. Census Bureau Geocoder (public, no key) over JSONP so it works on a static site.
 * The address goes only to the Census Bureau. We keep just the district numbers in this browser
 * (localStorage) so other pages can mark "your district". Without JavaScript the form is hidden
 * and the page still links to GoVoteColorado.gov.
 */
(function () {
  "use strict";
  var KEY = "lv-districts-v1";
  var GEOCODER = "https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress";

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY) || "null"); } catch (e) { return null; }
  }
  function save(v) {
    try { v ? localStorage.setItem(KEY, JSON.stringify(v)) : localStorage.removeItem(KEY); } catch (e) { /* private mode */ }
  }
  function el(tag, attrs, text) {
    var n = document.createElement(tag);
    for (var k in attrs || {}) n.setAttribute(k, attrs[k]);
    if (text != null) n.textContent = text;
    return n;
  }
  function pick(geos, needle) {
    for (var k in geos) if (k.indexOf(needle) !== -1 && geos[k] && geos[k][0]) return geos[k][0];
    return null;
  }

  function jsonp(url, cb) {
    var name = "lvGeo" + Date.now(), s = document.createElement("script"), done = false;
    var timer = setTimeout(function () { finish(null); }, 20000);
    function finish(data) {
      if (done) return; done = true; clearTimeout(timer);
      try { delete window[name]; } catch (e) { window[name] = undefined; }
      if (s.parentNode) s.parentNode.removeChild(s);
      cb(data);
    }
    window[name] = finish;
    s.onerror = function () { finish(null); };
    s.src = url + "&format=jsonp&callback=" + name;
    document.head.appendChild(s);
  }

  function lookup(address, cb) {
    var q = "?address=" + encodeURIComponent(address) +
      "&benchmark=Public_AR_Current&vintage=Current_Current&layers=all";
    jsonp(GEOCODER + q, function (data) {
      if (!data || !data.result) return cb({ error: "network" });
      var m = (data.result.addressMatches || [])[0];
      if (!m) return cb({ error: "nomatch" });
      var g = m.geographies || {};
      var lower = pick(g, "Legislative Districts - Lower");
      var upper = pick(g, "Legislative Districts - Upper");
      var place = pick(g, "Incorporated Places");
      var county = pick(g, "Counties");
      var cd = pick(g, "Congressional Districts");
      cb({
        matched: m.matchedAddress,
        hd: lower ? String(parseInt(lower.BASENAME, 10)) : null,
        sd: upper ? String(parseInt(upper.BASENAME, 10)) : null,
        cd: cd ? String(parseInt(cd.BASENAME, 10)) : null,
        place: place ? place.BASENAME : null,
        county: county ? county.BASENAME : null
      });
    });
  }

  /* ---------- home page form ---------- */
  function renderResult(box, r, races, prefix) {
    box.textContent = "";
    if (r.error) {
      box.appendChild(el("p", { "class": "lookup-msg" }, r.error === "nomatch"
        ? "We couldn't find that address. Try the street address with city and ZIP, like 480 S Allison Pkwy, Lakewood, CO 80226."
        : "The address lookup didn't answer. Please try again in a minute, or use GoVoteColorado.gov."));
      return;
    }
    box.appendChild(el("p", { "class": "meta" }, "Matched: " + r.matched));
    var warn = [];
    if (r.place !== "Lakewood") warn.push("This address is not inside the City of Lakewood" +
      (r.place ? " (it is in " + r.place + ")" : "") + ", so the Lakewood city questions (2G–2J) won't be on its ballot, and other local questions may be.");
    if (r.county && r.county !== "Jefferson") warn.push("This address is in " + r.county + " County, not Jefferson County. This guide covers Jefferson County races.");
    if (r.cd && r.cd !== "7") warn.push("This address is in Congressional District " + r.cd + ", not District 7.");
    warn.forEach(function (w) { box.appendChild(el("p", { "class": "lookup-warn" }, w)); });

    var ul = el("ul", { "class": "lookup-list" });
    [["hd", "State House District"], ["sd", "State Senate District"]].forEach(function (pair) {
      var num = r[pair[0]], li = el("li");
      if (!num) { li.textContent = pair[1] + ": not found"; ul.appendChild(li); return; }
      var id = pair[0] + "-" + num, label = pair[1] + " " + num;
      if (races[id]) {
        var a = el("a", { href: prefix + "races/" + id + ".html" }, label);
        li.appendChild(a);
        li.appendChild(document.createTextNode(" — " + races[id]));
      } else {
        li.textContent = label + " — not covered in this guide (it isn't a Lakewood district on the 2026 ballot).";
      }
      ul.appendChild(li);
    });
    box.appendChild(ul);
    box.appendChild(el("p", { "class": "note" },
      "The federal, statewide, county and judge races and the statewide measures are the same for every Lakewood voter. " +
      "We saved these two district numbers in this browser so the Offices page can mark them. Your address was not saved."));
    var clear = el("button", { type: "button", "class": "btn secondary" }, "Forget my districts");
    clear.addEventListener("click", function () { save(null); box.textContent = ""; mark(); });
    box.appendChild(clear);
  }

  function initForm(form) {
    var races = JSON.parse(form.getAttribute("data-races") || "{}");
    var prefix = form.getAttribute("data-prefix") || "";
    var box = document.getElementById("lookup-result");
    var input = form.querySelector("input");
    var btn = form.querySelector("button");
    form.hidden = false;
    var prev = load();
    if (prev && prev.matched) renderResult(box, prev, races, prefix);
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var addr = input.value.trim();
      if (!addr) return;
      if (!/co(lorado)?\b|8\d{4}/i.test(addr)) addr += ", Lakewood, CO";
      btn.disabled = true; btn.textContent = "Looking up…";
      box.textContent = ""; box.appendChild(el("p", { "class": "meta" }, "Asking the U.S. Census Bureau…"));
      lookup(addr, function (r) {
        btn.disabled = false; btn.textContent = "Find my districts";
        if (!r.error) save({ matched: r.matched, hd: r.hd, sd: r.sd, cd: r.cd, place: r.place, county: r.county });
        renderResult(box, r, races, prefix);
        mark();
        box.focus();
      });
    });
  }

  /* ---------- mark "your district" on any page with race cards ---------- */
  function mark() {
    updatePrompt();
    var d = load();
    var mine = d ? ["hd-" + d.hd, "sd-" + d.sd] : [];
    var cards = document.querySelectorAll("[data-race]");
    for (var i = 0; i < cards.length; i++) {
      var c = cards[i], id = c.getAttribute("data-race");
      if (!/^(hd|sd)-/.test(id)) continue;
      var on = mine.indexOf(id) !== -1, badge = c.querySelector(".mine");
      c.classList.toggle("is-mine", on);
      c.classList.toggle("not-mine", !!d && !on);
      if (on && !badge) {
        var b = el("span", { "class": "badge mine" }, "Your district");
        c.insertBefore(b, c.firstChild);
      } else if (!on && badge) badge.parentNode.removeChild(badge);
    }
  }

  /* ---------- put the districts (never the address) into the AI prompt ---------- */
  function updatePrompt() {
    var p = document.getElementById("ai-prompt");
    if (!p) return;
    var base = p.getAttribute("data-base");
    if (base == null) { base = p.textContent; p.setAttribute("data-base", base); }
    var d = load(), note = document.getElementById("ai-prompt-note");
    if (!d || !d.hd || !d.sd) {
      p.textContent = base;
      if (note) note.hidden = true;
      return;
    }
    var bits = "I'm in Colorado State House District " + d.hd + " and State Senate District " + d.sd;
    if (d.cd) bits += ", Congressional District " + d.cd;
    bits += d.place === "Lakewood" ? ", inside the City of Lakewood" : (d.place ? ", in " + d.place + " (not the City of Lakewood)" : "");
    bits += ". I already looked these up, so you don't need to ask which districts I'm in. ";
    var cut = base.indexOf(". ") + 2;  // after the first sentence
    p.textContent = base.slice(0, cut) + bits + base.slice(cut);
    if (note) note.hidden = false;
  }

  function initCopy() {
    var b = document.getElementById("ai-copy"), p = document.getElementById("ai-prompt");
    if (!b || !p || !navigator.clipboard) return;
    b.hidden = false;
    b.addEventListener("click", function () {
      navigator.clipboard.writeText(p.textContent).then(function () {
        b.textContent = "Copied";
        setTimeout(function () { b.textContent = "Copy"; }, 2000);
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var form = document.getElementById("lookup-form");
    if (form) initForm(form);
    initCopy();
    mark();
  });
})();
