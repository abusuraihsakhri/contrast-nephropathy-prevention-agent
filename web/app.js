const $ = (id) => document.getElementById(id);

const defaults = {
  weight: 70,
  age: 68,
  creatinine: 1.3,
  egfr: 52,
  contrast: 160,
  hypotension: false,
  iabp: false,
  chf: false,
  anemia: false,
  diabetes: true,
};

function readNumber(id) {
  const value = Number($(id).value);
  if (!Number.isFinite(value)) throw new Error("All numeric fields must contain finite values.");
  return value;
}

function setStatus(text, tone = "neutral") {
  const el = $("overallStatus");
  el.textContent = text;
  const colors = {
    neutral: "var(--muted)",
    low: "var(--success)",
    medium: "var(--warning)",
    high: "var(--danger)",
  };
  el.style.color = colors[tone] || colors.neutral;
}

function calculateMehran(data) {
  let score = 0;
  const factors = [];

  const add = (condition, points, label) => {
    if (!condition) return;
    score += points;
    factors.push(`${label} (+${points})`);
  };

  add(data.hypotension, 5, "Hypotension");
  add(data.iabp, 5, "IABP");
  add(data.chf, 5, "CHF");
  add(data.age > 75, 4, "Age >75");
  add(data.anemia, 3, "Anemia");
  add(data.diabetes, 3, "Diabetes");

  const contrastPoints = Math.floor(data.contrast / 100);
  if (contrastPoints > 0) {
    score += contrastPoints;
    factors.push(`Contrast volume (+${contrastPoints})`);
  }

  let renalPoints = 0;
  if (data.egfr < 20) renalPoints = 6;
  else if (data.egfr < 40) renalPoints = 4;
  else if (data.egfr < 60) renalPoints = 2;

  if (renalPoints) {
    score += renalPoints;
    factors.push(`Renal dysfunction (+${renalPoints})`);
  }

  if (score <= 5) return { score, category: "Low", risk: 7.5, dialysis: 0.04, factors, tone: "low" };
  if (score <= 10) return { score, category: "Moderate", risk: 14.0, dialysis: 0.12, factors, tone: "medium" };
  if (score <= 15) return { score, category: "High", risk: 26.1, dialysis: 1.09, factors, tone: "high" };
  return { score, category: "Very high", risk: 57.3, dialysis: 12.6, factors, tone: "high" };
}

function hydrationContext(data) {
  if (data.chf) {
    return "Volume expansion can worsen heart failure or other hypervolemic states. Any prophylaxis should be individualized by the treating team rather than calculated automatically.";
  }
  if (data.egfr < 30) {
    return "For IV iodinated contrast, ACR–NKF guidance generally supports isotonic normal-saline prophylaxis for AKI or eGFR <30 mL/min/1.73 m² when not contraindicated. Typical regimens start about 1 hour before and continue 3–12 hours after; exact rate and volume are individualized.";
  }
  if (data.egfr < 45) {
    return "For stable eGFR 30–44 mL/min/1.73 m², IV saline prophylaxis may be considered in selected high-risk circumstances. Route of contrast, recent AKI, hemodynamics, and local protocol matter.";
  }
  return "For stable eGFR ≥45 mL/min/1.73 m², routine IV saline prophylaxis is generally not indicated for IV iodinated contrast solely on the basis of kidney function. PCI/intra-arterial procedures require procedure-specific assessment.";
}

function evaluate() {
  const data = {
    weight: readNumber("weight"),
    age: readNumber("age"),
    creatinine: readNumber("creatinine"),
    egfr: readNumber("egfr"),
    contrast: readNumber("contrast"),
    hypotension: $("hypotension").checked,
    iabp: $("iabp").checked,
    chf: $("chf").checked,
    anemia: $("anemia").checked,
    diabetes: $("diabetes").checked,
  };

  if (data.weight <= 0) throw new Error("Weight must be greater than 0 kg.");
  if (data.age < 0 || data.age > 150) throw new Error("Age must be between 0 and 150 years.");
  if (data.creatinine <= 0) throw new Error("Creatinine must be greater than 0 mg/dL.");
  if (data.egfr < 0) throw new Error("eGFR cannot be negative.");
  if (data.contrast < 0) throw new Error("Contrast volume cannot be negative.");

  const mehran = calculateMehran(data);
  const adjustedCreatinine = Math.max(0.4, data.creatinine);
  const mcd = (5 * data.weight) / adjustedCreatinine;
  const ratio = data.contrast / Math.max(1, data.egfr);
  const ratioHigh = ratio >= 3.7 || (data.egfr < 30 && ratio >= 3.0);
  const mcdExceeded = data.contrast > mcd;

  $("scoreValue").textContent = String(mehran.score);
  $("scoreRisk").textContent = `${mehran.category} · historical CIN ${mehran.risk.toFixed(1)}%`;
  $("mcdValue").textContent = `${mcd.toFixed(0)} mL`;
  $("ratioValue").textContent = ratio.toFixed(2);
  $("ratioRisk").textContent = ratioHigh ? "Above repository PCI threshold" : "Below repository PCI threshold";

  const factorText = mehran.factors.length ? mehran.factors.join(", ") : "No score factors present";
  $("riskNarrative").textContent =
    `Original Mehran score: ${mehran.score} (${mehran.category}). Historical PCI-cohort CIN estimate ${mehran.risk.toFixed(1)}% and dialysis estimate ${mehran.dialysis.toFixed(2)}%. ${factorText}. ` +
    `Planned contrast is ${mcdExceeded ? "above" : "below"} the empirical maximum contrast dose.`;

  $("hydrationNarrative").textContent = hydrationContext(data);

  if (mehran.score >= 11 || (mcdExceeded && ratioHigh)) setStatus("High attention", "high");
  else if (mehran.score >= 6 || mcdExceeded || ratioHigh) setStatus("Review", "medium");
  else setStatus("Lower risk", "low");

  $("formError").textContent = "";
}

$("calculatorForm").addEventListener("submit", (event) => {
  event.preventDefault();
  try {
    evaluate();
  } catch (error) {
    $("formError").textContent = error instanceof Error ? error.message : "Unable to calculate.";
    setStatus("Input error", "high");
  }
});

$("resetButton").addEventListener("click", () => {
  for (const [key, value] of Object.entries(defaults)) {
    const el = $(key);
    if (!el) continue;
    if (typeof value === "boolean") el.checked = value;
    else el.value = value;
  }
  evaluate();
});

const storedTheme = localStorage.getItem("caki-theme");
if (storedTheme === "dark" || storedTheme === "light") {
  document.documentElement.dataset.theme = storedTheme;
}

$("themeToggle").addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  localStorage.setItem("caki-theme", next);
});

evaluate();
