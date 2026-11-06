// Gráficos em SVG puro: miniatura de série e gráfico de linhas com tooltip.

const NS = "http://www.w3.org/2000/svg";

function el(nome, atributos = {}, filhos = []) {
  const no = document.createElementNS(NS, nome);
  for (const [k, v] of Object.entries(atributos)) no.setAttribute(k, v);
  for (const f of filhos) no.append(f);
  return no;
}

export const fmtInteiro = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });
export const fmtTaxa = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });

function coordenadas(geometria) {
  const saida = [];
  const visitar = (item) => {
    if (typeof item?.[0] === "number") saida.push(item);
    else if (Array.isArray(item)) item.forEach(visitar);
  };
  visitar(geometria.coordinates);
  return saida;
}

function quantil(valores, proporcao) {
  if (!valores.length) return 0;
  return valores[Math.min(valores.length - 1, Math.floor((valores.length - 1) * proporcao))];
}

function caminhoGeometria(geometria, X, Y) {
  const poligonos = geometria.type === "Polygon" ? [geometria.coordinates] : geometria.coordinates;
  return poligonos.flatMap((poligono) => poligono.map((anel) => {
    const pontos = anel.map(([lon, lat], i) => `${i ? "L" : "M"}${X(lon).toFixed(1)},${Y(lat).toFixed(1)}`);
    return `${pontos.join("")}Z`;
  })).join("");
}

export function mapaMunicipal(container, malha, linhas, opcoes) {
  container.replaceChildren();
  const L = 720;
  const A = 520;
  const margem = 14;
  const todosPontos = malha.features.flatMap((f) => coordenadas(f.geometry));
  const longitudes = todosPontos.map((p) => p[0]);
  const latitudes = todosPontos.map((p) => p[1]);
  const minLon = Math.min(...longitudes);
  const maxLon = Math.max(...longitudes);
  const minLat = Math.min(...latitudes);
  const maxLat = Math.max(...latitudes);
  const escala = Math.min((L - 2 * margem) / (maxLon - minLon), (A - 2 * margem) / (maxLat - minLat));
  const largura = (maxLon - minLon) * escala;
  const altura = (maxLat - minLat) * escala;
  const sobraX = (L - largura) / 2;
  const sobraY = (A - altura) / 2;
  const X = (lon) => sobraX + (lon - minLon) * escala;
  const Y = (lat) => sobraY + (maxLat - lat) * escala;

  const porId = new Map(linhas.map((linha) => [linha.id, linha]));
  const valores = linhas.filter((linha) => linha.suficiente && linha.taxa != null).map((linha) => linha.taxa).sort((a, b) => a - b);
  const limites = [0.2, 0.4, 0.6, 0.8].map((p) => quantil(valores, p));
  const classe = (linha) => {
    if (!linha?.suficiente || linha.taxa == null) return "map-insuficiente";
    let indice = 0;
    while (indice < limites.length && linha.taxa > limites[indice]) indice += 1;
    return `map-q${indice}`;
  };

  const svg = el("svg", {
    viewBox: `0 0 ${L} ${A}`,
    class: "municipal-map",
    role: "img",
    "aria-label": opcoes.descricao,
  });
  const padrao = el("pattern", { id: "map-hatch", width: "7", height: "7", patternUnits: "userSpaceOnUse", patternTransform: "rotate(45)" });
  padrao.append(
    el("rect", { width: "7", height: "7", class: "map-hatch-bg" }),
    el("line", { x1: "0", y1: "0", x2: "0", y2: "7", class: "map-hatch-line" }),
  );
  svg.append(el("defs", {}, [padrao]));
  const dica = document.createElement("div");
  dica.className = "map-tip";
  dica.hidden = true;

  const mostrar = (evento, feature, linha) => {
    dica.replaceChildren();
    dica.append(Object.assign(document.createElement("strong"), { textContent: feature.properties.nome }));
    const texto = document.createElement("span");
    if (!linha?.suficiente || linha.taxa == null) texto.textContent = "Dado insuficiente para comparação";
    else texto.textContent = `${fmtTaxa.format(linha.taxa)} por 100 mil, ${fmtInteiro.format(linha.valor)} registros`;
    dica.append(texto);
    dica.hidden = false;
    const caixa = container.getBoundingClientRect();
    const alvo = evento.currentTarget.getBoundingClientRect();
    const clientX = Number.isFinite(evento.clientX) && evento.clientX > 0 ? evento.clientX : alvo.right;
    const clientY = Number.isFinite(evento.clientY) && evento.clientY > 0 ? evento.clientY : alvo.top;
    dica.style.left = `${Math.max(8, Math.min(clientX - caixa.left + 12, caixa.width - 220))}px`;
    dica.style.top = `${Math.max(8, clientY - caixa.top - 24)}px`;
  };
  const esconder = () => { dica.hidden = true; };

  for (const feature of malha.features) {
    const linha = porId.get(String(feature.id));
    const path = el("path", {
      d: caminhoGeometria(feature.geometry, X, Y),
      class: `map-municipio ${classe(linha)}${feature.id === opcoes.selecionado ? " selecionado" : ""}`,
      tabindex: "0",
      role: "button",
      "aria-label": linha?.suficiente && linha.taxa != null
        ? `${feature.properties.nome}: ${fmtTaxa.format(linha.taxa)} por 100 mil, ${fmtInteiro.format(linha.valor)} registros`
        : `${feature.properties.nome}: dado insuficiente`,
    });
    path.addEventListener("pointermove", (evento) => mostrar(evento, feature, linha));
    path.addEventListener("pointerleave", esconder);
    path.addEventListener("focus", (evento) => mostrar(evento, feature, linha));
    path.addEventListener("blur", esconder);
    path.addEventListener("click", () => opcoes.aoSelecionar(String(feature.id)));
    path.addEventListener("keydown", (evento) => {
      if (evento.key === "Enter" || evento.key === " ") {
        evento.preventDefault();
        opcoes.aoSelecionar(String(feature.id));
      }
    });
    svg.append(path);
  }
  container.append(svg, dica);
  return { limites, elegiveis: valores.length };
}

function escalaNice(maximo) {
  if (maximo <= 0) return { topo: 1, passo: 0.25 };
  const bruto = maximo / 4;
  const potencia = 10 ** Math.floor(Math.log10(bruto));
  const fracao = bruto / potencia;
  const passoBase = fracao <= 1 ? 1 : fracao <= 2 ? 2 : fracao <= 2.5 ? 2.5 : fracao <= 5 ? 5 : 10;
  const passo = passoBase * potencia;
  return { topo: Math.ceil(maximo / passo) * passo, passo };
}

/** Miniatura: pontos [{ano, y}] já filtrados. */
export function miniatura(pontos) {
  const L = 120;
  const A = 34;
  const svg = el("svg", { viewBox: `0 0 ${L} ${A}`, class: "spark", "aria-hidden": "true", focusable: "false" });
  if (pontos.length < 2) return svg;
  const ys = pontos.map((p) => p.y);
  const min = Math.min(...ys);
  const max = Math.max(...ys);
  const x0 = pontos[0].ano;
  const x1 = pontos[pontos.length - 1].ano;
  const X = (a) => 3 + ((a - x0) / (x1 - x0 || 1)) * (L - 6);
  const Y = (y) => A - 4 - ((y - min) / (max - min || 1)) * (A - 10);
  const d = pontos.map((p, i) => `${i ? "L" : "M"}${X(p.ano).toFixed(1)},${Y(p.y).toFixed(1)}`).join("");
  svg.append(el("path", { d, class: "spark-line", fill: "none" }));
  const ultimo = pontos[pontos.length - 1];
  svg.append(el("circle", { cx: X(ultimo.ano), cy: Y(ultimo.y), r: 2.6, class: "spark-dot" }));
  return svg;
}

/**
 * Gráfico de linhas.
 * series: [{ id, nome, classe, pontos: [{ano, y, situacao, valor, taxa, oco}] }]
 * opcoes: { rotuloY, formatoY, descricao }
 */
export function graficoLinhas(container, series, opcoes) {
  container.replaceChildren();
  const compacto = window.innerWidth < 600;
  const L = compacto ? 400 : 960;
  const A = compacto ? 270 : 300;
  const m = compacto ? { e: 44, d: 94, t: 14, b: 30 } : { e: 54, d: 132, t: 16, b: 34 };
  const todos = series.flatMap((s) => s.pontos);
  const anos = todos.map((p) => p.ano);
  const x0 = Math.min(...anos);
  const x1 = Math.max(...anos);
  const { topo, passo } = escalaNice(Math.max(...todos.map((p) => p.y)));
  const X = (a) => m.e + ((a - x0) / (x1 - x0 || 1)) * (L - m.e - m.d);
  const Y = (y) => A - m.b - (y / topo) * (A - m.t - m.b);

  const svg = el("svg", {
    viewBox: `0 0 ${L} ${A}`, class: "chart", role: "img",
    "aria-label": opcoes.descricao,
  });

  for (let v = 0; v <= topo + passo / 2; v += passo) {
    svg.append(
      el("line", { x1: m.e, x2: L - m.d, y1: Y(v), y2: Y(v), class: "grid" }),
      Object.assign(el("text", { x: m.e - 8, y: Y(v) + 4, class: "tick", "text-anchor": "end" }), {
        textContent: opcoes.formatoY(v),
      }),
    );
  }
  const passoAno = anos.length > 10 ? 2 : 1;
  for (let a = x0; a <= x1; a += 1) {
    if (a !== x1 && ((a - x0) % passoAno || x1 - a < passoAno)) continue;
    svg.append(
      Object.assign(el("text", { x: X(a), y: A - 10, class: "tick", "text-anchor": "middle" }), { textContent: a }),
    );
  }

  const rotulosFim = [];
  for (const s of series) {
    const validos = s.pontos;
    if (!validos.length) continue;
    for (let i = 1; i < validos.length; i++) {
      const a = validos[i - 1];
      const b = validos[i];
      if (b.ano - a.ano !== 1) continue;
      const tracejado = b.situacao !== "consolidado";
      svg.append(
        el("line", {
          x1: X(a.ano), y1: Y(a.y), x2: X(b.ano), y2: Y(b.y),
          class: `serie ${s.classe}${tracejado ? " tracejado" : ""}`,
        }),
      );
    }
    for (const p of validos) {
      svg.append(
        el("circle", {
          cx: X(p.ano), cy: Y(p.y), r: 3.6,
          class: `ponto ${s.classe}${p.oco ? " oco" : ""}`,
        }),
      );
    }
    const fim = validos[validos.length - 1];
    rotulosFim.push({ nome: s.nome, classe: s.classe, x: X(fim.ano) + 9, y: Y(fim.y) });
  }
  rotulosFim.sort((a, b) => a.y - b.y);
  for (let i = 1; i < rotulosFim.length; i++) {
    if (rotulosFim[i].y - rotulosFim[i - 1].y < 15) rotulosFim[i].y = rotulosFim[i - 1].y + 15;
  }
  for (const r of rotulosFim) {
    svg.append(Object.assign(el("text", { x: r.x, y: r.y + 4, class: `rotulo ${r.classe}` }), { textContent: r.nome }));
  }

  const guia = el("line", { y1: m.t, y2: A - m.b, class: "guia", visibility: "hidden" });
  const area = el("rect", { x: m.e, y: m.t, width: L - m.e - m.d, height: A - m.t - m.b, fill: "transparent" });
  svg.append(guia, area);

  const dica = document.createElement("div");
  dica.className = "chart-tip";
  dica.hidden = true;
  const caixa = document.createElement("div");
  caixa.className = "chart-box";
  caixa.append(svg, dica);
  container.append(caixa);

  const mover = (evento) => {
    const r = svg.getBoundingClientRect();
    const xSvg = ((evento.clientX - r.left) / r.width) * L;
    const ano = Math.round(x0 + ((xSvg - m.e) / (L - m.e - m.d)) * (x1 - x0));
    if (ano < x0 || ano > x1) return sair();
    const linhas = series
      .map((s) => ({ s, p: s.pontos.find((q) => q.ano === ano) }))
      .filter((x) => x.p);
    if (!linhas.length) return sair();
    guia.setAttribute("x1", X(ano));
    guia.setAttribute("x2", X(ano));
    guia.setAttribute("visibility", "visible");
    dica.replaceChildren();
    const titulo = document.createElement("strong");
    titulo.textContent = String(ano);
    dica.append(titulo);
    for (const { s, p } of linhas) {
      const linha = document.createElement("div");
      linha.className = `tip-linha ${s.classe}`;
      const partes = [`${s.nome}: ${fmtInteiro.format(p.valor)}`];
      if (p.taxa != null) partes.push(`${fmtTaxa.format(p.taxa)} por 100 mil`);
      if (p.situacao !== "consolidado") partes.push(p.situacao);
      linha.textContent = partes.join(" · ");
      dica.append(linha);
    }
    dica.hidden = false;
    const esquerda = (X(ano) / L) * r.width;
    const direita = esquerda > r.width * 0.6;
    dica.style.left = direita ? "auto" : `${esquerda + 12}px`;
    dica.style.right = direita ? `${r.width - esquerda + 12}px` : "auto";
  };
  const sair = () => {
    guia.setAttribute("visibility", "hidden");
    dica.hidden = true;
  };
  area.addEventListener("pointermove", mover);
  area.addEventListener("pointerleave", sair);
}
