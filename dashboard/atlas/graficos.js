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
  const L = compacto ? 400 : 760;
  const A = compacto ? 340 : 380;
  const m = compacto ? { e: 44, d: 100, t: 14, b: 30 } : { e: 54, d: 128, t: 16, b: 34 };
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
