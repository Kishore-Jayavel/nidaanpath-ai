"""
NidaanPath AI — run.py
Entry point for the application.
"""
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # use_debugger=False prevents Werkzeug from importing the removed
    # flask.debughelpers module (dropped in Flask 3.x) on form POST requests.
    # Auto-reload stays active via use_reloader=True.
    app.run(host='0.0.0.0', port=port, debug=True,
            use_debugger=False, use_reloader=True)
