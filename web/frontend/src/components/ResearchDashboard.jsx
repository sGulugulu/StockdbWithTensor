import React, { useEffect, useState } from "react";


function formatMetric(value, digits = 4) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  const numeric = Number(value);
  if (Number.isFinite(numeric)) {
    return numeric.toFixed(digits);
  }
  return String(value);
}


function resolveAssetUrl(apiBase, asset) {
  if (!asset?.url) {
    return "";
  }
  if (/^https?:\/\//.test(asset.url)) {
    return asset.url;
  }
  return `${apiBase}${asset.url}`;
}


function AssetFigure({ title, asset, caption, apiBase }) {
  if (!asset?.url) {
    return (
      <article className="asset-card">
        <h3>{title}</h3>
        <p className="muted-text">当前没有可展示的图形资源。</p>
      </article>
    );
  }
  const assetUrl = resolveAssetUrl(apiBase, asset);
  return (
    <article className="asset-card">
      <div className="asset-card-header">
        <h3>{title}</h3>
        <a href={assetUrl} target="_blank" rel="noreferrer">
          查看原图
        </a>
      </div>
      <img className="asset-image" src={assetUrl} alt={title} />
      {caption ? <p className="muted-text">{caption}</p> : null}
    </article>
  );
}


export default function ResearchDashboard({ apiBase }) {
  const [dashboard, setDashboard] = useState(null);
  const [patternDetail, setPatternDetail] = useState(null);
  const [selectedYear, setSelectedYear] = useState("latest");
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState("");
  const [detailError, setDetailError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      setLoading(true);
      setError("");
      try {
        const response = await fetch(`${apiBase}/api/reports/dashboard`);
        if (!response.ok) {
          throw new Error("report-dashboard-failed");
        }
        const payload = await response.json();
        if (!cancelled) {
          setDashboard(payload);
        }
      } catch {
        if (!cancelled) {
          setDashboard(null);
          setError("研究结果面板读取失败，请确认报告素材和后端接口已准备完成。");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadDashboard();
    return () => {
      cancelled = true;
    };
  }, [apiBase]);

  useEffect(() => {
    let cancelled = false;

    async function loadPatternDetail() {
      setDetailLoading(true);
      setDetailError("");
      const endpoint = selectedYear === "latest"
        ? `${apiBase}/api/reports/pattern-discovery`
        : `${apiBase}/api/reports/pattern-discovery/${selectedYear}`;
      try {
        const response = await fetch(endpoint);
        if (!response.ok) {
          throw new Error("pattern-detail-failed");
        }
        const payload = await response.json();
        if (!cancelled) {
          setPatternDetail(payload);
        }
      } catch {
        if (!cancelled) {
          setPatternDetail(null);
          setDetailError("模式发现图组读取失败，请检查年度图组文件是否完整。");
        }
      } finally {
        if (!cancelled) {
          setDetailLoading(false);
        }
      }
    }

    loadPatternDetail();
    return () => {
      cancelled = true;
    };
  }, [apiBase, selectedYear]);

  const yearOptions = dashboard?.long_window_years ?? [];
  const boundaryRows = dashboard?.boundary_portfolio ?? [];
  const patternSummary = patternDetail ?? dashboard?.pattern_discovery;
  const selectedYearRow = selectedYear === "latest"
    ? null
    : yearOptions.find((row) => row.year === selectedYear) ?? null;

  return (
    <div className="panel wide research-panel">
      <div className="formal-header">
        <div>
          <p className="eyebrow">Research Storyboard</p>
          <h2>研究结果看板</h2>
          <p className="lead compact">
            复用现有正式实验输出和答辩素材，集中浏览跨样本组合闭环、模式发现图组与长窗口年度图。
          </p>
        </div>
      </div>

      {error ? <p className="error-text">{error}</p> : null}
      {loading ? <p className="muted-text">正在读取研究结果概览...</p> : null}

      {!loading && !error ? (
        <>
          <section className="research-section">
            <div className="toolbar">
              <div>
                <h3>跨样本组合闭环</h3>
                <p className="muted-text">按样本边界比较最佳模型、收益、Sharpe、回撤和暴露。</p>
              </div>
            </div>
            {boundaryRows.length ? (
              <table>
                <thead>
                  <tr>
                    <th>运行</th>
                    <th>股票池</th>
                    <th>最佳 Rank IC 模型</th>
                    <th>最佳收益模型</th>
                    <th>最佳 Sharpe 模型</th>
                    <th>候选池</th>
                    <th>Top N</th>
                  </tr>
                </thead>
                <tbody>
                  {boundaryRows.map((row) => (
                    <tr key={row.run_name}>
                      <td>{row.run_name}</td>
                      <td>{row.universe_id}</td>
                      <td>{row.best_rank_ic_model}</td>
                      <td>{row.best_return_model}</td>
                      <td>{row.best_sharpe_model}</td>
                      <td>{row.candidate_pool_size}</td>
                      <td>{row.selection_top_n}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : <p className="muted-text">当前没有边界组合汇总数据。</p>}
          </section>

          <section className="research-section">
            <div className="toolbar">
              <div>
                <h3>模式发现图组</h3>
                <p className="muted-text">切换短窗口正式快照与长窗口年度图组，查看股票结构、行业聚类和样本边界差异。</p>
              </div>
              <label className="compact-field">
                年度
                <select value={selectedYear} onChange={(event) => setSelectedYear(event.target.value)}>
                  <option value="latest">正式快照</option>
                  {yearOptions.map((row) => (
                    <option key={row.year} value={row.year}>
                      {row.year}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            {detailError ? <p className="error-text">{detailError}</p> : null}
            {detailLoading ? <p className="muted-text">正在读取模式发现图组...</p> : null}
            {patternSummary ? (
              <>
                <div className="detail-grid research-kpis">
                  <div>
                    <strong>锚定运行</strong>
                    <p>{patternSummary.anchor_run ?? "-"}</p>
                  </div>
                  <div>
                    <strong>模型</strong>
                    <p>{patternSummary.model ?? "-"}</p>
                  </div>
                  <div>
                    <strong>股票数</strong>
                    <p>{patternSummary.stock_count ?? "-"}</p>
                  </div>
                  <div>
                    <strong>对比运行数</strong>
                    <p>{patternSummary.comparison_run_count ?? "-"}</p>
                  </div>
                  <div>
                    <strong>长窗口年度</strong>
                    <p>{selectedYear === "latest" ? "正式快照" : selectedYear}</p>
                  </div>
                </div>
                <div className="asset-grid">
                  <AssetFigure
                    title="股票潜在结构图"
                    asset={patternSummary.assets?.stock_structure_svg}
                    apiBase={apiBase}
                    caption="观察高频出现股票在潜在结构中的分布与行业颜色。"
                  />
                  <AssetFigure
                    title="聚类与行业交叉图"
                    asset={patternSummary.assets?.cluster_industry_svg}
                    apiBase={apiBase}
                    caption="观察聚类标签与行业标签的重合关系。"
                  />
                  <AssetFigure
                    title="样本边界对比图"
                    asset={patternSummary.assets?.boundary_comparison_svg}
                    apiBase={apiBase}
                    caption="比较指数、全 A、行业和市值边界下的表现差异。"
                  />
                </div>
              </>
            ) : null}
          </section>

          <section className="research-section">
            <div className="toolbar">
              <div>
                <h3>长窗口年度图</h3>
                <p className="muted-text">按年份查看全 A 长窗口的时间状态切换图与因子重要性热力图。</p>
              </div>
            </div>
            {selectedYear === "latest" ? (
              <p className="muted-text">切换到具体年份后，可查看该年度的时间状态图和因子热力图。</p>
            ) : selectedYearRow ? (
              <div className="asset-grid">
                <AssetFigure
                  title={`${selectedYear} 时间状态切换`}
                  asset={selectedYearRow.time_regime_asset}
                  apiBase={apiBase}
                  caption="展示 unified selection candidate 的日均 time regime score 变化。"
                />
                <AssetFigure
                  title={`${selectedYear} 因子重要性热力图`}
                  asset={selectedYearRow.factor_heatmap_asset}
                  apiBase={apiBase}
                  caption="展示不同模型下因子重要性的年度结构。"
                />
              </div>
            ) : (
              <p className="muted-text">当前年份没有可展示的长窗口图资产。</p>
            )}
          </section>

          {boundaryRows.length ? (
            <section className="research-section">
              <div className="toolbar">
                <div>
                  <h3>当前正式快照的模型对比</h3>
                  <p className="muted-text">展示正式快照中各模型在收益、Sharpe、波动和回撤上的核心数值。</p>
                </div>
              </div>
              <div className="model-grid">
                {(boundaryRows[0]?.models ?? []).map((row) => (
                  <article className="model-card" key={row.model}>
                    <div className="model-card-header">
                      <h4>{row.model}</h4>
                      <span>{formatMetric(row.rank_ic_mean)}</span>
                    </div>
                    <p><strong>累计收益：</strong>{formatMetric(row.cumulative_return)}</p>
                    <p><strong>Sharpe：</strong>{formatMetric(row.sharpe_ratio)}</p>
                    <p><strong>年化波动：</strong>{formatMetric(row.annualized_volatility)}</p>
                    <p><strong>最大回撤：</strong>{formatMetric(row.max_drawdown)}</p>
                  </article>
                ))}
              </div>
            </section>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
