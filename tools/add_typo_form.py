import os
import re

NEW_FORM_HTML = """
<section id="typo-report" class="typo-box">
  <h3 class="typo-title">誤植・修正提案</h3>
  <p class="typo-desc">コメント感覚で送れます（匿名OK）。ページURLは自動で添付されます。</p>

  <form id="typoForm"
        action="https://script.google.com/macros/s/AKfycbxbuP7GLEAwodsiLog16LZDZA0hnqlK0A21fx8Vq2-n-_gq_5EudLVMJy0yXk1KYO19lA/exec"
        method="POST"
        target="typoSink">

    <label class="typo-label" for="typoText">内容（必須）</label>
    <textarea id="typoText" name="typoText" class="typo-textarea" rows="4" required
      placeholder="例：誤字、脱字、年号違い…"></textarea>

    <label class="typo-label" for="typoQuote">該当箇所（任意）</label>
    <textarea id="typoQuote" name="typoQuote" class="typo-textarea" rows="2"
      placeholder="該当文をコピペ（任意）"></textarea>

    <input type="hidden" id="pageUrl" name="pageUrl">
    <input type="hidden" id="whenIso" name="whenIso">
    <input type="hidden" id="userAgent" name="userAgent">

    <div class="typo-row">
      <button type="submit" id="typoSubmit" class="typo-btn">送信</button>
      <span id="typoStatus" class="typo-status" aria-live="polite"></span>
    </div>
  </form>

  <iframe name="typoSink" id="typoSink" style="display:none;"></iframe>
</section>

<style>
  .typo-box{margin:2.5rem 0;padding:1rem 1.1rem;border:1px solid #ddd;border-radius:14px;background:#fff;}
  .typo-title{margin:0 0 .35rem 0;font-size:1.05rem;}
  .typo-desc{margin:0 0 1rem 0;opacity:.8;}
  .typo-label{display:block;font-weight:600;margin:.7rem 0 .35rem 0;}
  .typo-textarea{width:100%;box-sizing:border-box;padding:.7rem .75rem;border:1px solid #ccc;border-radius:12px;font:inherit;line-height:1.5;resize:vertical;}
  .typo-row{margin-top:.9rem;display:flex;gap:.75rem;align-items:center;}
  .typo-btn{padding:.6rem 1rem;border:0;border-radius:12px;background:#111;color:#fff;cursor:pointer;font:inherit;}
  .typo-btn[disabled]{opacity:.6;cursor:not-allowed;}
  .typo-status{font-size:.95rem;opacity:.9;}
</style>

<script>
(() => {
  const form = document.getElementById("typoForm");
  const sink = document.getElementById("typoSink");
  const statusEl = document.getElementById("typoStatus");
  const btn = document.getElementById("typoSubmit");

  function fillHidden() {
    document.getElementById("pageUrl").value = location.href;
    document.getElementById("whenIso").value = new Date().toISOString();
    document.getElementById("userAgent").value = navigator.userAgent;
  }
  fillHidden();

  form.addEventListener("submit", () => {
    fillHidden();
    btn.disabled = true;
    statusEl.textContent = "送信中…";
  });

  // iframe が読み込まれた = Apps Script が何か返した（成功/失敗のどちらでも）
  sink.addEventListener("load", () => {
    btn.disabled = false;
    statusEl.textContent = "送信しました。ありがとうございます！";
    setTimeout(() => form.reset(), 200);
  });
})();
</script>
"""

DP_DIR = r"c:\Users\dream\OneDrive\デスクトップ\Meiryu\mimune-no-uraniwa\dp"

def apply_to_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'id="typo-report"' in content:
        # Match from the comment start (if exists) or the section tag
        content = re.sub(r'<!-- =========================\n\s+Typo Report Inline Form.*?</script>', '', content, flags=re.DOTALL)
        content = re.sub(r'<section id="typo-report".*?</script>', '', content, flags=re.DOTALL)

    last_body_idx = content.rfind('</body>')
    if last_body_idx == -1:
        print(f"Error: </body> not found in {file_path}")
        return
    
    # Strip trailing whitespace before insert
    prefix = content[:last_body_idx].rstrip()
    new_content = prefix + "\n" + NEW_FORM_HTML + content[last_body_idx:]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Updated {file_path}")

if __name__ == "__main__":
    files = [f for f in os.listdir(DP_DIR) if f.endswith('.html')]
    targets = [f for f in files if (f[0].isdigit() or f == '20sho.html')]
    
    for filename in targets:
        path = os.path.join(DP_DIR, filename)
        apply_to_file(path)
