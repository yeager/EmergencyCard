from setuptools import setup, find_packages

setup(
    name="emergency-card",
    version="1.0.0",
    description="Digitalt nodkort for nodsituationer - offline-forst",
    author="EmergencyCard",
    packages=find_packages(),
    package_data={
        "": ["locale/*/LC_MESSAGES/*.mo"],
    },
    install_requires=["PyGObject", "qrcode", "pillow"],
    entry_points={
        "console_scripts": [
            "emergency-card=emergencycard.app:main",
        ],
    },
    data_files=[
        ("share/applications", ["se.emergencycard.app.desktop"]),
    ],
    python_requires=">=3.8",
)