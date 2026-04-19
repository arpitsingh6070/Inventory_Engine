import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from db_functions import (
    connect_to_db,
    get_basic_info,
    get_all_products, get_products_dropdown, get_category_list,
    get_products_by_category, search_products,
    add_product, update_product_price,
    get_product_history, needs_restock,
    get_all_suppliers, get_suppliers_dropdown, get_supplier_performance,
    get_stock_entries, get_low_stock_products, record_stock_movement,
    get_reorders, place_reorder, mark_reorder_received, get_reorder_status_summary,
    get_shipments,
    get_monthly_sales_trend, get_monthly_restock_trend,
    get_category_breakdown, get_top_products_by_value,
    get_stock_status_counts, get_sales_vs_restock, get_recent_activity,
)

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="InventoryPro | Smart Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
#  GLOBAL CSS — Premium Dark Theme
# ─────────────────────────────────────────────────────────────────────────────
st.html("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.stApp { background: #0b0f1a; color: #e2e8f0; }

/* SIDEBAR */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1526 0%, #0b0f1a 100%);
    border-right: 1px solid rgba(99,102,241,0.2);
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span { color: #cbd5e1 !important; }

/* KPI CARD */
.kpi-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.01) 100%);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 16px;
    padding: 20px 22px;
    position: relative;
    overflow: hidden;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    backdrop-filter: blur(8px);
    margin-bottom: 4px;
}
.kpi-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 16px 48px rgba(99,102,241,0.22);
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 16px 16px 0 0;
}
.kpi-indigo::before { background: linear-gradient(90deg, #6366f1, #818cf8); }
.kpi-green::before  { background: linear-gradient(90deg, #22c55e, #4ade80); }
.kpi-amber::before  { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.kpi-red::before    { background: linear-gradient(90deg, #ef4444, #f87171); }
.kpi-cyan::before   { background: linear-gradient(90deg, #06b6d4, #22d3ee); }
.kpi-purple::before { background: linear-gradient(90deg, #a855f7, #c084fc); }
.kpi-teal::before   { background: linear-gradient(90deg, #14b8a6, #2dd4bf); }
.kpi-orange::before { background: linear-gradient(90deg, #f97316, #fb923c); }
.kpi-pink::before   { background: linear-gradient(90deg, #ec4899, #f472b6); }

.kpi-icon  { font-size: 1.9rem; line-height: 1; margin-bottom: 8px; display: block; }
.kpi-value { font-size: 1.8rem; font-weight: 800; color: #f8fafc; line-height: 1.15; margin-bottom: 4px; }
.kpi-label { font-size: 0.73rem; font-weight: 500; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.08em; }

/* SECTION HEADERS */
.section-header {
    background: linear-gradient(90deg, #6366f1 0%, #a855f7 55%, #06b6d4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 1.65rem; font-weight: 800; margin-bottom: 2px;
}
.section-sub { color: #64748b; font-size: 0.85rem; margin-bottom: 1.2rem; }

/* DIVIDER */
.section-divider { border: none; border-top: 1px solid rgba(99,102,241,0.13); margin: 1.5rem 0; }

/* ACTIVITY FEED */
.act-item {
    display: flex; align-items: center; gap: 12px;
    padding: 9px 14px; border-radius: 10px;
    border: 1px solid rgba(99,102,241,0.1); margin-bottom: 5px;
    background: rgba(255,255,255,0.02); transition: background 0.2s;
}
.act-item:hover { background: rgba(99,102,241,0.08); }

/* LOGO */
.sidebar-logo { text-align: center; padding: 16px 8px 22px; }
.logo-text {
    font-size: 1.45rem; font-weight: 800;
    background: linear-gradient(90deg, #6366f1, #a855f7);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; letter-spacing: -0.5px;
}
.logo-sub { font-size: 0.7rem; color: #475569; letter-spacing: 0.12em; text-transform: uppercase; }

/* BUTTONS */
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #818cf8) !important;
    color: white !important; border: none !important; border-radius: 10px !important;
    font-weight: 600 !important; padding: 10px 24px !important;
    transition: all 0.2s !important; box-shadow: 0 4px 15px rgba(99,102,241,0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important; box-shadow: 0 8px 28px rgba(99,102,241,0.5) !important;
}

/* FORMS */
[data-testid="stForm"] {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(99,102,241,0.18); border-radius: 14px; padding: 18px;
}

/* DATAFRAMES */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(99,102,241,0.18) !important; border-radius: 12px !important; overflow: hidden;
}

/* EXPANDER */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(99,102,241,0.18) !important; border-radius: 12px !important;
}

/* TABS */
[data-testid="stTabs"] button { font-weight: 600; font-size: 0.88rem; color: #64748b !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color: #818cf8 !important; border-bottom-color: #6366f1 !important; }

/* INPUTS */
.stSelectbox > div > div,
.stNumberInput > div > div > input,
.stTextInput > div > div > input,
.stTextArea textarea {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(99,102,241,0.28) !important;
    border-radius: 10px !important; color: #e2e8f0 !important;
}
[data-testid="stWidgetLabel"], label, [data-testid="stMarkdownContainer"] p {
    color: #e2e8f0 !important;
    font-weight: 500 !important;
}

/* ALERTS */
[data-testid="stAlert"] { border-radius: 12px !important; }
</style>
""")

# ─────────────────────────────────────────────────────────────────────────────
#  SHARED CHART LAYOUT
# ─────────────────────────────────────────────────────────────────────────────
CL = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter', color='#94a3b8', size=12),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(bgcolor='rgba(255,255,255,0.04)', bordercolor='rgba(99,102,241,0.2)', borderwidth=1),
    colorway=['#6366f1','#22c55e','#f59e0b','#ef4444','#06b6d4','#a855f7','#ec4899','#14b8a6'],
)
AXIS_STYLE = dict(gridcolor='rgba(99,102,241,0.09)', linecolor='rgba(99,102,241,0.18)',
                  tickfont=dict(color='#64748b'), title_font=dict(color='#94a3b8'))

def style_axes(fig, **yaxis_overrides):
    """Apply consistent dark axis styling. Allows yaxis overrides without kwarg conflicts."""
    ya = {**AXIS_STYLE, **yaxis_overrides}
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**ya)
    return fig

# ─────────────────────────────────────────────────────────────────────────────
#  DB CONNECTION
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_conn():
    return connect_to_db()

conn = get_conn()

# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def fmt_currency(val):
    try:
        v = float(val)
        if v >= 1_00_00_000: return f"Rs {v/1_00_00_000:.1f} Cr"
        if v >= 1_00_000:    return f"Rs {v/1_00_000:.1f} L"
        if v >= 1_000:       return f"Rs {v/1_000:.1f} K"
        return f"Rs {v:,.2f}"
    except Exception:
        return str(val)

def kpi(icon, label, value, color="indigo"):
    st.markdown(f"""
    <div class="kpi-card kpi-{color}">
        <span class="kpi-icon">{icon}</span>
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
    </div>""", unsafe_allow_html=True)

def divider():
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div class="logo-text">📦 InventoryPro</div>
        <div class="logo-sub">SQL · SSMS · Python</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("Navigate", [
        "🏠  Dashboard",
        "📦  Products",
        "🏭  Suppliers",
        "📉  Stock Control",
        "📋  Reorders",
        "🚚  Shipments",
        "📈  Analytics",
    ], label_visibility="collapsed")
    st.markdown("---")
    st.markdown(
        "<div style='color:#475569;font-size:0.7rem;text-align:center;'>"
        "SQL SERVER · new_schema<br><span style='color:#22c55e;font-size:0.8rem'>● CONNECTED</span></div>",
        unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  PAGE: DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
if page == "🏠  Dashboard":
    st.markdown('<div class="section-header">Inventory Intelligence Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Real-time overview of inventory, sales, and supply chain</div>', unsafe_allow_html=True)

    info = get_basic_info(conn)

    # Row 1 — 5 KPIs
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: kpi("🏭", "Total Suppliers",  str(info.get("Total Suppliers", 0)),         "indigo")
    with c2: kpi("📦", "Total Products",   str(info.get("Total Products", 0)),           "cyan")
    with c3: kpi("🗂️", "Categories",        str(info.get("Total Categories", 0)),        "purple")
    with c4: kpi("💵", "Avg Price",          fmt_currency(info.get("Avg Product Price",0)),"teal")
    with c5: kpi("🏦", "Stock Value",        fmt_currency(info.get("Total Stock Value",0)),"green")

    st.markdown("<br>", unsafe_allow_html=True)

    # Row 2 — 4 KPIs
    c6, c7, c8, c9 = st.columns(4)
    with c6: kpi("💳", "Sales (3M)",        fmt_currency(info.get("Total Sale Value (Last 3 Months)",0)),    "indigo")
    with c7: kpi("🔄", "Restock (3M)",      fmt_currency(info.get("Total Restock Value (Last 3 Months)",0)), "green")
    with c8: kpi("⚠️", "Low Stock Alerts",  str(info.get("Low Stock (No Pending Reorder)", 0)),              "amber")
    with c9: kpi("🔃", "Pending Reorders",  str(info.get("Pending Reorders", 0)),                            "red")

    divider()

    # Row 3 — Sales trend + Stock health donut
    col_a, col_b = st.columns([2, 1])

    with col_a:
        st.markdown("#### 📈 Sales & Restock Trend — Last 12 Months")
        sales_df   = get_monthly_sales_trend(conn)
        restock_df = get_monthly_restock_trend(conn)
        fig = go.Figure()
        if not sales_df.empty:
            fig.add_trace(go.Scatter(
                x=sales_df['Month'], y=sales_df['Sales Value'],
                name='Sales', mode='lines+markers',
                line=dict(color='#6366f1', width=3),
                marker=dict(size=7, color='#6366f1',
                            line=dict(color='#312e81', width=2)),
                fill='tozeroy', fillcolor='rgba(99,102,241,0.08)',
            ))
        if not restock_df.empty:
            fig.add_trace(go.Scatter(
                x=restock_df['Month'], y=restock_df['Restock Value'],
                name='Restock', mode='lines+markers',
                line=dict(color='#22c55e', width=3),
                marker=dict(size=7, color='#22c55e',
                            line=dict(color='#14532d', width=2)),
                fill='tozeroy', fillcolor='rgba(34,197,94,0.06)',
            ))
        fig.update_layout(**CL, height=320, yaxis_title='Value (Rs)', hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("#### 🟢 Stock Health")
        status_df = get_stock_status_counts(conn)
        if not status_df.empty:
            color_map_h = {'Healthy':'#22c55e','Warning':'#f59e0b','Low Stock':'#ef4444','Out of Stock':'#7f1d1d'}
            fig2 = go.Figure(go.Pie(
                labels=status_df['Status'], values=status_df['Count'],
                hole=0.62,
                marker_colors=[color_map_h.get(s,'#6366f1') for s in status_df['Status']],
                textinfo='percent+label',
                textfont=dict(color='#e2e8f0', size=10),
            ))
            total_p = status_df['Count'].sum()
            fig2.update_layout(
                **CL, height=320, showlegend=False,
                annotations=[dict(text=f"<b>{total_p}</b><br>Products",
                                  font_size=16, showarrow=False, font_color='#f8fafc')],
            )
            st.plotly_chart(fig2, use_container_width=True)

    divider()

    # Row 4 — Top products + Category treemap
    col_c, col_d = st.columns([1, 1])

    with col_c:
        st.markdown("#### 🏆 Top 10 Products by Stock Value")
        top_df = get_top_products_by_value(conn, 10)
        if not top_df.empty:
            fig3 = go.Figure(go.Bar(
                x=top_df['Stock Value'], y=top_df['Product'],
                orientation='h',
                marker=dict(color=top_df['Stock Value'],
                            colorscale=[[0,'#312e81'],[1,'#818cf8']],
                            showscale=False),
                text=top_df['Stock Value'].apply(fmt_currency),
                textposition='outside', textfont=dict(color='#94a3b8'),
            ))
            fig3.update_layout(**CL, height=380)
            style_axes(fig3, autorange='reversed', gridcolor='rgba(99,102,241,0.07)',
                       tickfont=dict(size=10, color='#94a3b8'))
            st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        st.markdown("#### 🗂️ Category Stock Value")
        cat_df = get_category_breakdown(conn)
        if not cat_df.empty:
            fig4 = px.treemap(
                cat_df, path=['Category'], values='Stock Value',
                color='Products',
                color_continuous_scale=[[0,'#1e1b4b'],[0.5,'#6366f1'],[1,'#a5b4fc']],
                custom_data=['Products','Avg Price'],
            )
            fig4.update_traces(
                textinfo="label+value+percent root",
                hovertemplate="<b>%{label}</b><br>Value: Rs %{value:,.0f}<br>"
                              "Products: %{customdata[0]}<br>Avg Price: Rs %{customdata[1]}<extra></extra>",
                textfont=dict(color='#e2e8f0', size=12),
            )
            fig4.update_layout(**CL, height=380, coloraxis_showscale=False)
            st.plotly_chart(fig4, use_container_width=True)

    divider()

    # Row 5 — Sales vs Restock + Recent activity
    col_e, col_f = st.columns([3, 2])

    with col_e:
        st.markdown("#### ⚖️ Sales vs Restock Units — Last 6 Months")
        svr = get_sales_vs_restock(conn)
        if not svr.empty:
            fig5 = go.Figure()
            fig5.add_trace(go.Bar(x=svr['Month'], y=svr['Units Sold'],
                                  name='Units Sold', marker_color='#6366f1'))
            fig5.add_trace(go.Bar(x=svr['Month'], y=svr['Units Restocked'],
                                  name='Units Restocked', marker_color='#22c55e'))
            fig5.update_layout(**CL, barmode='group', height=280,
                               bargap=0.2, bargroupgap=0.05)
            st.plotly_chart(fig5, use_container_width=True)

    with col_f:
        st.markdown("#### 🕒 Recent Activity")
        act_df = get_recent_activity(conn, 15)
        if not act_df.empty:
            for _, row in act_df.head(12).iterrows():
                icon = "🔴" if row['Type'] == 'Sale' else "🟢"
                sign = "-" if row['Type'] == 'Sale' else "+"
                qty_color = "#f87171" if row['Type'] == 'Sale' else "#4ade80"
                st.markdown(f"""
                <div class="act-item">
                    <span style="font-size:1.1rem">{icon}</span>
                    <div style="flex:1">
                        <div style="font-size:0.82rem;color:#e2e8f0;font-weight:500">{row['Product']}</div>
                        <div style="font-size:0.72rem;color:#64748b">{str(row['Date'])[:10]}</div>
                    </div>
                    <div style="text-align:right">
                        <div style="font-size:0.84rem;font-weight:700;color:{qty_color}">{sign}{row['Qty']}</div>
                        <div style="font-size:0.7rem;color:#475569">{row['Type']}</div>
                    </div>
                </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  PAGE: PRODUCTS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "📦  Products":
    st.markdown('<div class="section-header">Product Management</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">View, search, filter, add, and update products</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1: search_kw    = st.text_input("🔍 Search", placeholder="Product name or category…")
    with col2: cats         = ["All"] + get_category_list(conn); sel_cat = st.selectbox("Category", cats)
    with col3: status_f     = st.selectbox("Status", ["All","Healthy","Warning","Low Stock","Out of Stock"])

    if search_kw.strip():
        df = search_products(conn, search_kw.strip())
    elif sel_cat != "All":
        df = get_products_by_category(conn, sel_cat)
    else:
        df = get_all_products(conn)

    if status_f != "All" and "Status" in df.columns:
        df = df[df["Status"] == status_f]

    st.caption(f"**{len(df)}** products")
    max_stock = int(df['Stock Qty'].max()) if not df.empty else 100
    st.dataframe(df, use_container_width=True, hide_index=True, height=380,
        column_config={
            "Price (INR)":       st.column_config.NumberColumn(format="Rs %.2f"),
            "Stock Value (INR)": st.column_config.NumberColumn(format="Rs %.2f"),
            "Stock Qty":         st.column_config.ProgressColumn(min_value=0, max_value=max_stock, format="%d"),
        })

    divider()

    tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Product", "✏️ Update Price", "📜 History", "🔎 Restock Check"])

    with tab1:
        sup_list = get_suppliers_dropdown(conn)
        sup_map  = {s[1]: s[0] for s in sup_list}
        with st.form("add_prod"):
            st.markdown("**Add New Product**")
            a1, a2 = st.columns(2)
            with a1:
                p_name    = st.text_input("Product Name")
                p_cat     = st.text_input("Category")
                p_price   = st.number_input("Price", min_value=0.0, step=0.5, format="%.2f")
            with a2:
                p_stock   = st.number_input("Opening Stock", min_value=0, step=1)
                p_reorder = st.number_input("Reorder Level", min_value=0, step=1)
                p_sup     = st.selectbox("Supplier", list(sup_map.keys()))
            if st.form_submit_button("➕ Add Product"):
                if not p_name.strip():
                    st.error("Product name is required.")
                else:
                    ok, msg = add_product(conn, p_name, p_cat, p_price, p_stock, p_reorder, sup_map[p_sup])
                    st.success(f"✅ {msg}") if ok else st.error(f"❌ {msg}")

    with tab2:
        prods    = get_products_dropdown(conn)
        prod_map = {f"#{r[0]} — {r[1]}": r[0] for r in prods}
        with st.form("upd_price"):
            st.markdown("**Update Product Price**")
            sel_p     = st.selectbox("Product", list(prod_map.keys()))
            new_price = st.number_input("New Price", min_value=0.01, step=0.5, format="%.2f")
            if st.form_submit_button("💾 Update"):
                ok, msg = update_product_price(conn, prod_map[sel_p], new_price)
                st.success(f"✅ {msg}") if ok else st.error(f"❌ {msg}")

    with tab3:
        prods2   = get_products_dropdown(conn)
        pmap2    = {f"#{r[0]} — {r[1]}": r[0] for r in prods2}
        sel_h    = st.selectbox("Product", list(pmap2.keys()), key="hist_sel")
        if st.button("📜 Load History"):
            hist   = get_product_history(conn, pmap2[sel_h])
            if hist.empty:
                st.info("No history found.")
            else:
                fig_h = go.Figure()
                for ctype, color in [("Sale","#ef4444"),("Restock","#22c55e")]:
                    sub = hist[hist['change_type'] == ctype]
                    if not sub.empty:
                        fig_h.add_trace(go.Scatter(
                            x=sub['entry_date'], y=sub['change_quantity'].abs(),
                            name=ctype, mode='lines+markers',
                            line=dict(color=color, width=2),
                            marker=dict(color=color, size=6),
                        ))
                fig_h.update_layout(**CL, height=240, title_text='Movement Timeline')
                st.plotly_chart(fig_h, use_container_width=True)
                st.dataframe(hist, use_container_width=True, hide_index=True)

    with tab4:
        prods3  = get_products_dropdown(conn)
        pmap3   = {f"#{r[0]} — {r[1]}": r[0] for r in prods3}
        sel_c   = st.selectbox("Product", list(pmap3.keys()), key="chk_sel")
        if st.button("🔍 Check"):
            needs, stock, level = needs_restock(conn, pmap3[sel_c])
            pct = min(stock / level, 1.0) if level else 1.0
            if needs:
                st.error(f"⚠️ RESTOCK NEEDED — Stock: {stock} | Level: {level} ({pct*100:.1f}%)")
            else:
                st.success(f"✅ Healthy — Stock: {stock} | Level: {level} ({pct*100:.1f}%)")
            st.progress(pct)


# ─────────────────────────────────────────────────────────────────────────────
#  PAGE: SUPPLIERS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "🏭  Suppliers":
    st.markdown('<div class="section-header">Supplier Directory</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Contact information and supply performance for all vendors</div>', unsafe_allow_html=True)

    sup_df = get_all_suppliers(conn)
    st.dataframe(sup_df, use_container_width=True, hide_index=True, height=400,
        column_config={"Total Stock Value (INR)": st.column_config.NumberColumn(format="Rs %.2f")})

    divider()

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown("#### 📊 Shipments per Supplier")
        perf = get_supplier_performance(conn)
        if not perf.empty:
            fig_s = px.bar(perf, x='Supplier', y='Total Shipments',
                           text='Total Shipments',
                           color='Total Units Received',
                           color_continuous_scale=[[0,'#1e1b4b'],[1,'#818cf8']])
            fig_s.update_traces(textposition='outside', textfont=dict(color='#94a3b8'))
            fig_s.update_layout(**CL, height=340, coloraxis_showscale=False, xaxis_tickangle=-30)
            st.plotly_chart(fig_s, use_container_width=True)
    with col_s2:
        st.markdown("#### 🏆 Top Suppliers by Stock Value")
        top_sup = sup_df.nlargest(10, 'Total Stock Value (INR)')
        fig_sv = px.bar(top_sup, x='Total Stock Value (INR)', y='Supplier Name',
                        orientation='h',
                        color='Total Stock Value (INR)',
                        color_continuous_scale=[[0,'#1e1b4b'],[1,'#a855f7']])
        fig_sv.update_layout(**CL, height=340, coloraxis_showscale=False)
        style_axes(fig_sv, autorange='reversed', tickfont=dict(size=10))
        st.plotly_chart(fig_sv, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
#  PAGE: STOCK CONTROL
# ─────────────────────────────────────────────────────────────────────────────
elif page == "📉  Stock Control":
    st.markdown('<div class="section-header">Stock Control Center</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Monitor movements, record sales/restocks, manage alerts</div>', unsafe_allow_html=True)

    tab_log, tab_rec, tab_low = st.tabs(["📋 Movement Log", "📝 Record Movement", "⚠️ Low Stock"])

    with tab_log:
        limit = st.slider("Show last N entries", 50, 500, 200, step=50)
        entries = get_stock_entries(conn, limit)
        if not entries.empty:
            c1, c2, c3 = st.columns(3)
            sales_n   = len(entries[entries['Type']=='Sale'])
            restock_n = len(entries[entries['Type']=='Restock'])
            with c1: kpi("🔴", "Sale Entries",    str(sales_n),        "red")
            with c2: kpi("🟢", "Restock Entries", str(restock_n),      "green")
            with c3: kpi("📋", "Total Entries",   str(len(entries)),   "indigo")
            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(entries, use_container_width=True, hide_index=True, height=380)

    with tab_rec:
        prods   = get_products_dropdown(conn)
        pmap_s  = {f"#{r[0]} — {r[1]}": r[0] for r in prods}
        with st.form("rec_mov"):
            st.markdown("**Record a Stock Movement**")
            b1, b2, b3 = st.columns(3)
            with b1: sel_mov = st.selectbox("Product", list(pmap_s.keys()))
            with b2: mov_type = st.radio("Type", ["Sale", "Restock"], horizontal=True)
            with b3: qty_mov  = st.number_input("Quantity", min_value=1, step=1)
            if st.form_submit_button("✅ Record"):
                ok, msg = record_stock_movement(conn, pmap_s[sel_mov], mov_type, qty_mov)
                st.success(f"✅ {msg}") if ok else st.error(f"❌ {msg}")

    with tab_low:
        low_df = get_low_stock_products(conn)
        if low_df.empty:
            st.success("🎉 All products are above reorder level!")
        else:
            st.error(f"🚨 **{len(low_df)}** products below reorder level")
            st.dataframe(low_df, use_container_width=True, hide_index=True,
                column_config={"Stock Pct": st.column_config.ProgressColumn(
                    min_value=0, max_value=100, format="%.1f%%")})
            fig_low = px.bar(low_df.head(20), x='product_name', y='Stock Pct',
                             text='Stock Pct', color='Stock Pct',
                             color_continuous_scale=[[0,'#7f1d1d'],[0.5,'#ef4444'],[1,'#f59e0b']],
                             title='Stock % of Reorder Level')
            fig_low.add_hline(y=100, line_dash='dash', line_color='#22c55e',
                              annotation_text='Reorder Level', annotation_font_color='#22c55e')
            fig_low.update_traces(texttemplate='%{text:.1f}%', textposition='outside',
                                  textfont=dict(color='#94a3b8'))
            fig_low.update_layout(**CL, height=340, coloraxis_showscale=False, xaxis_tickangle=-35)
            st.plotly_chart(fig_low, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
#  PAGE: REORDERS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "📋  Reorders":
    st.markdown('<div class="section-header">Reorder Management</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Place new reorders and mark them as received (simulates stored procedures)</div>', unsafe_allow_html=True)

    tab_all, tab_place, tab_recv = st.tabs(["📋 All Reorders", "🛒 Place Reorder", "✅ Mark Received"])

    with tab_all:
        summary = get_reorder_status_summary(conn)
        if not summary.empty:
            icon_m  = {'Received':'✅','Ordered':'🔃','Pending':'⏳','Cancelled':'❌'}
            color_m = {'Received':'green','Ordered':'indigo','Pending':'amber','Cancelled':'red'}
            cols    = st.columns(len(summary))
            for i, (_, row) in enumerate(summary.iterrows()):
                with cols[i]:
                    kpi(icon_m.get(row['Status'],'📋'), row['Status'],
                        str(row['Count']), color_m.get(row['Status'],'indigo'))

        st.markdown("<br>", unsafe_allow_html=True)
        ro_df   = get_reorders(conn)
        ro_filt = st.selectbox("Filter", ["All","Ordered","Received","Pending"])
        if ro_filt != "All":
            ro_df = ro_df[ro_df['Status'] == ro_filt]
        st.dataframe(ro_df, use_container_width=True, hide_index=True, height=380)

        if not summary.empty:
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                fig_ro = go.Figure(go.Pie(
                    labels=summary['Status'], values=summary['Count'], hole=0.6,
                    marker_colors=['#22c55e','#6366f1','#f59e0b','#ef4444'][:len(summary)],
                    textinfo='percent+label', textfont=dict(color='#e2e8f0', size=10),
                ))
                fig_ro.update_layout(**CL, height=280, showlegend=False, title_text='Status Mix')
                st.plotly_chart(fig_ro, use_container_width=True)
            with col_r2:
                full_ro = get_reorders(conn)
                if not full_ro.empty:
                    cat_ro = full_ro.groupby('Category')['Qty Ordered'].sum().reset_index()
                    fig_cr = px.bar(cat_ro, x='Category', y='Qty Ordered',
                                    title='Qty Ordered by Category',
                                    color='Qty Ordered',
                                    color_continuous_scale=[[0,'#1e1b4b'],[1,'#818cf8']])
                    fig_cr.update_layout(**CL, height=280, coloraxis_showscale=False, xaxis_tickangle=-25)
                    st.plotly_chart(fig_cr, use_container_width=True)

    with tab_place:
        prods   = get_products_dropdown(conn)
        pmap_ro = {f"#{r[0]} — {r[1]}": r[0] for r in prods}
        with st.form("place_ro"):
            st.markdown("**Place a New Reorder**")
            d1, d2 = st.columns(2)
            with d1: sel_ro_p = st.selectbox("Product", list(pmap_ro.keys()))
            with d2: ro_qty   = st.number_input("Quantity", min_value=1, step=1)
            if st.form_submit_button("🛒 Place Reorder"):
                ok, msg = place_reorder(conn, pmap_ro[sel_ro_p], ro_qty)
                st.success(f"✅ {msg}") if ok else st.error(f"❌ {msg}")

    with tab_recv:
        st.info("ℹ️ Marking a reorder as Received auto-updates stock — simulates a stored procedure.")
        ordered = get_reorders(conn)
        ordered = ordered[ordered['Status'] == 'Ordered']
        if ordered.empty:
            st.success("No pending 'Ordered' reorders.")
        else:
            ro_sel_map = {
                f"#{row['Reorder ID']} — {row['Product']} (Qty: {row['Qty Ordered']})": row['Reorder ID']
                for _, row in ordered.iterrows()
            }
            sel_ro = st.selectbox("Select Reorder", list(ro_sel_map.keys()))
            if st.button("✅ Mark as Received"):
                ok, msg = mark_reorder_received(conn, ro_sel_map[sel_ro])
                st.success(f"✅ {msg}") if ok else st.error(f"❌ {msg}")


# ─────────────────────────────────────────────────────────────────────────────
#  PAGE: SHIPMENTS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "🚚  Shipments":
    st.markdown('<div class="section-header">Shipment Tracker</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Incoming shipment log from all suppliers</div>', unsafe_allow_html=True)

    ship = get_shipments(conn)
    if not ship.empty:
        k1, k2, k3, k4 = st.columns(4)
        with k1: kpi("🚚","Total Shipments",     str(len(ship)),                         "indigo")
        with k2: kpi("📦","Units Received",       f"{ship['Qty Received'].sum():,}",      "green")
        with k3: kpi("🏭","Unique Suppliers",     str(ship['Supplier'].nunique()),         "purple")
        with k4: kpi("🗂️","Unique Products",      str(ship['Product'].nunique()),          "cyan")
        st.markdown("<br>", unsafe_allow_html=True)

    st.dataframe(ship, use_container_width=True, hide_index=True, height=380)

    divider()
    if not ship.empty:
        ship2 = ship.copy()
        ship2['Shipment Date'] = pd.to_datetime(ship2['Shipment Date'])
        ship2['Month'] = ship2['Shipment Date'].dt.strftime('%b %Y')
        monthly = ship2.groupby('Month').agg(Count=('Shipment ID','count'),
                                              Units=('Qty Received','sum')).reset_index()
        col_sh1, col_sh2 = st.columns(2)
        with col_sh1:
            fig_sh1 = px.area(monthly, x='Month', y='Units',
                              title='Monthly Units Received',
                              color_discrete_sequence=['#06b6d4'])
            fig_sh1.update_layout(**CL, height=320)
            st.plotly_chart(fig_sh1, use_container_width=True)
        with col_sh2:
            top_s = ship2.groupby('Supplier')['Qty Received'].sum().nlargest(10).reset_index()
            fig_sh2 = px.bar(top_s, x='Qty Received', y='Supplier', orientation='h',
                             title='Top Suppliers by Volume',
                             color='Qty Received',
                             color_continuous_scale=[[0,'#134e4a'],[1,'#2dd4bf']])
            fig_sh2.update_layout(**CL, height=320, coloraxis_showscale=False)
            style_axes(fig_sh2, autorange='reversed', tickfont=dict(size=10))
            st.plotly_chart(fig_sh2, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
#  PAGE: ANALYTICS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "📈  Analytics":
    st.markdown('<div class="section-header">Advanced Analytics & Reports</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Deep-dive business intelligence insights</div>', unsafe_allow_html=True)

    all_p = get_all_products(conn)

    st.markdown("#### 💵 Price Distribution")
    if not all_p.empty:
        e1, e2 = st.columns(2)
        with e1:
            fig_hst = px.histogram(all_p, x='Price (INR)', nbins=30,
                                   title='Product Price Histogram',
                                   color_discrete_sequence=['#6366f1'])
            fig_hst.update_layout(**CL, height=300)
            st.plotly_chart(fig_hst, use_container_width=True)
        with e2:
            fig_box = px.box(all_p, x='Category', y='Price (INR)', color='Category',
                             title='Price Range by Category',
                             color_discrete_sequence=['#6366f1','#22c55e','#f59e0b',
                                                      '#ef4444','#06b6d4','#a855f7','#ec4899','#14b8a6'])
            fig_box.update_layout(**CL, height=300, showlegend=False, xaxis_tickangle=-20)
            st.plotly_chart(fig_box, use_container_width=True)

    divider()

    st.markdown("#### 📅 Monthly Sales Value (12 Months)")
    s_df = get_monthly_sales_trend(conn)
    if not s_df.empty:
        fig_sal = go.Figure()
        fig_sal.add_trace(go.Bar(x=s_df['Month'], y=s_df['Sales Value'],
                                 name='Sales Value',
                                 marker=dict(color=s_df['Sales Value'],
                                             colorscale=[[0,'#312e81'],[1,'#818cf8']],
                                             showscale=False)))
        fig_sal.add_trace(go.Scatter(x=s_df['Month'], y=s_df['Sales Value'],
                                     name='Trend', mode='lines+markers',
                                     line=dict(color='#f59e0b', width=2, dash='dot'),
                                     marker=dict(color='#f59e0b', size=5)))
        fig_sal.update_layout(**CL, height=300, barmode='overlay')
        st.plotly_chart(fig_sal, use_container_width=True)

    divider()

    st.markdown("#### 🗂️ Category Deep Dive")
    cat2 = get_category_breakdown(conn)
    if not cat2.empty:
        fig_scat = px.scatter(cat2, x='Products', y='Stock Value',
                              size='Products', color='Category',
                              hover_data=['Avg Price'],
                              title='Products vs Stock Value per Category',
                              color_discrete_sequence=['#6366f1','#22c55e','#f59e0b',
                                                       '#ef4444','#06b6d4','#a855f7','#ec4899','#14b8a6'])
        fig_scat.update_layout(**CL, height=340)
        st.plotly_chart(fig_scat, use_container_width=True)
        st.dataframe(cat2, use_container_width=True, hide_index=True,
            column_config={"Stock Value": st.column_config.NumberColumn(format="Rs %.2f"),
                           "Avg Price":   st.column_config.NumberColumn(format="Rs %.2f")})

    divider()

    st.markdown("#### 🔄 Reorder Pattern Analysis")
    ro2 = get_reorders(conn)
    if not ro2.empty:
        f1, f2 = st.columns(2)
        with f1:
            cat_ro = ro2.groupby('Category')['Qty Ordered'].sum().reset_index()
            fig_ro2 = px.pie(cat_ro, names='Category', values='Qty Ordered',
                             title='Reorder Qty by Category',
                             color_discrete_sequence=['#6366f1','#22c55e','#f59e0b',
                                                      '#ef4444','#06b6d4','#a855f7'])
            fig_ro2.update_traces(textinfo='percent+label', textfont=dict(color='#e2e8f0', size=10))
            fig_ro2.update_layout(**CL, height=300, showlegend=False)
            st.plotly_chart(fig_ro2, use_container_width=True)
        with f2:
            sup_ro = ro2.groupby('Supplier')['Qty Ordered'].sum().nlargest(10).reset_index()
            fig_ro3 = px.bar(sup_ro, x='Qty Ordered', y='Supplier', orientation='h',
                             title='Top Suppliers Reordered From',
                             color='Qty Ordered',
                             color_continuous_scale=[[0,'#1e1b4b'],[1,'#818cf8']])
            fig_ro3.update_layout(**CL, height=300, coloraxis_showscale=False)
            style_axes(fig_ro3, autorange='reversed', tickfont=dict(size=10))
            st.plotly_chart(fig_ro3, use_container_width=True)
