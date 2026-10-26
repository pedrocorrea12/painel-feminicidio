const URLS = {
  monitoring: '../../../data/gold/integrado/monitoramento_atual_2025_2026.csv',
  history: '../../../data/gold/integrado/historico_integrado_2019_2024.csv',
  ratio: '../../../data/gold/integrado/razao_sim_sinesp_uf_2019_2024.csv',
  attempts: '../../../data/gold/integrado/tentativa_feminicidio_2019_2026.csv',
  homicide: '../../../data/gold/integrado/homicidio_doloso_feminicidio_2019_2026.csv',
  municipal: '../../../data/gold/integrado/taxa_municipal_feminicidio_sc_2019_2024.csv',
  season: '../../../data/gold/integrado/sinesp_sazonalidade_mes_2019_2025.csv',
  simRace: '../../../data/gold/raca/sim_raca_uf_ano_2019_2024.csv',
  simRaceMunicipal: '../../../data/gold/raca/sim_raca_municipios_sc_2019_2024.csv',
  sinanRace: '../../../data/gold/raca/sinan_raca_uf_2024.csv',
  raisSex: '../../../data/gold/rais/emprego_formal_sexo_2019_2025.csv',
  raisSexMunicipal: '../../../data/gold/rais/emprego_formal_sexo_municipios_sc_2019_2025.csv',
  raisMovement: '../../../data/gold/rais/movimentacao_mensal_sexo_2019_2025.csv',
  raisInsertion: '../../../data/gold/rais/insercao_formal_mulheres_negras_2024_2025.csv',
  raisSalaryRace: '../../../data/gold/rais/razao_salarial_raca_2024_2025.csv',
  raisSalaryRaceMunicipal: '../../../data/gold/rais/razao_salarial_raca_municipios_sc_2024_2025.csv',
  sinespMonthly: '../../../data/gold/integrado/sinesp_serie_mensal_2019_2026.csv'
};

const integer = new Intl.NumberFormat('pt-BR');
const decimal = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const decimal2 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const compact = new Intl.NumberFormat('pt-BR', { notation: 'compact', maximumFractionDigits: 1 });

const COLORS = { brazil: '#316a91', sc: '#147665', city: '#a22545', wine: '#c56b7e', gold: '#c59a45' };
const sourceOrder = ['Sinesp VDE', 'SIM', 'SINAN'];
const sourceMeta = {
  'Sinesp VDE': { title: 'Vítimas de feminicídio', territory: 'Local do fato', coverage: { 2025: 'Ano completo', 2026: 'Janeiro a agosto' } },
  SIM: { title: 'Óbitos de mulheres por agressão', territory: 'Residência da vítima', coverage: { 2025: '1 de janeiro a 26 de agosto', 2026: '1 de janeiro a 26 de agosto' } },
  SINAN: { title: 'Notificações de violência interpessoal', territory: 'Residência da vítima', coverage: { 2025: 'Ano completo', 2026: 'Sem dados nesta atualização' } }
};
const historyMetrics = {
  sinan: { title: 'Taxa de notificações', rate: 'sinan_taxa_notificacoes_100mil', count: 'sinan_notificacoes', noun: 'notificações' },
  sim: { title: 'Taxa de óbitos por agressão', rate: 'sim_taxa_obitos_agressao_100mil', count: 'sim_obitos_mulheres_agressao', noun: 'óbitos' },
  sinesp: { title: 'Taxa de feminicídios', rate: 'sinesp_taxa_feminicidio_100mil', count: 'sinesp_vitimas_feminicidio', noun: 'vítimas' }
};

const state = {
  data: {},
  year: 2026,
  municipalityId: null,
  historyMetric: 'sinan',
  indicatorTerritory: 'BR',
  inequalityTerritory: 'BR',
  view: 'monitoramento'
};

function parseCsv(text) {
  const records = [];
  let record = [];
  let field = '';
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    if (quoted) {
      if (character === '"' && text[index + 1] === '"') { field += '"'; index += 1; }
      else if (character === '"') quoted = false;
      else field += character;
    } else if (character === '"') quoted = true;
    else if (character === ',') { record.push(field); field = ''; }
    else if (character === '\n') { record.push(field.replace(/\r$/, '')); records.push(record); record = []; field = ''; }
    else field += character;
  }
  if (field || record.length) { record.push(field.replace(/\r$/, '')); records.push(record); }
  const headers = records.shift();
  return records.filter(row => row.length === headers.length).map(row => Object.fromEntries(headers.map((header, index) => [header, row[index]])));
}

function esc(value) {
  return String(value ?? '').replace(/[&<>'"]/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character]));
}
function numberOrNull(value) { return value === '' || value === null || value === undefined ? null : Number(value); }
function fmtInt(value) { return integer.format(Number(value) || 0); }
function fmt1(value) { return decimal.format(Number(value) || 0); }
function fmt2(value) { return decimal2.format(Number(value) || 0); }
function recordCount(value) { const number = Number(value) || 0; return `${fmtInt(number)} ${number === 1 ? 'registro' : 'registros'}`; }
function selectedMunicipalityName() {
  const row = state.data.monitoring.find(item => item.nivel_territorial === 'municipio' && item.id_territorio === state.municipalityId);
  return row ? row.territorio : 'Município';
}

function statusInfo(source, year) {
  if (source === 'SINAN' && year === 2026) return { label: 'Indisponível', className: 'unavailable' };
  const row = state.data.monitoring.find(item => item.fonte === source && Number(item.ano) === year);
  if (!row) return { label: 'Indisponível', className: 'unavailable' };
  if (row.situacao_dado === 'consolidado_publicacao') return { label: 'Completo', className: 'complete' };
  if (row.situacao_dado === 'preliminar') return { label: 'Preliminar', className: 'preliminary' };
  if (row.situacao_dado === 'previa') return { label: 'Prévia', className: 'preliminary' };
  return { label: 'Parcial', className: 'partial' };
}

function setView(name, updateHash = true) {
  const valid = ['monitoramento', 'historico', 'indicadores', 'desigualdades', 'municipios', 'metodologia'];
  state.view = valid.includes(name) ? name : 'monitoramento';
  document.querySelectorAll('[data-view]').forEach(view => {
    const active = view.dataset.view === state.view;
    view.hidden = !active;
    view.classList.toggle('active', active);
  });
  document.querySelectorAll('[data-view-target]').forEach(button => {
    const active = button.dataset.viewTarget === state.view;
    button.classList.toggle('active', active);
    if (active) button.setAttribute('aria-current', 'page'); else button.removeAttribute('aria-current');
  });
  if (updateHash) history.replaceState(null, '', `#${state.view}`);
  window.scrollTo({ top: 0, behavior: 'auto' });
}

function monitoringRows(source) {
  const rows = state.data.monitoring.filter(item => item.fonte === source && Number(item.ano) === state.year);
  return {
    Brasil: rows.find(item => item.nivel_territorial === 'brasil'),
    'Santa Catarina': rows.find(item => item.nivel_territorial === 'uf'),
    [selectedMunicipalityName()]: rows.find(item => item.nivel_territorial === 'municipio' && item.id_territorio === state.municipalityId)
  };
}

function renderMonitoringControls() {
  document.querySelectorAll('[data-year]').forEach(button => {
    const active = Number(button.dataset.year) === state.year;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
}

function renderCoverage() {
  const available = sourceOrder.filter(source => !(source === 'SINAN' && state.year === 2026)).length;
  document.getElementById('coverage-summary').textContent = state.year === 2026
    ? `${available} fontes disponíveis, todas com cobertura limitada no tempo.`
    : `${available} fontes disponíveis, com situações de fechamento diferentes.`;
  document.getElementById('coverage-grid').innerHTML = sourceOrder.map(source => {
    const status = statusInfo(source, state.year);
    return `<article class="coverage-card"><div class="coverage-top"><p class="source-name">${esc(source)}</p><span class="status ${status.className}">${status.label}</span></div><h3>${esc(sourceMeta[source].coverage[state.year])}</h3><p>${esc(sourceMeta[source].title)}</p></article>`;
  }).join('');
}

function changeLabel(value) {
  const number = numberOrNull(value);
  if (number === null) return 'Sem comparação percentual';
  if (number === 0) return 'Estável';
  return `${number > 0 ? '+' : ''}${fmt1(number)}%`;
}

function valueCell(row, territory) {
  if (!row) return `<div class="territory-value empty-value" data-territory="${esc(territory)}"><strong>Dado não disponível</strong><span>Sem registro nesta atualização</span></div>`;
  const current = Number(row.valor_absoluto) || 0;
  const change = numberOrNull(row.variacao_percentual);
  const changeClass = change === null || change === 0 ? 'stable' : change > 0 ? 'up' : 'down';
  const barWidth = change === null ? 0 : Math.min(Math.abs(change), 50) / 50 * 50;
  const barClass = change !== null && change < 0 ? 'negative' : 'positive';
  const zeroNote = current === 0 && state.year === 2026 ? '<span class="zero-note">Nenhum registro localizado até a atualização</span>' : '';
  return `<div class="territory-value" data-territory="${esc(territory)}"><strong>${fmtInt(current)}</strong>${zeroNote}<span class="previous">${fmtInt(row.valor_periodo_anterior)} no período comparável de ${esc(row.ano_comparacao)}</span><div class="change ${changeClass}">${changeLabel(row.variacao_percentual)}</div><div class="delta-track ${changeClass}" aria-hidden="true"><i class="${barClass}" style="width:${barWidth}%"></i></div></div>`;
}

function renderMonitoringIndicators() {
  const municipality = selectedMunicipalityName();
  const territories = ['Brasil', 'Santa Catarina', municipality];
  document.getElementById('territory-heading').innerHTML = `<div>Indicador</div>${territories.map(territory => `<div>${esc(territory)}</div>`).join('')}`;
  document.getElementById('indicator-list').innerHTML = sourceOrder.map(source => {
    const rows = monitoringRows(source);
    return `<article class="indicator"><div class="indicator-meta"><span class="indicator-source">${esc(source)}</span><h3>${esc(sourceMeta[source].title)}</h3><p>${esc(sourceMeta[source].coverage[state.year])}. Base territorial: ${esc(sourceMeta[source].territory.toLocaleLowerCase('pt-BR'))}.</p></div>${territories.map(territory => valueCell(rows[territory], territory)).join('')}</article>`;
  }).join('');
}

function directionText(row) {
  if (!row) return null;
  const current = Number(row.valor_absoluto) || 0;
  const change = numberOrNull(row.variacao_percentual);
  if (current === 0 && state.year === 2026) return `nenhum registro localizado até a atualização. No período comparável de ${row.ano_comparacao}, o valor era ${fmtInt(row.valor_periodo_anterior)}.`;
  if (change === null) return `${recordCount(current)}, sem variação percentual calculável.`;
  if (change === 0) return `${recordCount(current)}, o mesmo valor do período comparável de ${row.ano_comparacao}.`;
  return `${recordCount(current)}, ${fmt1(Math.abs(change))}% ${change > 0 ? 'acima' : 'abaixo'} do período comparável de ${row.ano_comparacao}.`;
}

function renderMonitoringReading() {
  const municipality = selectedMunicipalityName();
  document.getElementById('reading-grid').innerHTML = sourceOrder.map(source => {
    const rows = monitoringRows(source);
    if (!rows.Brasil) return `<article class="reading-card unavailable"><p class="source-name">${esc(source)}</p><p>O indicador ainda não está disponível para ${state.year}. A ausência é mostrada sem repetir o valor anterior.</p></article>`;
    return `<article class="reading-card"><p class="source-name">${esc(source)}</p><p>Brasil: ${esc(directionText(rows.Brasil))} Santa Catarina: ${esc(directionText(rows['Santa Catarina']))} ${esc(municipality)}: ${esc(directionText(rows[municipality]))}</p></article>`;
  }).join('');
}

function renderMonitoring() {
  renderMonitoringControls();
  renderCoverage();
  renderMonitoringIndicators();
  renderMonitoringReading();
}

function lineChart(targetId, series, options = {}) {
  const host = document.getElementById(targetId);
  const validSeries = series.filter(item => item.data.length);
  if (!host || !validSeries.length) return;
  const width = 1180;
  const height = options.height || 430;
  const pad = { left: 72, right: options.endLabels === false ? 40 : 190, top: 40, bottom: 58 };
  const plotWidth = width - pad.left - pad.right;
  const plotHeight = height - pad.top - pad.bottom;
  const years = [...new Set(validSeries.flatMap(item => item.data.map(row => row.year)))].sort((a, b) => a - b);
  const allValues = validSeries.flatMap(item => item.data.map(row => Number(row.value) || 0));
  const max = Math.max(...allValues, 1) * 1.15;
  const x = year => pad.left + years.indexOf(year) / Math.max(1, years.length - 1) * plotWidth;
  const y = value => pad.top + (1 - (Number(value) || 0) / max) * plotHeight;
  const ticks = [0, .25, .5, .75, 1];
  const axis = value => options.integerAxis ? compact.format(value) : fmt1(value);
  const paths = validSeries.map(item => {
    const points = item.data.map(row => `${x(row.year)},${y(row.value)}`).join(' ');
    const dots = item.data.map(row => `<circle cx="${x(row.year)}" cy="${y(row.value)}" r="4.5" fill="${item.color}"><title>${esc(item.label)}, ${row.year}: ${esc(options.tooltip ? options.tooltip(row) : fmt1(row.value))}</title></circle>`).join('');
    const last = item.data[item.data.length - 1];
    const end = options.endLabels === false ? '' : `<text class="chart-end" x="${x(last.year) + 13}" y="${y(last.value) + 4}" fill="${item.color}">${esc(item.label)} ${esc(options.endFormat ? options.endFormat(last) : fmt1(last.value))}</text>`;
    return `<polyline class="chart-line" points="${points}" stroke="${item.color}"/>${dots}${end}`;
  }).join('');
  host.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(options.label || 'Gráfico de linhas')}">${ticks.map(tick => `<line class="chart-grid" x1="${pad.left}" x2="${width - pad.right}" y1="${y(max * tick)}" y2="${y(max * tick)}"/><text class="chart-axis" x="${pad.left - 12}" y="${y(max * tick) + 4}" text-anchor="end">${axis(max * tick)}</text>`).join('')}<line class="chart-axis-line" x1="${pad.left}" x2="${width - pad.right}" y1="${height - pad.bottom}" y2="${height - pad.bottom}"/>${years.map(year => `<text class="chart-axis" x="${x(year)}" y="${height - 22}" text-anchor="middle">${year}${options.partialYear === year ? '*' : ''}</text>`).join('')}${paths}</svg>`;
}

function monthlyIndexChart(targetId, series) {
  const host = document.getElementById(targetId);
  const validSeries = series.filter(item => item.data.length);
  if (!host || !validSeries.length) return;
  const width = 1180;
  const height = 430;
  const pad = { left: 68, right: 190, top: 38, bottom: 58 };
  const plotWidth = width - pad.left - pad.right;
  const plotHeight = height - pad.top - pad.bottom;
  const count = validSeries[0].data.length;
  const values = validSeries.flatMap(item => item.data.map(row => row.value));
  const min = Math.max(0, Math.floor(Math.min(...values) / 10) * 10 - 10);
  const max = Math.ceil(Math.max(...values) / 10) * 10 + 10;
  const x = index => pad.left + index / Math.max(1, count - 1) * plotWidth;
  const y = value => pad.top + (1 - (value - min) / Math.max(1, max - min)) * plotHeight;
  const ticks = [0, .25, .5, .75, 1].map(part => min + (max - min) * part);
  const referenceY = y(100);
  const paths = validSeries.map(item => {
    const points = item.data.map((row, index) => `${x(index)},${y(row.value)}`).join(' ');
    const hitAreas = item.data.map((row, index) => `<circle class="chart-hit" cx="${x(index)}" cy="${y(row.value)}" r="7"><title>${esc(item.label)}, ${row.month}/${row.year}: índice ${fmt1(row.value)}, ${fmtInt(row.raw)} no acumulado de 12 meses</title></circle>`).join('');
    const last = item.data.at(-1);
    return `<polyline class="chart-line" points="${points}" stroke="${item.color}"/>${hitAreas}<text class="chart-end" x="${x(count - 1) + 13}" y="${y(last.value) + 4}" fill="${item.color}">${esc(item.shortLabel)} ${fmt1(last.value)}</text>`;
  }).join('');
  const yearTicks = validSeries[0].data.map((row, index) => ({ row, index })).filter(item => item.row.month === 1 || item.index === 0 || item.index === count - 1);
  host.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Índices de desligamentos e feminicídios acumulados em 12 meses"><line class="chart-reference" x1="${pad.left}" x2="${width - pad.right}" y1="${referenceY}" y2="${referenceY}"/>${ticks.map(tick => `<line class="chart-grid" x1="${pad.left}" x2="${width - pad.right}" y1="${y(tick)}" y2="${y(tick)}"/><text class="chart-axis" x="${pad.left - 12}" y="${y(tick) + 4}" text-anchor="end">${fmtInt(tick)}</text>`).join('')}<line class="chart-axis-line" x1="${pad.left}" x2="${width - pad.right}" y1="${height - pad.bottom}" y2="${height - pad.bottom}"/>${yearTicks.map(item => `<text class="chart-axis" x="${x(item.index)}" y="${height - 22}" text-anchor="middle">${item.row.year}</text>`).join('')}${paths}</svg>`;
}

function rollingTwelve(rows, field) {
  const ordered = [...rows].sort((a, b) => Number(a.ano) * 12 + Number(a.mes) - (Number(b.ano) * 12 + Number(b.mes)));
  return ordered.map((row, index) => {
    if (index < 11) return null;
    const windowRows = ordered.slice(index - 11, index + 1);
    return {
      key: `${row.ano}-${String(row.mes).padStart(2, '0')}`,
      year: Number(row.ano),
      month: Number(row.mes),
      raw: windowRows.reduce((sum, item) => sum + Number(item[field] || 0), 0)
    };
  }).filter(Boolean);
}

function normalizedSeries(rows) {
  const mean = rows.reduce((sum, row) => sum + row.raw, 0) / Math.max(1, rows.length);
  return rows.map(row => ({ ...row, value: mean ? row.raw / mean * 100 : 0 }));
}

function relationRow(label, value, detail, kind) {
  const numeric = Number(value) || 0;
  const ceiling = 2.2;
  const position = Math.min(100, Math.max(0, numeric / ceiling * 100));
  const reference = 1 / ceiling * 100;
  return `<article class="relation-row ${esc(kind)}"><div><strong>${esc(label)}</strong><span>${esc(detail)}</span></div><div class="relation-measure"><div class="relation-track" style="--reference:${reference}%; --position:${position}%"><i></i><b></b></div><em>${fmt2(numeric)}</em></div></article>`;
}

function renderEmploymentViolence(territory) {
  const jobRows = state.data.raisMovement.filter(row => row.id_territorio === territory && Number(row.cd_sexo) === 2 && Number(row.ano) <= 2025);
  const policeRows = state.data.sinespMonthly.filter(row => row.id_territorio === territory && Number(row.ano) <= 2025);
  const jobs = normalizedSeries(rollingTwelve(jobRows, 'desligamentos_sem_justa_causa'));
  const femicides = normalizedSeries(rollingTwelve(policeRows, 'feminicidio_total_vitimas'));
  const shared = new Set(jobs.map(row => row.key));
  const policeShared = femicides.filter(row => shared.has(row.key));
  const policeKeys = new Set(policeShared.map(row => row.key));
  const jobsShared = jobs.filter(row => policeKeys.has(row.key));
  monthlyIndexChart('employment-violence-chart', [
    { label: 'Desligamentos de mulheres sem justa causa', shortLabel: 'Desligamentos', color: '#e8a4b6', data: jobsShared },
    { label: 'Feminicídios registrados', shortLabel: 'Feminicídios', color: '#8dc7bb', data: policeShared }
  ]);
  document.getElementById('employment-violence-legend').innerHTML = `<span><i style="--legend:#e8a4b6"></i>Desligamentos de mulheres sem justa causa</span><span><i style="--legend:#8dc7bb"></i>Feminicídios registrados</span><span><i class="reference-key"></i>Média do período, índice 100</span>`;
  const latestJobs = jobsShared.at(-1);
  const latestPolice = policeShared.at(-1);
  const label = territory === 'BR' ? 'Brasil' : 'Santa Catarina';
  document.getElementById('employment-violence-note').innerHTML = `<p><strong>${esc(label)}, 12 meses encerrados em dezembro de 2025.</strong> ${fmtInt(latestJobs.raw)} desligamentos de mulheres sem justa causa, índice ${fmt1(latestJobs.value)}.</p><p>${fmtInt(latestPolice.raw)} feminicídios registrados, índice ${fmt1(latestPolice.value)}. A escala comum compara trajetórias, não volumes.</p>`;
}

function historyTerritories() {
  const city = selectedMunicipalityName();
  const rows = state.data.history;
  return [
    { label: 'Brasil', color: COLORS.brazil, rows: rows.filter(row => row.nivel_territorial === 'brasil') },
    { label: 'Santa Catarina', color: COLORS.sc, rows: rows.filter(row => row.nivel_territorial === 'uf') },
    { label: city, color: COLORS.city, rows: rows.filter(row => row.nivel_territorial === 'municipio' && row.id_territorio === state.municipalityId) }
  ];
}

function renderHistory() {
  const config = historyMetrics[state.historyMetric];
  document.getElementById('history-title').textContent = config.title;
  document.querySelectorAll('[data-history-metric]').forEach(button => button.classList.toggle('active', button.dataset.historyMetric === state.historyMetric));
  const territories = historyTerritories();
  document.getElementById('history-legend').innerHTML = territories.map(item => `<span><i style="--legend:${item.color}"></i>${esc(item.label)}</span>`).join('');
  const series = territories.map(item => ({ label: item.label, color: item.color, data: item.rows.map(row => ({ year: Number(row.ano), value: Number(row[config.rate]), count: Number(row[config.count]) })) }));
  lineChart('history-chart', series, { label: config.title, tooltip: row => `${fmt1(row.value)} por 100 mil, ${fmtInt(row.count)} ${config.noun}`, endFormat: row => fmt1(row.value) });
  document.getElementById('history-table-head').innerHTML = `<tr><th>Ano</th>${territories.map(item => `<th>${esc(item.label)}<br>taxa (total)</th>`).join('')}</tr>`;
  document.getElementById('history-table-body').innerHTML = [2019, 2020, 2021, 2022, 2023, 2024].map(year => `<tr><td>${year}</td>${territories.map(item => { const row = item.rows.find(value => Number(value.ano) === year); return `<td>${row ? `${fmt1(row[config.rate])} <span class="muted">(${fmtInt(row[config.count])})</span>` : 'n.a.'}</td>`; }).join('')}</tr>`).join('');
}

function renderRatio() {
  const rows = state.data.ratio.filter(row => row.id_territorio === 'BR' || row.id_territorio === 'SC');
  const make = (id, label, color) => ({ label, color, data: rows.filter(row => row.id_territorio === id).map(row => ({ year: Number(row.ano), value: Number(row.razao_feminicidios_total_sobre_sim) * 100 })) });
  const series = [make('BR', 'Brasil', COLORS.brazil), make('SC', 'Santa Catarina', COLORS.sc)];
  lineChart('ratio-chart', series, { label: 'Razão entre feminicídios e mortes de mulheres por agressão', tooltip: row => `${fmt1(row.value)}%`, endFormat: row => `${fmt1(row.value)}%` });
  const latestBr = series[0].data.at(-1);
  const latestSc = series[1].data.at(-1);
  document.getElementById('ratio-summary').innerHTML = `<article><span>Brasil em 2024</span><strong>${fmt1(latestBr.value)}%</strong><p>1.501 feminicídios e 3.622 óbitos por agressão</p></article><article><span>Santa Catarina em 2024</span><strong>${fmt1(latestSc.value)}%</strong><p>51 feminicídios e 90 óbitos por agressão</p></article>`;
}

function renderIndicatorCharts() {
  document.querySelectorAll('[data-indicator-territory]').forEach(button => button.classList.toggle('active', button.dataset.indicatorTerritory === state.indicatorTerritory));
  const attemptRows = state.data.attempts.filter(row => row.id_territorio === state.indicatorTerritory).sort((a, b) => Number(a.ano) - Number(b.ano));
  lineChart('attempt-chart', [
    { label: 'Tentativas', color: '#e8a4b6', data: attemptRows.map(row => ({ year: Number(row.ano), value: Number(row.tentativa_feminicidio_total_vitimas) })) },
    { label: 'Consumados', color: '#8dc7bb', data: attemptRows.map(row => ({ year: Number(row.ano), value: Number(row.feminicidio_total_vitimas) })) }
  ], { label: 'Tentativas e feminicídios consumados', integerAxis: true, tooltip: row => fmtInt(row.value), endFormat: row => fmtInt(row.value), partialYear: 2026 });
  const homicideRows = state.data.homicide.filter(row => row.id_territorio === state.indicatorTerritory).sort((a, b) => Number(a.ano) - Number(b.ano));
  lineChart('homicide-chart', [
    { label: 'Homicídio doloso', color: COLORS.brazil, data: homicideRows.map(row => ({ year: Number(row.ano), value: Number(row.homicidio_doloso_vitimas_femininas) })) },
    { label: 'Feminicídio', color: COLORS.city, data: homicideRows.map(row => ({ year: Number(row.ano), value: Number(row.feminicidio_vitimas_femininas) })) }
  ], { label: 'Mulheres vítimas de homicídio doloso e feminicídio', integerAxis: true, tooltip: row => fmtInt(row.value), endFormat: row => fmtInt(row.value), partialYear: 2026 });
  const seasonRows = state.data.season.filter(row => row.id_territorio === state.indicatorTerritory).sort((a, b) => Number(a.mes) - Number(b.mes));
  const max = Math.max(...seasonRows.map(row => Number(row.feminicidio_indice_sazonal)), 1);
  document.getElementById('season-chart').innerHTML = seasonRows.map(row => `<div class="season-item"><div class="season-bar"><i style="height:${Number(row.feminicidio_indice_sazonal) / max * 100}%"></i><span>${fmt1(row.feminicidio_indice_sazonal)}</span></div><strong>${esc(row.nome_mes.slice(0, 3))}</strong></div>`).join('');
}

function renderInequalities() {
  document.querySelectorAll('[data-inequality-territory]').forEach(button => {
    button.classList.toggle('active', button.dataset.inequalityTerritory === state.inequalityTerritory);
  });
  const territory = state.inequalityTerritory;
  const simRows = state.data.simRace
    .filter(row => row.sigla_uf === territory && (row.raca === 'Negra' || row.raca === 'Branca'))
    .sort((a, b) => Number(a.ano) - Number(b.ano));
  const simSeries = ['Negra', 'Branca'].map((race, index) => ({
    label: race,
    color: index === 0 ? COLORS.city : COLORS.brazil,
    data: simRows.filter(row => row.raca === race).map(row => ({
      year: Number(row.ano),
      value: Number(row.taxa_100mil_mulheres_censo2022),
      count: Number(row.obitos_mulheres_agressao)
    }))
  }));
  lineChart('sim-race-chart', simSeries, {
    label: 'Taxa de mortes de mulheres por agressão segundo raça',
    tooltip: row => `${fmt2(row.value)} por 100 mil, ${fmtInt(row.count)} mortes`,
    endFormat: row => fmt2(row.value)
  });
  const negra2024 = simRows.find(row => row.raca === 'Negra' && Number(row.ano) === 2024);
  const branca2024 = simRows.find(row => row.raca === 'Branca' && Number(row.ano) === 2024);
  const territoryLabel = territory === 'BR' ? 'Brasil' : 'Santa Catarina';
  document.getElementById('sim-race-summary').innerHTML = `
    <article><span>${esc(territoryLabel)}, mulheres negras em 2024</span><strong>${fmt2(negra2024.taxa_100mil_mulheres_censo2022)}</strong><p>${fmtInt(negra2024.obitos_mulheres_agressao)} mortes por agressão</p></article>
    <article><span>${esc(territoryLabel)}, mulheres brancas em 2024</span><strong>${fmt2(branca2024.taxa_100mil_mulheres_censo2022)}</strong><p>${fmtInt(branca2024.obitos_mulheres_agressao)} mortes por agressão</p></article>
    <article><span>Raça não informada no SIM</span><strong>${fmt2(negra2024.percentual_raca_nao_informada)}%</strong><p>Parcela do total de 2024</p></article>`;

  const sinanRows = state.data.sinanRace.filter(row => row.sigla_uf === territory);
  const sinanNegra = sinanRows.find(row => row.raca === 'Negra');
  const sinanBranca = sinanRows.find(row => row.raca === 'Branca');
  document.getElementById('sinan-race-summary').innerHTML = `
    <article><span>Mulheres negras</span><strong>${fmt2(sinanNegra.indice_representacao)}</strong><p>${fmt1(sinanNegra.percentual_raca_entre_informadas)}% das notificações e ${fmt1(sinanNegra.percentual_raca_populacao_censo)}% da população</p></article>
    <article><span>Mulheres brancas</span><strong>${fmt2(sinanBranca.indice_representacao)}</strong><p>${fmt1(sinanBranca.percentual_raca_entre_informadas)}% das notificações e ${fmt1(sinanBranca.percentual_raca_populacao_censo)}% da população</p></article>
    <article><span>Raça não informada no SINAN</span><strong>${fmt2(sinanNegra.percentual_raca_nao_informada)}%</strong><p>${fmtInt(sinanNegra.registros_raca_nao_informada)} notificações em 2024</p></article>`;

  const raisRows = state.data.raisSex
    .filter(row => row.id_territorio === territory)
    .sort((a, b) => Number(a.ano) - Number(b.ano));
  lineChart('rais-participation-chart', [{
    label: territoryLabel,
    color: COLORS.sc,
    data: raisRows.map(row => ({ year: Number(row.ano), value: Number(row.participacao_feminina_pct) }))
  }], { label: 'Participação feminina nos vínculos formais', tooltip: row => `${fmt1(row.value)}%`, endFormat: row => `${fmt1(row.value)}%` });
  lineChart('rais-salary-chart', [{
    label: territoryLabel,
    color: COLORS.city,
    data: raisRows.map(row => ({ year: Number(row.ano), value: Number(row.razao_salarial_mulher_homem) * 100 }))
  }], { label: 'Razão salarial mulher e homem', tooltip: row => `${fmt1(row.value)}%`, endFormat: row => `${fmt1(row.value)}%` });

  const insertion = state.data.raisInsertion.find(row => row.id_territorio === territory && Number(row.ano) === 2025);
  const racialSalary = state.data.raisSalaryRace.find(row => row.id_territorio === territory && Number(row.ano) === 2025);
  const mortalityRatio = Number(negra2024.taxa_100mil_mulheres_censo2022) / Number(branca2024.taxa_100mil_mulheres_censo2022);
  const notificationRatio = Number(sinanNegra.indice_representacao);
  const insertionRatio = Number(insertion.indice_insercao_formal_mulheres_negras);
  const salaryRatio = Number(racialSalary.razao_mulheres_negras_homens_brancos);
  document.getElementById('relation-profile').innerHTML = `
    <div class="relation-scale"><span>0</span><span>Referência 1,0</span><span>2,0 ou mais</span></div>
    ${relationRow('Mortalidade', mortalityRatio, 'Taxa de mulheres negras dividida pela taxa de mulheres brancas, SIM e Censo 2022', 'adverse')}
    ${relationRow('Notificações', notificationRatio, 'Presença de mulheres negras nas notificações dividida pela presença no Censo, SINAN 2024', 'adverse')}
    ${relationRow('Inserção formal', insertionRatio, 'Presença de mulheres negras entre trabalhadoras formais dividida pela presença no Censo, RAIS 2025', 'protective')}
    ${relationRow('Remuneração', salaryRatio, 'Salário médio de mulheres negras dividido pelo salário médio de homens brancos, RAIS 2025', 'protective')}`;
  document.getElementById('relation-reading').innerHTML = `
    <p class="source-name">Leitura de ${esc(territoryLabel)}</p>
    <h3>As bases não são somadas. Elas descrevem dimensões que coexistem no território.</h3>
    <p>Em 2024, a taxa de mortes por agressão de mulheres negras foi <strong>${fmt2(mortalityRatio)} vezes</strong> a taxa de mulheres brancas. Nas notificações, a presença de mulheres negras correspondeu a <strong>${fmt2(notificationRatio)} vezes</strong> sua participação na população feminina.</p>
    <p>Em 2025, a presença de mulheres negras no emprego formal correspondeu a <strong>${fmt2(insertionRatio)} vezes</strong> sua participação no Censo. A remuneração média equivaleu a <strong>${fmt1(salaryRatio * 100)}%</strong> da remuneração de homens brancos.</p>
    <p class="relation-caution">É um perfil territorial integrado. Não permite afirmar que as mesmas pessoas aparecem nas diferentes bases.</p>`;
  renderEmploymentViolence(territory);
  const cityName = selectedMunicipalityName();
  const cityBlack = state.data.simRaceMunicipal.find(row => row.id_municipio === state.municipalityId && row.raca === 'Negra');
  const cityWhite = state.data.simRaceMunicipal.find(row => row.id_municipio === state.municipalityId && row.raca === 'Branca');
  const cityJob = state.data.raisSexMunicipal.find(row => row.id_territorio === state.municipalityId);
  const cityRaceSalary = state.data.raisSalaryRaceMunicipal.find(row => row.id_territorio === state.municipalityId);
  document.getElementById('territorial-race-title').textContent = `Brasil, Santa Catarina e ${cityName}`;
  document.getElementById('inequality-stats').innerHTML = `
    <article><span>Inserção formal de mulheres negras em ${esc(territoryLabel)}</span><strong>${fmt2(insertion.indice_insercao_formal_mulheres_negras)}</strong><small>RAIS 2025 em relação à participação no Censo</small></article>
    <article><span>Salário de mulheres negras em ${esc(territoryLabel)}</span><strong>${fmt1(Number(racialSalary.razao_mulheres_negras_homens_brancos) * 100)}%</strong><small>Em relação aos homens brancos, RAIS 2025</small></article>
    <article><span>Taxa de mortes de mulheres negras em ${esc(cityName)}</span><strong>${cityBlack ? fmt2(cityBlack.taxa_anual_media_100mil_mulheres_censo2022) : 'n.a.'}</strong><small>Mulheres brancas: ${cityWhite ? fmt2(cityWhite.taxa_anual_media_100mil_mulheres_censo2022) : 'n.a.'}. Média anual de 2019 a 2024</small></article>
    <article><span>Participação feminina no emprego formal em ${esc(cityName)}</span><strong>${cityJob ? `${fmt1(cityJob.participacao_feminina_pct)}%` : 'n.a.'}</strong><small>Razão salarial mulher e homem: ${cityJob && cityJob.razao_salarial_mulher_homem ? `${fmt1(Number(cityJob.razao_salarial_mulher_homem) * 100)}%` : 'n.a.'}</small></article>
    <article><span>Salário de mulheres negras em ${esc(cityName)}</span><strong>${cityRaceSalary && cityRaceSalary.razao_mulheres_negras_homens_brancos ? `${fmt1(Number(cityRaceSalary.razao_mulheres_negras_homens_brancos) * 100)}%` : 'n.a.'}</strong><small>Em relação aos homens brancos, RAIS 2024 e 2025</small></article>
    <article><span>Raça não informada na RAIS de ${esc(territoryLabel)}</span><strong>${fmt2(insertion.pct_raca_nao_identificada)}%</strong><small>${insertion.flag_cautela_acima_10pct === 'True' ? 'Resultado com cautela' : 'Abaixo do limite de cautela de 10%'}</small></article>`;
}

function renderMunicipality() {
  const name = selectedMunicipalityName();
  document.getElementById('municipality-title').textContent = name;
  const row = state.data.municipal.find(item => item.id_municipio === state.municipalityId);
  if (!row) return;
  const ranking = row.ranking_taxa_apenas_dado_suficiente ? `${row.ranking_taxa_apenas_dado_suficiente}ª` : 'Sem posição';
  document.getElementById('municipality-stats').innerHTML = `<article><span>Feminicídios de 2019 a 2024</span><strong>${fmtInt(row.feminicidios_total)}</strong><small>Local do fato</small></article><article><span>Média anual</span><strong>${fmt2(row.media_anual_feminicidios)}</strong><small>Vítimas por ano</small></article><article><span>Taxa plurianual</span><strong>${fmt2(row.taxa_feminicidio_100mil_mulheres_ano)}</strong><small>Por 100 mil mulheres ao ano</small></article><article><span>Posição entre séries suficientes</span><strong>${ranking}</strong><small>${row.dado_suficiente === 'True' ? 'Pelo menos cinco vítimas' : 'Menos de cinco vítimas'}</small></article>`;
  const history = state.data.history.filter(item => item.nivel_territorial === 'municipio' && item.id_territorio === state.municipalityId).sort((a, b) => Number(a.ano) - Number(b.ano));
  document.getElementById('municipality-history').innerHTML = history.map(item => `<tr><td>${item.ano}</td><td>${fmtInt(item.sinan_notificacoes)} <span class="muted">(${fmt1(item.sinan_taxa_notificacoes_100mil)})</span></td><td>${fmtInt(item.sim_obitos_mulheres_agressao)} <span class="muted">(${fmt1(item.sim_taxa_obitos_agressao_100mil)})</span></td><td>${fmtInt(item.sinesp_vitimas_feminicidio)} <span class="muted">(${fmt1(item.sinesp_taxa_feminicidio_100mil)})</span></td></tr>`).join('');
  const eligible = state.data.municipal.filter(item => item.dado_suficiente === 'True').sort((a, b) => Number(b.taxa_feminicidio_100mil_mulheres_ano) - Number(a.taxa_feminicidio_100mil_mulheres_ano));
  const visible = eligible.slice(0, 10);
  if (!visible.some(item => item.id_municipio === state.municipalityId) && row.dado_suficiente === 'True') visible.push(row);
  const max = Number(eligible[0].taxa_feminicidio_100mil_mulheres_ano) || 1;
  document.getElementById('municipality-ranking').innerHTML = visible.map(item => `<div class="rank-row ${item.id_municipio === state.municipalityId ? 'selected' : ''}"><span>${item.ranking_taxa_apenas_dado_suficiente}ª</span><strong>${esc(item.municipio)}</strong><span class="rank-track"><i style="width:${Number(item.taxa_feminicidio_100mil_mulheres_ano) / max * 100}%"></i></span><b>${fmt2(item.taxa_feminicidio_100mil_mulheres_ano)}</b></div>`).join('');
}

function populateMunicipalities() {
  const municipalities = [...new Map(state.data.monitoring.filter(row => row.nivel_territorial === 'municipio').map(row => [row.id_territorio, row.territorio])).entries()].map(([id, name]) => ({ id, name })).sort((a, b) => a.name.localeCompare(b.name, 'pt-BR'));
  const preferred = municipalities.find(item => item.name === 'Florianópolis') || municipalities[0];
  state.municipalityId = preferred.id;
  document.querySelectorAll('[data-municipality-select]').forEach(select => { select.innerHTML = municipalities.map(item => `<option value="${esc(item.id)}">${esc(item.name)}</option>`).join(''); select.value = state.municipalityId; });
}

function syncMunicipalities() {
  document.querySelectorAll('[data-municipality-select]').forEach(select => { select.value = state.municipalityId; });
}

function bindEvents() {
  document.querySelectorAll('[data-view-target]').forEach(button => button.addEventListener('click', () => setView(button.dataset.viewTarget)));
  document.querySelectorAll('[data-year]').forEach(button => button.addEventListener('click', () => { state.year = Number(button.dataset.year); renderMonitoring(); }));
  document.querySelectorAll('[data-municipality-select]').forEach(select => select.addEventListener('change', event => { state.municipalityId = event.target.value; syncMunicipalities(); renderMonitoring(); renderHistory(); renderMunicipality(); renderInequalities(); }));
  document.querySelectorAll('[data-history-metric]').forEach(button => button.addEventListener('click', () => { state.historyMetric = button.dataset.historyMetric; renderHistory(); }));
  document.querySelectorAll('[data-indicator-territory]').forEach(button => button.addEventListener('click', () => { state.indicatorTerritory = button.dataset.indicatorTerritory; renderIndicatorCharts(); }));
  document.querySelectorAll('[data-inequality-territory]').forEach(button => button.addEventListener('click', () => { state.inequalityTerritory = button.dataset.inequalityTerritory; renderInequalities(); }));
}

async function init() {
  try {
    const entries = await Promise.all(Object.entries(URLS).map(async ([key, url]) => {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`Falha ao carregar ${key}: ${response.status}`);
      return [key, parseCsv(await response.text())];
    }));
    state.data = Object.fromEntries(entries);
    populateMunicipalities();
    bindEvents();
    renderMonitoring();
    renderHistory();
    renderRatio();
    renderIndicatorCharts();
    renderInequalities();
    renderMunicipality();
    const initial = window.location.hash.replace('#', '');
    setView(initial || 'monitoramento', false);
  } catch (error) {
    document.getElementById('conteudo').innerHTML = `<p class="page-width error">Não foi possível abrir a simulação. ${esc(error.message)}</p>`;
  }
}

init();
