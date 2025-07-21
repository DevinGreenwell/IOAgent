#!/usr/bin/env python
"""Management CLI for IOAgent application."""

import os
import sys
import click
from flask.cli import FlaskGroup
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app_factory import create_app
from src.models.user import db, User
from src.config.settings import EnvironmentManager, settings


def create_app_cli():
    """Create app for CLI."""
    return create_app()


cli = FlaskGroup(create_app=create_app_cli)


@cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    click.echo('Database initialized!')


@cli.command()
def reset_db():
    """Reset the database."""
    if click.confirm('This will delete all data. Are you sure?'):
        db.drop_all()
        db.create_all()
        click.echo('Database reset!')


@cli.command()
@click.option('--username', prompt=True)
@click.option('--email', prompt=True)
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
def create_admin(username, email, password):
    """Create an admin user."""
    from src.utils.security import validate_email, validate_password_strength
    
    # Validate inputs
    if not validate_email(email):
        click.echo('Invalid email format!')
        return
    
    validation = validate_password_strength(password)
    if not validation['valid']:
        click.echo('Password validation failed:')
        for error in validation['errors']:
            click.echo(f'  - {error}')
        return
    
    # Check if user exists
    if User.query.filter((User.username == username) | (User.email == email)).first():
        click.echo('User already exists!')
        return
    
    # Create user
    user = User(username=username, email=email, role='admin')
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    click.echo(f'Admin user {username} created successfully!')


@cli.command()
def check_config():
    """Check configuration and environment."""
    click.echo('IOAgent Configuration Check')
    click.echo('=' * 40)
    
    # Check environment
    validation = EnvironmentManager.validate_environment()
    click.echo(f"Environment: {validation['environment']}")
    
    if validation['valid']:
        click.echo('✓ All required environment variables are set')
    else:
        click.echo('✗ Missing environment variables:')
        for var in validation['missing_vars']:
            click.echo(f'  - {var}')
    
    # Show configuration summary
    click.echo('\nConfiguration Summary:')
    summary = EnvironmentManager.get_config_summary()
    for key, value in summary.items():
        click.echo(f'  {key}: {value}')
    
    # Check directories
    click.echo('\nDirectory Check:')
    from src.config.config import Config
    dirs = {
        'Static': Config.STATIC_FOLDER,
        'Upload': Config.UPLOAD_FOLDER,
        'Projects': Config.PROJECTS_FOLDER
    }
    
    for name, path in dirs.items():
        if path.exists():
            click.echo(f'  ✓ {name}: {path}')
        else:
            click.echo(f'  ✗ {name}: {path} (missing)')


@cli.command()
@click.option('--key', help='Setting key (e.g., ui.items_per_page)')
@click.option('--value', help='Setting value')
def config(key, value):
    """Manage application settings."""
    if not key:
        # Show all settings
        click.echo('Current Settings:')
        import json
        click.echo(json.dumps(settings.export_settings(), indent=2))
        return
    
    if value is None:
        # Get specific setting
        current = settings.get(key)
        click.echo(f'{key}: {current}')
    else:
        # Set setting
        try:
            # Try to parse as JSON first
            import json
            parsed_value = json.loads(value)
        except:
            # Use as string
            parsed_value = value
        
        settings.set(key, parsed_value)
        click.echo(f'Set {key} = {parsed_value}')


@cli.command()
def reset_settings():
    """Reset settings to defaults."""
    if click.confirm('This will reset all settings to defaults. Are you sure?'):
        settings.reset()
        click.echo('Settings reset to defaults!')


@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=5001, help='Port to bind to')
@click.option('--debug/--no-debug', default=None, help='Enable debug mode')
def run_server(host, port, debug):
    """Run the development server."""
    app = create_app()
    
    if debug is None:
        debug = app.config['DEBUG']
    
    click.echo(f'Starting IOAgent on {host}:{port} (debug={debug})')
    app.run(host=host, port=port, debug=debug)


@cli.command()
def generate_secret():
    """Generate a secure secret key."""
    import secrets
    click.echo('Generated secret key:')
    click.echo(secrets.token_hex(32))
    click.echo('\nAdd this to your .env file as SECRET_KEY or JWT_SECRET_KEY')


@cli.command()
@click.option('--output', default='backup.json', help='Output file')
def backup_settings(output):
    """Backup application settings."""
    import json
    
    data = {
        'settings': settings.export_settings(),
        'environment': EnvironmentManager.get_config_summary()
    }
    
    with open(output, 'w') as f:
        json.dump(data, f, indent=2)
    
    click.echo(f'Settings backed up to {output}')


@cli.command()
@click.option('--input', 'input_file', default='backup.json', help='Input file')
def restore_settings(input_file):
    """Restore application settings."""
    import json
    
    if not Path(input_file).exists():
        click.echo(f'File {input_file} not found!')
        return
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    if 'settings' in data:
        settings.import_settings(data['settings'])
        click.echo('Settings restored successfully!')
    else:
        click.echo('Invalid backup file!')


if __name__ == '__main__':
    cli()