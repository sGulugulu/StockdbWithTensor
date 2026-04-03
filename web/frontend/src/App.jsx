import React, { useEffect, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

export default function App() {
  const [markets, setMarkets] = useState([]);
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [selectionRows, setSelectionRows] = useState([]);
  const [tradeDate, setTradeDate] = useState("2026-01-09");

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
      return;
    }
    fetch(`${API_BASE}/api/runs/${selectedRun}/selection?trade_date=${tradeDate}&top_n=20`)
      .then((response) => response.json())
      .then(setSelectionRows)
      .catch(() => setSelectionRows([]));
  }, [selectedRun, tradeDate]);

  async function createRun() {
    await fetch(`${API_BASE}/api/runs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ run_sync: false })
    });
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

      <section className="grid">
        <div className="panel">
          <h2>市场</h2>
          <ul>
            {markets.map((market) => (
              <li key={market.market_id}>
                {market.market_name} / {market.default_universe_id}
              </li>
            ))}
          </ul>
        </div>

        <div className="panel">
          <h2>实验列表</h2>
          <ul className="run-list">
            {runs.map((run) => (
              <li key={run.run_id}>
                <button className={selectedRun === run.run_id ? "active" : ""} onClick={() => setSelectedRun(run.run_id)}>
                  {run.run_id} / {run.status.status}
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div className="panel wide">
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
                <th>主要因子</th>
              </tr>
            </thead>
            <tbody>
              {selectionRows.map((row) => (
                <tr key={`${row.stock_code}-${row.model}-${row.trade_date}`}>
                  <td>{row.stock_code}</td>
                  <td>{Number(row.total_score).toFixed(4)}</td>
                  <td>{Number(row.time_regime_score).toFixed(4)}</td>
                  <td>{row.cluster_label}</td>
                  <td>{row.top_factor_1}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
