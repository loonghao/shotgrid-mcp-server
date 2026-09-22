import { App } from "@modelcontextprotocol/ext-apps";
import "./styles.css";

/** Entity types offered by the dashboard switcher. */
const ENTITY_TYPES = ["Task", "Asset", "Shot", "Version", "PublishedFile"] as const;

/** Name of the server tool that produces the dashboard payload. */
const DASHBOARD_TOOL = "shotgrid_dashboard";

interface StatusBucket {
  status: string;
  label: string;
  count: number;
  share: number;
}

interface DashboardEntity {
  id: number;
  label: string;
  status: string;
  status_label: string;
  detail: string;
}

interface DashboardPayload {
  entity_type: string;
  project: { id: number; name: string } | null;
  total: number;
  truncated: boolean;
  breakdown: StatusBucket[];
  entities: DashboardEntity[];
  generated_at: string;
}

const el = {
  subtitle: requireElement<HTMLParagraphElement>("subtitle"),
  entityType: requireElement<HTMLSelectElement>("entity-type"),
  refresh: requireElement<HTMLButtonElement>("refresh"),
  summary: requireElement<HTMLDivElement>("summary"),
  bar: requireElement<HTMLDivElement>("bar"),
  legend: requireElement<HTMLUListElement>("legend"),
  rows: requireElement<HTMLTableSectionElement>("rows"),
  entityCount: requireElement<HTMLSpanElement>("entity-count"),
  footer: requireElement<HTMLElement>("footer"),
};

function requireElement<T extends HTMLElement>(id: string): T {
  const node = document.getElementById(id);
  if (!node) {
    throw new Error(`Missing required element #${id}`);
  }
  return node as T;
}

/** Map a ShotGrid status code onto a colour, falling back to a neutral grey. */
function statusColor(status: string): string {
  const custom = getComputedStyle(document.documentElement).getPropertyValue(`--status-${status}`).trim();
  if (custom) {
    return custom;
  }
  const fallback = getComputedStyle(document.documentElement).getPropertyValue("--status-default").trim();
  return fallback || "#7d8899";
}

function renderSummary(payload: DashboardPayload): void {
  const cards: string[] = [
    `<div class="card" style="border-left-color: ${statusColor("default")}">
       <div class="card__label">Total ${escapeHtml(payload.entity_type)}</div>
       <div class="card__value">${payload.total}</div>
       <div class="card__meta">${payload.project ? escapeHtml(payload.project.name) : "All projects"}</div>
     </div>`,
  ];

  for (const bucket of payload.breakdown) {
    cards.push(
      `<div class="card" style="border-left-color: ${statusColor(bucket.status)}">
         <div class="card__label">${escapeHtml(bucket.label)}</div>
         <div class="card__value">${bucket.count}</div>
         <div class="card__meta">${bucket.share.toFixed(1)}%</div>
       </div>`,
    );
  }

  if (payload.breakdown.length === 0) {
    cards.push(`<div class="card"><div class="card__label">Status</div><div class="card__value">—</div></div>`);
  }

  el.summary.innerHTML = cards.join("");
}

function renderDistribution(payload: DashboardPayload): void {
  if (payload.total === 0 || payload.breakdown.length === 0) {
    el.bar.innerHTML = "";
    el.legend.innerHTML = "";
    return;
  }

  el.bar.innerHTML = payload.breakdown
    .map(
      (bucket) =>
        `<div class="bar__segment" style="width: ${Math.max(bucket.share, 1).toFixed(
          2,
        )}%; background: ${statusColor(bucket.status)}" title="${escapeHtml(bucket.label)}: ${bucket.count}"></div>`,
    )
    .join("");

  el.legend.innerHTML = payload.breakdown
    .map(
      (bucket) =>
        `<li class="legend__item"><span class="legend__swatch" style="background: ${statusColor(
          bucket.status,
        )}"></span>${escapeHtml(bucket.label)} · ${bucket.count}</li>`,
    )
    .join("");
}

function renderEntities(payload: DashboardPayload): void {
  el.entityCount.textContent = `${payload.entities.length} of ${payload.total}`;

  if (payload.entities.length === 0) {
    el.rows.innerHTML = `<tr><td colspan="3"><div class="empty">No entities found.</div></td></tr>`;
    return;
  }

  el.rows.innerHTML = payload.entities
    .map(
      (entity) => `<tr>
        <td>${escapeHtml(entity.label)}</td>
        <td><span class="chip" style="background: ${statusColor(entity.status)}">${escapeHtml(
          entity.status_label,
        )}</span></td>
        <td>${escapeHtml(entity.detail || "—")}</td>
      </tr>`,
    )
    .join("");
}

function render(payload: DashboardPayload): void {
  el.subtitle.textContent = `${payload.entity_type} status overview · generated ${new Date(
    payload.generated_at,
  ).toLocaleString()}`;
  if (el.entityType.value !== payload.entity_type && ENTITY_TYPES.includes(payload.entity_type as never)) {
    el.entityType.value = payload.entity_type;
  }
  renderSummary(payload);
  renderDistribution(payload);
  renderEntities(payload);
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/** Pull the dashboard payload out of an MCP tool result. */
function extractPayload(result: unknown): DashboardPayload | null {
  if (!result || typeof result !== "object") {
    return null;
  }
  const candidate = result as { structuredContent?: unknown; content?: unknown };

  if (candidate.structuredContent && typeof candidate.structuredContent === "object") {
    return candidate.structuredContent as DashboardPayload;
  }

  if (Array.isArray(candidate.content)) {
    for (const part of candidate.content) {
      if (part && typeof part === "object" && typeof (part as { text?: unknown }).text === "string") {
        try {
          return JSON.parse((part as { text: string }).text) as DashboardPayload;
        } catch {
          continue;
        }
      }
    }
  }

  return null;
}

const app = new App({ name: "ShotGridDashboard", version: "1.0.0" }, {}, { autoResize: true });

async function requestDashboard(entityType: string): Promise<void> {
  el.refresh.disabled = true;
  const previousLabel = el.refresh.textContent;
  el.refresh.textContent = "Loading…";
  try {
    const result = await app.callServerTool({
      name: DASHBOARD_TOOL,
      arguments: { entity_type: entityType },
    });
    const payload = extractPayload(result);
    if (!payload) {
      el.subtitle.textContent = "The server returned no dashboard data.";
      return;
    }
    render(payload);
  } catch (error) {
    el.subtitle.textContent = `Failed to load dashboard: ${error instanceof Error ? error.message : String(error)}`;
  } finally {
    el.refresh.disabled = false;
    el.refresh.textContent = previousLabel ?? "Refresh";
  }
}

function boot(): void {
  el.entityType.innerHTML = ENTITY_TYPES.map(
    (type) => `<option value="${type}">${type}</option>`,
  ).join("");
  el.entityType.value = "Task";

  el.refresh.addEventListener("click", () => {
    void requestDashboard(el.entityType.value);
  });
  el.entityType.addEventListener("change", () => {
    void requestDashboard(el.entityType.value);
  });

  el.footer.innerHTML = `<span>MCP Apps sample · fastmcp</span><span id="host-name">host: unknown</span>`;
}

/** Mark the interactive controls unusable when the host cannot proxy tool calls. */
function applyHostCapabilities(): void {
  // Server tool calls are proxied by the host; when the host does not advertise
  // that capability the app still renders whatever the initial tool result gave it.
  if (!app.getHostCapabilities()?.serverTools) {
    el.refresh.disabled = true;
    el.entityType.disabled = true;
    el.refresh.title = "This host does not proxy MCP tool calls";
  }
}

app.ontoolresult = (result) => {
  const payload = extractPayload(result);
  if (!payload) {
    el.subtitle.textContent = "Waiting for data…";
    return;
  }
  render(payload);
};

app.onerror = (message) => {
  el.subtitle.textContent = message;
};

boot();

// `connect()` completes the ui/initialize handshake, so host capabilities are
// only known afterwards.
app.connect().then(applyHostCapabilities).catch((error) => {
  el.subtitle.textContent = `Failed to connect to the host: ${
    error instanceof Error ? error.message : String(error)
  }`;
});
