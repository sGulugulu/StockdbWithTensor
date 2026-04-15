import React, { useEffect, useState } from "react";
import FormalDataPanel from "./components/FormalDataPanel.jsx";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8080";

export default function App() {
  const [view, setView] = useState("config");
  const [markets, setMarkets] = useState([]);
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [selectionRows, setSelectionRows] = useState([]);
  const [detail, setDetail] = useState(null);
  const [submitError, setSubmitError] = useState("");
  const [tradeDate, setTradeDate] = useState("2026-01-09");
  const [configForm, setConfigForm] = useState({
    option_id: "formal_hs300",
    config_profile: "formal_hs300",
    market_id: "cn_a",
    universe_id: "HS300",
    start_date: "2015-01-01",
    end_date: "2026-12-31",
    selection_top_n: 20,
    models_enabled: {
      cp: true,
      tucker: true,
      pca: true
    },
    model_ranks: {
      cp: "2,3",
      tucker: "2x2x2;3x2x2",
      pca: "2,3"
    }
  });

  async function refreshRuns() {
    const response = await fetch(`${API_BASE}/api/runs`);
    const data = await response.json();
    setRuns(data);
    if (data.length && !selectedRun) {
      setSelectedRun(data[0].run_id);
    }
  }

  useEffect(() => {
    fetch(`${API_BASE}/api/markets`)
      .then((response) => response.json())
      .then((data) => {
        setMarkets(data);
        const selectedMarket = data.find((market) => market.option_id === configForm.option_id);
        if (selectedMarket) {
          setConfigForm((current) => ({
            ...current,
            config_profile: selectedMarket.config_profile,
            market_id: selectedMarket.market_id,
            universe_id: selectedMarket.universe_id
          }));
        }
      })
      .catch(() => setMarkets([]));
    refreshRuns().catch(() => setRuns([]));
  }, []);

  useEffect(() => {
    if (!selectedRun) {
      setSelectionRows([]);
      setDetail(null);
      return;
    }
    fetch(`${API_BASE}/api/runs/${selectedRun}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error("run-detail-failed");
        }
        return response.json();
      })
      .then((data) => {
        setDetail(data);
        const queryTopN = data.manifest?.selection_top_n ?? configForm.selection_top_n;
        return fetch(`${API_BASE}/api/runs/${selectedRun}/selection?trade_date=${tradeDate}&top_n=${queryTopN}`);
      })
      .then((response) => {
        if (!response.ok) {
          return [];
        }
        return response.json();
      })
      .then(setSelectionRows)
      .catch(() => {
        setDetail(null);
        setSelectionRows([]);
      });
  }, [selectedRun, tradeDate, configForm.selection_top_n]);

  async function createRun() {
    setSubmitError("");
    const response = await fetch(`${API_BASE}/api/runs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        run_sync: false,
        config_profile: configForm.config_profile,
        market_id: configForm.market_id,
        universe_id: configForm.universe_id,
        start_date: configForm.start_date,
        end_date: configForm.end_date,
        selection_top_n: configForm.selection_top_n,
        models_enabled: configForm.models_enabled,
        model_ranks: {
          cp: configForm.model_ranks.cp.split(",").map((item) => Number(item.trim())).filter(Boolean),
          tucker: configForm.model_ranks.tucker
            .split(";")
            .map((item) => item.split("x").map((part) => Number(part.trim())).filter(Boolean))
            .filter((item) => item.length === 3),
          pca: configForm.model_ranks.pca.split(",").map((item) => Number(item.trim())).filter(Boolean)
        }
      })
    });
    if (!response.ok) {
      let detail = "启动实验失败，请检查配置后重试。";
      try {
        const payload = await response.json();
        if (payload?.detail) {
          detail = String(payload.detail);
        }
      } catch {
        // 保持默认错误提示。
      }
      setSubmitError(detail);
      return;
    }
    setView("runs");
    await refreshRuns();
  }

  return (
    <div className="page">
      <section className="panel hero">
        <div>
          <p className="eyebrow">Tensor Factor Lab</p>
          <h1>股票因子降维与选股实验面板</h1>
          <p className="lead">
            面向 A 股与美股扩展的实验入口，提供市场选择、实验列表和候选股浏览。
          </p>
        </div>
        <button onClick={() => createRun()}>启动默认实验</button>
      </section>

      <section className="tabs">
        <button className={view === "config" ? "tab active" : "tab"} onClick={() => setView("config")}>实验配置页</button>
        <button className={view === "runs" ? "tab active" : "tab"} onClick={() => setView("runs")}>实验列表页</button>
        <button className={view === "detail" ? "tab active" : "tab"} onClick={() => setView("detail")}>实验详情页</button>
        <button className={view === "selection" ? "tab active" : "tab"} onClick={() => setView("selection")}>选股结果页</button>
        <button className={view === "formal" ? "tab active" : "tab"} onClick={() => setView("formal")}>Formal 数据页</button>
      </section>

      <section className="grid">
        {view === "config" && <div className="panel">
          <h2>实验配置</h2>
          <label>
            股票池模板
            <select
              value={configForm.option_id}
              onChange={(event) => {
                const selectedMarket = markets.find((market) => market.option_id === event.target.value);
                if (!selectedMarket) {
                  return;
                }
                setConfigForm((current) => ({
                  ...current,
                  option_id: selectedMarket.option_id,
                  config_profile: selectedMarket.config_profile,
                  market_id: selectedMarket.market_id,
                  universe_id: selectedMarket.universe_id
                }));
              }}
            >
              {markets.map((market) => (
                <option key={market.option_id} value={market.option_id}>
                  {market.market_name}
                </option>
              ))}
            </select>
          </label>
          <label>
            股票池
            <input
              value={configForm.universe_id}
              onChange={(event) => setConfigForm((current) => ({ ...current, universe_id: event.target.value }))}
              disabled={configForm.config_profile.startsWith("formal_")}
            />
          </label>
          <label>
            开始日期
            <input
              type="date"
              value={configForm.start_date}
              onChange={(event) => setConfigForm((current) => ({ ...current, start_date: event.target.value }))}
            />
          </label>
          <label>
            结束日期
            <input
              type="date"
              value={configForm.end_date}
              onChange={(event) => setConfigForm((current) => ({ ...current, end_date: event.target.value }))}
            />
          </label>
          <label>
            候选股 Top N
            <input
              type="number"
              min="1"
              value={configForm.selection_top_n}
              onChange={(event) =>
                setConfigForm((current) => {
                  if (event.target.value === "") {
                    return current;
                  }
                  return { ...current, selection_top_n: Number(event.target.value) };
                })
              }
            />
          </label>
          {submitError ? <p className="error-text">{submitError}</p> : null}
          <label>
            模型选择
            <div className="checkbox-group">
              {["cp", "tucker", "pca"].map((modelName) => (
                <label key={modelName} className="inline-check">
                  <input
                    type="checkbox"
                    checked={configForm.models_enabled[modelName]}
                    onChange={(event) =>
                      setConfigForm((current) => ({
                        ...current,
                        models_enabled: {
                          ...current.models_enabled,
                          [modelName]: event.target.checked
                        }
                      }))
                    }
                  />
                  {modelName}
                </label>
              ))}
            </div>
          </label>
          <label>
            CP 秩
            <input
              value={configForm.model_ranks.cp}
              onChange={(event) =>
                setConfigForm((current) => ({
                  ...current,
                  model_ranks: { ...current.model_ranks, cp: event.target.value }
                }))
              }
            />
          </label>
          <label>
            Tucker 秩
            <input
              value={configForm.model_ranks.tucker}
              onChange={(event) =>
                setConfigForm((current) => ({
                  ...current,
                  model_ranks: { ...current.model_ranks, tucker: event.target.value }
                }))
              }
            />
          </label>
          <label>
            PCA 秩
            <input
              value={configForm.model_ranks.pca}
              onChange={(event) =>
                setConfigForm((current) => ({
                  ...current,
                  model_ranks: { ...current.model_ranks, pca: event.target.value }
                }))
              }
            />
          </label>
        </div>}

        {view === "runs" && <div className="panel wide">
          <h2>实验列表</h2>
          <ul className="run-list">
            {runs.map((run) => (
              <li key={run.run_id}>
                <button
                  className={selectedRun === run.run_id ? "active" : ""}
                  onClick={() => {
                    setSelectedRun(run.run_id);
                    setView("detail");
                  }}
                >
                  {run.run_id} / {run.status.status}
                </button>
              </li>
            ))}
          </ul>
        </div>}

        {view === "detail" && <div className="panel wide">
          <h2>实验详情</h2>
          {detail ? (
            <div className="detail-grid">
              <div>
                <strong>状态</strong>
                <p>{detail.status.status}</p>
              </div>
              <div>
                <strong>市场</strong>
                <p>{detail.manifest?.market_id ?? "-"}</p>
              </div>
              <div>
                <strong>股票池</strong>
                <p>{detail.manifest?.universe_id ?? "-"}</p>
              </div>
              <div>
                <strong>候选池大小</strong>
                <p>{detail.manifest?.candidate_pool_size ?? "-"}</p>
              </div>
              <div>
                <strong>候选股 Top N</strong>
                <p>{detail.manifest?.selection_top_n ?? "-"}</p>
              </div>
            </div>
          ) : (
            <p>请选择一个实验查看详情。</p>
          )}
          {detail?.metrics?.length ? (
            <table className="metrics-table">
              <thead>
                <tr>
                  <th>模型</th>
                  <th>秩</th>
                  <th>MSE</th>
                  <th>Explained Variance</th>
                </tr>
              </thead>
              <tbody>
                {detail.metrics.map((row) => (
                  <tr key={`${row.model}-${row.rank}`}>
                    <td>{row.model}</td>
                    <td>{row.rank}</td>
                    <td>{Number(row.mse).toFixed(6)}</td>
                    <td>{Number(row.explained_variance).toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
          {detail?.factor_summaries ? (
            <div className="detail-sections">
              {Object.entries(detail.factor_summaries).map(([modelName, rows]) => (
                <div key={modelName}>
                  <strong>{modelName} 因子摘要</strong>
                  <ul>
                    {rows.slice(0, 3).map((row) => (
                      <li key={`${modelName}-${row.factor_name}`}>{row.factor_name}: {Number(row.importance).toFixed(4)}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          ) : null}
          {detail?.factor_associations ? (
            <div className="detail-sections">
              {Object.entries(detail.factor_associations).map(([modelName, rows]) => (
                <div key={modelName}>
                  <strong>{modelName} 因子关系</strong>
                  <ul>
                    {rows.slice(0, 3).map((row) => (
                      <li key={`${modelName}-${row.left}-${row.right}`}>{row.left} / {row.right}: {Number(row.score).toFixed(4)}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          ) : null}
          {detail?.time_regimes ? (
            <div className="detail-sections">
              {Object.entries(detail.time_regimes).map(([modelName, rows]) => (
                <div key={modelName}>
                    <strong>{modelName} 时间阶段</strong>
                  <ul>
                    {rows.slice(0, 3).map((row) => (
                      <li key={`${modelName}-${row.from}-${row.to}`}>{row.from} {"->"} {row.to}: {Number(row.shift_score).toFixed(4)}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          ) : null}
        </div>}

        {view === "selection" && <div className="panel wide">
          <div className="toolbar">
            <h2>选股结果</h2>
            <input type="date" value={tradeDate} onChange={(event) => setTradeDate(event.target.value)} />
          </div>
          {selectionRows.length ? <table>
            <thead>
              <tr>
                <th>股票</th>
                <th>总分</th>
                <th>市场状态分</th>
                <th>簇</th>
                <th>模型数</th>
                <th>主要因子</th>
              </tr>
            </thead>
            <tbody>
              {selectionRows.map((row) => (
                <tr key={`${row.stock_code}-${row.trade_date}`}>
                  <td>{row.stock_code}</td>
                  <td>{Number(row.total_score).toFixed(4)}</td>
                  <td>{Number(row.time_regime_score).toFixed(4)}</td>
                  <td>{row.cluster_label}</td>
                  <td>{row.model_count}</td>
                  <td>{row.top_factor_1}</td>
                </tr>
              ))}
            </tbody>
          </table> : <p>当前运行尚未生成候选股，或结果仍在处理中。</p>}
        </div>}

        {view === "formal" && <FormalDataPanel apiBase={API_BASE} />}
      </section>
    </div>
  );
}
