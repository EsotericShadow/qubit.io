# cube-generator/backend/server.py

import os
import shutil
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from uuid import uuid4

load_dotenv()

app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
VERCEL_TOKEN = os.getenv("VERCEL_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
TEMPLATE_PATH = os.path.join(os.getcwd(), "backend", "template")
TEMP_DIR = "/tmp"

@app.route("/generate", methods=["POST"])
def generate():
    data = request.form.to_dict()
    texture = request.files["texture"]
    project_id = str(uuid4())[:8]
    repo_name = f"neon-cube-{project_id}"
    project_path = os.path.join(TEMP_DIR, repo_name)

    shutil.copytree(TEMPLATE_PATH, project_path)
    customize_template(project_path, data)
    texture_path = os.path.join(project_path, "cube_texture.mp4")
    texture.save(texture_path)

    create_github_repo(repo_name)
    push_to_github(project_path, repo_name)
    live_url = deploy_to_vercel(repo_name)

    return jsonify({"url": live_url})

def customize_template(path, data):
    html_path = os.path.join(path, "index.html")
    with open(html_path, "r") as file:
        html = file.read()

    html = html.replace("{{TITLE}}", data.get("username", "Cube Site"))
    for i in range(1, 7):
        html = html.replace(f"{{LINK{i}}}", data.get(f"face{i}_link", "#"))
        html = html.replace(f"{{TITLE{i}}}", data.get(f"face{i}_title", f"Face {i}"))

    with open(html_path, "w") as file:
        file.write(html)

def create_github_repo(repo_name):
    res = requests.post(
        "https://api.github.com/user/repos",
        headers={"Authorization": f"token {GITHUB_TOKEN}"},
        json={"name": repo_name, "auto_init": True, "private": False}
    )
    res.raise_for_status()

def push_to_github(path, repo_name):
    os.system(f"cd {path} && git init")
    os.system(f"cd {path} && git remote add origin https://{GITHUB_TOKEN}@github.com/{GITHUB_USERNAME}/{repo_name}.git")
    os.system(f"cd {path} && git add .")
    os.system(f"cd {path} && git commit -m 'initial commit'")
    os.system(f"cd {path} && git push -u origin master")

def deploy_to_vercel(repo_name):
    res = requests.post(
        "https://api.vercel.com/v13/deployments",
        headers={"Authorization": f"Bearer {VERCEL_TOKEN}"},
        json={"name": repo_name, "gitSource": {"type": "github", "repoId": f"{GITHUB_USERNAME}/{repo_name}"}}
    )
    res.raise_for_status()
    return res.json().get("url")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
