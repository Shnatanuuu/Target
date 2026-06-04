import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from io import StringIO
import re

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Target Competitor Intelligence",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #F8F6F3;
        border-radius: 12px;
        padding: 16px 20px;
        border: 1px solid #E8E4DE;
    }
    .metric-value { font-size: 28px; font-weight: 600; color: #1A1A1A; margin: 0; }
    .metric-label { font-size: 12px; color: #6B6B6B; margin: 0; margin-top: 4px; }
    .section-title { font-size: 15px; font-weight: 600; color: #1A1A1A; margin-bottom: 4px; }
    .insight-box {
        background: #EEF6F1;
        border-left: 3px solid #1D9E75;
        padding: 10px 14px;
        border-radius: 0 8px 8px 0;
        font-size: 13px;
        color: #1A1A1A;
        margin-top: 8px;
    }
    .warn-box {
        background: #FEF6E7;
        border-left: 3px solid #EF9F27;
        padding: 10px 14px;
        border-radius: 0 8px 8px 0;
        font-size: 13px;
        color: #1A1A1A;
        margin-top: 8px;
    }
    [data-testid="stSidebar"] { background: #F4F1ED; }
    /* Icon-only export button */
    div[data-testid="stDownloadButton"] button {
        padding: 4px 8px !important;
        font-size: 14px !important;
        min-height: 0 !important;
        height: 28px !important;
        width: 28px !important;
        border-radius: 6px !important;
        background: #F4F1ED !important;
        border: 1px solid #E8E4DE !important;
        color: #1A1A1A !important;
    }
</style>
""", unsafe_allow_html=True)

COLORS = ["#1D9E75","#E07B39","#185FA5","#BA7517","#7B3FA0","#C23B5A","#2B8C9B","#8B7355"]

# ── CSV export helper ─────────────────────────────────────────────────────────
if "dl_counter" not in st.session_state:
    st.session_state["dl_counter"] = 0

def export_csv(df_export: pd.DataFrame, filename: str):
    """Render a small right-aligned icon-only CSV download button."""
    csv_bytes = df_export.to_csv(index=False).encode("utf-8-sig")
    _, btn_col = st.columns([12, 1])
    with btn_col:
        st.download_button(
            label="⬇",
            data=csv_bytes,
            file_name=filename,
            mime="text/csv",
            key=f"dl_{filename}",
            use_container_width=False,
        )

# ── Sample data (Target marketplace) ──────────────────────────────────────────
SAMPLE = """Subcategory	Link	Rating	Image_Src	Brand	Title	Price	Remark	Ranking	Country
Stiletto Heels	https://www.target.com/p/women-s-virginia-heels-with-memory-foam-insole-a-new-day-black/-/A-94601742?preselect=94567909#lnk=sametab	4.7 stars with 57 ratings	https://target.scene7.com/is/image/Target/GUEST_83ee76f3-86ac-47f8-9605-2fa0465bd5c4?qlt=65&fmt=webp&hei=350&wid=350	A New Day	Women's Virginia Heels with Memory Foam Insole – A New Day™ Black	$28.00		1	United States
Stiletto Heels	https://www.target.com/p/gossip-dramatic-strappy-stiletto-heels/-/A-1008391978?preselect=1008391983#lnk=sametab	4.3 stars with 12 ratings	https://target.scene7.com/is/image/Target/GUEST_0808cd2a-835e-4b2d-8fc8-332c42a76bce?qlt=65&fmt=webp&hei=350&wid=350	London Rag	Gossip Dramatic Strappy Stiletto Heels	$38.99		2	United States
Stiletto Heels	https://www.target.com/p/shoeverse-satin-stiletto-heels-with-embellished-bow/-/A-1009601387?preselect=1009601406#lnk=sametab	4.0 stars with 8 ratings	https://target.scene7.com/is/image/Target/GUEST_449b85f3-98d3-48e3-857a-62e03d92f804?qlt=65&fmt=webp&hei=350&wid=350	London Rag	Shoeverse Satin Stiletto Heels With Embellished Bow	$38.99		3	United States
Stiletto Heels	https://www.target.com/p/women-s-maddie-block-heel-pumps-a-new-day/-/A-94601738	4.2 stars with 34 ratings	https://target.scene7.com/is/image/Target/GUEST_d76a8dba-8b0c-4e62-88e6-3e4d5d01d7e4?qlt=65&fmt=webp&hei=350&wid=350	A New Day	Women's Maddie Block Heel Pumps – A New Day™ Black	$28.00	20% off	4	United States
Stiletto Heels	https://www.target.com/p/women-s-kaya-pointed-toe-stiletto-heels-wild-fable/-/A-88750586	3.9 stars with 22 ratings	https://target.scene7.com/is/image/Target/GUEST_912a2b98-9c51-4a25-90cd-1aee9e2c40b2?qlt=65&fmt=webp&hei=350&wid=350	Wild Fable	Women's Kaya Pointed Toe Stiletto Heels – Wild Fable™ Black	$25.00		5	United States
Ankle Boots	https://www.target.com/p/women-s-chelsea-ankle-boots-a-new-day/-/A-87967034	4.5 stars with 91 ratings	https://target.scene7.com/is/image/Target/GUEST_5f3e2d1f-9ce4-4e8c-a50b-4d49e5d4d52e?qlt=65&fmt=webp&hei=350&wid=350	A New Day	Women's Chelsea Ankle Boots – A New Day™ Black	$35.00	30% off	1	United States
Ankle Boots	https://www.target.com/p/women-s-chelsea-boots-wild-fable/-/A-88750578	4.1 stars with 16 ratings	https://target.scene7.com/is/image/Target/GUEST_08b4c6d2-ae29-4fa4-ba7e-9c2e17e6dcd9?qlt=65&fmt=webp&hei=350&wid=350	Wild Fable	Women's Chelsea Boots – Wild Fable™ Black	$30.00		2	United States
Ankle Boots	https://www.target.com/p/women-s-raglan-ankle-boots-london-rag/-/A-1008391999	4.6 stars with 45 ratings	https://target.scene7.com/is/image/Target/GUEST_3d6c9f89-65c4-42af-b2b2-2c9c4ecc8b0b?qlt=65&fmt=webp&hei=350&wid=350	London Rag	Women's Raglan Ankle Boots – London Rag™ Brown	$48.99		3	United States
Ankle Boots	https://www.target.com/p/women-s-block-heel-ankle-boots-a-new-day/-/A-87967042	4.3 stars with 63 ratings	https://target.scene7.com/is/image/Target/GUEST_91c7b3e6-e7e4-4fc3-a2e2-1fad8c3f3c1d?qlt=65&fmt=webp&hei=350&wid=350	A New Day	Women's Block Heel Ankle Boots – A New Day™ Brown	$35.00	Clearance	4	United States
Ankle Boots	https://www.target.com/p/women-s-combat-boots-wild-fable/-/A-88750582	4.0 stars with 29 ratings	https://target.scene7.com/is/image/Target/GUEST_6d2cbf1c-7b5f-42c1-8c2b-b7855c2b4f14?qlt=65&fmt=webp&hei=350&wid=350	Wild Fable	Women's Combat Boots – Wild Fable™ Black	$28.00	20% off	5	United States
Long Boots	https://www.target.com/p/women-s-knee-high-boots-a-new-day/-/A-87967044	4.5 stars with 52 ratings	https://target.scene7.com/is/image/Target/GUEST_7b2b4a7e-9d7e-4b8f-9be4-8c1ff4e87b1b?qlt=65&fmt=webp&hei=350&wid=350	A New Day	Women's Knee High Boots – A New Day™ Black	$45.00		1	United States
Long Boots	https://www.target.com/p/women-s-over-the-knee-boots-london-rag/-/A-1008392003	4.7 stars with 18 ratings	https://target.scene7.com/is/image/Target/GUEST_0ab3f4be-9e2b-42f4-a496-b2e9b9c82f58?qlt=65&fmt=webp&hei=350&wid=350	London Rag	Women's Over the Knee Boots – London Rag™ Black	$58.99		2	United States
Long Boots	https://www.target.com/p/women-s-wide-calf-knee-high-boots-a-new-day/-/A-87967048	4.1 stars with 37 ratings	https://target.scene7.com/is/image/Target/GUEST_c1c80b02-28e6-497c-9e5c-0c8f53dbdca7?qlt=65&fmt=webp&hei=350&wid=350	A New Day	Women's Wide Calf Knee High Boots – A New Day™ Black	$48.00		3	United States
Long Boots	https://www.target.com/p/women-s-tall-boots-wild-fable/-/A-88750590	3.9 stars with 11 ratings	https://target.scene7.com/is/image/Target/GUEST_042b2a8b-c0b3-4e65-a3a0-ae3a8941f05d?qlt=65&fmt=webp&hei=350&wid=350	Wild Fable	Women's Tall Boots – Wild Fable™ Black	$30.00	30% off	4	United States
Long Boots	https://www.target.com/p/women-s-riding-boots-london-rag/-/A-1008392007	4.4 stars with 25 ratings	https://target.scene7.com/is/image/Target/GUEST_99c2d8ca-6c26-45cf-8f25-29bbfc55e114?qlt=65&fmt=webp&hei=350&wid=350	London Rag	Women's Riding Boots – London Rag™ Brown	$54.99		5	United States
Sandals	https://www.target.com/p/women-s-slide-sandals-a-new-day/-/A-87967050	4.2 stars with 103 ratings	https://target.scene7.com/is/image/Target/GUEST_23f9b8d6-5d5f-4252-9c5b-bc07e78c43e1?qlt=65&fmt=webp&hei=350&wid=350	A New Day	Women's Slide Sandals – A New Day™ Black	$15.00		1	United States
Sandals	https://www.target.com/p/women-s-espadrille-wedge-sandals-wild-fable/-/A-88750594	4.0 stars with 44 ratings	https://target.scene7.com/is/image/Target/GUEST_13f1a2c7-19e9-4463-a2dd-8bf455db4a71?qlt=65&fmt=webp&hei=350&wid=350	Wild Fable	Women's Espadrille Wedge Sandals – Wild Fable™ Natural	$22.00		2	United States
Sandals	https://www.target.com/p/women-s-platform-sandals-london-rag/-/A-1008392011	4.6 stars with 32 ratings	https://target.scene7.com/is/image/Target/GUEST_a4e97f1e-4439-43e6-8b2f-3b1c8ef3ac8c?qlt=65&fmt=webp&hei=350&wid=350	London Rag	Women's Platform Sandals – London Rag™ White	$32.99	20% off	3	United States
Sandals	https://www.target.com/p/women-s-t-strap-sandals-a-new-day/-/A-87967054	4.3 stars with 68 ratings	https://target.scene7.com/is/image/Target/GUEST_7a7e5ab3-2a45-4c52-827f-767fd082174e?qlt=65&fmt=webp&hei=350&wid=350	A New Day	Women's T-Strap Sandals – A New Day™ Tan	$18.00	Clearance	4	United States
"""

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎯 Target Intel")
    st.markdown("---")
    st.markdown("**Upload your scraped data**")
    uploaded = st.file_uploader("CSV or TSV file", type=["csv","tsv","txt"])
    st.markdown("---")

    if uploaded:
        sep = "\t" if uploaded.name.endswith((".tsv",".txt")) else ","
        raw_bytes = uploaded.read()
        for enc in ["utf-8", "latin-1", "cp1252", "utf-8-sig"]:
            try:
                df_raw = pd.read_csv(StringIO(raw_bytes.decode(enc)), sep=sep)
                break
            except (UnicodeDecodeError, Exception):
                continue
        else:
            st.error("Could not decode your file. Try saving it as UTF-8 CSV from Excel.")
            st.stop()
    else:
        st.info("No file uploaded — using sample data.")
        df_raw = pd.read_csv(StringIO(SAMPLE), sep="\t")

    # ── Clean ─────────────────────────────────────────────────────────────────
    df_all = df_raw.copy()
    df_all.columns = [c.strip() for c in df_all.columns]

    # Canonical column mapping for Target data
    CANONICAL = {
        "subcategory": "Subcategory",
        "link": "Link",
        "rating": "Rating",
        "image_src": "Image_Src",
        "brand": "Brand",
        "title": "Title",
        "price": "Price",
        "remark": "Campaign_Type",      # treat remark as campaign type
        "ranking": "Ranking",
        "country": "Country",
    }
    df_all.rename(columns={c: CANONICAL.get(c.lower(), c) for c in df_all.columns}, inplace=True)

    # Parse Rating (text like "4.7 stars with 57 ratings") into numeric
    def parse_rating(text):
        if pd.isna(text):
            return np.nan
        match = re.match(r"([\d.]+)", str(text))
        return float(match.group(1)) if match else np.nan

    df_all["Ratings"] = df_all["Rating"].apply(parse_rating)

    # Clean Price: remove $ and commas, convert to float
    if "Price" in df_all.columns:
        df_all["Price"] = df_all["Price"].astype(str).str.replace(r"[$,]", "", regex=True)
        df_all["Price"] = pd.to_numeric(df_all["Price"], errors="coerce")

    # Ensure Ranking numeric
    if "Ranking" in df_all.columns:
        df_all["Ranking"] = pd.to_numeric(df_all["Ranking"], errors="coerce")

    # Drop rows without essential data
    df_all = df_all.dropna(subset=["Brand", "Price", "Ratings"])

    # Campaign flag from Campaign_Type (derived from Remark)
    if "Campaign_Type" not in df_all.columns:
        df_all["Campaign_Type"] = ""
    df_all["Campaign_Type"] = df_all["Campaign_Type"].fillna("").astype(str).str.strip()
    df_all["Campaign_Has"] = df_all["Campaign_Type"].apply(
        lambda x: "Has Campaign" if x not in ["", "nan", "No campaign"] else "No Campaign"
    )

    # ── Filters ───────────────────────────────────────────────────────────────
    st.markdown("**Filters**")
    cats   = sorted(df_all["Subcategory"].dropna().unique().tolist())
    brands = sorted(df_all["Brand"].dropna().unique().tolist())

    # Subcategory filter
    ca, cb = st.columns(2)
    if ca.button("✓ All", key="cat_all", use_container_width=True):
        st.session_state["sel_cats"] = cats
    if cb.button("✕ Clear", key="cat_clear", use_container_width=True):
        st.session_state["sel_cats"] = []
    if "sel_cats" not in st.session_state:
        st.session_state["sel_cats"] = cats
    sel_cats = st.multiselect("Subcategory", cats, key="sel_cats")

    # Brand filter
    ba, bb = st.columns(2)
    if ba.button("✓ All", key="brand_all", use_container_width=True):
        st.session_state["sel_brands"] = brands
    if bb.button("✕ Clear", key="brand_clear", use_container_width=True):
        st.session_state["sel_brands"] = []
    if "sel_brands" not in st.session_state:
        st.session_state["sel_brands"] = brands
    sel_brands = st.multiselect("Brands", brands, key="sel_brands")

    # Apply filters
    df = df_all.copy()
    if sel_cats:
        df = df[df["Subcategory"].isin(sel_cats)]
    if sel_brands:
        df = df[df["Brand"].isin(sel_brands)]

    st.markdown("---")
    st.markdown(f"**{len(df)} products** loaded")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# Target Competitor Intelligence Dashboard")
st.markdown("Upload scraped Target data and get instant competitive insights across price, ratings, rankings, and promotions.")
st.markdown("---")

if df.empty:
    st.warning("No data matches your filters.")
    st.stop()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview & Charts",
    "📁 Category × Brand Pricing",
    "🏷️ Brand Scorecard",
    "📣 Campaign Intelligence",
])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Overview
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    # ── ROW 1 — Share of shelf + Rating distribution ─────────────────────────
    c1, c2 = st.columns([1, 1])

    with c1:
        st.markdown('<p class="section-title">Share of shelf by brand</p>', unsafe_allow_html=True)
        shelf = df["Brand"].value_counts().reset_index()
        shelf.columns = ["Brand", "Count"]
        shelf["Share"] = (shelf["Count"] / shelf["Count"].sum() * 100).round(1)
        fig = px.pie(shelf, values="Count", names="Brand",
                     color_discrete_sequence=COLORS, hole=0.45)
        fig.update_traces(
            textposition="inside", textinfo="percent",
            textfont=dict(size=13, color="white"),
            insidetextorientation="horizontal",
            pull=[0.03] * len(shelf),
        )
        fig.update_layout(
            margin=dict(t=20, b=20, l=20, r=20), height=340, showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02, font=dict(size=12)),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)
        top = shelf.iloc[0]
        st.markdown(f'<div class="insight-box">🏆 <b>{top.Brand}</b> owns <b>{top.Share}%</b> of shelf space — the brand you need to displace or differentiate from.</div>', unsafe_allow_html=True)
        export_csv(shelf[["Brand", "Count", "Share"]], "share_of_shelf.csv")

    with c2:
        st.markdown('<p class="section-title">Rating distribution by brand</p>', unsafe_allow_html=True)
        brand_order_rating = sorted(df["Brand"].unique().tolist())
        fig2 = px.box(df, x="Brand", y="Ratings", color="Brand",
                      color_discrete_sequence=COLORS, points="all",
                      category_orders={"Brand": brand_order_rating})
        fig2.update_layout(showlegend=False, margin=dict(t=10, b=100, l=0, r=0),
                           height=320, paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(0,0,0,0)",
                           yaxis=dict(range=[0, 5.5], gridcolor="#E8E4DE"),
                           xaxis=dict(tickangle=-90),
                           xaxis_title="", yaxis_title="Rating")
        fig2.update_traces(marker_size=6)
        st.plotly_chart(fig2, use_container_width=True)
        low_brand = df.groupby("Brand")["Ratings"].mean().idxmin()
        st.markdown(f'<div class="warn-box">⚠️ <b>{low_brand}</b> has the lowest average rating — their unhappy customers are your acquisition opportunity.</div>', unsafe_allow_html=True)
        rating_summary = df.groupby("Brand")["Ratings"].agg(["mean", "min", "max", "count"]).round(2).reset_index()
        rating_summary.columns = ["Brand", "Avg_Rating", "Min_Rating", "Max_Rating", "Products"]
        export_csv(rating_summary, "rating_distribution.csv")

    st.markdown("---")

    # ── ROW 2 — Price positioning ─────────────────────────────────────────────
    st.markdown('<p class="section-title">Price positioning by brand</p>', unsafe_allow_html=True)
    brand_order_price = sorted(df["Brand"].unique().tolist())
    fig3 = px.violin(df, x="Brand", y="Price", color="Brand",
                     color_discrete_sequence=COLORS, box=True, points="all",
                     category_orders={"Brand": brand_order_price})
    fig3.update_layout(showlegend=False, margin=dict(t=10, b=100, l=0, r=0),
                       height=380, paper_bgcolor="rgba(0,0,0,0)",
                       plot_bgcolor="rgba(0,0,0,0)",
                       yaxis=dict(gridcolor="#E8E4DE"),
                       xaxis=dict(tickangle=-90),
                       xaxis_title="", yaxis_title="Price ($)")
    st.plotly_chart(fig3, use_container_width=True)
    price_summary = df.groupby("Brand")["Price"].agg(["median", "mean", "min", "max", "count"]).round(1).reset_index()
    price_summary.columns = ["Brand", "Median_Price", "Avg_Price", "Min_Price", "Max_Price", "Products"]
    export_csv(price_summary, "price_positioning.csv")

    st.markdown("---")

    # ── ROW 3 — Category heatmap + Price tier ────────────────────────────────
    c7, c9 = st.columns([1, 1])

    with c7:
        st.markdown('<p class="section-title">Brand × category presence heatmap</p>', unsafe_allow_html=True)
        heatmap_df = df.groupby(["Brand", "Subcategory"]).size().unstack(fill_value=0)
        row_order = heatmap_df.sum(axis=1).sort_values(ascending=False).index
        col_order = heatmap_df.sum(axis=0).sort_values(ascending=False).index
        heatmap_df = heatmap_df.loc[row_order, col_order]
        fig7 = px.imshow(heatmap_df, color_continuous_scale="Greens", text_auto=True, aspect="auto")
        fig7.update_layout(margin=dict(t=10, b=10, l=0, r=0), height=320,
                           paper_bgcolor="rgba(0,0,0,0)",
                           coloraxis_showscale=False, xaxis_title="", yaxis_title="",
                           xaxis=dict(tickangle=-90))
        fig7.update_traces(textfont_size=13)
        st.plotly_chart(fig7, use_container_width=True)
        st.markdown('<div class="insight-box">📊 Dark cells = dominant brand-category combinations. White/empty cells = gaps your brand can enter with less competition.</div>', unsafe_allow_html=True)
        heatmap_export = heatmap_df.reset_index()
        export_csv(heatmap_export, "brand_category_presence.csv")

    with c9:
        q1, q3 = df["Price"].quantile(0.25), df["Price"].quantile(0.75)
        def tier(p):
            if p <= q1: return "Budget"
            elif p <= q3: return "Mid-market"
            else: return "Premium"
        df["Tier"] = df["Price"].apply(tier)

        st.markdown(
            f'<p class="section-title">Price tier distribution — where is the crowd?'
            f'&nbsp;<span style="font-weight:400;font-size:12px;color:#6B6B6B;">'
            f'Budget ≤ ${q1:,.0f} &nbsp;|&nbsp; Mid-market ${q1:,.0f}–${q3:,.0f} &nbsp;|&nbsp; Premium > ${q3:,.0f}'
            f'</span></p>',
            unsafe_allow_html=True
        )
        tier_df = df.groupby(["Tier", "Brand"]).size().reset_index(name="Count")
        tier_totals = tier_df.groupby("Tier")["Count"].sum().sort_values(ascending=False)
        tier_order_sorted = tier_totals.index.tolist()
        fig9 = px.bar(tier_df, x="Tier", y="Count", color="Brand",
                      color_discrete_sequence=COLORS,
                      category_orders={"Tier": tier_order_sorted})
        fig9.update_layout(margin=dict(t=10, b=10, l=0, r=0), height=320,
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           yaxis=dict(gridcolor="#E8E4DE", title="Products"),
                           xaxis=dict(tickangle=-90),
                           xaxis_title="",
                           legend=dict(orientation="h", yanchor="bottom", y=1.01))
        st.plotly_chart(fig9, use_container_width=True)
        export_csv(tier_df, "price_tier_distribution.csv")

    st.markdown("---")

    # ── ROW 4 — All ranked products table WITH IMAGES ────────────────────────
    n_products = len(df)
    st.markdown(
        f'<p class="section-title">🏅 All ranked products — your benchmark list'
        f'&nbsp;<span style="font-weight:400;font-size:12px;color:#6B6B6B;">{n_products} SKUs · sorted by ranking</span></p>',
        unsafe_allow_html=True,
    )

    show_cols = [c for c in ["Ranking","Image_Src","Brand","Title","Subcategory","Price","Ratings","Campaign_Type"] if c in df.columns]
    all_products = df.sort_values("Ranking", na_position="last")[show_cols].reset_index(drop=True)
    all_products.index += 1

    col_cfg = {
        "Price":         st.column_config.NumberColumn("Price ($)", format="$%.2f"),
        "Ratings":       st.column_config.NumberColumn("Ratings ⭐", format="%.1f"),
        "Ranking":       st.column_config.NumberColumn("Rank #", format="%d"),
        "Campaign_Type": st.column_config.TextColumn("Remark"),
    }
    if "Image_Src" in all_products.columns:
        col_cfg["Image_Src"] = st.column_config.ImageColumn("Preview", help="Product thumbnail from retailer", width="small")

    tbl_height = min(1400, max(400, n_products * 120 + 40))
    st.dataframe(all_products, column_config=col_cfg, use_container_width=True, height=tbl_height, row_height=120)

    export_cols = [c for c in show_cols if c != "Image_Src"]
    export_csv(df.sort_values("Ranking", na_position="last")[export_cols].reset_index(drop=True), "all_ranked_products.csv")

    st.markdown("---")
    st.markdown('<p style="font-size:12px;color:#888">Built for Target competitive intelligence · Upload fresh scraped data weekly for trend tracking</p>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — Category × Brand Pricing Matrix
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("## 📁 Category × Brand Average Price Matrix")
    st.markdown("Filtered by the sidebar — select **All** in Subcategory and all brands to see the full picture.")
    st.markdown("---")

    grp = (
        df.groupby(["Subcategory", "Brand"])
        .agg(
            Avg_Price=("Price", "mean"),
            Products=("Price", "count"),
            Avg_Rating=("Ratings", "mean"),
        )
        .reset_index()
    )
    grp["Avg_Price"] = grp["Avg_Price"].round(1)
    grp["Avg_Rating"] = grp["Avg_Rating"].round(2)

    pivot = grp.pivot_table(index="Brand", columns="Subcategory", values="Avg_Price", aggfunc="mean")
    pivot = pivot.round(1)
    pivot = pivot.loc[pivot.mean(axis=1).sort_values(ascending=False).index]

    st.markdown('<p class="section-title">Average price heatmap — Subcategory × Brand ($)</p>', unsafe_allow_html=True)

    fig_heat = px.imshow(
        pivot,
        color_continuous_scale="RdYlGn_r",
        text_auto=True,
        aspect="auto",
        labels=dict(color="Avg Price ($)"),
    )
    fig_heat.update_layout(
        margin=dict(t=80, b=10, l=0, r=10),
        height=max(300, len(pivot) * 60),
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis_title="",
        yaxis_title="",
        coloraxis_colorbar=dict(title="$"),
        xaxis=dict(
            side="top",
            tickangle=-90,
            tickfont=dict(size=12),
        ),
    )
    fig_heat.update_traces(textfont_size=12)
    st.plotly_chart(fig_heat, use_container_width=True)
    st.markdown('<div class="insight-box">🟥 Red = higher avg price in that cell &nbsp;|&nbsp; 🟩 Green = lower avg price. Use this to spot where competitors price aggressively in specific categories.</div>', unsafe_allow_html=True)

    export_csv(grp, "avg_price_heatmap.csv")

    st.markdown("---")

    st.markdown('<p class="section-title">Full detail — subcategory × brand breakdown</p>', unsafe_allow_html=True)
    grp_display = grp.sort_values(["Subcategory", "Avg_Price"], ascending=[True, False]).reset_index(drop=True)
    grp_display.index += 1

    st.dataframe(
        grp_display,
        column_config={
            "Avg_Price":   st.column_config.NumberColumn("Avg Price ($)", format="$%.2f"),
            "Avg_Rating":  st.column_config.NumberColumn("Avg Rating ⭐", format="%.2f"),
            "Products":    st.column_config.NumberColumn("# Products", format="%d"),
            "Subcategory": st.column_config.TextColumn("Subcategory"),
            "Brand":       st.column_config.TextColumn("Brand"),
        },
        use_container_width=True,
        height=500,
    )
    export_csv(grp_display.reset_index(drop=True), "subcategory_brand_detail.csv")

    st.markdown("---")
    st.markdown('<p style="font-size:12px;color:#888">Filtered by sidebar selections. Select All to see full dataset.</p>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — Brand Scorecard
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("## 🏷️ Brand Scorecard")
    st.markdown("A single table summarising every brand's competitive position across all key metrics.")
    st.markdown("---")

    sc = df.groupby("Brand").agg(
        Total_Products=("Brand", "count"),
        Avg_Price=("Price", "mean"),
        Min_Price=("Price", "min"),
        Max_Price=("Price", "max"),
        Avg_Rating=("Ratings", "mean"),
        Best_Ranking=("Ranking", "min"),
        Avg_Ranking=("Ranking", "mean"),
        Categories=("Subcategory", "nunique"),
    ).reset_index()



    for col in ["Avg_Price", "Avg_Rating", "Avg_Ranking"]:
        sc[col] = sc[col].round(2)
    sc["Min_Price"] = sc["Min_Price"].round(1)
    sc["Max_Price"] = sc["Max_Price"].round(1)

    sc = sc.sort_values("Avg_Ranking").reset_index(drop=True)
    sc.index += 1

    st.dataframe(
        sc,
        column_config={
            "Brand":               st.column_config.TextColumn("Brand", width="medium"),
            "Total_Products":      st.column_config.NumberColumn("# Products", format="%d"),
            "Avg_Price":           st.column_config.NumberColumn("Avg Price ($)", format="$%.2f"),
            "Min_Price":           st.column_config.NumberColumn("Min Price ($)", format="$%.1f"),
            "Max_Price":           st.column_config.NumberColumn("Max Price ($)", format="$%.1f"),
            "Avg_Rating":          st.column_config.NumberColumn("Avg Rating ⭐", format="%.2f"),
            "Best_Ranking":        st.column_config.NumberColumn("Best Rank #", format="%d"),
            "Avg_Ranking":         st.column_config.NumberColumn("Avg Rank #", format="%.1f"),
            "Categories":          st.column_config.NumberColumn("Categories Covered", format="%d"),
           
        },
        use_container_width=True,
        height=450,
    )
    export_csv(sc.reset_index(drop=True), "brand_scorecard.csv")

    st.markdown("---")
    st.markdown('<p style="font-size:12px;color:#888">Filtered by sidebar selections.</p>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — Campaign Intelligence
# ════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("## 📣 Campaign Intelligence")
    st.markdown("Understand which promotions are driving shelf presence per brand, and how discounting spreads across the competitive landscape.")
    st.markdown("---")

    # ── Campaign type breakdown table ─────────────────────────────────────────
    st.markdown('<p class="section-title">Remark breakdown — who is discounting, and how?</p>', unsafe_allow_html=True)

    camp_summary = (
        df.groupby("Campaign_Type")
        .agg(
            Products=("Brand", "count"),
            Brands=("Brand", "nunique"),
            Avg_Price=("Price", "mean"),
            Avg_Rating=("Ratings", "mean"),
            Avg_Ranking=("Ranking", "mean"),
        )
        .reset_index()
        .sort_values("Products", ascending=False)
    )
    camp_summary["Avg_Price"]   = camp_summary["Avg_Price"].round(1)
    camp_summary["Avg_Rating"]  = camp_summary["Avg_Rating"].round(2)
    camp_summary["Avg_Ranking"] = camp_summary["Avg_Ranking"].round(1)
    camp_summary["Share_%"] = (camp_summary["Products"] / camp_summary["Products"].sum() * 100).round(1)
    camp_summary = camp_summary.reset_index(drop=True)
    camp_summary.index += 1

    st.dataframe(
        camp_summary,
        column_config={
            "Campaign_Type": st.column_config.TextColumn("Remark", width="large"),
            "Products":      st.column_config.NumberColumn("# Products", format="%d"),
            "Brands":        st.column_config.NumberColumn("Brands", format="%d"),
            "Avg_Price":     st.column_config.NumberColumn("Avg Price ($)", format="$%.1f"),
            "Avg_Rating":    st.column_config.NumberColumn("Avg Rating ⭐", format="%.2f"),
            "Avg_Ranking":   st.column_config.NumberColumn("Avg Rank #", format="%.1f"),
            "Share_%":       st.column_config.ProgressColumn(
                "Share of Products %", min_value=0, max_value=100, format="%.1f%%",
            ),
        },
        use_container_width=True,
        height=380,
    )
    export_csv(camp_summary.reset_index(drop=True), "remark_breakdown.csv")

    st.markdown("---")

    # ── Remark × Brand product count heatmap ─────────────────────────────────
    st.markdown('<p class="section-title">Remark × brand — product count heatmap</p>', unsafe_allow_html=True)
    

    camp_heatmap = (
        df.groupby(["Brand", "Campaign_Type"])
        .size()
        .unstack(fill_value=0)
    )
    camp_heatmap = camp_heatmap.loc[
        camp_heatmap.sum(axis=1).sort_values(ascending=False).index,
        camp_heatmap.sum(axis=0).sort_values(ascending=False).index,
    ]

    fig_camp_heat = px.imshow(
        camp_heatmap,
        color_continuous_scale="Blues",
        text_auto=True,
        aspect="auto",
        labels=dict(color="# Products"),
    )
    fig_camp_heat.update_layout(
        margin=dict(t=120, b=10, l=0, r=10),
        height=max(300, len(camp_heatmap) * 60 + 120),
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis_title="",
        yaxis_title="",
        coloraxis_colorbar=dict(title="# Products"),
        xaxis=dict(
            side="top",
            tickangle=-90,
            tickfont=dict(size=12),
        ),
        yaxis=dict(
            tickfont=dict(size=12),
        ),
    )
    fig_camp_heat.update_traces(textfont_size=13)
    st.plotly_chart(fig_camp_heat, use_container_width=True)

    most_active_brand = camp_heatmap.drop(columns=["No campaign"], errors="ignore").sum(axis=1).idxmax() if len(camp_heatmap.columns) > 1 else "N/A"
    st.markdown(f'<div class="insight-box">📣 <b>{most_active_brand}</b> appears most across active remark types </div>', unsafe_allow_html=True)

    camp_heat_export = camp_heatmap.reset_index()
    export_csv(camp_heat_export, "remark_brand_heatmap.csv")

    st.markdown("---")
    st.markdown('<p style="font-size:12px;color:#888">Filtered by sidebar selections.</p>', unsafe_allow_html=True)
