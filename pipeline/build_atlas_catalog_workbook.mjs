import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = process.cwd();
const outputDir = path.join(root, "outputs", "atlas_violencia_20261026");
const catalogPath = path.join(root, "data", "gold", "atlas", "catalogo_indicadores.csv");
const sourcesPath = path.join(root, "data", "gold", "atlas", "matriz_disponibilidade_fontes.csv");
const summaryPath = path.join(root, "data", "gold", "atlas", "resumo_catalogo.json");

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    if (quoted) {
      if (character === '"' && text[index + 1] === '"') {
        field += '"';
        index += 1;
      } else if (character === '"') {
        quoted = false;
      } else {
        field += character;
      }
    } else if (character === '"') {
      quoted = true;
    } else if (character === ",") {
      row.push(field);
      field = "";
    } else if (character === "\n") {
      row.push(field.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      field = "";
    } else {
      field += character;
    }
  }
  if (field || row.length) {
    row.push(field.replace(/\r$/, ""));
    rows.push(row);
  }
  return rows.filter(item => item.length && item.some(value => value !== ""));
}

function applyBaseStyle(sheet, rangeAddress) {
  const range = sheet.getRange(rangeAddress);
  range.format.font = { name: "Arial", size: 10, color: "#1E2524" };
  range.format.verticalAlignment = "center";
}

function styleHeader(range) {
  range.format.fill = "#1E2524";
  range.format.font = { name: "Arial", size: 10, bold: true, color: "#FFFEFA" };
  range.format.horizontalAlignment = "center";
  range.format.verticalAlignment = "center";
  range.format.wrapText = true;
  range.format.borders = { preset: "inside", style: "thin", color: "#F4F1EB" };
}

const catalogRows = parseCsv(await fs.readFile(catalogPath, "utf8"));
const sourceRows = parseCsv(await fs.readFile(sourcesPath, "utf8"));
const summary = JSON.parse(await fs.readFile(summaryPath, "utf8"));

const workbook = Workbook.create();
const resumo = workbook.worksheets.add("Resumo");
const catalogo = workbook.worksheets.add("Catalogo");
const fontes = workbook.worksheets.add("Fontes");

resumo.showGridLines = false;
catalogo.showGridLines = false;
fontes.showGridLines = false;
resumo.tabColor = "#8D1734";
catalogo.tabColor = "#C56B7E";
fontes.tabColor = "#D9C5CA";

resumo.getRange("A2:H2").format.borders = { bottom: { style: "thin", color: "#8D1734" } };
resumo.getRange("A2").values = [["Catálogo de indicadores do Panorama Territorial da Violência"]];
resumo.getRange("A2").format.font = { name: "Arial", size: 16, bold: true, color: "#1E2524" };
resumo.getRange("A3").values = [["Situação em 26 de outubro de 2026"]];
resumo.getRange("A3").format.font = { name: "Arial", size: 10, italic: true, color: "#656B68" };

resumo.getRange("A5:B5").values = [["Medida", "Valor"]];
styleHeader(resumo.getRange("A5:B5"));
resumo.getRange("A6:A12").values = [
  ["Indicadores catalogados"],
  ["Fontes"],
  ["Prioridade 1"],
  ["Prontos"],
  ["Prontos para mulheres"],
  ["Prontos com ressalva"],
  ["Dependem de reprocessamento"],
];
resumo.getRange("B6:B12").formulas = [
  [`=COUNTA(Catalogo!A2:A${catalogRows.length})`],
  ["=COUNTA(Fontes!A2:A7)"],
  [`=COUNTIF(Catalogo!R2:R${catalogRows.length},1)`],
  [`=COUNTIF(Catalogo!Q2:Q${catalogRows.length},\"pronto\")`],
  [`=COUNTIF(Catalogo!Q2:Q${catalogRows.length},\"pronto para mulheres\")`],
  [`=COUNTIF(Catalogo!Q2:Q${catalogRows.length},\"pronto com ressalva\")`],
  [`=COUNTIF(Catalogo!Q2:Q${catalogRows.length},\"requer reprocessamento\")`],
];
resumo.getRange("A6:B12").format.borders = { insideHorizontal: { style: "thin", color: "#C9C3B8" } };
resumo.getRange("B6:B12").format.horizontalAlignment = "right";
resumo.getRange("B6:B12").format.font = { name: "Arial", size: 11, bold: true, color: "#8D1734" };

resumo.getRange("D5:H5").values = [["Próxima etapa", "Dependência", "Ação", "Saída esperada", "Ordem"]];
styleHeader(resumo.getRange("D5:H5"));
resumo.getRange("D6:H6").values = [
  ["Produto", "Camadas validadas", summary.proxima_etapa, "Protótipo navegável do atlas", 1],
];
resumo.getRange("D6:H6").format.wrapText = true;
resumo.getRange("H6:H6").format.horizontalAlignment = "center";

resumo.getRange("A15:H15").format.borders = { bottom: { style: "thin", color: "#8D1734" } };
resumo.getRange("A15").values = [["Regras de leitura"]];
resumo.getRange("A15").format.font = { name: "Arial", size: 14, bold: true, color: "#1E2524" };
resumo.getRange("A17:H22").values = [
  ["1", "Não somar SINAN, SIM e Sinesp.", null, null, null, null, null, null],
  ["2", "Informar residência ou local do fato em cada indicador.", null, null, null, null, null, null],
  ["3", "Separar dados consolidados, preliminares e parciais.", null, null, null, null, null, null],
  ["4", "Mostrar o número absoluto junto da taxa.", null, null, null, null, null, null],
  ["5", "Aplicar critérios mínimos antes de ranquear municípios.", null, null, null, null, null, null],
  ["6", "Tratar relações entre trabalho e violência como associação descritiva.", null, null, null, null, null, null],
];
resumo.getRange("A17:A22").format.font = { name: "Arial", size: 10, bold: true, color: "#8D1734" };
resumo.getRange("B17:H22").format.wrapText = false;
resumo.getRange("A17:H22").format.borders = { insideHorizontal: { style: "thin", color: "#DED8CE" } };

catalogo.getRange("A1").write(catalogRows);
applyBaseStyle(catalogo, `A1:T${catalogRows.length}`);
styleHeader(catalogo.getRange("A1:T1"));
catalogo.getRange(`A2:T${catalogRows.length}`).format.wrapText = true;
catalogo.freezePanes.freezeRows(1);
catalogo.freezePanes.freezeColumns(3);
catalogo.getRange(`Q2:Q${catalogRows.length}`).conditionalFormats.add("containsText", {
  text: "requer",
  format: { fill: "#F4D9D9", font: { bold: true, color: "#8D1734" } },
});
catalogo.getRange(`Q2:Q${catalogRows.length}`).conditionalFormats.add("containsText", {
  text: "pronto",
  format: { fill: "#DBEAE6", font: { color: "#0C5E50" } },
});
catalogo.getRange(`R2:R${catalogRows.length}`).conditionalFormats.add("cellIs", {
  operator: "equal",
  formula: 1,
  format: { fill: "#F0E6CF", font: { bold: true, color: "#744B00" } },
});

fontes.getRange("A1").write(sourceRows);
applyBaseStyle(fontes, `A1:K${sourceRows.length}`);
styleHeader(fontes.getRange("A1:K1"));
fontes.getRange(`A2:K${sourceRows.length}`).format.wrapText = true;
fontes.freezePanes.freezeRows(1);
fontes.freezePanes.freezeColumns(1);

resumo.getRange("A1:H24").format.font = { name: "Arial", size: 10, color: "#1E2524" };
resumo.getRange("A2").format.font = { name: "Arial", size: 16, bold: true, color: "#1E2524" };
resumo.getRange("A3").format.font = { name: "Arial", size: 10, italic: true, color: "#656B68" };
resumo.getRange("A15").format.font = { name: "Arial", size: 14, bold: true, color: "#1E2524" };
styleHeader(resumo.getRange("A5:B5"));
styleHeader(resumo.getRange("D5:H5"));
resumo.getRange("A:A").format.columnWidth = 42;
resumo.getRange("B:B").format.columnWidth = 12;
resumo.getRange("C:C").format.columnWidth = 3;
resumo.getRange("D:D").format.columnWidth = 19;
resumo.getRange("E:E").format.columnWidth = 17;
resumo.getRange("F:F").format.columnWidth = 34;
resumo.getRange("G:G").format.columnWidth = 28;
resumo.getRange("H:H").format.columnWidth = 10;
resumo.getRange("5:22").format.autofitRows();
resumo.getRange("17:22").format.rowHeight = 24;

catalogo.getRange("A:A").format.columnWidth = 14;
catalogo.getRange("B:B").format.columnWidth = 23;
catalogo.getRange("C:C").format.columnWidth = 34;
catalogo.getRange("D:D").format.columnWidth = 16;
catalogo.getRange("E:E").format.columnWidth = 20;
catalogo.getRange("F:G").format.columnWidth = 18;
catalogo.getRange("H:N").format.columnWidth = 16;
catalogo.getRange("O:O").format.columnWidth = 28;
catalogo.getRange("P:P").format.columnWidth = 28;
catalogo.getRange("Q:Q").format.columnWidth = 23;
catalogo.getRange("R:R").format.columnWidth = 10;
catalogo.getRange("S:T").format.columnWidth = 38;
catalogo.getRange(`1:${catalogRows.length}`).format.autofitRows();

fontes.getRange("A:A").format.columnWidth = 18;
fontes.getRange("B:B").format.columnWidth = 16;
fontes.getRange("C:C").format.columnWidth = 32;
fontes.getRange("D:J").format.columnWidth = 13;
fontes.getRange("K:K").format.columnWidth = 52;
fontes.getRange(`1:${sourceRows.length}`).format.autofitRows();

workbook.recalculate();
await fs.mkdir(outputDir, { recursive: true });

const summaryInspection = await workbook.inspect({
  kind: "table",
  sheetId: "Resumo",
  range: "A1:H22",
  include: "values,formulas",
  tableMaxRows: 24,
  tableMaxCols: 8,
  maxChars: 12000,
});
console.log(summaryInspection.ndjson);

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 100 },
  summary: "verificação final de erros",
});
console.log(errors.ndjson);

for (const [sheetName, fileName] of [["Resumo", "preview_resumo.png"], ["Catalogo", "preview_catalogo.png"], ["Fontes", "preview_fontes.png"]]) {
  const preview = await workbook.render({ sheetName, autoCrop: "all", scale: 1, format: "png" });
  await fs.writeFile(path.join(outputDir, fileName), new Uint8Array(await preview.arrayBuffer()));
}

const output = await SpreadsheetFile.exportXlsx(workbook);
const outputPath = path.join(outputDir, "catalogo_indicadores_atlas.xlsx");
await output.save(outputPath);
console.log(JSON.stringify({ outputPath, expectedIndicators: summary.indicadores_catalogados, rows: catalogRows.length - 1 }));
