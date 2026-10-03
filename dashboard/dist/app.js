const format = new Intl.NumberFormat('pt-BR');
let data;
let current = 'santa_catarina';

const territoryLabel = {
  brasil: 'Brasil',
  santa_catarina: 'Santa Catarina',
  florianopolis: 'Florianópolis'
};

function percent(value) {
  return `${Number(value).toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%`;
}

function renderKPIs(series) {
  const last = series.at(-1);
  const previous = series.at(-2);
  const change = ((last.notificacoes / previous.notificacoes - 1) * 100);
  document.querySelector('#kpi-total').textContent = format.format(last.notificacoes);
  document.querySelector('#kpi-taxa').textContent = Number(last.taxa_notificacoes_100mil).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  document.querySelector('#kpi-populacao').textContent = `${format.format(last.populacao_feminina)} mulheres no denominador`;
  document.querySelector('#kpi-parceiro').textContent = format.format(last.parceiro);
  document.querySelector('#kpi-residencia').textContent = format.format(last.residencia);
  document.querySelector('#kpi-percentual').textContent = `${percent(last.percentual_parceiro)} do total`;
  document.querySelector('#kpi-variacao').textContent = `${change >= 0 ? '+' : ''}${percent(change)} em relação a ${previous.ano}`;
}

function linePath(values, x, y) {
  return values.map((d, i) => `${i ? 'L' : 'M'} ${x(d.ano)} ${y(d.valor)}`).join(' ');
}

function renderSeries(series) {
  const target = document.querySelector('#series-chart');
  const width = 960, height = 290, pad = { l: 58, r: 18, t: 18, b: 38 };
  const max = Math.max(...series.map(d => d.notificacoes)) * 1.1;
  const x = year => pad.l + (year - series[0].ano) / (series.at(-1).ano - series[0].ano) * (width - pad.l - pad.r);
  const y = value => height - pad.b - value / max * (height - pad.t - pad.b);
  const ticks = [0, .25, .5, .75, 1];
  const total = series.map(d => ({ ano: d.ano, valor: d.notificacoes }));
  const partner = series.map(d => ({ ano: d.ano, valor: d.parceiro }));
  target.innerHTML = `<svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" aria-hidden="true">
    ${ticks.map(t => `<line class="grid" x1="${pad.l}" x2="${width-pad.r}" y1="${y(max*t)}" y2="${y(max*t)}"/><text x="${pad.l-10}" y="${y(max*t)+4}" text-anchor="end">${compact(max*t)}</text>`).join('')}
    ${series.map(d => `<text x="${x(d.ano)}" y="${height-12}" text-anchor="middle">${d.ano}</text>`).join('')}
    <path class="line-total" d="${linePath(total, x, y)}"/>
    <path class="line-partner" d="${linePath(partner, x, y)}"/>
    ${total.map(d => `<circle cx="${x(d.ano)}" cy="${y(d.valor)}" r="4" fill="#5b4acb"><title>${d.ano}: ${format.format(d.valor)}</title></circle>`).join('')}
    ${partner.map(d => `<circle cx="${x(d.ano)}" cy="${y(d.valor)}" r="3" fill="#e82f68"><title>${d.ano}: ${format.format(d.valor)}</title></circle>`).join('')}
  </svg>`;
  target.setAttribute('aria-label', `Evolução das notificações em ${territoryLabel[current]}, de ${format.format(series[0].notificacoes)} em ${series[0].ano} para ${format.format(series.at(-1).notificacoes)} em ${series.at(-1).ano}. A taxa mais recente é ${Number(series.at(-1).taxa_notificacoes_100mil).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} por 100 mil mulheres.`);
}

function compact(value) {
  if (value >= 1_000_000) return `${(value/1_000_000).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} mi`;
  if (value >= 1_000) return `${Math.round(value/1_000)} mil`;
  return Math.round(value);
}

function renderRanking() {
  const top = data.municipios_sc_2024.slice(0, 10);
  const max = top[0].parceiro;
  document.querySelector('#ranking').innerHTML = top.map((d, index) => `<div class="rank-row">
    <span class="position">${String(index + 1).padStart(2, '0')}</span>
    <span>${d.municipio}</span>
    <span class="bar-track" aria-hidden="true"><span class="bar-fill" style="width:${d.parceiro/max*100}%"></span></span>
    <strong>${format.format(d.parceiro)}</strong>
  </div>`).join('');
}

function renderBars(selector, items, labelKey) {
  const max = Math.max(...items.map(d => d.notificacoes));
  document.querySelector(selector).innerHTML = items.map(d => `<div class="bar-item">
    <span>${d[labelKey]}</span>
    <span class="bar-track" aria-hidden="true"><span class="bar-fill" style="width:${d.notificacoes/max*100}%"></span></span>
    <strong>${compact(d.notificacoes)}</strong>
  </div>`).join('');
}

function updateTerritory(next) {
  current = next;
  document.querySelectorAll('[data-territorio]').forEach(button => {
    const active = button.dataset.territorio === next;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
  const series = data.territorios[next];
  renderKPIs(series);
  renderSeries(series);
}

async function init() {
  try {
    const response = await fetch('data/painel.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    data = await response.json();
    updateTerritory(current);
    renderRanking();
    renderBars('#race-chart', data.perfil_sc_2024.raca.slice(0, 6), 'categoria');
    renderBars('#type-chart', data.perfil_sc_2024.tipos_violencia, 'tipo');
    document.querySelector('#updated').textContent = `Camada Gold gerada em ${new Date(`${data.meta.atualizado}T12:00:00`).toLocaleDateString('pt-BR')}`;
    document.querySelectorAll('[data-territorio]').forEach(button => button.addEventListener('click', () => updateTerritory(button.dataset.territorio)));
  } catch (error) {
    document.querySelector('#series-chart').innerHTML = '<p class="quiet">Não foi possível carregar os dados do painel.</p>';
    console.error(error);
  }
}

init();

