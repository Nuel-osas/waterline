/* Waterline dashboard. Plain JavaScript, no framework. It reads data.js and claims.js; the only network use is the
   "Audit the latest block" button, which asks a public NEAR node from the reader's own browser. */
(function () {
  "use strict";
  var W = window.WATERLINE, CL = window.WATERLINE_CLAIMS, K = CL.by_id;
  var REPO = "https://github.com/Nuel-osas/waterline";
  var NS = "http://www.w3.org/2000/svg";
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var GROUP_COLORS = { NEAR: "#3987e5", Stablecoins: "#d95926", ZEC: "#199e70", BTC: "#c98500", ETH: "#d55181", Other: "#5E6A71" };
  var INK = "#0C1013", FOG = "#E9ECE8", FOG3 = "#7C878D", INK3 = "#626B70", ACCENT = "#3987E5", DEEP = "#070B0F", PAPER = "#EEEDE6";

  // ---------- small helpers ----------
  function T(day) { return Date.UTC(+day.slice(0, 4), +day.slice(5, 7) - 1, +day.slice(8, 10)); }
  function dayLong(day) { return +day.slice(8, 10) + " " + MONTHS[+day.slice(5, 7) - 1] + " " + day.slice(0, 4); }
  function dayShort(day) { return +day.slice(8, 10) + " " + MONTHS[+day.slice(5, 7) - 1]; }
  function usd(v) {
    var a = Math.abs(v), s = v < 0 ? "-" : "";
    if (a >= 1e9) return s + "$" + (a / 1e9).toFixed(2) + "B";
    if (a >= 1e6) return s + "$" + (a / 1e6).toFixed(1) + "M";
    if (a >= 1e3) return s + "$" + Math.round(a / 1e3) + "K";
    return s + "$" + Math.round(a);
  }
  function axisUsd(v) { return "$" + Math.round(v / 1e6) + "M"; }
  function el(tag, attrs, parent) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function text(parent, x, y, s, attrs) {
    var t = el("text", Object.assign({ x: x, y: y }, attrs || {}), parent);
    t.textContent = s;
    return t;
  }
  function html(tag, cls, s) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (s != null) e.textContent = s;
    return e;
  }
  function niceStep(max, target) {
    var raw = max / target, pow = Math.pow(10, Math.floor(Math.log10(raw))), n = raw / pow;
    return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 5 ? 5 : 10) * pow;
  }
  function monthTicks(t0, t1) {
    var out = [], d = new Date(t0);
    d = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 1));
    while (d.getTime() <= t1) { out.push({ t: d.getTime(), label: MONTHS[d.getUTCMonth()] }); d = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 1)); }
    return out;
  }
  function nearest(arr, x, getX) {
    var best = 0, bd = Infinity;
    for (var i = 0; i < arr.length; i++) { var d = Math.abs(getX(arr[i]) - x); if (d < bd) { bd = d; best = i; } }
    return best;
  }

  // ---------- tooltip ----------
  var tip = document.getElementById("tip");
  function showTip(ev, title, rows, sum) {
    tip.textContent = "";
    tip.appendChild(html("div", "t", title));
    rows.concat(sum ? [Object.assign({ sum: true }, sum)] : []).forEach(function (r) {
      var d = html("div", "r" + (r.sum ? " sum" : "")), s = html("span");
      if (r.color) { var i = html("i"); i.style.background = r.color; s.appendChild(i); }
      s.appendChild(document.createTextNode(r.name));
      d.appendChild(s); d.appendChild(html("b", null, r.value));
      tip.appendChild(d);
    });
    tip.hidden = false;
    var pad = 16, box = tip.getBoundingClientRect(), x = ev.clientX + pad, y = ev.clientY + pad;
    if (x + box.width > innerWidth - 8) x = ev.clientX - box.width - pad;
    if (y + box.height > innerHeight - 8) y = ev.clientY - box.height - pad;
    tip.style.left = Math.max(8, x) + "px"; tip.style.top = Math.max(8, y) + "px";
  }
  function hideTip() { tip.hidden = true; }
  function hover(svgNode, onMove, onLeave) {
    svgNode.addEventListener("pointermove", function (ev) {
      var r = svgNode.getBoundingClientRect();
      onMove(ev, (ev.clientX - r.left) * (svgNode.viewBox.baseVal.width / r.width));
    });
    svgNode.addEventListener("pointerdown", function (ev) {
      var r = svgNode.getBoundingClientRect();
      onMove(ev, (ev.clientX - r.left) * (svgNode.viewBox.baseVal.width / r.width));
    });
    svgNode.addEventListener("pointerleave", function () { hideTip(); onLeave(); });
  }

  // ---------- claims into the text ----------
  function fillClaims() {
    document.querySelectorAll("[data-claim]").forEach(function (n) {
      var c = K[n.getAttribute("data-claim")];
      if (!c) { n.textContent = "n/a"; return; }
      var s = c.shown, part = n.getAttribute("data-part"), m;
      if (part === "then" && (m = /\(([^)]+) then\)/.exec(c.what))) s = m[1];
      if (part === "unpriced" && (m = /\((\d+) of them/.exec(c.what))) s = m[1];
      if (n.getAttribute("data-fmt") === "date") s = dayLong(s);
      if (n.getAttribute("data-fmt") === "hm" && (m = /^(\d+) hours (\d+) minutes$/.exec(s))) s = m[1] + "h " + m[2] + "m";
      n.textContent = s;
      n.title = c.id + ": " + c.what;
    });
    document.querySelectorAll('[data-pin="height"]').forEach(function (n) { n.textContent = CL.pin_height.toLocaleString("en-US"); });
    document.querySelectorAll('[data-pin="day"]').forEach(function (n) { n.textContent = dayLong(CL.pin_day); });
    document.querySelectorAll('[data-pin="priced"]').forEach(function (n) { n.textContent = CL.priced_at.replace("T", " ").replace("Z", " UTC"); });
  }

  var EVENTS = [
    { day: W.events.b2b_launch, label: "13 Jul  B2B launch" },
    { day: W.events.all_private, label: "27 Oct  swaps go private" }
  ];

  // ---------- 1. the waterline: public above, private below ----------
  function chartWaterline() {
    var box = document.getElementById("chart-waterline");
    box.textContent = "";
    var pts = W.days.filter(function (d) { return d.share != null; }).map(function (d) {
      return { t: T(d.day), day: d.day, pub: d.public_usd, priv: d.private_usd, share: d.share };
    });
    if (pts.length < 2) return;
    var w = box.clientWidth, wide = w > 760, h = Math.round(Math.max(360, Math.min(620, w * 0.44)));
    var wrap = document.querySelector(".wl-head"), inset = wrap.getBoundingClientRect().left + parseFloat(getComputedStyle(wrap).paddingLeft);
    var m = { l: inset, r: inset + (wide ? 150 : 0), t: 40, b: 34 };
    var t0 = T(W.first_day), t1 = pts[pts.length - 1].t;
    var maxPub = Math.max.apply(null, pts.map(function (p) { return p.pub; })), maxPriv = Math.max.apply(null, pts.map(function (p) { return p.priv; }));
    var k = (h - m.t - m.b) / (maxPub * 1.15 + maxPriv * 1.08), zero = Math.round(m.t + maxPub * 1.15 * k);
    function X(t) { return m.l + (t - t0) / (t1 - t0) * (w - m.l - m.r); }
    box.style.background = "linear-gradient(to bottom, " + PAPER + " 0, " + PAPER + " " + zero + "px, " + DEEP + " " + zero + "px)";
    var s = el("svg", { viewBox: "0 0 " + w + " " + h, width: w, height: h }, box);

    var step = niceStep(Math.max(maxPub, maxPriv), 3);
    for (var v = step; v <= maxPub * 1.1; v += step) {
      el("line", { x1: m.l, x2: w - m.r, y1: zero - v * k, y2: zero - v * k, stroke: INK, "stroke-opacity": .1 }, s);
      text(s, m.l, zero - v * k - 6, axisUsd(v), { fill: INK3 });
    }
    for (v = step; v <= maxPriv * 1.05; v += step) {
      el("line", { x1: m.l, x2: w - m.r, y1: zero + v * k, y2: zero + v * k, stroke: FOG, "stroke-opacity": .1 }, s);
      text(s, m.l, zero + v * k - 6, axisUsd(v), { fill: FOG3 });
    }
    monthTicks(t0, t1).forEach(function (mt) { text(s, X(mt.t), h - 12, mt.label, { fill: FOG3, "text-anchor": "middle" }); });
    EVENTS.forEach(function (e, i) {
      var x = X(T(e.day));
      el("line", { x1: x, x2: x, y1: m.t - 14, y2: zero, stroke: INK, "stroke-opacity": .35 }, s);
      el("line", { x1: x, x2: x, y1: zero, y2: h - m.b, stroke: FOG, "stroke-opacity": .3 }, s);
      text(s, i === 1 && wide ? x - 8 : x + 8, m.t - 18, wide ? e.label : e.label.slice(0, 6), { fill: INK3, "text-anchor": i === 1 && wide ? "end" : "start" });
    });

    function path(get, sign) {
      return pts.map(function (p, i) { return (i ? "L" : "M") + X(p.t).toFixed(1) + "," + (zero + sign * get(p) * k).toFixed(1); }).join("");
    }
    var first = X(pts[0].t).toFixed(1), last = X(t1).toFixed(1);
    var up = path(function (p) { return p.pub; }, -1), down = path(function (p) { return p.priv; }, 1);
    el("path", { d: up + "L" + last + "," + zero + "L" + first + "," + zero + "Z", fill: INK, "fill-opacity": .08 }, s);
    el("path", { d: down + "L" + last + "," + zero + "L" + first + "," + zero + "Z", fill: ACCENT, "fill-opacity": .22 }, s);
    el("path", { d: up, fill: "none", stroke: INK, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }, s);
    el("path", { d: down, fill: "none", stroke: ACCENT, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }, s);

    var end = pts[pts.length - 1], ex = X(end.t);
    el("circle", { cx: ex, cy: zero - end.pub * k, r: 4.5, fill: INK, stroke: PAPER, "stroke-width": 2 }, s);
    el("circle", { cx: ex, cy: zero + end.priv * k, r: 4.5, fill: ACCENT, stroke: DEEP, "stroke-width": 2 }, s);
    if (wide) {
      text(s, ex + 14, zero - end.pub * k - 4, "Public", { fill: INK3 });
      text(s, ex + 14, zero - end.pub * k + 16, usd(end.pub), { fill: INK, "font-size": 17, "font-weight": 600, style: "font-family:var(--sans)" });
      text(s, ex + 14, zero + end.priv * k - 6, "Private", { fill: FOG3 });
      text(s, ex + 14, zero + end.priv * k + 14, usd(end.priv), { fill: FOG, "font-size": 17, "font-weight": 600, style: "font-family:var(--sans)" });
      text(s, ex + 14, zero + end.priv * k + 32, end.share.toFixed(1) + "% of these 20", { fill: FOG3 });
    } else {
      text(s, w - m.r, zero - 10, "Public " + usd(end.pub), { fill: INK, "text-anchor": "end", "font-weight": 600 });
      text(s, w - m.r, zero + 20, "Private " + usd(end.priv) + "  " + end.share.toFixed(1) + "%", { fill: FOG, "text-anchor": "end", "font-weight": 600 });
    }

    var cross = el("g", { visibility: "hidden" }, s);
    var c1 = el("line", { y1: m.t - 6, y2: zero, stroke: INK, "stroke-opacity": .55 }, cross), c2 = el("line", { y1: zero, y2: h - m.b, stroke: FOG, "stroke-opacity": .55 }, cross);
    var d1 = el("circle", { r: 4.5, fill: INK, stroke: PAPER, "stroke-width": 2 }, cross), d2 = el("circle", { r: 4.5, fill: ACCENT, stroke: DEEP, "stroke-width": 2 }, cross);
    hover(s, function (ev, x) {
      var p = pts[nearest(pts, x, function (q) { return X(q.t); })], px = X(p.t);
      cross.setAttribute("visibility", "visible");
      [c1, c2].forEach(function (c) { c.setAttribute("x1", px); c.setAttribute("x2", px); });
      d1.setAttribute("cx", px); d1.setAttribute("cy", zero - p.pub * k); d2.setAttribute("cx", px); d2.setAttribute("cy", zero + p.priv * k);
      showTip(ev, dayLong(p.day), [{ name: "Public", value: usd(p.pub), color: "#AAB4B9" }, { name: "Private", value: usd(p.priv), color: ACCENT }],
        { name: "Private share", value: p.share.toFixed(1) + "%" });
    }, function () { cross.setAttribute("visibility", "hidden"); });

    var table = document.getElementById("table-waterline");
    table.textContent = "";
    var head = table.insertRow();
    ["Reading", "Block", "Public", "Private", "Private share"].forEach(function (c) { head.appendChild(html("th", null, c)); });
    W.days.filter(function (d) { return d.share != null; }).reverse().forEach(function (d) {
      var r = table.insertRow();
      [dayLong(d.day), String(d.height), usd(d.public_usd), usd(d.private_usd), d.share.toFixed(1) + "%"].forEach(function (c) { r.insertCell().textContent = c; });
    });
  }

  // ---------- 2. the float by asset group ----------
  function chartStack() {
    var box = document.getElementById("chart-stack");
    box.textContent = "";
    var days = W.days, G = W.groups, w = box.clientWidth, wide = w > 700, h = Math.round(Math.max(300, Math.min(460, w * 0.4)));
    var m = { l: 0, r: wide ? 84 : 0, t: 26, b: 28 }, t0 = T(days[0].day), t1 = T(days[days.length - 1].day);
    var max = Math.max.apply(null, days.map(function (d) { return d.float_usd; })), step = niceStep(max, 3), top = Math.ceil(max / step) * step;
    function X(t) { return m.l + (t - t0) / (t1 - t0) * (w - m.l - m.r); }
    function Y(v) { return m.t + (1 - v / top) * (h - m.t - m.b); }
    var s = el("svg", { viewBox: "0 0 " + w + " " + h, width: w, height: h }, box);
    for (var v = 0; v <= top; v += step) {
      el("line", { x1: m.l, x2: w - m.r, y1: Y(v), y2: Y(v), stroke: FOG, "stroke-opacity": v ? .1 : .3 }, s);
      if (v) text(s, m.l, Y(v) - 6, axisUsd(v), { fill: FOG3 });
    }
    monthTicks(t0, t1).forEach(function (mt) { text(s, X(mt.t), h - 8, mt.label, { fill: FOG3, "text-anchor": "middle" }); });
    var base = days.map(function () { return 0; });
    G.forEach(function (g, gi) {
      var topLine = days.map(function (d, i) { return base[i] + d.groups[gi]; });
      var fwd = days.map(function (d, i) { return (i ? "L" : "M") + X(T(d.day)).toFixed(1) + "," + Y(topLine[i]).toFixed(1); }).join("");
      var back = days.map(function (d, i) { return "L" + X(T(d.day)).toFixed(1) + "," + Y(base[i]).toFixed(1); }).reverse().join("");
      el("path", { d: fwd + back + "Z", fill: GROUP_COLORS[g], "fill-opacity": .5 }, s);
      el("path", { d: fwd, fill: "none", stroke: DEEP, "stroke-width": 3 }, s);
      el("path", { d: fwd, fill: "none", stroke: GROUP_COLORS[g], "stroke-width": 1.5, "stroke-linejoin": "round" }, s);
      base = topLine;
    });
    EVENTS.forEach(function (e, i) {
      var x = X(T(e.day));
      el("line", { x1: x, x2: x, y1: m.t - 8, y2: h - m.b, stroke: FOG, "stroke-opacity": .35 }, s);
      text(s, i === 1 ? x - 8 : x + 8, m.t - 12, wide ? e.label : e.label.slice(0, 6), { fill: FOG3, "text-anchor": i === 1 ? "end" : "start" });
    });
    var last = days[days.length - 1];
    if (wide) {
      text(s, w - m.r + 12, Y(last.float_usd) + 2, usd(last.float_usd), { fill: FOG, "font-size": 17, "font-weight": 600, style: "font-family:var(--sans)" });
      text(s, w - m.r + 12, Y(last.float_usd) + 20, "all groups", { fill: FOG3 });
    }
    var cross = el("line", { y1: m.t - 4, y2: h - m.b, stroke: FOG, "stroke-opacity": .6, visibility: "hidden" }, s);
    hover(s, function (ev, x) {
      var d = days[nearest(days, x, function (q) { return X(T(q.day)); })], px = X(T(d.day));
      cross.setAttribute("x1", px); cross.setAttribute("x2", px); cross.setAttribute("visibility", "visible");
      showTip(ev, dayLong(d.day) + "  block " + d.height, G.map(function (g, i) { return { name: g, value: usd(d.groups[i]), color: GROUP_COLORS[g] }; }).reverse(),
        { name: "Float", value: usd(d.float_usd) });
    }, function () { cross.setAttribute("visibility", "hidden"); });

    var legend = document.getElementById("legend-stack");
    legend.textContent = "";
    G.forEach(function (g) {
      var li = html("li"), key = html("i", "key");
      key.style.background = GROUP_COLORS[g];
      li.appendChild(key); li.appendChild(document.createTextNode(g));
      legend.appendChild(li);
    });
  }

  // ---------- 3. change per day ----------
  function chartLumps() {
    var box = document.getElementById("chart-lumps");
    box.textContent = "";
    var days = W.days, moves = [];
    for (var i = 1; i < days.length; i++) moves.push({ day: days[i - 1].day, v: days[i].float_usd - days[i - 1].float_usd, i: i });
    var ranked = moves.slice().sort(function (a, b) { return b.v - a.v; }), topSet = {};
    ranked.slice(0, 10).forEach(function (mv) { topSet[mv.i] = true; });
    var w = box.clientWidth, h = Math.round(Math.max(240, Math.min(320, w * 0.5))), m = { l: 0, r: 0, t: 18, b: 26 };
    var up = ranked[0].v, down = -ranked[ranked.length - 1].v, k = (h - m.t - m.b) / (up * 1.12 + down * 1.12), zero = m.t + up * 1.12 * k;
    var t0 = T(days[0].day), t1 = T(days[days.length - 1].day), bw = Math.max(1, (w - m.l - m.r) / moves.length - 1);
    function X(t) { return m.l + (t - t0) / (t1 - t0) * (w - m.l - m.r - bw); }
    var s = el("svg", { viewBox: "0 0 " + w + " " + h, width: w, height: h }, box);
    [10e6, -10e6].forEach(function (v) {
      el("line", { x1: m.l, x2: w - m.r, y1: zero - v * k, y2: zero - v * k, stroke: FOG, "stroke-opacity": .1 }, s);
      text(s, m.l, zero - v * k - 6, (v > 0 ? "+" : "-") + "$10M", { fill: FOG3 });
    });
    monthTicks(t0, t1).forEach(function (mt) { text(s, X(mt.t), h - 8, mt.label, { fill: FOG3, "text-anchor": "middle" }); });
    moves.forEach(function (mv) {
      var y = mv.v >= 0 ? zero - mv.v * k : zero, hh = Math.max(.6, Math.abs(mv.v) * k);
      var hot = topSet[mv.i], bwid = bw;
      el("rect", { x: X(T(mv.day)) - (bwid - bw) / 2, y: y, width: bwid, height: hh, fill: hot ? ACCENT : FOG3, "fill-opacity": hot ? 1 : .5 }, s);
    });
    el("line", { x1: m.l, x2: w - m.r, y1: zero, y2: zero, stroke: FOG, "stroke-opacity": .35 }, s);
    var best = ranked[0], worst = ranked[ranked.length - 1];
    text(s, X(T(best.day)) - 8, zero - best.v * k + 4, "+" + usd(best.v).slice(0) + "  " + dayShort(best.day), { fill: FOG, "text-anchor": "end" });
    var wx = X(T(worst.day)), right = wx > w * 0.6;
    text(s, right ? wx - 8 : wx + bw + 8, zero - worst.v * k, usd(worst.v) + "  " + dayShort(worst.day), { fill: FOG, "text-anchor": right ? "end" : "start" });
    var cross = el("line", { y1: m.t, y2: h - m.b, stroke: FOG, "stroke-opacity": .5, visibility: "hidden" }, s);
    hover(s, function (ev, x) {
      var mv = moves[nearest(moves, x, function (q) { return X(T(q.day)) + bw / 2; })], px = X(T(mv.day)) + bw / 2;
      cross.setAttribute("x1", px); cross.setAttribute("x2", px); cross.setAttribute("visibility", "visible");
      showTip(ev, "During " + dayLong(mv.day), [{ name: topSet[mv.i] ? "Change (one of the ten best)" : "Change", value: (mv.v >= 0 ? "+" : "") + usd(mv.v), color: topSet[mv.i] ? ACCENT : FOG3 }]);
    }, function () { cross.setAttribute("visibility", "hidden"); });
  }

  // ---------- 4. the weeks around the switch ----------
  function chartSwitch() {
    var box = document.getElementById("chart-switch");
    box.textContent = "";
    var days = W.days.filter(function (d) { return d.day >= "2026-10-13"; });
    var w = box.clientWidth, h = Math.round(Math.max(240, Math.min(320, w * 0.5))), m = { l: 0, r: 70, t: 26, b: 26 };
    var max = Math.max.apply(null, days.map(function (d) { return d.float_usd; })), step = niceStep(max, 3), top = Math.ceil(max * 1.05 / step) * step;
    var t0 = T(days[0].day), t1 = T(days[days.length - 1].day);
    function X(t) { return m.l + (t - t0) / (t1 - t0) * (w - m.l - m.r); }
    function Y(v) { return m.t + (1 - v / top) * (h - m.t - m.b); }
    var s = el("svg", { viewBox: "0 0 " + w + " " + h, width: w, height: h }, box);
    for (var v = 0; v <= top; v += step) {
      el("line", { x1: m.l, x2: w - m.r, y1: Y(v), y2: Y(v), stroke: FOG, "stroke-opacity": v ? .1 : .3 }, s);
      if (v) text(s, m.l, Y(v) - 6, axisUsd(v), { fill: FOG3 });
    }
    days.forEach(function (d) { if (+d.day.slice(8, 10) % 7 === 6 || d.day === days[0].day) text(s, X(T(d.day)), h - 8, dayShort(d.day), { fill: FOG3, "text-anchor": d.day === days[0].day ? "start" : "middle" }); });
    var line = days.map(function (d, i) { return (i ? "L" : "M") + X(T(d.day)).toFixed(1) + "," + Y(d.float_usd).toFixed(1); }).join("");
    el("path", { d: line + "L" + X(t1) + "," + Y(0) + "L" + X(t0) + "," + Y(0) + "Z", fill: ACCENT, "fill-opacity": .1 }, s);
    el("path", { d: line, fill: "none", stroke: ACCENT, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }, s);
    var sx = X(T(W.events.all_private));
    el("line", { x1: sx, x2: sx, y1: m.t - 8, y2: h - m.b, stroke: FOG, "stroke-opacity": .45 }, s);
    text(s, sx + 8, m.t - 12, w > 420 ? "27 Oct  the switch" : "27 Oct", { fill: FOG3 });
    var last = days[days.length - 1];
    el("circle", { cx: X(t1), cy: Y(last.float_usd), r: 4.5, fill: ACCENT, stroke: DEEP, "stroke-width": 2 }, s);
    text(s, X(t1) + 12, Y(last.float_usd) + 5, usd(last.float_usd), { fill: FOG, "font-size": 15, "font-weight": 600, style: "font-family:var(--sans)" });
    var cross = el("g", { visibility: "hidden" }, s), cl = el("line", { y1: m.t, y2: h - m.b, stroke: FOG, "stroke-opacity": .5 }, cross),
      cd = el("circle", { r: 4.5, fill: ACCENT, stroke: DEEP, "stroke-width": 2 }, cross);
    hover(s, function (ev, x) {
      var d = days[nearest(days, x, function (q) { return X(T(q.day)); })], px = X(T(d.day));
      cross.setAttribute("visibility", "visible"); cl.setAttribute("x1", px); cl.setAttribute("x2", px); cd.setAttribute("cx", px); cd.setAttribute("cy", Y(d.float_usd));
      showTip(ev, dayLong(d.day), [{ name: "Float", value: usd(d.float_usd), color: ACCENT }]);
    }, function () { cross.setAttribute("visibility", "hidden"); });
  }

  // ---------- the float with and without NEAR's own token, around the reward programme ----------
  function chartReward() {
    var box = document.getElementById("chart-reward");
    if (!box) return;
    box.textContent = "";
    var days = W.days, ni = W.groups.indexOf("NEAR"), w = box.clientWidth, wide = w > 700, h = Math.round(Math.max(280, Math.min(400, w * 0.34)));
    var m = { l: 0, r: wide ? 96 : 0, t: 30, b: 28 }, t0 = T(days[0].day), t1 = T(days[days.length - 1].day);
    var max = Math.max.apply(null, days.map(function (d) { return Math.max(d.ex_near_usd, d.groups[ni]); })), step = niceStep(max, 3), top = Math.ceil(max * 1.05 / step) * step;
    function X(t) { return m.l + (t - t0) / (t1 - t0) * (w - m.l - m.r); }
    function Y(v) { return m.t + (1 - v / top) * (h - m.t - m.b); }
    var s = el("svg", { viewBox: "0 0 " + w + " " + h, width: w, height: h }, box);
    for (var v = 0; v <= top; v += step) {
      el("line", { x1: m.l, x2: w - m.r, y1: Y(v), y2: Y(v), stroke: FOG, "stroke-opacity": v ? .1 : .3 }, s);
      if (v) text(s, m.l, Y(v) - 6, axisUsd(v), { fill: FOG3 });
    }
    monthTicks(t0, t1).forEach(function (mt) { text(s, X(mt.t), h - 8, mt.label, { fill: FOG3, "text-anchor": "middle" }); });
    [{ day: W.events.reward_announced, label: "11 Jun  reward announced" }, { day: W.events.reward_trigger, label: "17 Sep  snapshot triggered" }].forEach(function (e, i) {
      var x = X(T(e.day));
      el("line", { x1: x, x2: x, y1: m.t - 10, y2: h - m.b, stroke: FOG, "stroke-opacity": .4 }, s);
      text(s, i ? x - 8 : x + 8, m.t - 14, wide ? e.label : e.label.slice(0, 6), { fill: FOG3, "text-anchor": i ? "end" : "start" });
    });
    function line(get, color) {
      var d = days.map(function (q, i) { return (i ? "L" : "M") + X(T(q.day)).toFixed(1) + "," + Y(get(q)).toFixed(1); }).join("");
      el("path", { d: d, fill: "none", stroke: color, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }, s);
    }
    line(function (q) { return q.groups[ni]; }, ACCENT);
    line(function (q) { return q.ex_near_usd; }, "#AAB4B9");
    var last = days[days.length - 1];
    if (wide) {
      text(s, w - m.r + 12, Y(last.ex_near_usd) + 5, usd(last.ex_near_usd), { fill: FOG, "font-size": 15, "font-weight": 600, style: "font-family:var(--sans)" });
      text(s, w - m.r + 12, Y(last.groups[ni]) + 5, usd(last.groups[ni]), { fill: FOG, "font-size": 15, "font-weight": 600, style: "font-family:var(--sans)" });
    }
    var cross = el("line", { y1: m.t, y2: h - m.b, stroke: FOG, "stroke-opacity": .5, visibility: "hidden" }, s);
    hover(s, function (ev, x) {
      var d = days[nearest(days, x, function (q) { return X(T(q.day)); })], px = X(T(d.day));
      cross.setAttribute("x1", px); cross.setAttribute("x2", px); cross.setAttribute("visibility", "visible");
      showTip(ev, dayLong(d.day), [{ name: "Without NEAR's token", value: usd(d.ex_near_usd), color: "#AAB4B9" }, { name: "NEAR's own token", value: usd(d.groups[ni]), color: ACCENT }],
        { name: "Float", value: usd(d.float_usd) });
    }, function () { cross.setAttribute("visibility", "hidden"); });
  }

  // ---------- one token around the October shortfall: held against credited ----------
  var WARN = "#FFB23E";
  function clock(ms) { var d = new Date(ms); return d.getUTCDate() + " " + MONTHS[d.getUTCMonth()] + " " + ("0" + d.getUTCHours()).slice(-2) + ":" + ("0" + d.getUTCMinutes()).slice(-2) + ":" + ("0" + d.getUTCSeconds()).slice(-2); }
  function stamp(s) { return Date.parse(s.replace(" ", "T") + "Z"); }

  // one mark per audited reading: blue when every token was whole, amber and taller when one was short
  function chartAudit() {
    var box = document.getElementById("chart-audit"), A = W.audit;
    if (!box || !A || !A.days.length) return;
    box.textContent = "";
    var days = A.days, w = box.clientWidth, h = 132, m = { l: 0, r: 0, t: 34, b: 26 };
    var t0 = T(W.first_day), t1 = T(W.last_day);
    function X(t) { return m.l + 6 + (t - t0) / (t1 - t0) * (w - m.l - m.r - 12); }
    var s = el("svg", { viewBox: "0 0 " + w + " " + h, width: w, height: h }, box);
    el("line", { x1: m.l, x2: w - m.r, y1: h - m.b, y2: h - m.b, stroke: FOG, "stroke-opacity": .3 }, s);
    monthTicks(t0, t1).forEach(function (mt) { text(s, X(mt.t), h - 8, mt.label, { fill: FOG3, "text-anchor": "middle" }); });
    var bw = Math.max(1.5, Math.min(4, (w - 12) / ((t1 - t0) / 864e5) - 1));
    days.forEach(function (d) {
      var x = X(T(d.day)), bad = d.short > 0;
      el("rect", { x: x - bw / 2, y: bad ? m.t - 14 : m.t + 14, width: bw, height: (h - m.b) - (bad ? m.t - 14 : m.t + 14), fill: bad ? WARN : ACCENT, rx: 1 }, s);
    });
    var bads = days.filter(function (d) { return d.short > 0; });
    if (bads.length) {
      var bx = X(T(bads[0].day)), label = "hole: " + bads.map(function (d) { return dayShort(d.day) + " " + usd(d.short_usd); }).join(", ");
      if (w < 640) label = bads.length + " readings with a hole";
      text(s, bx - 10, m.t - 2, label, { fill: FOG, "text-anchor": "end" });
    }
    var cross = el("line", { y1: 8, y2: h - m.b, stroke: FOG, "stroke-opacity": .5, visibility: "hidden" }, s);
    hover(s, function (ev, x) {
      var d = days[nearest(days, x, function (q) { return X(T(q.day)); })], px = X(T(d.day));
      cross.setAttribute("x1", px); cross.setAttribute("x2", px); cross.setAttribute("visibility", "visible");
      showTip(ev, dayLong(d.day) + ", 00:00 UTC", [{ name: "Tokens audited", value: String(d.checked) }, { name: "Held by NEAR Intents", value: usd(d.held_usd) }],
        d.short ? { name: "Hole", value: usd(d.short_usd) } : { name: "Short", value: "none" });
    }, function () { cross.setAttribute("visibility", "hidden"); });
  }

  // the hole, block by block, on a log scale: ten dollars to millions on one chart
  function chartExploit() {
    var box = document.getElementById("chart-exploit"), E = W.exploit;
    if (!box || !E || E.steps.length < 3) return;
    box.textContent = "";
    // leave out changes that reversed within a few seconds; they stay in the data
    var raw = E.steps, pts = [], i = 0;
    while (i < raw.length) {
      var prev = pts.length ? pts[pts.length - 1].hole : 0;
      if (i + 1 < raw.length && raw[i + 1].t - raw[i].t < 8000 && raw[i + 1].hole === prev) { i += 2; continue; }
      pts.push(raw[i]); i += 1;
    }
    var open = pts.filter(function (p) { return p.hole > 0; });
    if (!open.length) return;
    var first = open[0], peak = open.reduce(function (a, b) { return b.hole > a.hole ? b : a; });
    var shut = pts.filter(function (p) { return p.t > peak.t && p.hole <= 0; })[0];
    var paid = stamp(E.quoted.first_payout_utc), lastPaid = stamp(E.quoted.last_payout_utc), fix = stamp(E.quoted.upgrade_utc);
    var w = box.clientWidth, narrow = w < 640, h = Math.round(Math.max(300, Math.min(420, w * 0.4))), m = { l: 0, r: 0, t: narrow ? 64 : 48, b: 28 };
    var t0 = first.t - 6 * 36e5, t1 = (shut ? shut.t : fix) + 5 * 36e5;
    var lo = 0, hi = 7;   // powers of ten: $1 to $10M
    function X(t) { return m.l + 50 + (t - t0) / (t1 - t0) * (w - m.l - m.r - 62); }
    function Y(v) { var p = v <= 1 ? 0 : Math.log(v) / Math.LN10; return m.t + (1 - (p - lo) / (hi - lo)) * (h - m.t - m.b); }
    var s = el("svg", { viewBox: "0 0 " + w + " " + h, width: w, height: h }, box);
    [[1, "0"], [10, "$10"], [1e3, "$1K"], [1e5, "$100K"], [1e7, "$10M"]].forEach(function (g) {
      el("line", { x1: m.l, x2: w - m.r, y1: Y(g[0]), y2: Y(g[0]), stroke: FOG, "stroke-opacity": g[0] === 1 ? .3 : .1 }, s);
      text(s, m.l, Y(g[0]) - 6, g[1], { fill: FOG3 });
    });
    for (var day = Math.ceil(t0 / 864e5) * 864e5; day < t1; day += 864e5) {
      var d = new Date(day);
      el("line", { x1: X(day), x2: X(day), y1: h - m.b, y2: h - m.b + 5, stroke: FOG3 }, s);
      text(s, X(day), h - 8, d.getUTCDate() + " " + MONTHS[d.getUTCMonth()], { fill: FOG3, "text-anchor": X(day) > w - 26 ? "end" : "middle" });
    }
    // the stretch in which the hole was visible and nothing had been paid out yet
    el("rect", { x: X(first.t), y: m.t, width: X(paid) - X(first.t), height: h - m.t - m.b, fill: WARN, "fill-opacity": .08 }, s);
    // the line
    var path = "M" + X(t0).toFixed(1) + "," + Y(0).toFixed(1), y = Y(0);
    pts.forEach(function (p) {
      if (p.t < t0 || p.t > t1) return;
      path += "L" + X(p.t).toFixed(1) + "," + y.toFixed(1); y = Y(Math.max(p.hole, 0)); path += "L" + X(p.t).toFixed(1) + "," + y.toFixed(1);
    });
    path += "L" + X(t1).toFixed(1) + "," + y.toFixed(1);
    el("path", { d: path, fill: "none", stroke: WARN, "stroke-width": 2, "stroke-linejoin": "round" }, s);
    // quoted times
    function mark(t, label, row, anchor) {
      el("line", { x1: X(t), x2: X(t), y1: m.t - 6, y2: h - m.b, stroke: FOG, "stroke-opacity": .45, "stroke-dasharray": "3 4" }, s);
      text(s, X(t) + (anchor === "end" ? -6 : 6), 14 + row * 16, label, { fill: FOG2(), "text-anchor": anchor || "start", "class": "ann" });
    }
    function FOG2() { return "#AAB4B9"; }
    mark(paid, narrow ? "first payout" : "first payout, " + clock(paid).slice(-8) + " (CertiK)", 0, "end");
    mark(fix, narrow ? "upgrade" : "contract upgrade, " + clock(fix).slice(-8) + " (CertiK)", 0, "end");
    // our own marks
    el("circle", { cx: X(first.t), cy: Y(first.hole), r: 4, fill: WARN, stroke: DEEP, "stroke-width": 2 }, s);
    text(s, X(first.t) + 8, Y(first.hole) + 16, "$" + first.hole + (narrow ? "" : ", " + clock(first.t)), { fill: FOG });
    el("circle", { cx: X(peak.t), cy: Y(peak.hole), r: 4, fill: WARN, stroke: DEEP, "stroke-width": 2 }, s);
    text(s, X(peak.t) + 8, Y(peak.hole) - 8, usd(peak.hole) + (narrow ? "" : " at its largest"), { fill: FOG });
    if (shut) {
      el("circle", { cx: X(shut.t), cy: Y(0), r: 4, fill: ACCENT, stroke: DEEP, "stroke-width": 2 }, s);
      text(s, X(shut.t) - 8, Y(0) - 10, narrow ? "whole" : "whole again, " + clock(shut.t).slice(-8), { fill: FOG, "text-anchor": "end" });
    }
    if (!narrow) {
      var mid = (X(first.t) + X(paid)) / 2, by = m.t + 14;
      text(s, mid, by, K.A8 ? "in the books " + K.A8.shown + " before the first payout" : "", { fill: WARN, "text-anchor": "middle" });
    }
    var cross = el("line", { y1: m.t, y2: h - m.b, stroke: FOG, "stroke-opacity": .5, visibility: "hidden" }, s);
    hover(s, function (ev, x) {
      var k = 0;
      for (var j = 0; j < raw.length; j++) if (X(raw[j].t) <= x) k = j;
      var p = raw[k], px = Math.max(X(t0), Math.min(X(t1), x));
      cross.setAttribute("x1", px); cross.setAttribute("x2", px); cross.setAttribute("visibility", "visible");
      showTip(ev, "from " + clock(p.t) + " UTC, block " + p.height.toLocaleString("en-US"),
        [{ name: "Credited to everyone", value: p.credited.toLocaleString("en-US") }, { name: "Held by NEAR Intents", value: p.held.toLocaleString("en-US") }],
        { name: p.hole > 0 ? "Hole" : "Hole", value: p.hole > 0 ? p.hole.toLocaleString("en-US") : "none" });
    }, function () { cross.setAttribute("visibility", "hidden"); });
  }

  // ---------- the same audit, live, in the reader's browser ----------
  var NODES = ["https://rpc.mainnet.fastnear.com", "https://free.rpc.fastnear.com", "https://rpc.mainnet.near.org"];
  function rpc(method, params, n) {
    n = n || 0;
    return fetch(NODES[n % NODES.length], { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: method, params: params }) })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(function (j) { if (j.error) throw new Error(JSON.stringify(j.error).slice(0, 120)); return j.result; })
      .catch(function (e) { if (n >= 5) throw e; return new Promise(function (ok) { setTimeout(ok, 350 * (n + 1)); }).then(function () { return rpc(method, params, n + 1); }); });
  }
  function view(height, contract, method, args) {
    return rpc("query", { request_type: "call_function", block_id: height, account_id: contract, method_name: method, args_base64: btoa(JSON.stringify(args)) })
      .then(function (res) { return JSON.parse(String.fromCharCode.apply(null, res.result)); });
  }
  function heldCall(height, id) {
    var k = id.indexOf(":"), kind = id.slice(0, k), rest = id.slice(k + 1);
    if (kind === "nep141") return view(height, rest, "ft_balance_of", { account_id: "intents.near" });
    var c = rest.indexOf(":");
    return view(height, rest.slice(0, c), "mt_balance_of", { account_id: "intents.near", token_id: rest.slice(c + 1) });
  }
  function units(v, decimals) {   // whole tokens from base units, without losing digits
    var b = BigInt(v), u = BigInt(10) ** BigInt(decimals), whole = b / u, frac = Number(b % u) / Number(u);
    var v = Number(whole) + frac;
    return v.toLocaleString("en-US", { maximumFractionDigits: v !== 0 && v < 1 ? 8 : 2 });
  }
  function auditNow() {
    var A = W.audit, btn = document.getElementById("audit-run"), status = document.getElementById("audit-status");
    if (!A || !btn) return;
    btn.disabled = true; status.textContent = "Asking for the latest final block...";
    var height, when, credited, rows = [];
    rpc("block", { finality: "final" }).then(function (b) {
      height = b.header.height; when = Math.round(b.header.timestamp / 1e6);
      status.textContent = "Block " + height.toLocaleString("en-US") + ": asking intents.near what it has credited...";
      return view(height, "intents.near", "mt_batch_supply", { token_ids: A.tracked.map(function (t) { return t.id; }) });
    }).then(function (c) {
      credited = c;
      var done = 0, chain = Promise.resolve();
      A.tracked.forEach(function (t, i) {
        chain = chain.then(function () { return heldCall(height, t.id).then(function (hv) { return String(hv); }, function () { return null; }); })
          .then(function (hv) { rows[i] = hv; done += 1; status.textContent = "Block " + height.toLocaleString("en-US") + ": asking each token what NEAR Intents holds, " + done + " of " + A.tracked.length + "..."; });
      });
      return chain;
    }).then(function () {
      var short = 0, unknown = 0, total = 0, tbl = document.getElementById("audit-table");
      tbl.textContent = "";
      var head = document.createElement("thead"), tr = document.createElement("tr");
      [["Token", ""], ["", ""], ["Chain", ""], ["Credited", "num"], ["Held", "num"], ["Held minus credited", "num"]].forEach(function (c) { var th = html("th", c[1], c[0]); tr.appendChild(th); });
      head.appendChild(tr); tbl.appendChild(head);
      var body = document.createElement("tbody");
      A.tracked.forEach(function (t, i) {
        var c = credited && credited[i] != null ? BigInt(credited[i]) : null, hv = rows[i] != null ? BigInt(rows[i]) : null, r = document.createElement("tr"), st;
        if (c === null || hv === null) { st = "unknown"; unknown += 1; }
        else if (c > hv) { st = "short"; short += 1; }
        else st = c === hv ? "equal" : "surplus";
        if (hv !== null && t.price) total += Number(hv) / Math.pow(10, t.decimals) * t.price;
        var cell = html("td"), tag = html("span", "st " + st, st === "short" ? "SHORT" : st === "unknown" ? "NOT READ" : "WHOLE"); cell.appendChild(tag);
        r.appendChild(html("td", null, t.symbol)); r.appendChild(cell); r.appendChild(html("td", "chain", t.chain));
        r.appendChild(html("td", "num", c === null ? "not read" : units(c, t.decimals)));
        r.appendChild(html("td", "num", hv === null ? "not read" : units(hv, t.decimals)));
        r.appendChild(html("td", "num", c === null || hv === null ? "" : (hv >= c ? "+" + units(hv - c, t.decimals) : "-" + units(c - hv, t.decimals))));
        body.appendChild(r);
      });
      tbl.appendChild(body);
      var v = document.getElementById("audit-verdict"), n = A.tracked.length - unknown;
      v.className = "verdict" + (short ? " short" : "");
      v.textContent = short ? short + " of " + n + " tokens are short at this block." : (n - short) + " of " + n + " tokens whole. " + usd(total) + " held, nothing credited above it.";
      var sm = html("small", null, "Block " + height.toLocaleString("en-US") + ", " + clock(when) + " UTC, read just now by your browser" + (unknown ? ". " + unknown + " could not be read and are not counted as whole." : "."));
      v.appendChild(sm);
      document.getElementById("audit-result").hidden = false;
      status.textContent = "Done. Run it again for a newer block.";
      btn.disabled = false; btn.textContent = "Audit the latest block again";
    }).catch(function (e) {
      status.textContent = "The public node did not answer (" + String(e.message || e).slice(0, 80) + "). Try again, or run: python3 -m pipeline.audit --now";
      btn.disabled = false;
    });
  }

  function barRow(name, small, share, sub, title) {
    var row = html("div", "row"), n = html("div", "name", name);
    if (small) n.appendChild(html("small", null, small));
    var track = html("div", "track"), fill = html("div", "fill");
    fill.style.width = Math.min(100, share) + "%"; track.appendChild(fill);
    var val = html("div", "val", share.toFixed(1) + "%");
    val.appendChild(html("small", null, sub));
    row.title = title;
    row.appendChild(n); row.appendChild(track); row.appendChild(val);
    return row;
  }
  function barsTokens() {
    var groups = document.getElementById("bars-groups"), box = document.getElementById("bars-tokens");
    groups.textContent = ""; box.textContent = "";
    W.pin.groups.filter(function (g) { return g.share != null; }).sort(function (a, b) { return b.share - a.share; }).forEach(function (g) {
      groups.appendChild(barRow(g.name === "BTC" ? "Bitcoin" : g.name, null, g.share, usd(g.private_usd) + " of " + usd(g.held_usd),
        g.name + ": " + g.share.toFixed(1) + "% of what intents.near holds is private (" + usd(g.private_usd) + " of " + usd(g.held_usd) + ")"));
    });
    W.tokens.filter(function (t) { return t.share_now != null; }).forEach(function (t) {
      box.appendChild(barRow(t.symbol.replace("(DEPRECATED)", " (old id)"), "on " + t.chain, t.share_now, usd(t.private_usd) + " of " + usd(t.held_usd),
        t.symbol + " on " + t.chain + ": " + t.share_now.toFixed(1) + "% of what intents.near holds is private"));
    });
  }

  // ---------- readings ----------
  function num(id) { return parseFloat(K[id].shown.replace(/[^0-9.\-]/g, "")); }
  function meters() {
    var box = document.getElementById("meters");
    box.textContent = "";
    [
      { id: "R1", name: "Private float", now: K.C1.shown, v: num("C1"), max: 250, from: 200, to: 250, tick: 200, tickLabel: "$200M", rule: ["Holds at ", "$200M or more", ". Breaks below the pinned day's level."] },
      { id: "R2", name: "Ten best days as a share of the float", now: K.C17.shown, v: num("C17"), max: 100, from: 0, to: 45, tick: 45, tickLabel: "45%", rule: ["Holds ", "below 45%", ": new money arrives on many days. Breaks if it is still at the pinned day's level."] },
      { id: "R3", name: "Private share, the 20 tracked tokens", now: K.C23 ? K.C23.shown : "n/a", v: K.C23 ? num("C23") : 0, max: 100, from: 50, to: 100, tick: 50, tickLabel: "50%", rule: ["Holds at ", "50% or more", ". Breaks below 40%: money is moving back to the public side."] },
      { id: "R4", name: "Revenue reaching NEAR's wallets, as a share of new supply", now: K.V4.shown, v: num("V4"), max: 60, from: 25, to: 60, tick: 25, tickLabel: "25%", rule: ["Holds at ", "25% or more", ". Breaks below 10%. Counted NEAR against NEAR. Uses a quoted revenue figure, so it is scored by hand."] },
      { id: "R5", name: "Float without NEAR's own token", now: K.P4.shown, v: num("P4"), max: 180, from: 130, to: 180, tick: 130, tickLabel: "$130M", rule: ["Holds at ", "$130M or more", ". Breaks below the pinned day's level."] }
    ].forEach(function (r) {
      var mEl = html("div", "meter"), head = html("div", "head"), name = html("div", "name"), tag = html("small", null, r.id);
      name.appendChild(tag); name.appendChild(document.createTextNode(r.name));
      head.appendChild(name); head.appendChild(html("div", "now", r.now));
      var track = html("div", "track"), zone = html("div", "zone"), tick = html("div", "tick"), dot = html("div", "dot");
      zone.style.left = r.from / r.max * 100 + "%"; zone.style.width = (r.to - r.from) / r.max * 100 + "%";
      tick.style.left = r.tick / r.max * 100 + "%"; tick.appendChild(html("span", null, r.tickLabel));
      dot.style.left = Math.min(100, r.v / r.max * 100) + "%";
      track.appendChild(zone); track.appendChild(tick); track.appendChild(dot);
      var rule = html("p", "rule");
      rule.appendChild(document.createTextNode(r.rule[0])); rule.appendChild(html("b", null, r.rule[1])); rule.appendChild(document.createTextNode(r.rule[2]));
      mEl.setAttribute("role", "group"); mEl.setAttribute("aria-label", r.name + ": now " + r.now + ". " + r.rule.join(""));
      mEl.appendChild(head); mEl.appendChild(track); mEl.appendChild(rule);
      box.appendChild(mEl);
    });
  }

  function forward() {
    var F = window.WATERLINE_FORWARD, box = document.getElementById("forward");
    if (!F || !box) return;
    box.textContent = "";
    var near = F.tests.filter(function (t) { return t.id.charAt(0) === "E" || t.id.charAt(0) === "F"; });
    var G = window.WATERLINE_FORWARD_AUDIT;   // the audit's own tests come first: they test the claim the page leads with
    (G ? G.tests : []).concat(near).forEach(function (t) {
      var item = html("div", "item");
      item.appendChild(html("span", "id", t.id));
      item.appendChild(html("span", "txt", t.text + (t.value ? " Result: " + t.value + "." : " Scored on the " + dayLong(t.due) + " reading.")));
      var label = { PENDING: "Pending", PASS: "Passed", FAIL: "Failed", UNKNOWN: "Unknown" }[t.status] || t.status;
      item.appendChild(html("span", "st " + t.status, label));
      box.appendChild(item);
    });
  }

  function links() {
    var box = document.getElementById("links");
    box.textContent = "";
    if (!REPO) return;
    [["Repository", REPO], ["The full thesis", REPO + "/blob/main/THESIS.md"], ["Every constant and its source", REPO + "/blob/main/docs/SOURCES.md"], ["Raw readings", REPO + "/tree/main/data"]]
      .forEach(function (l) { var a = html("a", null, l[0]); a.href = l[1]; box.appendChild(a); });
  }

  function charts() { chartAudit(); chartExploit(); chartWaterline(); chartStack(); chartReward(); chartLumps(); chartSwitch(); }
  var runBtn = document.getElementById("audit-run");
  if (runBtn) runBtn.addEventListener("click", auditNow);
  fillClaims(); barsTokens(); meters(); forward(); links(); charts();
  var timer;
  addEventListener("resize", function () { clearTimeout(timer); timer = setTimeout(charts, 150); });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(charts);
})();
