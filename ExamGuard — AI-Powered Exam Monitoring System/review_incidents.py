
import os
from pathlib import Path

from database import get_incidents, get_connection


def show_incidents():
    incidents = get_incidents()

    if not incidents:
        print("No incidents found.")
        return

    print(f"\nTotal incidents: {len(incidents)}")
    print("=" * 60)

    for incident in incidents:
        image_path = incident["screenshot_path"]
        image_exists = Path(image_path).is_file() if image_path else False

        print(
            f"ID: {incident['id']} | "
            f"Person: {incident['track_id']} | "
            f"Confidence: {incident['confidence']:.2%} | "
            f"Status: {incident['review_status']}"
        )
        print(f"Timestamp: {incident['timestamp']}")
        print(f"Image exists: {image_exists}")
        print(f"Image: {image_path}")
        print("-" * 60)


def open_incident_image():
    try:
        incident_id = int(input("Enter incident ID: "))
    except ValueError:
        print("Please enter a valid number.")
        return

    with get_connection() as conn:
        incident = conn.execute(
            "SELECT screenshot_path FROM incidents WHERE id = ?",
            (incident_id,),
        ).fetchone()

    if incident is None:
        print("Incident not found.")
        return

    image_path = incident["screenshot_path"]

    if not image_path or not Path(image_path).is_file():
        print("Incident image not found.")
        return

    os.startfile(str(Path(image_path).resolve()))
    print(f"Opening image for incident #{incident_id}...")


if __name__ == "__main__":
    while True:
        print("\n=== Cheating Tracking System ===")
        print("1. Show all incidents")
        print("2. Open incident image")
        print("3. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            show_incidents()
        elif choice == "2":
            open_incident_image()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Choose 1, 2, or 3.")
