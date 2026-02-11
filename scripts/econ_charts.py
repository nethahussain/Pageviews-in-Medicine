import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.font_manager as fm
import numpy as np
from matplotlib.gridspec import GridSpec

# ── Load data ──────────────────────────────────────────────
with open('../data/data.json') as f:
    raw = json.load(f)

years = raw['years']
data = raw['data']
langs = sorted(
    [d for d in data if not d['is_summary']],
    key=lambda x: x['total'], reverse=True
)
summary = [d for d in data if d['is_summary']][0]

lang_names = {
    'en': 'English', 'es': 'Spanish', 'de': 'German', 'ru': 'Russian',
    'fr': 'French', 'ja': 'Japanese', 'it': 'Italian', 'pt': 'Portuguese',
    'zh': 'Chinese', 'pl': 'Polish', 'fa': 'Persian', 'ar': 'Arabic',
    'nl': 'Dutch', 'sv': 'Swedish', 'ko': 'Korean', 'fi': 'Finnish',
    'he': 'Hebrew', 'cs': 'Czech', 'tr': 'Turkish', 'uk': 'Ukrainian',
    'hi': 'Hindi', 'id': 'Indonesian', 'th': 'Thai', 'ro': 'Romanian',
    'hu': 'Hungarian', 'vi': 'Vietnamese', 'bg': 'Bulgarian', 'da': 'Danish',
    'el': 'Greek', 'sr': 'Serbian', 'bn': 'Bengali', 'no': 'Norwegian',
    'hr': 'Croatian', 'sk': 'Slovak', 'kk': 'Kazakh', 'simple': 'Simple Eng.',
    'sl': 'Slovenian', 'lt': 'Lithuanian', 'uz': 'Uzbek', 'ta': 'Tamil',
    'ms': 'Malay', 'ka': 'Georgian', 'az': 'Azerbaijani', 'sq': 'Albanian',
    'ca': 'Catalan', 'tl': 'Tagalog', 'ml': 'Malayalam', 'te': 'Telugu',
    'mr': 'Marathi', 'hy': 'Armenian', 'af': 'Afrikaans', 'lv': 'Latvian',
    'sw': 'Swahili', 'ky': 'Kyrgyz', 'et': 'Estonian', 'bs': 'Bosnian',
    'mk': 'Macedonian', 'mn': 'Mongolian', 'gu': 'Gujarati', 'my': 'Burmese',
    'si': 'Sinhala', 'tg': 'Tajik', 'ne': 'Nepali', 'ur': 'Urdu',
    'km': 'Khmer', 'tk': 'Turkmen', 'kn': 'Kannada', 'am': 'Amharic',
}

def get_name(code):
    return lang_names.get(code, code.upper())

def fmt(val):
    if val >= 1e9:   return f'{val/1e9:.1f}B'
    if val >= 1e6:   return f'{val/1e6:.0f}M'
    if val >= 1e3:   return f'{val/1e3:.0f}K'
    return str(int(val))

# ── Economist palette ──────────────────────────────────────
ECON_RED     = '#E3120B'
ECON_DARK    = '#1A1A1A'
ECON_GREY    = '#595959'
ECON_LIGHT   = '#D9D9D9'
ECON_BG      = '#F7F5F0'  # warm off-white
ECON_FILL    = '#E3120B'
ECON_BLUE    = '#006BA6'   # secondary accent

# ── Register fonts ─────────────────────────────────────────
# Economist uses proprietary fonts; we approximate with Georgia + Franklin Gothic
# Fallback to available serif + sans
try:
    # Try to find good substitutes
    available = set(f.name for f in fm.fontManager.ttflist)
    title_font = 'Georgia' if 'Georgia' in available else 'DejaVu Serif'
    body_font  = 'Franklin Gothic Medium' if 'Franklin Gothic Medium' in available else 'DejaVu Sans'
except:
    title_font = 'DejaVu Serif'
    body_font  = 'DejaVu Sans'

# ── Global rcParams for Economist feel ─────────────────────
plt.rcParams.update({
    'figure.facecolor': ECON_BG,
    'axes.facecolor':   ECON_BG,
    'axes.edgecolor':   'none',
    'axes.labelcolor':  ECON_GREY,
    'text.color':       ECON_DARK,
    'xtick.color':      ECON_GREY,
    'ytick.color':      ECON_GREY,
    'grid.color':       ECON_LIGHT,
    'grid.linewidth':   0.5,
    'font.family':      'sans-serif',
    'font.sans-serif':  [body_font],
    'axes.spines.top':    False,
    'axes.spines.right':  False,
    'axes.spines.left':   False,
    'axes.spines.bottom': False,
})


# ── Label de-overlap helper ────────────────────────────────
def deoverlap_labels(labels, min_gap_data, y_min=None, y_max=None, max_iters=500):
    """
    Iteratively push labels apart so no two are closer than min_gap_data.
    Uses a repulsion approach that spreads labels symmetrically.
    """
    labels = sorted(labels, key=lambda l: l['y'])
    for _ in range(max_iters):
        moved = False
        for i in range(1, len(labels)):
            gap = labels[i]['y'] - labels[i-1]['y']
            if gap < min_gap_data:
                push = (min_gap_data - gap) / 2.0 + 0.001
                labels[i-1]['y'] -= push
                labels[i]['y'] += push
                moved = True
        # Clamp
        if y_min is not None:
            for lab in labels:
                if lab['y'] < y_min:
                    lab['y'] = y_min
        if y_max is not None:
            for lab in labels:
                if lab['y'] > y_max:
                    lab['y'] = y_max
        if not moved:
            break
    return labels

def place_end_labels(ax, label_list, x_pos, fontsize, fontfamily):
    """
    Place non-overlapping end-labels on the right side of the chart.
    Expands y-axis if needed to fit all labels without overlap.
    Draws thin connector lines from data point to displaced label.
    """
    ylim = ax.get_ylim()
    y_range = ylim[1] - ylim[0]
    # Calculate min gap: roughly 1 label-height in data coords
    min_gap = y_range * 0.042 * (fontsize / 8.5)

    # Store original y for connector lines
    for lab in label_list:
        lab['y_orig'] = lab['y']

    # First attempt
    n = len(label_list)
    total_needed = min_gap * n
    current_span = y_range

    # If labels can't fit in current y-range, expand it
    if total_needed > current_span * 0.85:
        new_top = ylim[1] + (total_needed - current_span * 0.85) * 0.6
        ax.set_ylim(ylim[0], new_top)
        ylim = ax.get_ylim()
        y_range = ylim[1] - ylim[0]

    adjusted = deoverlap_labels(
        label_list, min_gap,
        y_min=ylim[0] + min_gap * 0.3,
        y_max=ylim[1] - min_gap * 0.3
    )

    for lab in adjusted:
        ax.text(x_pos, lab['y'], lab['text'], fontsize=fontsize,
                fontfamily=fontfamily, color=lab['color'], va='center',
                fontweight=lab.get('fontweight', 'normal'))
        # Draw a subtle connector line if label was nudged significantly
        displacement = abs(lab['y'] - lab['y_orig'])
        if displacement > min_gap * 0.5:
            ax.plot([x_pos - 0.15, x_pos - 0.05], [lab['y_orig'], lab['y']],
                    color=lab['color'], linewidth=0.6, alpha=0.5)


# ═══════════════════════════════════════════════════════════
#  PAGE 1: ALL LANGUAGES – SMALL MULTIPLES
# ═══════════════════════════════════════════════════════════

top_n = 25
ncols = 5
nrows = 5

fig = plt.figure(figsize=(22, 30), facecolor=ECON_BG)

# Outer margins
fig.subplots_adjust(left=0.04, right=0.97, top=0.90, bottom=0.04, hspace=0.55, wspace=0.28)

# ── Title block (Economist header style) ───────────────────
# Red rule at very top
fig.patches.append(plt.Rectangle(
    (0.04, 0.965), 0.93, 0.006,
    transform=fig.transFigure, facecolor=ECON_RED, edgecolor='none', zorder=10
))

fig.text(0.04, 0.955, 'Wikipedia medical articles',
         fontsize=28, fontweight='bold', fontfamily=title_font,
         color=ECON_DARK, va='top')
fig.text(0.04, 0.935, 'User views by language, 2016–25*',
         fontsize=16, color=ECON_GREY, fontfamily=body_font, va='top')
fig.text(0.04, 0.920, 'Annual pageviews, top 25 languages by total views  |  *2025 figure is year-to-date',
         fontsize=11, color='#888888', fontfamily=body_font, va='top', style='italic')

# ── Small multiples ────────────────────────────────────────
gs = GridSpec(nrows, ncols, figure=fig,
             left=0.04, right=0.97, top=0.86, bottom=0.06,
             hspace=0.85, wspace=0.30)

for idx in range(top_n):
    lang = langs[idx]
    row = idx // ncols
    col = idx % ncols
    ax = fig.add_subplot(gs[row, col])

    views = [lang[str(y)] for y in years]
    name  = get_name(lang['lang'])
    code  = lang['lang']
    peak  = max(views)
    peak_yr = years[views.index(peak)]

    # ── Area fill + line ──
    ax.fill_between(years, views, alpha=0.12, color=ECON_RED, linewidth=0)
    ax.plot(years, views, color=ECON_RED, linewidth=1.8, solid_capstyle='round')

    # Highlight peak with a dot
    ax.plot(peak_yr, peak, 'o', color=ECON_RED, markersize=4, zorder=5)

    # ── Panel title ──
    ax.set_title(f'{name}', fontsize=11, fontweight='bold', fontfamily=title_font,
                 color=ECON_DARK, loc='left', pad=18)

    # ── Red top rule per panel (placed AFTER title so we can position above it) ──
    ax_pos = ax.get_position()
    fig.patches.append(plt.Rectangle(
        (ax_pos.x0, ax_pos.y1 + 0.018), ax_pos.width, 0.0025,
        transform=fig.transFigure, facecolor=ECON_RED, edgecolor='none', zorder=10
    ))

    # ── Total annotation (top right) ──
    ax.text(0.98, 0.95, f'{fmt(lang["total"])} total',
            transform=ax.transAxes, fontsize=7.5, color=ECON_GREY,
            ha='right', va='top', fontfamily=body_font)

    # ── Y-axis formatting ──
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: fmt(v)))
    ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=4, integer=False))
    ax.tick_params(axis='y', labelsize=7.5, length=0, pad=2)
    ax.tick_params(axis='x', labelsize=7, length=0, pad=2)

    # ── X-axis: show only first, middle, last ──
    ax.set_xticks([2016, 2020, 2025])
    ax.set_xticklabels(["'16", "'20", "'25"], fontsize=7.5)
    ax.set_xlim(2015.3, 2025.7)

    # ── Grid ──
    ax.grid(axis='y', linewidth=0.4, color=ECON_LIGHT)
    ax.set_axisbelow(True)

    # ── Bottom baseline ──
    ax.axhline(y=0, color='#AAAAAA', linewidth=0.6)

# ── Source line (bottom) ───────────────────────────────────
fig.text(0.04, 0.018,
         'Source: WikiProject Medicine · mdwiki.toolforge.org/views · Users-agents data',
         fontsize=9, color='#888888', fontfamily=body_font, va='bottom')
fig.text(0.97, 0.018, 'Chart: Economist style',
         fontsize=9, color='#AAAAAA', fontfamily=body_font, va='bottom', ha='right', style='italic')

plt.savefig('../charts/econ_small_multiples_top25.png', dpi=220, bbox_inches='tight',
            facecolor=ECON_BG, edgecolor='none')
plt.close()
print("✓ Page 1: Top 25 small multiples")


# ═══════════════════════════════════════════════════════════
#  PAGE 2: GLOBAL COMBINED TREND (Economist hero chart)
# ═══════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(14, 8), facecolor=ECON_BG)

global_views = [summary[str(y)] for y in years]

# Red rule
fig.patches.append(plt.Rectangle(
    (0.06, 0.94), 0.88, 0.008,
    transform=fig.transFigure, facecolor=ECON_RED, edgecolor='none', zorder=10
))

fig.text(0.06, 0.925, 'The health of health content',
         fontsize=24, fontweight='bold', fontfamily=title_font, color=ECON_DARK, va='top')
fig.text(0.06, 0.865, 'Wikipedia medical articles, total user views across all 337 languages, bn',
         fontsize=13, color=ECON_GREY, fontfamily=body_font, va='top')

# Area + line
ax.fill_between(years, global_views, alpha=0.12, color=ECON_RED, linewidth=0)
ax.plot(years, global_views, color=ECON_RED, linewidth=3, solid_capstyle='round')
ax.plot(years, global_views, 'o', color=ECON_RED, markersize=6, zorder=5)

# Annotate each point
for i, v in enumerate(global_views):
    offset = 16 if i != global_views.index(min(global_views)) else -20
    ax.annotate(f'{v/1e9:.2f}B', (years[i], v),
                textcoords="offset points", xytext=(0, offset),
                ha='center', fontsize=10, fontweight='bold', color=ECON_DARK,
                fontfamily=body_font)

# COVID annotation
ax.annotate('COVID-19\npandemic →', xy=(2020, global_views[4]),
            xytext=(2017.5, global_views[4] * 1.05),
            fontsize=10, color=ECON_GREY, fontfamily=body_font,
            ha='center', va='bottom',
            arrowprops=dict(arrowstyle='->', color=ECON_GREY, lw=1.2))

ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: fmt(v)))
ax.set_xticks(years)
ax.set_xticklabels([str(y) for y in years], fontsize=11)
ax.tick_params(axis='y', labelsize=11, length=0)
ax.tick_params(axis='x', length=0)
ax.grid(axis='y', linewidth=0.5)
ax.set_axisbelow(True)
ax.axhline(y=0, color='#AAAAAA', linewidth=0.6)
ax.set_xlim(2015.3, 2025.7)

fig.text(0.06, 0.02,
         'Source: WikiProject Medicine · mdwiki.toolforge.org/views · *2025 is year-to-date',
         fontsize=9, color='#888888', fontfamily=body_font, va='bottom')

plt.subplots_adjust(top=0.80, bottom=0.08, left=0.08, right=0.96)
plt.savefig('../charts/econ_global_trend.png', dpi=220, bbox_inches='tight',
            facecolor=ECON_BG, edgecolor='none')
plt.close()
print("✓ Page 2: Global hero chart")


# ═══════════════════════════════════════════════════════════
#  PAGE 3: TOP 15 COMBINED LINE CHART
# ═══════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(16, 10), facecolor=ECON_BG)

fig.patches.append(plt.Rectangle(
    (0.05, 0.945), 0.90, 0.008,
    transform=fig.transFigure, facecolor=ECON_RED, edgecolor='none', zorder=10
))
fig.text(0.05, 0.932, 'A polyglot readership',
         fontsize=24, fontweight='bold', fontfamily=title_font, color=ECON_DARK, va='top')
fig.text(0.05, 0.905, 'User views of Wikipedia medical articles by language, top 15',
         fontsize=13, color=ECON_GREY, fontfamily=body_font, va='top')

# Economist uses a muted but distinguishable palette
econ_colors = [
    '#E3120B', '#006BA6', '#00843D', '#F5A623', '#6B3FA0',
    '#1B7A7D', '#D45D00', '#8B0000', '#2E86AB', '#A23B72',
    '#3C6E71', '#E07A5F', '#5F0F40', '#48639C', '#C97C5D'
]

top15 = langs[:15]
labels_p3 = []
for i, lang in enumerate(top15):
    views = [lang[str(y)] for y in years]
    name = get_name(lang['lang'])
    lw = 2.5 if i < 5 else 1.5
    alpha = 1.0 if i < 5 else 0.7

    ax.plot(years, views, color=econ_colors[i], linewidth=lw,
            alpha=alpha, solid_capstyle='round')

    labels_p3.append({
        'y': views[-1], 'text': name, 'color': econ_colors[i],
        'fontweight': 'bold' if i < 5 else 'normal'
    })

ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: fmt(v)))
ax.set_xticks(years)
ax.set_xticklabels([str(y) for y in years], fontsize=10)
ax.tick_params(axis='y', labelsize=10, length=0)
ax.tick_params(axis='x', length=0)
ax.grid(axis='y', linewidth=0.5)
ax.set_axisbelow(True)
ax.axhline(y=0, color='#AAAAAA', linewidth=0.6)
ax.set_xlim(2015.3, 2027.3)  # extra space for labels

# Place de-overlapped labels
place_end_labels(ax, labels_p3, 2025.3, 8.5, body_font)

fig.text(0.05, 0.02,
         'Source: WikiProject Medicine · mdwiki.toolforge.org/views · *2025 is year-to-date',
         fontsize=9, color='#888888', fontfamily=body_font, va='bottom')

plt.subplots_adjust(top=0.85, bottom=0.07, left=0.07, right=0.87)
plt.savefig('../charts/econ_top15_combined.png', dpi=220, bbox_inches='tight',
            facecolor=ECON_BG, edgecolor='none')
plt.close()
print("✓ Page 3: Top 15 combined")


# ═══════════════════════════════════════════════════════════
#  PAGE 4: TOP 15 EXCLUDING ENGLISH (rescaled)
# ═══════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(16, 10), facecolor=ECON_BG)

fig.patches.append(plt.Rectangle(
    (0.05, 0.945), 0.90, 0.008,
    transform=fig.transFigure, facecolor=ECON_RED, edgecolor='none', zorder=10
))
fig.text(0.05, 0.932, 'Beyond English',
         fontsize=24, fontweight='bold', fontfamily=title_font, color=ECON_DARK, va='top')
fig.text(0.05, 0.905, 'User views of Wikipedia medical articles, top 14 non-English languages',
         fontsize=13, color=ECON_GREY, fontfamily=body_font, va='top')

top14_ne = [l for l in langs if l['lang'] != 'en'][:14]
labels_p4 = []
for i, lang in enumerate(top14_ne):
    views = [lang[str(y)] for y in years]
    name = get_name(lang['lang'])
    lw = 2.5 if i < 5 else 1.5
    alpha = 1.0 if i < 5 else 0.7

    ax.plot(years, views, color=econ_colors[i], linewidth=lw,
            alpha=alpha, solid_capstyle='round')
    labels_p4.append({
        'y': views[-1], 'text': name, 'color': econ_colors[i],
        'fontweight': 'bold' if i < 5 else 'normal'
    })

ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: fmt(v)))
ax.set_xticks(years)
ax.set_xticklabels([str(y) for y in years], fontsize=10)
ax.tick_params(axis='y', labelsize=10, length=0)
ax.tick_params(axis='x', length=0)
ax.grid(axis='y', linewidth=0.5)
ax.set_axisbelow(True)
ax.axhline(y=0, color='#AAAAAA', linewidth=0.6)
ax.set_xlim(2015.3, 2027.3)

# Place de-overlapped labels
place_end_labels(ax, labels_p4, 2025.3, 8.5, body_font)

fig.text(0.05, 0.02,
         'Source: WikiProject Medicine · mdwiki.toolforge.org/views · *2025 is year-to-date',
         fontsize=9, color='#888888', fontfamily=body_font, va='bottom')

plt.subplots_adjust(top=0.85, bottom=0.07, left=0.07, right=0.87)
plt.savefig('../charts/econ_top14_no_english.png', dpi=220, bbox_inches='tight',
            facecolor=ECON_BG, edgecolor='none')
plt.close()
print("✓ Page 4: Top 14 excl. English")


# ═══════════════════════════════════════════════════════════
#  PAGE 5: GROWTH CHAMPIONS
# ═══════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(16, 10), facecolor=ECON_BG)

fig.patches.append(plt.Rectangle(
    (0.05, 0.945), 0.90, 0.008,
    transform=fig.transFigure, facecolor=ECON_RED, edgecolor='none', zorder=10
))
fig.text(0.05, 0.932, 'Rising stars',
         fontsize=24, fontweight='bold', fontfamily=title_font, color=ECON_DARK, va='top')
fig.text(0.05, 0.905, 'Fastest-growing languages for medical Wikipedia views, 2016–24 (% change)',
         fontsize=13, color=ECON_GREY, fontfamily=body_font, va='top')
fig.text(0.05, 0.883, 'Languages with >100,000 views in 2016, ranked by percentage growth',
         fontsize=11, color='#888888', fontfamily=body_font, va='top', style='italic')

growth_langs = []
for lang in langs:
    v16 = lang[str(2016)]
    v24 = lang[str(2024)]
    if v16 > 100000:
        growth = (v24 - v16) / v16 * 100
        growth_langs.append((lang, growth))
growth_langs.sort(key=lambda x: x[1], reverse=True)
top_growers = growth_langs[:12]

labels_p5 = []
for i, (lang, growth) in enumerate(top_growers):
    views = [lang[str(y)] for y in years]
    name = get_name(lang['lang'])
    ax.plot(years, views, color=econ_colors[i], linewidth=2, solid_capstyle='round')
    label = f'{name} (+{growth:.0f}%)' if growth > 0 else f'{name} ({growth:.0f}%)'
    labels_p5.append({
        'y': views[-1], 'text': label, 'color': econ_colors[i % len(econ_colors)],
        'fontweight': 'bold'
    })

ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: fmt(v)))
ax.set_xticks(years)
ax.set_xticklabels([str(y) for y in years], fontsize=10)
ax.tick_params(axis='y', labelsize=10, length=0)
ax.tick_params(axis='x', length=0)
ax.grid(axis='y', linewidth=0.5)
ax.set_axisbelow(True)
ax.axhline(y=0, color='#AAAAAA', linewidth=0.6)
ax.set_xlim(2015.3, 2028.5)

# Place de-overlapped labels
place_end_labels(ax, labels_p5, 2025.3, 8, body_font)

fig.text(0.05, 0.02,
         'Source: WikiProject Medicine · mdwiki.toolforge.org/views · *2025 is year-to-date',
         fontsize=9, color='#888888', fontfamily=body_font, va='bottom')

plt.subplots_adjust(top=0.83, bottom=0.07, left=0.07, right=0.82)
plt.savefig('../charts/econ_growth_champions.png', dpi=220, bbox_inches='tight',
            facecolor=ECON_BG, edgecolor='none')
plt.close()
print("✓ Page 5: Growth champions")

print("\n=== ALL ECONOMIST-STYLE CHARTS GENERATED ===")
