from setuptools import setup

setup(
    name="emergency-card",
    version="1.0.0",
    description="Digitalt nodkort for nodsituationer - offline-forst",
    author="EmergencyCard",
    py_modules=["emergency_card"],
    install_requires=["PyGObject", "qrcode", "pillow"],
    entry_points={
        "console_scripts": [
            "emergency-card=emergency_card:main",
        ],
    },
    data_files=[
        ("share/applications", ["se.emergencycard.app.desktop"]),
    ],
    python_requires=">=3.8",
)
