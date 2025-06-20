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
        'API_BASE_URL': 'https://your-backend-url.herokuapp.com/api',  # Update this
        'ENVIRONMENT': 'production'
    }
    
    # Write config to JavaScript file
    config_js = f"""
// Production configuration
window.CONFIG = {json.dumps(config, indent=2)};
"""
    
    with open(dist_dir / 'config.js', 'w') as f:
        f.write(config_js)
    
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
    
    # Create CNAME file if custom domain is needed
    # (dist_dir / 'CNAME').write_text('your-domain.com')
    
    print("Static build completed successfully!")
    print(f"Files built in: {dist_dir.absolute()}")

if __name__ == '__main__':
    build_static()

