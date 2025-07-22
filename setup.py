"""
Setup script for contractor enrichment system
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = requirements_path.read_text().strip().split('\n')

setup(
    name="contractor-enrichment",
    version="1.0.0",
    description="Contractor Data Enrichment System using LLM analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Contractor Enrichment Team",
    author_email="admin@contractor-enrichment.com",
    url="https://github.com/contractor-enrichment/system",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-asyncio>=0.21.0',
            'black>=22.0.0',
            'flake8>=4.0.0',
        ]
    },
    entry_points={
        'console_scripts': [
            'contractor-enrichment=main:main',
            'setup-db=scripts.setup_database:main',
            'import-data=scripts.import_data:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
    ],
    python_requires=">=3.11",
    keywords="contractor, enrichment, llm, data-processing, web-scraping",
    project_urls={
        "Bug Reports": "https://github.com/contractor-enrichment/system/issues",
        "Source": "https://github.com/contractor-enrichment/system",
    },
)