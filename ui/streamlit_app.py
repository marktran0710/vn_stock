from __future__ import annotations

from datetime import datetime
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
from vnstock_analyzer.news import fetch_vnexpress_stock_news
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
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1222 0%, #111b31 100%);
        border-right: 1px solid rgba(148, 163, 184, 0.2);
    }
    section[data-testid="stSidebar"] * {
        color: #e5eefc;
    }
    section[data-testid="stSidebar"] [data-baseweb="radio"] > div {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 12px;
        padding: 0.2rem;
    }
    section[data-testid="stSidebar"] [data-baseweb="radio"] label {
        border-radius: 8px;
        padding: 0.35rem 0.5rem;
    }
    section[data-testid="stSidebar"] [data-baseweb="radio"] input:checked + div {
        background: rgba(14, 165, 233, 0.24);
        border-color: rgba(56, 189, 248, 0.55);
    }
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(15, 23, 42, 0.82);
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 12px;
        padding: 0.25rem;
        gap: 0.25rem;
    }
    .stTabs [data-baseweb="tab"] {
        color: #cbd5e1;
        border-radius: 8px;
        padding: 0.4rem 0.75rem;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(14, 165, 233, 0.22);
        color: #f8fafc;
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
    mode = st.radio("Mode", ["Compare 2-3 stocks", "Market scan (Top 200)", "Buy potential ideas"], index=1)
    periods = st.multiselect(
        "Timeframes",
        ["1mo", "2mo", "3mo", "6mo", "1y", "2y", "3y", "5y"],
        default=["1mo", "3mo", "6mo", "1y"],
    )
    benchmark = st.text_input("Benchmark ticker", value="").strip()
    st.caption("Leave benchmark blank if Yahoo data is not available.")
    universe_file = st.text_input("Universe file", value=str(PROJECT_ROOT / "data" / "universe" / "top200_vn_stocks.csv"))
    scan_limit = st.slider("Universe size", min_value=20, max_value=200, value=200, step=10)
    top_n = st.slider("Top join candidates", min_value=3, max_value=20, value=10, step=1)
    min_buy_score = st.slider("Min buy score", min_value=-1.0, max_value=2.0, value=0.0, step=0.05)
    st.caption("Symbols should use Yahoo Finance format like VCB.VN.")

st.subheader("Current view")

@st.cache_data(ttl=900, show_spinner=False)
def cached_stock_news(limit: int = 10):
    return fetch_vnexpress_stock_news(limit=limit)


news_col, news_action_col = st.columns([5, 1])
with news_col:
    st.markdown('<div class="section-title">Top VNExpress stock news (latest 10)</div>', unsafe_allow_html=True)
with news_action_col:
    refresh_news = st.button("Refresh news")
if refresh_news:
    cached_stock_news.clear()

news_items = cached_stock_news(limit=10)
if news_items:
    for idx, item in enumerate(news_items, start=1):
        published_text = f" - {item.published_at}" if item.published_at else ""
        st.markdown(f"{idx}. [{item.title}]({item.link}) ({item.source}{published_text})")
else:
    st.info("No VNExpress stock news is available right now.")

st.divider()

if "market_scan_refresh_token" not in st.session_state:
    st.session_state["market_scan_refresh_token"] = 0
if "buy_scan_refresh_token" not in st.session_state:
    st.session_state["buy_scan_refresh_token"] = 0
if "market_scan_last_refresh" not in st.session_state:
    st.session_state["market_scan_last_refresh"] = None
if "buy_scan_last_refresh" not in st.session_state:
    st.session_state["buy_scan_last_refresh"] = None


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
def cached_universe_scan(
    universe_file: str,
    periods: tuple[str, ...],
    benchmark: str | None,
    scan_limit: int,
    top_n: int,
    refresh_token: int,
):
    _ = refresh_token
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
        if not periods:
            st.error("Please select at least one timeframe first.")
        else:
            symbols = [item.strip() for item in symbols_text.split(",") if item.strip()]
            try:
                result, failures = build_compare_analysis(symbols, periods, benchmark=benchmark if benchmark else None)
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

                line_df = build_normalized_line_frame(symbols, periods, benchmark=benchmark if benchmark else None)
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
                if period_rows:
                    st.dataframe(pd.DataFrame(period_rows), use_container_width=True, hide_index=True)
                else:
                    st.warning("No return data available for selected periods.")

                chart_df = pd.DataFrame(
                    {
                        metric.symbol: [metric.returns.get(period) for period in periods]
                        for metric in result.metrics
                    },
                    index=periods,
                ).T
                if not chart_df.empty:
                    st.bar_chart(chart_df)
                else:
                    st.warning("Unable to generate bar chart from available data.")
                st.download_button(
                    "Download JSON",
                    data=json.dumps(analysis_result_to_payload(result), ensure_ascii=False, indent=2),
                    file_name="vnstock_compare.json",
                    mime="application/json",
                )
                if failures:
                    st.warning(f"Skipped optional symbols: {', '.join(failures)}")
elif mode == "Market scan (Top 200)":
    if not periods:
        st.error("Please select at least one timeframe first.")
    else:
        refresh_scan = st.button("Refresh market scan", type="primary")

        if refresh_scan:
            st.session_state["market_scan_refresh_token"] += 1
            st.session_state["market_scan_last_refresh"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        scan_key = (
            universe_file,
            tuple(periods),
            benchmark if benchmark else None,
            scan_limit,
            top_n,
            st.session_state["market_scan_refresh_token"],
        )

        try:
            result, failures = cached_universe_scan(*scan_key)
        except ValueError as exc:
            st.error(str(exc))
        else:

            metric_cols = st.columns(3)
            metric_cols[0].metric("Universe size", result.total_symbols)
            metric_cols[1].metric("Analyzed symbols", result.analyzed_symbols)
            metric_cols[2].metric("Top join candidates", len(result.top_join_candidates_now))
            if st.session_state["market_scan_last_refresh"]:
                st.caption(f"Last manual refresh: {st.session_state['market_scan_last_refresh']}")
            else:
                st.caption(f"Latest scan timestamp: {result.as_of}")

            st.info(result.market_fluctuation_summary)

            st.markdown('<div class="section-title">Top 10 potential stocks to join (3M horizon)</div>', unsafe_allow_html=True)
            top_join_candidates_3m = getattr(result, "top_join_candidates_3m", None)
            if top_join_candidates_3m is None:
                # Backward compatibility for stale cached objects created before this field existed.
                top_join_candidates_3m = list(getattr(result, "top_join_candidates_now", []))[:10]

            if top_join_candidates_3m:
                for symbol, score, rationale in top_join_candidates_3m:
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
                top_3m_df = pd.DataFrame(
                    top_join_candidates_3m,
                    columns=["Symbol", "3M potential score", "Rationale"],
                )
                st.dataframe(top_3m_df, use_container_width=True, hide_index=True)
            else:
                st.info("No 3-month potential candidates available.")

            st.markdown('<div class="section-title">Top join candidates now</div>', unsafe_allow_html=True)
            if result.top_join_candidates_now:
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
            else:
                st.info("No join candidates found for current parameters.")

            st.markdown('<div class="section-title">3M winners and losers</div>', unsafe_allow_html=True)
            left, right = st.columns(2)
            with left:
                st.write("Top gainers")
                if result.top_gainers_3m:
                    st.dataframe(pd.DataFrame(result.top_gainers_3m, columns=["Symbol", "3M return (%)"]), use_container_width=True, hide_index=True)
                else:
                    st.info("No gainers data available.")
            with right:
                st.write("Top losers")
                if result.top_losers_3m:
                    st.dataframe(pd.DataFrame(result.top_losers_3m, columns=["Symbol", "3M return (%)"]), use_container_width=True, hide_index=True)
                else:
                    st.info("No losers data available.")

            st.markdown('<div class="section-title">Average returns by period</div>', unsafe_allow_html=True)
            if result.average_returns:
                average_df = pd.DataFrame(list(result.average_returns.items()), columns=["Period", "Average return (%)"])
                st.bar_chart(average_df.set_index("Period"))
            else:
                st.info("No average returns data available.")

            st.markdown('<div class="section-title">Sector groups: pillar / growth / sustainable</div>', unsafe_allow_html=True)
            sector_tabs = st.tabs(["3 Months", "6 Months", "12 Months"])
            period_map = [("3mo", sector_tabs[0]), ("6mo", sector_tabs[1]), ("1y", sector_tabs[2])]
            sector_group_analysis = getattr(result, "sector_group_analysis", None) or {}
            if sector_group_analysis:
                for period_key, period_tab in period_map:
                    with period_tab:
                        groups = sector_group_analysis.get(period_key, {})
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write("Pillar sectors")
                            pillar_data = groups.get("pillar", [])
                            if pillar_data:
                                st.dataframe(
                                    pd.DataFrame(pillar_data, columns=["Sector", "Score", "Coverage"]),
                                    use_container_width=True,
                                    hide_index=True,
                                )
                            else:
                                st.info("No pillar sector data.")
                        with col2:
                            st.write("Growth sectors")
                            growth_data = groups.get("growth", [])
                            if growth_data:
                                st.dataframe(
                                    pd.DataFrame(growth_data, columns=["Sector", "Score", "Coverage"]),
                                    use_container_width=True,
                                    hide_index=True,
                                )
                            else:
                                st.info("No growth sector data.")
                        with col3:
                            st.write("Sustainable sectors")
                            sustainable_data = groups.get("sustainable", [])
                            if sustainable_data:
                                st.dataframe(
                                    pd.DataFrame(sustainable_data, columns=["Sector", "Score", "Coverage"]),
                                    use_container_width=True,
                                    hide_index=True,
                                )
                            else:
                                st.info("No sustainable sector data.")
            else:
                st.info("No sector analysis data available.")

            st.download_button(
                "Download JSON",
                data=json.dumps(universe_result_to_payload(result), ensure_ascii=False, indent=2),
                file_name="vnstock_market_scan.json",
                mime="application/json",
            )
            if failures:
                st.warning(f"Skipped symbols with missing data: {len(failures)}")

else:
    if not periods:
        st.error("Please select at least one timeframe first.")
    else:
        refresh_scan = st.button("Refresh buy potential", type="primary")

        if refresh_scan:
            st.session_state["buy_scan_refresh_token"] += 1
            st.session_state["buy_scan_last_refresh"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        scan_key = (
            universe_file,
            tuple(periods),
            benchmark if benchmark else None,
            scan_limit,
            top_n,
            st.session_state["buy_scan_refresh_token"],
        )

        try:
            result, failures = cached_universe_scan(*scan_key)
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.info(result.market_fluctuation_summary)
            if st.session_state["buy_scan_last_refresh"]:
                st.caption(f"Last manual refresh: {st.session_state['buy_scan_last_refresh']}")
            else:
                st.caption(f"Latest scan timestamp: {result.as_of}")

            buy_potential_candidates = getattr(result, "buy_potential_candidates", None)
            if buy_potential_candidates is None:
                # Backward compatibility for stale cached objects created before this field existed.
                buy_potential_candidates = []

            candidates = [
                row for row in buy_potential_candidates if row[1] >= min_buy_score
            ]

            stats_cols = st.columns(3)
            stats_cols[0].metric("Analyzed symbols", result.analyzed_symbols)
            stats_cols[1].metric("Candidates above threshold", len(candidates))
            stats_cols[2].metric("Threshold", f"{min_buy_score:.2f}")

            st.markdown('<div class="section-title">Buy potential candidates</div>', unsafe_allow_html=True)
            if candidates:
                for symbol, score, setup_strength, summary in candidates:
                    badge_color = {
                        "high": "#22c55e",
                        "medium": "#f59e0b",
                        "low": "#ef4444",
                    }.get(setup_strength, "#94a3b8")
                    st.markdown(
                        f"""
<div class="candidate-box">
  <div class="metric-label">{symbol}</div>
  <div class="metric-value">Score {score:.4f}</div>
  <div class="small-muted">Setup: <span style=\"color:{badge_color};font-weight:700;\">{setup_strength.upper()}</span></div>
  <div class="small-muted">{summary}</div>
</div>
""",
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No symbols met the current score threshold.")

            if candidates:
                table_df = pd.DataFrame(
                    candidates,
                    columns=["Symbol", "Score", "Setup strength", "Summary"],
                )
                st.dataframe(table_df, use_container_width=True, hide_index=True)

            st.download_button(
                "Download buy potential JSON",
                data=json.dumps(
                    {
                        "as_of": result.as_of,
                        "benchmark": result.benchmark,
                        "analyzed_symbols": result.analyzed_symbols,
                        "min_buy_score": min_buy_score,
                        "buy_potential_candidates": candidates,
                        "market_fluctuation_summary": result.market_fluctuation_summary,
                        "notes": result.notes,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                file_name="vnstock_buy_potential.json",
                mime="application/json",
            )

            st.caption("Buy potential scores are educational signals, not guaranteed outcomes.")

            if failures:
                st.warning(f"Skipped symbols with missing data: {len(failures)}")

st.caption("Educational use only, not financial advice.")
