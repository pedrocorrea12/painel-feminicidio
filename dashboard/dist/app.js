const number = new Intl.NumberFormat('pt-BR');
const decimal = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
let data;
let currentTerritory = 'santa_catarina';

const territoryLabel = {
  brasil: 'Brasil',
  santa_catarina: 'Santa Catarina',
  florianopolis: 'Florianópolis'
};

const viewMeta = {
  'visao-geral': ['Painel de indicadores', 'Visão geral'],
  evolucao: ['Análise temporal', 'Evolução'],
  territorios: ['Análise geográfica', 'Territórios'],
  perfil: ['Características dos registros', 'Perfil'],
  metodologia: ['Transparência dos dados', 'Metodologia']
};

function percent(value) {
  return `${decimal.format(Number(value))}%`;
}

function compact(value) {
  if (value >= 1_000_000) return `${decimal.format(value / 1_000_000)} mi`;
  if (value >= 1_000) return `${decimal.format(value / 1_000)} mil`;
  return number.format(Math.round(value));
}

function linePath(values, x, y) {
  return values.map((item, index) => `${index ? 'L' : 'M'} ${x(item.ano)} ${y(item.valor)}`).join(' ');
}

function areaPath(values, x, y, baseline) {
  return `${linePath(values, x, y)} L ${x(values.at(-1).ano)} ${baseline} L ${x(values[0].ano)} ${baseline} Z`;
}

function renderLineChart(targetSelector, series, large = false) {
  const target = document.querySelector(targetSelector);
  if (!target || !series?.length) return;
  const width = 980;
  const height = large ? 380 : 270;
  const pad = { l: 58, r: 18, t: 20, b: 35 };
  const max = Math.max(...series.map(item => item.notificacoes)) * 1.08;
  const range = series.at(-1).ano - series[0].ano || 1;
  const x = year => pad.l + (year - series[0].ano) / range * (width - pad.l - pad.r);
  const y = value => height - pad.b - value / max * (height - pad.t - pad.b);
  const total = series.map(item => ({ ano: item.ano, valor: item.notificacoes }));
  const partner = series.map(item => ({ ano: item.ano, valor: item.parceiro }));
  const ticks = [0, .25, .5, .75, 1];
  const baseline = height - pad.b;
  target.innerHTML = `<svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" aria-hidden="true">
    ${ticks.map(tick => `<line class="grid" x1="${pad.l}" x2="${width - pad.r}" y1="${y(max * tick)}" y2="${y(max * tick)}"/><text x="${pad.l - 10}" y="${y(max * tick) + 4}" text-anchor="end">${compact(max * tick)}</text>`).join('')}
    <line class="axis-line" x1="${pad.l}" x2="${width - pad.r}" y1="${baseline}" y2="${baseline}"/>
    ${series.map(item => `<text x="${x(item.ano)}" y="${height - 11}" text-anchor="middle">${item.ano}</text>`).join('')}
    <path class="area-total" d="${areaPath(total, x, y, baseline)}"/>
    <path class="line-total" d="${linePath(total, x, y)}"/>
    <path class="line-partner" d="${linePath(partner, x, y)}"/>
    ${total.map(item => `<circle cx="${x(item.ano)}" cy="${y(item.valor)}" r="3.5" fill="#253247"><title>${item.ano}: ${number.format(item.valor)} notificações</title></circle>`).join('')}
    ${partner.map(item => `<circle cx="${x(item.ano)}" cy="${y(item.valor)}" r="3" fill="#c93e5a"><title>${item.ano}: ${number.format(item.valor)} com parceiro/ex</title></circle>`).join('')}
  </svg>`;
  const first = series[0];
  const last = series.at(-1);
  target.setAttribute('aria-label', `Em ${territoryLabel[currentTerritory]}, as notificações passaram de ${number.format(first.notificacoes)} em ${first.ano} para ${number.format(last.notificacoes)} em ${last.ano}.`);
}

function renderKPIs(series) {
  const last = series.at(-1);
  const previous = series.at(-2);
  const change = (last.notificacoes / previous.notificacoes - 1) * 100;
  document.querySelector('#kpi-total').textContent = number.format(last.notificacoes);
  document.querySelector('#kpi-taxa').textContent = decimal.format(last.taxa_notificacoes_100mil);
  document.querySelector('#kpi-populacao').textContent = `${number.format(last.populacao_feminina)} mulheres no denominador`;
  document.querySelector('#kpi-parceiro').textContent = number.format(last.parceiro);
  document.querySelector('#kpi-residencia').textContent = number.format(last.residencia);
  document.querySelector('#kpi-percentual').textContent = `${percent(last.percentual_parceiro)} do total`;
  document.querySelector('#kpi-variacao').textContent = `${change >= 0 ? '+' : ''}${percent(change)} em relação a ${previous.ano}`;
  document.querySelector('#insight-share').textContent = percent(last.percentual_parceiro);
  document.querySelector('#insight-copy').textContent = `das notificações de ${last.ano} em ${territoryLabel[currentTerritory]} envolveram parceiro ou ex-parceiro.`;
  document.querySelector('#insight-first').textContent = number.format(series[0].notificacoes);
  document.querySelector('#insight-last').textContent = number.format(last.notificacoes);
}

function renderSeriesTable(series) {
  document.querySelector('#series-table').innerHTML = [...series].reverse().map(item => `<tr>
    <td>${item.ano}</td><td>${number.format(item.notificacoes)}</td><td>${number.format(item.parceiro)}</td>
    <td>${percent(item.percentual_parceiro)}</td><td>${decimal.format(item.taxa_notificacoes_100mil)}</td><td>${decimal.format(item.taxa_parceiro_100mil)}</td>
  </tr>`).join('');
}

function renderSim() {
  const max = Math.max(...data.sim_referencia.map(item => item.obitos_agressao_sc));
  document.querySelector('#sim-bars').innerHTML = data.sim_referencia.map(item => `<div class="sim-item">
    <span>${item.ano}</span><span></span><strong>${number.format(item.obitos_agressao_sc)}</strong>
    <div class="sim-track" aria-hidden="true"><div class="sim-fill" style="--height:${item.obitos_agressao_sc / max * 100}%"></div></div>
  </div>`).join('');
}

function renderRanking() {
  const top = [...data.municipios_sc_2024].sort((a, b) => b.parceiro - a.parceiro).slice(0, 10);
  const max = top[0].parceiro;
  document.querySelector('#ranking').innerHTML = top.map((item, index) => `<div class="rank-row" aria-label="${item.municipio}: ${number.format(item.parceiro)} notificações com parceiro ou ex-parceiro">
    <span class="position">${String(index + 1).padStart(2, '0')}</span><span>${item.municipio}</span>
    <span class="bar-track" aria-hidden="true"><span class="bar-fill" style="--bar-size:${item.parceiro / max * 100}%"></span></span><strong>${number.format(item.parceiro)}</strong>
  </div>`).join('');
  document.querySelector('#municipal-count').textContent = number.format(data.municipios_sc_2024.filter(item => item.parceiro > 0).length);
}

function renderMunicipalTable(query = '') {
  const normalized = query.trim().toLocaleLowerCase('pt-BR');
  const rows = [...data.municipios_sc_2024]
    .filter(item => item.municipio.toLocaleLowerCase('pt-BR').includes(normalized))
    .sort((a, b) => b.parceiro - a.parceiro);
  document.querySelector('#municipal-table').innerHTML = rows.map(item => `<tr>
    <td>${item.municipio}</td><td>${number.format(item.notificacoes)}</td><td>${number.format(item.parceiro)}</td>
    <td>${percent(item.percentual_parceiro)}</td><td>${decimal.format(item.taxa_notificacoes_100mil)}</td>
  </tr>`).join('') || '<tr><td colspan="5">Nenhum município encontrado.</td></tr>';
}

function renderBars(selector, items, labelKey) {
  const max = Math.max(...items.map(item => item.notificacoes));
  document.querySelector(selector).innerHTML = items.map(item => `<div class="bar-item" aria-label="${item[labelKey]}: ${number.format(item.notificacoes)} notificações">
    <span>${item[labelKey]}</span><span class="bar-track" aria-hidden="true"><span class="bar-fill" style="--bar-size:${item.notificacoes / max * 100}%"></span></span><strong>${number.format(item.notificacoes)}</strong>
  </div>`).join('');
}

function updateTerritory(next) {
  currentTerritory = next;
  const series = data.territorios[next];
  renderKPIs(series);
  renderLineChart('#series-chart', series);
  renderLineChart('#evolution-chart', series, true);
  renderSeriesTable(series);
  document.querySelector('#evolution-territory').textContent = territoryLabel[next];
}

function setView(viewName, updateHash = true) {
  const next = viewMeta[viewName] ? viewName : 'visao-geral';
  document.querySelectorAll('[data-view]').forEach(view => {
    const active = view.dataset.view === next;
    view.hidden = !active;
    view.classList.toggle('active', active);
  });
  document.querySelectorAll('.nav-item').forEach(button => {
    const active = button.dataset.viewTarget === next;
    button.classList.toggle('active', active);
    if (active) button.setAttribute('aria-current', 'page'); else button.removeAttribute('aria-current');
  });
  document.querySelector('#page-context').textContent = viewMeta[next][0];
  document.querySelector('#page-title').textContent = viewMeta[next][1];
  if (updateHash) history.replaceState(null, '', `#${next}`);
  closeSidebar();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function openSidebar() {
  document.querySelector('#sidebar').classList.add('open');
  document.querySelector('#scrim').hidden = false;
  document.querySelector('#menu-toggle').setAttribute('aria-expanded', 'true');
}

function closeSidebar() {
  document.querySelector('#sidebar').classList.remove('open');
  document.querySelector('#scrim').hidden = true;
  document.querySelector('#menu-toggle').setAttribute('aria-expanded', 'false');
}

function bindEvents() {
  document.querySelectorAll('[data-view-target]').forEach(button => button.addEventListener('click', () => setView(button.dataset.viewTarget)));
  document.querySelector('#territory-select').addEventListener('change', event => updateTerritory(event.target.value));
  document.querySelector('#municipality-search').addEventListener('input', event => renderMunicipalTable(event.target.value));
  document.querySelector('#menu-toggle').addEventListener('click', openSidebar);
  document.querySelector('#sidebar-close').addEventListener('click', closeSidebar);
  document.querySelector('#scrim').addEventListener('click', closeSidebar);
  window.addEventListener('hashchange', () => setView(location.hash.slice(1), false));
}

async function init() {
  try {
    const response = await fetch('data/painel.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    data = await response.json();
    updateTerritory(currentTerritory);
    renderSim();
    renderRanking();
    renderMunicipalTable();
    renderBars('#race-chart', data.perfil_sc_2024.raca, 'categoria');
    renderBars('#type-chart', data.perfil_sc_2024.tipos_violencia, 'tipo');
    document.querySelector('#updated').textContent = new Date(`${data.meta.atualizado}T12:00:00`).toLocaleDateString('pt-BR');
    bindEvents();
    setView(location.hash.slice(1) || 'visao-geral', false);
  } catch (error) {
    document.querySelector('#main-content').innerHTML = '<section class="panel"><h2>Não foi possível carregar os dados.</h2><p>Verifique o arquivo da camada Gold e tente novamente.</p></section>';
    console.error(error);
  }
}

init();
