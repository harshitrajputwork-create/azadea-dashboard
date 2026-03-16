import os

def build_stlite_html():
    files_to_bundle = [
        "app.py",
        "data_loader.py",
        "dashboards/chiller_freezer.py",
        "dashboards/hygiene_receiving.py",
        "dashboards/manager_checklists.py"
    ]
    
    files_js = ""
    for file_path in files_to_bundle:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Escape backticks and backslashes for JS template literal
            content_escaped = content.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
            if file_path == "app.py":
                content_escaped = content_escaped.replace(
                    """chiller_path   = up_chiller if up_chiller else """,
                    """import os\n    chiller_path   = up_chiller if up_chiller else """
                )
                
            files_js += f'\n                    "{file_path}": `{content_escaped}`,'
            
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Azadea Analytics</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@stlite/mountable@0.63.1/build/stlite.css" />
</head>
<body>
    <div id="root"></div>
    <script src="https://cdn.jsdelivr.net/npm/@stlite/mountable@0.63.1/build/stlite.js"></script>
    <script>
        stlite.mount(
            {{
                requirements: ["pandas", "plotly"],
                entrypoint: "app.py",
                files: {{{files_js}
                }}
            }},
            document.getElementById("root")
        );
    </script>
</body>
</html>"""

    with open("offline_dashboard.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("Generated offline_dashboard.html")

if __name__ == "__main__":
    build_stlite_html()
