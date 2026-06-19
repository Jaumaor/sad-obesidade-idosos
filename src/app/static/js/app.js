/**
 * Dashboard SAD - Frontend Application
 * Carrega dados da API e popula o dashboard
 */

const API_BASE = "/api/v1";

// ===== INICIALIZAÇÃO =====

document.addEventListener("DOMContentLoaded", () => {
  console.log("Iniciando Dashboard SAD...");
  loadDashboardData();
});

// ===== FUNÇÕES PRINCIPAIS =====

async function loadDashboardData() {
  try {
    const [kpis, pacientes, risco, grau] = await Promise.all([
      fetchKPIs(),
      fetchPacientes(),
      fetchDistribuicaoRisco(),
      fetchDistribuicaoGrau(),
    ]);

    renderKPIs(kpis, risco);
    renderRiskChart(risco);
    renderPatientTable(pacientes);

    // Mapa carrega em paralelo (pode ser mais lento)
    loadHeatmap();
  } catch (error) {
    console.error("Erro ao carregar dados do dashboard:", error);
    showErrorMessage("Erro ao carregar dados do dashboard");
  }
}

// ===== API REQUESTS =====

async function fetchKPIs() {
  const response = await fetch(`${API_BASE}/kpis`);
  if (!response.ok) throw new Error("Erro ao buscar KPIs");
  return await response.json();
}

async function fetchPacientes(limite = 50) {
  const response = await fetch(`${API_BASE}/pacientes?limite=${limite}`);
  if (!response.ok) throw new Error("Erro ao buscar pacientes");
  return await response.json();
}

async function fetchDistribuicaoRisco() {
  const response = await fetch(`${API_BASE}/distribuicao/risco`);
  if (!response.ok) throw new Error("Erro ao buscar distribuição de risco");
  return await response.json();
}

async function fetchDistribuicaoGrau() {
  const response = await fetch(`${API_BASE}/distribuicao/grau`);
  if (!response.ok) throw new Error("Erro ao buscar distribuição de grau");
  return await response.json();
}

// ===== RENDERIZAÇÃO: KPIs =====

function renderKPIs(kpis, riscoData) {
  const container = document.getElementById("kpi-container");
  container.innerHTML = "";

  const total = kpis.total_pacientes || 0;
  const faltosos = kpis.pacientes_faltosos || 0;
  const territorios = kpis.total_territorios || 0;

  // Calcular alto risco a partir da distribuição
  const parsed = parseRiskData(riscoData);
  const altoRisco = parsed.critico + parsed.alto;

  // Percentual de acompanhamento
  const ativos = kpis.pacientes_ativos || 0;
  const pctAcomp = total > 0 ? Math.round((ativos / total) * 100) : 0;

  // KPI 1: Total de Monitorados
  container.innerHTML += `
    <div class="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
      <p class="text-xs font-bold text-slate-500 uppercase mb-2">Total Monitorados (≥60a, IMC ≥35)</p>
      <div class="flex items-end justify-between">
        <h3 class="text-4xl font-black text-slate-800 dark:text-slate-100">${total}</h3>
        <span class="material-symbols-outlined text-primary/40 text-3xl">monitoring</span>
      </div>
    </div>
  `;

  // KPI 2: Alto Risco + Crítico
  container.innerHTML += `
    <div class="bg-white dark:bg-slate-900 p-6 rounded-xl border-l-4 border-l-red-500 border-y border-r border-slate-200 dark:border-slate-800 shadow-sm">
      <p class="text-xs font-bold text-slate-500 uppercase mb-2">Alto Risco + Crítico (ML)</p>
      <div class="flex items-end justify-between">
        <h3 class="text-4xl font-black text-red-600">${altoRisco}</h3>
        <span class="flex items-center text-xs font-bold text-red-600 bg-red-50 dark:bg-red-900/20 px-2 py-1 rounded">
          ${total > 0 ? Math.round((altoRisco / total) * 100) : 0}% do total
        </span>
      </div>
    </div>
  `;

  // KPI 3: Faltosos (sem visita > 90 dias)
  container.innerHTML += `
    <div class="bg-white dark:bg-slate-900 p-6 rounded-xl border-l-4 border-l-amber-500 border-y border-r border-slate-200 dark:border-slate-800 shadow-sm">
      <p class="text-xs font-bold text-slate-500 uppercase mb-2">Faltosos (>90 dias sem visita)</p>
      <div class="flex items-end justify-between">
        <h3 class="text-4xl font-black text-amber-600">${faltosos}</h3>
        <span class="material-symbols-outlined text-amber-400 text-3xl">schedule</span>
      </div>
    </div>
  `;

  // KPI 4: Territórios Cobertos
  container.innerHTML += `
    <div class="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
      <p class="text-xs font-bold text-slate-500 uppercase mb-2">Bairros/Territórios</p>
      <div class="flex items-end justify-between">
        <h3 class="text-4xl font-black text-slate-800 dark:text-slate-100">${territorios}</h3>
        <span class="material-symbols-outlined text-primary/40 text-3xl">location_city</span>
      </div>
    </div>
  `;
}

// ===== RENDERIZAÇÃO: Risk Chart =====

function renderRiskChart(data) {
  const container = document.getElementById("risk-chart");
  const r = parseRiskData(data);
  const total = r.critico + r.alto + r.moderado + r.baixo;
  if (total === 0) { container.innerHTML = '<p class="text-slate-400">Sem dados</p>'; return; }

  const pct = (v) => Math.round((v / total) * 100);
  const criticoPct = pct(r.critico);
  const altoPct = pct(r.alto);
  const moderadoPct = pct(r.moderado);
  const baixoPct = pct(r.baixo);

  // offsets acumulados para o donut SVG
  const o1 = 0;
  const o2 = criticoPct;
  const o3 = o2 + altoPct;
  const o4 = o3 + moderadoPct;

  container.innerHTML = `
    <div class="relative size-48">
      <svg class="size-full -rotate-90" viewBox="0 0 36 36">
        <circle class="stroke-red-700" cx="18" cy="18" fill="none" r="16"
          stroke-dasharray="${criticoPct} 100" stroke-dashoffset="-${o1}" stroke-width="4"></circle>
        <circle class="stroke-red-400" cx="18" cy="18" fill="none" r="16"
          stroke-dasharray="${altoPct} 100" stroke-dashoffset="-${o2}" stroke-width="4"></circle>
        <circle class="stroke-amber-500" cx="18" cy="18" fill="none" r="16"
          stroke-dasharray="${moderadoPct} 100" stroke-dashoffset="-${o3}" stroke-width="4"></circle>
        <circle class="stroke-emerald-500" cx="18" cy="18" fill="none" r="16"
          stroke-dasharray="${baixoPct} 100" stroke-dashoffset="-${o4}" stroke-width="4"></circle>
      </svg>
      <div class="absolute inset-0 flex flex-col items-center justify-center">
        <span class="text-xs text-slate-500 font-bold uppercase">Total</span>
        <span class="text-2xl font-black">${total}</span>
      </div>
    </div>
    <div class="w-full space-y-2">
      <div class="flex items-center justify-between text-sm">
        <span class="flex items-center gap-2"><span class="size-2 rounded-full bg-red-700"></span> Crítico</span>
        <span class="font-bold">${r.critico} (${criticoPct}%)</span>
      </div>
      <div class="flex items-center justify-between text-sm">
        <span class="flex items-center gap-2"><span class="size-2 rounded-full bg-red-400"></span> Alto</span>
        <span class="font-bold">${r.alto} (${altoPct}%)</span>
      </div>
      <div class="flex items-center justify-between text-sm">
        <span class="flex items-center gap-2"><span class="size-2 rounded-full bg-amber-500"></span> Moderado</span>
        <span class="font-bold">${r.moderado} (${moderadoPct}%)</span>
      </div>
      <div class="flex items-center justify-between text-sm">
        <span class="flex items-center gap-2"><span class="size-2 rounded-full bg-emerald-500"></span> Baixo</span>
        <span class="font-bold">${r.baixo} (${baixoPct}%)</span>
      </div>
    </div>
  `;
}

function parseRiskData(data) {
  const result = { critico: 0, alto: 0, moderado: 0, baixo: 0 };
  if (!Array.isArray(data)) return result;

  data.forEach((item) => {
    const nivel = (item.Risco || item.nivel_risco || item.risco || "").toLowerCase();
    const qtd = parseInt(item.Quantidade || item.quantidade || item.count || 0);
    if (nivel.includes("crit"))       result.critico += qtd;
    else if (nivel.includes("alto"))  result.alto += qtd;
    else if (nivel.includes("mod"))   result.moderado += qtd;
    else if (nivel.includes("baix"))  result.baixo += qtd;
  });
  return result;
}

// ===== RENDERIZAÇÃO: Patient Table =====

function renderPatientTable(pacientes) {
  const tbody = document.getElementById("patient-tbody");
  tbody.innerHTML = "";

  if (!Array.isArray(pacientes) || pacientes.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="px-6 py-8 text-center text-slate-500">
          Nenhum paciente encontrado
        </td>
      </tr>`;
    return;
  }

  const getRiscoPeso = (p) => {
    const r = (p.Risco || "").toLowerCase();
    if (r.includes("crit")) return 10;
    if (r.includes("alto")) return 8;
    if (r.includes("mod")) return 6;
    return 3;
  };

  const sorted = pacientes.slice(0, 15).sort((a, b) => getRiscoPeso(b) - getRiscoPeso(a));

  sorted.forEach((p) => {
    const codigo = p.Codigo || "---";
    const codigoShort = codigo.substring(0, 8) + "…";
    const idade = p.Idade ?? "—";
    const sexo = (p.Sexo || "").substring(0, 1);
    const imc = Number(p.IMC);
    const imcStr = Number.isFinite(imc) ? imc.toFixed(1) : "—";
    const grau = p.Grau || "—";
    const risco = p.Risco || "—";
    const dias = p["Dias Sem Visita"];
    const diasStr = dias != null ? `${dias}d` : "—";
    const territorio = p.Territorio || "—";
    const comorbidades = p.Comorbidades ?? 0;

    // Estilo do risco
    let badge = "bg-emerald-100 text-emerald-700";
    const rl = risco.toLowerCase();
    if (rl.includes("crit")) badge = "bg-red-100 text-red-700";
    else if (rl.includes("alto")) badge = "bg-red-50 text-red-600";
    else if (rl.includes("mod")) badge = "bg-amber-100 text-amber-700";

    // Estilo do grau
    let grauBadge = "bg-blue-50 text-blue-600";
    if (grau.includes("III")) grauBadge = "bg-orange-100 text-orange-700";
    else if (grau.includes("Super")) grauBadge = "bg-purple-100 text-purple-700";

    tbody.innerHTML += `
      <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
        <td class="px-6 py-4">
          <p class="font-bold text-sm font-mono">${codigoShort}</p>
          <p class="text-[10px] text-slate-500">${territorio}</p>
        </td>
        <td class="px-6 py-4 text-sm text-center">${idade} <span class="text-slate-400 text-xs">${sexo}</span></td>
        <td class="px-6 py-4 text-center">
          <span class="font-bold text-sm">${imcStr}</span>
          <span class="block text-[9px] px-1 py-0.5 rounded ${grauBadge} font-bold mt-0.5">${grau}</span>
        </td>
        <td class="px-6 py-4 text-center">
          <span class="px-2 py-1 rounded-full ${badge} text-[10px] font-bold">${risco.toUpperCase()}</span>
        </td>
        <td class="px-6 py-4 text-sm text-center font-mono ${dias > 365 ? 'text-red-500 font-bold' : 'text-slate-600'}">${diasStr}</td>
        <td class="px-6 py-4 text-sm text-center">${comorbidades}</td>
        <td class="px-6 py-4 text-right">
          <button class="bg-primary text-white text-[10px] font-bold px-3 py-1.5 rounded-lg hover:bg-primary/90 transition-colors">
            Detalhes
          </button>
        </td>
      </tr>`;
  });
}

// ===== MAPA DE CALOR (Leaflet + PostGIS) =====

let heatmapInstance = null;

async function loadHeatmap() {
  const container = document.getElementById("heatmap");
  if (!container) return;

  // Centro de Vitória da Conquista
  const VDC_LAT = -14.866;
  const VDC_LNG = -40.844;

  // Inicializar mapa Leaflet
  const map = L.map("heatmap", { zoomControl: true }).setView([VDC_LAT, VDC_LNG], 13);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>',
    maxZoom: 18,
  }).addTo(map);

  // Placeholder enquanto carrega
  const info = L.control({ position: "bottomleft" });
  info.onAdd = () => {
    const div = L.DomUtil.create("div", "bg-white px-3 py-2 rounded shadow text-xs font-bold text-slate-600");
    div.innerHTML = "Carregando pontos...";
    return div;
  };
  info.addTo(map);

  try {
    const response = await fetch(`${API_BASE}/mapa/calor`);
    if (!response.ok) throw new Error("Erro ao buscar dados do mapa");
    const pontos = await response.json();

    if (pontos.length === 0) {
      info.getContainer().innerHTML = "Nenhum ponto geo disponivel";
      return;
    }

    // Converter para formato leaflet-heat: [lat, lng, intensidade]
    // Normalizar intensidade para 0-1
    const maxInt = Math.max(...pontos.map((p) => p.intensidade), 1);
    const heatData = pontos.map((p) => [
      p.lat,
      p.lon,
      p.intensidade / maxInt,
    ]);

    // Adicionar heatmap layer
    heatmapInstance = L.heatLayer(heatData, {
      radius: 25,
      blur: 20,
      maxZoom: 16,
      max: 1.0,
      gradient: {
        0.0: "#22c55e",
        0.3: "#eab308",
        0.6: "#f97316",
        0.8: "#ef4444",
        1.0: "#7f1d1d",
      },
    }).addTo(map);

    // Ajustar zoom para conter todos os pontos
    if (heatData.length > 1) {
      const bounds = L.latLngBounds(heatData.map((d) => [d[0], d[1]]));
      map.fitBounds(bounds, { padding: [30, 30] });
    }

    // Atualizar info
    info.getContainer().innerHTML = `${pontos.length} pacientes geolocalizados`;

    // Adicionar marcadores de cluster por bairro
    const bairros = {};
    pontos.forEach((p) => {
      const b = p.bairro || "Sem bairro";
      if (!bairros[b]) bairros[b] = { lat: 0, lon: 0, n: 0, critico: 0 };
      bairros[b].lat += p.lat;
      bairros[b].lon += p.lon;
      bairros[b].n += 1;
      if (p.nivel_risco === "Critico") bairros[b].critico += 1;
    });

    Object.entries(bairros).forEach(([nome, data]) => {
      const lat = data.lat / data.n;
      const lon = data.lon / data.n;
      const pctCritico = Math.round((data.critico / data.n) * 100);
      const color = pctCritico > 60 ? "#dc2626" : pctCritico > 30 ? "#f59e0b" : "#22c55e";

      L.circleMarker([lat, lon], {
        radius: Math.min(6 + data.n * 0.5, 18),
        fillColor: color,
        color: "#fff",
        weight: 2,
        fillOpacity: 0.85,
      })
        .bindPopup(
          `<div style="font-family:Inter,sans-serif;min-width:140px">
            <strong>${nome}</strong><br>
            <span style="font-size:12px">
              Pacientes: <b>${data.n}</b><br>
              Criticos: <b>${data.critico}</b> (${pctCritico}%)
            </span>
          </div>`
        )
        .addTo(map);
    });
  } catch (err) {
    console.error("Erro no heatmap:", err);
    info.getContainer().innerHTML = "Erro ao carregar mapa";
  }
}

// ===== UTILIDADES =====

function showErrorMessage(message) {
  console.error(message);
}

// ===== EXPORTAÇÕES =====

window.dashboardApp = {
  loadDashboardData,
  fetchKPIs,
  fetchPacientes,
  fetchDistribuicaoRisco,
  fetchDistribuicaoGrau,
  loadHeatmap,
};
