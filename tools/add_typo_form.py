import os
import sys

FORM_HTML = """
<!-- =========================
  Typo Report Inline Form
  Paste before </body>
========================= -->
<section id="typo-report" class="typo-box" aria-label="誤植報告フォーム">
  <h3 class="typo-title">誤植・修正提案</h3>
  <p class="typo-desc">コメント感覚で送れます（匿名OK）。ページURLは自動で添付されます。</p>

  <form id="typoForm" class="typo-form">
    <label class="typo-label" for="typoText">内容（必須）</label>
    <textarea id="typoText" class="typo-textarea" rows="4" required
      placeholder="例：『復帰』が『腹筋』になっています / 年号が違う、など"></textarea>

    <label class="typo-label" for="typoQuote">該当箇所（任意）</label>
    <textarea id="typoQuote" class="typo-textarea" rows="2"
      placeholder="該当文をコピペ（任意）"></textarea>

    <div class="typo-row">
      <button type="submit" id="typoSubmit" class="typo-btn">送信</button>
      <span id="typoStatus" class="typo-status" role="status" aria-live="polite"></span>
    </div>
  </form>
</section>

<style>
  .typo-box{
    margin: 2.5rem 0;
    padding: 1rem 1.1rem;
    border: 1px solid #ddd;
    border-radius: 14px;
    background: #fff;
  }
  .typo-title{ margin: 0 0 .35rem 0; font-size: 1.05rem; }
  .typo-desc{ margin: 0 0 1rem 0; opacity: .8; }
  .typo-label{ display:block; font-weight:600; margin:.7rem 0 .35rem 0; }
  .typo-textarea{
    width: 100%;
    box-sizing: border-box;
    padding: .7rem .75rem;
    border: 1px solid #ccc;
    border-radius: 12px;
    font: inherit;
    line-height: 1.5;
    resize: vertical;
  }
  .typo-row{
    margin-top: .9rem;
    display:flex;
    gap: .75rem;
    align-items:center;
  }
  .typo-btn{
    padding: .6rem 1rem;
    border: 0;
    border-radius: 12px;
    background: #111;
    color: #fff;
    cursor: pointer;
    font: inherit;
  }
  .typo-btn[disabled]{ opacity:.6; cursor:not-allowed; }
  .typo-status{ font-size: .95rem; opacity:.9; }
</style>

<script>
(() => {
  // ★あなたのWebアプリURL（これでOK）
  const SUBMIT_URL = "https://script.google.com/macros/s/AKfycbytTeBaqjbGvHp1_NLcg_6z6MUxGgEQzBn8Ua-POwEwfMzrdBZwKBFPx5Dmp7LZbrLuKA/exec";

  const form = document.getElementById("typoForm");
  const statusEl = document.getElementById("typoStatus");
  const submitBtn = document.getElementById("typoSubmit");

  const setStatus = (msg) => { statusEl.textContent = msg; };

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const typoText = document.getElementById("typoText").value.trim();
    const typoQuote = document.getElementById("typoQuote").value.trim();

    if (!typoText) {
      setStatus("内容を入力してください。");
      return;
    }

    submitBtn.disabled = true;
    setStatus("送信中…");

    // 送信データ（ページURLなど自動添付）
    const payload = {
      typoText,
      typoQuote,
      pageUrl: location.href,
      whenIso: new Date().toISOString(),
      userAgent: navigator.userAgent
    };

    // x-www-form-urlencoded で送る（CORS preflight回避しやすい）
    const body = new URLSearchParams(payload).toString();

    try {
      // no-cors にすることで、GitHub Pages → Apps Script で詰まりにくくする
      await fetch(SUBMIT_URL, {
        method: "POST",
        mode: "no-cors",
        headers: { "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8" },
        body
      });

      // no-cors は成功/失敗を厳密に読めないので「投函箱」方式で運用（実用上これでOK）
      form.reset();
      setStatus("送信しました。ありがとうございます！");
    } catch (err) {
      console.error(err);
      setStatus("送信に失敗しました（通信エラー）。");
    } finally {
      submitBtn.disabled = false;
    }
  });
})();
</script>
"""

DP_DIR = r"c:\Users\dream\OneDrive\デスクトップ\Meiryu\mimune-no-uraniwa\dp"

def apply_to_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'id="typo-report"' in content:
        print(f"Skipping {file_path} (already has form)")
        return

    # Find the last </body>
    last_body_idx = content.rfind('</body>')
    if last_body_idx == -1:
        print(f"Error: </body> not found in {file_path}")
        return
    
    new_content = content[:last_body_idx] + FORM_HTML + content[last_body_idx:]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Updated {file_path}")

if __name__ == "__main__":
    files = [f for f in os.listdir(DP_DIR) if f.endswith('.html')]
    # Target body pages: starts with digit or 20sho.html
    targets = [f for f in files if (f[0].isdigit() or f == '20sho.html')]
    # Exclude non-body if any (though digits usually mean chapters here)
    
    for filename in targets:
        path = os.path.join(DP_DIR, filename)
        apply_to_file(path)
