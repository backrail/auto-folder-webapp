from flask import Flask, render_template, request, send_file
import io, zipfile
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # セキュリティのために、ランダムな文字列に置き換えてください

IROHA = ["イ","ロ","ハ","ニ","ホ","ヘ","ト","チ","リ","ヌ","ル","ヲ","ワ","カ","ヨ","タ","レ","ソ","ツ","ネ","ナ","ラ","ム","ウ","ヰ","ノ","オ","ク","ヤ","マ","ケ","フ","コ","エ","テ","ア","サ","キ","ユ","メ","ミ","シ","ヱ","ヒ","モ","セ","ス"]

def parse_lines(s):
    if not s:
        return []
    parts = []
    for line in s.replace(",", "\n").splitlines():
        val = line.strip()
        if val:
            parts.append(val)
    return parts

def alpha_col(n, upper=True):
    n0 = max(1, n)
    s = ""
    while n0 > 0:
        n0, rem = divmod(n0 - 1, 26)
        s = chr((65 if upper else 97) + rem) + s
    return s

def iroha_n(n):
    idx = (n - 1) % len(IROHA)
    return IROHA[idx]

def format_token(n_raw, style, digits, use_paren):
    if style == "num":
        token = str(n_raw).zfill(digits)
    elif style == "alpha":
        token = alpha_col(n_raw, upper=True)
    elif style == "iroha":
        token = iroha_n(n_raw)
    else:
        token = str(n_raw)
    if use_paren:
        token = f"({token})"
    return token

def assemble_name(order, textA, textB, token):
    segs = []
    for t in order:
        if t == "A":
            if textA: segs.append(textA)
        elif t == "N":
            segs.append(token)
        elif t == "B":
            if textB: segs.append(textB)
    return "".join(segs)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        child_enabled = request.form.get("child_enabled") == "on"
        grand_enabled = request.form.get("grand_enabled") == "on"
        child_names = parse_lines(request.form.get("child_names", "") if child_enabled else "")
        grand_names = parse_lines(request.form.get("grand_names", "") if grand_enabled else "")

        mode = request.form.get("mode", "auto")
        folder_names = []

        if mode == "custom":
            custom_names = parse_lines(request.form.get("custom_names", ""))
            if not custom_names:
                # エラーメッセージを返すためのロジックをここに記述
                return "カスタム名が空です。1行＝1フォルダ名で入力してください。", 400
            folder_names = custom_names
        else:
            order_str = (request.form.get("order") or "A,N,B").strip()
            order = [x.strip() for x in order_str.split(",") if x.strip() in ("A","N","B")]
            if "N" not in order:
                # エラーメッセージを返すためのロジックをここに記述
                return "番号ブロック（N）が順序に含まれていません。", 400

            textA = (request.form.get("textA") or "").strip()
            textB = (request.form.get("textB") or "").strip()

            start = int(request.form.get("start", "1") or 1)
            digits = int(request.form.get("digits", "4") or 4)
            count = int(request.form.get("count", "1") or 1)
            num_style = request.form.get("num_style", "num")
            use_paren = request.form.get("use_paren") == "on"

            if count < 1:
                # エラーメッセージを返すためのロジックをここに記述
                return "作成数は1以上にしてください。", 400

            if num_style == "num":
                digits = max(digits, len(str(start)))

            for i in range(start, start + count):
                token = format_token(i, num_style, digits, use_paren)
                folder_names.append(assemble_name(order, textA, textB, token))

        mem = io.BytesIO()
        with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as zf:
            for top in folder_names:
                zf.writestr(f"{top}/", "")
                if child_names:
                    for c in child_names:
                        zf.writestr(f"{top}/{c}/", "")
                        if grand_names:
                            for g in grand_names:
                                zf.writestr(f"{top}/{c}/{g}/", "")
                elif grand_names:
                    for g in grand_names:
                        zf.writestr(f"{top}/{g}/", "")

        mem.seek(0)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"folders_{ts}.zip"
        return send_file(mem, as_attachment=True, download_name=filename, mimetype="application/zip")
    else:
        return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)