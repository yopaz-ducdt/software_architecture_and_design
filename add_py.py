import os

base_dir = r"d:\This Semester\Analysis and Design\assigments\assignment_5"
for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file == "requirements.txt":
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if "pymysql" not in content.lower():
                with open(path, "a", encoding="utf-8") as f:
                    if not content.endswith('\n'):
                        f.write("\n")
                    f.write("pymysql\ncryptography\n")
                    print(f"Added pymysql to {path}")
