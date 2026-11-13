/* Waterline dashboard. Plain JavaScript, no framework, no network: it reads data.js and claims.js. */
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
  function chartShort() {
    var box = document.getElementById("chart-short"), C = W.shortfall_case;
    if (!box || !C || C.days.length < 2) return;
    box.textContent = "";
    var days = C.days, w = box.clientWidth, h = Math.round(Math.max(240, Math.min(340, w * 0.3))), m = { l: 0, r: 0, t: 22, b: 26 };
    var max = Math.max.apply(null, days.map(function (d) { return Math.max(d.held, d.credited); })), step = niceStep(max, 4), top = Math.ceil(max * 1.05 / step) * step;
    var t0 = T(days[0].day), t1 = T(days[days.length - 1].day);
    function X(t) { return m.l + 44 + (t - t0) / (t1 - t0) * (w - m.l - m.r - 88); }
    function Y(v) { return m.t + (1 - v / top) * (h - m.t - m.b); }
    function tok(v) { return v >= 1e6 ? (v / 1e6).toFixed(2) + "M" : Math.round(v / 1e3) + "K"; }
    var s = el("svg", { viewBox: "0 0 " + w + " " + h, width: w, height: h }, box);
    for (var v = 0; v <= top; v += step) {
      el("line", { x1: m.l, x2: w - m.r, y1: Y(v), y2: Y(v), stroke: FOG, "stroke-opacity": v ? .1 : .3 }, s);
      if (v) text(s, m.l, Y(v) - 6, tok(v), { fill: FOG3 });
    }
    days.forEach(function (d, i) { if (i % 2 === 0) text(s, X(T(d.day)), h - 8, dayShort(d.day), { fill: FOG3, "text-anchor": "middle" }); });
    // shade the gap wherever less was held than was credited
    for (var i = 1; i < days.length; i++) {
      var a = days[i - 1], b = days[i];
      if (a.held < a.credited || b.held < b.credited) {
        el("path", { d: "M" + X(T(a.day)) + "," + Y(a.credited) + "L" + X(T(b.day)) + "," + Y(b.credited) + "L" + X(T(b.day)) + "," + Y(Math.min(b.held, b.credited)) + "L" + X(T(a.day)) + "," + Y(Math.min(a.held, a.credited)) + "Z", fill: "#FFB23E", "fill-opacity": .22 }, s);
      }
    }
    function line(key, color) {
      el("path", { d: days.map(function (q, k) { return (k ? "L" : "M") + X(T(q.day)).toFixed(1) + "," + Y(q[key]).toFixed(1); }).join(""), fill: "none", stroke: color, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }, s);
      days.forEach(function (q) { el("circle", { cx: X(T(q.day)), cy: Y(q[key]), r: 3.5, fill: color, stroke: DEEP, "stroke-width": 2 }, s); });
    }
    line("credited", ACCENT); line("held", "#AAB4B9");
    var low = days.reduce(function (p, q) { return q.held < p.held ? q : p; });
    text(s, X(T(low.day)) + 10, Y(low.held) - 10, tok(low.held) + " held on " + dayShort(low.day), { fill: FOG });
    var cross = el("line", { y1: m.t, y2: h - m.b, stroke: FOG, "stroke-opacity": .5, visibility: "hidden" }, s);
    hover(s, function (ev, x) {
      var d = days[nearest(days, x, function (q) { return X(T(q.day)); })], px = X(T(d.day));
      cross.setAttribute("x1", px); cross.setAttribute("x2", px); cross.setAttribute("visibility", "visible");
      showTip(ev, dayLong(d.day) + ", 00:00 UTC", [{ name: "Held by NEAR Intents", value: d.held.toLocaleString("en-US"), color: "#AAB4B9" }, { name: "Credited to the private chain", value: d.credited.toLocaleString("en-US"), color: ACCENT }],
        d.held < d.credited ? { name: "Missing", value: (d.credited - d.held).toLocaleString("en-US") } : null);
    }, function () { cross.setAttribute("visibility", "hidden"); });
  }

  // ---------- 5. share by asset group, then token by token ----------
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
      { id: "R5", name: "Float without NEAR's own token", now: K.P4.shown, v: num("P4"), max: 180, from: 130, to: 180, tick: 130, tickLabel: "$130M", rule: ["Holds at ", "$130M or more", ". Breaks below the pinned day's level: the rest was rented too."] },
      { id: "R4", name: "Revenue reaching NEAR's wallets, as a share of new supply", now: K.V4.shown, v: num("V4"), max: 60, from: 25, to: 60, tick: 25, tickLabel: "25%", rule: ["Holds at ", "25% or more", ". Breaks below 10%. Counted NEAR against NEAR. Uses a quoted revenue figure, so it is scored by hand."] }
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
    near.forEach(function (t) {
      var item = html("div", "item");
      item.appendChild(html("span", "id", t.id));
      item.appendChild(html("span", "txt", t.text + (t.value ? " Result: " + t.value + "." : " Scored on the " + dayLong(t.due) + " reading.")));
      item.appendChild(html("span", "st " + t.status, t.status === "PENDING" ? "Pending" : t.status === "PASS" ? "Passed" : "Failed"));
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

  function charts() { chartWaterline(); chartStack(); chartReward(); chartLumps(); chartSwitch(); chartShort(); }
  fillClaims(); barsTokens(); meters(); forward(); links(); charts();
  var timer;
  addEventListener("resize", function () { clearTimeout(timer); timer = setTimeout(charts, 150); });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(charts);
})();
