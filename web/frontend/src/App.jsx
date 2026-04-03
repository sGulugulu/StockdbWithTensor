import React, { useEffect, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

export default function App() {
  const [view, setView] = useState("config");
  const [markets, setMarkets] = useState([]);
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [selectionRows, setSelectionRows] = useState([]);
  const [detail, setDetail] = useState(null);
  const [tradeDate, setTradeDate] = useState("2026-01-09");
  const [configForm, setConfigForm] = useState({
    market_id: "cn_a",
    universe_id: "CSI_A500",
    start_date: "2015-01-01",
    end_date: "2026-12-31",
    top_n: 20
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
      .then(setMarkets)
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
      .then((response) => response.json())
      .then(setDetail)
      .catch(() => setDetail(null));
    fetch(`${API_BASE}/api/runs/${selectedRun}/selection?trade_date=${tradeDate}&top_n=20`)
      .then((response) => response.json())
      .then(setSelectionRows)
      .catch(() => setSelectionRows([]));
  }, [selectedRun, tradeDate]);

  async function createRun() {
    await fetch(`${API_BASE}/api/runs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        run_sync: false,
        market_id: configForm.market_id,
        universe_id: configForm.universe_id,
        start_date: configForm.start_date,
        end_date: configForm.end_date,
        top_n: configForm.top_n
      })
    });
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
      </section>

      <section className="grid">
        {view === "config" && <div className="panel">
          <h2>实验配置</h2>
          <label>
            市场
            <select
              value={configForm.market_id}
              onChange={(event) => setConfigForm((current) => ({ ...current, market_id: event.target.value }))}
            >
              {markets.map((market) => (
                <option key={market.market_id} value={market.market_id}>
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
            Top N
            <input
              type="number"
              value={configForm.top_n}
              onChange={(event) => setConfigForm((current) => ({ ...current, top_n: Number(event.target.value) }))}
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
            </div>
          ) : (
            <p>请选择一个实验查看详情。</p>
          )}
        </div>}

        {view === "selection" && <div className="panel wide">
          <div className="toolbar">
            <h2>选股结果</h2>
            <input type="date" value={tradeDate} onChange={(event) => setTradeDate(event.target.value)} />
          </div>
          <table>
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
          </table>
        </div>}
      </section>
    </div>
  );
}
