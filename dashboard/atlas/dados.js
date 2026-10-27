// Acesso aos dados do atlas: carrega sob demanda e indexa séries por território.
// Uma série é uma lista de pontos ordenados por ano:
// { ano, valor, taxa, populacao, situacao, meses, suficiente }

const SC = { id: "SC", nome: "Santa Catarina", tipo: "uf" };
const BRASIL = { id: "BR", nome: "Brasil", tipo: "brasil" };

export function criarDados(manifesto) {
  const indicadores = new Map(manifesto.indicadores.map((i) => [i.id, i]));
  const promessas = new Map();
  let indiceNacional = null;

  function buscar(url) {
    if (!promessas.has(url)) {
      promessas.set(
        url,
        fetch(url).then((r) => {
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

  async function nacional() {
    if (!indiceNacional) {
      const tabela = await buscar("data/nacional.json");
      indiceNacional = indexar(
        tabela,
        (l, c) => `${l[c.indicador]}|${l[c.id_territorio]}|${l[c.sexo]}`,
      );
    }
    return indiceNacional;
  }

  async function municipio(id) {
    const tabela = await buscar(`data/municipio/${id}.json`);
    return indexar(tabela, (l, c) => `${l[c.indicador]}|${l[c.sexo]}`);
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
    SC,
    BRASIL,
  };
}
