# Build script for static deployment

import os
import shutil
import json
from pathlib import Path

def build_static():
    """Build static files for GitHub Pages deployment"""
    
    # Create dist directory
    dist_dir = Path('dist')
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir()
    
    # Copy static files
    static_dir = Path('src/static')
    if static_dir.exists():
        for file in static_dir.iterdir():
            if file.is_file():
                shutil.copy2(file, dist_dir)
    
    # Create configuration for production
    config = {
        'API_BASE_URL': 'https://ioagent.onrender.com/api',  # Your Render backend URL
        'ENVIRONMENT': 'production'
    }
    
    # Write config to JavaScript file
    config_js = f"""
// Production configuration
window.CONFIG = {json.dumps(config, indent=2)};
"""
    
    with open(dist_dir / 'config.js', 'w') as f:
        f.write(config_js)
    
    # Update app.js to use the config
    app_js_path = dist_dir / 'app.js'
    if app_js_path.exists():
        with open(app_js_path, 'r') as f:
            content = f.read()
        
        # Replace the API base URL configuration
        content = content.replace(
            "this.apiBase = window.location.origin + '/api';",
            """this.apiBase = window.CONFIG ? window.CONFIG.API_BASE_URL : window.location.origin + '/api';"""
        )
        
        with open(app_js_path, 'w') as f:
            f.write(content)
    
    # Update index.html to include config
    index_path = dist_dir / 'index.html'
    if index_path.exists():
        with open(index_path, 'r') as f:
            content = f.read()
        
        # Insert config script before app.js
        content = content.replace(
            '<script src="app.js"></script>',
            '<script src="config.js"></script>\n    <script src="app.js"></script>'
        )
        
        with open(index_path, 'w') as f:
            f.write(content)
    
    # Create .nojekyll file to bypass Jekyll processing
    (dist_dir / '.nojekyll').touch()
    
    print("Static build completed successfully!")
    print(f"Files built in: {dist_dir.absolute()}")
    print("Don't forget to update the API_BASE_URL in the config with your actual Heroku URL!")

if __name__ == '__main__':
    build_static()