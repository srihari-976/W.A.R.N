from flask import Blueprint, jsonify
import subprocess

isolation_bp = Blueprint('isolation', __name__)

BROWSERS = ['brave.exe', 'chrome.exe', 'firefox.exe', 'msedge.exe']

@isolation_bp.route('/isolate', methods=['POST'])
def isolate_system():
    killed = []
    for browser in BROWSERS:
        try:
            subprocess.run(['taskkill', '/IM', browser, '/F'], check=True)
            killed.append(browser)
        except Exception:
            pass
    if killed:
        return jsonify({'success': True, 'message': f'Killed: {", ".join(killed)}'}), 200
    else:
        return jsonify({'success': False, 'message': 'No browsers killed.'}), 500 