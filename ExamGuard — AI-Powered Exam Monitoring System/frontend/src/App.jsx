import { useCallback, useEffect, useState, useRef, useMemo } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Eye,
  RefreshCw,
  ShieldCheck,
  Smartphone,
  XCircle,
  Save,
  FileText,
  LayoutDashboard,
  Search,
  ArrowLeft,
  UploadCloud,
  Play,
  Film,
  Settings,
  Sliders,
  Check,
  AlertCircle,
  Cpu,
  Database,
  ExternalLink,
  ChevronRight,
  ChevronLeft,
  BookOpen,
  Laptop,
  Moon,
  Sun,
  Volume2,
  VolumeX,
  Download,
  Filter,
  Users,
  ShieldAlert,
  HelpCircle,
  Maximize2,
  Layers,
  ZoomIn,
  ZoomOut,
  Printer,
  Sparkles,
  Award,
  Camera,
  Video,
  Square,
  Radio,
  Target,
} from "lucide-react";
import "./App.css";
import DashboardCharts from "./DashboardCharts";
import StudentRoster from "./StudentRoster";
import OfficialReportModal from "./OfficialReportModal";

const API_URL = "http://127.0.0.1:8000";

const STATUS_LABELS = {
  pending: "Pending Review",
  reviewed: "Confirmed Misconduct",
  dismissed: "False Alarm",
};

// Web Audio API Synthesizer for instant audible alerts without external files
function playSecurityChime() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
    osc.frequency.exponentialRampToValueAtTime(880.0, ctx.currentTime + 0.12); // A5
    gain.gain.setValueAtTime(0.15, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.35);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.35);
  } catch (_) {}
}

export default function App() {
  const [isDark, setIsDark] = useState(() => {
    return localStorage.getItem("examguard_theme") === "light" ? false : true;
  });

  const [incidents, setIncidents] = useState([]);
  const [stats, setStats] = useState({
    total_incidents: 0,
    pending: 0,
    reviewed: 0,
    dismissed: 0,
  });
  const [sampleVideos, setSampleVideos] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [systemInfo, setSystemInfo] = useState(null);
  const [activeJob, setActiveJob] = useState({
    is_running: false,
    processed_frames: 0,
    total_frames: 0,
    fps: 0,
    incident_count: 0,
    people_count: 0,
    status: "idle",
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [activePage, setActivePage] = useState("dashboard"); // 'dashboard' | 'upload' | 'review' | 'students' | 'videos' | 'settings'
  const [filter, setFilter] = useState("all");
  const [behaviorFilter, setBehaviorFilter] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [studentFilter, setStudentFilter] = useState(null);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [reviewStatus, setReviewStatus] = useState("pending");
  const [reviewNotes, setReviewNotes] = useState("");
  const [updatingId, setUpdatingId] = useState(null);

  // Ingestion Mode: 'live' (laptop webcam) vs 'upload' (recorded video)
  const [ingestMode, setIngestMode] = useState("live");
  const [liveStatus, setLiveStatus] = useState({
    is_running: false,
    camera_index: 0,
    fps: 0,
    people_count: 0,
    incident_count: 0,
    session_start_time: null,
    last_incident: "",
  });

  // Video playback & jump-to-incident targeting
  const [playingVideo, setPlayingVideo] = useState(null);
  const [videoSeekTarget, setVideoSeekTarget] = useState(null);
  const videoPlayerRef = useRef(null);

  // Advanced Review Modal Features
  const [zoomLevel, setZoomLevel] = useState(1);
  const [dossierData, setDossierData] = useState(null);

  // Audio & Security Features
  const [soundEnabled, setSoundEnabled] = useState(true);

  // Video processing states
  const [selectedVideoPath, setSelectedVideoPath] = useState("");
  const [selectedVideoName, setSelectedVideoName] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");
  const [confThreshold, setConfThreshold] = useState(0.10);

  const fileInputRef = useRef(null);

  // Toggle theme
  function toggleTheme() {
    const next = !isDark;
    setIsDark(next);
    localStorage.setItem("examguard_theme", next ? "dark" : "light");
  }

  // Load main dashboard data
  const loadData = useCallback(async (showLoader = false) => {
    if (showLoader) setLoading(true);
    try {
      const [incRes, statsRes, samRes, jobsRes, sysRes, jobStateRes] =
        await Promise.all([
          fetch(`${API_URL}/api/incidents`).catch(() => null),
          fetch(`${API_URL}/api/stats`).catch(() => null),
          fetch(`${API_URL}/api/sample-videos`).catch(() => null),
          fetch(`${API_URL}/api/jobs`).catch(() => null),
          fetch(`${API_URL}/api/system-info`).catch(() => null),
          fetch(`${API_URL}/api/active-job`).catch(() => null),
        ]);

      if (incRes && incRes.ok) setIncidents(await incRes.json());
      if (statsRes && statsRes.ok) setStats(await statsRes.json());
      if (samRes && samRes.ok) {
        const vids = await samRes.json();
        setSampleVideos(vids);
        if (!selectedVideoPath && vids.length > 0) {
          setSelectedVideoPath(vids[0].path);
          setSelectedVideoName(vids[0].filename);
        }
      }
      if (jobsRes && jobsRes.ok) setJobs(await jobsRes.json());
      if (sysRes && sysRes.ok) setSystemInfo(await sysRes.json());
      if (jobStateRes && jobStateRes.ok) {
        const jstate = await jobStateRes.json();
        setActiveJob(jstate);
      }
    } catch (_) {
      setError("Could not reach backend API at " + API_URL);
    } finally {
      if (showLoader) setLoading(false);
    }
  }, [selectedVideoPath]);

  useEffect(() => {
    loadData(true);
  }, []);

  // Poll live webcam status & telemetry
  useEffect(() => {
    let timer = null;
    let prevIncCount = 0;

    const checkLive = async () => {
      try {
        const res = await fetch(`${API_URL}/api/live-stream/status`);
        if (res.ok) {
          const data = await res.json();
          setLiveStatus(data);

          if (data.incident_count > prevIncCount && soundEnabled) {
            playSecurityChime();
            prevIncCount = data.incident_count;
            loadData(false); // reload incidents in background
          }
        }
      } catch (_) {}
    };

    checkLive();
    timer = setInterval(checkLive, 1200);

    return () => {
      if (timer) clearInterval(timer);
    };
  }, [soundEnabled, loadData]);

  // Start live webcam session
  async function handleStartLiveCam() {
    setError("");
    setSuccess("");
    try {
      const res = await fetch(`${API_URL}/api/live-stream/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          camera_index: 0,
          confidence_threshold: Number(confThreshold),
          cooldown_seconds: 3.5,
        }),
      });
      const data = await res.json();
      setLiveStatus((prev) => ({ ...prev, is_running: true }));
      setSuccess("Live laptop camera proctoring started! Green = compliant, Red = cheating alert.");
      if (soundEnabled) playSecurityChime();
    } catch (e) {
      setError("Failed to start laptop webcam: " + e.message);
    }
  }

  // Stop live webcam session
  async function handleStopLiveCam() {
    try {
      await fetch(`${API_URL}/api/live-stream/stop`, { method: "POST" });
      setLiveStatus((prev) => ({ ...prev, is_running: false }));
      setSuccess("Live webcam session ended. All incidents recorded in database.");
      loadData(false);
    } catch (e) {
      setError("Failed to stop webcam: " + e.message);
    }
  }

  // Poll active video job progress while running
  useEffect(() => {
    let intervalId = null;
    let prevIncCount = activeJob.incident_count;

    if (activeJob.is_running) {
      intervalId = setInterval(async () => {
        try {
          const res = await fetch(`${API_URL}/api/active-job`);
          if (res.ok) {
            const data = await res.json();
            setActiveJob(data);

            if (data.incident_count > prevIncCount && soundEnabled) {
              playSecurityChime();
              prevIncCount = data.incident_count;
            }

            if (!data.is_running) {
              loadData(false);
              setSuccess("Video analysis completed! All incidents and evidence saved.");
              if (soundEnabled) playSecurityChime();
            }
          }
        } catch (_) {}
      }, 1000);
    }
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [activeJob.is_running, soundEnabled, loadData]);

  // Handle local file upload
  async function handleFileUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadStatus("Uploading " + file.name + "...");
    setError("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_URL}/api/upload-video`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Upload failed");
      }

      const data = await res.json();
      setSelectedVideoPath(data.path);
      setSelectedVideoName(data.filename);
      setUploadStatus("Uploaded: " + data.filename + " (" + data.size_mb + " MB)");
      setSuccess("Video uploaded successfully. Ready to process!");
      loadData(false);
    } catch (err) {
      setError(err.message || "Failed to upload video.");
      setUploadStatus("");
    } finally {
      setIsUploading(false);
    }
  }

  // Trigger AI video processing
  async function handleStartProcessing(customPath = null) {
    const targetPath = customPath || selectedVideoPath;
    if (!targetPath) {
      setError("Please select or upload a video first.");
      return;
    }

    setError("");
    setSuccess("");

    try {
      const res = await fetch(`${API_URL}/api/process-video`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          video_path: targetPath,
          confidence_threshold: Number(confThreshold),
          cooldown_seconds: 4.0,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to trigger processing");
      }

      setActiveJob({
        is_running: true,
        job_id: data.job_id,
        source_video: selectedVideoName || targetPath,
        processed_frames: 0,
        total_frames: 100,
        fps: 0,
        incident_count: 0,
        status: "processing",
      });

      setSuccess("AI proctoring processing started! Real-time frame tracking active.");
      if (soundEnabled) playSecurityChime();
    } catch (err) {
      setError(err.message || "Could not start video processing.");
    }
  }

  // Jump to exact video moment from incident snapshot
  function jumpToIncidentVideo(incident) {
    if (!incident) return;

    let targetFile = null;
    let fps = 25.0;

    // Match job by job_id or source_video name
    const matchingJob =
      jobs.find(
        (j) =>
          (incident.job_id && j.job_id === incident.job_id) ||
          (incident.source_video &&
            j.source_video &&
            (j.source_video.includes(incident.source_video) ||
              incident.source_video.includes(j.source_video)))
      ) || jobs.find((j) => j.output_video);

    if (matchingJob?.output_video) {
      targetFile = matchingJob.output_video.split("\\").pop().split("/").pop();
      fps = matchingJob.fps || 25.0;
    } else if (jobs.length > 0 && jobs[0].output_video) {
      targetFile = jobs[0].output_video.split("\\").pop().split("/").pop();
      fps = jobs[0].fps || 25.0;
    }

    const frameNum = incident.frame_number || 0;
    const seekSeconds = Math.max(0, frameNum / fps - 0.75); // buffer ~0.8s before

    if (targetFile) {
      setPlayingVideo(targetFile);
    }

    setVideoSeekTarget({
      time: seekSeconds,
      frame: frameNum,
      incidentId: incident.id,
      studentId: incident.track_id,
      eventType: incident.event_type,
      notes: incident.notes,
    });

    setActivePage("videos");

    if (selectedIncident) {
      setSelectedIncident(null);
    }

    setTimeout(() => {
      if (videoPlayerRef.current) {
        videoPlayerRef.current.currentTime = seekSeconds;
        videoPlayerRef.current.play().catch(() => {});
      }
    }, 300);
  }

  // Save incident review
  async function saveReview() {
    if (!selectedIncident) return;
    setUpdatingId(selectedIncident.id);
    setError("");
    setSuccess("");

    try {
      const res = await fetch(
        `${API_URL}/api/incidents/${selectedIncident.id}/review`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            status: reviewStatus,
            notes: reviewNotes,
          }),
        }
      );

      const result = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(result.detail || "Could not save incident review");
      }

      setSuccess("Review decision and notes saved successfully.");
      await loadData(false);
      setSelectedIncident((cur) =>
        cur?.id === selectedIncident.id ? { ...cur, ...result.incident } : cur
      );
    } catch (err) {
      setError(err.message || "Could not save the review.");
    } finally {
      setUpdatingId(null);
    }
  }

  // Export CSV Report
  function exportCSVReport() {
    if (incidents.length === 0) return;
    const headers = [
      "ID",
      "Timestamp",
      "Student Track ID",
      "Behavior Type",
      "Confidence",
      "Status",
      "Notes",
      "Source Video",
    ];
    const rows = incidents.map((i) => [
      i.id,
      i.timestamp,
      i.track_id ?? "",
      i.event_type ?? "",
      Math.round((i.confidence || 0) * 100) + "%",
      i.review_status ?? "",
      `"${(i.notes || "").replace(/"/g, '""')}"`,
      i.source_video ?? "",
    ]);

    const csvContent =
      "data:text/csv;charset=utf-8," +
      [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute(
      "download",
      `ExamGuard_Incident_Report_${new Date().toISOString().slice(0, 10)}.csv`
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  function openReview(incident) {
    setSelectedIncident(incident);
    setReviewStatus(incident.review_status || "pending");
    setReviewNotes(incident.notes || "");
    setZoomLevel(1);
  }

  function closeReview() {
    setSelectedIncident(null);
    setZoomLevel(1);
  }

  function formatDate(val) {
    if (!val) return "—";
    const d = new Date(val);
    return Number.isNaN(d.getTime()) ? val : d.toLocaleString();
  }

  function formatEventType(evt) {
    if (!evt) return "General Incident";
    return evt
      .replaceAll("_", " ")
      .replace("detected", "")
      .replace("required", "")
      .trim()
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }

  function getSeverity(type, conf = 0) {
    const t = (type || "").toLowerCase();
    if (t.includes("phone") || t.includes("laptop"))
      return { label: "CRITICAL", class: "severity-critical" };
    if (t.includes("peeking") || conf >= 0.75)
      return { label: "HIGH", class: "severity-high" };
    return { label: "MEDIUM", class: "severity-medium" };
  }

  // Filtered incidents
  const filteredIncidents = useMemo(() => {
    return incidents.filter((item) => {
      const matchesStatus = filter === "all" || item.review_status === filter;
      const matchesBehavior =
        behaviorFilter === "all" ||
        (behaviorFilter === "peeking" && item.event_type?.includes("peeking")) ||
        (behaviorFilter === "phone" && item.event_type?.includes("phone")) ||
        (behaviorFilter === "laptop" && item.event_type?.includes("laptop")) ||
        (behaviorFilter === "book" &&
          (item.event_type?.includes("book") || item.event_type?.includes("notes")));

      const matchesStudent =
        studentFilter === null || item.track_id === studentFilter;

      const query = searchTerm.trim().toLowerCase();
      const matchesSearch =
        !query ||
        String(item.id).includes(query) ||
        String(item.track_id ?? "").includes(query) ||
        String(item.event_type ?? "").toLowerCase().includes(query) ||
        String(item.notes ?? "").toLowerCase().includes(query);

      return matchesStatus && matchesBehavior && matchesStudent && matchesSearch;
    });
  }, [incidents, filter, behaviorFilter, studentFilter, searchTerm]);

  // Carousel navigation indices
  const currentReviewIndex = useMemo(() => {
    if (!selectedIncident) return -1;
    return filteredIncidents.findIndex((i) => i.id === selectedIncident.id);
  }, [selectedIncident, filteredIncidents]);

  const prevIncident =
    currentReviewIndex > 0 ? filteredIncidents[currentReviewIndex - 1] : null;
  const nextIncident =
    currentReviewIndex >= 0 && currentReviewIndex < filteredIncidents.length - 1
      ? filteredIncidents[currentReviewIndex + 1]
      : null;

  // Keyboard shortcut listener for rapid review navigation
  useEffect(() => {
    function handleKeyDown(e) {
      if (!selectedIncident) return;
      if (e.key === "Escape") closeReview();
      if (e.key === "ArrowLeft" && prevIncident) openReview(prevIncident);
      if (e.key === "ArrowRight" && nextIncident) openReview(nextIncident);
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selectedIncident, prevIncident, nextIncident]);

  // Aggregate Unique Tracked Students Count
  const uniqueStudents = useMemo(() => {
    const s = new Set();
    incidents.forEach((i) => {
      if (i.track_id !== null && i.track_id !== undefined) s.add(i.track_id);
    });
    return Array.from(s);
  }, [incidents]);

  // Exam Hall Integrity Index (0-100%)
  const integrityScore = useMemo(() => {
    if (incidents.length === 0) return 100;
    const reviewedCount = stats.reviewed || 0;
    const pendingCount = stats.pending || 0;
    const penalty = reviewedCount * 6 + pendingCount * 2.5;
    return Math.max(12, Math.min(100, Math.round(100 - penalty)));
  }, [incidents, stats]);

  // Incidents mapped to current playing video for timeline scrubber
  const currentVideoIncidents = useMemo(() => {
    if (!playingVideo) return [];
    return incidents.filter((i) => i.frame_number && i.frame_number > 0);
  }, [playingVideo, incidents]);

  return (
    <div className={`app-shell ${isDark ? "theme-dark" : "theme-light"}`}>
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <ShieldAlert size={28} />
          </div>
          <div className="brand-text">
            <h2>ExamGuard</h2>
            <div className="brand-sub">
              <span className="live-pill">PROCTORING AI</span>
              <span>v2.2 PRO</span>
            </div>
          </div>
        </div>

        <div className="sidebar-section-title">COMMAND CENTER</div>

        <nav className="nav-menu">
          <button
            type="button"
            className={`nav-item ${activePage === "dashboard" ? "active" : ""}`}
            onClick={() => setActivePage("dashboard")}
          >
            <LayoutDashboard size={19} />
            <span>Dashboard</span>
          </button>

          <button
            type="button"
            className={`nav-item ${activePage === "upload" ? "active" : ""}`}
            onClick={() => setActivePage("upload")}
          >
            <Camera size={19} />
            <span>Live Cam &amp; Video</span>
            {liveStatus.is_running && <span className="nav-pulse" />}
            {activeJob.is_running && <span className="nav-pulse" />}
          </button>

          <button
            type="button"
            className={`nav-item ${activePage === "review" ? "active" : ""}`}
            onClick={() => setActivePage("review")}
          >
            <AlertTriangle size={19} />
            <span>Incident Evidence</span>
            {stats.pending > 0 && (
              <span className="nav-count nav-count-pending">{stats.pending}</span>
            )}
          </button>

          <button
            type="button"
            className={`nav-item ${activePage === "students" ? "active" : ""}`}
            onClick={() => setActivePage("students")}
          >
            <Users size={19} />
            <span>Student Roster</span>
            <span className="nav-count">{uniqueStudents.length}</span>
          </button>

          <button
            type="button"
            className={`nav-item ${activePage === "videos" ? "active" : ""}`}
            onClick={() => setActivePage("videos")}
          >
            <Film size={19} />
            <span>Annotated Video</span>
          </button>

          <button
            type="button"
            className={`nav-item ${activePage === "settings" ? "active" : ""}`}
            onClick={() => setActivePage("settings")}
          >
            <Settings size={19} />
            <span>Vision Models &amp; AI</span>
          </button>
        </nav>

        {/* Quick System Summary in Sidebar */}
        <div className="sidebar-system-box">
          <div className="system-box-header">
            <span className="status-dot pulse-green" />
            <strong>AI Engine Active</strong>
          </div>
          <p>YOLOv8 + ByteTrack + Pose</p>
          <div className="system-meta-row">
            <span>Threats Flagged:</span> <strong>{stats.total_incidents}</strong>
          </div>
          <div className="system-meta-row">
            <span>Integrity Rating:</span> <strong>{integrityScore}%</strong>
          </div>
          {liveStatus.is_running && (
            <div className="system-meta-row text-green">
              <span>Webcam Live:</span> <strong>{liveStatus.fps} FPS</strong>
            </div>
          )}
        </div>

        <div className="sidebar-footer">
          <div className="status-dot" />
          <div className="footer-details">
            <strong>FastAPI Microservice</strong>
            <p>127.0.0.1:8000</p>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        {/* Top Navigation Bar */}
        <header className="topbar">
          <div className="topbar-titles">
            <div className="breadcrumb">
              <span>SECURITY COMMAND</span>
              <ChevronRight size={14} />
              <span className="breadcrumb-active">{activePage.toUpperCase()}</span>
            </div>
            <h1>
              {activePage === "dashboard" && "Exam Security & Integrity Dashboard"}
              {activePage === "upload" && "Live Webcam & Video Ingestion Center"}
              {activePage === "review" && "Forensic Incident Review & Evidence Vault"}
              {activePage === "students" && "Tracked Student Roster & Risk Scoring"}
              {activePage === "videos" && "Annotated Output Video Inspection"}
              {activePage === "settings" && "Vision Pipeline & Neural Architecture"}
            </h1>
            <p className="subtitle">
              {activePage === "dashboard" &&
                "Live multi-student tracking, behavioral peeking heuristics, and automated evidence auditing."}
              {activePage === "upload" &&
                "Toggle between real-time laptop webcam proctoring or pre-recorded exam video inference."}
              {activePage === "review" &&
                "Forensic inspection with color-coded bounding boxes and jump-to-video playback."}
              {activePage === "students" &&
                "Comprehensive student registry with per-student infractions, threat levels, and disciplinary dossier export."}
              {activePage === "videos" &&
                "Inspect rendered recordings with real-time green/red boxes and click-to-seek evidence markers."}
              {activePage === "settings" &&
                "Inspect model architectures, keypoint detection thresholds, and neural network diagnostics."}
            </p>
          </div>

          <div className="topbar-actions">
            {/* Audio Alert Toggle */}
            <button
              type="button"
              className={`icon-btn ${soundEnabled ? "icon-btn-active" : ""}`}
              onClick={() => {
                setSoundEnabled(!soundEnabled);
                if (!soundEnabled) playSecurityChime();
              }}
              title={soundEnabled ? "Audio alerts enabled" : "Audio alerts muted"}
            >
              {soundEnabled ? <Volume2 size={18} /> : <VolumeX size={18} />}
            </button>

            {/* Dark / Light Mode Toggle */}
            <button
              type="button"
              className="icon-btn"
              onClick={toggleTheme}
              title={isDark ? "Switch to Light Theme" : "Switch to Dark Theme"}
            >
              {isDark ? <Sun size={18} /> : <Moon size={18} />}
            </button>

            {/* Official Disciplinary Dossier Button */}
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => {
                if (incidents.length > 0) {
                  setDossierData({ incident: incidents[0], student: null });
                } else {
                  setError("No incidents available to generate report.");
                }
              }}
              title="Generate Official Disciplinary Report"
            >
              <FileText size={15} />
              <span>Official Dossier</span>
            </button>

            {/* Export CSV Button */}
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={exportCSVReport}
              title="Download Incident Audit Log"
            >
              <Download size={15} />
              <span>Export CSV</span>
            </button>

            {/* Refresh Data */}
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => loadData(true)}
              disabled={loading}
            >
              <RefreshCw size={15} className={loading ? "spin" : ""} />
              <span>Refresh</span>
            </button>

            {/* Quick Live Cam / Upload CTA */}
            {activePage !== "upload" && (
              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={() => setActivePage("upload")}
              >
                <Camera size={15} />
                <span>Live Cam &amp; Video</span>
              </button>
            )}
          </div>
        </header>

        {/* Global Notifications */}
        {error && (
          <div className="alert-banner alert-danger">
            <AlertCircle size={18} />
            <span>{error}</span>
            <button className="banner-dismiss" onClick={() => setError("")}>
              &times;
            </button>
          </div>
        )}
        {success && (
          <div className="alert-banner alert-success">
            <CheckCircle2 size={18} />
            <span>{success}</span>
            <button className="banner-dismiss" onClick={() => setSuccess("")}>
              &times;
            </button>
          </div>
        )}

        {/* ============================================================== */}
        {/* 1. DASHBOARD OVERVIEW PAGE                                    */}
        {/* ============================================================== */}
        {activePage === "dashboard" && (
          <div className="page-section animate-fade">
            {/* Real-time Status Strip */}
            <div className="proctor-status-strip">
              <div className="strip-item">
                <span className="strip-indicator online" />
                <span>
                  YOLOv8 Detection: <strong>Online (640px)</strong>
                </span>
              </div>
              <div className="strip-item">
                <span className="strip-indicator online" />
                <span>
                  Pose Estimation: <strong>Online (17 Keypoints)</strong>
                </span>
              </div>
              <div className="strip-item">
                <span className="strip-indicator online" />
                <span>
                  ByteTrack Multi-Student: <strong>Active</strong>
                </span>
              </div>
              <div className="strip-item">
                <span className="strip-indicator online" />
                <span>
                  Laptop Webcam:{" "}
                  <strong>{liveStatus.is_running ? "Streaming Live" : "Standby"}</strong>
                </span>
              </div>
            </div>

            {/* Executive Exam Hall Integrity Gauge */}
            <div className="room-integrity-widget">
              <div className="gauge-col">
                <div className="circular-meter">
                  <svg className="meter-svg" viewBox="0 0 100 100">
                    <circle className="meter-bg" cx="50" cy="50" r="40" />
                    <circle
                      className="meter-bar"
                      cx="50"
                      cy="50"
                      r="40"
                      strokeDasharray={251.2}
                      strokeDashoffset={
                        251.2 - (251.2 * integrityScore) / 100
                      }
                      style={{
                        stroke:
                          integrityScore > 80
                            ? "var(--color-success)"
                            : integrityScore > 60
                            ? "var(--color-warning)"
                            : "var(--color-danger)",
                      }}
                    />
                  </svg>
                  <div className="meter-center">
                    <span className="meter-val">{integrityScore}%</span>
                    <span className="meter-label">INTEGRITY</span>
                  </div>
                </div>
              </div>

              <div className="integrity-info-col">
                <div className="integrity-status-pill-row">
                  <span
                    className={`status-chip ${
                      integrityScore > 80
                        ? "chip-success"
                        : integrityScore > 60
                        ? "chip-warning"
                        : "chip-danger"
                    }`}
                  >
                    {integrityScore > 80
                      ? "HIGH ACADEMIC INTEGRITY"
                      : integrityScore > 60
                      ? "SUSPICIOUS ACTIVITY DETECTED"
                      : "CRITICAL MISCONDUCT DETECTED"}
                  </span>
                  <span className="chip-muted">
                    Surveillance Engine: YOLOv8-ByteTrack + Pose
                  </span>
                </div>

                <h3>Automated Exam Hall Vigilance Assessment</h3>
                <p>
                  Continuous neural evaluation tracking lateral head tilt, ear-to-ear asymmetry, peer test glance duration, and unauthorized physical devices.
                </p>

                <div className="integrity-metrics-strip">
                  <div className="int-metric">
                    <span>TRACKED STUDENTS:</span>
                    <strong>{uniqueStudents.length} Monitored</strong>
                  </div>
                  <div className="int-metric">
                    <span>CONFIRMED CHEATING:</span>
                    <strong className="text-danger">
                      {stats.reviewed} Incidents
                    </strong>
                  </div>
                  <div className="int-metric">
                    <span>PENDING VERIFICATION:</span>
                    <strong className="text-amber">
                      {stats.pending} Suspect Flags
                    </strong>
                  </div>
                  <div className="int-metric">
                    <span>LIVE WEBCAM:</span>
                    <strong className={liveStatus.is_running ? "text-green" : "text-muted"}>
                      {liveStatus.is_running ? "Active" : "Standby"}
                    </strong>
                  </div>
                </div>
              </div>
            </div>

            {/* Stats Cards */}
            <section className="stats-grid">
              <div className="stat-card stat-total">
                <div className="stat-header">
                  <span className="stat-label">TOTAL THREATS FLAGGED</span>
                  <div className="stat-icon icon-blue">
                    <Activity size={22} />
                  </div>
                </div>
                <p className="stat-value">{stats.total_incidents}</p>
                <span className="stat-hint">Across all exam recordings</span>
              </div>

              <div className="stat-card stat-pending">
                <div className="stat-header">
                  <span className="stat-label">PENDING PROCTOR REVIEW</span>
                  <div className="stat-icon icon-amber">
                    <Clock3 size={22} />
                  </div>
                </div>
                <p className="stat-value">{stats.pending}</p>
                <span className="stat-hint text-amber">
                  Requires human verification
                </span>
              </div>

              <div className="stat-card stat-reviewed">
                <div className="stat-header">
                  <span className="stat-label">CONFIRMED MISCONDUCT</span>
                  <div className="stat-icon icon-green">
                    <CheckCircle2 size={22} />
                  </div>
                </div>
                <p className="stat-value">{stats.reviewed}</p>
                <span className="stat-hint text-green">
                  Verified academic cheating
                </span>
              </div>

              <div className="stat-card stat-dismissed">
                <div className="stat-header">
                  <span className="stat-label">FALSE ALARMS / DISMISSED</span>
                  <div className="stat-icon icon-red">
                    <XCircle size={22} />
                  </div>
                </div>
                <p className="stat-value">{stats.dismissed}</p>
                <span className="stat-hint text-muted">Audited &amp; exonerated</span>
              </div>
            </section>

            {/* Active AI Job Banner if running */}
            {activeJob.is_running && (
              <div
                className="active-job-spotlight"
                onClick={() => setActivePage("upload")}
              >
                <div className="spotlight-left">
                  <span className="badge badge-amber pulse">
                    INFERENCE IN PROGRESS
                  </span>
                  <h3>Analyzing: {activeJob.source_video}</h3>
                  <p>
                    Processing frame {activeJob.processed_frames} of{" "}
                    {activeJob.total_frames} ({activeJob.fps} FPS) &bull;{" "}
                    {activeJob.incident_count} threats detected
                  </p>
                </div>
                <div className="spotlight-right">
                  <span className="spotlight-pct">
                    {activeJob.total_frames > 0
                      ? Math.round(
                          (activeJob.processed_frames / activeJob.total_frames) *
                            100
                        )
                      : 0}
                    %
                  </span>
                  <button className="btn btn-primary btn-sm">
                    View Live HUD &rarr;
                  </button>
                </div>
              </div>
            )}

            {/* Visual Analytics Charts */}
            <DashboardCharts
              incidents={incidents}
              stats={stats}
              isDark={isDark}
            />

            {/* Recent Incidents Panel with One-Click Video Jump */}
            <section className="panel-card mt-6">
              <div className="panel-header">
                <div>
                  <span className="section-eyebrow">
                    <AlertTriangle size={13} />
                    LIVE SURVEILLANCE FEED
                  </span>
                  <h3>Recent Flagged Cheating Incidents</h3>
                  <p>Latest automated detections requiring human confirmation. Click "Seek Video" to jump directly to the exact moment.</p>
                </div>
                <div className="panel-header-actions">
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => setActivePage("review")}
                  >
                    View All Incidents ({incidents.length}) &rarr;
                  </button>
                </div>
              </div>

              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>EVIDENCE</th>
                      <th>STUDENT</th>
                      <th>BEHAVIOR DETECTED</th>
                      <th>SEVERITY</th>
                      <th>CONFIDENCE</th>
                      <th>TIMESTAMP</th>
                      <th>STATUS</th>
                      <th>ACTION</th>
                    </tr>
                  </thead>
                  <tbody>
                    {incidents.slice(0, 7).map((item) => {
                      const sev = getSeverity(item.event_type, item.confidence);
                      return (
                        <tr key={item.id}>
                          <td>
                            <div
                              className="table-thumb-container"
                              onClick={() => openReview(item)}
                            >
                              <img
                                src={`${API_URL}/api/incidents/${item.id}/image`}
                                alt="evidence"
                                className="table-thumb"
                                onError={(e) => {
                                  e.target.style.display = "none";
                                }}
                              />
                              <Eye size={14} className="thumb-hover-icon" />
                            </div>
                          </td>
                          <td>
                            <button
                              className="student-pill"
                              onClick={() => {
                                setStudentFilter(item.track_id);
                                setActivePage("review");
                              }}
                              title="Filter all incidents for this student"
                            >
                              <Users size={12} />
                              Student #{item.track_id ?? "?"}
                            </button>
                          </td>
                          <td>
                            <strong className="event-name-text">
                              {formatEventType(item.event_type)}
                            </strong>
                          </td>
                          <td>
                            <span className={`severity-tag ${sev.class}`}>
                              {sev.label}
                            </span>
                          </td>
                          <td>
                            <span className="conf-pill">
                              {Math.round((item.confidence || 0) * 100)}%
                            </span>
                          </td>
                          <td className="text-muted text-sm">
                            {formatDate(item.timestamp)}
                          </td>
                          <td>
                            <span
                              className={`status-badge status-${item.review_status}`}
                            >
                              {STATUS_LABELS[item.review_status] ||
                                item.review_status}
                            </span>
                          </td>
                          <td>
                            <div className="action-button-cell">
                              <button
                                className="btn btn-secondary btn-xs"
                                onClick={() => openReview(item)}
                                title="Inspect Evidence Details"
                              >
                                <Eye size={13} />
                                <span>Inspect</span>
                              </button>
                              <button
                                className="btn btn-primary btn-xs"
                                onClick={() => jumpToIncidentVideo(item)}
                                title="Jump to this exact frame in the video"
                              >
                                <Play size={12} />
                                <span>Seek Video</span>
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                    {incidents.length === 0 && (
                      <tr>
                        <td colSpan="8" className="text-center py-8 text-muted">
                          No incidents recorded yet. Start the live camera or upload an exam video.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        )}

        {/* ============================================================== */}
        {/* 2. LIVE CAMERA & VIDEO INGESTION PAGE (2 INGESTION MODES)      */}
        {/* ============================================================== */}
        {activePage === "upload" && (
          <div className="page-section animate-fade">
            {/* Top Ingestion Mode Switcher */}
            <div className="ingest-mode-selector-card">
              <div className="mode-tabs-wrap">
                <button
                  type="button"
                  className={`mode-tab-btn ${ingestMode === "live" ? "active" : ""}`}
                  onClick={() => setIngestMode("live")}
                >
                  <Camera size={18} />
                  <span>Option A: Live Laptop Webcam (تشغيل كاميرا اللاب لايف)</span>
                  {liveStatus.is_running && <span className="tab-live-pulse" />}
                </button>

                <button
                  type="button"
                  className={`mode-tab-btn ${ingestMode === "upload" ? "active" : ""}`}
                  onClick={() => setIngestMode("upload")}
                >
                  <UploadCloud size={18} />
                  <span>Option B: Upload Exam Video (رفع فيديو مسجل)</span>
                  {activeJob.is_running && <span className="tab-live-pulse" />}
                </button>
              </div>
            </div>

            {/* ---------------- OPTION A: LIVE WEBCAM CONSOLE ---------------- */}
            {ingestMode === "live" && (
              <div className="live-webcam-workspace animate-fade">
                <div className="webcam-grid">
                  {/* Left: Live MJPEG Video Stream Viewport */}
                  <div className="panel-card webcam-stream-panel">
                    <div className="panel-header">
                      <div>
                        <span className="section-eyebrow">
                          <Radio size={13} className="pulse text-danger" />
                          REAL-TIME SENSING
                        </span>
                        <h3>Live Camera Feed with AI Bounding Boxes</h3>
                        <p>
                          🟢 Green Box = Normal Student &bull; 🔴 Red Box = Cheating Suspect (Peeking / Phone).
                        </p>
                      </div>
                      <span className={`status-badge ${liveStatus.is_running ? "status-reviewed" : "status-dismissed"}`}>
                        {liveStatus.is_running ? "STREAMING LIVE" : "STANDBY"}
                      </span>
                    </div>

                    <div className="webcam-viewport-box">
                      {liveStatus.is_running ? (
                        <div className="live-stream-container">
                          <img
                            src={`${API_URL}/api/live-stream/feed`}
                            alt="Live Camera Feed"
                            className="live-stream-viewport"
                          />
                          <div className="live-stream-hud-overlay">
                            <span className="hud-badge hud-rec">
                              <Radio size={12} className="pulse" /> LIVE WEBCAM (Camera 0)
                            </span>
                            <span className="hud-badge hud-fps">
                              {liveStatus.fps} FPS
                            </span>
                          </div>
                        </div>
                      ) : (
                        <div className="webcam-offline-placeholder">
                          <Camera size={64} className="cam-placeholder-icon" />
                          <h4>Laptop Camera is currently in Standby</h4>
                          <p>
                            Click <strong>"Start Live Camera Proctoring"</strong> to activate real-time student tracking, pose peeking detection, and automatic cheating snapshot capture.
                          </p>
                          <button
                            className="btn btn-success btn-lg mt-4"
                            onClick={handleStartLiveCam}
                          >
                            <Camera size={18} />
                            <span>Start Live Camera Proctoring</span>
                          </button>
                        </div>
                      )}
                    </div>

                    {/* Live Telemetry Strip below camera */}
                    {liveStatus.is_running && (
                      <div className="webcam-live-hud-strip">
                        <div className="hud-metric">
                          <span>FPS SPEED:</span>
                          <strong>{liveStatus.fps} Frames/sec</strong>
                        </div>
                        <div className="hud-metric">
                          <span>STUDENTS MONITORED:</span>
                          <strong>{liveStatus.people_count} Student(s)</strong>
                        </div>
                        <div className="hud-metric">
                          <span>LIVE CHEATING ALERTS:</span>
                          <strong className={liveStatus.incident_count > 0 ? "text-danger" : "text-green"}>
                            {liveStatus.incident_count} Flagged
                          </strong>
                        </div>
                        <div className="hud-metric">
                          <span>STATUS:</span>
                          <strong className={liveStatus.incident_count > 0 ? "text-danger" : "text-green"}>
                            {liveStatus.last_incident || "All Clear"}
                          </strong>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Right: Camera Controls & Live Diagnostics */}
                  <div className="panel-card webcam-controls-panel">
                    <div className="panel-header">
                      <div>
                        <span className="section-eyebrow">
                          <Sliders size={13} />
                          CONFIGURATION
                        </span>
                        <h3>Webcam Proctor Controls</h3>
                        <p>Adjust neural sensitivity and manage recording session.</p>
                      </div>
                    </div>

                    <div className="webcam-controls-body">
                      {/* Active Status Banner */}
                      <div className={`webcam-status-card ${liveStatus.is_running ? "card-online" : "card-offline"}`}>
                        <div className="status-card-header">
                          <span className={`status-dot ${liveStatus.is_running ? "pulse-green" : ""}`} />
                          <strong>
                            {liveStatus.is_running
                              ? "Live Session Running (Laptop Webcam #0)"
                              : "Webcam Standby (Ready to Test)"}
                          </strong>
                        </div>
                        <p>
                          {liveStatus.is_running
                            ? "Engine is analyzing your face, head angle, phone, and books in real-time."
                            : "Test by looking away towards a neighbor or holding your phone to see red bounding boxes!"}
                        </p>
                      </div>

                      {/* Main Action Buttons */}
                      <div className="webcam-action-buttons">
                        {!liveStatus.is_running ? (
                          <button
                            className="btn btn-success btn-lg"
                            onClick={handleStartLiveCam}
                          >
                            <Camera size={19} />
                            <span>Start Live Camera Proctoring</span>
                          </button>
                        ) : (
                          <button
                            className="btn btn-danger btn-lg"
                            onClick={handleStopLiveCam}
                          >
                            <Square size={19} />
                            <span>Stop Live Camera Session</span>
                          </button>
                        )}
                      </div>

                      {/* Sensitivity Slider */}
                      <div className="control-field mt-4">
                        <div className="control-label-row">
                          <label>
                            <Sliders size={15} />
                            AI Detection Sensitivity
                          </label>
                          <span className="threshold-val">
                            {Math.round(confThreshold * 100)}%
                          </span>
                        </div>
                        <input
                          type="range"
                          min="0.05"
                          max="0.45"
                          step="0.02"
                          value={confThreshold}
                          onChange={(e) =>
                            setConfThreshold(parseFloat(e.target.value))
                          }
                        />
                        <div className="slider-hints">
                          <span>High Sensitivity (0.05)</span>
                          <span>Balanced (0.15)</span>
                          <span>Strict (0.45)</span>
                        </div>
                      </div>

                      {/* Live Detection Rules Callout */}
                      <div className="info-callout mt-4">
                        <ShieldCheck size={20} className="callout-icon" />
                        <div>
                          <strong>Live Webcam Test Guide:</strong>
                          <ul>
                            <li>
                              <strong>Normal behavior:</strong> Look forward at screen ➔ 🟢 Green box.
                            </li>
                            <li>
                              <strong>Peeking behavior:</strong> Turn head left/right for &gt;1 sec ➔ 🔴 Red box &amp; snapshot saved!
                            </li>
                            <li>
                              <strong>Unauthorized object:</strong> Hold a phone or notebook ➔ 🔴 Red box &amp; alert chime!
                            </li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* ---------------- OPTION B: UPLOAD & SAMPLE VIDEOS ---------------- */}
            {ingestMode === "upload" && (
              <div className="upload-workspace animate-fade">
                {/* Live Progress Bar if active */}
                {activeJob.is_running && (
                  <div className="processing-progress-card">
                    <div className="progress-card-header">
                      <div>
                        <span className="badge badge-amber pulse">
                          AI PROCESSING LIVE
                        </span>
                        <h3>Analyzing: {activeJob.source_video}</h3>
                      </div>
                      <div className="progress-pct">
                        {activeJob.total_frames > 0
                          ? Math.round(
                              (activeJob.processed_frames / activeJob.total_frames) *
                                100
                            )
                          : 0}
                        %
                      </div>
                    </div>

                    <div className="progress-bar-bg">
                      <div
                        className="progress-bar-fill"
                        style={{
                          width: `${
                            activeJob.total_frames > 0
                              ? Math.min(
                                  100,
                                  Math.round(
                                    (activeJob.processed_frames /
                                      activeJob.total_frames) *
                                      100
                                  )
                                )
                              : 0
                          }%`,
                        }}
                      />
                    </div>

                    <div className="progress-stats-row">
                      <div className="progress-metric">
                        <span>Frames Processed:</span>
                        <strong>
                          {activeJob.processed_frames} / {activeJob.total_frames}
                        </strong>
                      </div>
                      <div className="progress-metric">
                        <span>Inference Speed:</span>
                        <strong>{activeJob.fps} FPS</strong>
                      </div>
                      <div className="progress-metric">
                        <span>Students Tracked:</span>
                        <strong>{activeJob.people_count} Students</strong>
                      </div>
                      <div className="progress-metric metric-danger">
                        <span>Threats Flagged:</span>
                        <strong>{activeJob.incident_count} Incidents</strong>
                      </div>
                    </div>
                  </div>
                )}

                <div className="upload-grid">
                  {/* Upload Card */}
                  <div className="panel-card">
                    <div className="panel-header">
                      <div>
                        <span className="section-eyebrow">
                          <UploadCloud size={13} />
                          UPLOAD FILE
                        </span>
                        <h3>1. Ingest Examination Video</h3>
                        <p>Select or drag exam camera recordings (MP4, AVI, MOV).</p>
                      </div>
                      <span className="panel-tag">Source Ingestion</span>
                    </div>

                    <div
                      className="dropzone-area"
                      onClick={() => fileInputRef.current?.click()}
                    >
                      <input
                        type="file"
                        ref={fileInputRef}
                        accept="video/mp4,video/avi,video/quicktime"
                        style={{ display: "none" }}
                        onChange={handleFileUpload}
                      />
                      <div className="dropzone-icon-box">
                        <UploadCloud size={40} />
                      </div>
                      <h4>Click to Browse or Drag &amp; Drop Video</h4>
                      <p>Supports MP4, AVI, MOV container formats (H.264 / MPEG-4)</p>
                      {uploadStatus && (
                        <div className="upload-status-chip">{uploadStatus}</div>
                      )}
                    </div>

                    {/* Selected File Details */}
                    {selectedVideoPath && (
                      <div className="selected-video-bar">
                        <div className="video-icon-badge">
                          <Film size={22} />
                        </div>
                        <div className="video-meta">
                          <strong>TARGET VIDEO QUEUED:</strong>
                          <p>{selectedVideoName || selectedVideoPath}</p>
                        </div>
                      </div>
                    )}

                    {/* Parameters & Start Button */}
                    <div className="processing-controls">
                      <div className="control-field">
                        <div className="control-label-row">
                          <label>
                            <Sliders size={15} />
                            AI Detection Sensitivity
                          </label>
                          <span className="threshold-val">
                            {Math.round(confThreshold * 100)}%
                          </span>
                        </div>
                        <input
                          type="range"
                          min="0.05"
                          max="0.45"
                          step="0.02"
                          value={confThreshold}
                          onChange={(e) =>
                            setConfThreshold(parseFloat(e.target.value))
                          }
                        />
                        <div className="slider-hints">
                          <span>High Sensitivity (0.05)</span>
                          <span>Balanced (0.15)</span>
                          <span>Strict (0.45)</span>
                        </div>
                      </div>

                      <button
                        className="btn btn-primary btn-lg"
                        onClick={() => handleStartProcessing()}
                        disabled={
                          activeJob.is_running || isUploading || !selectedVideoPath
                        }
                      >
                        <Play size={18} />
                        <span>
                          {activeJob.is_running
                            ? "Inference Running..."
                            : "Start Automated Cheating Analysis"}
                        </span>
                      </button>
                    </div>
                  </div>

                  {/* Sample Test Videos Card */}
                  <div className="panel-card">
                    <div className="panel-header">
                      <div>
                        <span className="section-eyebrow">
                          <Film size={13} />
                          STAGE 2: PRESET LIBRARY
                        </span>
                        <h3>2. Project Test Footage Library</h3>
                        <p>Verified exam videos available on the host machine.</p>
                      </div>
                      <span className="panel-tag">Test Samples</span>
                    </div>

                    <div className="sample-videos-list">
                      {sampleVideos.map((vid) => (
                        <div
                          key={vid.path}
                          className={`sample-video-item ${
                            selectedVideoPath === vid.path ? "selected" : ""
                          }`}
                          onClick={() => {
                            setSelectedVideoPath(vid.path);
                            setSelectedVideoName(vid.filename);
                          }}
                        >
                          <div className="sample-icon">
                            <Film size={20} />
                          </div>
                          <div className="sample-info">
                            <strong>{vid.filename}</strong>
                            <p>{vid.size_mb} MB &bull; Ready for inference</p>
                          </div>
                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedVideoPath(vid.path);
                              setSelectedVideoName(vid.filename);
                              handleStartProcessing(vid.path);
                            }}
                            disabled={activeJob.is_running}
                          >
                            <Play size={13} />
                            <span>Run</span>
                          </button>
                        </div>
                      ))}

                      {sampleVideos.length === 0 && (
                        <div className="text-muted py-6 text-center">
                          No sample videos discovered in directory.
                        </div>
                      )}
                    </div>

                    <div className="info-callout">
                      <ShieldCheck size={20} className="callout-icon" />
                      <div>
                        <strong>Automated AI Protection Protocol:</strong>
                        <ul>
                          <li>
                            <strong>Student Tracking:</strong> ByteTrack maintains
                            persistent student identities across occlusions.
                          </li>
                          <li>
                            <strong>Peeking Detection:</strong> Pose model tracks head yaw
                            and ear asymmetry when looking at neighbors.
                          </li>
                          <li>
                            <strong>Unauthorized Items:</strong> Detects cell phones,
                            laptops, and hidden notes/books.
                          </li>
                          <li>
                            <strong>Color Coding:</strong> 🟢 Green for normal
                            students, 🔴 Red for cheating events.
                          </li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Video Processing Jobs History */}
                <div className="panel-card mt-6">
                  <div className="panel-header">
                    <div>
                      <span className="section-eyebrow">
                        <Clock3 size={13} />
                        AUDIT REGISTRY
                      </span>
                      <h3>Processing Job History</h3>
                      <p>Audit trail of all analyzed video sessions.</p>
                    </div>
                  </div>

                  <div className="table-wrapper">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>JOB ID</th>
                          <th>SOURCE VIDEO</th>
                          <th>FRAMES</th>
                          <th>FPS</th>
                          <th>THREATS FLAGGED</th>
                          <th>STUDENTS</th>
                          <th>STATUS</th>
                          <th>PLAYBACK</th>
                        </tr>
                      </thead>
                      <tbody>
                        {jobs.map((job) => (
                          <tr key={job.job_id}>
                            <td>
                              <code className="code-badge">
                                {job.job_id.slice(-14)}
                              </code>
                            </td>
                            <td>
                              <strong>{job.source_video}</strong>
                            </td>
                            <td>
                              {job.processed_frames} / {job.total_frames}
                            </td>
                            <td>{Math.round(job.fps || 0)}</td>
                            <td>
                              <span className="badge badge-danger">
                                {job.incident_count} Threats
                              </span>
                            </td>
                            <td>{job.people_count}</td>
                            <td>
                              <span
                                className={`status-badge status-${job.status}`}
                              >
                                {job.status}
                              </span>
                            </td>
                            <td>
                              {job.output_video ? (
                                <button
                                  className="btn btn-secondary btn-xs"
                                  onClick={() => {
                                    const fname = job.output_video
                                      .split("\\")
                                      .pop()
                                      .split("/")
                                      .pop();
                                    setPlayingVideo(fname);
                                    setActivePage("videos");
                                  }}
                                >
                                  <Play size={12} />
                                  <span>Play Video</span>
                                </button>
                              ) : (
                                <span className="text-muted">—</span>
                              )}
                            </td>
                          </tr>
                        ))}
                        {jobs.length === 0 && (
                          <tr>
                            <td colSpan="8" className="text-center py-6 text-muted">
                              No previous processing sessions logged.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ============================================================== */}
        {/* 3. INCIDENT REVIEW & EVIDENCE PAGE                             */}
        {/* ============================================================== */}
        {activePage === "review" && (
          <div className="page-section animate-fade">
            {/* Filter & Search Bar */}
            <div className="filter-panel">
              <div className="search-row">
                <div className="search-box">
                  <Search size={16} />
                  <input
                    type="text"
                    placeholder="Search by student ID, incident type, notes..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                  {searchTerm && (
                    <button
                      className="clear-search"
                      onClick={() => setSearchTerm("")}
                    >
                      &times;
                    </button>
                  )}
                </div>

                {studentFilter !== null && (
                  <div className="student-filter-chip">
                    <span>Filtering Student #{studentFilter}</span>
                    <button onClick={() => setStudentFilter(null)}>&times;</button>
                  </div>
                )}
              </div>

              {/* Status Filters */}
              <div className="filter-row">
                <div className="filter-group">
                  <span className="filter-label">
                    <Filter size={13} /> Status:
                  </span>
                  <button
                    className={`filter-btn ${filter === "all" ? "active" : ""}`}
                    onClick={() => setFilter("all")}
                  >
                    All ({incidents.length})
                  </button>
                  <button
                    className={`filter-btn ${
                      filter === "pending" ? "active" : ""
                    }`}
                    onClick={() => setFilter("pending")}
                  >
                    Pending ({stats.pending})
                  </button>
                  <button
                    className={`filter-btn ${
                      filter === "reviewed" ? "active" : ""
                    }`}
                    onClick={() => setFilter("reviewed")}
                  >
                    Confirmed ({stats.reviewed})
                  </button>
                  <button
                    className={`filter-btn ${
                      filter === "dismissed" ? "active" : ""
                    }`}
                    onClick={() => setFilter("dismissed")}
                  >
                    Dismissed ({stats.dismissed})
                  </button>
                </div>

                {/* Behavior Filters */}
                <div className="behavior-filter-group">
                  <span className="filter-label">
                    <Layers size={13} /> Mode:
                  </span>
                  <button
                    className={`pill-btn ${
                      behaviorFilter === "all" ? "active" : ""
                    }`}
                    onClick={() => setBehaviorFilter("all")}
                  >
                    All Modes
                  </button>
                  <button
                    className={`pill-btn ${
                      behaviorFilter === "peeking" ? "active" : ""
                    }`}
                    onClick={() => setBehaviorFilter("peeking")}
                  >
                    👀 Peeking / Head Turn
                  </button>
                  <button
                    className={`pill-btn ${
                      behaviorFilter === "phone" ? "active" : ""
                    }`}
                    onClick={() => setBehaviorFilter("phone")}
                  >
                    📱 Mobile Phone
                  </button>
                  <button
                    className={`pill-btn ${
                      behaviorFilter === "laptop" ? "active" : ""
                    }`}
                    onClick={() => setBehaviorFilter("laptop")}
                  >
                    💻 Laptop
                  </button>
                  <button
                    className={`pill-btn ${
                      behaviorFilter === "book" ? "active" : ""
                    }`}
                    onClick={() => setBehaviorFilter("book")}
                  >
                    📖 Notes / Book
                  </button>
                </div>
              </div>
            </div>

            {/* Incidents Grid with Direct Jump Button */}
            <div className="evidence-grid">
              {filteredIncidents.map((item) => {
                const sev = getSeverity(item.event_type, item.confidence);
                return (
                  <div
                    key={item.id}
                    className="evidence-card"
                    onClick={() => openReview(item)}
                  >
                    <div className="evidence-img-container">
                      <img
                        src={`${API_URL}/api/incidents/${item.id}/image`}
                        alt="Incident Snapshot"
                        className="evidence-img"
                        loading="lazy"
                      />
                      <span className={`severity-tag-overlay ${sev.class}`}>
                        {sev.label}
                      </span>
                      <span className="confidence-tag">
                        {Math.round((item.confidence || 0) * 100)}% Conf
                      </span>
                      <span className={`status-tag status-${item.review_status}`}>
                        {item.review_status}
                      </span>
                    </div>

                    <div className="evidence-body">
                      <div className="evidence-header-row">
                        <strong>Threat #{item.id}</strong>
                        <span className="badge badge-track">
                          Student #{item.track_id ?? "?"}
                        </span>
                      </div>

                      <h4 className="event-title">
                        {formatEventType(item.event_type)}
                      </h4>
                      <p className="notes-excerpt">
                        {item.notes || "No notes logged."}
                      </p>

                      <div className="evidence-footer">
                        <span className="time-text">
                          <Clock3 size={12} />
                          {formatDate(item.timestamp)}
                        </span>
                        <div className="evidence-footer-actions">
                          <button
                            className="btn btn-secondary btn-xs"
                            onClick={(e) => {
                              e.stopPropagation();
                              openReview(item);
                            }}
                          >
                            Inspect
                          </button>
                          <button
                            className="btn btn-primary btn-xs"
                            onClick={(e) => {
                              e.stopPropagation();
                              jumpToIncidentVideo(item);
                            }}
                            title="Jump to this moment in video"
                          >
                            <Play size={11} />
                            <span>Watch</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}

              {filteredIncidents.length === 0 && (
                <div className="empty-evidence-box">
                  <ShieldAlert size={42} />
                  <h3>No Incidents Match Selected Filters</h3>
                  <p>Try resetting filters or analyze a new exam video.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* 4. TRACKED STUDENTS ROSTER PAGE                                */}
        {/* ============================================================== */}
        {activePage === "students" && (
          <StudentRoster
            incidents={incidents}
            onSelectStudent={(tid) => {
              setStudentFilter(tid);
              setActivePage("review");
            }}
            onGenerateReport={(studentObj) => {
              setDossierData({ incident: null, student: studentObj });
            }}
          />
        )}

        {/* ============================================================== */}
        {/* 5. ANNOTATED VIDEOS PLAYBACK PAGE WITH DIRECT JUMP SCRUBBER    */}
        {/* ============================================================== */}
        {activePage === "videos" && (
          <div className="page-section animate-fade">
            <div className="video-player-container panel-card">
              <div className="panel-header">
                <div>
                  <span className="section-eyebrow">
                    <Film size={13} />
                    COMPUTER VISION PLAYBACK
                  </span>
                  <h3>Annotated Output Video Inspection</h3>
                  <p>
                    Review real-time bounding box color coding (🟢 Green = Normal,
                    🔴 Red = Cheating Event). Click any incident marker below to seek immediately.
                  </p>
                </div>
                <span className="panel-tag">HTML5 Video Engine</span>
              </div>

              {/* Jump Target Banner */}
              {videoSeekTarget && (
                <div className="video-jump-banner animate-fade">
                  <div className="jump-banner-left">
                    <span className="badge badge-amber pulse">
                      <Target size={13} /> JUMPED TO THREAT #{videoSeekTarget.incidentId}
                    </span>
                    <strong>
                      Student #{videoSeekTarget.studentId ?? "?"}: {formatEventType(videoSeekTarget.eventType)}
                    </strong>
                    <span>
                      Frame: {videoSeekTarget.frame} &bull; Time: {Math.floor(videoSeekTarget.time / 60)}:
                      {Math.floor(videoSeekTarget.time % 60)
                        .toString()
                        .padStart(2, "0")}s
                    </span>
                  </div>
                  <button
                    className="btn btn-secondary btn-xs"
                    onClick={() => setVideoSeekTarget(null)}
                  >
                    &times; Dismiss Banner
                  </button>
                </div>
              )}

              {playingVideo ? (
                <div className="player-wrapper">
                  <video
                    ref={videoPlayerRef}
                    key={playingVideo}
                    controls
                    autoPlay
                    className="html5-video-player"
                    src={`${API_URL}/api/videos/${playingVideo}`}
                    onLoadedMetadata={() => {
                      if (videoSeekTarget && videoPlayerRef.current) {
                        videoPlayerRef.current.currentTime = videoSeekTarget.time;
                        videoPlayerRef.current.play().catch(() => {});
                      }
                    }}
                  >
                    Your browser does not support the video tag.
                  </video>
                  <div className="video-playing-title">
                    <Film size={18} className="text-blue" />
                    <span>
                      Now Playing: <strong>{playingVideo}</strong>
                    </span>
                  </div>

                  {/* Interactive Evidence Timeline Scrubber */}
                  {currentVideoIncidents.length > 0 && (
                    <div className="video-evidence-timeline mt-4">
                      <div className="timeline-header-row">
                        <span className="timeline-title">
                          <Target size={14} /> JUMP TO SUSPICIOUS MOMENTS ({currentVideoIncidents.length} CHEATING EVENTS):
                        </span>
                      </div>
                      <div className="timeline-markers-row">
                        {currentVideoIncidents.map((inc) => {
                          const estSec = (inc.frame_number || 0) / 25.0;
                          return (
                            <button
                              key={inc.id}
                              className={`timeline-marker-btn ${
                                videoSeekTarget?.incidentId === inc.id ? "active-marker" : ""
                              }`}
                              onClick={() => {
                                if (videoPlayerRef.current) {
                                  videoPlayerRef.current.currentTime = Math.max(0, estSec - 0.5);
                                  videoPlayerRef.current.play().catch(() => {});
                                }
                                setVideoSeekTarget({
                                  time: estSec,
                                  frame: inc.frame_number,
                                  incidentId: inc.id,
                                  studentId: inc.track_id,
                                  eventType: inc.event_type,
                                });
                              }}
                              title={`Jump to frame ${inc.frame_number} (${estSec.toFixed(1)}s)`}
                            >
                              <Play size={10} />
                              <span>#{inc.id} Student #{inc.track_id ?? "?"} ({Math.round(estSec)}s)</span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="player-placeholder">
                  <Film size={52} />
                  <h4>Select a video below to watch annotated playback</h4>
                  <p>
                    Processed exam videos display real-time green/red student bounding boxes.
                  </p>
                </div>
              )}

              {/* Processed videos list */}
              <div className="output-videos-archive mt-6">
                <h4>Available Processed Recordings</h4>
                <div className="output-cards-grid">
                  {jobs
                    .filter((j) => j.output_video)
                    .map((j) => {
                      const fname = j.output_video
                        .split("\\")
                        .pop()
                        .split("/")
                        .pop();
                      const isCurrent = playingVideo === fname;
                      return (
                        <div
                          key={j.job_id}
                          className={`output-card ${
                            isCurrent ? "active-card" : ""
                          }`}
                          onClick={() => setPlayingVideo(fname)}
                        >
                          <div className="output-card-icon">
                            <Play size={20} />
                          </div>
                          <div className="output-card-meta">
                            <strong>{fname}</strong>
                            <p>
                              {j.processed_frames} frames &bull;{" "}
                              {j.incident_count} threats flagged
                            </p>
                          </div>
                        </div>
                      );
                    })}

                  {jobs.filter((j) => j.output_video).length === 0 && (
                    <p className="text-muted">
                      No processed videos generated yet. Run a video from the
                      "Upload &amp; Analyze" tab.
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* 6. SYSTEM SETTINGS & MODELS PAGE                               */}
        {/* ============================================================== */}
        {activePage === "settings" && (
          <div className="page-section animate-fade">
            <div className="panel-card">
              <div className="panel-header">
                <div>
                  <span className="section-eyebrow">
                    <Cpu size={13} />
                    NEURAL ARCHITECTURE
                  </span>
                  <h3>AI Vision Models &amp; Hardware Status</h3>
                  <p>
                    Real-time environment information and inference pipeline status.
                  </p>
                </div>
                <span className="panel-tag">Architecture</span>
              </div>

              <div className="settings-grid">
                <div className="setting-stat-card">
                  <div className="stat-icon icon-blue">
                    <Cpu size={22} />
                  </div>
                  <div>
                    <strong>Detection Model</strong>
                    <p>YOLOv8 Nano (yolov8n.pt)</p>
                    <small>Classes: Person, Phone, Laptop, Book/Notes</small>
                  </div>
                </div>

                <div className="setting-stat-card">
                  <div className="stat-icon icon-purple">
                    <Eye size={22} />
                  </div>
                  <div>
                    <strong>Pose &amp; Peeking Model</strong>
                    <p>YOLOv8 Pose (yolov8n-pose.pt)</p>
                    <small>17 Body Keypoints &amp; Head Yaw Heuristics</small>
                  </div>
                </div>

                <div className="setting-stat-card">
                  <div className="stat-icon icon-amber">
                    <Sliders size={22} />
                  </div>
                  <div>
                    <strong>Tracking Algorithm</strong>
                    <p>ByteTrack (bytetrack.yaml)</p>
                    <small>Persistent multi-student tracking IDs</small>
                  </div>
                </div>

                <div className="setting-stat-card">
                  <div className="stat-icon icon-green">
                    <Database size={22} />
                  </div>
                  <div>
                    <strong>Database Engine</strong>
                    <p>SQLite (cheating_system.db)</p>
                    <small>Incidents &amp; Jobs Persistence</small>
                  </div>
                </div>
              </div>

              <div className="system-json-dump mt-6">
                <h4>System Diagnostic Information</h4>
                <pre>{JSON.stringify(systemInfo, null, 2)}</pre>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* ============================================================== */}
      {/* EVIDENCE DETAIL / PROCTOR REVIEW MODAL WITH ZOOM & NAV          */}
      {/* ============================================================== */}
      {selectedIncident && (
        <div className="modal-overlay" onClick={closeReview}>
          <div
            className="modal-card animate-scale"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="modal-header">
              <div>
                <span className="badge badge-amber">
                  INCIDENT EVIDENCE FORENSICS
                </span>
                <h3>
                  Incident #{selectedIncident.id} &bull; Student #
                  {selectedIncident.track_id ?? "N/A"}
                </h3>
              </div>

              <div className="modal-header-actions">
                <button
                  className="btn btn-primary btn-xs"
                  onClick={() => jumpToIncidentVideo(selectedIncident)}
                  title="Jump directly to this exact frame in video"
                >
                  <Play size={13} />
                  <span>Watch in Video</span>
                </button>
                <button
                  className="btn btn-secondary btn-xs"
                  onClick={() =>
                    setDossierData({
                      incident: selectedIncident,
                      student: null,
                    })
                  }
                  title="Generate Official Formal Dossier"
                >
                  <FileText size={13} />
                  <span>Dossier</span>
                </button>
                <button className="modal-close-btn" onClick={closeReview}>
                  &times;
                </button>
              </div>
            </div>

            {/* Quick Carousel Navigation & Zoom Magnifier Bar */}
            <div className="modal-toolbar-bar">
              <div className="modal-nav-group">
                <button
                  className="btn btn-secondary btn-xs"
                  onClick={() => prevIncident && openReview(prevIncident)}
                  disabled={!prevIncident}
                  title="Previous Incident (Left Arrow key)"
                >
                  <ChevronLeft size={14} />
                  <span>Prev Threat</span>
                </button>
                <span className="modal-carousel-counter">
                  {currentReviewIndex >= 0 ? currentReviewIndex + 1 : 1} of{" "}
                  {filteredIncidents.length}
                </span>
                <button
                  className="btn btn-secondary btn-xs"
                  onClick={() => nextIncident && openReview(nextIncident)}
                  disabled={!nextIncident}
                  title="Next Incident (Right Arrow key)"
                >
                  <span>Next Threat</span>
                  <ChevronRight size={14} />
                </button>
              </div>

              {/* Digital Zoom Magnifier */}
              <div className="modal-zoom-group">
                <span className="zoom-label">
                  <Eye size={12} /> Magnifier:
                </span>
                <button
                  className={`zoom-btn ${zoomLevel === 1 ? "active" : ""}`}
                  onClick={() => setZoomLevel(1)}
                >
                  1x
                </button>
                <button
                  className={`zoom-btn ${zoomLevel === 1.6 ? "active" : ""}`}
                  onClick={() => setZoomLevel(1.6)}
                >
                  1.6x
                </button>
                <button
                  className={`zoom-btn ${zoomLevel === 2.4 ? "active" : ""}`}
                  onClick={() => setZoomLevel(2.4)}
                >
                  2.4x
                </button>
              </div>
            </div>

            <div className="modal-body">
              {/* Evidence Screenshot with Zoom Container */}
              <div className="modal-evidence-preview">
                <div
                  className="screenshot-zoom-box"
                  style={{
                    overflow: zoomLevel > 1 ? "auto" : "hidden",
                    cursor: zoomLevel > 1 ? "grab" : "default",
                  }}
                >
                  <img
                    src={`${API_URL}/api/incidents/${selectedIncident.id}/image`}
                    alt="Evidence Frame"
                    className="modal-screenshot"
                    style={{
                      transform: `scale(${zoomLevel})`,
                      transformOrigin: "top center",
                      transition: "transform 0.2s ease-out",
                    }}
                  />
                </div>
                <div className="screenshot-caption">
                  Color protocol: 🟢 Green = Normal Students, 🔴 Red = Suspect.
                  {zoomLevel > 1 && (
                    <span className="zoom-hint">
                      {" "}
                      (Magnified {zoomLevel}x &bull; scroll or drag to inspect)
                    </span>
                  )}
                </div>
              </div>

              {/* Incident Details & Review Form */}
              <div className="modal-details-form">
                <div className="details-list">
                  <div>
                    <span>Detected Behavior:</span>
                    <strong>
                      {formatEventType(selectedIncident.event_type)}
                    </strong>
                  </div>
                  <div>
                    <span>AI Confidence:</span>
                    <strong>
                      {Math.round((selectedIncident.confidence || 0) * 100)}%
                    </strong>
                  </div>
                  <div>
                    <span>Threat Severity:</span>
                    <strong>
                      {
                        getSeverity(
                          selectedIncident.event_type,
                          selectedIncident.confidence
                        ).label
                      }
                    </strong>
                  </div>
                  <div>
                    <span>Timestamp:</span>
                    <strong>{formatDate(selectedIncident.timestamp)}</strong>
                  </div>
                  <div>
                    <span>Source Video:</span>
                    <strong>{selectedIncident.source_video || "—"}</strong>
                  </div>
                  <div>
                    <span>Frame Number:</span>
                    <strong>{selectedIncident.frame_number ?? "—"}</strong>
                  </div>
                </div>

                <div className="proctor-decision-section">
                  <label className="section-label">
                    Proctor Review Decision:
                  </label>
                  <div className="decision-buttons">
                    <button
                      type="button"
                      className={`btn ${
                        reviewStatus === "reviewed"
                          ? "btn-success"
                          : "btn-secondary"
                      }`}
                      onClick={() => setReviewStatus("reviewed")}
                    >
                      <CheckCircle2 size={16} />
                      <span>Confirm Misconduct</span>
                    </button>

                    <button
                      type="button"
                      className={`btn ${
                        reviewStatus === "dismissed"
                          ? "btn-danger"
                          : "btn-secondary"
                      }`}
                      onClick={() => setReviewStatus("dismissed")}
                    >
                      <XCircle size={16} />
                      <span>False Alarm / Dismiss</span>
                    </button>

                    <button
                      type="button"
                      className={`btn ${
                        reviewStatus === "pending"
                          ? "btn-warning"
                          : "btn-secondary"
                      }`}
                      onClick={() => setReviewStatus("pending")}
                    >
                      <Clock3 size={16} />
                      <span>Keep Pending</span>
                    </button>
                  </div>

                  <div className="notes-entry mt-4">
                    <label className="section-label">
                      Proctor Investigation Notes:
                    </label>
                    <textarea
                      rows={3}
                      value={reviewNotes}
                      placeholder="Add investigation findings, exam proctor notes, or reasoning..."
                      onChange={(e) => setReviewNotes(e.target.value)}
                    />
                  </div>

                  <button
                    className="btn btn-primary btn-block mt-4"
                    onClick={saveReview}
                    disabled={updatingId === selectedIncident.id}
                  >
                    <Save size={16} />
                    <span>
                      {updatingId === selectedIncident.id
                        ? "Saving Decision..."
                        : "Save Review Decision"}
                    </span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* OFFICIAL DISCIPLINARY DOSSIER MODAL (PRINT / SAVE AS PDF)       */}
      {/* ============================================================== */}
      {dossierData && (
        <OfficialReportModal
          incident={dossierData.incident}
          student={dossierData.student}
          allIncidents={incidents}
          apiUrl={API_URL}
          onClose={() => setDossierData(null)}
        />
      )}
    </div>
  );
}
