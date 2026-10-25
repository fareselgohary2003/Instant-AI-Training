import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  AreaChart,
  Area,
} from "recharts";

const STATUS_COLORS = {
  Pending: "#f59e0b",
  Reviewed: "#10b981",
  Dismissed: "#ef4444",
};

const BEHAVIOR_COLORS = {
  peeking: "#8b5cf6",
  phone: "#ef4444",
  notes: "#f59e0b",
  book: "#f59e0b",
  laptop: "#0ea5e9",
  other: "#64748b",
};

function getBehaviorColor(name) {
  const lower = name.toLowerCase();
  for (const [key, color] of Object.entries(BEHAVIOR_COLORS)) {
    if (lower.includes(key)) return color;
  }
  return "#3b82f6";
}

export default function DashboardCharts({ incidents = [], stats = {}, isDark = false }) {
  const statusData = [
    { name: "Pending", value: Number(stats.pending ?? 0) },
    { name: "Reviewed", value: Number(stats.reviewed ?? 0) },
    { name: "Dismissed", value: Number(stats.dismissed ?? 0) },
  ];

  const typeCounts = incidents.reduce((counts, incident) => {
    let type = incident.event_type || "Unknown";
    type = type
      .replaceAll("_", " ")
      .replace("detected", "")
      .replace("required", "")
      .trim()
      .replace(/\b\w/g, (c) => c.toUpperCase());
    counts[type] = (counts[type] || 0) + 1;
    return counts;
  }, {});

  const typeData = Object.entries(typeCounts).map(([name, count]) => ({
    name,
    count,
    color: getBehaviorColor(name),
  }));

  // Group incidents into time intervals or chronological index for trend
  const timelineData = [...incidents]
    .slice(-15)
    .map((item, idx) => ({
      index: `#${item.id}`,
      confidence: Math.round((item.confidence || 0) * 100),
      student: `Student #${item.track_id || "?"}`,
      type: item.event_type ? item.event_type.replace(/_/g, " ") : "Threat",
    }));

  const hasStatusData = statusData.some((item) => item.value > 0);
  const gridColor = isDark ? "rgba(255, 255, 255, 0.08)" : "#f1f5f9";
  const textColor = isDark ? "#94a3b8" : "#64748b";
  const tooltipBg = isDark ? "#1e293b" : "#ffffff";
  const tooltipBorder = isDark ? "#334155" : "#e2e8f0";

  return (
    <section className="dashboard-charts-grid">
      {/* 1. Review Status Donut Chart */}
      <div className="chart-card">
        <div className="chart-heading">
          <div>
            <h3>Review Status Distribution</h3>
            <p>Verification state of security alerts</p>
          </div>
          <span className="chart-badge">{incidents.length} Events</span>
        </div>

        {hasStatusData ? (
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={statusData.filter((item) => item.value > 0)}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="45%"
                innerRadius={55}
                outerRadius={88}
                paddingAngle={4}
                stroke={isDark ? "#111827" : "#ffffff"}
                strokeWidth={2}
              >
                {statusData
                  .filter((item) => item.value > 0)
                  .map((item) => (
                    <Cell
                      key={item.name}
                      fill={STATUS_COLORS[item.name]}
                    />
                  ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: tooltipBg,
                  borderColor: tooltipBorder,
                  borderRadius: "10px",
                  fontSize: "12px",
                  color: isDark ? "#f8fafc" : "#0f172a",
                }}
              />
              <Legend
                wrapperStyle={{ fontSize: "12px", paddingTop: "10px" }}
              />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div className="chart-empty">No incidents recorded yet.</div>
        )}
      </div>

      {/* 2. Incidents by Cheating Behavior Bar Chart */}
      <div className="chart-card">
        <div className="chart-heading">
          <div>
            <h3>Threats by Behavior Type</h3>
            <p>Frequency of detected cheating modes</p>
          </div>
          <span className="chart-badge">AI Classified</span>
        </div>

        {typeData.length > 0 ? (
          <ResponsiveContainer width="100%" height={260}>
            <BarChart
              data={typeData}
              margin={{ top: 15, right: 15, left: -15, bottom: 40 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
              <XAxis
                dataKey="name"
                interval={0}
                angle={-15}
                textAnchor="end"
                height={55}
                tick={{ fontSize: 11, fill: textColor }}
              />
              <YAxis
                allowDecimals={false}
                tick={{ fontSize: 11, fill: textColor }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: tooltipBg,
                  borderColor: tooltipBorder,
                  borderRadius: "10px",
                  fontSize: "12px",
                  color: isDark ? "#f8fafc" : "#0f172a",
                }}
              />
              <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                {typeData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="chart-empty">No behaviors flagged yet.</div>
        )}
      </div>

      {/* 3. Threat Confidence Timeline Trend */}
      <div className="chart-card chart-card-wide">
        <div className="chart-heading">
          <div>
            <h3>Detection Confidence Flow (Recent Incidents)</h3>
            <p>Model certainty and threat severity progression across detections</p>
          </div>
          <span className="chart-badge">YOLOv8 + Pose</span>
        </div>

        {timelineData.length > 0 ? (
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart
              data={timelineData}
              margin={{ top: 10, right: 20, left: -10, bottom: 0 }}
            >
              <defs>
                <linearGradient id="colorConfidence" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
              <XAxis
                dataKey="index"
                tick={{ fontSize: 11, fill: textColor }}
              />
              <YAxis
                domain={[0, 100]}
                unit="%"
                tick={{ fontSize: 11, fill: textColor }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: tooltipBg,
                  borderColor: tooltipBorder,
                  borderRadius: "10px",
                  fontSize: "12px",
                  color: isDark ? "#f8fafc" : "#0f172a",
                }}
                formatter={(val) => [`${val}%`, "AI Confidence"]}
                labelFormatter={(lbl) => `Incident ${lbl}`}
              />
              <Area
                type="monotone"
                dataKey="confidence"
                stroke="#3b82f6"
                strokeWidth={3}
                fillOpacity={1}
                fill="url(#colorConfidence)"
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="chart-empty">No timeline data available.</div>
        )}
      </div>
    </section>
  );
}