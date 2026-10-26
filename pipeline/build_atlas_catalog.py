"""Gera o catálogo de indicadores e a matriz de disponibilidade do atlas."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "gold" / "atlas"
SINESP_ANUAL = ROOT / "data" / "gold" / "sinesp" / "sinesp_sc_brasil_anual.csv"
SINESP_UF = ROOT / "data" / "gold" / "sinesp" / "sinesp_uf_anual.csv"
SINESP_MUNICIPIOS = ROOT / "data" / "gold" / "sinesp" / "sinesp_sc_municipios_anual.csv"
POPULACAO_FEMININA = ROOT / "data" / "silver" / "populacao_feminina_municipio.parquet"
POPULACAO_TOTAL = ROOT / "data" / "silver" / "populacao_municipio_ano.parquet"
POPULACAO_SEXO = ROOT / "data" / "silver" / "populacao_municipio_sexo_ano.parquet"
POPULACAO_IDADE = ROOT / "data" / "silver" / "populacao_municipio_idade_ano.parquet"
SINESP_COBERTURA = ROOT / "data" / "gold" / "atlas" / "sinesp_cobertura_evento_resumo.csv"
SINESP_TERRITORIO = ROOT / "data" / "gold" / "atlas" / "sinesp_prioridade_territorio_ano.csv"
SINESP_MENSAL = ROOT / "data" / "gold" / "atlas" / "sinesp_prioridade_mensal.csv"

CATALOGO = GOLD / "catalogo_indicadores.csv"
MATRIZ_FONTES = GOLD / "matriz_disponibilidade_fontes.csv"
RESUMO = GOLD / "resumo_catalogo.json"


EVENTOS_PESSOA = {
    "Feminicídio",
    "Tentativa de feminicídio",
    "Homicídio doloso",
    "Tentativa de homicídio",
    "Lesão corporal seguida de morte",
    "Roubo seguido de morte (latrocínio)",
    "Estupro",
    "Estupro de vulnerável",
    "Morte por intervenção de Agente do Estado",
    "Morte de Agente do Estado",
    "Suicídio",
    "Suicídio de Agente do Estado",
    "Mortes no trânsito",
    "Morte no trânsito ou em decorrência dele (exceto homicídio doloso)",
    "Mortes a esclarecer (sem indício de crime)",
    "Pessoa Desaparecida",
    "Pessoa Localizada",
}

EVENTOS_PESO = {"Apreensão de Cocaína", "Apreensão de Maconha"}

EIXO_EVENTO = {
    "Feminicídio": "Violência contra a mulher",
    "Tentativa de feminicídio": "Violência contra a mulher",
    "Homicídio doloso": "Violência letal",
    "Tentativa de homicídio": "Violência letal",
    "Lesão corporal seguida de morte": "Violência letal",
    "Roubo seguido de morte (latrocínio)": "Violência letal",
    "Morte por intervenção de Agente do Estado": "Violência letal",
    "Morte de Agente do Estado": "Violência letal",
    "Mortes a esclarecer (sem indício de crime)": "Violência letal",
    "Estupro": "Violência sexual",
    "Estupro de vulnerável": "Violência sexual",
    "Suicídio": "Violência autoprovocada",
    "Suicídio de Agente do Estado": "Violência autoprovocada",
    "Pessoa Desaparecida": "Desaparecimentos",
    "Pessoa Localizada": "Desaparecimentos",
    "Mortes no trânsito": "Trânsito",
    "Morte no trânsito ou em decorrência dele (exceto homicídio doloso)": "Trânsito",
    "Furto de veículo": "Patrimônio",
    "Roubo de veículo": "Patrimônio",
    "Roubo de carga": "Patrimônio",
    "Roubo a instituição financeira": "Patrimônio",
    "Tráfico de drogas": "Drogas e armas",
    "Apreensão de Cocaína": "Drogas e armas",
    "Apreensão de Maconha": "Drogas e armas",
    "Arma de Fogo Apreendida": "Drogas e armas",
    "Mandado de prisão cumprido": "Atividade policial",
    "Atendimento pré-hospitalar": "Emergência e resgate",
    "Busca e salvamento": "Emergência e resgate",
    "Combate a incêndios": "Emergência e resgate",
    "Realização de vistorias": "Emergência e resgate",
    "Emissão de Alvarás de licença": "Emergência e resgate",
}

PRIORIDADE_EVENTO = {
    "Feminicídio": 1,
    "Tentativa de feminicídio": 1,
    "Homicídio doloso": 1,
    "Tentativa de homicídio": 1,
    "Estupro": 1,
    "Estupro de vulnerável": 1,
    "Suicídio": 1,
    "Pessoa Desaparecida": 1,
    "Pessoa Localizada": 1,
    "Lesão corporal seguida de morte": 2,
    "Roubo seguido de morte (latrocínio)": 2,
    "Morte por intervenção de Agente do Estado": 2,
    "Mortes a esclarecer (sem indício de crime)": 2,
}


def _sim_nao(valor: bool) -> str:
    return "sim" if valor else "não"


def _linha(
    *,
    eixo: str,
    indicador: str,
    fonte: str,
    unidade: str,
    periodo_bronze: str,
    periodo_processado: str,
    brasil: str,
    uf: str,
    municipio_sc: str,
    mensal: str,
    sexo: str,
    idade: str,
    raca: str,
    denominador: str,
    territorio_referencia: str,
    prontidao: str,
    prioridade: int,
    transformacao: str,
    ressalva: str,
) -> dict:
    return {
        "eixo": eixo,
        "indicador": indicador,
        "fonte": fonte,
        "unidade": unidade,
        "periodo_bronze": periodo_bronze,
        "periodo_processado": periodo_processado,
        "brasil": brasil,
        "uf": uf,
        "municipio_sc": municipio_sc,
        "mensal": mensal,
        "sexo": sexo,
        "idade": idade,
        "raca": raca,
        "denominador_disponivel": denominador,
        "territorio_referencia": territorio_referencia,
        "prontidao": prontidao,
        "prioridade": prioridade,
        "transformacao_necessaria": transformacao,
        "ressalva_principal": ressalva,
    }


def _catalogo_sinesp() -> list[dict]:
    anual = pd.read_csv(SINESP_ANUAL)
    uf = pd.read_csv(SINESP_UF)
    municipios = pd.read_csv(SINESP_MUNICIPIOS)
    cobertura = pd.read_csv(SINESP_COBERTURA).set_index("indicador")
    eventos = sorted(anual["evento"].dropna().unique())
    linhas = []
    for evento in eventos:
        pessoa = evento in EVENTOS_PESSOA
        if evento in EVENTOS_PESO:
            unidade = "quilogramas apreendidos"
        elif pessoa:
            unidade = "vítimas"
        else:
            unidade = "ocorrências ou registros"

        anos = anual.loc[anual.evento.eq(evento), "ano"]
        anos_uf = uf.loc[uf.evento.eq(evento), "ano"]
        anos_mun = municipios.loc[municipios.evento.eq(evento), "ano"]
        periodo = f"{int(anos.min())} a {int(anos.max())}"
        periodo_uf = f"{int(anos_uf.min())} a {int(anos_uf.max())}" if len(anos_uf) else "indisponível"
        periodo_mun = f"{int(anos_mun.min())} a {int(anos_mun.max())}" if len(anos_mun) else "indisponível"

        prontidao = "pronto com ressalva"
        transformacao = "validar continuidade anual e meses informados"
        ressalva = "registro policial pelo local do fato"
        if evento in {"Feminicídio", "Tentativa de feminicídio"}:
            prontidao = "pronto"
            transformacao = "reutilizar a camada Gold existente"
        elif evento in {"Estupro", "Estupro de vulnerável"}:
            transformacao = "somar estupro e estupro de vulnerável para a série comparável"
            ressalva = "há quebra de classificação em Santa Catarina em 2020"
        elif evento in {"Homicídio doloso", "Tentativa de homicídio", "Suicídio", "Pessoa Desaparecida", "Pessoa Localizada"}:
            transformacao = "criar camada Gold temática e validar cobertura por UF"

        if evento in cobertura.index:
            validacao = cobertura.loc[evento]
            transformacao = "reutilizar a Gold temática validada do Sinesp"
            ressalva = str(validacao["ressalva_principal"])
            if not bool(validacao["sc_tem_cobertura_municipal"]):
                periodo_mun = "indisponível"

        linhas.append(
            _linha(
                eixo=EIXO_EVENTO.get(evento, "Outros registros"),
                indicador=evento,
                fonte="Sinesp VDE",
                unidade=unidade,
                periodo_bronze=periodo,
                periodo_processado=periodo,
                brasil="sim",
                uf=f"sim, {periodo_uf}",
                municipio_sc=f"sim, {periodo_mun}",
                mensal="sim",
                sexo="sim" if pessoa else "não se aplica",
                idade="limitado a alguns eventos",
                raca="não",
                denominador="população total, por sexo e por idade até 2024",
                territorio_referencia="local do fato",
                prontidao=prontidao,
                prioridade=PRIORIDADE_EVENTO.get(evento, 3),
                transformacao=transformacao,
                ressalva=ressalva,
            )
        )
    linhas.append(
        _linha(
            eixo="Violência sexual",
            indicador="Violência sexual policial, soma das classificações",
            fonte="Sinesp VDE",
            unidade="vítimas",
            periodo_bronze="2019 a 2026",
            periodo_processado="2019 a 2026",
            brasil="sim",
            uf="sim, 2019 a 2026",
            municipio_sc="indisponível",
            mensal="sim",
            sexo="sim",
            idade="limitado a alguns eventos",
            raca="não",
            denominador="população total e por sexo até 2024",
            territorio_referencia="local do fato",
            prontidao="pronto com ressalva",
            prioridade=1,
            transformacao="somar Estupro e Estupro de vulnerável na Gold temática validada",
            ressalva="a soma não elimina quebras de classificação entre UFs e anos",
        )
    )
    return linhas


def _catalogo_sim() -> list[dict]:
    comum = dict(
        fonte="SIM",
        unidade="óbitos",
        periodo_bronze="2015 a 2026",
        brasil="sim",
        uf="sim",
        municipio_sc="sim",
        mensal="possível a partir da data do óbito",
        sexo="sim no arquivo bruto",
        idade="sim",
        raca="sim",
        territorio_referencia="residência e local da ocorrência disponíveis no bruto",
    )
    return [
        _linha(
            eixo="Violência contra a mulher",
            indicador="Óbitos de mulheres por agressão",
            periodo_processado="2015 a 2026",
            denominador="população feminina até 2024",
            prontidao="pronto",
            prioridade=1,
            transformacao="reutilizar Silver e Gold existentes",
            ressalva="agressão não equivale à classificação policial de feminicídio",
            **comum,
        ),
        _linha(
            eixo="Violência letal",
            indicador="Óbitos por agressão, população total",
            periodo_processado="2015 a 2026",
            denominador="população total anual disponível até 2024",
            prontidao="pronto",
            prioridade=1,
            transformacao="reutilizar a Silver e as Gold do SIM para o atlas",
            ressalva="CID-10 X85 a Y09; taxas por residência somente até 2024",
            **comum,
        ),
        _linha(
            eixo="Violência autoprovocada",
            indicador="Óbitos por suicídio",
            periodo_processado="2015 a 2026",
            denominador="população total, por sexo e por idade disponível até 2024",
            prontidao="pronto",
            prioridade=1,
            transformacao="reutilizar a Silver e as Gold do SIM para o atlas",
            ressalva="CID-10 X60 a X84; mortalidade por residência não é ocorrência policial",
            **comum,
        ),
        _linha(
            eixo="Trânsito",
            indicador="Óbitos por acidentes de transporte",
            periodo_processado="2015 a 2026",
            denominador="população total, por sexo e por idade disponível até 2024",
            prontidao="pronto",
            prioridade=2,
            transformacao="reutilizar a Silver e as Gold do SIM para o atlas",
            ressalva="CID-10 V01 a V99; taxas por residência somente até 2024",
            **comum,
        ),
    ]


def _catalogo_sinan() -> list[dict]:
    indicadores = [
        ("Violência interpessoal", "Notificações de violência interpessoal", "todas as marcações de violência interpessoal", 1),
        ("Violência autoprovocada", "Notificações de violência autoprovocada", "LES_AUTOP igual a 1", 1),
        ("Violência interpessoal", "Violência física", "VIOL_FISIC igual a 1", 1),
        ("Violência interpessoal", "Violência psicológica", "VIOL_PSICO igual a 1", 1),
        ("Violência sexual", "Violência sexual notificada", "VIOL_SEXU igual a 1", 1),
        ("Violência interpessoal", "Violência financeira", "VIOL_FINAN igual a 1", 2),
        ("Violência interpessoal", "Negligência", "VIOL_NEGLI igual a 1", 2),
        ("Violência interpessoal", "Tortura", "VIOL_TORT igual a 1", 2),
        ("Violência interpessoal", "Tráfico de pessoas", "VIOL_TRAF igual a 1", 2),
    ]
    linhas = []
    for eixo, indicador, regra, prioridade in indicadores:
        linhas.append(
            _linha(
                eixo=eixo,
                indicador=indicador,
                fonte="SINAN",
                unidade="notificações",
                periodo_bronze="2015 a 2025",
                periodo_processado="2015 a 2025",
                brasil="sim",
                uf="sim",
                municipio_sc="sim",
                mensal="possível a partir da data da ocorrência ou notificação",
                sexo="sim no arquivo bruto",
                idade="sim",
                raca="sim",
                denominador="população total, por sexo e por idade disponível até 2024",
                territorio_referencia="residência da pessoa notificada",
                prontidao="pronto",
                prioridade=prioridade,
                transformacao="reutilizar a Silver e as Gold do SINAN para o atlas",
                ressalva="conta notificações, não pessoas únicas; tipos podem coexistir no mesmo registro",
            )
        )
    return linhas


def _catalogo_contexto() -> list[dict]:
    return [
        _linha(
            eixo="Denominadores",
            indicador="População feminina anual",
            fonte="IBGE",
            unidade="pessoas",
            periodo_bronze="2015 a 2024",
            periodo_processado="2015 a 2024",
            brasil="sim",
            uf="sim",
            municipio_sc="sim",
            mensal="não se aplica",
            sexo="feminino",
            idade="não",
            raca="não",
            denominador="é o próprio denominador",
            territorio_referencia="residência estimada",
            prontidao="pronto",
            prioridade=1,
            transformacao="reutilizar a Silver existente",
            ressalva="mantida para compatibilidade com as análises já publicadas",
        ),
        _linha(
            eixo="Denominadores",
            indicador="População total, por sexo e por idade",
            fonte="IBGE",
            unidade="pessoas",
            periodo_bronze="2012 a 2024",
            periodo_processado="2015 a 2024",
            brasil="sim",
            uf="sim",
            municipio_sc="sim",
            mensal="não se aplica",
            sexo="sim",
            idade="sim",
            raca="não",
            denominador="é o próprio denominador",
            territorio_referencia="residência estimada",
            prontidao="pronto",
            prioridade=1,
            transformacao="reutilizar as três bases Silver geradas por fetch_populacao_geral.py",
            ressalva="sexo e idade são recortes independentes, não cruzados; série termina em 2024",
        ),
        _linha(
            eixo="Desigualdades",
            indicador="População feminina por raça",
            fonte="Censo 2022",
            unidade="pessoas",
            periodo_bronze="2022",
            periodo_processado="2022",
            brasil="sim",
            uf="sim",
            municipio_sc="sim",
            mensal="não se aplica",
            sexo="feminino",
            idade="não",
            raca="sim",
            denominador="é o próprio denominador",
            territorio_referencia="residência censitária",
            prontidao="pronto",
            prioridade=1,
            transformacao="reutilizar Gold existente",
            ressalva="denominador fixo de 2022 para análises raciais",
        ),
        _linha(
            eixo="Desigualdades",
            indicador="Emprego formal, remuneração e escolaridade",
            fonte="RAIS",
            unidade="vínculos formais",
            periodo_bronze="2019 a 2025",
            periodo_processado="2019 a 2025; raça em 2024 e 2025",
            brasil="sim",
            uf="sim",
            municipio_sc="sim",
            mensal="movimentação disponível",
            sexo="sim",
            idade="não no recorte atual",
            raca="sim em 2024 e 2025",
            denominador="Censo 2022 para índice de inserção racial",
            territorio_referencia="local do estabelecimento",
            prontidao="pronto com ressalva",
            prioridade=2,
            transformacao="reutilizar Silver e Gold existentes",
            ressalva="mede vínculos formais, não toda a população ocupada",
        ),
    ]


def _matriz_fontes(catalogo: pd.DataFrame) -> pd.DataFrame:
    def disponivel(valores: pd.Series, aceitar_feminino: bool = False) -> bool:
        textos = valores.fillna("").str.lower()
        prefixos = ("sim", "limitado")
        if textos.str.startswith(prefixos).any():
            return True
        return aceitar_feminino and textos.eq("feminino").any()

    linhas = []
    for fonte, grupo in catalogo.groupby("fonte", sort=False):
        linhas.append(
            {
                "fonte": fonte,
                "indicadores_catalogados": len(grupo),
                "periodo_bronze": "; ".join(sorted(grupo.periodo_bronze.unique())),
                "brasil": _sim_nao(grupo.brasil.str.startswith("sim").any()),
                "uf": _sim_nao(grupo.uf.str.startswith("sim").any()),
                "municipio_sc": _sim_nao(grupo.municipio_sc.str.startswith("sim").any()),
                "mensal": _sim_nao(grupo.mensal.str.startswith("sim").any() | grupo.mensal.str.startswith("possível").any()),
                "sexo": _sim_nao(disponivel(grupo.sexo, aceitar_feminino=True)),
                "idade": _sim_nao(disponivel(grupo.idade)),
                "raca": _sim_nao(disponivel(grupo.raca)),
                "principal_pendencia": {
                    "Sinesp VDE": "manter alertas de comparabilidade e atualizar a cobertura a cada carga",
                    "SIM": "manter 2025 e 2026 sem taxa até haver denominadores compatíveis",
                    "SINAN": "manter tipos coexistentes e 2025 sem taxa até haver denominador compatível",
                    "IBGE": "obter denominadores posteriores a 2024 quando a fonte os publicar",
                    "Censo 2022": "incluir população geral por sexo, idade e raça se necessário",
                    "RAIS": "manter como contexto socioeconômico, sem inferência causal",
                }.get(fonte, "documentar regras"),
            }
        )
    return pd.DataFrame(linhas)


def main() -> None:
    obrigatorios = [
        SINESP_ANUAL,
        SINESP_UF,
        SINESP_MUNICIPIOS,
        POPULACAO_FEMININA,
        POPULACAO_TOTAL,
        POPULACAO_SEXO,
        POPULACAO_IDADE,
        SINESP_COBERTURA,
        SINESP_TERRITORIO,
        SINESP_MENSAL,
    ]
    ausentes = [str(path.relative_to(ROOT)) for path in obrigatorios if not path.exists()]
    if ausentes:
        raise FileNotFoundError(f"Arquivos ausentes: {ausentes}")

    catalogo = pd.DataFrame(
        _catalogo_sinesp() + _catalogo_sim() + _catalogo_sinan() + _catalogo_contexto()
    ).sort_values(["prioridade", "eixo", "fonte", "indicador"]).reset_index(drop=True)
    catalogo.insert(0, "id_indicador", [f"ATLAS_{numero:03d}" for numero in range(1, len(catalogo) + 1)])
    matriz = _matriz_fontes(catalogo)

    GOLD.mkdir(parents=True, exist_ok=True)
    catalogo.to_csv(CATALOGO, index=False, encoding="utf-8-sig")
    matriz.to_csv(MATRIZ_FONTES, index=False, encoding="utf-8-sig")

    resumo = {
        "indicadores_catalogados": int(len(catalogo)),
        "fontes": sorted(catalogo.fonte.unique().tolist()),
        "por_prontidao": {str(chave): int(valor) for chave, valor in catalogo.prontidao.value_counts().items()},
        "por_prioridade": {str(chave): int(valor) for chave, valor in catalogo.prioridade.value_counts().sort_index().items()},
        "eventos_sinesp": int(catalogo.fonte.eq("Sinesp VDE").sum()),
        "proxima_etapa": "prototipar a navegação do atlas com as camadas validadas, sem alterar o painel publicado",
    }
    RESUMO.write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Catálogo: {CATALOGO.relative_to(ROOT)} ({len(catalogo)} indicadores)")
    print(f"Matriz: {MATRIZ_FONTES.relative_to(ROOT)} ({len(matriz)} fontes)")
    print(f"Resumo: {RESUMO.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
