"""
Configuration Checker for PythonAnywhere Deployment
Run this script to verify your setup is correct
"""
import os
import sys

def check_config():
    print("🔍 Checking Bid Management System Configuration...\n")
    
    issues = []
    warnings = []
    
    # Check Python version
    py_version = sys.version_info
    if py_version.major == 3 and py_version.minor >= 9:
        print(f"✅ Python version: {py_version.major}.{py_version.minor}.{py_version.micro}")
    else:
        issues.append(f"❌ Python version {py_version.major}.{py_version.minor} is too old. Need Python 3.9+")
    
    # Check required files
    required_files = [
        'app.py',
        'db_helper.py',
        'create_database.py',
        'requirements.txt',
        'wsgi.py'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ Found: {file}")
        else:
            issues.append(f"❌ Missing: {file}")
    
    # Check templates folder
    if os.path.exists('templates'):
        template_files = os.listdir('templates')
        print(f"✅ Templates folder: {len(template_files)} files")
        
        required_templates = [
            'base.html', 'admin_dashboard.html',
            'vendor_login.html', 'vendor_dashboard.html',
            'a1_dashboard.html', 'a2_dashboard.html'
        ]
        
        for template in required_templates:
            if template not in template_files:
                warnings.append(f"⚠️  Missing template: {template}")
    else:
        issues.append("❌ Missing templates folder")
    
    # Check database
    if os.path.exists('database.xlsx'):
        print("✅ Database file exists")
    else:
        warnings.append("⚠️  Database file not found. Run: python create_database.py")
    
    # Check secret key in app.py
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if "app.secret_key = 'your-secret-key-here'" in content:
                warnings.append("⚠️  Default secret key detected. Change it for production!")
            else:
                print("✅ Secret key has been customized")
    except:
        warnings.append("⚠️  Could not check secret key")
    
    # Check for WSGI configuration
    try:
        with open('wsgi.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'YOUR_USERNAME' in content:
                issues.append("❌ WSGI file still has 'YOUR_USERNAME' placeholder. Replace it!")
            else:
                print("✅ WSGI file configured")
    except:
        issues.append("❌ Could not check WSGI file")
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    
    if not issues and not warnings:
        print("✅ Everything looks good! Ready for deployment.")
        print("\nNext steps:")
        print("1. Upload files to PythonAnywhere")
        print("2. Set up virtual environment")
        print("3. Configure WSGI (replace YOUR_USERNAME)")
        print("4. Reload web app")
        return True
    
    if warnings:
        print(f"\n⚠️  {len(warnings)} WARNING(S):")
        for warning in warnings:
            print(f"   {warning}")
    
    if issues:
        print(f"\n❌ {len(issues)} ISSUE(S) FOUND:")
        for issue in issues:
            print(f"   {issue}")
        print("\nPlease fix these issues before deploying.")
        return False
    
    print("\n✅ No critical issues found. Address warnings if needed.")
    return True

if __name__ == '__main__':
    try:
        success = check_config()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error running config check: {e}")
        sys.exit(1)
