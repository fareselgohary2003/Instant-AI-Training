import { useState } from "react";
import {
  Users,
  AlertTriangle,
  CheckCircle2,
  Eye,
  FileText,
  Clock,
  Activity,
  Layers,
  ChevronRight,
  ShieldAlert,
} from "lucide-react";

export default function StudentRoster({
  incidents = [],
  onSelectStudent,
  onGenerateReport,
}) {
  const [filterMode, setFilterMode] = useState("all"); // 'all', 'high_risk', 'clean', 'reviewed'

  // Aggregate incidents by student track_id
  const studentMap = {};

  incidents.forEach((inc) => {
    const tid = inc.track_id !== null && inc.track_id !== undefined ? inc.track_id : "Unknown";
    if (!studentMap[tid]) {
      studentMap[tid] = {
        track_id: tid,
        total_incidents: 0,
        behaviors: {},
        max_confidence: 0,
        first_seen: inc.timestamp,
        last_seen: inc.timestamp,
        has_reviewed: false,
        has_dismissed: false,
        has_pending: false,
        incidents: [],
      };
    }

    const s = studentMap[tid];
    s.total_incidents += 1;
    s.incidents.push(inc);

    const bType = inc.event_type || "unspecified";
    s.behaviors[bType] = (s.behaviors[bType] || 0) + 1;

    if ((inc.confidence || 0) > s.max_confidence) {
      s.max_confidence = inc.confidence;
    }

    if (new Date(inc.timestamp) < new Date(s.first_seen)) {
      s.first_seen = inc.timestamp;
    }
    if (new Date(inc.timestamp) > new Date(s.last_seen)) {
      s.last_seen = inc.timestamp;
    }

    if (inc.review_status === "reviewed") s.has_reviewed = true;
    else if (inc.review_status === "dismissed") s.has_dismissed = true;
    else s.has_pending = true;
  });

  const studentsList = Object.values(studentMap).map((s) => {
    let riskTier = "LOW";
    let riskColor = "var(--color-success)";
    let badgeClass = "badge-success";

    if (s.total_incidents >= 4 || s.has_reviewed) {
      riskTier = "CRITICAL";
      riskColor = "var(--color-danger)";
      badgeClass = "badge-danger";
    } else if (s.total_incidents >= 2 || s.has_pending) {
      riskTier = "ELEVATED";
      riskColor = "var(--color-warning)";
      badgeClass = "badge-amber";
    }

    return {
      ...s,
      riskTier,
      riskColor,
      badgeClass,
    };
  });

  // Sort by highest risk / incident count
  studentsList.sort((a, b) => b.total_incidents - a.total_incidents);

  const filteredStudents = studentsList.filter((s) => {
    if (filterMode === "high_risk") return s.riskTier === "CRITICAL";
    if (filterMode === "elevated") return s.riskTier === "ELEVATED";
    if (filterMode === "reviewed") return s.has_reviewed;
    return true;
  });

  function formatTime(val) {
    if (!val) return "—";
    const d = new Date(val);
    return isNaN(d.getTime()) ? val : d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  }

  function cleanBehaviorName(name) {
    return name
      .replace(/_/g, " ")
      .replace("detected", "")
      .replace("required", "")
      .trim()
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }

  return (
    <div className="student-roster-container animate-fade">
      {/* Header Bar */}
      <div className="roster-header-panel">
        <div>
          <span className="section-eyebrow">
            <Users size={13} />
            EXAM ATTENDEE SURVEILLANCE
          </span>
          <h2>Tracked Students &amp; Academic Integrity Status</h2>
          <p className="roster-subtitle">
            Comprehensive audit of every student tracked by ByteTrack, aggregated across all examination sessions.
          </p>
        </div>

        <div className="roster-actions">
          <div className="filter-pill-group">
            <button
              className={`filter-pill ${filterMode === "all" ? "active" : ""}`}
              onClick={() => setFilterMode("all")}
            >
              All Students ({studentsList.length})
            </button>
            <button
              className={`filter-pill ${filterMode === "high_risk" ? "active" : ""}`}
              onClick={() => setFilterMode("high_risk")}
            >
              Critical Risk ({studentsList.filter((s) => s.riskTier === "CRITICAL").length})
            </button>
            <button
              className={`filter-pill ${filterMode === "elevated" ? "active" : ""}`}
              onClick={() => setFilterMode("elevated")}
            >
              Elevated Watch ({studentsList.filter((s) => s.riskTier === "ELEVATED").length})
            </button>
            <button
              className={`filter-pill ${filterMode === "reviewed" ? "active" : ""}`}
              onClick={() => setFilterMode("reviewed")}
            >
              Confirmed Cases ({studentsList.filter((s) => s.has_reviewed).length})
            </button>
          </div>
        </div>
      </div>

      {/* Student Cards Grid */}
      <div className="students-cards-grid">
        {filteredStudents.map((student) => (
          <div key={student.track_id} className="student-profile-card">
            <div className="card-top-row">
              <div className="student-identity">
                <div
                  className="student-avatar"
                  style={{
                    borderColor: student.riskColor,
                    boxShadow: `0 0 12px ${student.riskColor}33`,
                  }}
                >
                  <span>#{student.track_id}</span>
                </div>
                <div>
                  <h3 className="student-name">Student #{student.track_id}</h3>
                  <span className="student-session-meta">
                    <Clock size={11} /> First flagged: {formatTime(student.first_seen)}
                  </span>
                </div>
              </div>

              <span className={`badge ${student.badgeClass}`}>
                {student.riskTier} RISK
              </span>
            </div>

            {/* Quick Metrics */}
            <div className="student-metrics-row">
              <div className="student-metric-box">
                <span className="metric-title">TOTAL FLAGS</span>
                <strong className="metric-number text-danger">
                  {student.total_incidents}
                </strong>
              </div>
              <div className="student-metric-box">
                <span className="metric-title">MAX CONFIDENCE</span>
                <strong className="metric-number">
                  {Math.round((student.max_confidence || 0) * 100)}%
                </strong>
              </div>
              <div className="student-metric-box">
                <span className="metric-title">STATUS</span>
                <strong className="metric-number text-muted">
                  {student.has_reviewed
                    ? "Confirmed"
                    : student.has_pending
                    ? "Pending"
                    : "Dismissed"}
                </strong>
              </div>
            </div>

            {/* Detected Behaviors Chips */}
            <div className="behaviors-section">
              <span className="section-label-tiny">DETECTED INFRACTIONS:</span>
              <div className="behavior-chips-wrap">
                {Object.entries(student.behaviors).map(([bName, count]) => (
                  <span key={bName} className="behavior-chip">
                    {cleanBehaviorName(bName)} &times; {count}
                  </span>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="card-action-footer">
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => onSelectStudent(student.track_id)}
                title="View all snapshots for this student"
              >
                <Eye size={13} />
                <span>View Evidence ({student.total_incidents})</span>
              </button>

              <button
                className="btn btn-primary btn-sm"
                onClick={() => onGenerateReport(student)}
                title="Generate official academic integrity report"
              >
                <FileText size={13} />
                <span>Dossier</span>
              </button>
            </div>
          </div>
        ))}

        {filteredStudents.length === 0 && (
          <div className="roster-empty-state">
            <ShieldAlert size={48} />
            <h3>No Students In This Category</h3>
            <p>All students currently have clear records or no incidents match the filter.</p>
          </div>
        )}
      </div>
    </div>
  );
}
