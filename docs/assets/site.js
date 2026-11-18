(function () {
  "use strict";
  var AR = window.LANG === "ar", C = window.C || {};
  var nf = new Intl.NumberFormat("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  function nm(i) { return C[i] ? (AR ? C[i].ar : C[i].en) : i; }
  function usd(v) { return v == null ? "–" : "$" + (v >= 100 ? Math.round(v).toLocaleString("en-US") : nf.format(v)); }
  function pc(v) { return v == null ? "–" : (v < 10 ? v.toFixed(1) : Math.round(v)) + "%"; }
  function x(m) { return m.toFixed(1) + "×"; }
  function bdi(s) { return '<bdi dir="ltr">' + s + "</bdi>"; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  /* ---------- hero sentence ---------- */
  var sel = document.getElementById("country");
  function lede(iso) {
    var c = C[iso], L = document.getElementById("lede"), L2 = document.getElementById("lede2"),
      S = document.getElementById("stamp");
    if (!c || !L) return;
    var n = esc(nm(iso)), a = "", b = "", stamp = null, lab = "";
    if (c.fp != null) {
      a = AR
        ? "في " + n + "، متوسط باقة الألياف (≈" + bdi(String(Math.round(c.fd || 0))) + " ميغابت) يكلّف " + bdi("<b>" + usd(c.fp) + "</b>") + " شهرياً، أي " + bdi("<b>" + pc(c.fpct) + "</b>") + " من متوسط الدخل الشهري."
        : "In " + n + ", the average fiber plan (≈" + Math.round(c.fd || 0) + " Mbps) costs <b>" + usd(c.fp) + "</b> a month: <b>" + pc(c.fpct) + "</b> of an average monthly income.";
      if (c.fmult != null) {
        stamp = c.fmult;
        lab = AR ? "سعر الألياف مقابل وسيط " + c.fpeer_n + " دولة دخلها مشابه|" + usd(c.fpeer_med)
                 : "fiber price vs the median of " + c.fpeer_n + " similar-income countries|" + usd(c.fpeer_med);
      }
    } else {
      a = AR ? "لم نجد في " + n + " سعر ألياف منشوراً يمكن التحقق منه."
             : "No published, verifiable fiber price was found for " + n + ".";
    }
    if (c.mgb != null) {
      b = AR
        ? "الجوال: الغيغابايت بـ" + bdi(usd(c.mgb)) + " (باقة 10 غيغابايت ≈ " + bdi(usd(c.m10)) + "، أي " + bdi(pc(c.mpct)) + " من الدخل الشهري)" + (c.mmult != null ? "، و" + bdi(x(c.mmult)) + " وسيط الدول ذات الدخل المشابه." : ".")
        : "Mobile: " + usd(c.mgb) + " per GB (10 GB ≈ " + usd(c.m10) + ", " + pc(c.mpct) + " of monthly income)" + (c.mmult != null ? ", " + x(c.mmult) + " its peers’ median." : ".");
      if (stamp == null && c.mmult != null) {
        stamp = c.mmult;
        lab = AR ? "سعر الغيغابايت مقارنةً بوسيط " + c.mpeer_n + " دولة دخلها مشابه" : "price per GB vs the median of " + c.mpeer_n + " similar-income countries";
      }
    }
    if (c.gni_note === "est" || c.gni_note === "gdp-fallback")
      b += AR ? " (الدخل تقديري.)" : " (Income is an estimate.)";
    L.innerHTML = a; L2.innerHTML = b;
    if (stamp != null) {
      S.hidden = false;
      document.getElementById("stampnum").textContent = x(stamp);
      var parts = lab.split("|"), sl = document.getElementById("stamplab");
      sl.textContent = parts[0];
      if (parts[1]) { var m = document.createElement("bdi"); m.dir = "ltr"; m.className = "med"; m.textContent = parts[1]; sl.appendChild(document.createElement("br")); sl.appendChild(m); }
      S.classList.toggle("fair", stamp < 1);
      S.classList.remove("thump"); void S.offsetWidth; S.classList.add("thump");
    } else S.hidden = true;
    mark(iso);
  }

  /* ---------- chart selection + tooltips ---------- */
  var NS = "http://www.w3.org/2000/svg";
  function mark(iso) {
    document.querySelectorAll(".chart").forEach(function (svg) {
      svg.querySelectorAll(".sel").forEach(function (d) { d.classList.remove("sel"); d.setAttribute("r", "5.5"); });
      svg.querySelectorAll(".sel-lab").forEach(function (t) { t.remove(); });
      var d = svg.querySelector('.dot[data-iso="' + iso + '"]');
      if (!d) return;
      d.classList.add("sel"); d.setAttribute("r", "9"); d.parentNode.appendChild(d);
      var t = document.createElementNS(NS, "text");
      t.setAttribute("class", "sel-lab"); t.setAttribute("x", d.getAttribute("cx"));
      t.setAttribute("y", +d.getAttribute("cy") - 14); t.setAttribute("text-anchor", "middle");
      t.textContent = nm(iso); svg.appendChild(t);
    });
  }
  var tip = document.getElementById("tip");
  function tipText(iso, svg) {
    var c = C[iso]; if (!c) return iso;
    var isM = svg && svg.dataset.kind === "m";
    if (isM && c.mgb != null) return nm(iso) + " · " + usd(c.mgb) + (AR ? " / غيغابايت · " : " / GB · ") + pc(c.mpct);
    if (c.fp != null) return nm(iso) + " · " + usd(c.fp) + (AR ? " شهرياً · " : "/mo · ") + pc(c.fpct);
    return nm(iso);
  }
  function show(e, d) {
    tip.textContent = tipText(d.dataset.iso, d.ownerSVGElement); tip.hidden = false;
    var r = d.getBoundingClientRect(), w = tip.offsetWidth;
    tip.style.left = Math.max(8, Math.min(innerWidth - w - 8, r.left + r.width / 2 - w / 2)) + "px";
    tip.style.top = Math.max(8, r.top - tip.offsetHeight - 10) + "px";
  }
  document.addEventListener("pointerover", function (e) { var d = e.target.closest && e.target.closest(".dot"); if (d) show(e, d); });
  document.addEventListener("pointerout", function (e) { if (e.target.closest && e.target.closest(".dot")) tip.hidden = true; });
  document.addEventListener("click", function (e) {
    var d = e.target.closest && e.target.closest(".dot");
    if (!d) { tip.hidden = true; return; }
    show(e, d);
    if (sel && sel.tagName === "SELECT") { sel.value = d.dataset.iso; lede(d.dataset.iso); } else mark(d.dataset.iso);
  });
  window.addEventListener("scroll", function () { tip.hidden = true; }, { passive: true });

  /* ---------- region chips ---------- */
  document.querySelectorAll(".chips").forEach(function (g) {
    var fig = g.nextElementSibling;
    g.addEventListener("click", function (e) {
      var b = e.target.closest(".chip"); if (!b) return;
      g.querySelectorAll(".chip").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
      var r = b.dataset.region;
      fig.querySelectorAll(".dot").forEach(function (d) { d.classList.toggle("dim", !!r && d.dataset.region !== r); });
    });
  });

  /* ---------- sortable tables + search ---------- */
  document.querySelectorAll("table.sortable").forEach(function (tb) {
    var ths = tb.tHead.rows[0].cells;
    Array.prototype.forEach.call(ths, function (th, i) {
      th.tabIndex = 0;
      function go() {
        var dir = th.getAttribute("aria-sort") === "descending" ? "ascending" : "descending";
        Array.prototype.forEach.call(ths, function (h) { h.removeAttribute("aria-sort"); });
        th.setAttribute("aria-sort", dir);
        var body = tb.tBodies[0], rows = Array.prototype.slice.call(body.rows);
        var coll = new Intl.Collator(AR ? "ar" : "en");
        rows.sort(function (a, b) {
          var A = a.cells[i], B = b.cells[i], av = A.dataset.v, bv = B.dataset.v, r;
          if (av !== undefined || bv !== undefined) {
            av = av === "" || av === undefined ? -Infinity : +av; bv = bv === "" || bv === undefined ? -Infinity : +bv; r = av - bv;
          } else r = coll.compare(A.textContent, B.textContent);
          return dir === "ascending" ? r : -r;
        });
        rows.forEach(function (r) { body.appendChild(r); });
      }
      th.addEventListener("click", go);
      th.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); } });
    });
  });
  document.querySelectorAll("input.search").forEach(function (inp) {
    var tb = inp.parentNode.querySelector("table");
    inp.addEventListener("input", function () {
      var q = inp.value.trim().toLowerCase();
      Array.prototype.forEach.call(tb.tBodies[0].rows, function (r) {
        var iso = r.dataset.iso, c = C[iso] || {};
        var hay = (r.textContent + " " + (c.en || "") + " " + iso).toLowerCase();
        r.hidden = q && hay.indexOf(q) < 0;
      });
    });
  });

  if (sel) {
    if (sel.tagName === "SELECT") {
      var h = (location.hash || "").slice(1).toUpperCase();
      if (C[h]) sel.value = h;
      sel.addEventListener("change", function () { history.replaceState(null, "", "#" + sel.value); lede(sel.value); });
    }
    lede(sel.value);
  }
})();
