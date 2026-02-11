import json
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
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
    'eu': 'Basque', 'gl': 'Galician', 'be': 'Belarusian', 'la': 'Latin',
    'eo': 'Esperanto', 'war': 'Waray', 'ceb': 'Cebuano', 'sh': 'Serbo-Croatian',
    'nn': 'Nynorsk', 'ga': 'Irish', 'cy': 'Welsh', 'ku': 'Kurdish',
    'ast': 'Asturian', 'oc': 'Occitan', 'an': 'Aragonese', 'br': 'Breton',
    'nds': 'Low German', 'scn': 'Sicilian', 'pms': 'Piedmontese',
    'lb': 'Luxembourgish', 'jv': 'Javanese', 'su': 'Sundanese',
    'min': 'Minangkabau', 'sco': 'Scots', 'io': 'Ido', 'nap': 'Neapolitan',
    'lmo': 'Lombard', 'bar': 'Bavarian', 'als': 'Alemannic', 'fo': 'Faroese',
    'is': 'Icelandic', 'mt': 'Maltese', 'pa': 'Punjabi', 'or': 'Odia',
    'sa': 'Sanskrit', 'ps': 'Pashto', 'sd': 'Sindhi', 'ckb': 'Sorani Kurdish',
    'yi': 'Yiddish', 'vec': 'Venetian', 'ba': 'Bashkir', 'tt': 'Tatar',
    'cv': 'Chuvash', 'ce': 'Chechen', 'os': 'Ossetian', 'mhr': 'Meadow Mari',
    'myv': 'Erzya', 'udm': 'Udmurt', 'sah': 'Yakut', 'ab': 'Abkhaz',
    'dv': 'Dhivehi', 'lo': 'Lao', 'bo': 'Tibetan', 'ug': 'Uyghur',
    'zu': 'Zulu', 'xh': 'Xhosa', 'sn': 'Shona', 'yo': 'Yoruba',
    'ig': 'Igbo', 'ha': 'Hausa', 'rw': 'Kinyarwanda', 'so': 'Somali',
    'mg': 'Malagasy', 'ny': 'Chichewa', 'st': 'Sesotho', 'lg': 'Luganda',
    'wo': 'Wolof', 'bm': 'Bambara', 'tn': 'Tswana', 'ti': 'Tigrinya',
    'om': 'Oromo', 'ee': 'Ewe', 'ak': 'Akan', 'tw': 'Twi',
    'fy': 'West Frisian', 'li': 'Limburgish', 'wa': 'Walloon',
    'gd': 'Scottish Gaelic', 'kw': 'Cornish', 'gv': 'Manx',
    'ie': 'Interlingue', 'ia': 'Interlingua', 'vo': 'Volapük',
    'nov': 'Novial', 'qu': 'Quechua', 'ay': 'Aymara', 'gn': 'Guarani',
    'nah': 'Nahuatl', 'ht': 'Haitian Creole', 'pap': 'Papiamento',
    'bcl': 'Central Bikol', 'ilo': 'Ilocano', 'pag': 'Pangasinan',
    'cbk-zam': 'Chavacano', 'hif': 'Fiji Hindi', 'map-bms': 'Banyumasan',
    'ace': 'Acehnese', 'bug': 'Buginese', 'bjn': 'Banjar', 'mai': 'Maithili',
    'bh': 'Bihari', 'new': 'Newari', 'as': 'Assamese', 'lij': 'Ligurian',
    'fur': 'Friulian', 'eml': 'Emilian-Romagnol', 'frr': 'North Frisian',
    'stq': 'Saterland Frisian', 'rm': 'Romansh', 'vls': 'West Flemish',
    'zea': 'Zeelandic', 'pcd': 'Picard', 'nrm': 'Norman', 'frp': 'Arpitan',
    'ext': 'Extremaduran', 'mwl': 'Mirandese', 'roa-tara': 'Tarantino',
    'co': 'Corsican', 'lad': 'Ladino', 'rue': 'Rusyn', 'szl': 'Silesian',
    'csb': 'Kashubian', 'dsb': 'Lower Sorbian', 'hsb': 'Upper Sorbian',
    'crh': 'Crimean Tatar', 'krc': 'Karachay-Balkar', 'ltg': 'Latgalian',
    'vep': 'Veps', 'koi': 'Komi-Permyak', 'kv': 'Komi', 'mdf': 'Moksha',
    'mrj': 'Hill Mari', 'xmf': 'Mingrelian', 'lbe': 'Lak', 'lez': 'Lezgian',
    'av': 'Avar', 'inh': 'Ingush', 'kbd': 'Kabardian', 'ady': 'Adyghe',
    'tyv': 'Tuvan', 'bxr': 'Buryat', 'ary': 'Moroccan Arabic',
    'arz': 'Egyptian Arabic', 'azb': 'South Azerbaijani', 'tcy': 'Tulu',
    'diq': 'Zazaki', 'pnb': 'Western Punjabi', 'wuu': 'Wu Chinese',
    'zh-yue': 'Cantonese', 'zh-min-nan': 'Min Nan', 'zh-classical': 'Classical Chinese',
    'hak': 'Hakka', 'gan': 'Gan Chinese', 'cdo': 'Min Dong',
    'tpi': 'Tok Pisin', 'bi': 'Bislama', 'mi': 'Māori', 'sm': 'Samoan',
    'to': 'Tongan', 'fj': 'Fijian', 'haw': 'Hawaiian', 'chr': 'Cherokee',
    'iu': 'Inuktitut', 'cr': 'Cree', 'nv': 'Navajo', 'oj': 'Ojibwe',
    'se': 'Northern Sami', 'mus': 'Muscogee',
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
ECON_BG      = '#F7F5F0'

try:
    import matplotlib.font_manager as fm
    available = set(f.name for f in fm.fontManager.ttflist)
    title_font = 'Georgia' if 'Georgia' in available else 'DejaVu Serif'
    body_font  = 'Franklin Gothic Medium' if 'Franklin Gothic Medium' in available else 'DejaVu Sans'
except:
    title_font = 'DejaVu Serif'
    body_font  = 'DejaVu Sans'

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

# ── Generate pages ─────────────────────────────────────────
per_page = 25
ncols = 5
nrows = 5
total_pages = math.ceil(len(langs) / per_page)

for page in range(total_pages):
    start = page * per_page
    end = min(start + per_page, len(langs))
    page_langs = langs[start:end]
    actual_count = len(page_langs)

    fig = plt.figure(figsize=(22, 30), facecolor=ECON_BG)
    fig.subplots_adjust(left=0.04, right=0.97, top=0.90, bottom=0.04, hspace=0.55, wspace=0.28)

    # ── Header ─────────────────────────────────────────────
    fig.patches.append(plt.Rectangle(
        (0.04, 0.965), 0.93, 0.006,
        transform=fig.transFigure, facecolor=ECON_RED, edgecolor='none', zorder=10
    ))

    fig.text(0.04, 0.955, 'Wikipedia medical articles',
             fontsize=28, fontweight='bold', fontfamily=title_font,
             color=ECON_DARK, va='top')
    fig.text(0.04, 0.935, f'User views by language, 2016–25*   ·   Page {page+1} of {total_pages}',
             fontsize=16, color=ECON_GREY, fontfamily=body_font, va='top')
    rank_range = f'Ranked #{start+1}–{end} by total views'
    fig.text(0.04, 0.920, f'{rank_range}  |  *2025 figure is year-to-date',
             fontsize=11, color='#888888', fontfamily=body_font, va='top', style='italic')

    # ── Grid ───────────────────────────────────────────────
    gs = GridSpec(nrows, ncols, figure=fig,
                 left=0.04, right=0.97, top=0.86, bottom=0.06,
                 hspace=0.85, wspace=0.30)

    for idx in range(actual_count):
        lang = page_langs[idx]
        row = idx // ncols
        col = idx % ncols
        ax = fig.add_subplot(gs[row, col])

        views = [lang[str(y)] for y in years]
        name  = get_name(lang['lang'])
        peak  = max(views)
        peak_yr = years[views.index(peak)]
        rank = start + idx + 1

        # ── Area fill + line ──
        ax.fill_between(years, views, alpha=0.12, color=ECON_RED, linewidth=0)
        ax.plot(years, views, color=ECON_RED, linewidth=1.8, solid_capstyle='round')
        ax.plot(peak_yr, peak, 'o', color=ECON_RED, markersize=4, zorder=5)

        # ── Panel title with rank ──
        ax.set_title(f'#{rank}  {name}', fontsize=10.5, fontweight='bold',
                     fontfamily=title_font, color=ECON_DARK, loc='left', pad=18)

        # ── Red top rule per panel ──
        ax_pos = ax.get_position()
        fig.patches.append(plt.Rectangle(
            (ax_pos.x0, ax_pos.y1 + 0.018), ax_pos.width, 0.0025,
            transform=fig.transFigure, facecolor=ECON_RED, edgecolor='none', zorder=10
        ))

        # ── Total annotation ──
        ax.text(0.98, 0.95, f'{fmt(lang["total"])} total',
                transform=ax.transAxes, fontsize=7.5, color=ECON_GREY,
                ha='right', va='top', fontfamily=body_font)

        # ── Y-axis ──
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: fmt(v)))
        ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=4, integer=False))
        ax.tick_params(axis='y', labelsize=7.5, length=0, pad=2)
        ax.tick_params(axis='x', labelsize=7, length=0, pad=2)

        # ── X-axis ──
        ax.set_xticks([2016, 2020, 2025])
        ax.set_xticklabels(["'16", "'20", "'25"], fontsize=7.5)
        ax.set_xlim(2015.3, 2025.7)

        # ── Grid + baseline ──
        ax.grid(axis='y', linewidth=0.4, color=ECON_LIGHT)
        ax.set_axisbelow(True)
        ax.axhline(y=0, color='#AAAAAA', linewidth=0.6)

    # ── Source ─────────────────────────────────────────────
    fig.text(0.04, 0.018,
             'Source: WikiProject Medicine · mdwiki.toolforge.org/views · Users-agents data',
             fontsize=9, color='#888888', fontfamily=body_font, va='bottom')
    fig.text(0.97, 0.018, f'Page {page+1}/{total_pages}',
             fontsize=9, color='#AAAAAA', fontfamily=body_font, va='bottom',
             ha='right', style='italic')

    outpath = f'../charts/econ_all_langs_page_{page+1:02d}.png'
    plt.savefig(outpath, dpi=200, bbox_inches='tight',
                facecolor=ECON_BG, edgecolor='none')
    plt.close()
    print(f'✓ Page {page+1}/{total_pages}: langs #{start+1}–{end}')

print(f'\n=== ALL {total_pages} PAGES GENERATED ===')
