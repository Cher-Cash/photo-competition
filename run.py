from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="192.168.3.12", port=5000)
