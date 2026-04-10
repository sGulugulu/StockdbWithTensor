import React, { useEffect, useState } from "react";
import FormalCoverageCard from "./FormalCoverageCard.jsx";


function normalizeRows(value) {
  if (Array.isArray(value)) {
    return value;
  }
  if (value && typeof value === "object") {
    return [value];
  }
  return [];
}


export default function FormalDataPanel({ apiBase }) {
  const [coverage, setCoverage] = useState(null);
  const [coverageError, setCoverageError] = useState("");
  const [coverageLoading, setCoverageLoading] = useState(true);
  const [memberRows, setMemberRows] = useState([]);
  const [memberError, setMemberError] = useState("");
  const [memberLoading, setMemberLoading] = useState(true);
  const [universeId, setUniverseId] = useState("HS300");
  const [tradeDate, setTradeDate] = useState("2026-03-02");

  useEffect(() => {
    let cancelled = false;

    async function loadCoverage() {
      setCoverageLoading(true);
      setCoverageError("");
      try {
        const response = await fetch(`${apiBase}/api/formal/coverage`);
        if (!response.ok) {
          throw new Error("formal-coverage-failed");
        }
        const payload = await response.json();
        if (!cancelled) {
          setCoverage(payload);
        }
      } catch {
        if (!cancelled) {
          setCoverage(null);
          setCoverageError("Formal 覆盖率读取失败，请确认 DuckDB catalog 已生成。");
        }
      } finally {
        if (!cancelled) {
          setCoverageLoading(false);
        }
      }
    }

    loadCoverage();
    return () => {
      cancelled = true;
    };
  }, [apiBase]);

  useEffect(() => {
    let cancelled = false;

    async function loadMembers() {
      setMemberLoading(true);
      setMemberError("");
      try {
        const response = await fetch(
          `${apiBase}/api/formal/universes/${encodeURIComponent(universeId)}?trade_date=${tradeDate}`
        );
        if (!response.ok) {
          throw new Error("formal-universe-failed");
        }
        const payload = await response.json();
        if (!cancelled) {
          setMemberRows(payload);
        }
      } catch {
        if (!cancelled) {
          setMemberRows([]);
          setMemberError("股票池成员读取失败，请检查日期、股票池名称或后端 DuckDB 服务状态。");
        }
      } finally {
        if (!cancelled) {
          setMemberLoading(false);
        }
      }
    }

    loadMembers();
    return () => {
      cancelled = true;
    };
  }, [apiBase, tradeDate, universeId]);

  return (
    <div className="panel wide formal-panel">
      <div className="formal-header">
        <div>
          <p className="eyebrow">DuckDB Formal Catalog</p>
          <h2>Formal 数据覆盖率</h2>
          <p className="lead compact">
            直接读取本地 DuckDB catalog，展示 shared master、full master、因子面板与财务/报告数据覆盖情况。
          </p>
        </div>
      </div>

      {coverageError ? <p className="error-text">{coverageError}</p> : null}
      {coverageLoading ? <p className="muted-text">正在读取 formal 覆盖率...</p> : null}

      {!coverageLoading && !coverageError ? (
        <div className="coverage-grid">
          <FormalCoverageCard title="Shared Master" rows={normalizeRows(coverage?.master)} />
          <FormalCoverageCard title="Full Master" rows={normalizeRows(coverage?.full_master)} />
          <FormalCoverageCard title="Factor Panels" rows={normalizeRows(coverage?.factors)} />
          <FormalCoverageCard title="Financial / Reports" rows={[...normalizeRows(coverage?.financial), ...normalizeRows(coverage?.reports)]} />
        </div>
      ) : null}

      <section className="formal-members-section">
        <div className="toolbar">
          <div>
            <h2>股票池按日成员</h2>
            <p className="muted-text">按指定交易日查询 formal universe 历史成员。</p>
          </div>
        </div>
        <div className="formal-query-bar">
          <label>
            股票池
            <select value={universeId} onChange={(event) => setUniverseId(event.target.value)}>
              <option value="HS300">HS300</option>
              <option value="SZ50">SZ50</option>
              <option value="ZZ500">ZZ500</option>
              <option value="ALL_A_TRADABLE">ALL_A_TRADABLE</option>
            </select>
          </label>
          <label>
            交易日
            <input type="date" value={tradeDate} onChange={(event) => setTradeDate(event.target.value)} />
          </label>
        </div>

        {memberError ? <p className="error-text">{memberError}</p> : null}
        {memberLoading ? <p className="muted-text">正在读取股票池成员...</p> : null}

        {!memberLoading && !memberError ? (
          memberRows.length ? (
            <table>
              <thead>
                <tr>
                  <th>交易日</th>
                  <th>股票代码</th>
                  <th>市场</th>
                  <th>股票池</th>
                  <th>起始日</th>
                  <th>结束日</th>
                </tr>
              </thead>
              <tbody>
                {memberRows.map((row) => (
                  <tr key={`${row.trade_date}-${row.stock_code}`}>
                    <td>{row.trade_date}</td>
                    <td>{row.stock_code}</td>
                    <td>{row.market_id}</td>
                    <td>{row.universe_id}</td>
                    <td>{row.start_date}</td>
                    <td>{row.end_date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <p className="muted-text">当前日期下没有查询到成员记录。</p>
        ) : null}
      </section>
    </div>
  );
}
