import { iniciarSecoes } from "./secoes.js";

// Esqueleto do atlas: estado na URL, seletor de território, tema e navegação.
// As seções de conteúdo escutam o evento "atlas:estado" (document) e leem
// o estado por obterEstado(). Nenhum gráfico é desenhado nesta etapa.

const UFS = {
  AC: "Acre", AL: "Alagoas", AM: "Amazonas", AP: "Amapá", BA: "Bahia",
  CE: "Ceará", DF: "Distrito Federal", ES: "Espírito Santo", GO: "Goiás",
  MA: "Maranhão", MG: "Minas Gerais", MS: "Mato Grosso do Sul",
  MT: "Mato Grosso", PA: "Pará", PB: "Paraíba", PE: "Pernambuco", PI: "Piauí",
  PR: "Paraná", RJ: "Rio de Janeiro", RN: "Rio Grande do Norte",
  RO: "Rondônia", RR: "Roraima", RS: "Rio Grande do Sul", SC: "Santa Catarina",
  SE: "Sergipe", SP: "São Paulo", TO: "Tocantins",
};

const SEXOS = { total: "Todos", feminino: "Feminino", masculino: "Masculino" };
const ANO_MIN = 2015;
const ANO_MAX = 2026;
const MEDIDAS = ["taxa", "absoluto"];
const PADRAO = { t: "SC", i: "sim_agressao", a: "2024", s: "total", m: "taxa" };

let manifesto = null;
let territorios = [];
let estado = { ...PADRAO };

const $ = (id) => document.getElementById(id);

function semAcento(texto) {
  return texto.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

function montarTerritorios() {
  territorios = [
    { id: "BR", nome: "Brasil", tipo: "brasil", grupo: "País" },
    ...Object.entries(UFS).map(([id, nome]) => ({ id, nome, tipo: "uf", grupo: "Estados" })),
    ...manifesto.municipios.map((m) => ({
      id: m.id, nome: m.nome, tipo: "municipio", grupo: "Municípios de Santa Catarina",
    })),
  ];
}

function territorioPorId(id) {
  return territorios.find((t) => t.id === id);
}

function validar(bruto) {
  const saida = { ...PADRAO };
  if (territorioPorId(bruto.t)) saida.t = bruto.t;
  if (manifesto.indicadores.some((i) => i.id === bruto.i)) saida.i = bruto.i;
  const ano = Number(bruto.a);
  if (Number.isInteger(ano) && ano >= ANO_MIN && ano <= ANO_MAX) saida.a = String(ano);
  if (bruto.s in SEXOS) saida.s = bruto.s;
  if (MEDIDAS.includes(bruto.m)) saida.m = bruto.m;
  return saida;
}

function lerUrl() {
  const p = new URLSearchParams(location.search);
  return validar({ t: p.get("t"), i: p.get("i"), a: p.get("a"), s: p.get("s"), m: p.get("m") });
}

function escreverUrl(modo) {
  const p = new URLSearchParams();
  for (const chave of Object.keys(PADRAO)) {
    if (estado[chave] !== PADRAO[chave]) p.set(chave, estado[chave]);
  }
  const consulta = p.toString();
  const destino = `${location.pathname}${consulta ? `?${consulta}` : ""}${location.hash}`;
  history[modo === "push" ? "pushState" : "replaceState"](null, "", destino);
}

export function obterEstado() {
  return { ...estado };
}

export function definirEstado(parcial, modo = "replace") {
  const proximo = validar({ ...estado, ...parcial });
  if (JSON.stringify(proximo) === JSON.stringify(estado)) return;
  estado = proximo;
  escreverUrl(modo);
  atualizar();
}

function preposicao(territorio) {
  return territorio.tipo === "brasil" ? "no" : "em";
}

function atualizar() {
  const territorio = territorioPorId(estado.t);
  const indicador = manifesto.indicadores.find((i) => i.id === estado.i);
  $("territorio-atual").textContent = territorio.nome;
  $("titulo-pagina").textContent = `Violência ${preposicao(territorio)} ${territorio.nome}`;
  document.title = `${territorio.nome} · Territórios da Violência`;

  const tipo = { brasil: "País", uf: "Estado", municipio: "Município de Santa Catarina" }[territorio.tipo];
  const linhas = [
    ["Território", `${territorio.nome} (${tipo})`],
    ["Indicador", `${indicador.rotulo} · ${indicador.fonte}`],
    ["Base territorial", indicador.base_territorial],
    ["Ano", estado.a],
    ["Sexo", SEXOS[estado.s]],
  ];
  const lista = $("estado-atual");
  lista.replaceChildren(
    ...linhas.flatMap(([rotulo, valor]) => {
      const dt = document.createElement("dt");
      dt.textContent = rotulo;
      const dd = document.createElement("dd");
      dd.textContent = valor;
      return [dt, dd];
    }),
  );
  desenharLista($("busca-territorio").value);
  document.dispatchEvent(new CustomEvent("atlas:estado", { detail: obterEstado() }));
}

/* Seletor de território */
function desenharLista(consulta = "") {
  const termo = semAcento(consulta.trim());
  const filtrados = territorios.filter((t) => !termo || semAcento(t.nome).includes(termo));
  const lista = $("lista-territorios");
  lista.replaceChildren();
  if (!filtrados.length) {
    const vazio = document.createElement("p");
    vazio.className = "territory-empty";
    vazio.textContent = "Nenhum território encontrado. Os municípios disponíveis são os de Santa Catarina.";
    lista.append(vazio);
    return;
  }
  let grupoAtual = null;
  for (const t of filtrados) {
    if (t.grupo !== grupoAtual) {
      grupoAtual = t.grupo;
      const titulo = document.createElement("p");
      titulo.className = "territory-group";
      titulo.textContent = grupoAtual;
      lista.append(titulo);
    }
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "territory-option";
    botao.setAttribute("role", "option");
    botao.setAttribute("aria-selected", String(t.id === estado.t));
    botao.dataset.id = t.id;
    botao.textContent = t.nome;
    lista.append(botao);
  }
}

function configurarSeletor() {
  const dialogo = $("dialogo-territorio");
  const busca = $("busca-territorio");
  $("abrir-territorio").addEventListener("click", () => {
    busca.value = "";
    desenharLista();
    dialogo.showModal();
    busca.focus();
  });
  busca.addEventListener("input", () => desenharLista(busca.value));
  $("lista-territorios").addEventListener("click", (evento) => {
    const opcao = evento.target.closest(".territory-option");
    if (!opcao) return;
    definirEstado({ t: opcao.dataset.id }, "push");
    dialogo.close();
  });
  dialogo.addEventListener("click", (evento) => {
    if (evento.target === dialogo) dialogo.close();
  });
}

/* Tema */
function temaEfetivo() {
  const manual = document.documentElement.dataset.tema;
  if (manual) return manual;
  return matchMedia("(prefers-color-scheme: dark)").matches ? "escuro" : "claro";
}

function configurarTema() {
  $("alternar-tema").addEventListener("click", () => {
    const proximo = temaEfetivo() === "escuro" ? "claro" : "escuro";
    document.documentElement.dataset.tema = proximo;
    try {
      localStorage.setItem("atlas-tema", proximo);
    } catch (e) {}
  });
}

/* Navegação: destaca a seção visível */
function configurarNavegacao() {
  const links = [...document.querySelectorAll(".nav-link")];
  const secoes = links.map((a) => document.querySelector(a.getAttribute("href")));
  const marcar = (id) => {
    for (const a of links) {
      if (a.getAttribute("href") === `#${id}`) a.setAttribute("aria-current", "true");
      else a.removeAttribute("aria-current");
    }
  };
  const observador = new IntersectionObserver(
    (entradas) => {
      const visivel = entradas.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
      if (visivel) marcar(visivel.target.id);
    },
    { rootMargin: "-20% 0px -65% 0px" },
  );
  secoes.filter(Boolean).forEach((s) => observador.observe(s));
}

function tamanho(bytes) {
  return bytes >= 1048576 ? `${(bytes / 1048576).toFixed(1)} MB` : `${Math.round(bytes / 1024)} KB`;
}

function preencherMetadados() {
  const [ano, mes, dia] = manifesto.atualizado_em.split("-");
  $("meta-atualizado").textContent = `${dia}/${mes}/${ano}`;
  const lista = $("lista-downloads");
  lista.replaceChildren(
    ...manifesto.downloads.map((d) => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = d.arquivo;
      a.textContent = `${d.fonte} (CSV compactado, ${tamanho(d.bytes)})`;
      li.append(a);
      return li;
    }),
  );
}

async function iniciar() {
  configurarTema();
  try {
    const resposta = await fetch("data/manifesto.json");
    if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`);
    manifesto = await resposta.json();
  } catch (erro) {
    $("titulo-pagina").textContent = "Não foi possível carregar os dados";
    $("meta-atualizado").textContent = "indisponível";
    console.error(erro);
    return;
  }
  montarTerritorios();
  estado = lerUrl();
  preencherMetadados();
  configurarSeletor();
  configurarNavegacao();
  iniciarSecoes({ manifesto, territorioPorId, definirEstado, obterEstado });
  window.addEventListener("popstate", () => {
    estado = lerUrl();
    atualizar();
  });
  atualizar();
}

iniciar();
