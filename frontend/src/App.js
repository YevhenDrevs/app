import { useState, useEffect, useCallback } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import { Toaster, toast } from "sonner";
import {
  Newspaper,
  LayoutDashboard,
  Settings,
  Database,
  FileText,
  Sparkles,
  RefreshCw,
  Search,
  Plus,
  Trash2,
  Edit,
  ExternalLink,
  Download,
  Play,
  Pause,
  X,
  Check,
  Filter,
  ChevronLeft,
  ChevronRight,
  Clock,
  Zap,
  Globe,
  Rss,
  MessageSquare,
  Code
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Sidebar Navigation Component
const Sidebar = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: "dashboard", icon: LayoutDashboard, label: "Dashboard" },
    { id: "articles", icon: Newspaper, label: "News Feed" },
    { id: "sources", icon: Database, label: "Sources" },
    { id: "summaries", icon: Sparkles, label: "AI Summaries" },
    { id: "exports", icon: FileText, label: "Exports" },
    { id: "settings", icon: Settings, label: "Settings" },
  ];

  return (
    <aside className="sidebar" data-testid="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">
          <Zap size={24} />
        </div>
        <h1>TechPulse</h1>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <button
            key={item.id}
            data-testid={`nav-${item.id}`}
            className={`nav-item ${activeTab === item.id ? "active" : ""}`}
            onClick={() => setActiveTab(item.id)}
          >
            <item.icon size={20} />
            {item.label}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <p style={{ fontSize: "0.75rem", color: "var(--muted-foreground)" }}>
          Tech News Monitor v1.0
        </p>
      </div>
    </aside>
  );
};

// Dashboard Component
const Dashboard = ({ stats, onCollect, collecting }) => {
  return (
    <div data-testid="dashboard-page">
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>Monitor your tech news collection pipeline</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-card-header">
            <span>Total Articles</span>
            <div className="stat-card-icon blue">
              <Newspaper size={20} />
            </div>
          </div>
          <div className="stat-card-value" data-testid="stat-total-articles">
            {stats.total_articles || 0}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <span>Active Sources</span>
            <div className="stat-card-icon green">
              <Database size={20} />
            </div>
          </div>
          <div className="stat-card-value" data-testid="stat-active-sources">
            {stats.active_sources || 0}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <span>Exported</span>
            <div className="stat-card-icon purple">
              <FileText size={20} />
            </div>
          </div>
          <div className="stat-card-value" data-testid="stat-exported">
            {stats.exported_articles || 0}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <span>AI Summaries</span>
            <div className="stat-card-icon orange">
              <Sparkles size={20} />
            </div>
          </div>
          <div className="stat-card-value" data-testid="stat-summaries">
            {stats.total_summaries || 0}
          </div>
        </div>
      </div>

      <div className="two-column">
        <div className="card">
          <div className="card-header">
            <h3>Quick Actions</h3>
          </div>
          <div className="card-body">
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              <Button
                data-testid="btn-collect-now"
                onClick={onCollect}
                disabled={collecting}
                className="w-full justify-start"
              >
                {collecting ? (
                  <RefreshCw size={18} className="animate-spin" />
                ) : (
                  <RefreshCw size={18} />
                )}
                {collecting ? "Collecting..." : "Collect News Now"}
              </Button>

              <div
                className={`scheduler-status ${
                  stats.scheduler_running ? "running" : "stopped"
                }`}
              >
                <Clock size={16} />
                <span>
                  Scheduler: {stats.scheduler_running ? "Running" : "Stopped"}
                </span>
                {stats.next_collection && (
                  <span style={{ marginLeft: "auto", fontSize: "0.75rem" }}>
                    Next: {new Date(stats.next_collection).toLocaleTimeString()}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3>Categories</h3>
          </div>
          <div className="card-body">
            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {Object.entries(stats.by_category || {}).map(([category, count]) => (
                <div
                  key={category}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "0.5rem 0",
                    borderBottom: "1px solid var(--border)",
                  }}
                >
                  <span style={{ fontSize: "0.875rem" }}>{category}</span>
                  <Badge variant="secondary">{count}</Badge>
                </div>
              ))}
              {Object.keys(stats.by_category || {}).length === 0 && (
                <p style={{ color: "var(--muted-foreground)", fontSize: "0.875rem" }}>
                  No articles categorized yet
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Articles Component
const Articles = ({ onCategoryChange }) => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [categories, setCategories] = useState([]);
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const limit = 20;

  const fetchArticles = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: (page * limit).toString(),
      });
      if (search) params.append("search", search);
      if (category) params.append("category", category);

      const response = await axios.get(`${API}/articles?${params}`);
      setArticles(response.data.articles);
      setTotal(response.data.total);
    } catch (error) {
      toast.error("Failed to fetch articles");
    }
    setLoading(false);
  }, [search, category, page]);

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API}/articles/categories`);
      setCategories(response.data.categories);
    } catch (error) {
      console.error("Failed to fetch categories");
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      fetchArticles();
    }, 300);
    return () => clearTimeout(timeoutId);
  }, [fetchArticles]);

  const getCategoryBadgeClass = (cat) => {
    if (!cat) return "badge-default";
    const lower = cat.toLowerCase();
    if (lower.includes("ai") || lower.includes("ml")) return "badge-ai";
    if (lower.includes("software") || lower.includes("dev")) return "badge-dev";
    if (lower.includes("security")) return "badge-security";
    if (lower.includes("tech")) return "badge-tech";
    return "badge-default";
  };

  return (
    <div data-testid="articles-page">
      <div className="page-header">
        <h2>News Feed</h2>
        <p>Browse and search collected tech news</p>
      </div>

      <div className="search-bar">
        <div className="search-input-wrapper" style={{ flex: 1 }}>
          <Search />
          <Input
            data-testid="search-input"
            placeholder="Search articles..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(0);
            }}
            style={{ paddingLeft: "2.5rem" }}
          />
        </div>

        <Select
          value={category}
          onValueChange={(val) => {
            setCategory(val === "all" ? "" : val);
            setPage(0);
          }}
        >
          <SelectTrigger data-testid="category-filter" style={{ width: "200px" }}>
            <SelectValue placeholder="All Categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            {categories.map((cat) => (
              <SelectItem key={cat} value={cat}>
                {cat}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Button variant="outline" onClick={fetchArticles} data-testid="refresh-articles">
          <RefreshCw size={18} />
        </Button>
      </div>

      {loading ? (
        <div className="loading-overlay">
          <div className="spinner" />
        </div>
      ) : articles.length === 0 ? (
        <div className="empty-state">
          <Newspaper className="empty-state-icon" />
          <h4>No articles found</h4>
          <p>Try adjusting your search or collect more news</p>
        </div>
      ) : (
        <>
          <div className="articles-list">
            {articles.map((article) => (
              <div key={article.id} className="article-item" data-testid={`article-${article.id}`}>
                <div className="article-header">
                  <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="article-title"
                  >
                    {article.title}
                  </a>
                  {article.exported === 1 && (
                    <Badge className="badge-exported">Exported</Badge>
                  )}
                </div>
                <p className="article-description">{article.description}</p>
                <div className="article-footer">
                  <div className="article-meta">
                    <span>{article.source_name || "Unknown Source"}</span>
                    {article.published_date && (
                      <span>
                        {new Date(article.published_date).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    {article.category && (
                      <span className={`badge ${getCategoryBadgeClass(article.category)}`}>
                        {article.category}
                      </span>
                    )}
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-sm btn-outline"
                    >
                      <ExternalLink size={14} />
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="pagination">
            <button
              className="pagination-btn"
              disabled={page === 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              data-testid="pagination-prev"
            >
              <ChevronLeft size={18} />
            </button>
            <span className="pagination-info">
              Page {page + 1} of {Math.ceil(total / limit) || 1}
            </span>
            <button
              className="pagination-btn"
              disabled={(page + 1) * limit >= total}
              onClick={() => setPage((p) => p + 1)}
              data-testid="pagination-next"
            >
              <ChevronRight size={18} />
            </button>
          </div>
        </>
      )}
    </div>
  );
};

// Sources Component
const Sources = () => {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingSource, setEditingSource] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    type: "rss",
    url: "",
    enabled: true,
  });

  const fetchSources = async () => {
    try {
      const response = await axios.get(`${API}/sources`);
      setSources(response.data.sources);
    } catch (error) {
      toast.error("Failed to fetch sources");
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchSources();
  }, []);

  const handleSubmit = async () => {
    try {
      if (editingSource) {
        await axios.put(`${API}/sources/${editingSource.id}`, formData);
        toast.success("Source updated");
      } else {
        await axios.post(`${API}/sources`, formData);
        toast.success("Source created");
      }
      setShowModal(false);
      setEditingSource(null);
      setFormData({ name: "", type: "rss", url: "", enabled: true });
      fetchSources();
    } catch (error) {
      toast.error("Failed to save source");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this source?")) return;
    try {
      await axios.delete(`${API}/sources/${id}`);
      toast.success("Source deleted");
      fetchSources();
    } catch (error) {
      toast.error("Failed to delete source");
    }
  };

  const handleToggle = async (source) => {
    try {
      await axios.put(`${API}/sources/${source.id}`, {
        enabled: !source.enabled,
      });
      fetchSources();
    } catch (error) {
      toast.error("Failed to update source");
    }
  };

  const handleCollect = async (id) => {
    try {
      await axios.post(`${API}/sources/${id}/collect`);
      toast.success("Collection started");
    } catch (error) {
      toast.error("Failed to start collection");
    }
  };

  const getSourceIcon = (type) => {
    switch (type) {
      case "rss":
        return <Rss size={16} />;
      case "reddit":
        return <MessageSquare size={16} />;
      case "scraper":
        return <Code size={16} />;
      default:
        return <Globe size={16} />;
    }
  };

  return (
    <div data-testid="sources-page">
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h2>News Sources</h2>
          <p>Manage your RSS feeds, APIs, and scrapers</p>
        </div>
        <Button
          data-testid="add-source-btn"
          onClick={() => {
            setEditingSource(null);
            setFormData({ name: "", type: "rss", url: "", enabled: true });
            setShowModal(true);
          }}
        >
          <Plus size={18} />
          Add Source
        </Button>
      </div>

      {loading ? (
        <div className="loading-overlay">
          <div className="spinner" />
        </div>
      ) : (
        <div className="sources-grid">
          {sources.map((source) => (
            <div key={source.id} className="source-card" data-testid={`source-${source.id}`}>
              <div className="source-card-header">
                <span className="source-name">{source.name}</span>
                <span className="source-type">
                  {getSourceIcon(source.type)} {source.type}
                </span>
              </div>
              <p className="source-url">{source.url}</p>
              {source.last_fetched && (
                <p style={{ fontSize: "0.75rem", color: "var(--muted-foreground)", marginBottom: "0.5rem" }}>
                  Last fetched: {new Date(source.last_fetched).toLocaleString()}
                </p>
              )}
              <div className="source-footer">
                <div className="source-status">
                  <span
                    className={`status-dot ${source.enabled ? "enabled" : "disabled"}`}
                  />
                  <span>{source.enabled ? "Enabled" : "Disabled"}</span>
                </div>
                <div className="action-buttons">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleCollect(source.id)}
                    title="Collect now"
                  >
                    <RefreshCw size={16} />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      setEditingSource(source);
                      setFormData({
                        name: source.name,
                        type: source.type,
                        url: source.url,
                        enabled: source.enabled,
                      });
                      setShowModal(true);
                    }}
                  >
                    <Edit size={16} />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleDelete(source.id)}
                  >
                    <Trash2 size={16} />
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingSource ? "Edit Source" : "Add New Source"}
            </DialogTitle>
          </DialogHeader>
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div>
              <label className="form-label">Name</label>
              <Input
                data-testid="source-name-input"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Source name"
              />
            </div>
            <div>
              <label className="form-label">Type</label>
              <Select
                value={formData.type}
                onValueChange={(val) => setFormData({ ...formData, type: val })}
              >
                <SelectTrigger data-testid="source-type-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="rss">RSS Feed</SelectItem>
                  <SelectItem value="reddit">Reddit</SelectItem>
                  <SelectItem value="scraper">Web Scraper</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="form-label">URL</label>
              <Input
                data-testid="source-url-input"
                value={formData.url}
                onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                placeholder="https://..."
              />
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Switch
                checked={formData.enabled}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, enabled: checked })
                }
              />
              <span>Enabled</span>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} data-testid="save-source-btn">
              {editingSource ? "Update" : "Create"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Summaries Component
const Summaries = () => {
  const [summaries, setSummaries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [outputFormat, setOutputFormat] = useState("markdown");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [categories, setCategories] = useState([]);

  const fetchSummaries = async () => {
    try {
      const response = await axios.get(`${API}/summaries`);
      setSummaries(response.data.summaries);
    } catch (error) {
      toast.error("Failed to fetch summaries");
    }
    setLoading(false);
  };

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API}/articles/categories`);
      setCategories(response.data.categories);
    } catch (error) {
      console.error("Failed to fetch categories");
    }
  };

  useEffect(() => {
    fetchSummaries();
    fetchCategories();
  }, []);

  const generateSummary = async () => {
    setGenerating(true);
    try {
      const response = await axios.post(`${API}/summarize`, {
        output_format: outputFormat,
        category: selectedCategory || null,
        limit: 20,
      });
      toast.success("Summary generated!");
      fetchSummaries();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to generate summary");
    }
    setGenerating(false);
  };

  return (
    <div data-testid="summaries-page">
      <div className="page-header">
        <h2>AI Summaries</h2>
        <p>Generate AI-powered summaries of your collected news</p>
      </div>

      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <div className="card-header">
          <h3>Generate New Summary</h3>
        </div>
        <div className="card-body">
          <div style={{ display: "flex", gap: "1rem", alignItems: "flex-end", flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: "200px" }}>
              <label className="form-label">Category Filter</label>
              <Select
                value={selectedCategory}
                onValueChange={setSelectedCategory}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All Categories" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {categories.map((cat) => (
                    <SelectItem key={cat} value={cat}>
                      {cat}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div style={{ flex: 1, minWidth: "200px" }}>
              <label className="form-label">Output Format</label>
              <Select value={outputFormat} onValueChange={setOutputFormat}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="markdown">Markdown</SelectItem>
                  <SelectItem value="json">JSON</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button
              data-testid="generate-summary-btn"
              onClick={generateSummary}
              disabled={generating}
            >
              {generating ? (
                <RefreshCw size={18} className="animate-spin" />
              ) : (
                <Sparkles size={18} />
              )}
              {generating ? "Generating..." : "Generate Summary"}
            </Button>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="loading-overlay">
          <div className="spinner" />
        </div>
      ) : summaries.length === 0 ? (
        <div className="empty-state">
          <Sparkles className="empty-state-icon" />
          <h4>No summaries yet</h4>
          <p>Generate your first AI summary to get started</p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {summaries.map((summary) => (
            <div key={summary.id} className="summary-preview" data-testid={`summary-${summary.id}`}>
              <div className="summary-preview-header">
                <div>
                  <h4 style={{ marginBottom: "0.25rem" }}>
                    Summary #{summary.id}
                    {summary.category && (
                      <Badge variant="secondary" style={{ marginLeft: "0.5rem" }}>
                        {summary.category}
                      </Badge>
                    )}
                  </h4>
                  <span style={{ fontSize: "0.8125rem", color: "var(--muted-foreground)" }}>
                    {new Date(summary.created_at).toLocaleString()} •{" "}
                    {summary.article_ids?.length || 0} articles
                  </span>
                </div>
              </div>
              <ScrollArea className="h-[300px] rounded-md border p-4">
                <div className="summary-content">
                  {summary.summary_text}
                </div>
              </ScrollArea>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Exports Component
const Exports = () => {
  const [exports, setExports] = useState([]);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [exportType, setExportType] = useState("notebooklm");
  const [unexportedOnly, setUnexportedOnly] = useState(false);
  const [notebooklmPrompt, setNotebooklmPrompt] = useState("");

  const fetchExports = async () => {
    try {
      const response = await axios.get(`${API}/exports`);
      setFiles(response.data.files);
      setExports(response.data.history);
    } catch (error) {
      toast.error("Failed to fetch exports");
    }
    setLoading(false);
  };

  const fetchPrompt = async () => {
    try {
      const response = await axios.get(`${API}/notebooklm/prompt`);
      setNotebooklmPrompt(response.data.prompt);
    } catch (error) {
      console.error("Failed to fetch prompt");
    }
  };

  useEffect(() => {
    fetchExports();
    fetchPrompt();
  }, []);

  const createExport = async () => {
    setExporting(true);
    try {
      const response = await axios.post(`${API}/export`, {
        export_type: exportType,
        unexported_only: unexportedOnly,
        mark_exported: true,
        limit: 100,
      });
      toast.success(`Exported ${response.data.articles_count} articles`);
      fetchExports();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Export failed");
    }
    setExporting(false);
  };

  const downloadExport = async (filename) => {
    try {
      const response = await axios.get(`${API}/exports/${filename}`);
      const blob = new Blob([response.data], { type: "text/plain" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
    } catch (error) {
      toast.error("Download failed");
    }
  };

  const deleteExport = async (filename) => {
    if (!window.confirm("Delete this export?")) return;
    try {
      await axios.delete(`${API}/exports/${filename}`);
      toast.success("Export deleted");
      fetchExports();
    } catch (error) {
      toast.error("Failed to delete export");
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  return (
    <div data-testid="exports-page">
      <div className="page-header">
        <h2>Exports</h2>
        <p>Export articles for NotebookLM or other analysis tools</p>
      </div>

      <Tabs defaultValue="create">
        <TabsList style={{ marginBottom: "1.5rem" }}>
          <TabsTrigger value="create">Create Export</TabsTrigger>
          <TabsTrigger value="files">Export Files</TabsTrigger>
          <TabsTrigger value="prompt">NotebookLM Prompt</TabsTrigger>
        </TabsList>

        <TabsContent value="create">
          <div className="card">
            <div className="card-header">
              <h3>Create New Export</h3>
            </div>
            <div className="card-body">
              <div style={{ display: "flex", gap: "1rem", alignItems: "flex-end", flexWrap: "wrap", marginBottom: "1rem" }}>
                <div style={{ flex: 1, minWidth: "200px" }}>
                  <label className="form-label">Export Format</label>
                  <Select value={exportType} onValueChange={setExportType}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="notebooklm">
                        NotebookLM (Text)
                      </SelectItem>
                      <SelectItem value="jsonl">JSONL</SelectItem>
                      <SelectItem value="urls">URLs List</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <Switch
                    checked={unexportedOnly}
                    onCheckedChange={setUnexportedOnly}
                  />
                  <span>Unexported articles only</span>
                </div>
                <Button
                  data-testid="create-export-btn"
                  onClick={createExport}
                  disabled={exporting}
                >
                  {exporting ? (
                    <RefreshCw size={18} className="animate-spin" />
                  ) : (
                    <Download size={18} />
                  )}
                  {exporting ? "Exporting..." : "Create Export"}
                </Button>
              </div>

              <div style={{ padding: "1rem", background: "var(--muted)", borderRadius: "8px", fontSize: "0.875rem" }}>
                <p style={{ marginBottom: "0.5rem", fontWeight: "500" }}>
                  Export Types:
                </p>
                <ul style={{ paddingLeft: "1.25rem", color: "var(--muted-foreground)" }}>
                  <li>
                    <strong>NotebookLM:</strong> Formatted text file ready for
                    upload to Google NotebookLM
                  </li>
                  <li>
                    <strong>JSONL:</strong> Machine-readable format for data
                    processing
                  </li>
                  <li>
                    <strong>URLs:</strong> List of article URLs for adding as
                    web sources
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="files">
          <div className="card">
            <div className="card-header">
              <h3>Export Files</h3>
            </div>
            <div className="card-body" style={{ padding: 0 }}>
              {files.length === 0 ? (
                <div className="empty-state">
                  <FileText className="empty-state-icon" />
                  <h4>No exports yet</h4>
                  <p>Create your first export to get started</p>
                </div>
              ) : (
                <table className="exports-table">
                  <thead>
                    <tr>
                      <th>Filename</th>
                      <th>Type</th>
                      <th>Size</th>
                      <th>Created</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {files.map((file) => (
                      <tr key={file.filename}>
                        <td>{file.filename}</td>
                        <td>
                          <Badge variant="secondary">{file.type}</Badge>
                        </td>
                        <td>{formatFileSize(file.size)}</td>
                        <td>{new Date(file.created).toLocaleString()}</td>
                        <td>
                          <div className="action-buttons">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => downloadExport(file.filename)}
                            >
                              <Download size={16} />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => deleteExport(file.filename)}
                            >
                              <Trash2 size={16} />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="prompt">
          <div className="card">
            <div className="card-header">
              <h3>NotebookLM Instructions</h3>
            </div>
            <div className="card-body">
              <p style={{ marginBottom: "1rem", color: "var(--muted-foreground)" }}>
                Copy this prompt and paste it in NotebookLM when analyzing your
                exported news articles:
              </p>
              <Textarea
                value={notebooklmPrompt}
                readOnly
                style={{ minHeight: "300px", fontFamily: "monospace", fontSize: "0.875rem" }}
              />
              <Button
                variant="outline"
                style={{ marginTop: "1rem" }}
                onClick={() => {
                  navigator.clipboard.writeText(notebooklmPrompt);
                  toast.success("Copied to clipboard!");
                }}
              >
                Copy to Clipboard
              </Button>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

// Settings Component
const SettingsPage = () => {
  const [settings, setSettings] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [schedulerRunning, setSchedulerRunning] = useState(false);

  const fetchSettings = async () => {
    try {
      const [settingsRes, statusRes] = await Promise.all([
        axios.get(`${API}/settings`),
        axios.get(`${API}/scheduler/status`),
      ]);
      setSettings(settingsRes.data.settings);
      setSchedulerRunning(statusRes.data.running);
    } catch (error) {
      toast.error("Failed to fetch settings");
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const saveSettings = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/settings`, { settings });
      toast.success("Settings saved");
    } catch (error) {
      toast.error("Failed to save settings");
    }
    setSaving(false);
  };

  const toggleScheduler = async () => {
    try {
      if (schedulerRunning) {
        await axios.post(`${API}/scheduler/stop`);
        toast.success("Scheduler stopped");
      } else {
        await axios.post(`${API}/scheduler/start`);
        toast.success("Scheduler started");
      }
      const statusRes = await axios.get(`${API}/scheduler/status`);
      setSchedulerRunning(statusRes.data.running);
    } catch (error) {
      toast.error("Failed to toggle scheduler");
    }
  };

  if (loading) {
    return (
      <div className="loading-overlay">
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div data-testid="settings-page">
      <div className="page-header">
        <h2>Settings</h2>
        <p>Configure your news monitoring system</p>
      </div>

      <div className="settings-section">
        <h3>Scheduler</h3>
        <div className="settings-row">
          <div className="settings-row-label">
            <h4>Automatic Collection</h4>
            <p>Enable/disable automatic news collection</p>
          </div>
          <div className="settings-row-control">
            <span style={{ fontSize: "0.875rem", marginRight: "0.5rem" }}>
              {schedulerRunning ? "Running" : "Stopped"}
            </span>
            <Switch checked={schedulerRunning} onCheckedChange={toggleScheduler} />
          </div>
        </div>
        <div className="settings-row">
          <div className="settings-row-label">
            <h4>Collection Interval (minutes)</h4>
            <p>How often to fetch new articles</p>
          </div>
          <div className="settings-row-control">
            <Input
              data-testid="interval-input"
              type="number"
              min="5"
              max="1440"
              value={settings.schedule_interval || 60}
              onChange={(e) =>
                setSettings({ ...settings, schedule_interval: e.target.value })
              }
              style={{ width: "100px" }}
            />
          </div>
        </div>
      </div>

      <div className="settings-section">
        <h3>AI Configuration</h3>
        <div className="settings-row">
          <div className="settings-row-label">
            <h4>Auto-Categorize Articles</h4>
            <p>Automatically categorize new articles using AI</p>
          </div>
          <div className="settings-row-control">
            <Switch
              checked={settings.auto_summarize === "true"}
              onCheckedChange={(checked) =>
                setSettings({ ...settings, auto_summarize: checked ? "true" : "false" })
              }
            />
          </div>
        </div>
        <div className="settings-row">
          <div className="settings-row-label">
            <h4>LLM Model</h4>
            <p>AI model for summarization and categorization</p>
          </div>
          <div className="settings-row-control">
            <Select
              value={settings.llm_model || "gpt-4o-mini"}
              onValueChange={(val) => setSettings({ ...settings, llm_model: val })}
            >
              <SelectTrigger style={{ width: "180px" }}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="gpt-4o-mini">GPT-4o Mini</SelectItem>
                <SelectItem value="gpt-4o">GPT-4o</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      <div className="settings-section">
        <h3>Categories</h3>
        <div className="settings-row" style={{ flexDirection: "column", alignItems: "stretch" }}>
          <div className="settings-row-label">
            <h4>Category Keywords</h4>
            <p>Comma-separated list of categories for filtering</p>
          </div>
          <Textarea
            data-testid="categories-input"
            value={settings.categories || ""}
            onChange={(e) => setSettings({ ...settings, categories: e.target.value })}
            style={{ marginTop: "0.5rem" }}
          />
        </div>
      </div>

      <div className="settings-section">
        <h3>Limits</h3>
        <div className="settings-row">
          <div className="settings-row-label">
            <h4>Max Articles Per Fetch</h4>
            <p>Maximum number of articles to fetch per source</p>
          </div>
          <div className="settings-row-control">
            <Input
              type="number"
              min="10"
              max="500"
              value={settings.max_articles_per_fetch || 50}
              onChange={(e) =>
                setSettings({ ...settings, max_articles_per_fetch: e.target.value })
              }
              style={{ width: "100px" }}
            />
          </div>
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <Button data-testid="save-settings-btn" onClick={saveSettings} disabled={saving}>
          {saving ? "Saving..." : "Save Settings"}
        </Button>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [stats, setStats] = useState({});
  const [collecting, setCollecting] = useState(false);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/stats`);
      setStats(response.data);
    } catch (error) {
      console.error("Failed to fetch stats");
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleCollect = async () => {
    setCollecting(true);
    try {
      await axios.post(`${API}/collect/sync`);
      toast.success("News collection completed!");
      fetchStats();
    } catch (error) {
      toast.error("Collection failed");
    }
    setCollecting(false);
  };

  const renderContent = () => {
    switch (activeTab) {
      case "dashboard":
        return (
          <Dashboard
            stats={stats}
            onCollect={handleCollect}
            collecting={collecting}
          />
        );
      case "articles":
        return <Articles />;
      case "sources":
        return <Sources />;
      case "summaries":
        return <Summaries />;
      case "exports":
        return <Exports />;
      case "settings":
        return <SettingsPage />;
      default:
        return <Dashboard stats={stats} onCollect={handleCollect} collecting={collecting} />;
    }
  };

  return (
    <div className="app-container" data-testid="app-container">
      <Toaster position="bottom-right" richColors />
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main className="main-content">{renderContent()}</main>
    </div>
  );
}

export default App;
