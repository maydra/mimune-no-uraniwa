import subprocess

with open("changed_files.txt", "r", encoding="utf-8") as f:
    files = [
        line.strip()[3:]
        for line in f
        if line.strip().endswith(".html") and line.startswith(" M ")
    ]

batch_size = 210
batches = [files[i:i+batch_size] for i in range(0, len(files), batch_size)]

for i, batch in enumerate(batches, start=1):
    print(f"🔧 第{i}バッチ ({len(batch)}件) をコミット中...")

    try:
        subprocess.run(["git", "add"] + batch, check=True)
        subprocess.run(["git", "commit", "-m", f"part {i}: commit {len(batch)} files"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"⚠️ コミット失敗: {e}")
        break

print("\n✅ すべてのバッチをコミットしました！（途中中断がなければ）")
print("🚀 最後に git push を実行してください。")
