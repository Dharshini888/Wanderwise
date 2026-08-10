# Offline package service

def generate_offline_package(origin: str, destination: str):
    return {
        "status": "Ready for download",
        "package_size": "12.4 MB",
        "contents": [
            "Offline Route map",
            "Hotel Addresses",
            "Emergency Contacts",
            "Weather Snapshot",
            "Trip PDF",
            "Important Documents Checklist"
        ]
    }
