"""納付税額確認書（納付税額一覧表）PDF生成。

使い方: python make_nozei_kakuninsho.py input.json output.pdf
入力JSONの形は example_input.json を参照。申告書から拾うのは「年間税額」と「中間納付額」だけ。
申告納付額・計・翌期予定納付額・納期限はここで計算する（計算ルールは README.md）。
"""
import json, sys, datetime
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

pdfmetrics.registerFont(TTFont('M', 'C:/Windows/Fonts/msmincho.ttc', subfontIndex=0))
fl100 = lambda v: v // 100 * 100
half = lambda v: fl100(v // 2)                 # 翌期予定: 年間税額の1/2を100円未満切捨て
n = lambda v: '' if v is None else f"{v:,}"
WD = "月火水木金土日"


def reiwa(d):
    return f"令和 {d.year - 2018}年{d.month:>2}月{d.day:>2}日"


def next_due_dates(period_start):
    """消費税の翌期3回の納期限。翌期開始から3か月ごとの期間末の2か月後の月末。土日は翌月曜に繰り延べ。"""
    out = []
    y, m = period_start.year + 1, period_start.month   # 翌期の開始年月
    for k in range(3):
        em0 = m + 3 * (k + 1) - 1 + 2                   # 期間末月 + 2か月（連続月番号）
        ey = y + (em0 - 1) // 12
        em = (em0 - 1) % 12 + 1
        nxt = datetime.date(ey + (em == 12), em % 12 + 1, 1)
        last = nxt - datetime.timedelta(days=1)
        d, note = last, ""
        while d.weekday() >= 5:
            d += datetime.timedelta(days=1)
        if d != last:
            note = f"（ {last.month}月{last.day}日が{WD[last.weekday()]}曜日のため）"
        out.append((d, note))
    return out


def build_rows(cfg):
    """(label, kind, [年間,中間,申告,見込,差引,相殺後,翌期]) を返す。"""
    def item(a, i):
        return [a, i, a - i, None, a - i, a - i, half(a)]

    def add(*rs):
        return [None if all(r[k] is None for r in rs) else sum(r[k] or 0 for r in rs) for k in range(7)]

    kz, p, s = cfg["kokuzei"], cfg["pref"], cfg["shohizei"]
    hojin = item(kz["houjin"]["annual"], kz["houjin"]["interim"])
    chiho = item(kz["chiho_houjin"]["annual"], kz["chiho_houjin"]["interim"])
    kokuzei = add(hojin, chiho)
    wari = item(p["houjinzei_wari"]["annual"], p["houjinzei_wari"]["interim"])
    kinto = item(p["kintowari"]["annual"], p["kintowari"]["interim"])
    minzei = add(wari, kinto)
    shotoku = item(p["jigyozei_shotoku"]["annual"], p["jigyozei_shotoku"]["interim"])
    shunyu = item(p["jigyozei_shunyu"]["annual"], p["jigyozei_shunyu"]["interim"])
    jigyo = add(shotoku, shunyu)
    toku = item(p["tokubetsu"]["annual"], p["tokubetsu"]["interim"])
    jigyo_toku = add(jigyo, toku)
    pref_total = add(minzei, jigyo_toku)
    sub = add(kokuzei, pref_total)
    # 消費税: 翌期予定は1回分（年額×3/12、地方消費税は国税分×22/78）。年額480万円超で年3回
    sk, sk_i = s["annual"], s["interim"]
    shohi = [sk, sk_i, sk - sk_i, None, sk - sk_i, sk - sk_i, fl100(sk * 3 // 12)]
    ca, ci = s["chiho_annual"], s["chiho_interim"]
    chi = [ca, ci, ca - ci, None, ca - ci, ca - ci, fl100(shohi[6] * 22 // 78)]
    shohi_total = add(shohi, chi)
    grand = add(sub, shohi_total)
    kojo = cfg.get("shotokuzei_kojo")
    rows = [
        ("控除所得税等の額", "sub", [f"控除( {kojo:,})" if kojo else "", f"税額( {kojo:,})" if kojo else "", '/', '/', '/', '/', '/']),
        ("欠損金繰戻し還付", "sub", ['', '', '/', '/', '/', '/', '/']),
        ("法　人　税", "tax", hojin, 2),
        ("外国税額の控除額", "sub", ['控除(      )', '', '/', '/', '/', '/', '/']),
        ("欠損金繰戻し還付", "sub", ['', '', '/', '/', '/', '/', '/']),
        ("地　方　法　人　税", "tax", chiho, 2),
        ("法人税・地方法人税 計", "tax", kokuzei, 2),
        ("法 人 税 割 額", "in", wari[:3] + ['/', '/', '/', wari[6]]),
        ("均 等 割 額", "in", kinto[:3] + ['/', '/', '/', kinto[6]]),
        ("都 道 府 県 民 税", "tax", minzei, 2),
        ("所　得　割", "in", shotoku),
        ("付 加 価 値 割", "in", [None] * 7),
        ("資　本　割", "in", [None] * 7),
        ("収　入　割", "in", shunyu),
        ("事　業　税", "tax", jigyo, 2),
        ("特別法人事業税", "tax", toku),
        ("事業税・特別税 計", "tax", jigyo_toku, 2),
        ("都道府県税額 計", "tax", pref_total, 2),
        ("法 人 税 割 額", "in", [None, None, None, '/', '/', '/', None]),
        ("均 等 割 額", "in", [None, None, None, '/', '/', '/', None]),
        ("市 町 村 民 税", "tax", [None] * 7, 2),
        ("小　　　　　　計", "tot", sub, 2),
        ("消　費　税", "in", shohi),
        ("地 方 消 費 税", "in", chi),
        ("消　費　税　計", "tax", shohi_total[:6] + ["※" + n(shohi_total[6])], 2),
        ("事　業　所　税", "tax", [None, '既納(      )', None, '/', None, None, '/']),
        ("", "tax", [None] * 7),
        ("合　　　　　　計", "tot", grand, 3),
    ]
    pref_rows = [
        ("法人税割額", "in", wari[:3] + ['/', '/', '/', wari[6]]),
        ("均 等 割 額", "in", kinto[:3] + ['/', '/', '/', kinto[6]]),
        ("都道府県民税", "tax", minzei),
        ("所　得　割", "in", shotoku), ("付加価値割", "in", [None] * 7), ("資　本　割", "in", [None] * 7),
        ("収　入　割", "in", shunyu), ("事　業　税", "tax", jigyo), ("特別法人事業税", "in", toku),
        ("事業税・特別税計", "tax", jigyo_toku), ("都道府県税額計", "tax", pref_total),
    ]
    return rows, pref_rows, dict(grand=grand)


HEAD = ["年間税額", "予定・中間納付額", "申告納付額", "見込納付額", "差引納付額", "相殺後納付額", "翌期予定納付額"]
L = 57
LABW = 105
CW = [56, 58, 56, 50, 56, 56, 56]
X = [L, L + LABW]
for w in CW:
    X.append(X[-1] + w)
R = X[-1]
W, H = A4


def render(cfg, out):
    rows, pref_rows, tot = build_rows(cfg)
    c = canvas.Canvas(out, pagesize=A4)
    c.setTitle("納付税額確認書")

    def hline(y, x0=L, x1=R, w=.5):
        c.setLineWidth(w); c.line(x0, y, x1, y)

    def diag(x0, x1, y0, y1):
        c.setLineWidth(.3); c.line(x0, y0, x1, y1)

    def dl(y):
        c.setDash(1, 2); c.setLineWidth(.4); c.line(L, y - 3, R, y - 3); c.setDash()

    def table(top, rows, rh, head_h=26, fs=8):
        y = top
        c.setFont('M', fs + 1); c.drawString(X[0] + 28, y - head_h + 8, "税　　　　目")
        for i, h in enumerate(HEAD):
            c.setFont('M', 6.2 if len(h) > 5 else 8)
            c.drawCentredString((X[i + 1] + X[i + 2]) / 2, y - head_h + 8, h)
        y -= head_h
        hline(y, w=.8)
        for r in rows:
            label, kind, vals = r[0], r[1], r[2]
            h = rh * (r[3] if len(r) > 3 else 1)
            y1 = y - h
            sub = kind == 'sub'
            if kind == 'tot':
                c.setFillGray(.93); c.rect(L, y1, R - L, h, stroke=0, fill=1); c.setFillGray(0)
            c.setFont('M', fs - 1 if sub else fs)
            c.drawString(X[0] + (8 if kind in ('in', 'sub') else 4), y1 + 3, label)
            for i, v in enumerate(vals):
                xa, xb = X[i + 1], X[i + 2]
                if v == '/':
                    diag(xa, xb, y1, y)
                elif v not in (None, ''):
                    c.setFont('M', fs - 1.5 if sub else fs)
                    c.drawRightString(xb - 3, y1 + 3, v if isinstance(v, str) else n(v))
            hline(y1, w=.3 if kind in ('in', 'sub') else .5)
            y = y1
        for i, x in enumerate(X):
            c.setLineWidth(.5 if 0 < i < len(X) - 1 else .8); c.line(x, top - head_h, x, y)
        c.setLineWidth(.8); c.rect(L, y, R - L, top - y, stroke=1, fill=0)
        return y

    ps = datetime.date.fromisoformat(cfg["period_start"])
    pe = datetime.date.fromisoformat(cfg["period_end"])
    span = (f"(自) 令和 {ps.year-2018} 年 {ps.month} 月 {ps.day} 日  (至) 令和 {pe.year-2018} 年 {pe.month} 月 {pe.day} 日"
            f"   〔   {cfg.get('shinkoku', '確定申告')}   〕")
    # --- 1ページ目 ---
    c.setFont('M', 17); c.drawCentredString(W / 2, H - 62, "納 付 税 額 確 認 書")
    c.setLineWidth(.6); c.line(W / 2 - 78, H - 66, W / 2 + 78, H - 66)
    c.setFont('M', 10.5); c.drawString(L, H - 92, f"{cfg['company']}　御中")
    c.setFont('M', 9.5); c.drawString(L + 3, H - 122, span)
    for i, (a, b) in enumerate((("資本金額：", cfg["capital"]), ("当期利益：", cfg["profit"]), ("課税所得：", cfg["taxable_income"]))):
        c.drawString(R - 150, H - 84 - i * 13, a); c.drawRightString(R, H - 84 - i * 13, n(b) + "円")
    c.drawRightString(R, H - 136, "単位：円")
    bot = table(H - 140, rows, 11.6)
    y = bot - 34
    c.setFont('M', 9.5); c.drawString(L + 2, y, "上記のとおりご査収ください。"); dl(y)
    for k in range(3):
        dl(y - 14 * (k + 1))
    y2 = y - 14 * 5 - 16
    for i, (d, note) in enumerate(next_due_dates(ps)):
        head = "消費税の翌期の納期限　" if i == 0 else "　　　　　　　　　　　"
        c.drawString(L + 2, y2 - i * 12, f"{head}{i+1}回目　{reiwa(d)}{'　' + note if note else ''}"); dl(y2 - i * 12)
    c.setFont('M', 8.5)
    c.drawString(L + 2, y2 - 36, "※ 消費税の予定納付は年 3回あり、上記の金額は1回当たりの支払額を表示しています。"); dl(y2 - 36)
    c.showPage()
    # --- 2ページ目 ---
    c.setFont('M', 15); c.drawCentredString(W / 2, H - 52, "地方税納付税額明細書（都道府県）")
    c.setLineWidth(.6); c.line(W / 2 - 100, H - 56, W / 2 + 100, H - 56)
    c.setFont('M', 10); c.drawString(L, H - 80, cfg["company"])
    c.setFont('M', 9); c.drawString(L + 3, H - 100, span); c.drawRightString(R, H - 100, "単位：円")
    top = H - 112
    rh = 12
    c.setFont('M', 9); c.drawString(X[0] + 28, top - 18, "税　　　目")
    for i, h in enumerate(HEAD):
        c.setFont('M', 6.2 if len(h) > 5 else 8)
        c.drawCentredString((X[i + 1] + X[i + 2]) / 2, top - 18, h)
    y = top - 26
    hline(y, w=.8)
    blank = [(a, b, [v if v == '/' else None for v in d]) for a, b, d in pref_rows]

    def block(y, title, data):
        c.setFillGray(.93); c.rect(L, y - rh, R - L, rh, stroke=0, fill=1); c.setFillGray(0)
        c.setFont('M', 8.5); c.drawString(L + 4, y - rh + 3, title)
        y -= rh
        hline(y)
        for lab, kind, vals in data:
            h = rh * (1.5 if kind == 'tax' else 1)
            y1 = y - h
            c.setFont('M', 7.8); c.drawString(L + (6 if kind == 'in' else 3), y1 + 3, lab)
            for i, v in enumerate(vals):
                xa, xb = X[i + 1], X[i + 2]
                if v == '/':
                    diag(xa, xb, y1, y)
                elif v is not None:
                    c.setFont('M', 8); c.drawRightString(xb - 3, y1 + 3, n(v))
            hline(y1, w=.3)
            y = y1
        return y

    y = block(y, f"{cfg['pref']['code']} {cfg['pref']['name']}", pref_rows)
    y = block(y, "　　合　　計", pref_rows)
    y = block(y, "", blank)
    y = block(y, "", blank)
    for i, x in enumerate(X):
        c.setLineWidth(.5 if 0 < i < len(X) - 1 else .8); c.line(x, top - 26, x, y)
    c.setLineWidth(.8); c.rect(L, y, R - L, top - y, stroke=1, fill=0)
    c.setFont('M', 8); c.drawCentredString(W / 2, y - 18, "1")
    c.save()
    return tot


if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1], encoding='utf-8'))
    t = render(cfg, sys.argv[2])
    print("申告納付額 合計:", n(t['grand'][2]), "／ 翌期予定 合計:", n(t['grand'][6]))
