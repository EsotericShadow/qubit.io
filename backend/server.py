import os
import shutil
import subprocess
from uuid import uuid4
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USER = os.getenv("GITHUB_USER")
VERCEL_TOKEN = os.getenv("VERCEL_TOKEN")
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "template")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.form.to_dict()
    files = request.files

    project_id = f"neon-cube-{uuid4().hex[:8]}"
    project_dir = f"/tmp/{project_id}"
    os.makedirs(project_dir, exist_ok=True)
    shutil.copytree(TEMPLATE_DIR, project_dir, dirs_exist_ok=True)

    # Save texture
    texture = files["texture"]
    ext = texture.filename.split('.')[-1]
    filename = f"cube_texture.{ext}"
    texture_path = os.path.join(project_dir, filename)
    texture.save(texture_path)

    # Modify HTML
    with open(os.path.join(project_dir, "index.html"), "r") as f:
        html = f.read()
    html = html.replace("{{TITLE}}", data["username"])
    html = html.replace("{{TEXTURE}}", filename)
    for i in range(1, 7):
        html = html.replace(f"{{LINK{i}}}", data[f"face{i}_link"])
        html = html.replace(f"{{TITLE{i}}}", data[f"face{i}_title"])
    with open(os.path.join(project_dir, "index.html"), "w") as f:
        f.write(html)

    # Git operations
    os.chdir(project_dir)
    subprocess.run(["git", "init"])
    subprocess.run(["git", "remote", "add", "origin", f"https://{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{project_id}.git"], check=True)
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)
    subprocess.run(["git", "branch", "-M", "main"], check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], check=True)

    # Vercel deploy
    deploy_cmd = [
        "vercel", "--token", VERCEL_TOKEN,
        "--prod", "--confirm", "--cwd", project_dir,
        "--name", project_id
    ]
    deploy = subprocess.run(deploy_cmd, capture_output=True, text=True)
    url = deploy.stdout.strip().split("\n")[-1]

    return jsonify({"url": url})

if __name__ == "__main__":
    app.run(debug=True)
