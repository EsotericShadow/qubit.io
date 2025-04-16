import os, shutil, zipfile, requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from uuid import uuid4

load_dotenv()
app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
VERCEL_TOKEN = os.getenv("VERCEL_TOKEN")
TEMPLATE_PATH = "backend/template"

def generate_repo(user_data, texture_path):
    project_id = str(uuid4())[:8]
    repo_name = f"neon-cube-{project_id}"

    # Clone template and fill with data
    project_path = f"/tmp/{repo_name}"
    shutil.copytree(TEMPLATE_PATH, project_path)

    # Replace placeholders in template files
    with open(f"{project_path}/index.html", "r") as f:
        html = f.read()
    html = html.replace("{{TITLE}}", user_data["username"])
    for i in range(1, 7):
        html = html.replace(f"{{LINK{i}}}", user_data[f"face{i}_link"])
        html = html.replace(f"{{TITLE{i}}}", user_data[f"face{i}_title"])
    with open(f"{project_path}/index.html", "w") as f:
        f.write(html)

    # Save uploaded texture
    texture_target = os.path.join(project_path, "cube_texture.mp4")
    shutil.copyfile(texture_path, texture_target)

    # Push to GitHub
    create_repo_on_github(repo_name)
    push_to_github(project_path, repo_name)

    # Deploy to Vercel
    url = deploy_to_vercel(repo_name)
    return url

def create_repo_on_github(name):
    res = requests.post(
        "https://api.github.com/user/repos",
        headers={"Authorization": f"token {GITHUB_TOKEN}"},
        json={"name": name, "auto_init": True}
    )
    return res.json()

def push_to_github(path, repo_name):
    os.system(f"cd {path} && git init")
    os.system(f"cd {path} && git remote add origin https://{GITHUB_TOKEN}@github.com/YOUR_USERNAME/{repo_name}.git")
    os.system(f"cd {path} && git add . && git commit -m 'init cube' && git push origin master")

def deploy_to_vercel(repo_name):
    res = requests.post(
        "https://api.vercel.com/v12/deployments",
        headers={"Authorization": f"Bearer {VERCEL_TOKEN}"},
        json={
            "name": repo_name,
            "gitSource": {
                "type": "github",
                "repoId": f"YOUR_USERNAME/{repo_name}"
            }
        }
    )
    return res.json()["url"]

@app.route("/generate", methods=["POST"])
def generate():
    data = request.form.to_dict()
    texture = request.files["texture"]
    texture_path = f"/tmp/{texture.filename}"
    texture.save(texture_path)
    url = generate_repo(data, texture_path)
    return jsonify({"url": url})

if __name__ == "__main__":
    app.run(debug=True)
