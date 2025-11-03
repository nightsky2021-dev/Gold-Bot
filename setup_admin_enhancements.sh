#!/bin/bash

# Admin Panel Enhancement Setup Script
# This script sets up the enhanced admin panel for the Gold Trading Bot System

echo "🚀 Setting up Admin Panel Enhancements..."
echo ""

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Error: Python is not installed or not in PATH"
    exit 1
fi

echo "📦 Installing required packages..."
pip install -r requirements.txt

echo ""
echo "🗄️  Running database migrations..."
python manage.py makemigrations
python manage.py migrate

echo ""
echo "📊 Collecting static files..."
python manage.py collectstatic --noinput

echo ""
echo "✅ Admin Panel Enhancements Setup Complete!"
echo ""
echo "📚 Next steps:"
echo "   1. Create a superuser if you haven't already:"
echo "      python manage.py createsuperuser"
echo ""
echo "   2. Start the development server:"
echo "      python manage.py runserver"
echo ""
echo "   3. Access the admin panel at:"
echo "      http://localhost:8000/admin/"
echo ""
echo "   4. View the dashboard at:"
echo "      http://localhost:8000/admin/dashboard/"
echo ""
echo "📖 For detailed documentation, see ADMIN_PANEL_ENHANCEMENTS.md"
echo ""
