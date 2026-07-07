/* Spec 09 - camada de apresentacao. Consome somente docs/data/dashboard_data.js,
   gerado por src/dashboard_build.py a partir de outputs validados (Specs 01-08).
   Nenhuma regra de negocio e recalculada aqui; apenas formatacao e agregacao
   visual dos valores ja publicados. Sem dependencias externas (sem CDN). */
"use strict";

(function () {
  const DATA = window.DASHBOARD_DATA;
  const main = document.querySelector("main");
  if (!DATA) {
    const aviso = document.createElement("div");
    aviso.className = "bloco";
    aviso.textContent =
      "Dados do painel não encontrados (docs/data/dashboard_data.js). " +
      "Gere-os com: python src/dashboard_build.py (alvo make dashboard-build).";
    main.prepend(aviso);
    return;
  }

  /* ---------------- helpers de DOM e formato ---------------- */

  function el(tag, attrs, ...children) {
    const node = document.createElement(tag);
    if (attrs) {
      for (const [k, v] of Object.entries(attrs)) {
        if (k === "class") node.className = v;
        else if (k === "dataset") Object.assign(node.dataset, v);
        else node.setAttribute(k, v);
      }
    }
    for (const child of children.flat()) {
      if (child === null || child === undefined) continue;
      node.append(child.nodeType ? child : document.createTextNode(String(child)));
    }
    return node;
  }

  const nfBRL0 = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
  const nfInt = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });
  const nfNum2 = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 });

  function fmtBRL(v) {
    if (v === null || v === undefined || Number.isNaN(v)) return "—";
    return nfBRL0.format(v);
  }
  function fmtBRLCompacto(v) {
    if (v === null || v === undefined || Number.isNaN(v)) return "—";
    const abs = Math.abs(v);
    if (abs >= 1e6) return "R$ " + nfNum2.format(v / 1e6) + " mi";
    if (abs >= 1e3) return "R$ " + nfInt.format(v / 1e3) + " mil";
    return nfBRL0.format(v);
  }
  function fmtNum(v) {
    if (v === null || v === undefined || Number.isNaN(v)) return "—";
    return nfInt.format(v);
  }
  function fmtNumCompacto(v) {
    if (v === null || v === undefined || Number.isNaN(v)) return "—";
    const abs = Math.abs(v);
    if (abs >= 1e6) return nfNum2.format(v / 1e6) + " mi";
    if (abs >= 1e3) return nfInt.format(v / 1e3) + " mil";
    return nfInt.format(v);
  }
  function fmtPct(v, casas) {
    if (v === null || v === undefined || Number.isNaN(v)) return "—";
    const d = casas === undefined ? 1 : casas;
    return new Intl.NumberFormat("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d }).format(v * 100) + "%";
  }

  /* ---------------- selos epistemicos ---------------- */

  const SELOS = {
    fato: { texto: "Fato validado", classe: "selo-fato", icone: "✓" },
    descritiva: { texto: "Evidência descritiva", classe: "selo-descritiva", icone: "◆" },
    exploratoria: { texto: "Associação exploratória", classe: "selo-exploratoria", icone: "≈" },
    triagem: { texto: "Triagem", classe: "selo-triagem", icone: "⚑" },
    bloqueado: { texto: "Bloqueado", classe: "selo-bloqueado", icone: "⛔" },
    ausente: { texto: "Dado ausente", classe: "selo-ausente", icone: "∅" },
    naovalidado: { texto: "Não validado", classe: "selo-naovalidado", icone: "!" },
  };

  function selo(tipo, textoOverride) {
    const cfg = SELOS[tipo] || SELOS.ausente;
    return el("span", { class: "selo " + cfg.classe }, cfg.icone + " " + (textoOverride || cfg.texto));
  }

  const SELO_POR_STATUS_HIPOTESE = {
    "Confirmada descritivamente": "descritiva",
    "Parcialmente suportada": "exploratoria",
    "Exploratória": "exploratoria",
    "Não comprovada": "naovalidado",
    "Rejeitada": "ausente",
    "Inválida por limitação de dados": "bloqueado",
  };

  /* ---------------- KPI tile ---------------- */

  function tile(cfg) {
    const t = el("div", { class: "tile" });
    const rot = el("div", { class: "rotulo" }, cfg.rotulo);
    if (cfg.selo) rot.append(selo(cfg.selo, cfg.seloTexto));
    t.append(rot, el("div", { class: "valor" }, cfg.valor));
    if (cfg.delta) t.append(el("div", { class: "delta" }, cfg.delta));
    if (cfg.nota) {
      const dl = el("dl");
      const campos = [
        ["Fórmula", cfg.nota.formula],
        ["Fonte", cfg.nota.fonte],
        ["Unidade", cfg.nota.unidade],
        ["Confiança", cfg.nota.confianca],
        ["Limitação", cfg.nota.limitacao],
      ];
      for (const [dt, dd] of campos) {
        if (dd) dl.append(el("dt", null, dt), el("dd", null, dd));
      }
      t.append(el("details", null, el("summary", null, "nota metodológica"), dl));
    }
    return t;
  }

  /* ---------------- tooltip ---------------- */

  const tip = document.getElementById("tooltip");

  function showTip(evt, titulo, linhas) {
    tip.textContent = "";
    if (titulo) tip.append(el("div", { class: "t-titulo" }, titulo));
    for (const linha of linhas) {
      const row = el("div", { class: "t-linha" });
      if (linha.cor) {
        const chave = el("span", { class: "t-chave" });
        chave.style.background = linha.cor;
        row.append(chave);
      }
      row.append(el("span", { class: "t-valor" }, linha.valor));
      if (linha.nome) row.append(el("span", { class: "t-nome" }, linha.nome));
      tip.append(row);
    }
    tip.style.display = "block";
    const margem = 14;
    const rect = tip.getBoundingClientRect();
    let x = evt.clientX + margem;
    let y = evt.clientY + margem;
    if (x + rect.width > window.innerWidth - 8) x = evt.clientX - rect.width - margem;
    if (y + rect.height > window.innerHeight - 8) y = evt.clientY - rect.height - margem;
    tip.style.left = x + "px";
    tip.style.top = y + "px";
  }
  function hideTip() {
    tip.style.display = "none";
  }

  /* ---------------- SVG ---------------- */

  const SVGNS = "http://www.w3.org/2000/svg";
  function svgEl(tag, attrs) {
    const node = document.createElementNS(SVGNS, tag);
    for (const [k, v] of Object.entries(attrs || {})) node.setAttribute(k, v);
    return node;
  }

  function niceTicks(min, max, alvo) {
    if (min === max) {
      max = min + 1;
    }
    const bruto = (max - min) / (alvo || 5);
    const mag = Math.pow(10, Math.floor(Math.log10(bruto)));
    const normal = bruto / mag;
    let passo;
    if (normal <= 1) passo = 1;
    else if (normal <= 2) passo = 2;
    else if (normal <= 5) passo = 5;
    else passo = 10;
    passo *= mag;
    const inicio = Math.floor(min / passo) * passo;
    const ticks = [];
    for (let v = inicio; v <= max + passo * 0.001; v += passo) ticks.push(Math.round(v * 1e9) / 1e9);
    return ticks;
  }

  function moldura(W, H, m, dominio, yFmt, labels, mostrarCadaN) {
    const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, role: "img" });
    const plotW = W - m.l - m.r;
    const plotH = H - m.t - m.b;
    const ticks = niceTicks(dominio.min, dominio.max, 5);
    const yMin = Math.min(dominio.min, ticks[0]);
    const yMax = Math.max(dominio.max, ticks[ticks.length - 1]);
    const y = (v) => m.t + plotH - ((v - yMin) / (yMax - yMin)) * plotH;
    for (const t of ticks) {
      const linha = svgEl("line", { x1: m.l, x2: m.l + plotW, y1: y(t), y2: y(t), "stroke-width": 1 });
      linha.style.stroke = "var(--grid)";
      svg.append(linha);
      const rotulo = svgEl("text", { x: m.l - 8, y: y(t) + 4, "text-anchor": "end", "font-size": 11 });
      rotulo.style.fill = "var(--ink-3)";
      rotulo.textContent = yFmt(t);
      svg.append(rotulo);
    }
    if (yMin <= 0 && yMax >= 0) {
      const zero = svgEl("line", { x1: m.l, x2: m.l + plotW, y1: y(0), y2: y(0), "stroke-width": 1 });
      zero.style.stroke = "var(--baseline)";
      svg.append(zero);
    }
    const n = labels.length;
    const x = (i) => m.l + (n === 1 ? plotW / 2 : (i / (n - 1)) * plotW);
    const cada = mostrarCadaN || Math.ceil(n / 8);
    labels.forEach((rotulo, i) => {
      if (i % cada !== 0 && i !== n - 1) return;
      const texto = svgEl("text", { x: x(i), y: H - 8, "text-anchor": "middle", "font-size": 11 });
      texto.style.fill = "var(--ink-3)";
      texto.textContent = rotulo;
      svg.append(texto);
    });
    return { svg, x, y, plotW, plotH, yMin, yMax };
  }

  function legenda(container, series, tipo) {
    if (series.length < 2) return;
    const box = el("div", { class: "legenda" });
    for (const s of series) {
      const chave = el("span", { class: tipo === "caixa" ? "caixa" : "traco" });
      chave.style.background = s.cor;
      box.append(el("span", { class: "chave" }, chave, s.nome));
    }
    container.append(box);
  }

  /* Linha (com faixa opcional e crosshair). series: [{nome, cor, values}] */
  function lineChart(container, cfg) {
    container.textContent = "";
    legenda(container, cfg.series, "traco");
    const W = 860;
    const H = cfg.altura || 280;
    const m = { l: 58, r: 30, t: 14, b: 30 };
    let vmin = Infinity;
    let vmax = -Infinity;
    for (const s of cfg.series) {
      for (const v of s.values) {
        if (v === null || v === undefined) continue;
        vmin = Math.min(vmin, v);
        vmax = Math.max(vmax, v);
      }
    }
    if (cfg.banda) {
      for (const v of [...cfg.banda.inferior, ...cfg.banda.superior]) {
        if (v === null || v === undefined) continue;
        vmin = Math.min(vmin, v);
        vmax = Math.max(vmax, v);
      }
    }
    if (vmin > 0) vmin = 0;
    const { svg, x, y } = moldura(W, H, m, { min: vmin, max: vmax }, cfg.yFmt, cfg.labels);

    if (cfg.banda) {
      let d = "";
      const idx = [];
      cfg.banda.superior.forEach((v, i) => {
        if (v !== null && v !== undefined && cfg.banda.inferior[i] !== null && cfg.banda.inferior[i] !== undefined) idx.push(i);
      });
      if (idx.length > 1) {
        idx.forEach((i, k) => {
          d += (k === 0 ? "M" : "L") + x(i) + " " + y(cfg.banda.superior[i]) + " ";
        });
        for (let k = idx.length - 1; k >= 0; k--) {
          d += "L" + x(idx[k]) + " " + y(cfg.banda.inferior[idx[k]]) + " ";
        }
        const caminho = svgEl("path", { d: d + "Z" });
        caminho.style.fill = cfg.banda.cor;
        svg.append(caminho);
      }
    }

    for (const s of cfg.series) {
      let d = "";
      let caneta = false;
      s.values.forEach((v, i) => {
        if (v === null || v === undefined) {
          caneta = false;
          return;
        }
        d += (caneta ? "L" : "M") + x(i) + " " + y(v) + " ";
        caneta = true;
      });
      const caminho = svgEl("path", { d, fill: "none", "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" });
      caminho.style.stroke = s.cor;
      svg.append(caminho);
      for (let i = s.values.length - 1; i >= 0; i--) {
        if (s.values[i] !== null && s.values[i] !== undefined) {
          const anel = svgEl("circle", { cx: x(i), cy: y(s.values[i]), r: 6.5 });
          anel.style.fill = "var(--surface)";
          const ponto = svgEl("circle", { cx: x(i), cy: y(s.values[i]), r: 4.5 });
          ponto.style.fill = s.cor;
          svg.append(anel, ponto);
          break;
        }
      }
    }

    const cursor = svgEl("line", { y1: m.t, y2: H - m.b, "stroke-width": 1, opacity: 0 });
    cursor.style.stroke = "var(--baseline)";
    svg.append(cursor);
    const marcadores = cfg.series.map((s) => {
      const anel = svgEl("circle", { r: 6.5, opacity: 0 });
      anel.style.fill = "var(--surface)";
      const ponto = svgEl("circle", { r: 4.5, opacity: 0 });
      ponto.style.fill = s.cor;
      svg.append(anel, ponto);
      return { anel, ponto };
    });

    const captura = svgEl("rect", { x: m.l, y: m.t, width: W - m.l - m.r, height: H - m.t - m.b, fill: "transparent" });
    captura.addEventListener("pointermove", (evt) => {
      const box = svg.getBoundingClientRect();
      const px = ((evt.clientX - box.left) / box.width) * W;
      const n = cfg.labels.length;
      const i = Math.max(0, Math.min(n - 1, Math.round(((px - m.l) / (W - m.l - m.r)) * (n - 1))));
      cursor.setAttribute("x1", x(i));
      cursor.setAttribute("x2", x(i));
      cursor.setAttribute("opacity", 1);
      const linhas = [];
      cfg.series.forEach((s, k) => {
        const v = s.values[i];
        if (v === null || v === undefined) {
          marcadores[k].anel.setAttribute("opacity", 0);
          marcadores[k].ponto.setAttribute("opacity", 0);
          return;
        }
        marcadores[k].anel.setAttribute("cx", x(i));
        marcadores[k].anel.setAttribute("cy", y(v));
        marcadores[k].anel.setAttribute("opacity", 1);
        marcadores[k].ponto.setAttribute("cx", x(i));
        marcadores[k].ponto.setAttribute("cy", y(v));
        marcadores[k].ponto.setAttribute("opacity", 1);
        linhas.push({ cor: s.cor, valor: (cfg.tipFmt || cfg.yFmt)(v), nome: s.nome });
      });
      if (cfg.banda && cfg.banda.inferior[i] !== null && cfg.banda.inferior[i] !== undefined) {
        linhas.push({ valor: (cfg.tipFmt || cfg.yFmt)(cfg.banda.inferior[i]) + " – " + (cfg.tipFmt || cfg.yFmt)(cfg.banda.superior[i]), nome: cfg.banda.nome });
      }
      showTip(evt, cfg.labels[i], linhas);
    });
    captura.addEventListener("pointerleave", () => {
      cursor.setAttribute("opacity", 0);
      marcadores.forEach((mk) => {
        mk.anel.setAttribute("opacity", 0);
        mk.ponto.setAttribute("opacity", 0);
      });
      hideTip();
    });
    svg.append(captura);
    container.append(svg);
  }

  function barraArredondada(x0, y0, w, h, r, pontaEmCima) {
    if (h <= 0) return "";
    const raio = Math.min(r, w / 2, h);
    if (pontaEmCima) {
      return `M${x0} ${y0 + h} L${x0} ${y0 + raio} Q${x0} ${y0} ${x0 + raio} ${y0} L${x0 + w - raio} ${y0} Q${x0 + w} ${y0} ${x0 + w} ${y0 + raio} L${x0 + w} ${y0 + h} Z`;
    }
    return `M${x0} ${y0} L${x0 + w} ${y0} L${x0 + w} ${y0 + h - raio} Q${x0 + w} ${y0 + h} ${x0 + w - raio} ${y0 + h} L${x0 + raio} ${y0 + h} Q${x0} ${y0 + h} ${x0} ${y0 + h - raio} L${x0} ${y0} Z`;
  }

  /* Colunas verticais (suporta valores negativos e linha de referencia). */
  function columnChart(container, cfg) {
    container.textContent = "";
    const W = 860;
    const H = cfg.altura || 260;
    const m = { l: 58, r: 30, t: 14, b: 30 };
    let vmin = 0;
    let vmax = 0;
    for (const v of cfg.values) {
      if (v === null || v === undefined) continue;
      vmin = Math.min(vmin, v);
      vmax = Math.max(vmax, v);
    }
    if (cfg.refLinha) vmax = Math.max(vmax, cfg.refLinha.valor);
    const { svg, x, y } = moldura(W, H, m, { min: vmin, max: vmax }, cfg.yFmt, cfg.labels, cfg.mostrarCadaN);
    const n = cfg.labels.length;
    const slot = (W - m.l - m.r) / n;
    const larg = Math.min(24, Math.max(6, slot - 6));
    cfg.values.forEach((v, i) => {
      if (v === null || v === undefined) return;
      const cx = m.l + slot * i + slot / 2;
      const y0 = Math.min(y(v), y(0));
      const h = Math.abs(y(v) - y(0));
      const caminho = svgEl("path", { d: barraArredondada(cx - larg / 2, y0, larg, Math.max(h, 1), 4, v >= 0) });
      caminho.style.fill = cfg.cor;
      caminho.addEventListener("pointermove", (evt) => {
        caminho.setAttribute("opacity", 0.8);
        showTip(evt, cfg.labels[i], [{ cor: cfg.cor, valor: (cfg.tipFmt || cfg.yFmt)(v), nome: cfg.nomeSerie }]);
      });
      caminho.addEventListener("pointerleave", () => {
        caminho.setAttribute("opacity", 1);
        hideTip();
      });
      svg.append(caminho);
    });
    if (cfg.refLinha) {
      const yr = y(cfg.refLinha.valor);
      const linha = svgEl("line", { x1: m.l, x2: W - m.r, y1: yr, y2: yr, "stroke-width": 1 });
      linha.style.stroke = "var(--ink-3)";
      svg.append(linha);
      const rotulo = svgEl("text", { x: W - m.r, y: yr - 5, "text-anchor": "end", "font-size": 11 });
      rotulo.style.fill = "var(--ink-3)";
      rotulo.textContent = cfg.refLinha.rotulo;
      svg.append(rotulo);
    }
    container.append(svg);
  }

  /* Colunas empilhadas com gap de 2px entre segmentos. */
  function stackedColumns(container, cfg) {
    container.textContent = "";
    legenda(container, cfg.series, "caixa");
    const W = 860;
    const H = cfg.altura || 260;
    const m = { l: 58, r: 30, t: 14, b: 30 };
    const totais = cfg.labels.map((_, i) => cfg.series.reduce((acc, s) => acc + (s.values[i] || 0), 0));
    const { svg, y } = moldura(W, H, m, { min: 0, max: Math.max(...totais) }, cfg.yFmt, cfg.labels, 1);
    const n = cfg.labels.length;
    const slot = (W - m.l - m.r) / n;
    const larg = Math.min(24, Math.max(8, slot - 10));
    cfg.labels.forEach((rotulo, i) => {
      let acumulado = 0;
      const cx = m.l + slot * i + slot / 2;
      cfg.series.forEach((s, k) => {
        const v = s.values[i] || 0;
        if (v <= 0) return;
        const yTopo = y(acumulado + v);
        const yBase = y(acumulado);
        const gap = k === 0 ? 0 : 2;
        const h = Math.max(yBase - yTopo - gap, 1);
        const rect = svgEl("rect", { x: cx - larg / 2, y: yTopo, width: larg, height: h, rx: 2 });
        rect.style.fill = s.cor;
        rect.addEventListener("pointermove", (evt) => {
          rect.setAttribute("opacity", 0.8);
          showTip(evt, rotulo, cfg.series.map((serie) => ({ cor: serie.cor, valor: fmtNum(serie.values[i] || 0), nome: serie.nome })));
        });
        rect.addEventListener("pointerleave", () => {
          rect.setAttribute("opacity", 1);
          hideTip();
        });
        svg.append(rect);
        acumulado += v;
      });
    });
    container.append(svg);
  }

  /* Barras horizontais com rotulo de valor na ponta. */
  function barChartH(container, cfg) {
    container.textContent = "";
    const alturaBarra = 26;
    const m = { l: cfg.margemEsq || 150, r: 74, t: 8, b: 26 };
    const n = cfg.items.length;
    const W = 860;
    const H = m.t + m.b + n * alturaBarra;
    const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, role: "img" });
    let vmin = 0;
    let vmax = 0;
    for (const item of cfg.items) {
      vmin = Math.min(vmin, item.valor);
      vmax = Math.max(vmax, item.valor);
    }
    const plotW = W - m.l - m.r;
    const ticks = niceTicks(vmin, vmax, 5);
    const xMin = Math.min(vmin, ticks[0]);
    const xMax = Math.max(vmax, ticks[ticks.length - 1]);
    const x = (v) => m.l + ((v - xMin) / (xMax - xMin || 1)) * plotW;
    for (const t of ticks) {
      const linha = svgEl("line", { x1: x(t), x2: x(t), y1: m.t, y2: H - m.b, "stroke-width": 1 });
      linha.style.stroke = "var(--grid)";
      svg.append(linha);
      const rotulo = svgEl("text", { x: x(t), y: H - 8, "text-anchor": "middle", "font-size": 11 });
      rotulo.style.fill = "var(--ink-3)";
      rotulo.textContent = cfg.xFmt(t);
      svg.append(rotulo);
    }
    const zero = svgEl("line", { x1: x(0), x2: x(0), y1: m.t, y2: H - m.b, "stroke-width": 1 });
    zero.style.stroke = "var(--baseline)";
    svg.append(zero);
    cfg.items.forEach((item, i) => {
      const cy = m.t + i * alturaBarra + alturaBarra / 2;
      const rotulo = svgEl("text", { x: m.l - 8, y: cy + 4, "text-anchor": "end", "font-size": 12 });
      rotulo.style.fill = "var(--ink-2)";
      rotulo.textContent = item.rotulo;
      svg.append(rotulo);
      const x0 = Math.min(x(0), x(item.valor));
      const w = Math.max(Math.abs(x(item.valor) - x(0)), 1);
      const h = 16;
      const negativo = item.valor < 0;
      const raio = Math.min(4, w / 2);
      const dCaminho = negativo
        ? `M${x0 + w} ${cy - h / 2} L${x0 + raio} ${cy - h / 2} Q${x0} ${cy - h / 2} ${x0} ${cy - h / 2 + raio} L${x0} ${cy + h / 2 - raio} Q${x0} ${cy + h / 2} ${x0 + raio} ${cy + h / 2} L${x0 + w} ${cy + h / 2} Z`
        : `M${x0} ${cy - h / 2} L${x0 + w - raio} ${cy - h / 2} Q${x0 + w} ${cy - h / 2} ${x0 + w} ${cy - h / 2 + raio} L${x0 + w} ${cy + h / 2 - raio} Q${x0 + w} ${cy + h / 2} ${x0 + w - raio} ${cy + h / 2} L${x0} ${cy + h / 2} Z`;
      const barra = svgEl("path", { d: dCaminho });
      barra.style.fill = cfg.cor;
      barra.addEventListener("pointermove", (evt) => {
        barra.setAttribute("opacity", 0.8);
        showTip(evt, item.rotulo, [{ cor: cfg.cor, valor: cfg.xFmt(item.valor), nome: cfg.nomeSerie }, ...(item.extra || [])]);
      });
      barra.addEventListener("pointerleave", () => {
        barra.setAttribute("opacity", 1);
        hideTip();
      });
      svg.append(barra);
      const valor = svgEl("text", {
        x: negativo ? x0 + w + 6 : x0 + w + 6,
        y: cy + 4,
        "text-anchor": "start",
        "font-size": 12,
        "font-weight": 600,
      });
      valor.style.fill = "var(--ink-1)";
      valor.textContent = cfg.xFmt(item.valor);
      svg.append(valor);
    });
    container.append(svg);
  }

  /* ---------------- tabela com busca, ordenacao, paginacao e download ---------------- */

  function renderTable(container, cfg) {
    container.textContent = "";
    const estado = { busca: "", filtro: "", ordem: null, asc: true, pagina: 0 };
    const barra = el("div", { class: "tabela-barra" });
    let inputBusca = null;
    if (cfg.busca !== false) {
      inputBusca = el("input", { type: "search", placeholder: "Buscar…", "aria-label": "Buscar na tabela" });
      inputBusca.addEventListener("input", () => {
        estado.busca = inputBusca.value.toLowerCase();
        estado.pagina = 0;
        desenhar();
      });
      barra.append(inputBusca);
    }
    let seletor = null;
    if (cfg.filtro) {
      seletor = el("select", { "aria-label": cfg.filtro.rotulo });
      seletor.append(el("option", { value: "" }, cfg.filtro.rotulo + ": todos"));
      const valores = cfg.filtro.opcoes || [...new Set(cfg.rows.map((r) => r[cfg.filtro.chave]))].sort();
      for (const v of valores) seletor.append(el("option", { value: v }, String(v)));
      seletor.addEventListener("change", () => {
        estado.filtro = seletor.value;
        estado.pagina = 0;
        desenhar();
      });
      barra.append(seletor);
    }
    const contagem = el("span", { class: "contagem" });
    barra.append(contagem);
    if (cfg.download) {
      const botao = el("button", { type: "button" }, "Baixar CSV (derivado)");
      botao.addEventListener("click", () => {
        const linhasFiltradas = filtrar();
        const cab = cfg.columns.map((c) => '"' + c.label.replaceAll('"', '""') + '"').join(",");
        const corpo = linhasFiltradas
          .map((r) => cfg.columns.map((c) => '"' + String(r[c.key] ?? "").replaceAll('"', '""') + '"').join(","))
          .join("\n");
        const blob = new Blob(["﻿" + cab + "\n" + corpo], { type: "text/csv;charset=utf-8" });
        const a = el("a", { href: URL.createObjectURL(blob), download: cfg.download });
        a.click();
        URL.revokeObjectURL(a.href);
      });
      barra.append(botao);
    }
    const wrap = el("div", { class: "tabela-wrap" });
    const tabela = el("table", { class: "dados" });
    wrap.append(tabela);
    const paginacao = el("div", { class: "paginacao" });
    container.append(barra, wrap, paginacao);
    if (cfg.notaFonte) container.append(el("p", { class: "nota-limitacao" }, cfg.notaFonte));

    function filtrar() {
      let linhas = cfg.rows;
      if (estado.filtro && cfg.filtro) linhas = linhas.filter((r) => String(r[cfg.filtro.chave]) === estado.filtro);
      if (estado.busca) {
        linhas = linhas.filter((r) => cfg.columns.some((c) => String(r[c.key] ?? "").toLowerCase().includes(estado.busca)));
      }
      if (estado.ordem) {
        const col = cfg.columns.find((c) => c.key === estado.ordem);
        const fator = estado.asc ? 1 : -1;
        linhas = [...linhas].sort((a, b) => {
          const va = a[estado.ordem];
          const vb = b[estado.ordem];
          if (va === null || va === undefined) return 1;
          if (vb === null || vb === undefined) return -1;
          if (col && col.num) return (va - vb) * fator;
          return String(va).localeCompare(String(vb), "pt-BR") * fator;
        });
      }
      return linhas;
    }

    function desenhar() {
      const linhas = filtrar();
      const tamanho = cfg.pageSize || 12;
      const paginas = Math.max(1, Math.ceil(linhas.length / tamanho));
      estado.pagina = Math.min(estado.pagina, paginas - 1);
      const visiveis = linhas.slice(estado.pagina * tamanho, (estado.pagina + 1) * tamanho);
      tabela.textContent = "";
      const trCab = el("tr");
      for (const c of cfg.columns) {
        const th = el("th", { scope: "col" }, c.label + " ");
        if (estado.ordem === c.key) th.append(el("span", { class: "seta" }, estado.asc ? "▲" : "▼"));
        th.addEventListener("click", () => {
          if (estado.ordem === c.key) estado.asc = !estado.asc;
          else {
            estado.ordem = c.key;
            estado.asc = true;
          }
          desenhar();
        });
        trCab.append(th);
      }
      tabela.append(el("thead", null, trCab));
      const corpo = el("tbody");
      for (const r of visiveis) {
        const tr = el("tr");
        for (const c of cfg.columns) {
          const bruto = r[c.key];
          const texto = c.fmt ? c.fmt(bruto, r) : bruto === null || bruto === undefined ? "—" : String(bruto);
          const td = el("td", { class: c.num ? "num" : "" });
          if (texto && texto.nodeType) td.append(texto);
          else td.textContent = texto;
          tr.append(td);
        }
        corpo.append(tr);
      }
      tabela.append(corpo);
      contagem.textContent = fmtNum(linhas.length) + " linhas";
      paginacao.textContent = "";
      if (paginas > 1) {
        const anterior = el("button", { type: "button" }, "‹ anterior");
        const proxima = el("button", { type: "button" }, "próxima ›");
        anterior.disabled = estado.pagina === 0;
        proxima.disabled = estado.pagina >= paginas - 1;
        anterior.addEventListener("click", () => {
          estado.pagina--;
          desenhar();
        });
        proxima.addEventListener("click", () => {
          estado.pagina++;
          desenhar();
        });
        paginacao.append(anterior, el("span", null, `página ${estado.pagina + 1} de ${paginas}`), proxima);
      }
    }
    desenhar();
  }

  /* ================= SECOES ================= */

  const COR = {
    s1: "var(--serie-1)",
    s2: "var(--serie-2)",
    s3: "var(--serie-3)",
    s4: "var(--serie-4)",
    s5: "var(--serie-5)",
    s6: "var(--serie-6)",
    neutro: "var(--ink-3)",
  };

  /* ---------- 1. Sumario executivo ---------- */

  function renderSumario() {
    const k = DATA.kpis;
    const grade = document.getElementById("sumario-kpis");
    grade.textContent = "";
    grade.append(
      tile({
        rotulo: "Receita observada 24 meses",
        valor: fmtBRLCompacto(k.receita_total_24m),
        selo: "fato",
        nota: {
          formula: "sum(QUANTIDADE_VENDIDA × PRECO_UNIT_MEDIO)",
          fonte: "outputs/tables/vendas_mensais.csv",
          unidade: "BRL",
          confianca: "Alta (grão validado, 0 duplicatas)",
          limitacao: "Receita observada, não margem. Venda observada não é demanda real.",
        },
      }),
      tile({
        rotulo: "Receita 2025-12",
        valor: fmtBRLCompacto(k.receita_2025_12),
        delta: fmtPct(k.queda_janela_2024_11_a_2025_12) + " vs 2024-11 (" + fmtBRLCompacto(k.receita_2024_11) + ") — janela extrema",
        selo: "descritiva",
        nota: {
          formula: "(valor_atual − valor_base) / valor_base",
          fonte: "outputs/tables/vendas_mensais.csv",
          unidade: "% sobre BRL",
          confianca: "Média (depende da janela declarada)",
          limitacao: "2024-11 tem Black Friday; outras janelas produzem percentuais diferentes.",
        },
      }),
      tile({
        rotulo: "SKUs vendidos 2025-12",
        valor: fmtNum(k.skus_2025_12),
        delta: "vs " + fmtNum(k.skus_2024_11) + " em 2024-11",
        selo: "descritiva",
        nota: {
          formula: "count_distinct(CODIGO com venda no mês)",
          fonte: "outputs/tables/sortimento_controlado_por_volume.csv",
          unidade: "SKUs",
          confianca: "Média",
          limitacao: "Mede sortimento observado em vendas; não mede disponibilidade nem procura.",
        },
      }),
      tile({
        rotulo: "Pares loja-mês comparáveis 2025",
        valor: fmtNum(k.lojas_comparaveis_2025) + " de " + fmtNum(k.pares_loja_mes_2025),
        delta: k.lojas + " lojas ativas na base",
        selo: "descritiva",
        nota: {
          formula: "loja com venda no mês atual e no mesmo mês do ano anterior",
          fonte: "outputs/tables/vendas_same_store_yoy.csv",
          unidade: "pares loja × mês",
          confianca: "Média",
          limitacao: "Comparabilidade não prova status operacional (DADO AUSENTE: calendário de lojas).",
        },
      }),
      tile({
        rotulo: "Cobertura das entradas conhecidas",
        valor: fmtPct(k.cobertura_entradas_pct),
        delta: k.classificacao_cobertura,
        selo: "fato",
        nota: {
          formula: "(estoque inicial + compras em armazenagem) / vendas em armazenagem",
          fonte: "outputs/tables/compras_coverage_audit.csv",
          unidade: "% em unidade de estoque",
          confianca: "Alta como medição; bloqueia análise causal",
          limitacao: "Gap contábil não é ruptura física comprovada; base de compras incompleta.",
        },
      }),
      tile({
        rotulo: "Checks de qualidade",
        valor:
          fmtNum(k.qualidade_checks.PASS || 0) + " PASS · " + fmtNum(k.qualidade_checks.WARN || 0) + " WARN · " + fmtNum(k.qualidade_checks.FAIL || 0) + " FAIL",
        selo: "fato",
        nota: {
          formula: "checks de contrato/qualidade da Spec 02",
          fonte: "outputs/tables/data_quality_report.csv",
          unidade: "checks",
          confianca: "Alta",
          limitacao: "FAIL invalida ou torna não comprovável conclusão importante do relatório.",
        },
      })
    );

    const epistemico = document.getElementById("sumario-epistemico");
    epistemico.textContent = "";
    const colunas = [
      {
        selo: "fato",
        titulo: "Validado com maior confiança",
        itens: [
          "Grão da base de vendas validado (produto × loja × dia × embalagem, 0 duplicatas).",
          "Base de compras incompleta: 7 de 11 lojas e 329 de 2.731 produtos.",
          "Entradas conhecidas cobrem 37,4% das saídas — não confiável para análise causal.",
          "Gap contábil material: 14.570 de 28.721 pares produto × loja com gap > 0.",
        ],
      },
      {
        selo: "descritiva",
        titulo: "Evidência descritiva",
        itens: [
          "Queda anual observada em todas as 11 lojas (−30,6% a −66,5% em 2025).",
          "Queda majoritariamente generalizada entre categorias (206 linhas categoria-mês).",
          "Sortimento vendido caiu de 2.490 SKUs (2024-11) para 1.212 (2025-12).",
          "2025-12 ficou abaixo do sortimento esperado pelo controle de volume (~1.849 SKUs).",
        ],
      },
      {
        selo: "exploratoria",
        titulo: "Hipótese / associação exploratória",
        itens: [
          "Causa operacional da queda permanece aberta (H7 exploratória).",
          "Correlação preço-volume negativa em 160 produtos — candidatos a investigação, não elasticidade.",
          "Estreitamento de sortimento compatível com várias explicações (disponibilidade, procura, mix, captura).",
          "Triagens de repricing, compras, promoção e descontinuação priorizam investigação.",
        ],
      },
      {
        selo: "bloqueado",
        titulo: "Bloqueado / dado ausente",
        itens: [
          "Causalidade compras → queda de vendas (cobertura insuficiente).",
          "Ruptura física operacional e demanda potencial sem censura.",
          "Compra líquida sugerida e pedido final (sem estoque atual confiável).",
          "Ação automática de promoção ou descontinuação (sem margem, lead time, lote mínimo).",
        ],
      },
    ];
    for (const col of colunas) {
      const bloco = el("div", { class: "col" });
      bloco.append(el("h4", null, selo(col.selo), col.titulo));
      bloco.append(el("ul", null, col.itens.map((item) => el("li", null, item))));
      epistemico.append(bloco);
    }

    const hip = document.getElementById("sumario-hipoteses");
    hip.textContent = "";
    for (const h of DATA.hipoteses) {
      hip.append(
        tile({
          rotulo: h.hipotese_id + " — " + h.hipotese,
          valor: "",
          selo: SELO_POR_STATUS_HIPOTESE[h.status] || "ausente",
          seloTexto: h.status,
          delta: "Confiança: " + h.nivel_confianca,
        })
      );
    }
  }

  /* ---------- 2. Qualidade ---------- */

  function renderQualidade() {
    const grade = document.getElementById("qualidade-kpis");
    grade.textContent = "";
    const contagens = DATA.qualidade.contagem_status;
    const falhasPorTabela = {};
    for (const c of DATA.qualidade.checks) {
      if (c.status === "FAIL") falhasPorTabela[c.tabela] = (falhasPorTabela[c.tabela] || 0) + 1;
    }
    const piorTabela = Object.entries(falhasPorTabela).sort((a, b) => b[1] - a[1])[0];
    grade.append(
      tile({ rotulo: "✓ PASS", valor: fmtNum(contagens.PASS || 0), delta: "checks sem problema detectado", selo: "fato" }),
      tile({ rotulo: "⚠ WARN", valor: fmtNum(contagens.WARN || 0), delta: "degradam, mas não invalidam", selo: "fato" }),
      tile({ rotulo: "✕ FAIL", valor: fmtNum(contagens.FAIL || 0), delta: "invalidam ou tornam não comprovável", selo: "fato" }),
      tile({
        rotulo: "Base com maior risco",
        valor: piorTabela ? piorTabela[0] : "—",
        delta: piorTabela ? piorTabela[1] + " checks FAIL" : "",
        selo: "descritiva",
      })
    );
    renderTable(document.getElementById("qualidade-tabela"), {
      columns: [
        { key: "tabela", label: "Tabela" },
        { key: "check", label: "Check" },
        { key: "status", label: "Status" },
        { key: "linhas_afetadas", label: "Linhas", num: true, fmt: fmtNum },
        { key: "pct_afetado", label: "% afetado", num: true, fmt: (v) => (v === null || v === undefined ? "—" : fmtPct(v, 2)) },
        { key: "severidade", label: "Severidade" },
        { key: "descricao", label: "Descrição" },
        { key: "impacto_analitico", label: "Impacto analítico" },
        { key: "acao_recomendada", label: "Ação recomendada" },
      ],
      rows: DATA.qualidade.checks,
      filtro: { chave: "status", rotulo: "Status", opcoes: ["PASS", "WARN", "FAIL"] },
      pageSize: 10,
      download: "data_quality_report_derivado.csv",
    });
    renderTable(document.getElementById("ingestao-tabela"), {
      columns: [
        { key: "arquivo", label: "Arquivo" },
        { key: "encoding_usado", label: "Encoding" },
        { key: "separador_detectado", label: "Separador" },
        { key: "linhas_lidas", label: "Linhas", num: true, fmt: fmtNum },
        { key: "colunas_lidas", label: "Colunas", num: true, fmt: fmtNum },
        { key: "erros_parsing", label: "Erros parsing", num: true },
        { key: "nulos_antes", label: "Nulos antes", num: true, fmt: fmtNum },
        { key: "nulos_depois", label: "Nulos depois", num: true, fmt: fmtNum },
        { key: "zeros_criados", label: "Zeros criados", num: true, fmt: fmtNum },
        { key: "registros_descartados", label: "Descartados", num: true, fmt: fmtNum },
        { key: "status_ingestao", label: "Status" },
      ],
      rows: DATA.ingestao,
      busca: false,
      pageSize: 10,
    });
  }

  /* ---------- 3. Vendas ---------- */

  function renderVendas() {
    const vm = DATA.vendas_mensais;
    const labels = vm.map((r) => r.ano_mes);
    const grade = document.getElementById("vendas-kpis");
    grade.textContent = "";
    grade.append(
      tile({
        rotulo: "Receita total (24 meses)",
        valor: fmtBRLCompacto(DATA.kpis.receita_total_24m),
        selo: "fato",
        nota: {
          formula: "sum(QUANTIDADE_VENDIDA × PRECO_UNIT_MEDIO)",
          fonte: "outputs/tables/vendas_mensais.csv",
          unidade: "BRL",
          confianca: "Alta",
          limitacao: "Receita observada; não é margem nem demanda real.",
        },
      }),
      tile({
        rotulo: "Maior mês (2024-11)",
        valor: fmtBRLCompacto(DATA.kpis.receita_2024_11),
        delta: "Black Friday — sazonalidade forte",
        selo: "descritiva",
      }),
      tile({
        rotulo: "Menor mês (2025-12)",
        valor: fmtBRLCompacto(DATA.kpis.receita_2025_12),
        delta: fmtPct(DATA.kpis.queda_janela_2024_11_a_2025_12) + " vs 2024-11 — janela extrema, declarar método",
        selo: "descritiva",
      })
    );
    lineChart(document.getElementById("vendas-graf-receita"), {
      labels,
      series: [{ nome: "Receita mensal", cor: COR.s1, values: vm.map((r) => r.receita) }],
      yFmt: fmtBRLCompacto,
      tipFmt: fmtBRL,
    });
    lineChart(document.getElementById("vendas-graf-qtd"), {
      labels,
      series: [{ nome: "Quantidade vendida", cor: COR.s1, values: vm.map((r) => r.qtd_vendida) }],
      yFmt: fmtNumCompacto,
      tipFmt: fmtNum,
    });
    const meses2025 = vm.filter((r) => r.ano_mes.startsWith("2025"));
    columnChart(document.getElementById("vendas-graf-yoy"), {
      labels: meses2025.map((r) => r.ano_mes),
      values: meses2025.map((r) => r.variacao_receita_yoy),
      cor: COR.s1,
      nomeSerie: "Variação YoY da receita",
      yFmt: (v) => fmtPct(v, 0),
      tipFmt: fmtPct,
      mostrarCadaN: 1,
    });
    renderTable(document.getElementById("vendas-tabela"), {
      columns: [
        { key: "ano_mes", label: "Mês" },
        { key: "receita", label: "Receita", num: true, fmt: fmtBRL },
        { key: "qtd_vendida", label: "Qtd. vendida", num: true, fmt: fmtNum },
        { key: "variacao_receita_yoy", label: "Receita YoY", num: true, fmt: (v) => fmtPct(v) },
        { key: "variacao_qtd_yoy", label: "Qtd. YoY", num: true, fmt: (v) => fmtPct(v) },
      ],
      rows: vm,
      pageSize: 12,
      download: "vendas_mensais_derivado.csv",
      notaFonte: "YoY em branco em 2024: não há 2023 na base (DADO AUSENTE). Fonte: outputs/tables/vendas_mensais.csv.",
    });
  }

  /* ---------- 4. Lojas ---------- */

  function renderLojas() {
    const anual = DATA.lojas_yoy_anual_2025;
    barChartH(document.getElementById("lojas-graf-anual"), {
      items: anual.map((r) => ({
        rotulo: r.COD_EMPRESA + " — " + r.CD_CIDADE + "/" + r.CD_ESTADO,
        valor: r.variacao_receita_yoy,
        extra: [
          { valor: fmtBRLCompacto(r.receita), nome: "receita 2025" },
          { valor: fmtBRLCompacto(r.receita_ano_anterior), nome: "receita 2024" },
        ],
      })),
      cor: COR.s1,
      nomeSerie: "Variação anual 2025 vs 2024",
      xFmt: (v) => fmtPct(v, 0),
      margemEsq: 215,
    });

    const seletor = document.getElementById("lojas-seletor");
    seletor.textContent = "";
    const lojas = [...anual].sort((a, b) => a.COD_EMPRESA - b.COD_EMPRESA);
    for (const loja of lojas) {
      seletor.append(el("option", { value: loja.COD_EMPRESA }, loja.COD_EMPRESA + " — " + loja.CD_CIDADE + "/" + loja.CD_ESTADO));
    }
    function desenharLoja() {
      const cod = Number(seletor.value);
      const linhas = DATA.same_store.filter((r) => r.COD_EMPRESA === cod && r.ANO_MES.startsWith("2025"));
      linhas.sort((a, b) => a.ANO_MES.localeCompare(b.ANO_MES));
      lineChart(document.getElementById("lojas-graf-mensal"), {
        labels: linhas.map((r) => r.ANO_MES),
        series: [
          { nome: "Receita 2025", cor: COR.s1, values: linhas.map((r) => r.receita) },
          { nome: "Mesmo mês de 2024", cor: COR.neutro, values: linhas.map((r) => r.receita_ano_anterior) },
        ],
        yFmt: fmtBRLCompacto,
        tipFmt: fmtBRL,
        mostrarCadaN: 1,
      });
      const naoComparaveis = linhas.filter((r) => !r.loja_comparavel_yoy).length;
      document.getElementById("lojas-seletor-info").textContent =
        naoComparaveis > 0 ? naoComparaveis + " mês(es) sem base comparável no ano anterior." : "12 meses comparáveis YoY.";
    }
    seletor.addEventListener("change", desenharLoja);
    desenharLoja();

    renderTable(document.getElementById("lojas-tabela"), {
      columns: [
        { key: "ANO_MES", label: "Mês" },
        { key: "COD_EMPRESA", label: "Loja", num: true },
        { key: "CD_CIDADE", label: "Cidade" },
        { key: "receita", label: "Receita", num: true, fmt: fmtBRL },
        { key: "receita_ano_anterior", label: "Receita ano ant.", num: true, fmt: fmtBRL },
        { key: "variacao_receita_yoy", label: "YoY", num: true, fmt: (v) => fmtPct(v) },
        { key: "dias_com_venda", label: "Dias c/ venda", num: true },
        { key: "dias_com_venda_ano_anterior", label: "Dias ano ant.", num: true },
        { key: "skus_vendidos", label: "SKUs", num: true, fmt: fmtNum },
        { key: "loja_comparavel_yoy", label: "Comparável", fmt: (v) => (v ? "Sim" : "Não") },
      ],
      rows: DATA.same_store,
      filtro: { chave: "COD_EMPRESA", rotulo: "Loja" },
      pageSize: 12,
      download: "vendas_same_store_yoy_derivado.csv",
      notaFonte:
        "Dias com venda contam dias com ao menos uma linha observada; não substituem calendário operacional (DADO AUSENTE). Fonte: outputs/tables/vendas_same_store_yoy.csv.",
    });
  }

  /* ---------- 5. Categorias ---------- */

  function renderCategorias() {
    const classif = DATA.classificacao_categorias_mensal_2025;
    const chaves = ["queda generalizada", "queda concentrada", "crescimento", "comportamento atipico"];
    const cores = [COR.s1, COR.s2, COR.s3, COR.s4];
    const extras = [...new Set(classif.flatMap((r) => Object.keys(r)))].filter((k) => k !== "periodo" && !chaves.includes(k));
    const todas = [...chaves, ...extras];
    stackedColumns(document.getElementById("categorias-graf-classif"), {
      labels: classif.map((r) => r.periodo),
      series: todas.map((chave, i) => ({
        nome: chave,
        cor: cores[i] || COR.s5,
        values: classif.map((r) => r[chave] || 0),
      })),
      yFmt: fmtNum,
    });
    renderTable(document.getElementById("categorias-tabela"), {
      columns: [
        { key: "periodicidade", label: "Periodicidade" },
        { key: "periodo", label: "Período" },
        { key: "NIVEL_1", label: "Categoria (NIVEL_1)" },
        { key: "receita", label: "Receita", num: true, fmt: fmtBRL },
        { key: "receita_ano_anterior", label: "Receita ano ant.", num: true, fmt: fmtBRL },
        { key: "variacao_receita_yoy", label: "YoY", num: true, fmt: (v) => fmtPct(v) },
        { key: "contribuicao_queda_periodo", label: "Contrib. queda", num: true, fmt: (v) => fmtPct(v) },
        { key: "classificacao_categoria", label: "Classificação" },
      ],
      rows: DATA.categorias_yoy,
      filtro: { chave: "classificacao_categoria", rotulo: "Classificação" },
      pageSize: 12,
      download: "vendas_categorias_yoy_derivado.csv",
      notaFonte:
        "Mês compara com mesmo mês do ano anterior; trimestre com mesmo trimestre. 2024 fica como dados insuficientes (sem 2023 — DADO AUSENTE). Fonte: outputs/tables/vendas_categorias_yoy.csv.",
    });
  }

  /* ---------- 6. Sortimento ---------- */

  function renderSortimento() {
    const s = DATA.sortimento;
    const labels = s.map((r) => r.ANO_MES);
    lineChart(document.getElementById("sortimento-graf"), {
      labels,
      series: [
        { nome: "SKUs observados", cor: COR.s1, values: s.map((r) => r.skus_observados) },
        { nome: "SKUs esperados (média bootstrap)", cor: COR.s2, values: s.map((r) => r.skus_esperados_media) },
      ],
      banda: {
        nome: "faixa esperada p05–p95",
        cor: "var(--wash-2)",
        inferior: s.map((r) => r.skus_esperados_p05),
        superior: s.map((r) => r.skus_esperados_p95),
      },
      yFmt: fmtNum,
      tipFmt: fmtNum,
    });
    lineChart(document.getElementById("sortimento-graf-linhas"), {
      labels,
      series: [{ nome: "Linhas de venda diárias", cor: COR.s1, values: s.map((r) => r.linhas_venda_diarias) }],
      yFmt: fmtNumCompacto,
      tipFmt: fmtNum,
    });
    renderTable(document.getElementById("sortimento-tabela"), {
      columns: [
        { key: "ANO_MES", label: "Mês" },
        { key: "skus_observados", label: "SKUs observados", num: true, fmt: fmtNum },
        { key: "skus_esperados_media", label: "Esperados (média)", num: true, fmt: (v) => (v === null || v === undefined ? "—" : fmtNum(v)) },
        { key: "skus_esperados_p05", label: "p05", num: true, fmt: (v) => (v === null || v === undefined ? "—" : fmtNum(v)) },
        { key: "skus_esperados_p95", label: "p95", num: true, fmt: (v) => (v === null || v === undefined ? "—" : fmtNum(v)) },
        { key: "linhas_venda_diarias", label: "Linhas diárias", num: true, fmt: fmtNum },
        { key: "status_sortimento_controlado", label: "Status" },
      ],
      rows: s,
      pageSize: 24,
      busca: false,
      download: "sortimento_controlado_derivado.csv",
      notaFonte:
        "Status DADO AUSENTE em 2024: sem referência de 2023 para o mix. Fonte: outputs/tables/sortimento_controlado_por_volume.csv.",
    });
  }

  /* ---------- 7. Compras / gap ---------- */

  function renderCompras() {
    const total = DATA.cobertura.periodo_total;
    const resumo = DATA.gaps.resumo;
    const grade = document.getElementById("compras-kpis");
    grade.textContent = "";
    grade.append(
      tile({
        rotulo: "Saídas observadas (un. estoque)",
        valor: fmtNumCompacto(total.total_vendido_estoque),
        selo: "fato",
        nota: {
          formula: "sum(QUANTIDADE_VENDIDA × CONVERSAO_VENDA_PARA_ARMAZENAGEM)",
          fonte: "outputs/tables/compras_coverage_audit.csv",
          unidade: "unidade de armazenagem",
          confianca: "Alta",
          limitacao: "Venda observada não é demanda real.",
        },
      }),
      tile({
        rotulo: "Entradas conhecidas",
        valor: fmtNumCompacto(total.entradas_conhecidas_estoque),
        delta: "estoque inicial " + fmtNumCompacto(total.estoque_inicial_estoque) + " + compras " + fmtNumCompacto(total.compras_registradas_estoque),
        selo: "fato",
        nota: {
          formula: "estoque_inicial + QUANTIDADE_COMPRA × CONVERSAO_COMPRA_ARMAZENAGEM",
          fonte: "outputs/tables/compras_coverage_audit.csv",
          unidade: "unidade de armazenagem",
          confianca: "Alta como soma; baixa como universo de entradas",
          limitacao: "DADO AUSENTE: transferências, ajustes, devoluções e inventário final.",
        },
      }),
      tile({
        rotulo: "Cobertura das entradas",
        valor: fmtPct(total.pct_cobertura_entradas),
        delta: total.classificacao_confiabilidade,
        selo: "bloqueado",
        seloTexto: "Bloqueado p/ causal",
        nota: {
          formula: "entradas_conhecidas / saídas observadas",
          fonte: "outputs/tables/compras_coverage_audit.csv",
          unidade: "%",
          confianca: "Alta como medição",
          limitacao: "Cobertura baixa bloqueia conclusão causal sobre reposição (H5).",
        },
      }),
      tile({
        rotulo: "Pares com venda sem compra registrada",
        valor: fmtPct(total.pct_skus_venda_sem_compra),
        delta: "21.118 de 21.387 pares com venda",
        selo: "fato",
      }),
      tile({
        rotulo: "Pares com gap contábil > 0",
        valor: fmtNum(resumo.n_pares_com_gap_positivo) + " de " + fmtNum(resumo.n_pares_produto_loja),
        selo: "fato",
        nota: {
          formula: "max(vendas − estoque inicial − compras, 0) por produto × loja",
          fonte: "outputs/tables/gaps_saldo_contabil_estoque.csv",
          unidade: "pares produto × loja",
          confianca: "Alta como gap contábil",
          limitacao: "Gap contábil não é ruptura física comprovada.",
        },
      }),
      tile({
        rotulo: "Eventos com saldo projetado negativo",
        valor: fmtPct(total.pct_eventos_saldo_projetado_negativo),
        delta: "interpretação obrigatória: gap contábil",
        selo: "fato",
      })
    );

    const porMes = DATA.cobertura.por_mes;
    columnChart(document.getElementById("compras-graf-mes"), {
      labels: porMes.map((r) => r.chave_agrupamento),
      values: porMes.map((r) => r.pct_cobertura_entradas),
      cor: COR.s1,
      nomeSerie: "Cobertura das entradas",
      yFmt: (v) => fmtPct(v, 0),
      tipFmt: fmtPct,
      refLinha: { valor: 1, rotulo: "100% = entradas cobrem saídas" },
    });
    const cidadePorLoja = {};
    for (const r of DATA.lojas_yoy_anual_2025) cidadePorLoja[r.COD_EMPRESA] = r.CD_CIDADE + "/" + r.CD_ESTADO;
    const porLoja = [...DATA.cobertura.por_loja].sort((a, b) => a.pct_cobertura_entradas - b.pct_cobertura_entradas);
    barChartH(document.getElementById("compras-graf-loja"), {
      items: porLoja.map((r) => ({
        rotulo: r.chave_agrupamento + " — " + (cidadePorLoja[r.chave_agrupamento] || ""),
        valor: r.pct_cobertura_entradas,
        extra: [{ valor: r.classificacao_confiabilidade, nome: "classificação" }],
      })),
      cor: COR.s1,
      nomeSerie: "Cobertura das entradas",
      xFmt: (v) => fmtPct(v, 0),
      margemEsq: 215,
    });
    renderTable(document.getElementById("compras-tabela-gaps"), {
      columns: [
        { key: "COD_EMPRESA", label: "Loja", num: true },
        { key: "CODIGO", label: "Código", num: true },
        { key: "DESCRICAO", label: "Descrição" },
        { key: "NIVEL_1", label: "Categoria" },
        { key: "ESTOQUE_INICIAL", label: "Estoque inicial", num: true, fmt: fmtNum },
        { key: "COMPRAS_REGISTRADAS_ESTOQUE", label: "Compras", num: true, fmt: fmtNum },
        { key: "VENDAS_ESTOQUE", label: "Vendas", num: true, fmt: fmtNum },
        { key: "SALDO_PROJETADO_CONTABIL", label: "Saldo projetado", num: true, fmt: fmtNum },
        { key: "GAP_CONTABIL_ESTOQUE", label: "Gap contábil", num: true, fmt: fmtNum },
      ],
      rows: DATA.gaps.top,
      pageSize: 10,
      download: "gaps_top50_derivado.csv",
      notaFonte: resumo.nota_amostra,
    });
    document.getElementById("compras-gaps-interpretacao").textContent =
      "Interpretação obrigatória: " + resumo.interpretacao_saldo_negativo + " Possíveis causas: " + resumo.possiveis_causas_gap;
  }

  /* ---------- 8. Precificacao ---------- */

  function renderPrecificacao() {
    const c = DATA.correlacao;
    const grade = document.getElementById("precificacao-kpis");
    grade.textContent = "";
    grade.append(
      tile({
        rotulo: "Candidatos a investigação de preço",
        valor: fmtNum(c.n_produtos),
        selo: "exploratoria",
        nota: {
          formula: "corr(preço médio mensal, quantidade mensal) < −0,4 com n_obs ≥ 8",
          fonte: "outputs/tables/produtos_correlacao_preco_volume_negativa.csv",
          unidade: "produtos",
          confianca: "Baixa (associação observacional)",
          limitacao: "Correlação preço-volume não é elasticidade nem prova causalidade.",
        },
      }),
      tile({
        rotulo: "Limiar de triagem",
        valor: "corr < −0,4",
        delta: "mínimo de 8 observações produto-mês — limiar herdado, NÃO VALIDADO com o negócio",
        selo: "naovalidado",
      }),
      tile({
        rotulo: "Decisão de repricing",
        valor: "BLOQUEADO",
        delta: "faltam margem, concorrência, campanhas e teste controlado (DADO AUSENTE)",
        selo: "bloqueado",
      })
    );
    columnChart(document.getElementById("precificacao-graf-hist"), {
      labels: c.histograma.map((r) => r.faixa),
      values: c.histograma.map((r) => r.produtos),
      cor: COR.s1,
      nomeSerie: "Produtos na faixa",
      yFmt: fmtNum,
      mostrarCadaN: 2,
    });
    renderTable(document.getElementById("precificacao-tabela"), {
      columns: [
        { key: "CODIGO", label: "Código", num: true },
        { key: "DESCRICAO", label: "Descrição" },
        { key: "NIVEL_1", label: "Categoria" },
        { key: "correlacao_preco_volume", label: "Correlação", num: true, fmt: (v) => nfNum2.format(v) },
        { key: "n_obs", label: "Obs.", num: true },
        { key: "receita_total", label: "Receita 24m", num: true, fmt: fmtBRL },
        { key: "nivel_confianca", label: "Confiança" },
        { key: "tipo_analise", label: "Tipo de análise" },
      ],
      rows: c.rows,
      pageSize: 10,
      download: "correlacao_preco_volume_derivado.csv",
      notaFonte: "Fonte: outputs/tables/produtos_correlacao_preco_volume_negativa.csv — associação exploratória, sem leitura causal.",
    });
  }

  /* ---------- 9. Projecao e triagens ---------- */

  function renderProjecao() {
    const t = DATA.projecao.totais;
    const grade = document.getElementById("projecao-kpis");
    grade.textContent = "";
    const variacao = t.venda_observada_projetada_2026_total / t.venda_media_anual_observada_historica_total - 1;
    grade.append(
      tile({
        rotulo: "Venda observada projetada 2026",
        valor: fmtNumCompacto(t.venda_observada_projetada_2026_total) + " un.",
        delta: fmtPct(variacao) + " vs média anual histórica observada (" + fmtNumCompacto(t.venda_media_anual_observada_historica_total) + " un.)",
        selo: "exploratoria",
        nota: {
          formula: "tendência linear por produto × índice sazonal por categoria",
          fonte: "outputs/tables/projecao_venda_observada_2026.csv",
          unidade: "unidade de estoque",
          confianca: "Baixa",
          limitacao: "Projeta venda observada (cenário-piso), não demanda potencial; herda censura do histórico.",
        },
      }),
      tile({
        rotulo: "Compra bruta sugerida (triagem)",
        valor: fmtNumCompacto(t.compra_bruta_sugerida_total) + " un.",
        delta: "= projeção + estoque de segurança 30d (limiar NÃO VALIDADO)",
        selo: "triagem",
        nota: {
          formula: "venda_observada_projetada_2026 + estoque_seguranca_30d",
          fonte: "outputs/tables/projecao_venda_observada_2026.csv",
          unidade: "unidade de estoque",
          confianca: "Baixa",
          limitacao: "Piso para triagem; não desconta estoque atual; não é pedido de compra.",
        },
      }),
      tile({
        rotulo: "Compra líquida sugerida",
        valor: "BLOQUEADO",
        delta: fmtNum(t.n_compra_liquida_bloqueada) + " de " + fmtNum(t.n_produtos) + " produtos sem estoque atual confiável",
        selo: "bloqueado",
        nota: {
          formula: "max(projeção + estoque segurança − estoque disponível, 0) — exige estoque confiável",
          fonte: "outputs/tables/projecao_venda_observada_2026.csv (flag_nao_calcular_compra_liquida_por_estoque_inconfiavel)",
          unidade: "unidade de estoque",
          confianca: "BLOQUEADO",
          limitacao: "DADO AUSENTE: estoque atual confiável, lead time, lote mínimo, fornecedor.",
        },
      })
    );
    renderTable(document.getElementById("projecao-tabela"), {
      columns: [
        { key: "CODIGO", label: "Código", num: true },
        { key: "DESCRICAO", label: "Descrição" },
        { key: "NIVEL_1", label: "Categoria" },
        { key: "venda_observada_projetada_2026", label: "Projeção 2026", num: true, fmt: fmtNum },
        { key: "venda_media_anual_observada_historica", label: "Média anual hist.", num: true, fmt: fmtNum },
        { key: "compra_bruta_sugerida", label: "Compra bruta (triagem)", num: true, fmt: fmtNum },
        { key: "status_compra_liquida", label: "Compra líquida" },
        { key: "nivel_confianca", label: "Confiança" },
      ],
      rows: DATA.projecao.top,
      pageSize: 10,
      download: "projecao_top30_derivado.csv",
      notaFonte: "Top 30 por projeção; 2.729 produtos no CSV completo. Unidade: unidade de estoque.",
    });

    const seletor = document.getElementById("triagem-seletor");
    const detalhe = document.getElementById("triagem-detalhe");
    function desenharTriagem() {
      const tri = DATA.triagens[seletor.value];
      detalhe.textContent = "";
      const chips = el("div", { class: "grade-tiles" });
      chips.append(
        tile({ rotulo: "Linhas na triagem", valor: fmtNum(tri.n_linhas), selo: "triagem" }),
        tile({
          rotulo: "Nível de confiança",
          valor: Object.entries(tri.nivel_confianca).map(([k, v]) => k + ": " + fmtNum(v)).join(" · "),
          selo: "exploratoria",
        }),
        tile({
          rotulo: "Status de decisão",
          valor: Object.keys(tri.status_decisao_final).join(" · "),
          delta: "toda linha exige validação antes de qualquer ação",
          selo: "bloqueado",
        })
      );
      detalhe.append(chips);
      const dl = el("dl", { class: "glossario" });
      const campos = [
        ["Regra usada", tri.regra_usada],
        ["Evidência (exemplos na amostra abaixo)", null],
        ["Dado faltante", tri.dado_faltante],
        ["Limitação", tri.limitacao],
        ["Risco de decisão", tri.risco_decisao],
        ["Próxima validação necessária", tri.proxima_validacao_necessaria],
        ["Ação recomendada", tri.acao_recomendada],
      ];
      for (const [titulo, valores] of campos) {
        if (!valores) continue;
        dl.append(el("dt", null, titulo));
        for (const v of valores) dl.append(el("dd", null, v));
      }
      detalhe.append(dl);
      const alvoTabela = el("div");
      detalhe.append(alvoTabela);
      renderTable(alvoTabela, {
        columns: [
          { key: "CODIGO", label: "Código", num: true },
          { key: "DESCRICAO", label: "Descrição" },
          { key: "NIVEL_1", label: "Categoria" },
          { key: "nivel_confianca", label: "Confiança" },
          { key: "status_decisao_final", label: "Status de decisão" },
          { key: "evidencia", label: "Evidência" },
        ],
        rows: tri.amostra,
        pageSize: 8,
        download: "triagem_" + seletor.value + "_amostra.csv",
        notaFonte: tri.nota_amostra + " Fonte: " + tri.arquivo + ".",
      });
    }
    seletor.addEventListener("change", desenharTriagem);
    desenharTriagem();
  }

  /* ---------- 10. Hipoteses ---------- */

  function renderHipoteses() {
    const filtro = document.getElementById("hipoteses-filtro");
    const statusUnicos = [...new Set(DATA.hipoteses.map((h) => h.status))];
    for (const s of statusUnicos) filtro.append(el("option", { value: s }, s));
    const alvo = document.getElementById("hipoteses-tabela");
    const camposCsv = [
      "hipotese_id",
      "hipotese",
      "status",
      "nivel_confianca",
      "resultado",
      "conclusao_permitida",
      "conclusao_proibida",
      "evidencia_usada",
      "dados_ausentes",
    ];
    function desenhar() {
      const rows = filtro.value ? DATA.hipoteses.filter((h) => h.status === filtro.value) : DATA.hipoteses;
      alvo.textContent = "";
      const barra = el("div", { class: "tabela-barra" });
      barra.append(el("span", { class: "contagem" }, fmtNum(rows.length) + " de " + fmtNum(DATA.hipoteses.length) + " hipóteses"));
      const botao = el("button", { type: "button" }, "Baixar CSV (derivado)");
      botao.addEventListener("click", () => {
        const cab = camposCsv.map((c) => '"' + c + '"').join(",");
        const corpo = rows
          .map((r) => camposCsv.map((c) => '"' + String(r[c] ?? "").replaceAll('"', '""') + '"').join(","))
          .join("\n");
        const blob = new Blob(["﻿" + cab + "\n" + corpo], { type: "text/csv;charset=utf-8" });
        const a = el("a", { href: URL.createObjectURL(blob), download: "hypothesis_status_derivado.csv" });
        a.click();
        URL.revokeObjectURL(a.href);
      });
      barra.append(botao);
      alvo.append(barra);
      for (const h of rows) {
        const item = el("article", { class: "hipotese-item" });
        item.append(
          el(
            "div",
            { class: "hipotese-cab" },
            el("h4", null, h.hipotese_id + " — " + h.hipotese),
            selo(SELO_POR_STATUS_HIPOTESE[h.status] || "ausente", h.status),
            el("span", { class: "hipotese-confianca" }, "Confiança: " + h.nivel_confianca)
          ),
          el("p", { class: "hipotese-resultado" }, h.resultado),
          el(
            "div",
            { class: "hipotese-conclusoes" },
            el(
              "div",
              { class: "conclusao permitida" },
              el("span", { class: "rotulo-mini" }, "Conclusão permitida"),
              el("p", null, h.conclusao_permitida)
            ),
            el(
              "div",
              { class: "conclusao proibida" },
              el("span", { class: "rotulo-mini" }, "Conclusão proibida"),
              el("p", null, h.conclusao_proibida)
            )
          ),
          el("p", { class: "hipotese-meta" }, "Evidência: " + h.evidencia_usada),
          el("p", { class: "hipotese-meta" }, "Dados ausentes: " + h.dados_ausentes)
        );
        alvo.append(item);
      }
      alvo.append(
        el(
          "p",
          { class: "nota-limitacao" },
          "Fonte: outputs/tables/hypothesis_status.csv. A conclusão proibida delimita o que o dado NÃO autoriza afirmar."
        )
      );
    }
    filtro.addEventListener("change", desenhar);
    desenhar();
  }

  /* ---------- 11. Glossario ---------- */

  function renderGlossario() {
    const alvoSelos = document.getElementById("glossario-selos");
    alvoSelos.textContent = "";
    const descricoes = {
      fato: "Medição validada por contrato, teste e outputs reexecutáveis. Ainda assim é descritiva — não autoriza leitura causal.",
      descritiva: "O dado observado sustenta a afirmação descritiva, sem implicar causa.",
      exploratoria: "Sinal ou associação que prioriza investigação; não prova efeito.",
      triagem: "Lista de priorização com dados críticos ausentes; exige validação item a item.",
      bloqueado: "Decisão ou conclusão impossível com os dados atuais.",
      ausente: "Informação que não existe no repositório (DADO AUSENTE).",
      naovalidado: "Afirmação plausível sem evidência reexecutável (NÃO VALIDADO).",
    };
    const dl = el("dl", { class: "glossario" });
    for (const [tipo, desc] of Object.entries(descricoes)) {
      dl.append(el("dt", null, selo(tipo)), el("dd", null, desc));
    }
    alvoSelos.append(dl);

    const formulas = [
      ["Receita bruta", "sum(QUANTIDADE_VENDIDA × PRECO_UNIT_MEDIO)"],
      ["Quantidade em unidade de armazenagem", "sum(QUANTIDADE_VENDIDA × CONVERSAO_VENDA_PARA_ARMAZENAGEM)"],
      ["Compras em unidade de armazenagem", "sum(QUANTIDADE_COMPRA × CONVERSAO_COMPRA_ARMAZENAGEM)"],
      ["Entradas conhecidas", "estoque_inicial + compras_armazenagem"],
      ["Saldo projetado contábil", "estoque_inicial + compras_armazenagem − vendas_armazenagem"],
      ["Gap contábil de estoque", "max(vendas − estoque_inicial − compras, 0)"],
      ["Variação percentual", "(valor_atual − valor_base) / valor_base"],
      ["Ticket médio por linha diária", "receita_bruta / linhas_venda_diarias (não é ticket de cupom)"],
      ["Preço médio vendido", "receita_bruta / quantidade_vendida"],
      ["Correlação preço-volume", "corr(preço_médio_mensal, quantidade_mensal), n_obs ≥ 8"],
      ["Cobertura de compras", "lojas_com_compra / total_lojas; produtos_com_compra / total_produtos"],
    ];
    const alvoFormulas = document.getElementById("glossario-formulas");
    alvoFormulas.textContent = "";
    const dlFormulas = el("dl", { class: "glossario" });
    for (const [nome, formula] of formulas) {
      dlFormulas.append(el("dt", null, nome), el("dd", null, el("code", null, formula)));
    }
    alvoFormulas.append(dlFormulas);
  }

  /* ---------------- roteador ---------------- */

  const PAGINAS = [
    "sumario",
    "qualidade",
    "vendas",
    "lojas",
    "categorias",
    "sortimento",
    "compras",
    "precificacao",
    "projecao",
    "hipoteses",
    "glossario",
  ];

  function navegar() {
    const alvo = (location.hash || "#/sumario").replace("#/", "");
    const pagina = PAGINAS.includes(alvo) ? alvo : "sumario";
    for (const id of PAGINAS) {
      document.getElementById(id).classList.toggle("ativa", id === pagina);
    }
    document.querySelectorAll("nav.abas a").forEach((a) => {
      a.classList.toggle("ativo", a.getAttribute("href") === "#/" + pagina);
    });
    window.scrollTo({ top: 0 });
  }

  renderSumario();
  renderQualidade();
  renderVendas();
  renderLojas();
  renderCategorias();
  renderSortimento();
  renderCompras();
  renderPrecificacao();
  renderProjecao();
  renderHipoteses();
  renderGlossario();
  window.addEventListener("hashchange", navegar);
  navegar();
})();
