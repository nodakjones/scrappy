#!/usr/bin/env python3
"""
Docker setup script for contractor enrichment system
"""
import os
import subprocess
import sys
from pathlib import Path


def run_command(command, check=True):
    """Run a shell command"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result


def check_docker():
    """Check if Docker is installed and running"""
    try:
        result = run_command("docker --version", check=False)
        if result.returncode != 0:
            print("❌ Docker is not installed. Please install Docker first.")
            return False
        
        result = run_command("docker-compose --version", check=False)
        if result.returncode != 0:
            print("❌ Docker Compose is not installed. Please install Docker Compose first.")
            return False
        
        result = run_command("docker info", check=False)
        if result.returncode != 0:
            print("❌ Docker daemon is not running. Please start Docker first.")
            return False
        
        print("✅ Docker and Docker Compose are ready")
        return True
    except Exception as e:
        print(f"❌ Error checking Docker: {e}")
        return False


def setup_environment():
    """Set up environment file"""
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("📝 Creating .env file from template...")
            run_command(f"cp env.example .env")
            print("⚠️  Please edit .env file with your API keys before running the application")
        else:
            print("❌ env.example file not found")
            return False
    else:
        print("✅ .env file already exists")
    
    return True


def build_and_start():
    """Build and start the Docker containers"""
    print("🔨 Building Docker images...")
    run_command("docker-compose build")
    
    print("🚀 Starting services...")
    run_command("docker-compose up -d")
    
    print("⏳ Waiting for services to be ready...")
    run_command("docker-compose ps")
    
    print("✅ Services are starting up!")
    print("📊 You can check logs with: docker-compose logs -f")


def show_usage():
    """Show usage information"""
    print("\n📋 Docker Setup Complete!")
    print("\n🔧 Available commands:")
    print("  docker-compose up -d          # Start services in background")
    print("  docker-compose down           # Stop services")
    print("  docker-compose logs -f        # Follow logs")
    print("  docker-compose exec app bash  # Access app container")
    print("  docker-compose exec postgres psql -U postgres -d contractor_enrichment  # Access database")
    
    print("\n📁 Important directories:")
    print("  ./data/                       # Data files (mounted to container)")
    print("  ./exports/                    # Export files (mounted to container)")
    print("  ./sql/                        # Database initialization scripts")
    
    print("\n⚠️  Remember to:")
    print("  1. Edit .env file with your API keys")
    print("  2. Place your data files in ./data/ directory")
    print("  3. Check logs if something goes wrong")


def main():
    """Main setup function"""
    print("🐳 Setting up Contractor Enrichment System with Docker")
    print("=" * 60)
    
    # Check Docker installation
    if not check_docker():
        sys.exit(1)
    
    # Set up environment
    if not setup_environment():
        sys.exit(1)
    
    # Build and start services
    try:
        build_and_start()
        show_usage()
    except KeyboardInterrupt:
        print("\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 