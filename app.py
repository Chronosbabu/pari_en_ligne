from flask import Flask, render_template, send_from_directory

app = Flask(__name__)

@app.route("/")
def home():
    apps = [
        {
            "name": "Mon App",
            "apk": "mon_app_v2.apk",
            "icon": "mon_app.png"
        }
    ]
    return render_template("index.html", apps=apps)

@app.route("/download/<apk>")
def download(apk):
    return send_from_directory("static/apks", apk, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
