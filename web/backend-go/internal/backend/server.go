package backend

import (
	"context"
	"crypto/rand"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"

	_ "github.com/duckdb/duckdb-go/v2"
	"gopkg.in/yaml.v3"
)

type Config struct {
	RepoRoot            string
	OutputRoot          string
	FormalRoot          string
	CatalogPath         string
	DefaultConfigPath   string
	PythonExecutable    string
	RunnerScriptPath    string
	RegistrarScriptPath string
}

type App struct {
	config Config
	mu     sync.Mutex
}

type validationError struct {
	message string
}

func (e validationError) Error() string {
	return e.message
}

type marketOption struct {
	OptionID      string `json:"option_id"`
	ConfigProfile string `json:"config_profile"`
	MarketID      string `json:"market_id"`
	MarketName    string `json:"market_name"`
	UniverseID    string `json:"universe_id"`
	IsFormal      bool   `json:"is_formal"`
}

var marketOptions = []marketOption{
	{
		OptionID:      "formal_hs300",
		ConfigProfile: "formal_hs300",
		MarketID:      "cn_a",
		MarketName:    "A股 / 沪深300",
		UniverseID:    "HS300",
		IsFormal:      true,
	},
	{
		OptionID:      "formal_sz50",
		ConfigProfile: "formal_sz50",
		MarketID:      "cn_a",
		MarketName:    "A股 / 上证50",
		UniverseID:    "SZ50",
		IsFormal:      true,
	},
	{
		OptionID:      "formal_zz500",
		ConfigProfile: "formal_zz500",
		MarketID:      "cn_a",
		MarketName:    "A股 / 中证500",
		UniverseID:    "ZZ500",
		IsFormal:      true,
	},
	{
		OptionID:      "sample_cn_smoke",
		ConfigProfile: "sample_cn_smoke",
		MarketID:      "cn_a",
		MarketName:    "A股样例",
		UniverseID:    "CSI_A500",
		IsFormal:      false,
	},
	{
		OptionID:      "sample_us_equity",
		ConfigProfile: "sample_us_equity",
		MarketID:      "us_equity",
		MarketName:    "美股样例",
		UniverseID:    "EXTERNAL_LIST",
		IsFormal:      false,
	},
}

var universeViewByID = map[string]string{
	"ALL_A_TRADABLE": "universes.vw_all_a_tradable_on_date",
	"HS300":          "universes.vw_hs300_on_date",
	"SZ50":           "universes.vw_sz50_on_date",
	"ZZ500":          "universes.vw_zz500_on_date",
}

var runIDPattern = regexp.MustCompile(`^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$`)

var allowedConfigSuffixes = map[string]struct{}{
	".yaml": {},
	".yml":  {},
}

func NewHandler(cfg Config) (http.Handler, error) {
	resolved, err := normalizeConfig(cfg)
	if err != nil {
		return nil, err
	}
	app := &App{config: resolved}
	mux := http.NewServeMux()
	mux.HandleFunc("GET /api/markets", app.handleMarkets)
	mux.HandleFunc("GET /api/formal/coverage", app.handleFormalCoverage)
	mux.HandleFunc("GET /api/formal/universes/{universe_id}", app.handleFormalUniverse)
	mux.HandleFunc("GET /api/runs", app.handleRuns)
	mux.HandleFunc("POST /api/runs", app.handleCreateRun)
	mux.HandleFunc("GET /api/runs/{run_id}/metrics", app.handleRunMetrics)
	mux.HandleFunc("GET /api/runs/{run_id}/selection", app.handleRunSelection)
	mux.HandleFunc("GET /api/runs/{run_id}", app.handleRunDetail)
	return mux, nil
}

func normalizeConfig(cfg Config) (Config, error) {
	resolved := cfg
	if resolved.RepoRoot == "" {
		cwd, err := os.Getwd()
		if err != nil {
			return Config{}, err
		}
		resolved.RepoRoot = cwd
	}
	abs := func(path string) string {
		if path == "" {
			return ""
		}
		if filepath.IsAbs(path) {
			return filepath.Clean(path)
		}
		return filepath.Clean(filepath.Join(resolved.RepoRoot, path))
	}
	resolved.RepoRoot = abs(resolved.RepoRoot)
	if resolved.OutputRoot == "" {
		resolved.OutputRoot = filepath.Join(resolved.RepoRoot, "code", "outputs")
	}
	if resolved.FormalRoot == "" {
		resolved.FormalRoot = filepath.Join(resolved.RepoRoot, "code", "data", "formal")
	}
	if resolved.CatalogPath == "" {
		resolved.CatalogPath = filepath.Join(resolved.FormalRoot, "catalog.duckdb")
	}
	if resolved.DefaultConfigPath == "" {
		resolved.DefaultConfigPath = filepath.Join(resolved.RepoRoot, "code", "configs", "default.yaml")
	}
	if resolved.RunnerScriptPath == "" {
		resolved.RunnerScriptPath = filepath.Join(resolved.RepoRoot, "code", "main.py")
	}
	if resolved.RegistrarScriptPath == "" {
		resolved.RegistrarScriptPath = filepath.Join(resolved.RepoRoot, "code", "data", "register_formal_duckdb_catalog.py")
	}
	if resolved.PythonExecutable == "" {
		candidates := []string{
			filepath.Join(resolved.RepoRoot, ".venv", "Scripts", "python.exe"),
			filepath.Join(resolved.RepoRoot, ".venv", "bin", "python"),
		}
		for _, candidate := range candidates {
			if _, err := os.Stat(candidate); err == nil {
				resolved.PythonExecutable = candidate
				break
			}
		}
		if resolved.PythonExecutable == "" {
			resolved.PythonExecutable = "python"
		}
	}
	resolved.OutputRoot = abs(resolved.OutputRoot)
	resolved.FormalRoot = abs(resolved.FormalRoot)
	resolved.CatalogPath = abs(resolved.CatalogPath)
	resolved.DefaultConfigPath = abs(resolved.DefaultConfigPath)
	resolved.RunnerScriptPath = abs(resolved.RunnerScriptPath)
	resolved.RegistrarScriptPath = abs(resolved.RegistrarScriptPath)
	return resolved, nil
}

func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(payload)
}

func writeError(w http.ResponseWriter, status int, detail string) {
	writeJSON(w, status, map[string]string{"detail": detail})
}

func newValidationError(message string) error {
	return validationError{message: message}
}

func isValidationError(err error) bool {
	var target validationError
	return errors.As(err, &target)
}

func isPathWithinRoot(candidate string, root string) bool {
	relative, err := filepath.Rel(root, candidate)
	if err != nil {
		return false
	}
	return relative != ".." && !strings.HasPrefix(relative, fmt.Sprintf("..%c", filepath.Separator))
}

func evalSymlinkPath(path string) (string, error) {
	resolvedPath, err := filepath.EvalSymlinks(path)
	if err != nil {
		return "", err
	}
	return filepath.Clean(resolvedPath), nil
}

func validateRunID(runID string) (string, error) {
	candidate := strings.TrimSpace(runID)
	if !runIDPattern.MatchString(candidate) {
		return "", newValidationError("run_id 只能包含字母、数字、下划线和中划线，且长度不能超过 64")
	}
	return candidate, nil
}

func validatePositiveInt(value int, fieldName string) error {
	if value <= 0 {
		return newValidationError(fmt.Sprintf("%s 必须是大于 0 的整数", fieldName))
	}
	return nil
}

func coercePositiveInt(value any, fieldName string) (int, error) {
	switch typed := value.(type) {
	case int:
		return typed, validatePositiveInt(typed, fieldName)
	case int64:
		converted := int(typed)
		if int64(converted) != typed {
			return 0, newValidationError(fmt.Sprintf("%s 必须是整数", fieldName))
		}
		return converted, validatePositiveInt(converted, fieldName)
	case float64:
		if typed != float64(int(typed)) {
			return 0, newValidationError(fmt.Sprintf("%s 必须是整数", fieldName))
		}
		converted := int(typed)
		return converted, validatePositiveInt(converted, fieldName)
	case string:
		parsed, err := strconv.Atoi(strings.TrimSpace(typed))
		if err != nil {
			return 0, newValidationError(fmt.Sprintf("%s 必须是整数", fieldName))
		}
		return parsed, validatePositiveInt(parsed, fieldName)
	default:
		return 0, newValidationError(fmt.Sprintf("%s 必须是整数", fieldName))
	}
}

func (a *App) resolveRunDir(runID string, validatePattern bool) (string, error) {
	candidate := strings.TrimSpace(runID)
	if strings.Contains(candidate, "\\") {
		return "", newValidationError("run_id 不能包含路径分隔符")
	}
	var safeRunID string
	var err error
	if validatePattern {
		safeRunID, err = validateRunID(candidate)
	} else {
		if candidate == "" {
			return "", newValidationError("run_id 不能为空")
		}
		safeRunID = candidate
	}
	if err != nil {
		return "", err
	}
	runDir := filepath.Clean(filepath.Join(a.config.OutputRoot, safeRunID))
	comparisonRoot := filepath.Clean(a.config.OutputRoot)
	outputRootResolved := false
	if _, statErr := os.Lstat(comparisonRoot); statErr == nil {
		resolvedOutputRoot, err := evalSymlinkPath(comparisonRoot)
		if err != nil {
			return "", newValidationError("输出目录无法解析")
		}
		comparisonRoot = resolvedOutputRoot
		outputRootResolved = true
	}
	if _, statErr := os.Lstat(runDir); statErr == nil {
		resolvedRunDir, err := evalSymlinkPath(runDir)
		if err != nil {
			return "", newValidationError("run_id 对应的运行目录无法解析")
		}
		runDir = resolvedRunDir
	} else if outputRootResolved {
		runDir = filepath.Clean(filepath.Join(comparisonRoot, safeRunID))
	}
	// 这里用真实路径边界约束 run_id，避免路径穿越进入 outputs 目录之外。
	if !isPathWithinRoot(runDir, comparisonRoot) {
		return "", newValidationError("run_id 超出输出目录边界")
	}
	return runDir, nil
}

func (a *App) resolveRequestedConfigPath(rawConfigPath string) (string, error) {
	candidate := strings.TrimSpace(rawConfigPath)
	if candidate == "" {
		return "", newValidationError("config_path 不能为空")
	}
	var resolvedPath string
	if filepath.IsAbs(candidate) {
		resolvedPath = candidate
	} else {
		defaultConfigDir := filepath.Dir(a.config.DefaultConfigPath)
		candidatePaths := []string{
			filepath.Join(defaultConfigDir, candidate),
			filepath.Join(a.config.RepoRoot, candidate),
		}
		resolvedPath = candidatePaths[0]
		for _, path := range candidatePaths {
			if _, err := os.Stat(path); err == nil {
				resolvedPath = path
				break
			}
		}
	}
	resolvedPath = filepath.Clean(resolvedPath)

	if _, ok := allowedConfigSuffixes[strings.ToLower(filepath.Ext(resolvedPath))]; !ok {
		return "", newValidationError("config_path 只能指向 YAML 配置文件")
	}
	if info, err := os.Stat(resolvedPath); err != nil {
		return "", newValidationError("config_path 指向的配置文件不存在")
	} else if info.IsDir() {
		return "", newValidationError("config_path 必须指向配置文件")
	}
	realConfigPath, err := evalSymlinkPath(resolvedPath)
	if err != nil {
		return "", newValidationError("config_path 无法解析符号链接")
	}
	if realOutputRoot, err := evalSymlinkPath(a.config.OutputRoot); err == nil {
		if filepath.Base(realConfigPath) == "submitted_config.yaml" && isPathWithinRoot(realConfigPath, realOutputRoot) {
			return realConfigPath, nil
		}
	}

	// 自定义配置只允许落在受控目录，避免任意文件被注入到实验执行链路。
	allowedRoots := []string{
		filepath.Clean(filepath.Join(a.config.RepoRoot, "code", "configs")),
		filepath.Clean(filepath.Dir(a.config.DefaultConfigPath)),
	}
	for _, root := range allowedRoots {
		realRoot, err := evalSymlinkPath(root)
		if err != nil {
			continue
		}
		if isPathWithinRoot(realConfigPath, realRoot) {
			return realConfigPath, nil
		}
	}
	return "", newValidationError("config_path 不在允许的配置目录内")
}

func (a *App) handleMarkets(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, marketOptions)
}

func (a *App) handleFormalCoverage(w http.ResponseWriter, r *http.Request) {
	payload, err := a.getFormalCoverage()
	if err != nil {
		writeError(w, http.StatusServiceUnavailable, err.Error())
		return
	}
	writeJSON(w, http.StatusOK, payload)
}

func (a *App) handleFormalUniverse(w http.ResponseWriter, r *http.Request) {
	universeID := normalizeUniverseID(r.PathValue("universe_id"))
	tradeDate := r.URL.Query().Get("trade_date")
	rows, err := a.getUniverseMembersForDate(universeID, tradeDate)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) || strings.Contains(err.Error(), "unknown universe") {
			writeError(w, http.StatusNotFound, "Universe not found")
			return
		}
		writeError(w, http.StatusServiceUnavailable, err.Error())
		return
	}
	writeJSON(w, http.StatusOK, rows)
}

func (a *App) handleRuns(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, a.listRuns())
}

func (a *App) handleRunDetail(w http.ResponseWriter, r *http.Request) {
	runID := r.PathValue("run_id")
	runDir, err := a.resolveRunDir(runID, false)
	if err != nil {
		writeError(w, http.StatusUnprocessableEntity, err.Error())
		return
	}
	if _, err := os.Stat(runDir); err != nil {
		writeError(w, http.StatusNotFound, "Run not found")
		return
	}
	detail, err := a.getRunDetail(runID)
	if err != nil {
		writeError(w, http.StatusInternalServerError, err.Error())
		return
	}
	writeJSON(w, http.StatusOK, detail)
}

func (a *App) handleRunMetrics(w http.ResponseWriter, r *http.Request) {
	runID := r.PathValue("run_id")
	runDir, err := a.resolveRunDir(runID, false)
	if err != nil {
		writeError(w, http.StatusUnprocessableEntity, err.Error())
		return
	}
	if _, err := os.Stat(runDir); err != nil {
		writeError(w, http.StatusNotFound, "Run not found")
		return
	}
	status := a.loadStatus(runDir)
	metricsPath := filepath.Join(runDir, "metrics.json")
	if status["status"] != "completed" {
		writeError(w, http.StatusConflict, "Run metrics are not available yet")
		return
	}
	metrics, err := readJSONFile(metricsPath)
	if err != nil {
		writeError(w, http.StatusConflict, "Run metrics are not available yet")
		return
	}
	writeJSON(w, http.StatusOK, metrics)
}

func (a *App) handleRunSelection(w http.ResponseWriter, r *http.Request) {
	runID := r.PathValue("run_id")
	tradeDate := r.URL.Query().Get("trade_date")
	topN := 50
	if value := r.URL.Query().Get("top_n"); value != "" {
		parsed, err := strconv.Atoi(value)
		if err != nil {
			writeError(w, http.StatusUnprocessableEntity, "top_n 必须是整数")
			return
		}
		topN = parsed
	}
	if err := validatePositiveInt(topN, "top_n"); err != nil {
		writeError(w, http.StatusUnprocessableEntity, err.Error())
		return
	}
	runDir, err := a.resolveRunDir(runID, false)
	if err != nil {
		writeError(w, http.StatusUnprocessableEntity, err.Error())
		return
	}
	if _, err := os.Stat(runDir); err != nil {
		writeError(w, http.StatusNotFound, "Run not found")
		return
	}
	status := a.loadStatus(runDir)
	if status["status"] != "completed" {
		writeError(w, http.StatusConflict, "Selection results are not available yet")
		return
	}
	rows, err := a.getSelectionForDate(runID, tradeDate, topN)
	if err != nil {
		writeError(w, http.StatusConflict, "Selection results are not available yet")
		return
	}
	writeJSON(w, http.StatusOK, rows)
}

func (a *App) handleCreateRun(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		writeError(w, http.StatusBadRequest, "Failed to read request body")
		return
	}
	var payload map[string]any
	if len(body) > 0 {
		if err := json.Unmarshal(body, &payload); err != nil {
			writeError(w, http.StatusBadRequest, "Invalid JSON payload")
			return
		}
	} else {
		payload = map[string]any{}
	}

	status, err := a.submitRun(payload)
	if err != nil {
		if isValidationError(err) {
			writeError(w, http.StatusUnprocessableEntity, err.Error())
			return
		}
		writeError(w, http.StatusInternalServerError, err.Error())
		return
	}
	writeJSON(w, http.StatusOK, status)
}

func repoRelativePath(repoRoot string, target string) string {
	if target == "" {
		return ""
	}
	if !filepath.IsAbs(target) {
		return filepath.ToSlash(filepath.Clean(target))
	}
	relative, err := filepath.Rel(repoRoot, target)
	if err != nil || strings.HasPrefix(relative, "..") {
		return filepath.ToSlash(filepath.Clean(target))
	}
	return filepath.ToSlash(relative)
}

func pathRelativeTo(baseDir string, target string) string {
	relative, err := filepath.Rel(baseDir, target)
	if err != nil {
		return filepath.ToSlash(target)
	}
	return filepath.ToSlash(relative)
}

func readJSONFile(path string) (any, error) {
	content, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var payload any
	if err := json.Unmarshal(content, &payload); err != nil {
		return nil, err
	}
	return payload, nil
}

func writeJSONFile(path string, payload map[string]any) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	tempPath := fmt.Sprintf("%s.%d.tmp", path, time.Now().UnixNano())
	content, err := json.MarshalIndent(payload, "", "  ")
	if err != nil {
		return err
	}
	if err := os.WriteFile(tempPath, content, 0o644); err != nil {
		return err
	}
	return os.Rename(tempPath, path)
}

func utcNowISO() string {
	return time.Now().UTC().Format(time.RFC3339Nano)
}

func (a *App) statusPath(runDir string) string {
	return filepath.Join(runDir, "run_status.json")
}

func (a *App) loadStatus(runDir string) map[string]any {
	statusPath := a.statusPath(runDir)
	payloadAny, err := readJSONFile(statusPath)
	if err != nil {
		return map[string]any{
			"run_id":     filepath.Base(runDir),
			"status":     "unknown",
			"created_at": nil,
			"updated_at": nil,
		}
	}
	if payload, ok := payloadAny.(map[string]any); ok {
		return payload
	}
	return map[string]any{
		"run_id":     filepath.Base(runDir),
		"status":     "unknown",
		"created_at": nil,
		"updated_at": nil,
	}
}

func (a *App) updateStatus(runDir string, status string, extra map[string]any) map[string]any {
	a.mu.Lock()
	defer a.mu.Unlock()
	payload := a.loadStatus(runDir)
	payload["status"] = status
	payload["updated_at"] = utcNowISO()
	if payload["created_at"] == nil {
		payload["created_at"] = payload["updated_at"]
	}
	for key, value := range extra {
		payload[key] = value
	}
	_ = writeJSONFile(a.statusPath(runDir), payload)
	return payload
}

func (a *App) listRuns() []map[string]any {
	entries, err := os.ReadDir(a.config.OutputRoot)
	if err != nil {
		return []map[string]any{}
	}
	runs := make([]map[string]any, 0)
	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		runDir := filepath.Join(a.config.OutputRoot, entry.Name())
		status := a.loadStatus(runDir)
		var manifest any
		manifestPath := filepath.Join(runDir, "run_manifest.json")
		if payload, err := readJSONFile(manifestPath); err == nil {
			manifest = payload
		}
		_, metricsExistsErr := os.Stat(filepath.Join(runDir, "metrics.json"))
		runs = append(runs, map[string]any{
			"run_id":         entry.Name(),
			"status":         status,
			"manifest":       manifest,
			"metrics_exists": metricsExistsErr == nil,
		})
	}
	sort.Slice(runs, func(i, j int) bool {
		return fmt.Sprint(runs[i]["run_id"]) < fmt.Sprint(runs[j]["run_id"])
	})
	return runs
}

func (a *App) getRunDetail(runID string) (map[string]any, error) {
	runDir, err := a.resolveRunDir(runID, false)
	if err != nil {
		return nil, err
	}
	detail := map[string]any{
		"run_id":              filepath.Base(runDir),
		"status":              a.loadStatus(runDir),
		"manifest":            []any{},
		"metrics":             []any{},
		"factor_summaries":    map[string]any{},
		"factor_associations": map[string]any{},
		"time_regimes":        map[string]any{},
	}
	if manifest, err := readJSONFile(filepath.Join(runDir, "run_manifest.json")); err == nil {
		detail["manifest"] = manifest
	} else {
		detail["manifest"] = nil
	}
	if metrics, err := readJSONFile(filepath.Join(runDir, "metrics.json")); err == nil {
		detail["metrics"] = metrics
	} else {
		detail["metrics"] = []any{}
	}
	loadPattern := func(prefix string) map[string]any {
		result := map[string]any{}
		entries, _ := os.ReadDir(runDir)
		for _, entry := range entries {
			if entry.IsDir() {
				continue
			}
			name := entry.Name()
			if strings.HasPrefix(name, prefix) && strings.HasSuffix(name, ".json") {
				key := strings.TrimSuffix(strings.TrimPrefix(name, prefix), ".json")
				if payload, err := readJSONFile(filepath.Join(runDir, name)); err == nil {
					result[key] = payload
				}
			}
		}
		return result
	}
	detail["factor_summaries"] = loadPattern("factor_summary_")
	detail["factor_associations"] = loadPattern("factor_association_")
	detail["time_regimes"] = loadPattern("time_regimes_")
	return detail, nil
}

func (a *App) getSelectionForDate(runID string, tradeDate string, topN int) ([]map[string]any, error) {
	runDir, err := a.resolveRunDir(runID, false)
	if err != nil {
		return nil, err
	}
	selectionAny, err := readJSONFile(filepath.Join(runDir, "selection_candidates.json"))
	if err != nil {
		return nil, err
	}
	selectionRowsAny, ok := selectionAny.([]any)
	if !ok {
		return nil, errors.New("selection payload is not an array")
	}
	rows := make([]map[string]any, 0)
	for _, item := range selectionRowsAny {
		row, ok := item.(map[string]any)
		if !ok {
			continue
		}
		if fmt.Sprint(row["trade_date"]) == tradeDate {
			rows = append(rows, row)
		}
	}
	sort.Slice(rows, func(i, j int) bool {
		return toFloat(rows[i]["total_score"]) > toFloat(rows[j]["total_score"])
	})
	if topN < len(rows) {
		rows = rows[:topN]
	}
	return rows, nil
}

func toFloat(value any) float64 {
	switch typed := value.(type) {
	case float64:
		return typed
	case float32:
		return float64(typed)
	case int:
		return float64(typed)
	case int64:
		return float64(typed)
	case json.Number:
		result, _ := typed.Float64()
		return result
	case string:
		result, _ := strconv.ParseFloat(typed, 64)
		return result
	default:
		return 0
	}
}

func normalizeUniverseID(value string) string {
	normalized := strings.ToUpper(strings.TrimSpace(value))
	switch normalized {
	case "ALL_A", "ALL_A_TRADABLE_HISTORY":
		return "ALL_A_TRADABLE"
	default:
		return normalized
	}
}

func (a *App) ensureCatalog(ctx context.Context) error {
	if _, err := os.Stat(a.config.CatalogPath); err == nil {
		return nil
	}
	command := exec.CommandContext(
		ctx,
		a.config.PythonExecutable,
		a.config.RegistrarScriptPath,
		"--formal-root",
		a.config.FormalRoot,
		"--catalog-path",
		a.config.CatalogPath,
	)
	command.Dir = a.config.RepoRoot
	output, err := command.CombinedOutput()
	if err != nil {
		return fmt.Errorf("failed to create DuckDB catalog: %w: %s", err, strings.TrimSpace(string(output)))
	}
	return nil
}

func openDuckDB(catalogPath string) (*sql.DB, error) {
	database, err := sql.Open("duckdb", catalogPath)
	if err != nil {
		return nil, err
	}
	return database, nil
}

func queryRows(database *sql.DB, query string, args ...any) ([]map[string]any, error) {
	rows, err := database.Query(query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	columns, err := rows.Columns()
	if err != nil {
		return nil, err
	}
	results := make([]map[string]any, 0)
	for rows.Next() {
		values := make([]any, len(columns))
		pointers := make([]any, len(columns))
		for index := range values {
			pointers[index] = &values[index]
		}
		if err := rows.Scan(pointers...); err != nil {
			return nil, err
		}
		entry := make(map[string]any, len(columns))
		for index, column := range columns {
			entry[column] = normalizeSQLValue(values[index])
		}
		results = append(results, entry)
	}
	return results, rows.Err()
}

func normalizeSQLValue(value any) any {
	switch typed := value.(type) {
	case []byte:
		return string(typed)
	case time.Time:
		return typed.Format("2006-01-02")
	default:
		return typed
	}
}

func (a *App) getFormalCoverage() (map[string]any, error) {
	if err := a.ensureCatalog(context.Background()); err != nil {
		return nil, err
	}
	database, err := openDuckDB(a.config.CatalogPath)
	if err != nil {
		return nil, err
	}
	defer database.Close()

	masterRows, err := queryRows(database, "SELECT row_count, stock_count, CAST(min_trade_date AS VARCHAR) AS min_trade_date, CAST(max_trade_date AS VARCHAR) AS max_trade_date FROM master.vw_shared_master_coverage")
	if err != nil {
		return nil, err
	}
	fullMasterRows, err := queryRows(database, "SELECT row_count, stock_count, CAST(min_trade_date AS VARCHAR) AS min_trade_date, CAST(max_trade_date AS VARCHAR) AS max_trade_date FROM full_master.coverage_summary")
	if err != nil {
		return nil, err
	}
	factorRows, err := queryRows(database, "SELECT universe_id, row_count, stock_count, CAST(min_trade_date AS VARCHAR) AS min_trade_date, CAST(max_trade_date AS VARCHAR) AS max_trade_date FROM factors.vw_factor_panel_coverage ORDER BY universe_id")
	if err != nil {
		return nil, err
	}
	financialRows, err := queryRows(database, "SELECT dataset_name, row_count, stock_count, min_query_year, max_query_year FROM financial.vw_financial_dataset_coverage ORDER BY dataset_name")
	if err != nil {
		return nil, err
	}
	reportRows, err := queryRows(database, "SELECT dataset_name, row_count, stock_count, min_query_year, max_query_year FROM reports.vw_report_dataset_coverage ORDER BY dataset_name")
	if err != nil {
		return nil, err
	}

	var master any
	if len(masterRows) > 0 {
		master = masterRows[0]
	}
	var fullMaster any
	if len(fullMasterRows) > 0 {
		fullMaster = fullMasterRows[0]
	}
	return map[string]any{
		"catalog_path": a.config.CatalogPath,
		"master":       master,
		"full_master":  fullMaster,
		"factors":      factorRows,
		"financial":    financialRows,
		"reports":      reportRows,
	}, nil
}

func (a *App) getUniverseMembersForDate(universeID string, tradeDate string) ([]map[string]any, error) {
	viewName, ok := universeViewByID[universeID]
	if !ok {
		return nil, fmt.Errorf("unknown universe: %s", universeID)
	}
	if err := a.ensureCatalog(context.Background()); err != nil {
		return nil, err
	}
	database, err := openDuckDB(a.config.CatalogPath)
	if err != nil {
		return nil, err
	}
	defer database.Close()
	query := fmt.Sprintf(
		"SELECT CAST(trade_date AS VARCHAR) AS trade_date, market_id, universe_id, stock_code, CAST(start_date AS VARCHAR) AS start_date, CAST(end_date AS VARCHAR) AS end_date FROM %s WHERE trade_date = CAST(? AS DATE) ORDER BY stock_code",
		viewName,
	)
	return queryRows(database, query, tradeDate)
}

func generateRunID() (string, error) {
	buffer := make([]byte, 6)
	if _, err := rand.Read(buffer); err != nil {
		return "", err
	}
	return hex.EncodeToString(buffer), nil
}

func (a *App) submitRun(payload map[string]any) (map[string]any, error) {
	runID, hasRunID := payload["run_id"]
	if hasRunID && runID != nil {
		runIDString, ok := runID.(string)
		if !ok {
			return nil, newValidationError("run_id 必须是字符串")
		}
		runID = runIDString
	}
	runIDString, _ := runID.(string)
	if strings.TrimSpace(runIDString) == "" {
		generated, err := generateRunID()
		if err != nil {
			return nil, err
		}
		runIDString = generated
	}
	safeRunID, err := validateRunID(runIDString)
	if err != nil {
		return nil, err
	}
	baseConfigPath, err := a.resolveRequestedConfig(payload)
	if err != nil {
		return nil, err
	}
	if value, exists := payload["selection_top_n"]; exists && value != nil {
		parsed, err := coercePositiveInt(value, "selection_top_n")
		if err != nil {
			return nil, err
		}
		payload["selection_top_n"] = parsed
	}
	runDir, err := a.resolveRunDir(safeRunID, true)
	if err != nil {
		return nil, err
	}
	if err := os.MkdirAll(runDir, 0o755); err != nil {
		return nil, err
	}

	configPath, err := a.buildRunConfig(safeRunID, runDir, baseConfigPath, payload)
	if err != nil {
		return nil, err
	}

	status := a.updateStatus(runDir, "queued", map[string]any{
		"run_id":      safeRunID,
		"config_path": repoRelativePath(a.config.RepoRoot, configPath),
	})

	runSync, _ := payload["run_sync"].(bool)
	if runSync {
		a.executeRun(safeRunID, runDir, configPath)
	} else {
		go a.executeRun(safeRunID, runDir, configPath)
	}
	return status, nil
}

func (a *App) executeRun(runID string, runDir string, configPath string) {
	a.updateStatus(runDir, "running", map[string]any{})
	command := exec.Command(a.config.PythonExecutable, a.config.RunnerScriptPath, "--config", configPath)
	command.Dir = a.config.RepoRoot
	output, err := command.CombinedOutput()
	if err != nil {
		errorMessage := strings.TrimSpace(string(output))
		if errorMessage == "" {
			errorMessage = err.Error()
		}
		a.updateStatus(runDir, "failed", map[string]any{
			"error":      errorMessage,
			"output_dir": repoRelativePath(a.config.RepoRoot, runDir),
		})
		return
	}

	extra := map[string]any{
		"output_dir": repoRelativePath(a.config.RepoRoot, runDir),
		"runner_log": strings.TrimSpace(string(output)),
	}
	if manifestAny, err := readJSONFile(filepath.Join(runDir, "run_manifest.json")); err == nil {
		if manifest, ok := manifestAny.(map[string]any); ok {
			if models, ok := manifest["models"]; ok {
				extra["models"] = models
			}
		}
	}
	a.updateStatus(runDir, "completed", extra)
}

func (a *App) resolveRequestedConfig(payload map[string]any) (string, error) {
	configProfile, _ := payload["config_profile"].(string)
	marketID, _ := payload["market_id"].(string)
	universeID, _ := payload["universe_id"].(string)
	if rawConfigPath, exists := payload["config_path"]; exists && rawConfigPath != nil {
		configPath, ok := rawConfigPath.(string)
		if !ok {
			return "", newValidationError("config_path 必须是字符串")
		}
		if strings.TrimSpace(configPath) != "" {
			return a.resolveRequestedConfigPath(configPath)
		}
	}
	profiles := map[string]string{
		"formal_hs300":     filepath.Join(a.config.RepoRoot, "code", "configs", "formal_hs300.yaml"),
		"formal_sz50":      filepath.Join(a.config.RepoRoot, "code", "configs", "formal_sz50.yaml"),
		"formal_zz500":     filepath.Join(a.config.RepoRoot, "code", "configs", "formal_zz500.yaml"),
		"sample_cn_smoke":  filepath.Join(a.config.RepoRoot, "code", "configs", "sample_cn_smoke.yaml"),
		"sample_us_equity": filepath.Join(a.config.RepoRoot, "code", "configs", "sample_us_equity.yaml"),
	}
	if resolved, ok := profiles[configProfile]; ok {
		return resolved, nil
	}
	if marketID == "cn_a" && universeID == "HS300" {
		return profiles["formal_hs300"], nil
	}
	if marketID == "cn_a" && universeID == "SZ50" {
		return profiles["formal_sz50"], nil
	}
	if marketID == "cn_a" && universeID == "ZZ500" {
		return profiles["formal_zz500"], nil
	}
	if marketID == "us_equity" {
		return profiles["sample_us_equity"], nil
	}
	if marketID == "cn_a" {
		return a.config.DefaultConfigPath, nil
	}
	return a.config.DefaultConfigPath, nil
}

func coerceStringMap(value any) map[string]any {
	if value == nil {
		return map[string]any{}
	}
	if typed, ok := value.(map[string]any); ok {
		return typed
	}
	result := map[string]any{}
	if typed, ok := value.(map[any]any); ok {
		for key, item := range typed {
			result[fmt.Sprint(key)] = item
		}
	}
	return result
}

func convertArray(value any) []any {
	if value == nil {
		return nil
	}
	if typed, ok := value.([]any); ok {
		return typed
	}
	return nil
}

func (a *App) buildRunConfig(runID string, runDir string, baseConfigPath string, payload map[string]any) (string, error) {
	content, err := os.ReadFile(baseConfigPath)
	if err != nil {
		return "", err
	}
	var config map[string]any
	if err := yaml.Unmarshal(content, &config); err != nil {
		return "", err
	}

	baseDir := filepath.Dir(baseConfigPath)
	market := coerceStringMap(config["market"])
	data := coerceStringMap(config["data"])
	evaluation := coerceStringMap(config["evaluation"])
	runtime := coerceStringMap(config["runtime"])
	models := coerceStringMap(config["models"])
	output := coerceStringMap(config["output"])

	if pathValue, ok := data["path"].(string); ok && pathValue != "" {
		data["path"] = pathRelativeTo(runDir, filepath.Clean(filepath.Join(baseDir, pathValue)))
	}
	if universePath, ok := market["universe_path"].(string); ok && universePath != "" {
		market["universe_path"] = pathRelativeTo(runDir, filepath.Clean(filepath.Join(baseDir, universePath)))
	}
	output["root_dir"] = pathRelativeTo(runDir, filepath.Dir(runDir))
	output["experiment_name"] = runID

	configProfile, _ := payload["config_profile"].(string)
	if !strings.HasPrefix(configProfile, "formal_") {
		for _, key := range []string{"market_id", "universe_id", "start_date", "end_date"} {
			if value, exists := payload[key]; exists && value != nil {
				market[key] = value
			}
		}
	}
	if value, exists := payload["top_k_pairs"]; exists && value != nil {
		evaluation["top_k_pairs"] = value
	}
	if value, exists := payload["selection_top_n"]; exists && value != nil {
		parsed, err := coercePositiveInt(value, "selection_top_n")
		if err != nil {
			return "", err
		}
		runtime["selection_top_n"] = parsed
	}
	if enabledMap := coerceStringMap(payload["models_enabled"]); len(enabledMap) > 0 {
		for modelName, enabled := range enabledMap {
			modelConfig := coerceStringMap(models[modelName])
			if len(modelConfig) == 0 {
				continue
			}
			modelConfig["enabled"] = enabled
			models[modelName] = modelConfig
		}
	}
	if rankMap := coerceStringMap(payload["model_ranks"]); len(rankMap) > 0 {
		for modelName, ranks := range rankMap {
			modelConfig := coerceStringMap(models[modelName])
			if len(modelConfig) == 0 {
				continue
			}
			modelConfig["ranks"] = ranks
			models[modelName] = modelConfig
		}
	}

	config["market"] = market
	config["data"] = data
	config["evaluation"] = evaluation
	config["runtime"] = runtime
	config["models"] = models
	config["output"] = output

	submittedConfigPath := filepath.Join(runDir, "submitted_config.yaml")
	rendered, err := yaml.Marshal(config)
	if err != nil {
		return "", err
	}
	if err := os.WriteFile(submittedConfigPath, rendered, 0o644); err != nil {
		return "", err
	}
	return submittedConfigPath, nil
}
