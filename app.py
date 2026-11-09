import os

from app import create_app

app = create_app()

if __name__ == '__main__':
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', '5000'))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'

    if debug:
        app.run(host=host, port=port, debug=True)
    else:
        try:
            from waitress import serve
        except ImportError:
            # fallback, если waitress не установлен
            app.run(host=host, port=port, debug=False)
        else:
            print(f'Music Assistant запущен: http://{host}:{port}')
            serve(app, host=host, port=port)
