package backend

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func writeTextFile(t *testing.T, path string, content string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatalf("mkdir failed: %v", err)
	}
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatalf("write failed: %v", err)
	}
}

func readJSONResponse(t *testing.T, recorder *httptest.ResponseRecorder, target any) {
	t.Helper()
	if err := json.Unmarshal(recorder.Body.Bytes(), target); err != nil {
		t.Fatalf("failed to decode json: %v", err)
	}
}

func realRepoRoot(t *testing.T) string {
	t.Helper()
	workingDir, err := os.Getwd()
	if err != nil {
		t.Fatalf("failed to get working directory: %v", err)
	}
	return filepath.Clean(filepath.Join(workingDir, "..", "..", "..", ".."))
}

func TestReadOnlyRoutes(t *testing.T) {
	root := t.TempDir()
	actualRepoRoot := realRepoRoot(t)
	formalRoot := filepath.Join(root, "formal")
	outputRoot := filepath.Join(root, "outputs")
	catalogPath := filepath.Join(formalRoot, "catalog.duckdb")
	defaultConfigPath := filepath.Join(root, "configs", "default.yaml")

	writeTextFile(t, filepath.Join(formalRoot, "universes", "hs300_history.csv"), "market_id,universe_id,stock_code,start_date,end_date\ncn_a,HS300,600000.SH,2026-03-02,2026-03-03\n")
	writeTextFile(t, filepath.Join(formalRoot, "factors", "hs300_factor_panel.csv"), "stock_code,trade_date,industry,value_factor,momentum_factor,quality_factor,volatility_factor,future_return\n600000.SH,2026-03-02,Bank,1,2,3,4,0.1\n600000.SH,2026-03-03,Bank,1,2,3,4,0.2\n")
	writeTextFile(t, filepath.Join(formalRoot, "master", "shared_kline_panel.csv"), "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST\n2026-03-02,sh.600000,10,11,9,10,9.8,100,1000,3,0.2,1,2.0,6.4,0.45,1.85,-1.52,0\n2026-03-03,sh.600000,10,11,9,10,9.8,100,1000,3,0.2,1,2.0,6.4,0.45,1.85,-1.52,0\n")
	writeTextFile(t, filepath.Join(formalRoot, "master", "full_master_2026.csv"), "date,code,open,high,low,close,preclose,volume,amount,adjustflag,pctChg,source_price_vendor,source_file,turn,tradestatus,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST\n2026-03-02,sh.600000,10,11,9,10,9.8,100,1000,2,2.0,tongdaxin,a.day,0.2,1,6.4,0.45,1.85,-1.52,0\n2026-03-03,sh.600000,10,11,9,10,9.8,100,1000,2,2.0,tongdaxin,a.day,0.2,1,6.4,0.45,1.85,-1.52,0\n")
	writeTextFile(t, filepath.Join(formalRoot, "baostock", "financial", "profit_data", "2025.csv"), "code,pubDate,statDate,dataset,query_year,query_quarter\nsh.600000,2025-04-30,2025-03-31,profit_data,2025,1\n")
	writeTextFile(t, filepath.Join(formalRoot, "baostock", "reports", "forecast_report", "2025.csv"), "code,profitForcastExpPubDate,profitForcastExpStatDate,dataset,query_year\nsh.600000,2025-01-21,2024-12-31,forecast_report,2025\n")

	runDir := filepath.Join(outputRoot, "go_read_run")
	writeTextFile(t, filepath.Join(runDir, "run_status.json"), `{"run_id":"go_read_run","status":"completed","created_at":"x","updated_at":"x"}`)
	writeTextFile(t, filepath.Join(runDir, "run_manifest.json"), `{"market_id":"cn_a","universe_id":"HS300","selection_top_n":2}`)
	writeTextFile(t, filepath.Join(runDir, "metrics.json"), `[{"model":"cp","rank":"2","mse":0.1,"explained_variance":0.9}]`)
	writeTextFile(t, filepath.Join(runDir, "selection_candidates.json"), `[{"trade_date":"2026-01-09","stock_code":"600000.SH","total_score":0.9,"model_count":3,"cluster_label":"A","top_factor_1":"value","time_regime_score":0.3},{"trade_date":"2026-01-09","stock_code":"600009.SH","total_score":0.8,"model_count":2,"cluster_label":"B","top_factor_1":"momentum","time_regime_score":0.2}]`)
	writeTextFile(t, filepath.Join(runDir, "factor_summary_cp.json"), `[{"factor_name":"value","importance":0.8}]`)
	writeTextFile(t, filepath.Join(runDir, "factor_association_cp.json"), `[{"left":"value","right":"momentum","score":0.7}]`)
	writeTextFile(t, filepath.Join(runDir, "time_regimes_cp.json"), `[{"from":"2026-01-08","to":"2026-01-09","shift_score":0.6}]`)
	writeTextFile(t, defaultConfigPath, "market:\n  market_id: cn_a\n  universe_id: CSI_A500\n  start_date: 2025-01-01\n  end_date: 2026-01-31\n  timezone: Asia/Shanghai\n  currency: CNY\ndata:\n  path: ../data/sample.csv\n  format: wide\n  stock_column: stock_code\n  date_column: trade_date\n  factor_columns: [value_factor]\npreprocess:\n  max_missing_ratio: 0.5\n  winsor_limits: [0.05, 0.95]\nmodels:\n  seed: 7\n  cp:\n    enabled: true\n    ranks: [2]\n    max_iter: 5\n    tol: 1.0e-6\n  tucker:\n    enabled: false\n    ranks: [[2,2,2]]\n    max_iter: 5\n    tol: 1.0e-6\n  pca:\n    enabled: false\n    ranks: [2]\nevaluation:\n  top_k_pairs: 5\n  rolling_window: 3\nruntime:\n  selection_top_n: 20\noutput:\n  root_dir: ../outputs\n  experiment_name: default_run\n")

	handler, err := NewHandler(Config{
		RepoRoot:            root,
		OutputRoot:          outputRoot,
		FormalRoot:          formalRoot,
		CatalogPath:         catalogPath,
		DefaultConfigPath:   defaultConfigPath,
		PythonExecutable:    "python",
		RunnerScriptPath:    filepath.Join(root, "runner.py"),
		RegistrarScriptPath: filepath.Join(actualRepoRoot, "code", "data", "register_formal_duckdb_catalog.py"),
	})
	if err != nil {
		t.Fatalf("new handler failed: %v", err)
	}

	recorder := httptest.NewRecorder()
	request := httptest.NewRequest(http.MethodGet, "/api/markets", nil)
	handler.ServeHTTP(recorder, request)
	if recorder.Code != http.StatusOK {
		t.Fatalf("expected 200 for markets, got %d", recorder.Code)
	}

	recorder = httptest.NewRecorder()
	request = httptest.NewRequest(http.MethodGet, "/api/formal/coverage", nil)
	handler.ServeHTTP(recorder, request)
	if recorder.Code != http.StatusOK {
		t.Fatalf("expected 200 for formal coverage, got %d: %s", recorder.Code, recorder.Body.String())
	}
	var coveragePayload map[string]any
	readJSONResponse(t, recorder, &coveragePayload)
	if coveragePayload["catalog_path"] == nil {
		t.Fatalf("expected catalog_path in coverage payload")
	}

	recorder = httptest.NewRecorder()
	request = httptest.NewRequest(http.MethodGet, "/api/formal/universes/HS300?trade_date=2026-03-02", nil)
	handler.ServeHTTP(recorder, request)
	if recorder.Code != http.StatusOK {
		t.Fatalf("expected 200 for universe members, got %d", recorder.Code)
	}
	var universePayload []map[string]any
	readJSONResponse(t, recorder, &universePayload)
	if len(universePayload) != 1 || universePayload[0]["stock_code"] != "600000.SH" {
		t.Fatalf("unexpected universe payload: %#v", universePayload)
	}

	recorder = httptest.NewRecorder()
	request = httptest.NewRequest(http.MethodGet, "/api/runs", nil)
	handler.ServeHTTP(recorder, request)
	if recorder.Code != http.StatusOK {
		t.Fatalf("expected 200 for runs list, got %d", recorder.Code)
	}
	var runsPayload []map[string]any
	readJSONResponse(t, recorder, &runsPayload)
	if len(runsPayload) != 1 {
		t.Fatalf("expected one run, got %#v", runsPayload)
	}

	recorder = httptest.NewRecorder()
	request = httptest.NewRequest(http.MethodGet, "/api/runs/go_read_run", nil)
	handler.ServeHTTP(recorder, request)
	if recorder.Code != http.StatusOK {
		t.Fatalf("expected 200 for run detail, got %d", recorder.Code)
	}

	recorder = httptest.NewRecorder()
	request = httptest.NewRequest(http.MethodGet, "/api/runs/go_read_run/metrics", nil)
	handler.ServeHTTP(recorder, request)
	if recorder.Code != http.StatusOK {
		t.Fatalf("expected 200 for metrics, got %d", recorder.Code)
	}

	recorder = httptest.NewRecorder()
	request = httptest.NewRequest(http.MethodGet, "/api/runs/go_read_run/selection?trade_date=2026-01-09&top_n=1", nil)
	handler.ServeHTTP(recorder, request)
	if recorder.Code != http.StatusOK {
		t.Fatalf("expected 200 for selection, got %d", recorder.Code)
	}
	var selectionPayload []map[string]any
	readJSONResponse(t, recorder, &selectionPayload)
	if len(selectionPayload) != 1 || selectionPayload[0]["stock_code"] != "600000.SH" {
		t.Fatalf("unexpected selection payload: %#v", selectionPayload)
	}
}

func TestCreateRunRoute(t *testing.T) {
	root := t.TempDir()
	actualRepoRoot := realRepoRoot(t)
	formalRoot := filepath.Join(root, "formal")
	outputRoot := filepath.Join(root, "outputs")
	defaultConfigPath := filepath.Join(root, "configs", "default.yaml")
	runnerScriptPath := filepath.Join(root, "fake_runner.py")

	writeTextFile(t, filepath.Join(root, "data", "sample.csv"), "stock_code,trade_date,value_factor\n600000.SH,2026-01-09,1.0\n")
	writeTextFile(t, filepath.Join(root, "data", "sample_history.csv"), "market_id,universe_id,stock_code,start_date,end_date\ncn_a,CSI_A500,600000.SH,2026-01-01,2026-01-31\n")
	writeTextFile(t, defaultConfigPath, "market:\n  market_id: cn_a\n  universe_id: CSI_A500\n  start_date: 2025-01-01\n  end_date: 2026-01-31\n  timezone: Asia/Shanghai\n  currency: CNY\n  universe_path: ../data/sample_history.csv\n  universe_symbol_column: stock_code\n  universe_start_column: start_date\n  universe_end_column: end_date\n  universe_market_column: market_id\n  universe_id_column: universe_id\ndata:\n  path: ../data/sample.csv\n  format: wide\n  stock_column: stock_code\n  date_column: trade_date\n  factor_columns: [value_factor]\npreprocess:\n  max_missing_ratio: 0.5\n  winsor_limits: [0.05, 0.95]\nmodels:\n  seed: 7\n  cp:\n    enabled: true\n    ranks: [2]\n    max_iter: 5\n    tol: 1.0e-6\n  tucker:\n    enabled: false\n    ranks: [[2,2,2]]\n    max_iter: 5\n    tol: 1.0e-6\n  pca:\n    enabled: false\n    ranks: [2]\nevaluation:\n  top_k_pairs: 5\n  rolling_window: 3\nruntime:\n  selection_top_n: 20\noutput:\n  root_dir: ../outputs\n  experiment_name: default_run\n")
	writeTextFile(t, filepath.Join(root, "code", "configs", "sample_us_equity.yaml"), "market:\n  market_id: us_equity\n  universe_id: EXTERNAL_LIST\n  start_date: 2025-01-01\n  end_date: 2026-01-31\n  timezone: America/New_York\n  currency: USD\ndata:\n  path: ../../data/sample.csv\n  format: wide\n  stock_column: stock_code\n  date_column: trade_date\n  factor_columns: [value_factor]\npreprocess:\n  max_missing_ratio: 0.5\n  winsor_limits: [0.05, 0.95]\nmodels:\n  seed: 7\n  cp:\n    enabled: true\n    ranks: [2]\n    max_iter: 5\n    tol: 1.0e-6\n  tucker:\n    enabled: false\n    ranks: [[2,2,2]]\n    max_iter: 5\n    tol: 1.0e-6\n  pca:\n    enabled: true\n    ranks: [2]\nevaluation:\n  top_k_pairs: 5\n  rolling_window: 3\nruntime:\n  selection_top_n: 20\noutput:\n  root_dir: ../../outputs\n  experiment_name: sample_us_run\n")
	writeTextFile(t, runnerScriptPath, "import argparse, json\nfrom pathlib import Path\nimport yaml\nparser = argparse.ArgumentParser()\nparser.add_argument('--config', required=True)\nargs = parser.parse_args()\nconfig_path = Path(args.config)\nconfig = yaml.safe_load(config_path.read_text(encoding='utf-8'))\noutput_root = (config_path.parent / config['output']['root_dir']).resolve()\nrun_dir = output_root / config['output']['experiment_name']\nrun_dir.mkdir(parents=True, exist_ok=True)\n(run_dir / 'run_manifest.json').write_text(json.dumps({'market_id': config['market']['market_id'], 'universe_id': config['market']['universe_id'], 'selection_top_n': config['runtime']['selection_top_n']}), encoding='utf-8')\n(run_dir / 'metrics.json').write_text(json.dumps([{'model': 'cp', 'rank': '2', 'mse': 0.1, 'explained_variance': 0.9}]), encoding='utf-8')\n(run_dir / 'selection_candidates.json').write_text(json.dumps([{'trade_date': '2026-01-09', 'stock_code': '600000.SH', 'total_score': 0.9, 'model_count': 1, 'cluster_label': 'A', 'top_factor_1': 'value', 'time_regime_score': 0.3}]), encoding='utf-8')\n")

	handler, err := NewHandler(Config{
		RepoRoot:            root,
		OutputRoot:          outputRoot,
		FormalRoot:          formalRoot,
		CatalogPath:         filepath.Join(formalRoot, "catalog.duckdb"),
		DefaultConfigPath:   defaultConfigPath,
		PythonExecutable:    "python",
		RunnerScriptPath:    runnerScriptPath,
		RegistrarScriptPath: filepath.Join(actualRepoRoot, "code", "data", "register_formal_duckdb_catalog.py"),
	})
	if err != nil {
		t.Fatalf("new handler failed: %v", err)
	}

	requestBody, err := json.Marshal(map[string]any{
		"run_id":           "go_submit_run",
		"run_sync":         false,
		"market_id":        "us_equity",
		"selection_top_n":  7,
		"models_enabled":   map[string]any{"cp": true, "tucker": false, "pca": true},
		"model_ranks":      map[string]any{"cp": []any{2}, "pca": []any{2}},
	})
	if err != nil {
		t.Fatalf("marshal body failed: %v", err)
	}

	recorder := httptest.NewRecorder()
	request := httptest.NewRequest(http.MethodPost, "/api/runs", bytes.NewReader(requestBody))
	request.Header.Set("Content-Type", "application/json")
	handler.ServeHTTP(recorder, request)
	if recorder.Code != http.StatusOK {
		t.Fatalf("expected 200 for create run, got %d: %s", recorder.Code, recorder.Body.String())
	}

	submittedConfigPath := filepath.Join(outputRoot, "go_submit_run", "submitted_config.yaml")
	deadline := time.Now().Add(10 * time.Second)
	for time.Now().Before(deadline) {
		if _, err := os.Stat(filepath.Join(outputRoot, "go_submit_run", "run_manifest.json")); err == nil {
			break
		}
		time.Sleep(100 * time.Millisecond)
	}

	if _, err := os.Stat(submittedConfigPath); err != nil {
		t.Fatalf("submitted config was not written: %v", err)
	}

	recorder = httptest.NewRecorder()
	request = httptest.NewRequest(http.MethodGet, "/api/runs/go_submit_run", nil)
	handler.ServeHTTP(recorder, request)
	if recorder.Code != http.StatusOK {
		t.Fatalf("expected 200 for submitted run detail, got %d", recorder.Code)
	}
	var detailPayload map[string]any
	readJSONResponse(t, recorder, &detailPayload)
	statusPayload, ok := detailPayload["status"].(map[string]any)
	if !ok || statusPayload["status"] != "completed" {
		t.Fatalf("expected completed status, got %#v", detailPayload["status"])
	}
}
