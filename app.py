from helpers.create_app import (
    create_app,
)
import config

app = create_app()

if __name__ == '__main__':  # pragma: no cover
    app.run(debug=config.DEBUG, host=config.HOST, port=config.PORT)
