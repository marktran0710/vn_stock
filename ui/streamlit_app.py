from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from vnstock_analyzer.data import align_series, load_history
from vnstock_analyzer.reporting import analysis_result_to_payload, universe_result_to_payload
from vnstock_analyzer.services import build_compare_analysis, build_universe_scan_analysis


st.set_page_config(page_title="VNStock Studio", page_icon="📈", layout="wide")

st.markdown(
    """
<style>
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(14, 165, 233, 0.14), transparent 25%),
            radial-gradient(circle at top right, rgba(16, 185, 129, 0.12), transparent 28%),
            linear-gradient(180deg, #08101f 0%, #0f172a 48%, #111827 100%);
        color: #e5eefc;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    h1, h2, h3, h4, h5, h6, p, label, span, div {
        color: #e5eefc;
    }
    .hero {
        padding: 1.5rem 1.75rem;
        border-radius: 24px;
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.88), rgba(30, 41, 59, 0.86));
        border: 1px solid rgba(148, 163, 184, 0.2);
        box-shadow: 0 20px 70px rgba(0, 0, 0, 0.35);
        margin-bottom: 1rem;
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin-bottom: 0.25rem;
    }
    .hero-subtitle {
        color: #cbd5e1;
        font-size: 1rem;
    }
    .glass-card {
        padding: 1rem 1rem 0.9rem 1rem;
        border-radius: 18px;
        background: rgba(15, 23, 42, 0.78);
        border: 1px solid rgba(148, 163, 184, 0.18);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
        margin-bottom: 0.9rem;
    }
    .metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #94a3b8;
        margin-bottom: 0.2rem;
    }
    .metric-value {
        font-size: 1.45rem;
        font-weight: 800;
        color: #f8fafc;
    }
    .metric-note {
        color: #cbd5e1;
        font-size: 0.85rem;
    }
    .section-title {
        margin-top: 0.4rem;
        margin-bottom: 0.5rem;
        font-size: 1.1rem;
        font-weight: 700;
        color: #f8fafc;
    }
    .candidate-box {
        padding: 0.9rem 1rem;
        border-radius: 16px;
        background: linear-gradient(135deg, rgba(8, 145, 178, 0.18), rgba(15, 118, 110, 0.16));
        border: 1px solid rgba(45, 212, 191, 0.16);
        margin-bottom: 0.7rem;
    }
    .small-muted {
        color: #cbd5e1;
        font-size: 0.86rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="hero">
  <div class="hero-title">VNStock Studio</div>
  <div class="hero-subtitle">Compare stocks, scan the Top 200 universe, and rank the strongest near-term join candidates.</div>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Controls")
    mode = st.radio("Mode", ["Compare 2-3 stocks", "Market scan (Top 200)"], index=1)
    periods = st.multiselect(
        "Timeframes",
        ["1mo", "2mo", "3mo", "6mo", "1y", "2y", "3y", "5y"],
        default=["1mo", "3mo", "6mo", "1y"],
    )
    benchmark = st.text_input("Benchmark ticker", value="")
    st.caption("Leave benchmark blank if Yahoo data is not available.")
    universe_file = st.text_input("Universe file", value=str(PROJECT_ROOT / "data" / "universe" / "top200_vn_stocks.csv"))
    scan_limit = st.slider("Universe size", min_value=20, max_value=200, value=200, step=10)
    top_n = st.slider("Top join candidates", min_value=3, max_value=20, value=10, step=1)
    st.caption("Symbols should use Yahoo Finance format like VCB.VN.")

st.subheader("Current view")


def build_normalized_line_frame(symbols: list[str], periods: list[str], benchmark: str | None = None) -> pd.DataFrame | None:
    requested = list(dict.fromkeys([symbol.upper() for symbol in symbols] + ([benchmark.upper()] if benchmark else [])))
    history_map: dict[str, pd.DataFrame] = {}
    for symbol in requested:
        try:
            history_map[symbol] = load_history(symbol, periods)
        except Exception:
            continue

    combined = align_series(history_map)
    if combined.empty:
        return None
    return combined / combined.iloc[0] * 100.0


@st.cache_data(ttl=600, show_spinner=False)
def cached_universe_scan(universe_file: str, periods: tuple[str, ...], benchmark: str | None, scan_limit: int, top_n: int):
    return build_universe_scan_analysis(
        universe_file=Path(universe_file),
        periods=list(periods),
        benchmark=benchmark,
        scan_limit=scan_limit,
        top_n=top_n,
    )

if mode == "Compare 2-3 stocks":
    symbols_text = st.text_input("Symbols (comma separated)", value="VCB.VN, FPT.VN, MWG.VN")
    analyze_clicked = st.button("Analyze comparison", type="primary")

    if analyze_clicked:
        symbols = [item.strip() for item in symbols_text.split(",") if item.strip()]
        try:
            result, failures = build_compare_analysis(symbols, periods, benchmark=benchmark or None)
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.markdown('<div class="section-title">Overview</div>', unsafe_allow_html=True)
            cols = st.columns(len(result.metrics))
            for column, metric in zip(cols, result.metrics):
                with column:
                    latest_close_text = f"{metric.latest_close:.2f}" if metric.latest_close is not None else "n/a"
                    trend_text = f"{metric.trend_score:.2f}" if metric.trend_score is not None else "n/a"
                    volatility_text = f"{metric.volatility_30d:.2f}" if metric.volatility_30d is not None else "n/a"
                    st.markdown(
                        f"""
<div class="glass-card">
  <div class="metric-label">{metric.symbol}</div>
  <div class="metric-value">{latest_close_text}</div>
  <div class="metric-note">Trend {trend_text} | Vol {volatility_text}%</div>
</div>
""",
                        unsafe_allow_html=True,
                    )
            st.info(result.market_fluctuation_summary)
            st.write(result.comparison_summary)

            line_df = build_normalized_line_frame(symbols, periods, benchmark=benchmark or None)
            if line_df is not None:
                st.markdown('<div class="section-title">Line chart comparison</div>', unsafe_allow_html=True)
                st.line_chart(line_df, use_container_width=True)
            else:
                st.warning("Unable to build line chart comparison from the available data.")

            period_rows = []
            for metric in result.metrics:
                row = {"Symbol": metric.symbol}
                row.update({period: metric.returns.get(period) for period in periods})
                period_rows.append(row)
            st.dataframe(pd.DataFrame(period_rows), use_container_width=True, hide_index=True)

            chart_df = pd.DataFrame(
                {
                    metric.symbol: [metric.returns.get(period) for period in periods]
                    for metric in result.metrics
                },
                index=periods,
            ).T
            st.bar_chart(chart_df)
            st.download_button(
                "Download JSON",
                data=json.dumps(analysis_result_to_payload(result), ensure_ascii=False, indent=2),
                file_name="vnstock_compare.json",
                mime="application/json",
            )
            if failures:
                st.warning(f"Skipped optional symbols: {', '.join(failures)}")

else:
    refresh_scan = st.button("Refresh market scan", type="primary")

    scan_key = (
        universe_file,
        tuple(periods),
        benchmark or None,
        scan_limit,
        top_n,
    )

    try:
        result, failures = cached_universe_scan(*scan_key)
    except ValueError as exc:
        st.error(str(exc))
    else:
        if refresh_scan:
            cached_universe_scan.clear()
            result, failures = cached_universe_scan(*scan_key)

        metric_cols = st.columns(3)
        metric_cols[0].metric("Universe size", result.total_symbols)
        metric_cols[1].metric("Analyzed symbols", result.analyzed_symbols)
        metric_cols[2].metric("Top join candidates", len(result.top_join_candidates_now))

        st.info(result.market_fluctuation_summary)

        st.markdown('<div class="section-title">Top join candidates now</div>', unsafe_allow_html=True)
        for symbol, score, rationale in result.top_join_candidates_now:
            st.markdown(
                f"""
<div class="candidate-box">
  <div class="metric-label">{symbol}</div>
  <div class="metric-value">Score {score:.4f}</div>
  <div class="small-muted">{rationale}</div>
</div>
""",
                unsafe_allow_html=True,
            )

        st.markdown('<div class="section-title">3M winners and losers</div>', unsafe_allow_html=True)
        left, right = st.columns(2)
        with left:
            st.write("Top gainers")
            st.dataframe(pd.DataFrame(result.top_gainers_3m, columns=["Symbol", "3M return (%)"]), use_container_width=True, hide_index=True)
        with right:
            st.write("Top losers")
            st.dataframe(pd.DataFrame(result.top_losers_3m, columns=["Symbol", "3M return (%)"]), use_container_width=True, hide_index=True)

        st.markdown('<div class="section-title">Average returns by period</div>', unsafe_allow_html=True)
        average_df = pd.DataFrame(list(result.average_returns.items()), columns=["Period", "Average return (%)"])
        st.bar_chart(average_df.set_index("Period"))

        st.markdown('<div class="section-title">Sector groups: pillar / growth / sustainable</div>', unsafe_allow_html=True)
        sector_tabs = st.tabs(["3 Months", "6 Months", "12 Months"])
        period_map = [("3mo", sector_tabs[0]), ("6mo", sector_tabs[1]), ("1y", sector_tabs[2])]
        sector_group_analysis = getattr(result, "sector_group_analysis", {}) or {}
        for period_key, period_tab in period_map:
            with period_tab:
                groups = sector_group_analysis.get(period_key, {})
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write("Pillar sectors")
                    st.dataframe(
                        pd.DataFrame(groups.get("pillar", []), columns=["Sector", "Score", "Coverage"]),
                        use_container_width=True,
                        hide_index=True,
                    )
                with col2:
                    st.write("Growth sectors")
                    st.dataframe(
                        pd.DataFrame(groups.get("growth", []), columns=["Sector", "Score", "Coverage"]),
                        use_container_width=True,
                        hide_index=True,
                    )
                with col3:
                    st.write("Sustainable sectors")
                    st.dataframe(
                        pd.DataFrame(groups.get("sustainable", []), columns=["Sector", "Score", "Coverage"]),
                        use_container_width=True,
                        hide_index=True,
                    )

        st.download_button(
            "Download JSON",
            data=json.dumps(universe_result_to_payload(result), ensure_ascii=False, indent=2),
            file_name="vnstock_market_scan.json",
            mime="application/json",
        )
        if failures:
            st.warning(f"Skipped symbols with missing data: {len(failures)}")

st.caption("Educational use only, not financial advice.")
