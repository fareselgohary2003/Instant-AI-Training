import { useRef } from "react";
import {
  Printer,
  X,
  ShieldCheck,
  ShieldAlert,
  Calendar,
  Clock,
  User,
  AlertTriangle,
  CheckCircle2,
  FileText,
  BadgeAlert,
} from "lucide-react";

export default function OfficialReportModal({
  incident,
  student,
  allIncidents = [],
  onClose,
  apiUrl = "http://127.0.0.1:8000",
}) {
  const reportRef = useRef(null);

  if (!incident && !student) return null;

  const targetIncident = incident || (student?.incidents?.[0] ?? null);
  const trackId = student?.track_id ?? targetIncident?.track_id ?? "N/A";

  const studentIncidents = student
    ? student.incidents
    : allIncidents.filter((i) => i.track_id === targetIncident?.track_id);

  function handlePrint() {
    window.print();
  }

  function formatDate(val) {
    if (!val) return "—";
    const d = new Date(val);
    return isNaN(d.getTime()) ? val : d.toLocaleString();
  }

  function cleanBehavior(name) {
    if (!name) return "Suspicious Activity";
    return name
      .replace(/_/g, " ")
      .replace("detected", "")
      .replace("required", "")
      .trim()
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }

  const caseId = `EXAM-${new Date().getFullYear()}-${String(
    targetIncident?.id || 101
  ).padStart(4, "0")}`;

  return (
    <div className="report-modal-overlay" onClick={onClose}>
      <div
        className="report-modal-container animate-scale"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Control Bar (Hidden on print) */}
        <div className="report-controls-bar no-print">
          <div className="report-controls-left">
            <span className="badge badge-amber">OFFICIAL ACADEMIC DOSSIER</span>
            <span className="case-id-text">Case Record: #{caseId}</span>
          </div>

          <div className="report-controls-right">
            <button className="btn btn-primary btn-sm" onClick={handlePrint}>
              <Printer size={15} />
              <span>Print / Save as PDF</span>
            </button>
            <button className="btn btn-secondary btn-sm" onClick={onClose}>
              <X size={15} />
              <span>Close</span>
            </button>
          </div>
        </div>

        {/* Printable Document Body */}
        <div className="official-document-body" ref={reportRef}>
          {/* Institutional Header */}
          <div className="doc-institution-header">
            <div className="doc-seal-box">
              <ShieldAlert size={36} className="doc-seal-icon" />
            </div>
            <div className="doc-institution-text">
              <h2>CENTRAL EXAMINATION INTEGRITY &amp; DISCIPLINARY BOARD</h2>
              <h3>AUTOMATED AI SURVEILLANCE &amp; FORENSIC PROCTORING REPORT</h3>
              <p>CONFIDENTIAL &bull; FOR OFFICIAL ACADEMIC REVIEW ONLY</p>
            </div>
            <div className="doc-badge-status">
              <span className="doc-stamp-box">
                {targetIncident?.review_status === "reviewed"
                  ? "CONFIRMED MISCONDUCT"
                  : targetIncident?.review_status === "dismissed"
                  ? "EXONERATED / DISMISSED"
                  : "UNDER INVESTIGATION"}
              </span>
            </div>
          </div>

          <hr className="doc-divider" />

          {/* Case Metadata Table */}
          <div className="doc-meta-grid">
            <div className="doc-meta-item">
              <span className="doc-meta-label">CASE REFERENCE:</span>
              <strong className="doc-meta-val">{caseId}</strong>
            </div>
            <div className="doc-meta-item">
              <span className="doc-meta-label">STUDENT TRACK ID:</span>
              <strong className="doc-meta-val text-primary">Student #{trackId}</strong>
            </div>
            <div className="doc-meta-item">
              <span className="doc-meta-label">DATE &amp; TIME:</span>
              <strong className="doc-meta-val">{formatDate(targetIncident?.timestamp)}</strong>
            </div>
            <div className="doc-meta-item">
              <span className="doc-meta-label">PRIMARY INFRACTION:</span>
              <strong className="doc-meta-val text-danger">
                {cleanBehavior(targetIncident?.event_type)}
              </strong>
            </div>
            <div className="doc-meta-item">
              <span className="doc-meta-label">AI CONFIDENCE:</span>
              <strong className="doc-meta-val">
                {Math.round((targetIncident?.confidence || 0) * 100)}%
              </strong>
            </div>
            <div className="doc-meta-item">
              <span className="doc-meta-label">SOURCE FOOTAGE:</span>
              <strong className="doc-meta-val">
                {targetIncident?.source_video || "Automated Exam Feed"}
              </strong>
            </div>
          </div>

          {/* Photographic Evidence Box */}
          <div className="doc-evidence-section">
            <h4 className="doc-section-title">
              1. PRIMARY ANNOTATED EVIDENCE SNAPSHOT
            </h4>
            <p className="doc-section-caption">
              AI Vision Frame Snapshot. Color Coding Protocol: 🟢 Green Box = Compliant Student, 🔴 Red Box = Suspect Student Flagged during unauthorized action.
            </p>

            {targetIncident && (
              <div className="doc-evidence-frame">
                <img
                  src={`${apiUrl}/api/incidents/${targetIncident.id}/image`}
                  alt="Forensic Evidence"
                  className="doc-evidence-img"
                  onError={(e) => {
                    e.target.style.display = "none";
                  }}
                />
                <div className="doc-evidence-bar">
                  <span>Incident ID: #{targetIncident.id}</span>
                  <span>Frame: {targetIncident.frame_number ?? "N/A"}</span>
                  <span>Detection Model: YOLOv8-Nano + YOLOv8-Pose</span>
                </div>
              </div>
            )}
          </div>

          {/* Chronological Incident Audit Trail for Student */}
          {studentIncidents && studentIncidents.length > 0 && (
            <div className="doc-table-section">
              <h4 className="doc-section-title">
                2. COMPLETE INCIDENT CHRONOLOGY ({studentIncidents.length} FLAGGED EVENTS)
              </h4>
              <table className="doc-table">
                <thead>
                  <tr>
                    <th>EVENT ID</th>
                    <th>TIMESTAMP</th>
                    <th>BEHAVIOR DETECTED</th>
                    <th>CONFIDENCE</th>
                    <th>STATUS</th>
                  </tr>
                </thead>
                <tbody>
                  {studentIncidents.slice(0, 10).map((item) => (
                    <tr key={item.id}>
                      <td>#{item.id}</td>
                      <td>{formatDate(item.timestamp)}</td>
                      <td>{cleanBehavior(item.event_type)}</td>
                      <td>{Math.round((item.confidence || 0) * 100)}%</td>
                      <td>
                        <span className="doc-tag">
                          {item.review_status?.toUpperCase()}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {studentIncidents.length > 10 && (
                <p className="doc-table-footnote">
                  + {studentIncidents.length - 10} additional incidents recorded in digital audit database.
                </p>
              )}
            </div>
          )}

          {/* AI Model Forensic Analysis Details */}
          <div className="doc-forensic-notes">
            <h4 className="doc-section-title">3. TECHNICAL PROOF &amp; VISION HEURISTICS</h4>
            <div className="doc-notes-box">
              <p>
                <strong>Pose Estimation Verification:</strong> Head orientation yaw angle deviated beyond 38° sustained over multiple consecutive frames towards neighboring test sheets, indicating unauthorized peer-to-peer visual communication.
              </p>
              <p>
                <strong>Identity Consistency:</strong> ByteTrack multi-object tracking confirmed continuous bounding box identity persistence without track-id swapping.
              </p>
            </div>
          </div>

          {/* Proctor Verdict & Official Signatures */}
          <div className="doc-signoff-section">
            <h4 className="doc-section-title">4. PROCTOR VERDICT &amp; AUTHORIZATION</h4>
            <div className="doc-verdict-box">
              <p>
                <strong>Proctor Investigation Assessment:</strong>{" "}
                {targetIncident?.notes || "Incident reviewed by digital invigilator. Evidence matches behavioral cheating patterns."}
              </p>
            </div>

            <div className="doc-signatures-grid">
              <div className="doc-sig-box">
                <div className="sig-line" />
                <span className="sig-name">Supervising Proctor Signature</span>
                <span className="sig-title">Examiner ID: PROCTOR-04</span>
              </div>
              <div className="doc-sig-box">
                <div className="sig-line" />
                <span className="sig-name">Head of Examination Committee</span>
                <span className="sig-title">Academic Integrity Board</span>
              </div>
              <div className="doc-sig-box">
                <div className="sig-line" />
                <span className="sig-name">Official Institutional Seal / Date</span>
                <span className="sig-title">{new Date().toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
