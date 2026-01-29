#!/bin/bash

echo "🚀 Tavi Hackathon - Setup Script"
echo "================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your API keys for full functionality"
    echo "   (The app will work without API keys using mock data)"
    echo ""
else
    echo "✅ .env file already exists"
    echo ""
fi

# Ask if user wants to start the application
echo "Would you like to start the application now? (y/n)"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo ""
    echo "🏗️  Building and starting Docker containers..."
    echo "   This may take a few minutes on first run..."
    echo ""
    
    docker-compose up --build -d
    
    echo ""
    echo "✅ Application started successfully!"
    echo ""
    echo "📍 Access points:"
    echo "   Frontend:  http://localhost:3000"
    echo "   Backend:   http://localhost:8000"
    echo "   API Docs:  http://localhost:8000/docs"
    echo ""
    echo "📊 View logs:"
    echo "   docker-compose logs -f"
    echo ""
    echo "🛑 Stop application:"
    echo "   docker-compose down"
    echo ""
else
    echo ""
    echo "👍 Setup complete! Start the application when ready with:"
    echo "   docker-compose up --build"
    echo ""
fi
