const integer = new Intl.NumberFormat('pt-BR');
const decimal = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const compact = new Intl.NumberFormat('pt-BR', { notation: 'compact', maximumFractionDigits: 1 });

const COLORS = { brasil: '#316a91', santa_catarina: '#147665', municipio: '#8d1734' };
const state = { data: null, municipalityId: null, metric: 'rate', allLabels: false };

function fmtInt(value) { return integer.format(Math.round(Number(value) || 0)); }
function fmt1(value) { return decimal.format(Number(value) || 0); }
function pct(value) { return `${fmt1(value)}%`; }
function signedPct(value) { return `${value >= 0 ? '+' : ''}${fmt1(value)}%`; }
function esc(value) { return String(value).replace(/[&<>'"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[c])); }
function last(series) { return series[series.length - 1]; }
function change(first, final) { return first ? (final / first - 1) * 100 : 0; }

function selectedMunicipality() {
  return state.data.municipios_sc.find(item => item.id === state.municipalityId) || state.data.municipios_sc[0];
}

function comparisonSeries() {
  const municipality = selectedMunicipality();
  return [
    { key: 'brasil', label: 'Brasil', color: COLORS.brasil, data: state.data.series.brasil },
    { key: 'santa_catarina', label: 'Santa Catarina', color: COLORS.santa_catarina, data: state.data.series.santa_catarina },
    { key: 'municipio', label: municipality.nome, color: COLORS.municipio, data: municipality.serie },
  ];
}

function metricValue(item, metric, baseline) {
  if (metric === 'absolute') return Number(item.notificacoes);
  if (metric === 'index') return baseline ? Number(item.notificacoes) / baseline * 100 : 0;
  return Number(item.taxa_notificacoes_100mil);
}

function metricLabel(metric) {
  return metric === 'absolute' ? 'Notificações' : metric === 'index' ? 'Índice (2015 = 100)' : 'Taxa por 100 mil mulheres';
}

function axisFormat(value, metric) {
  if (metric === 'absolute') return compact.format(value);
  return fmt1(value);
}

function lineChart(targetId, series, options = {}) {
  const host = document.getElementById(targetId);
  if (!host || !series.length) return;
  host.classList.add('chart-host');
  const metric = options.metric || 'rate';
  const width = 1180;
  const height = options.height || 440;
  const pad = { left: 72, right: series.length > 1 ? 190 : 80, top: 42, bottom: 54 };
  const plotWidth = width - pad.left - pad.right;
  const plotHeight = height - pad.top - pad.bottom;
  const years = series[0].data.map(row => row.ano);
  const prepared = series.map(item => {
    const baseline = Number(item.data[0].notificacoes);
    return { ...item, values: item.data.map(row => metricValue(row, metric, baseline)) };
  });
  const rawMax = Math.max(...prepared.flatMap(item => item.values));
  const max = rawMax * 1.12 || 1;
  const x = index => pad.left + index / Math.max(1, years.length - 1) * plotWidth;
  const y = value => pad.top + (1 - value / max) * plotHeight;
  const ticks = [0, .25, .5, .75, 1];
  const showEveryLabel = options.allLabels || series.length === 1;
  const labelValue = (row, value) => metric === 'rate'
    ? `${fmt1(value)} · ${fmtInt(row.notificacoes)}`
    : metric === 'absolute' ? fmtInt(value) : fmt1(value);

  const paths = prepared.map(item => {
    const d = item.values.map((value, index) => `${index ? 'L' : 'M'} ${x(index)} ${y(value)}`).join(' ');
    const points = item.values.map((value, index) => {
      const row = item.data[index];
      const allLabel = showEveryLabel ? `<text class="data-label" x="${x(index)}" y="${y(value) - 11}" text-anchor="middle">${labelValue(row, value)}</text>` : '';
      return `<circle class="point" cx="${x(index)}" cy="${y(value)}" r="4" fill="${item.color}"><title>${esc(item.label)}, ${row.ano}: ${fmt1(row.taxa_notificacoes_100mil)} por 100 mil (${fmtInt(row.notificacoes)} notificações)</title></circle>${allLabel}`;
    }).join('');
    const finalRow = last(item.data);
    const finalValue = last(item.values);
    const endLabel = series.length > 1
      ? `<text class="data-label end-label" x="${x(years.length - 1) + 14}" y="${y(finalValue) + 4}" fill="${item.color}">${esc(item.label)} · ${labelValue(finalRow, finalValue)}</text>`
      : '';
    return `<path class="series-line" d="${d}" stroke="${item.color}"/>${points}${endLabel}`;
  }).join('');

  host.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(options.ariaLabel || metricLabel(metric))}">
    ${ticks.map(tick => `<line class="grid" x1="${pad.left}" x2="${width - pad.right}" y1="${y(max * tick)}" y2="${y(max * tick)}"/><text x="${pad.left - 12}" y="${y(max * tick) + 4}" text-anchor="end">${axisFormat(max * tick, metric)}</text>`).join('')}
    <line class="axis" x1="${pad.left}" x2="${width - pad.right}" y1="${height - pad.bottom}" y2="${height - pad.bottom}"/>
    ${years.map((year, index) => `<text x="${x(index)}" y="${height - 20}" text-anchor="middle">${year}</text>`).join('')}
    ${paths}
    <g class="hover-layer" visibility="hidden"><line class="crosshair" x1="0" x2="0" y1="${pad.top}" y2="${height - pad.bottom}"/>${prepared.map(item => `<circle class="hover-point" r="6" fill="${item.color}" stroke="#fffefa" stroke-width="3"/>`).join('')}</g>
    <rect class="overlay" x="${pad.left}" y="${pad.top}" width="${plotWidth}" height="${plotHeight}"/>
  </svg><div class="hover-card" hidden></div>`;

  const svg = host.querySelector('svg');
  const overlay = host.querySelector('.overlay');
  const hoverLayer = host.querySelector('.hover-layer');
  const crosshair = host.querySelector('.crosshair');
  const hoverPoints = [...host.querySelectorAll('.hover-point')];
  const card = host.querySelector('.hover-card');

  function show(event) {
    const rect = svg.getBoundingClientRect();
    const scaleX = width / rect.width;
    const svgX = (event.clientX - rect.left) * scaleX;
    const index = Math.max(0, Math.min(years.length - 1, Math.round((svgX - pad.left) / plotWidth * (years.length - 1))));
    const cx = x(index);
    hoverLayer.setAttribute('visibility', 'visible');
    crosshair.setAttribute('x1', cx); crosshair.setAttribute('x2', cx);
    hoverPoints.forEach((point, i) => { point.setAttribute('cx', cx); point.setAttribute('cy', y(prepared[i].values[index])); });
    card.hidden = false;
    card.innerHTML = `<strong>${years[index]}</strong>${prepared.map(item => {
      const row = item.data[index];
      return `<div class="hover-row"><i style="--dot:${item.color}"></i><span>${esc(item.label)}</span><b>${fmt1(row.taxa_notificacoes_100mil)} · ${fmtInt(row.notificacoes)}</b></div>`;
    }).join('')}<small>taxa/100 mil · total absoluto</small>`;
    const localX = event.clientX - host.getBoundingClientRect().left;
    card.style.left = `${Math.min(Math.max(8, localX + 16), host.clientWidth - card.offsetWidth - 8)}px`;
    card.style.top = `${Math.max(8, event.clientY - host.getBoundingClientRect().top - card.offsetHeight - 12)}px`;
  }
  overlay.addEventListener('pointermove', show);
  overlay.addEventListener('pointerdown', show);
  overlay.addEventListener('pointerleave', () => { hoverLayer.setAttribute('visibility', 'hidden'); card.hidden = true; });
}

function renderTerritoryKey() {
  document.getElementById('territory-key').innerHTML = comparisonSeries().map(item => {
    const row = last(item.data);
    return `<div class="key-item"><i class="key-line" style="--key:${item.color}"></i><span>${esc(item.label)}</span><small>${fmt1(row.taxa_notificacoes_100mil)} · ${fmtInt(row.notificacoes)}</small></div>`;
  }).join('');
}

function renderCompareTable() {
  const series = comparisonSeries();
  document.getElementById('compare-table-head').innerHTML = `<tr><th>Ano</th>${series.map(item => `<th>${esc(item.label)}<br>taxa (total)</th>`).join('')}</tr>`;
  document.getElementById('compare-table-body').innerHTML = series[0].data.map((_, index) => `<tr><td>${series[0].data[index].ano}</td>${series.map(item => {
    const row = item.data[index];
    return `<td>${fmt1(row.taxa_notificacoes_100mil)} <span class="muted">(${fmtInt(row.notificacoes)})</span></td>`;
  }).join('')}</tr>`).join('');
}

function renderCompareFinding() {
  const series = comparisonSeries();
  const br = last(series[0].data); const sc = last(series[1].data); const city = last(series[2].data);
  const vsSc = (city.taxa_notificacoes_100mil / sc.taxa_notificacoes_100mil - 1) * 100;
  const vsBr = (city.taxa_notificacoes_100mil / br.taxa_notificacoes_100mil - 1) * 100;
  const trajectory = change(series[2].data[0].taxa_notificacoes_100mil, city.taxa_notificacoes_100mil);
  const relation = value => value >= 0 ? `${fmt1(Math.abs(value))}% acima` : `${fmt1(Math.abs(value))}% abaixo`;
  const caution = city.dado_suficiente ? '' : ' Como o volume é pequeno, a taxa municipal deve ser lida com cautela.';
  document.getElementById('compare-finding').textContent = `Em 2024, ${series[2].label} registrou taxa ${relation(vsSc)} da catarinense e ${relation(vsBr)} da nacional. Desde 2015, a taxa municipal variou ${signedPct(trajectory)}.${caution}`;
}

function renderComparison() {
  renderTerritoryKey();
  lineChart('compare-chart', comparisonSeries(), { metric: state.metric, height: 500, allLabels: state.allLabels, ariaLabel: `Comparação de ${metricLabel(state.metric)} entre Brasil, Santa Catarina e ${selectedMunicipality().nome}` });
  document.getElementById('compare-chart-title').textContent = metricLabel(state.metric);
  document.getElementById('compare-chart-note').textContent = state.metric === 'rate'
    ? 'Registros por 100 mil mulheres; o valor absoluto aparece junto ao dado.'
    : state.metric === 'absolute' ? 'Volume registrado em cada território; compare escalas com cautela.' : 'Trajetória relativa ao primeiro ano; 2015 corresponde a 100.';
  renderCompareTable();
  renderCompareFinding();
}

function statsMarkup(series, partnerLabel) {
  const current = last(series); const previous = series[series.length - 2];
  const delta = change(previous.notificacoes, current.notificacoes);
  return `<div class="stat"><span>Notificações em 2024</span><strong>${fmtInt(current.notificacoes)}</strong><small>${signedPct(delta)} ante 2023</small></div>
    <div class="stat"><span>Taxa por 100 mil</span><strong>${fmt1(current.taxa_notificacoes_100mil)}</strong><small>${fmtInt(current.populacao_feminina)} mulheres no denominador</small></div>
    <div class="stat"><span>${partnerLabel}</span><strong>${fmtInt(current.parceiro)}</strong><small>${pct(current.percentual_parceiro)} dos registros</small></div>
    <div class="stat"><span>Na residência</span><strong>${fmtInt(current.residencia)}</strong><small>${pct(current.residencia / current.notificacoes * 100)} do total</small></div>`;
}

function profileMarkup(profile) {
  const group = (title, rows, type = '') => {
    const visible = rows.filter(row => row.categoria !== 'Ignorada').slice(0, type ? 5 : 6);
    const max = Math.max(...visible.map(row => row.percentual), 1);
    return `<div class="profile-block"><h3>${title}</h3>${visible.map(row => `<div class="profile-row ${type}"><span>${esc(row.categoria)}</span><span class="track"><i class="fill" style="--w:${row.percentual / max * 100}%"></i></span><strong>${pct(row.percentual)}</strong></div>`).join('')}</div>`;
  };
  return group('Raça/cor', profile.raca) + group('Faixa etária', profile.idade) + group('Tipo de violência*', profile.tipos, 'type') + '<p class="interaction-note">*Uma notificação pode registrar mais de um tipo.</p>';
}

function renderBrazil() {
  const series = state.data.series.brasil;
  document.getElementById('brasil-stats').innerHTML = statsMarkup(series, 'Parceiro ou ex-parceiro');
  lineChart('brasil-chart', [{ label: 'Brasil', color: COLORS.brasil, data: series }], { metric: 'rate', ariaLabel: 'Evolução da taxa nacional de notificações, com totais absolutos' });
  const ranking = state.data.ufs.map(item => ({ ...item, row: last(item.serie) })).sort((a, b) => b.row.taxa_notificacoes_100mil - a.row.taxa_notificacoes_100mil);
  const scIndex = ranking.findIndex(item => item.sigla === 'SC');
  const sc = ranking[scIndex];
  const br = last(series);
  document.getElementById('brasil-position').textContent = `Santa Catarina ocupa a ${scIndex + 1}ª posição entre as 27 UFs em 2024. Sua taxa de ${fmt1(sc.row.taxa_notificacoes_100mil)} é ${sc.row.taxa_notificacoes_100mil >= br.taxa_notificacoes_100mil ? 'superior' : 'inferior'} à nacional (${fmt1(br.taxa_notificacoes_100mil)}).`;
  const top = ranking.slice(0, 10);
  if (!top.some(item => item.sigla === 'SC')) top.push(sc);
  const rankMax = ranking[0].row.taxa_notificacoes_100mil;
  document.getElementById('uf-ranking').innerHTML = top.map(item => `<div class="rank-row ${item.sigla === 'SC' ? 'sc' : ''}"><span>${ranking.indexOf(item) + 1}</span><strong>${item.sigla}</strong><span class="track"><i class="fill" style="--w:${item.row.taxa_notificacoes_100mil / rankMax * 100}%"></i></span><span>${fmt1(item.row.taxa_notificacoes_100mil)}</span></div>`).join('');
  document.getElementById('uf-table').innerHTML = ranking.map((item, index) => `<tr class="${item.sigla === 'SC' ? 'sc-row' : ''}"><td>${index + 1}ª</td><td class="text-cell">${item.sigla}</td><td>${fmt1(item.row.taxa_notificacoes_100mil)}</td><td>${fmtInt(item.row.notificacoes)}</td><td>${fmtInt(item.row.parceiro)}</td></tr>`).join('');
  document.getElementById('brasil-profile').innerHTML = profileMarkup(state.data.perfis_2024.brasil);
}

function scatterChart() {
  const host = document.getElementById('municipality-scatter');
  const rows = state.data.municipios_sc.map(item => ({ nome: item.nome, ...last(item.serie) }));
  const width = 760; const height = 390; const pad = { left: 68, right: 26, top: 24, bottom: 58 };
  const xMax = Math.max(...rows.map(row => row.notificacoes)) * 1.06;
  const sufficientRates = rows.filter(row => row.dado_suficiente).map(row => row.taxa_notificacoes_100mil).sort((a, b) => a - b);
  const yMax = sufficientRates[Math.floor(sufficientRates.length * .97)] * 1.15;
  const x = value => pad.left + value / xMax * (width - pad.left - pad.right);
  const y = value => height - pad.bottom - Math.min(value, yMax) / yMax * (height - pad.top - pad.bottom);
  const ticks = [0, .25, .5, .75, 1];
  host.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Relação entre taxa e volume de notificações nos municípios catarinenses em 2024">
    ${ticks.map(t => `<line class="grid" x1="${pad.left}" x2="${width - pad.right}" y1="${y(yMax * t)}" y2="${y(yMax * t)}"/><text x="${pad.left - 10}" y="${y(yMax * t) + 4}" text-anchor="end">${fmt1(yMax * t)}</text>`).join('')}
    <line class="axis" x1="${pad.left}" x2="${width - pad.right}" y1="${height - pad.bottom}" y2="${height - pad.bottom}"/>
    ${ticks.map(t => `<text x="${x(xMax * t)}" y="${height - 28}" text-anchor="middle">${compact.format(xMax * t)}</text>`).join('')}
    <text x="${width / 2}" y="${height - 5}" text-anchor="middle">Notificações (volume)</text>
    ${rows.map(row => `<circle cx="${x(row.notificacoes)}" cy="${y(row.taxa_notificacoes_100mil)}" r="${row.dado_suficiente ? 3.8 : 2.7}" fill="${row.dado_suficiente ? COLORS.green || '#147665' : '#9b6b16'}" opacity=".68"><title>${esc(row.nome)}: ${fmt1(row.taxa_notificacoes_100mil)} por 100 mil · ${fmtInt(row.notificacoes)} notificações${row.dado_suficiente ? '' : ' · cautela estatística'}</title></circle>`).join('')}
  </svg>`;
}

function municipalityRows(query = '') {
  const normalized = query.trim().toLocaleLowerCase('pt-BR');
  const rows = state.data.municipios_sc.map(item => ({ ...item, row: last(item.serie) }))
    .sort((a, b) => b.row.taxa_notificacoes_100mil - a.row.taxa_notificacoes_100mil);
  const ranking = new Map(rows.map((item, index) => [item.id, index + 1]));
  return rows.filter(item => item.nome.toLocaleLowerCase('pt-BR').includes(normalized)).map(item => ({ ...item, position: ranking.get(item.id) }));
}

function renderMunicipalityTable(query = '') {
  const rows = municipalityRows(query);
  document.getElementById('municipality-table').innerHTML = rows.map(item => `<tr><td>${item.position}ª</td><td class="text-cell">${esc(item.nome)}</td><td>${fmt1(item.row.taxa_notificacoes_100mil)}</td><td>${fmtInt(item.row.notificacoes)}</td><td>${fmtInt(item.row.parceiro)}</td><td>${item.row.dado_suficiente ? 'Série suficiente' : '<span class="status-note">Cautela: baixo volume</span>'}</td></tr>`).join('') || '<tr><td colspan="6" class="text-cell">Nenhum município encontrado.</td></tr>';
}

function renderSantaCatarina() {
  const sc = state.data.series.santa_catarina;
  document.getElementById('sc-stats').innerHTML = statsMarkup(sc, 'Parceiro ou ex-parceiro');
  lineChart('sc-chart', [
    { label: 'Brasil', color: COLORS.brasil, data: state.data.series.brasil },
    { label: 'Santa Catarina', color: COLORS.santa_catarina, data: sc },
  ], { metric: 'rate', ariaLabel: 'Comparação das taxas de Brasil e Santa Catarina' });
  scatterChart();
  document.getElementById('sc-profile').innerHTML = profileMarkup(state.data.perfis_2024.santa_catarina);
  renderMunicipalityTable();
}

function populateMunicipalities() {
  const select = document.getElementById('municipio-select');
  select.innerHTML = state.data.municipios_sc.map(item => `<option value="${item.id}">${esc(item.nome)}</option>`).join('');
  const preferred = state.data.municipios_sc.find(item => item.nome === 'Florianópolis') || state.data.municipios_sc.find(item => item.nome === 'Joinville') || state.data.municipios_sc[0];
  state.municipalityId = preferred.id;
  select.value = preferred.id;
}

function setView(name, updateHash = true) {
  const next = ['comparar', 'brasil', 'santa-catarina', 'dados'].includes(name) ? name : 'comparar';
  document.querySelectorAll('[data-view]').forEach(view => { const active = view.dataset.view === next; view.hidden = !active; view.classList.toggle('active', active); });
  document.querySelectorAll('[data-view-target]').forEach(button => { const active = button.dataset.viewTarget === next; button.classList.toggle('active', active); if (active) button.setAttribute('aria-current', 'page'); else button.removeAttribute('aria-current'); });
  if (updateHash) history.replaceState(null, '', `#${next}`);
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function bindEvents() {
  document.querySelectorAll('[data-view-target]').forEach(button => button.addEventListener('click', () => setView(button.dataset.viewTarget)));
  document.getElementById('municipio-select').addEventListener('change', event => { state.municipalityId = event.target.value; renderComparison(); });
  document.querySelectorAll('[data-metric]').forEach(button => button.addEventListener('click', () => {
    state.metric = button.dataset.metric;
    document.querySelectorAll('[data-metric]').forEach(item => item.classList.toggle('active', item === button));
    renderComparison();
  }));
  document.getElementById('all-labels').addEventListener('change', event => { state.allLabels = event.target.checked; renderComparison(); });
  document.getElementById('municipality-search').addEventListener('input', event => renderMunicipalityTable(event.target.value));
  window.addEventListener('hashchange', () => setView(location.hash.slice(1), false));
}

async function init() {
  try {
    const response = await fetch('data/analise.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.data = await response.json();
    populateMunicipalities();
    renderComparison();
    renderBrazil();
    renderSantaCatarina();
    document.getElementById('data-updated').textContent = new Date(`${state.data.meta.gerado_em}T12:00:00`).toLocaleDateString('pt-BR');
    bindEvents();
    setView(location.hash.slice(1) || 'comparar', false);
  } catch (error) {
    document.getElementById('conteudo').innerHTML = '<section class="page-intro content-width"><div><p class="eyebrow">Falha de carregamento</p><h1>Os dados não puderam ser abertos.</h1><p class="dek">Verifique o pacote analítico e tente novamente.</p></div></section>';
    console.error(error);
  }
}

init();
