import os

base_dir = r"d:\This Semester\Analysis and Design\assigments\assignment_5"
for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file in ("main.py", "database.py"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if 'host="localhost"' in content:
                content = content.replace('host="localhost"', 'host="host.docker.internal"')
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Fixed {path}")
