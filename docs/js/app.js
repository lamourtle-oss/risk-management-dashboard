const charts = {};
const MAP = {
  กรุงเทพมหานคร: [180, 250],
  ปทุมธานี: [188, 232],
  ชลบุรี: [230, 268],
  ระยอง: [242, 292],
  นครราชสีมา: [230, 210],
  ขอนแก่น: [250, 168],
  อุดรธานี: [248, 132],
  เชียงใหม่: [118, 78],
  สงขลา: [168, 430],
  สุราษฎร์ธานี: [158, 370],
};

const state = {
  data: null,
  tab: "npl",
  quarter: "",
  search: "",
  nplType: "",
  salesBranch: "",
};

function $(id) {
  return document.getElementById(id);
}

function money(value) {
  return Number(value || 0).toLocaleString("th-TH", { maximumFractionDigits: 0 });
}

function matchesSearch(text) {
  if (!state.search) return true;
  return String(text || "").toLowerCase().includes(state.search);
}

function showBanner(message, isError) {
  const el = $("banner");
  if (!message) {
    el.hidden = true;
    return;
  }
  el.hidden = false;
  el.textContent = message;
  el.style.background = isError ? "#fff1f2" : "#fff7ed";
  el.style.borderColor = isError ? "#fecdd3" : "#fed7aa";
  el.style.color = isError ? "#9f1239" : "#9a3412";
}

function drawChart(id, config) {
  if (charts[id]) charts[id].destroy();
  const canvas = $(id);
  if (!canvas || !window.Chart) return;
  charts[id] = new Chart(canvas, config);
}

function currentQuarterItems(list, extra) {
  return (list || []).filter((item) => {
    if (state.quarter && item.quarter && item.quarter !== state.quarter) return false;
    if (extra && !extra(item)) return false;
    return true;
  });
}

function renderFilters() {
  const quarters = state.data.quarters || [];
  const select = $("quarter-filter");
  const current = state.quarter;
  select.innerHTML = `<option value="">ทุกไตรมาส</option>` + quarters.map((q) => `<option value="${q}">${q}</option>`).join("");
  select.value = current && quarters.includes(current) ? current : "";
  state.quarter = select.value;

  const types = [...new Set((state.data.npl.byStage || []).map((item) => item.type).filter(Boolean))];
  $("npl-type").innerHTML =
    `<option value="">ทั้งหมด</option>` + types.map((t) => `<option value="${t}">${t}</option>`).join("");
  $("npl-type").value = state.nplType;

  const branches = [...new Set((state.data.sales.byBranch || []).map((item) => item.branch).filter(Boolean))];
  $("sales-branch").innerHTML =
    `<option value="">ทุกสาขา</option>` + branches.map((b) => `<option value="${b}">${b}</option>`).join("");
  $("sales-branch").value = state.salesBranch;
}

function renderNpl() {
  const overview = currentQuarterItems(state.data.npl.overview, (item) => !state.nplType || item.type === state.nplType);
  const labels = [...new Set(overview.map((item) => item.quarter || item.type))];
  const types = [...new Set(overview.map((item) => item.type))];
  drawChart("npl-overview", {
    type: "bar",
    data: {
      labels: state.quarter ? types : [...new Set(overview.map((item) => item.quarter))],
      datasets: state.quarter
        ? [
            {
              label: "% NPL",
              data: types.map((t) => overview.find((item) => item.type === t)?.ratio || 0),
              backgroundColor: "#1e3a5f",
            },
          ]
        : types.map((t, idx) => ({
            label: t,
            data: [...new Set(overview.map((item) => item.quarter))].map(
              (q) => overview.find((item) => item.quarter === q && item.type === t)?.ratio || 0
            ),
            backgroundColor: ["#1e3a5f", "#9f1239", "#b45309"][idx % 3],
          })),
    },
    options: { plugins: { legend: { position: "bottom" } }, scales: { y: { beginAtZero: true } } },
  });

  const stages = currentQuarterItems(state.data.npl.byStage, (item) => !state.nplType || item.type === state.nplType);
  const stageNames = [...new Set(stages.map((item) => item.stage))];
  drawChart("npl-stage", {
    type: "bar",
    data: {
      labels: stageNames,
      datasets: [
        {
          label: "จำนวนสัญญา",
          data: stageNames.map((s) => stages.filter((item) => item.stage === s).reduce((sum, item) => sum + item.contracts, 0)),
          backgroundColor: "#9f1239",
        },
      ],
    },
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
  });

  const closures = currentQuarterItems(state.data.npl.closures);
  const grouped = {};
  closures.forEach((item) => {
    const key = item.loanType;
    if (!grouped[key]) grouped[key] = { ...item };
    else {
      grouped[key].writeoffContracts += item.writeoffContracts;
      grouped[key].writeoffAmount += item.writeoffAmount;
      grouped[key].repossessContracts += item.repossessContracts;
      grouped[key].repossessAmount += item.repossessAmount;
      grouped[key].normalContracts += item.normalContracts;
      grouped[key].normalAmount += item.normalAmount;
    }
  });
  $("npl-close-body").innerHTML = Object.values(grouped)
    .filter((item) => matchesSearch(item.loanType))
    .map(
      (item) => `<tr>
        <td>${item.loanType}</td>
        <td>${item.writeoffContracts}</td><td>${money(item.writeoffAmount)}</td>
        <td>${item.repossessContracts}</td><td>${money(item.repossessAmount)}</td>
        <td>${item.normalContracts}</td><td>${money(item.normalAmount)}</td>
      </tr>`
    )
    .join("");

  const home = state.data.npl.hpHomeNew || [];
  drawChart("npl-home", {
    type: "line",
    data: {
      labels: home.map((item) => item.month),
      datasets: [{ label: "% NPL", data: home.map((item) => item.ratio), borderColor: "#1e3a5f", tension: 0.2 }],
    },
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
  });
}

function renderSales() {
  const mix = currentQuarterItems(state.data.sales.mix);
  const cats = [...new Set(mix.map((item) => item.category))];
  const quarters = [...new Set(mix.map((item) => item.quarter))];
  drawChart("sales-mix", {
    type: "bar",
    data: {
      labels: quarters.length ? quarters : cats,
      datasets: cats.map((cat, idx) => ({
        label: cat,
        data: (quarters.length ? quarters : [""]).map((q) =>
          mix.filter((item) => item.category === cat && (!q || item.quarter === q)).reduce((sum, item) => sum + item.amount, 0)
        ),
        backgroundColor: ["#1e3a5f", "#9f1239", "#b45309", "#166534", "#7c3aed", "#0f766e"][idx % 6],
      })),
    },
    options: { plugins: { legend: { position: "bottom" } }, scales: { x: { stacked: true }, y: { stacked: true, beginAtZero: true } } },
  });

  const branches = currentQuarterItems(state.data.sales.byBranch, (item) => matchesSearch(`${item.branch} ${item.province}`));
  const branchNames = [...new Set(branches.map((item) => item.branch))];
  drawChart("sales-branch-chart", {
    type: "bar",
    data: {
      labels: branchNames,
      datasets: [
        {
          data: branchNames.map((name) => branches.filter((item) => item.branch === name).reduce((sum, item) => sum + item.amount, 0)),
          backgroundColor: "#1e3a5f",
        },
      ],
    },
    options: { plugins: { legend: { display: false } }, indexAxis: "y", scales: { x: { beginAtZero: true } } },
  });

  const products = currentQuarterItems(
    state.data.sales.byProduct,
    (item) => (!state.salesBranch || item.branch === state.salesBranch) && matchesSearch(`${item.branch} ${item.product}`)
  );
  const productTotals = {};
  products.forEach((item) => {
    productTotals[item.product] = (productTotals[item.product] || 0) + item.amount;
  });
  const ranked = Object.entries(productTotals).sort((a, b) => b[1] - a[1]);
  const best = ranked.slice(0, 5);
  const worst = ranked.slice(-5).reverse();
  drawChart("sales-best", {
    type: "bar",
    data: { labels: best.map((item) => item[0]), datasets: [{ data: best.map((item) => item[1]), backgroundColor: "#166534" }] },
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
  });
  drawChart("sales-worst", {
    type: "bar",
    data: { labels: worst.map((item) => item[0]), datasets: [{ data: worst.map((item) => item[1]), backgroundColor: "#9f1239" }] },
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
  });

  $("sales-table").innerHTML = products
    .map(
      (item) => `<tr>
        <td>${item.branch}</td><td>${item.province}</td><td>${item.product}</td><td>${money(item.amount)}</td>
      </tr>`
    )
    .join("");
}

function renderMap(targetId, points, colorFn, titleFn) {
  const dots = points
    .map((point) => {
      const pos = MAP[point.province];
      if (!pos) return "";
      const color = colorFn(point);
      return `<g class="dot" data-title="${titleFn(point)}" data-body="${point.body}">
        <circle cx="${pos[0]}" cy="${pos[1]}" r="9" fill="${color}" stroke="#fff" stroke-width="2"></circle>
        <text x="${pos[0] + 12}" y="${pos[1] + 4}" font-size="11" fill="#1c1917">${point.province}</text>
      </g>`;
    })
    .join("");
  $(targetId).innerHTML = `<svg viewBox="0 0 340 500">
    <path d="M150 30 C210 40 250 90 240 140 C270 160 290 200 270 250 C300 280 280 320 240 330 C220 380 200 430 180 470 C160 430 150 380 155 330 C110 310 100 250 120 200 C90 150 110 80 150 30 Z" fill="#cfe3d4" stroke="#7fa08a"/>
    ${dots}
  </svg>
  <p class="legend"><span style="color:#9f1239">● สูง / ไม่ตามเป้า</span><span style="color:#166534">● ปกติ</span></p>`;
  $(targetId).querySelectorAll(".dot").forEach((node) => {
    node.addEventListener("click", () => {
      $("popup-title").textContent = node.dataset.title;
      $("popup-body").innerHTML = node.dataset.body;
      $("popup").showModal();
    });
  });
}

function renderInventory() {
  const aging = (state.data.inventory.aging || []).filter((item) =>
    matchesSearch(`${item.product} ${item.branch} ${item.province} ${item.location}`)
  );
  $("aging-table").innerHTML = aging
    .map(
      (item, idx) => `<tr class="clickable" data-idx="${idx}">
        <td>${item.product}</td><td>${item.grade}</td>
        <td>${money(item.cost)}</td><td>${money(item.provision)}</td>
        <td>${item.age0to2}</td><td>${item.age3to4}</td><td>${item.age4plus}</td>
        <td>${item.branch}</td>
      </tr>`
    )
    .join("");
  $("aging-table").querySelectorAll("tr").forEach((row) => {
    row.addEventListener("click", () => {
      const item = aging[Number(row.dataset.idx)];
      $("popup-title").textContent = item.product;
      $("popup-body").innerHTML = `Location: <b>${item.location}</b><br>สาขา ${item.branch} · ${item.province}<br>สภาพ ${item.grade}`;
      $("popup").showModal();
    });
  });

  const mapPoints = aging.map((item) => ({
    province: item.province,
    body: `${item.product}<br>Location: ${item.location}<br>ค้าง 4 ปีขึ้นไป ${item.age4plus} ชิ้น`,
    slow: item.age4plus + item.age3to4,
  }));
  const unique = [];
  mapPoints.forEach((point) => {
    const found = unique.find((item) => item.province === point.province);
    if (found) found.slow += point.slow;
    else unique.push({ ...point });
  });
  renderMap("inv-map", unique, (p) => (p.slow >= 12 ? "#9f1239" : "#166534"), (p) => p.province);

  const minmax = (state.data.inventory.minmax || []).filter((item) => matchesSearch(`${item.branch} ${item.province}`));
  $("minmax-table").innerHTML = minmax
    .map(
      (item) => `<tr>
        <td>${item.branch}</td><td>${item.province}</td>
        <td>${item.minStock}</td><td>${item.maxStock}</td><td>${item.onHand}</td>
      </tr>`
    )
    .join("");
}

function renderOil() {
  const rows = currentQuarterItems(state.data.oil, (item) => matchesSearch(`${item.branch} ${item.province}`));
  const order = ["0-50 ลิตร", "51-100 ลิตร", "101-150 ลิตร", "151-200 ลิตร", "มากกว่า 200 ลิตร"];
  const grouped = order.map((bucket) => {
    const items = rows.filter((item) => item.bucket === bucket);
    return { bucket, count: items.length, liters: items.reduce((sum, item) => sum + item.liters, 0) };
  });
  drawChart("oil-chart", {
    type: "bar",
    data: {
      labels: order,
      datasets: [{ label: "จำนวนสาขา", data: grouped.map((item) => item.count), backgroundColor: "#b45309" }],
    },
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
  });
  $("oil-table").innerHTML = grouped
    .map((item) => `<tr><td>${item.bucket}</td><td>${item.count}</td><td>${money(item.liters)}</td></tr>`)
    .join("");
}

function renderService() {
  const sla = currentQuarterItems(state.data.service.sla);
  const buckets = [...new Set(sla.map((item) => item.bucket))];
  drawChart("sla-chart", {
    type: "bar",
    data: {
      labels: buckets,
      datasets: [
        {
          data: buckets.map((b) => sla.filter((item) => item.bucket === b).reduce((sum, item) => sum + item.jobs, 0)),
          backgroundColor: buckets.map((b) => (b === "0-7 วัน" ? "#166534" : "#9f1239")),
        },
      ],
    },
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
  });

  const csat = state.data.service.csat || [];
  drawChart("csat-chart", {
    type: "line",
    data: {
      labels: csat.map((item) => item.quarter),
      datasets: [{ label: "CSAT", data: csat.map((item) => item.score), borderColor: "#1e3a5f", tension: 0.25 }],
    },
    options: { scales: { y: { min: 0, max: 5 } } },
  });

  const provinces = currentQuarterItems(state.data.service.provinces, (item) => matchesSearch(item.province));
  const unique = [];
  provinces.forEach((item) => {
    const found = unique.find((row) => row.province === item.province);
    if (found) {
      found.slaMet += item.slaMet;
      found.slaMiss += item.slaMiss;
    } else unique.push({ ...item });
  });
  unique.forEach((item) => {
    item.body = `ตาม SLA ${item.slaMet} งาน<br>ไม่ตาม SLA ${item.slaMiss} งาน`;
  });
  renderMap("sla-map", unique, (p) => (p.slaMiss > p.slaMet * 0.2 ? "#9f1239" : "#166534"), (p) => p.province);
}

function render() {
  try {
    const source = state.data.sourceLabel ? ` · ${state.data.sourceLabel}` : "";
    $("generated-at").textContent = `${state.data.generatedAtLabel || "-"}${source}`;
    renderFilters();
    renderNpl();
    renderSales();
    renderInventory();
    renderOil();
    renderService();
  } catch (error) {
    showBanner(error.message || "แสดงผลไม่ครบ", true);
  }
}

function showTab(name) {
  state.tab = name;
  document.querySelectorAll(".tab-page").forEach((page) => {
    page.hidden = page.dataset.page !== name;
  });
  document.querySelectorAll(".tabs button").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === name);
  });
}

async function loadData() {
  const response = await fetch(`data/dashboard.json?t=${Date.now()}`);
  if (!response.ok) throw new Error("ยังไม่มีข้อมูล กรุณารัน python pipeline/run.py");
  state.data = await response.json();
  render();
}

async function refresh() {
  const btn = $("refresh-btn");
  btn.disabled = true;
  btn.textContent = "กำลังอัปเดต...";
  try {
    const local = await fetch("api/refresh", { method: "POST" });
    if (local.ok) {
      await loadData();
      showBanner("ประมวลผลไฟล์บนเครื่องเรียบร้อย");
      return;
    }
  } catch (error) {
    if (!(error instanceof TypeError)) {
      showBanner(error.message, true);
      return;
    }
  } finally {
    btn.disabled = false;
    btn.textContent = "รีเฟรชข้อมูล";
  }
  await loadData();
  showBanner("โหลดข้อมูลล่าสุดจากไฟล์ที่เผยแพร่แล้ว หากต้องการของใหม่จาก SharePoint ให้โหลดไฟล์ลงเครื่อง แล้วประมวลผลก่อน push GitHub");
}

function startDashboard() {
  loadData().catch(function (error) {
    showBanner(error.message, true);
  });
}

document.addEventListener("dashboard-ready", startDashboard);
if ($("app") && !$("app").hidden) {
  startDashboard();
}

$("refresh-btn").addEventListener("click", refresh);
$("quarter-filter").addEventListener("change", function (event) {
  state.quarter = event.target.value;
  render();
});
$("search").addEventListener("input", function (event) {
  state.search = event.target.value.trim().toLowerCase();
  render();
});
$("npl-type").addEventListener("change", function (event) {
  state.nplType = event.target.value;
  renderNpl();
});
$("sales-branch").addEventListener("change", function (event) {
  state.salesBranch = event.target.value;
  renderSales();
});
$("tabs").addEventListener("click", function (event) {
  var btn = event.target.closest("button[data-tab]");
  if (btn) showTab(btn.dataset.tab);
});
