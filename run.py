from app import create_app

app = create_app()

if __name__ == '__main__':
    # TODO: turn this into False when deploying to production
    app.run(debug=True)