// Seções de conteúdo: cartões da Visão geral e gráfico de Evolução.
// Reagem ao evento "atlas:estado" disparado por app.js.

import { criarDados } from "./dados.js";
import { fmtInteiro, fmtTaxa, graficoLinhas, miniatura } from "./graficos.js";

const CARTOES = [
  { id: "sinesp_homicidio_doloso", titulo: "Homicídio doloso" },
  { id: "sim_agressao", titulo: "Mortes por agressão" },
  { id: "sinesp_tentativa_de_homicidio", titulo: "Tentativa de homicídio" },
  { id: "sinesp_violencia_sexual_policial_soma_das_classificacoes", titulo: "Estupro e estupro de vulnerável" },
  { id: "sim_suicidio", titulo: "Mortes por suicídio" },
  { id: "sinesp_pessoa_desaparecida", titulo: "Pessoas desaparecidas" },
];

const SEXOS = [
  ["total", "Todos"],
  ["feminino", "Feminino"],
  ["masculino", "Masculino"],
];
const MEDIDAS = [
  ["taxa", "Taxa por 100 mil"],
  ["absoluto", "Valor absoluto"],
];

const $ = (id) => document.getElementById(id);

function tag(nome, classe, texto) {
  const e = document.createElement(nome);
  if (classe) e.className = classe;
  if (texto !== undefined) e.textContent = texto;
  return e;
}

export function iniciarSecoes({ manifesto, territorioPorId, definirEstado, obterEstado }) {
  const dados = criarDados(manifesto);
  let rodada = 0;

  /* Controles segmentados (sexo e medida) */
  function segmentado(opcoes, atual, chave, rotulo) {
    const grupo = tag("div", "segmented");
    grupo.setAttribute("role", "group");
    grupo.setAttribute("aria-label", rotulo);
    for (const [valor, texto] of opcoes) {
      const b = tag("button", "", texto);
      b.type = "button";
      b.setAttribute("aria-pressed", String(valor === atual));
      b.addEventListener("click", () => definirEstado({ [chave]: valor }));
      grupo.append(b);
    }
    return grupo;
  }

  function desenharControles(estado) {
    $("controles-sexo-geral").replaceChildren(segmentado(SEXOS, estado.s, "s", "Sexo"));
    $("controles-evolucao").replaceChildren(
      campoIndicador(estado),
      segmentado(SEXOS, estado.s, "s", "Sexo"),
      segmentado(MEDIDAS, estado.m, "m", "Medida"),
    );
  }

  function campoIndicador(estado) {
    const rotulo = tag("label", "select-field");
    rotulo.append(tag("span", "", "Indicador"));
    const seletor = document.createElement("select");
    const eixos = new Map();
    for (const ind of manifesto.indicadores) {
      if (!eixos.has(ind.eixo)) eixos.set(ind.eixo, []);
      eixos.get(ind.eixo).push(ind);
    }
    for (const [eixo, lista] of eixos) {
      const grupo = document.createElement("optgroup");
      grupo.label = eixo;
      for (const ind of lista) {
        const o = tag("option", "", `${ind.rotulo} (${ind.fonte})`);
        o.value = ind.id;
        o.selected = ind.id === estado.i;
        grupo.append(o);
      }
      seletor.append(grupo);
    }
    seletor.addEventListener("change", () => definirEstado({ i: seletor.value }));
    rotulo.append(seletor);
    return rotulo;
  }

  /* Cartões */
  function variacao(pontos, campo) {
    const validos = pontos.filter((p) => p[campo] != null && p[campo] > 0);
    if (validos.length < 2) return null;
    const ini = validos[0];
    const fim = validos[validos.length - 1];
    return { de: ini.ano, pct: ((fim[campo] - ini[campo]) / ini[campo]) * 100 };
  }

  async function montarCartao(config, estado, territorio) {
    const ind = dados.indicador(config.id);
    const { territorio: efetivo, substituido } = dados.resolver(territorio, config.id);
    const serie = await dados.serie(efetivo, config.id, estado.s);
    const consolidados = serie.filter((p) => p.situacao === "consolidado");
    const comTaxa = consolidados.filter((p) => p.taxa != null);
    const alvo = comTaxa.length ? comTaxa[comTaxa.length - 1] : consolidados[consolidados.length - 1];

    const botao = tag("button", "card");
    botao.type = "button";
    botao.append(
      tag("p", "card-source", `${ind.fonte} · ${ind.base_territorial}`),
      tag("h3", "card-title", config.titulo),
    );
    if (!alvo) {
      botao.append(tag("p", "card-empty", "Sem dados para este recorte."));
      return botao;
    }
    const campo = alvo.taxa != null ? "taxa" : "valor";
    const ate = serie.filter((p) => p.ano <= alvo.ano && p.situacao === "consolidado");
    botao.append(
      tag("p", "card-value", fmtInteiro.format(alvo.valor)),
      tag("p", "card-year", `${ind.unidade} em ${alvo.ano}`),
    );
    if (alvo.taxa != null) botao.append(tag("p", "card-rate", `${fmtTaxa.format(alvo.taxa)} por 100 mil`));
    else botao.append(tag("p", "card-rate", "Taxa indisponível"));

    const insuficiente = efetivo.tipo === "municipio" && !alvo.suficiente;
    const v = insuficiente ? null : variacao(ate, campo);
    if (insuficiente) botao.append(tag("p", "card-flag", "Poucos casos: interpretar com cautela"));
    else if (v) {
      const sinal = v.pct > 0 ? "+" : "";
      botao.append(tag("p", "card-var", `${sinal}${fmtInteiro.format(Math.round(v.pct))}% desde ${v.de}`));
    }
    botao.append(miniatura(ate.filter((p) => p[campo] != null).map((p) => ({ ano: p.ano, y: p[campo] }))));
    if (substituido) botao.append(tag("p", "card-flag", "Total de Santa Catarina: sem detalhe municipal"));
    botao.addEventListener("click", () => {
      definirEstado({ i: config.id });
      $("evolucao").scrollIntoView();
    });
    botao.setAttribute("aria-label", `${config.titulo}: ver evolução`);
    return botao;
  }

  async function desenharCartoes(estado, territorio, minhaRodada) {
    const cartoes = await Promise.all(CARTOES.map((c) => montarCartao(c, estado, territorio)));
    if (minhaRodada !== rodada) return;
    $("cartoes").replaceChildren(...cartoes);
  }

  /* Evolução */
  function pontosDaSerie(serie, medida) {
    return serie
      .filter((p) => (medida === "taxa" ? p.taxa != null : p.valor != null))
      .map((p) => ({
        ano: p.ano,
        y: medida === "taxa" ? p.taxa : p.valor,
        valor: p.valor,
        taxa: p.taxa,
        situacao: p.situacao,
        oco: !p.suficiente,
      }));
  }

  async function desenharEvolucao(estado, territorio, minhaRodada) {
    const ind = dados.indicador(estado.i);
    const { territorio: efetivo, substituido } = dados.resolver(territorio, estado.i);
    const alvos = [efetivo];
    if (estado.m === "taxa") {
      for (const extra of [dados.SC, dados.BRASIL]) {
        if (!alvos.some((t) => t.id === extra.id)) alvos.push(extra);
      }
    }
    const series = [];
    for (const [i, t] of alvos.entries()) {
      const bruta = await dados.serie(t, estado.i, estado.s);
      series.push({ id: t.id, nome: t.nome, classe: i === 0 ? "s-a" : t.id === "SC" ? "s-b" : "s-c", pontos: pontosDaSerie(bruta, estado.m), bruta });
    }
    if (minhaRodada !== rodada) return;

    $("titulo-grafico").textContent = `${ind.rotulo}: ${efetivo.nome}`;
    const area = $("grafico");
    const comDados = series.filter((s) => s.pontos.length);
    if (!comDados.length) {
      area.replaceChildren(tag("p", "chart-empty", "Não há dados deste indicador para o recorte escolhido."));
    } else {
      const unidade = estado.m === "taxa" ? "por 100 mil" : ind.unidade;
      graficoLinhas(area, comDados, {
        formatoY: (v) => (estado.m === "taxa" ? fmtTaxa.format(v) : fmtInteiro.format(v)),
        descricao: `Gráfico de linhas: ${ind.rotulo} (${unidade}) em ${alvos.map((t) => t.nome).join(", ")}`,
      });
    }

    const notas = [];
    if (substituido) notas.push(`Este indicador não tem detalhe municipal. Mostrando o total de ${efetivo.nome}.`);
    if (estado.m === "absoluto" && alvos.length === 1) {
      notas.push("Valores absolutos de territórios de tamanhos diferentes não se comparam no mesmo eixo. Escolha a taxa para comparar com Santa Catarina e o Brasil.");
    }
    if (estado.m === "taxa") {
      notas.push("Taxas existem apenas até 2024, por falta de população estimada para 2025 em diante. Passe o mouse sobre os pontos para ver os valores absolutos.");
    }
    if (efetivo.tipo === "municipio") {
      notas.push("Pontos vazados indicam anos com menos de 5 casos: a taxa oscila muito em municípios pequenos.");
    }
    if (series.some((s) => s.pontos.some((p) => p.situacao !== "consolidado"))) {
      notas.push("Trechos tracejados: 2025 é preliminar e 2026 é parcial, até agosto.");
    }
    notas.push(ind.ressalva);
    $("notas-grafico").replaceChildren(...notas.map((n) => tag("li", "", n)));

    desenharTabela(comDados, estado, ind);
  }

  function desenharTabela(series, estado, ind) {
    const tabela = tag("table", "data-table");
    const cabeca = document.createElement("tr");
    cabeca.append(tag("th", "", "Ano"));
    for (const s of series) {
      cabeca.append(tag("th", "", `${s.nome}: ${ind.unidade}`), tag("th", "", `${s.nome}: taxa por 100 mil`));
    }
    const thead = document.createElement("thead");
    thead.append(cabeca);
    tabela.append(thead);
    const anos = [...new Set(series.flatMap((s) => s.bruta.map((p) => p.ano)))].sort((a, b) => a - b);
    const corpo = document.createElement("tbody");
    for (const ano of anos) {
      const tr = document.createElement("tr");
      tr.append(tag("th", "", String(ano)));
      for (const s of series) {
        const p = s.bruta.find((q) => q.ano === ano);
        tr.append(
          tag("td", "", p ? fmtInteiro.format(p.valor) : "—"),
          tag("td", "", p && p.taxa != null ? fmtTaxa.format(p.taxa) : "—"),
        );
      }
      corpo.append(tr);
    }
    tabela.append(corpo);
    $("tabela-grafico").replaceChildren(tabela);
  }

  async function atualizar(estado) {
    const minhaRodada = ++rodada;
    const territorio = territorioPorId(estado.t);
    desenharControles(estado);
    try {
      await Promise.all([
        desenharCartoes(estado, territorio, minhaRodada),
        desenharEvolucao(estado, territorio, minhaRodada),
      ]);
    } catch (erro) {
      console.error(erro);
      $("cartoes").replaceChildren(tag("p", "chart-empty", "Não foi possível carregar os dados deste território."));
    }
  }

  document.addEventListener("atlas:estado", (e) => atualizar(e.detail));
  matchMedia("(max-width: 599px)").addEventListener("change", () => atualizar(obterEstado()));
}
