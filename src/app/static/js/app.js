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
    // Carrega dados em paralelo
    const [kpis, pacientes, risco] = await Promise.all([
      fetchKPIs(),
      fetchPacientes(),
      fetchDistribuicaoRisco(),
    ]);

    // Renderiza componentes
    renderKPIs(kpis);
    renderRiskChart(risco);
    renderPatientTable(pacientes);
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

function renderKPIs(kpis) {
  const container = document.getElementById("kpi-container");
  container.innerHTML = "";

  // KPI 1: Total de Monitorados
  const totalMonitorados = kpis.total_pacientes || 245;
  container.innerHTML += `
    <div class="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
      <p class="text-xs font-bold text-slate-500 uppercase mb-2">Total de Monitorados (≥60 anos, IMC ≥35)</p>
      <div class="flex items-end justify-between">
        <h3 class="text-4xl font-black text-slate-800 dark:text-slate-100">${totalMonitorados}</h3>
        <span class="flex items-center text-xs font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 px-2 py-1 rounded">
          <span class="material-symbols-outlined text-sm">trending_up</span> 5%
        </span>
      </div>
    </div>
  `;

  // KPI 2: Pacientes em Alto Risco
  const pacientesAltoRisco = kpis.pacientes_alto_risco || 38;
  container.innerHTML += `
    <div class="bg-white dark:bg-slate-900 p-6 rounded-xl border-l-4 border-l-red-500 border-y border-r border-slate-200 dark:border-slate-800 shadow-sm">
      <p class="text-xs font-bold text-slate-500 uppercase mb-2">Pacientes em Alto Risco (Predição ML)</p>
      <div class="flex items-end justify-between">
        <h3 class="text-4xl font-black text-red-600">${pacientesAltoRisco}</h3>
        <span class="flex items-center text-xs font-bold text-red-600 bg-red-50 dark:bg-red-900/20 px-2 py-1 rounded">
          CRÍTICO
        </span>
      </div>
    </div>
  `;

  // KPI 3: Visitas Prioritárias
  const visitasPrioritarias = kpis.visitas_7_dias || 15;
  container.innerHTML += `
    <div class="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
      <p class="text-xs font-bold text-slate-500 uppercase mb-2">Visitas Prioritárias (7 dias)</p>
      <div class="flex items-end justify-between">
        <h3 class="text-4xl font-black text-slate-800 dark:text-slate-100">${visitasPrioritarias}</h3>
        <span class="material-symbols-outlined text-primary/40 text-3xl">home_health</span>
      </div>
    </div>
  `;

  // KPI 4: Acompanhamento Regular
  const acompanhamentoRegular = kpis.acompanhamento_regular || 72;
  container.innerHTML += `
    <div class="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
      <p class="text-xs font-bold text-slate-500 uppercase mb-2">Acompanhamento Regular</p>
      <div class="flex items-end justify-between">
        <h3 class="text-4xl font-black text-slate-800 dark:text-slate-100">${acompanhamentoRegular}%</h3>
        <div class="w-16 h-2 bg-slate-100 dark:bg-slate-800 rounded-full mb-2 overflow-hidden">
          <div class="bg-primary h-full" style="width: ${acompanhamentoRegular}%"></div>
        </div>
      </div>
    </div>
  `;
}

// ===== RENDERIZAÇÃO: Risk Chart =====

function renderRiskChart(data) {
  const container = document.getElementById("risk-chart");

  // Parse data - esperamos uma lista de registros com 'nivel_risco' e 'quantidade'
  const riskData = parseRiskData(data);
  const total = Object.values(riskData).reduce((a, b) => a + b, 0);

  // Calcula percentuais
  const altoPct = Math.round((riskData.alto / total) * 100);
  const medioPct = Math.round((riskData.medio / total) * 100);
  const baixoPct = Math.round((riskData.baixo / total) * 100);

  // Canvas para o donut chart (usando SVG)
  const svg = `
    <div class="relative size-48">
      <svg class="size-full -rotate-90" viewbox="0 0 36 36">
        <circle class="stroke-emerald-500" cx="18" cy="18" fill="none" r="16"
          stroke-dasharray="${baixoPct} 100" stroke-width="4"></circle>
        <circle class="stroke-amber-500" cx="18" cy="18" fill="none" r="16"
          stroke-dasharray="${medioPct} 100" stroke-dashoffset="-${baixoPct}" stroke-width="4"></circle>
        <circle class="stroke-red-500" cx="18" cy="18" fill="none" r="16"
          stroke-dasharray="${altoPct} 100" stroke-dashoffset="-${baixoPct + medioPct}" stroke-width="4"></circle>
      </svg>
      <div class="absolute inset-0 flex flex-col items-center justify-center">
        <span class="text-xs text-slate-500 font-bold uppercase">Total</span>
        <span class="text-2xl font-black">${total}</span>
      </div>
    </div>
    <div class="w-full space-y-3">
      <div class="flex items-center justify-between text-sm">
        <span class="flex items-center gap-2"><span class="size-2 rounded-full bg-red-500"></span> Alto Risco</span>
        <span class="font-bold">${riskData.alto} (${altoPct}%)</span>
      </div>
      <div class="flex items-center justify-between text-sm">
        <span class="flex items-center gap-2"><span class="size-2 rounded-full bg-amber-500"></span> Médio Risco</span>
        <span class="font-bold">${riskData.medio} (${medioPct}%)</span>
      </div>
      <div class="flex items-center justify-between text-sm">
        <span class="flex items-center gap-2"><span class="size-2 rounded-full bg-emerald-500"></span> Baixo Risco</span>
        <span class="font-bold">${riskData.baixo} (${baixoPct}%)</span>
      </div>
    </div>
  `;

  container.innerHTML = svg;
}

function parseRiskData(data) {
  // Parseia os dados de risco da API
  const result = { alto: 0, medio: 0, baixo: 0 };

  if (Array.isArray(data)) {
    data.forEach((item) => {
      const nivel =
        item.nivel_risco?.toLowerCase() ||
        item.risco?.toLowerCase() ||
        item.Risco?.toLowerCase() ||
        "";
      const quantidade = parseInt(item.quantidade || item.Quantidade || item.count || 0);

      if (nivel.includes("alto") || nivel.includes("critico")) {
        result.alto += quantidade;
      } else if (nivel.includes("medio")) {
        result.medio += quantidade;
      } else if (nivel.includes("baixo")) {
        result.baixo += quantidade;
      }
    });
  }

  // Fallback se não houver dados
  if (result.alto === 0 && result.medio === 0 && result.baixo === 0) {
    result.alto = 38;
    result.medio = 122;
    result.baixo = 85;
  }

  return result;
}

// ===== RENDERIZAÇÃO: Patient Table =====

function renderPatientTable(pacientes) {
  const tbody = document.getElementById("patient-tbody");
  tbody.innerHTML = "";

  const getRiscoPeso = (paciente) => {
    const risco =
      paciente.escore_risco ??
      paciente.risco ??
      paciente.nivel_risco_atual ??
      paciente.Risco ??
      0;

    const riscoNumero = Number(risco);
    if (Number.isFinite(riscoNumero)) return riscoNumero;

    const riscoTexto = String(risco).toLowerCase();
    if (riscoTexto.includes("crit")) return 10;
    if (riscoTexto.includes("alto")) return 8;
    if (riscoTexto.includes("medio") || riscoTexto.includes("médio")) return 6;
    return 3;
  };

  if (!Array.isArray(pacientes) || pacientes.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="px-6 py-8 text-center text-slate-500">
          Nenhum paciente encontrado
        </td>
      </tr>
    `;
    return;
  }

  // Limita a 10 pacientes e ordena por risco
  const sortedPacientes = pacientes
    .slice(0, 10)
    .sort((a, b) => getRiscoPeso(b) - getRiscoPeso(a));

  sortedPacientes.forEach((paciente) => {
    const nome =
      paciente.nome_paciente ||
      paciente.nome ||
      paciente.Codigo ||
      paciente.codigo_anonimo ||
      "N/A";
    const idade = paciente.idade ?? paciente.Idade ?? "N/A";

    const imcValue = paciente.imc ?? paciente.imc_atual ?? paciente.IMC;
    const imcNumber = Number(imcValue);
    const imc = Number.isFinite(imcNumber) ? imcNumber.toFixed(1) : "N/A";

    const riscoRaw =
      paciente.escore_risco ??
      paciente.risco ??
      paciente.nivel_risco_atual ??
      paciente.Risco ??
      0;

    const ultimaVisita =
      paciente.ultima_visita ||
      (paciente["Dias Sem Visita"] != null ? `${paciente["Dias Sem Visita"]} dias` : "N/A");
    const acs = paciente.acs_responsavel || paciente.territorio || paciente.Territorio || "N/A";
    const unidade = paciente.ubs || paciente.territorio || paciente.Territorio || "N/A";

    // Estilo por nível de risco
    let riscoBgColor = "bg-emerald-100 text-emerald-600";
    let riscoLabel = "BAIXO";
    let riscoExibicao = "";

    const riscoNumero = Number(riscoRaw);
    if (Number.isFinite(riscoNumero)) {
      riscoExibicao = ` (${riscoNumero.toFixed(1)})`;
      if (riscoNumero >= 9) {
        riscoBgColor = "bg-red-100 text-red-600";
        riscoLabel = "CRÍTICO";
      } else if (riscoNumero >= 8) {
        riscoBgColor = "bg-red-100 text-red-600";
        riscoLabel = "ALTO";
      } else if (riscoNumero >= 6) {
        riscoBgColor = "bg-amber-100 text-amber-600";
        riscoLabel = "MÉDIO";
      }
    } else {
      const riscoTexto = String(riscoRaw).toLowerCase();
      if (riscoTexto.includes("crit")) {
        riscoBgColor = "bg-red-100 text-red-600";
        riscoLabel = "CRÍTICO";
      } else if (riscoTexto.includes("alto")) {
        riscoBgColor = "bg-red-100 text-red-600";
        riscoLabel = "ALTO";
      } else if (riscoTexto.includes("medio") || riscoTexto.includes("médio")) {
        riscoBgColor = "bg-amber-100 text-amber-600";
        riscoLabel = "MÉDIO";
      }
    }

    const row = `
      <tr>
        <td class="px-6 py-4">
          <p class="font-bold text-sm">${nome}</p>
          <p class="text-[10px] text-slate-500">UBS ${unidade}</p>
        </td>
        <td class="px-6 py-4 text-sm text-center">${idade}</td>
        <td class="px-6 py-4 text-sm font-bold text-center">${imc}</td>
        <td class="px-6 py-4 text-center">
          <span class="px-2 py-1 rounded-full ${riscoBgColor} text-[10px] font-bold">
            ${riscoLabel}${riscoExibicao}
          </span>
        </td>
        <td class="px-6 py-4 text-sm">${ultimaVisita}</td>
        <td class="px-6 py-4 text-sm">${acs}</td>
        <td class="px-6 py-4 text-right">
          <button class="bg-primary text-white text-[10px] font-bold px-3 py-1.5 rounded-lg hover:bg-primary/90 transition-colors">
            Agendar Visita
          </button>
        </td>
      </tr>
    `;

    tbody.innerHTML += row;
  });
}

// ===== UTILIDADES =====

function showErrorMessage(message) {
  console.error(message);
  // Pode implementar um toast ou modal aqui
  alert(message);
}

// ===== EXPORTAÇÕES =====

window.dashboardApp = {
  loadDashboardData,
  fetchKPIs,
  fetchPacientes,
  fetchDistribuicaoRisco,
  fetchDistribuicaoGrau,
};
