import os
import sys
import subprocess
import argparse
import click
from flask.cli import FlaskGroup
from backend.app import create_app, db
from backend.models.user import User
import logging
import requests
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
import json
from datetime import datetime

logger = logging.getLogger(__name__)
console = Console()

def create_cli_app():
    return create_app()

cli = FlaskGroup(create_app=create_cli_app)

def run_command(command):
    """Run a shell command and return its output"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e.stderr}")
        sys.exit(1)

def setup_dev():
    """Set up the development environment"""
    click.echo('Setting up development environment...')
    
    # Create .env file
    env_content = """FLASK_APP=backend/app.py
FLASK_ENV=development
FLASK_DEBUG=1
DATABASE_URL=sqlite:///dev.db
JWT_SECRET_KEY=dev-secret-key-change-in-production
ELASTICSEARCH_HOST=http://localhost:9200
ELASTICSEARCH_USER=elastic
ELASTICSEARCH_PASSWORD=changeme
ELASTICSEARCH_INDEX=security_events
"""
    with open('.env', 'w') as f:
        f.write(env_content)
    
    # Install dependencies
    run_command("pip install -r requirements.txt")
    
    # Create database tables
    with cli.app.app_context():
        db.create_all()
        
        # Create test user if it doesn't exist
        if not User.query.filter_by(username='test_user').first():
            user = User(
                username='test_user',
                email='test@example.com',
                role='admin'
            )
            user.set_password('test123')
            db.session.add(user)
            db.session.commit()
            click.echo('Created test user')
    
    click.echo('Setup complete')

def run_tests():
    """Run tests"""
    click.echo('Running tests...')
    run_command("pytest backend/tests/ -v")

def run_server():
    """Run the development server"""
    click.echo('Starting development server...')
    os.system('flask run --host=0.0.0.0 --port=5000')

@cli.command()
def setup():
    """Set up the development environment"""
    click.echo('Setting up development environment...')
    
    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write("""FLASK_APP=backend.app
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=dev-secret-key
DATABASE_URL=sqlite:///app.db
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_USER=elastic
ELASTICSEARCH_PASSWORD=changeme
ELASTICSEARCH_INDEX=security_events
""")
        click.echo('Created .env file')
    
    # Create database tables
    from backend.db import db
    from backend.models.user import User
    from backend.models.alert import Alert
    from backend.models.asset import Asset
    from backend.models.event import SecurityEvent
    
    app = create_app()
    with app.app_context():
        db.create_all()
        click.echo('Created database tables')
        
        # Create test user if it doesn't exist
        if not User.query.filter_by(username='testuser').first():
            test_user = User(
                username='testuser',
                email='test@example.com',
                role='admin'
            )
            test_user.set_password('testpass')
            db.session.add(test_user)
            db.session.commit()
            click.echo('Created test user')

@cli.command()
def test():
    """Run tests"""
    click.echo('Running tests...')
    run_tests()

@cli.command()
def run():
    """Run the development server"""
    run_server()

@cli.command()
def all():
    """Run setup, tests, and start server"""
    setup()
    test()
    run()

def show_help():
    """Show help message"""
    print("""
Cybersecurity Project Management Script

Usage:
    python manage.py [command]

Commands:
    setup     - Set up the development environment
    test      - Run all tests
    run       - Start the development server
    all       - Set up, test, and run the server
    help      - Show this help message

Examples:
    python manage.py setup    # Set up the environment
    python manage.py test     # Run tests
    python manage.py run      # Start server
    python manage.py all      # Do everything
    """)

def main():
    parser = argparse.ArgumentParser(description='Manage the cybersecurity project')
    parser.add_argument('command', choices=['setup', 'test', 'run', 'all', 'help'],
                      help='Command to run')
    
    args = parser.parse_args()
    
    if args.command == 'setup':
        setup()
    elif args.command == 'test':
        test()
    elif args.command == 'run':
        run()
    elif args.command == 'all':
        all()
    elif args.command == 'help':
        show_help()
    else:
        print(f"Unknown command: {args.command}")
        show_help()
        sys.exit(1)

class APIClient:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.token = None
        self.console = Console()

    def print_response(self, response, title):
        self.console.print(f"\n[bold blue]=== {title} ===[/bold blue]")
        self.console.print(f"Status Code: {response.status_code}")
        try:
            data = response.json()
            self.console.print(json.dumps(data, indent=2))
        except:
            self.console.print(response.text)

    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def register(self):
        username = Prompt.ask("Enter username")
        email = Prompt.ask("Enter email")
        password = Prompt.ask("Enter password", password=True)
        role = Prompt.ask("Enter role", default="user")

        response = requests.post(
            f"{self.base_url}/api/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password,
                "role": role
            }
        )
        self.print_response(response, "Registration Response")

    def login(self):
        username = Prompt.ask("Enter username")
        password = Prompt.ask("Enter password", password=True)

        response = requests.post(
            f"{self.base_url}/api/auth/login",
            json={"username": username, "password": password}
        )
        if response.status_code == 200:
            self.token = response.json()['access_token']
            self.console.print("[green]Login successful![/green]")
        else:
            self.console.print("[red]Login failed![/red]")
        self.print_response(response, "Login Response")

    def get_user_profile(self):
        response = requests.get(
            f"{self.base_url}/api/auth/me",
            headers=self.get_headers()
        )
        self.print_response(response, "User Profile")

    def get_assets(self):
        response = requests.get(
            f"{self.base_url}/api/assets",
            headers=self.get_headers()
        )
        self.print_response(response, "Assets List")

    def get_events(self):
        response = requests.get(
            f"{self.base_url}/api/events",
            headers=self.get_headers()
        )
        self.print_response(response, "Security Events")

    def get_alerts(self):
        response = requests.get(
            f"{self.base_url}/api/alerts",
            headers=self.get_headers()
        )
        self.print_response(response, "Alerts List")

    def add_event(self):
        event_type = Prompt.ask("Enter event type")
        severity = Prompt.ask("Enter severity (low/medium/high)")
        source_ip = Prompt.ask("Enter source IP")
        details = Prompt.ask("Enter event details (JSON)")

        try:
            details_json = json.loads(details)
        except:
            details_json = {"message": details}

        response = requests.post(
            f"{self.base_url}/api/events",
            headers=self.get_headers(),
            json={
                "event_type": event_type,
                "severity": severity,
                "source_ip": source_ip,
                "details": details_json
            }
        )
        self.print_response(response, "Add Event Response")

    def add_alert(self):
        alert_type = Prompt.ask("Enter alert type")
        severity = Prompt.ask("Enter severity (low/medium/high)")
        source = Prompt.ask("Enter source")
        details = Prompt.ask("Enter alert details (JSON)")

        try:
            details_json = json.loads(details)
        except:
            details_json = {"message": details}

        response = requests.post(
            f"{self.base_url}/api/alerts",
            headers=self.get_headers(),
            json={
                "alert_type": alert_type,
                "severity": severity,
                "source": source,
                "details": details_json
            }
        )
        self.print_response(response, "Add Alert Response")

    def display_risk_analysis(self):
        response = requests.get(
            f"{self.base_url}/api/risk/scores",
            headers=self.get_headers()
        )
        if response.status_code == 200:
            data = response.json()
            table = Table(title="Risk Analysis")
            table.add_column("Asset ID")
            table.add_column("Risk Score")
            table.add_column("Vulnerability Score")
            table.add_column("Threat Score")
            
            for score in data.get('risk_scores', []):
                table.add_row(
                    str(score['asset_id']),
                    f"{score['score']:.2f}",
                    f"{score['factors']['vulnerability_score']:.2f}",
                    f"{score['factors']['threat_score']:.2f}"
                )
            self.console.print(table)

def show_menu():
    console.print(Panel.fit(
        "[bold blue]Cybersecurity API Testing Tool[/bold blue]\n"
        "An interactive tool for testing the Cybersecurity API endpoints",
        title="Welcome"
    ))

    api_client = APIClient()

    while True:
        console.print("\n[bold]Available Operations:[/bold]")
        console.print("1. Register new user")
        console.print("2. Login")
        console.print("3. View user profile")
        console.print("4. View assets")
        console.print("5. View security events")
        console.print("6. Add security event")
        console.print("7. View alerts")
        console.print("8. Add alert")
        console.print("9. View risk analysis")
        console.print("0. Exit")

        choice = Prompt.ask("\nSelect an operation", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"])

        if choice == "0":
            break
        elif choice == "1":
            api_client.register()
        elif choice == "2":
            api_client.login()
        elif choice == "3":
            api_client.get_user_profile()
        elif choice == "4":
            api_client.get_assets()
        elif choice == "5":
            api_client.get_events()
        elif choice == "6":
            api_client.add_event()
        elif choice == "7":
            api_client.get_alerts()
        elif choice == "8":
            api_client.add_alert()
        elif choice == "9":
            api_client.display_risk_analysis()

@cli.command()
def interactive():
    """Start interactive API testing tool"""
    show_menu()

if __name__ == '__main__':
    cli() 