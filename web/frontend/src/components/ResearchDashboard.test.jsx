import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import ResearchDashboard from "./ResearchDashboard.jsx";


describe("ResearchDashboard", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders report overview, pattern assets, and yearly long-window assets", async () => {
    const fetchMock = vi.fn((input) => {
      const url = String(input);
      if (url.endsWith("/api/reports/dashboard")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              boundary_portfolio: [
                {
                  run_name: "formal_all_a_run",
                  universe_id: "ALL_A_ACTIVE",
                  best_rank_ic_model: "tucker",
                  best_return_model: "pca",
                  best_sharpe_model: "pca",
                  candidate_pool_size: 80,
                  selection_top_n: 20,
                  models: [
                    {
                      model: "cp",
                      rank_ic_mean: -0.1,
                      cumulative_return: -0.05,
                      sharpe_ratio: -1.2,
                      annualized_volatility: 0.23,
                      max_drawdown: -0.06
                    }
                  ]
                }
              ],
              pattern_discovery: {
                anchor_run: "formal_all_a_run",
                model: "tucker",
                stock_count: 60,
                comparison_run_count: 10,
                assets: {
                  stock_structure_svg: {
                    path: "pattern_discovery/stock.svg",
                    url: "/api/reports/assets/pattern_discovery/stock.svg"
                  },
                  cluster_industry_svg: {
                    path: "pattern_discovery/cluster.svg",
                    url: "/api/reports/assets/pattern_discovery/cluster.svg"
                  },
                  boundary_comparison_svg: {
                    path: "pattern_discovery/boundary.svg",
                    url: "/api/reports/assets/pattern_discovery/boundary.svg"
                  }
                }
              },
              long_window_years: [
                {
                  year: "2026",
                  time_regime_asset: {
                    path: "defense_materials/long_window_assets/2026_timeline.svg",
                    url: "/api/reports/assets/defense_materials/long_window_assets/2026_timeline.svg"
                  },
                  factor_heatmap_asset: {
                    path: "defense_materials/long_window_assets/2026_heatmap.svg",
                    url: "/api/reports/assets/defense_materials/long_window_assets/2026_heatmap.svg"
                  },
                  pattern_discovery_available: true
                }
              ]
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      if (url.endsWith("/api/reports/pattern-discovery")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              anchor_run: "formal_all_a_run",
              model: "tucker",
              stock_count: 60,
              comparison_run_count: 10,
              assets: {
                stock_structure_svg: {
                  path: "pattern_discovery/stock.svg",
                  url: "/api/reports/assets/pattern_discovery/stock.svg"
                },
                cluster_industry_svg: {
                  path: "pattern_discovery/cluster.svg",
                  url: "/api/reports/assets/pattern_discovery/cluster.svg"
                },
                boundary_comparison_svg: {
                  path: "pattern_discovery/boundary.svg",
                  url: "/api/reports/assets/pattern_discovery/boundary.svg"
                }
              }
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      return Promise.reject(new Error(`Unhandled fetch: ${url}`));
    });

    vi.stubGlobal("fetch", fetchMock);

    render(<ResearchDashboard apiBase="http://127.0.0.1:8080" />);

    await waitFor(() => {
      expect(screen.getByText("研究结果看板")).toBeInTheDocument();
    });

    expect(screen.getByText("跨样本组合闭环")).toBeInTheDocument();
    expect(screen.getByText("模式发现图组")).toBeInTheDocument();
    expect(screen.getAllByText("formal_all_a_run").length).toBeGreaterThan(0);
    expect(screen.getByAltText("股票潜在结构图")).toBeInTheDocument();
    expect(screen.getByText("长窗口年度图")).toBeInTheDocument();
  });
});
