import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App.jsx";


describe("App", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows formal coverage cards and universe members on the formal data page", async () => {
    const fetchMock = vi.fn((input) => {
      const url = String(input);
      if (url.endsWith("/api/markets")) {
        return Promise.resolve(
          new Response(
            JSON.stringify([
              {
                option_id: "formal_hs300",
                config_profile: "formal_hs300",
                market_id: "cn_a",
                market_name: "A股 / 沪深300",
                universe_id: "HS300",
                is_formal: true
              }
            ]),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      if (url.endsWith("/api/runs")) {
        return Promise.resolve(new Response(JSON.stringify([]), { status: 200 }));
      }
      if (url.endsWith("/api/formal/coverage")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              master: {
                row_count: 2,
                stock_count: 1,
                min_trade_date: "2026-03-02",
                max_trade_date: "2026-03-03"
              },
              full_master: {
                row_count: 2,
                stock_count: 1,
                min_trade_date: "2026-03-02",
                max_trade_date: "2026-03-03"
              },
              factors: [
                {
                  universe_id: "HS300",
                  row_count: 2,
                  stock_count: 1,
                  min_trade_date: "2026-03-02",
                  max_trade_date: "2026-03-03"
                }
              ],
              financial: [
                {
                  dataset_name: "profit_data",
                  row_count: 1,
                  stock_count: 1,
                  min_query_year: 2025,
                  max_query_year: 2025
                }
              ],
              reports: [
                {
                  dataset_name: "forecast_report",
                  row_count: 1,
                  stock_count: 1,
                  min_query_year: 2025,
                  max_query_year: 2025
                }
              ]
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      if (url.includes("/api/formal/universes/HS300?trade_date=2026-03-02")) {
        return Promise.resolve(
          new Response(
            JSON.stringify([
              {
                trade_date: "2026-03-02",
                market_id: "cn_a",
                universe_id: "HS300",
                stock_code: "600000.SH",
                start_date: "2026-03-02",
                end_date: "2026-03-03"
              }
            ]),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      return Promise.reject(new Error(`Unhandled fetch: ${url}`));
    });

    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Formal 数据页" }));

    await waitFor(() => {
      expect(screen.getByText("Formal 数据覆盖率")).toBeInTheDocument();
    });

    expect(screen.getByText("Shared Master")).toBeInTheDocument();
    expect(screen.getByText("股票池按日成员")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("600000.SH")).toBeInTheDocument();
    });
  });
});
