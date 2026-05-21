import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
import warnings
warnings.filterwarnings("ignore")

np.random.seed(42)

# ── Sample Data ──
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
revenue    = [120, 135, 118, 152, 168, 145, 172, 189, 162, 195, 210, 230]
orders     = [4200, 4500, 4100, 5000, 5300, 4800, 5500, 5900, 5200, 6100, 6500, 7000]
churn_rate = [8.2, 7.9, 8.5, 7.2, 6.8, 7.1, 6.5, 6.0, 6.3, 5.8, 5.5, 5.2]
categories = ["Electronics", "Clothing", "Grocery", "Home", "Sports"]
cat_rev    = [4500, 2100, 1800, 2800, 950]
seg_labels = ["Champions", "Loyal", "At Risk", "Lost", "New"]
seg_counts = [200, 300, 250, 150, 100]

fig = plt.figure(figsize=(18, 12), facecolor="#0F1923")
fig.suptitle("Customer Behavior Analytics Dashboard",
             fontsize=22, fontweight="bold", color="white", y=0.98)

gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

COLORS = {"blue": "#4FC3F7", "green": "#69F0AE", "orange": "#FFB74D",
          "red": "#EF5350", "purple": "#CE93D8", "bg": "#1A2535", "text": "white"}

def kpi_box(ax, label, value, delta, color):
    ax.set_facecolor(COLORS["bg"])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.5, 0.72, value, ha="center", va="center",
            fontsize=22, fontweight="bold", color=color)
    ax.text(0.5, 0.45, label, ha="center", va="center",
            fontsize=10, color="lightgray")
    ax.text(0.5, 0.2, delta, ha="center", va="center",
            fontsize=9, color=COLORS["green"])

# ── Row 0: KPI Cards ──
kpis = [
    ("Total Revenue", "$1.95M", "↑ 18% YoY", COLORS["blue"]),
    ("Total Orders",  "100,000", "↑ 22% YoY", COLORS["green"]),
    ("Churn Rate",    "5.2%",    "↓ 3.0pp YoY", COLORS["orange"]),
]
for i, (label, value, delta, color) in enumerate(kpis):
    ax = fig.add_subplot(gs[0, i])
    kpi_box(ax, label, value, delta, color)

# ── Row 1 Left: Revenue Trend ──
ax1 = fig.add_subplot(gs[1, :2])
ax1.set_facecolor(COLORS["bg"])
ax1.plot(months, revenue, color=COLORS["blue"], linewidth=2.5, marker="o", markersize=5)
ax1.fill_between(months, revenue, alpha=0.15, color=COLORS["blue"])
ax1.set_title("Monthly Revenue (K$)", color="white", fontsize=12, pad=8)
ax1.tick_params(colors="lightgray"); ax1.spines[:].set_visible(False)
ax1.set_facecolor(COLORS["bg"]); ax1.yaxis.label.set_color("lightgray")
for spine in ax1.spines.values(): spine.set_edgecolor("#2A3B4C")

# ── Row 1 Right: Customer Segments ──
ax2 = fig.add_subplot(gs[1, 2])
ax2.set_facecolor(COLORS["bg"])
clrs = [COLORS["blue"], COLORS["green"], COLORS["orange"], COLORS["red"], COLORS["purple"]]
wedges, texts, autotexts = ax2.pie(
    seg_counts, labels=seg_labels, autopct="%1.0f%%",
    colors=clrs, startangle=140, pctdistance=0.75,
    wedgeprops={"width": 0.5, "edgecolor": "#0F1923", "linewidth": 2}
)
for t in texts: t.set_color("lightgray"); t.set_fontsize(8)
for t in autotexts: t.set_color("white"); t.set_fontsize(8)
ax2.set_title("Customer Segments", color="white", fontsize=12, pad=8)

# ── Row 2 Left: Category Revenue ──
ax3 = fig.add_subplot(gs[2, 0])
ax3.set_facecolor(COLORS["bg"])
bars = ax3.barh(categories, cat_rev, color=clrs, edgecolor="#0F1923", height=0.6)
ax3.set_title("Revenue by Category (K$)", color="white", fontsize=11, pad=8)
ax3.tick_params(colors="lightgray"); ax3.spines[:].set_visible(False)

# ── Row 2 Mid: Churn Rate Trend ──
ax4 = fig.add_subplot(gs[2, 1])
ax4.set_facecolor(COLORS["bg"])
ax4.plot(months, churn_rate, color=COLORS["red"], linewidth=2.5, marker="s", markersize=5)
ax4.fill_between(months, churn_rate, alpha=0.15, color=COLORS["red"])
ax4.set_title("Churn Rate (%) Trend", color="white", fontsize=11, pad=8)
ax4.tick_params(colors="lightgray"); ax4.spines[:].set_visible(False)

# ── Row 2 Right: Orders Bar ──
ax5 = fig.add_subplot(gs[2, 2])
ax5.set_facecolor(COLORS["bg"])
ax5.bar(months, orders, color=COLORS["green"], alpha=0.8, edgecolor="#0F1923", width=0.6)
ax5.set_title("Monthly Orders", color="white", fontsize=11, pad=8)
ax5.tick_params(colors="lightgray", axis="both")
ax5.set_xticklabels(months, rotation=45, fontsize=7)
ax5.spines[:].set_visible(False)

for ax in [ax1, ax3, ax4, ax5]:
    ax.set_facecolor(COLORS["bg"])
    ax.tick_params(colors="lightgray")
    for spine in ax.spines.values():
        spine.set_edgecolor("#2A3B4C")

plt.savefig("reports/dashboard.png", dpi=150, bbox_inches="tight",
            facecolor=fig.get_facecolor())
print("Dashboard saved → reports/dashboard.png")
plt.show()
