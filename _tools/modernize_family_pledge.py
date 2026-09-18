import re
import os

FILE_PATH = r"c:\Users\dream\OneDrive\デスクトップ\Meiryu\mimune-no-uraniwa\family_pledge.html"

MODERN_STYLE = """    <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;500;700;900&family=Crimson+Pro:wght@400;600;700&display=swap" rel="stylesheet" />
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Noto Serif JP', 'Crimson Pro', serif;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            min-height: 100vh;
            color: #e0e0e0;
            padding: 3rem 1rem;
            line-height: 1.8;
        }
        body::before {
            content: '';
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.15) 0%, transparent 50%),
                        radial-gradient(circle at 80% 80%, rgba(255, 107, 107, 0.1) 0%, transparent 50%);
            pointer-events: none;
            z-index: 0;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(25px);
            padding: 4rem;
            border-radius: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 25px 60px rgba(0, 0, 0, 0.5);
        }
        h1 {
            font-size: clamp(2.5rem, 6vw, 4rem);
            font-weight: 900;
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 4rem;
            letter-spacing: 0.1em;
            text-shadow: 0 0 30px rgba(102, 126, 234, 0.2);
        }
        h1 a { color: inherit; text-decoration: none; }
        
        h2 {
            font-size: 1.8rem;
            font-weight: 700;
            color: #fff;
            margin-bottom: 1.5rem;
            border-left: 5px solid #667eea;
            padding-left: 1rem;
            display: flex;
            align-items: center;
        }

        .section {
            padding: 2.5rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        .section:last-of-type { border-bottom: none; }

        p.line {
            margin: 0.8rem 0;
            font-size: 1.5rem;
            color: #e0e0e0;
        }

        ruby rt {
            font-size: 0.6em;
            color: #a5b4fc;
            font-weight: normal;
        }

        .jpblock {
            background: rgba(255, 255, 255, 0.03);
            padding: 3rem;
            border-radius: 20px;
            margin-top: 5rem;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        .jpblock h2 { border-left-color: #f093fb; margin-top: 0; }
        .jpitem { margin: 1.5rem 0; font-size: 1.3rem; line-height: 2; }
        .jpitem strong { color: #667eea; margin-right: 0.5em; }

        .nav-links {
            margin-top: 5rem;
            text-align: center;
            border-top: 1px solid rgba(255,255,255,0.1);
            padding-top: 3rem;
        }
        .nav-links a {
            color: #fff;
            text-decoration: none;
            padding: 1rem 3rem;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 50px;
            transition: all 0.3s;
            border: 1px solid rgba(255, 255, 255, 0.2);
            font-weight: 700;
        }
        .nav-links a:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        }

        @media (max-width: 768px) {
            .container { padding: 2rem; }
            h1 { font-size: 2rem; }
            p.line { font-size: 1.2rem; }
            .jpblock { padding: 1.5rem; }
            .jpitem { font-size: 1.1rem; }
        }
    </style>
"""

def main():
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        html = f.read()

    # Replace head contents (Google tag and old styles)
    # Preserve Google Tag
    gtag_match = re.search(r'<!-- Google tag.*?/script>', html, re.DOTALL)
    gtag = gtag_match.group(0) if gtag_match else ""

    # Generate new head
    new_head = f"<head>\n{gtag}\n    <meta charset=\"utf-8\"/>\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\"/>\n    <title>家庭盟誓 | み旨の裏庭</title>\n    <link rel=\"icon\" href=\"/mimune-no-uraniwa/favicon.png\" type=\"image/png\"/>\n    <meta property=\"og:image\" content=\"https://maydra.github.io/mimune-no-uraniwa/og-image.png\"/>\n{MODERN_STYLE}</head>"

    html = re.sub(r'<head>.*?</head>', new_head, html, flags=re.DOTALL | re.IGNORECASE)

    # Wrap body content in a clean container if not already
    # (Actually we want to clean up the existing body and redo the structure slightly)
    
    # Extract the main content (inside div.container)
    content_match = re.search(r'<div class="container">(.*?)</div>', html, re.DOTALL)
    if content_match:
        inner_content = content_match.group(1)
        # Add nav links back to top
        inner_content += '<div class="nav-links"><a href="index.html">トップページへ戻る</a></div>'
        
        # Reconstruct body
        new_body = f"<body>\n<div class=\"container\">\n{inner_content}\n</div>\n"
        
        # Add typo report if it exists
        typo_match = re.search(r'<section id="typo-report".*?</script>', html, re.DOTALL)
        if typo_match:
            new_body += typo_match.group(0)
            
        new_body += "\n</body>"
        
        html = re.sub(r'<body>.*?</body>', new_body, html, flags=re.DOTALL | re.IGNORECASE)

    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    print("family_pledge.html modernized.")

if __name__ == "__main__":
    main()
