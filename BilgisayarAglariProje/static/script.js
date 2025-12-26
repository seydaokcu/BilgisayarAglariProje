document.addEventListener("DOMContentLoaded", () => {
  // ----------------------------------------
  // SABİTLER (DOM Elementleri)
  // ----------------------------------------
  const qosForm = document.getElementById("qos-form");
  const calcBtn = document.getElementById("calcBtn");
  const algorithmCards = document.querySelectorAll(".algorithm-card");
  const selectedAlgInput = document.getElementById("selected-algorithm-input");
  const outputAlgDisplay = document.getElementById("output-alg");

  // Sonuç Ekranları
  const totalCostDisplay = document.getElementById("total-cost-display");
  const pathDisplay = document.getElementById("path-display");
  const relVal = document.getElementById("rel-val");
  const delayVal = document.getElementById("delay-val");
  const usageVal = document.getElementById("usage-val");
  const resultDisplay = document.getElementById("result-display");
  const graphPlaceholder = document.getElementById("graph-placeholder");
  const metricsBreakdown = document.getElementById("metrics-breakdown");

  // TOOLTIP (Hover Bilgisi İçin)
  const tooltip = document.createElement("div");
  tooltip.className =
    "fixed bg-black text-white text-xs p-2 rounded z-50 hidden pointer-events-none shadow-lg opacity-90";
  document.body.appendChild(tooltip);

  // CYTOSCAPE INSTANCE
  let cy = null;

  function initCy(elements) {
    if (cy) cy.destroy(); // Varsa eskiyi temizle

    graphPlaceholder.classList.add("hidden");

    cy = cytoscape({
      container: document.getElementById("cy-container"),
      elements: elements,
      style: [
        {
          selector: "node",
          style: {
            "background-color": "#9ca3af",
            label: "data(label)",
            color: "#1f2937",
            "font-size": "10px",
            width: 20,
            height: 20,
          },
        },
        {
          selector: "edge",
          style: {
            width: 2,
            "line-color": "#e5e7eb",
            "target-arrow-color": "#e5e7eb",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
          },
        },
        // HIGHLIGHT STYLES
        {
          selector: ".path-node",
          style: {
            "background-color": "#2563eb", // Primary Blue
            width: 25,
            height: 25,
            "font-weight": "bold",
          },
        },
        {
          selector: ".source-node",
          style: {
            "background-color": "#16a34a", // Green
            width: 30,
            height: 30,
          },
        },
        {
          selector: ".target-node",
          style: {
            "background-color": "#dc2626", // Red
            width: 30,
            height: 30,
          },
        },
        {
          selector: ".path-edge",
          style: {
            width: 4,
            "line-color": "#f59e0b", // Amber/Yellow
            "target-arrow-color": "#f59e0b",
            "z-index": 10,
          },
        },
      ],
      layout: {
        name: "cose", // Physics-based layout
        animate: false,
        padding: 10,
      },
    });

    // HOVER EVENTS
    cy.on("mouseover", "edge", function (evt) {
      const edge = evt.target;
      const d = edge.data();
      tooltip.innerHTML = `
                <div class="font-bold border-b mb-1 pb-1">Link Özellikleri</div>
                <div>Bandwidth: ${d.bandwidth} Mbps</div>
                <div>Delay: ${d.delay} ms</div>
                <div>Reliability: ${d.reliability}</div>
            `;
      tooltip.classList.remove("hidden");
    });

    cy.on("mouseover", "node", function (evt) {
      const node = evt.target;
      const d = node.data();
      tooltip.innerHTML = `
                <div class="font-bold border-b mb-1 pb-1">Düğüm ${d.id}</div>
                <div>Processing Delay: ${d.delay} ms</div>
                <div>Reliability: ${d.reliability}</div>
            `;
      tooltip.classList.remove("hidden");
    });

    cy.on("mousemove", function (evt) {
      tooltip.style.left = evt.originalEvent.clientX + 15 + "px";
      tooltip.style.top = evt.originalEvent.clientY + 15 + "px";
    });

    cy.on("mouseout", "edge, node", function (evt) {
      tooltip.classList.add("hidden");
    });
  }

  // INITIAL LOAD
  fetch("/get_initial_graph")
    .then((res) => res.json())
    .then((data) => initCy(data))
    .catch((err) => console.error("Graf yüklenemedi:", err));

  // ----------------------------------------
  // 1. Algoritma Kartı Seçimi
  // ----------------------------------------
  algorithmCards.forEach((card) => {
    card.addEventListener("click", () => {
      algorithmCards.forEach((c) => c.classList.remove("active"));
      card.classList.add("active");
      const selectedAlg = card.getAttribute("data-alg");
      selectedAlgInput.value = selectedAlg;
      outputAlgDisplay.textContent = selectedAlg;
    });
  });

  // ----------------------------------------
  // 2. Form Gönderimi
  // ----------------------------------------
  calcBtn.addEventListener("click", async () => {
    calcBtn.disabled = true;
    calcBtn.innerHTML =
      '<span class="material-symbols-outlined animate-spin">progress_activity</span> Hesaplama Yapılıyor...';

    const data = {
      algorithm: selectedAlgInput.value,
      source: document.getElementById("source").value,
      target: document.getElementById("target").value,
      min_bandwidth: parseFloat(document.getElementById("min_bandwidth").value),
      w_rel: document.getElementById("w_rel").value,
      w_delay: document.getElementById("w_delay").value,
      w_res: document.getElementById("w_res").value,
    };

    try {
      const response = await fetch("/calculate_route", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      const result = await response.json();

      if (response.ok) {
        totalCostDisplay.textContent = result.total_cost;
        relVal.textContent = `${result.reliability}%`;
        delayVal.textContent = `${result.delay}ms`;
        usageVal.textContent = `${Math.min(
          100,
          Math.max(0, parseFloat(result.usage))
        ).toFixed(2)}%`;

        pathDisplay.innerHTML = result.path
          .map((node, index) => {
            return index === result.path.length - 1
              ? `<span>${node}</span>`
              : `<span>${node}</span> <span class="material-symbols-outlined text-sm">arrow_forward</span>`;
          })
          .join("");

        // RENDER GRAPH
        if (result.graph_data) {
          initCy(result.graph_data);
        } else {
          console.error("Graf verisi dönmedi!");
        }

        resultDisplay.textContent = result.debug;
      } else {
        const errorMessage = result.error || "Hata oluştu.";
        totalCostDisplay.textContent = "--.--";
        pathDisplay.textContent = errorMessage;
        resultDisplay.textContent = `HATA: ${errorMessage}`;
        // Grafiği gizlemiyoruz, eski graf kalsın veya boşaltalım?
        // cy.destroy() yapabiliriz ama hata durumunda eskiyi görmek iyidir.
      }
    } catch (error) {
      resultDisplay.textContent = `BAĞLANTI HATASI: ${error.message}`;
    } finally {
      calcBtn.disabled = false;
      calcBtn.innerHTML =
        '<span class="material-symbols-outlined">play_circle</span> Optimal Rotayı Hesapla';
    }
  });

  // ----------------------------------------
  // 3. Metrik Ağırlık Bütçe Kilidi (Sum <= 1.0)
  // ----------------------------------------
  function handleWeightInput(id, numId, value) {
    const weights = [
      { id: "w_rel", numId: "w_rel_number" },
      { id: "w_delay", numId: "w_delay_number" },
      { id: "w_res", numId: "w_res_number" },
    ];

    const changedIdx = weights.findIndex((w) => w.id === id || w.numId === id);
    const otherIndices = [0, 1, 2].filter((i) => i !== changedIdx);

    // Diğerlerinin toplamını bul
    const otherSum = otherIndices.reduce((sum, idx) => {
      return (
        sum +
        (parseFloat(document.getElementById(weights[idx].numId).value) || 0)
      );
    }, 0);

    // Bu ağırlığın alabileceği maksimum değer = 1.0 - diğerlerinin toplamı
    let maxAllowed = Math.max(0, 1.0 - otherSum);
    let requestedVal = parseFloat(value) || 0;

    // Değeri kısıtla (0 ile maxAllowed arasında)
    let finalVal = Math.min(requestedVal, maxAllowed);
    finalVal = Math.max(0, finalVal);

    // UI Güncelle (Hem slider hem sayı kutusu)
    // Yuvarlama yapıyoruz (0.01 hassasiyet)
    const displayVal = finalVal.toFixed(2);
    document.getElementById(weights[changedIdx].id).value = displayVal;
    document.getElementById(weights[changedIdx].numId).value = displayVal;
  }

  function setupWeightSync(id, numId) {
    const range = document.getElementById(id);
    const number = document.getElementById(numId);

    range.addEventListener("input", () =>
      handleWeightInput(id, numId, range.value)
    );
    number.addEventListener("input", () =>
      handleWeightInput(numId, numId, number.value)
    );
  }

  setupWeightSync("w_rel", "w_rel_number");
  setupWeightSync("w_delay", "w_delay_number");
  setupWeightSync("w_res", "w_res_number");
});
