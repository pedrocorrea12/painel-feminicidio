// Acesso aos dados do atlas: carrega sob demanda e indexa séries por território.
// Uma série é uma lista de pontos ordenados por ano:
// { ano, valor, taxa, populacao, situacao, meses, suficiente }

const SC = { id: "SC", nome: "Santa Catarina", tipo: "uf" };
const BRASIL = { id: "BR", nome: "Brasil", tipo: "brasil" };

export function criarDados(manifesto) {
  const indicadores = new Map(manifesto.indicadores.map((i) => [i.id, i]));
  const promessas = new Map();
  const mapas = new Map();
  let indiceNacional = null;
  let linhasNacionais = null;

  function buscar(url) {
    if (!promessas.has(url)) {
      promessas.set(
        url,
        fetch(url, { cache: "no-store" }).then((r) => {
          if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`);
          return r.json();
        }),
      );
    }
    return promessas.get(url);
  }

  function indexar(tabela, chaveLinha) {
    const indice = new Map();
    const col = Object.fromEntries(tabela.colunas.map((nome, posicao) => [nome, posicao]));
    for (const linha of tabela.linhas) {
      const chave = chaveLinha(linha, col);
      if (!indice.has(chave)) indice.set(chave, []);
      indice.get(chave).push({
        ano: linha[col.ano],
        valor: linha[col.valor],
        taxa: linha[col.taxa],
        populacao: linha[col.populacao],
        situacao: linha[col.situacao_dado],
        meses: col.meses_observados === undefined ? null : linha[col.meses_observados],
        suficiente: col.suficiente === undefined ? true : linha[col.suficiente],
        suficiente3a: col.suficiente_3a === undefined ? true : linha[col.suficiente_3a],
      });
    }
    for (const serie of indice.values()) serie.sort((a, b) => a.ano - b.ano);
    return indice;
  }

  function paraObjetos(tabela) {
    return tabela.linhas.map((linha) => Object.fromEntries(
      tabela.colunas.map((nome, posicao) => [nome, linha[posicao]]),
    ));
  }

  async function nacional() {
    if (!indiceNacional) {
      const tabela = await buscar("data/nacional.json");
      linhasNacionais = paraObjetos(tabela);
      indiceNacional = indexar(
        tabela,
        (l, c) => `${l[c.indicador]}|${l[c.id_territorio]}|${l[c.sexo]}`,
      );
    }
    return indiceNacional;
  }

  async function comparacao(indicadorId, sexo, ano) {
    await nacional();
    return linhasNacionais.filter((linha) =>
      linha.indicador === indicadorId
      && linha.sexo === sexo
      && linha.ano === ano
      && linha.taxa != null,
    );
  }

  async function municipio(id) {
    const tabela = await buscar(`data/municipio/${id}.json`);
    return indexar(tabela, (l, c) => `${l[c.indicador]}|${l[c.sexo]}`);
  }

  async function mapa(indicadorId) {
    const ind = indicadores.get(indicadorId);
    if (!ind?.arquivo_mapa) return null;
    if (!mapas.has(indicadorId)) {
      mapas.set(indicadorId, buscar(ind.arquivo_mapa).then((tabela) => {
        const col = Object.fromEntries(tabela.colunas.map((nome, posicao) => [nome, posicao]));
        return tabela.linhas.map((linha) => ({
          id: linha[col.id_territorio],
          nome: linha[col.territorio],
          ano: linha[col.ano],
          sexo: linha[col.sexo],
          valor: linha[col.valor],
          taxa: linha[col.taxa],
          suficiente: linha[col.suficiente],
          valor3a: linha[col.valor_3a],
          taxa3a: linha[col.taxa_3a],
          suficiente3a: linha[col.suficiente_3a],
          situacao: linha[col.situacao_dado],
        }));
      }));
    }
    return mapas.get(indicadorId);
  }

  return {
    indicador: (id) => indicadores.get(id),
    // Indicadores sem detalhe municipal usam o total de Santa Catarina.
    resolver(territorio, indicadorId) {
      const ind = indicadores.get(indicadorId);
      if (territorio.tipo === "municipio" && !ind.municipal) {
        return { territorio: SC, substituido: true };
      }
      return { territorio, substituido: false };
    },
    async serie(territorio, indicadorId, sexo) {
      if (territorio.tipo === "municipio") {
        const indice = await municipio(territorio.id);
        return indice.get(`${indicadorId}|${sexo}`) ?? [];
      }
      const indice = await nacional();
      return indice.get(`${indicadorId}|${territorio.id}|${sexo}`) ?? [];
    },
    mapa,
    malha: () => buscar("data/malha_sc.json"),
    comparacao,
    idade: async (indicadorId, ano) => {
      const tabela = await buscar("data/idade.json");
      return paraObjetos(tabela).filter((linha) =>
        linha.indicador === indicadorId && linha.ano === ano,
      );
    },
    mensal: async (indicadorId, sexo) => {
      const tabela = await buscar("data/mensal.json");
      return paraObjetos(tabela).filter((linha) =>
        linha.indicador === indicadorId && linha.sexo === sexo,
      );
    },
    desigualdades: async () => {
      const tabelas = await buscar("data/desigualdades.json");
      return Object.fromEntries(
        Object.entries(tabelas).map(([nome, tabela]) => [nome, paraObjetos(tabela)]),
      );
    },
    SC,
    BRASIL,
  };
}
