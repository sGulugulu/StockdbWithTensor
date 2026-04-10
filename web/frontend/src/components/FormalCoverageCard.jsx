import React from "react";


function formatValue(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  if (typeof value === "number") {
    return value.toLocaleString("zh-CN");
  }
  return String(value);
}


export default function FormalCoverageCard({ title, rows = [] }) {
  return (
    <article className="coverage-card">
      <div className="coverage-card-header">
        <h3>{title}</h3>
        <span>{rows.length ? `${rows.length} 组` : "无数据"}</span>
      </div>
      <div className="coverage-card-body">
        {rows.length ? rows.map((row, index) => (
          <div className="coverage-record" key={`${title}-${index}`}>
            {Object.entries(row).map(([key, value]) => (
              <div key={key}>
                <strong>{key}</strong>
                <p>{formatValue(value)}</p>
              </div>
            ))}
          </div>
        )) : <p className="muted-text">当前 catalog 中没有可展示的覆盖率数据。</p>}
      </div>
    </article>
  );
}
