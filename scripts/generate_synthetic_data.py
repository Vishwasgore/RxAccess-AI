"""
Generate synthetic prescription data for testing
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


def generate_prescription_image(output_path: Path):
    """Generate a synthetic prescription image"""
    
    # Create image
    width, height = 800, 1000
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a font, fallback to default
    try:
        title_font = ImageFont.truetype("arial.ttf", 24)
        header_font = ImageFont.truetype("arial.ttf", 18)
        body_font = ImageFont.truetype("arial.ttf", 14)
    except:
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
    
    y_position = 50
    
    # Clinic header
    draw.text((50, y_position), "CITY MEDICAL CENTER", fill='black', font=title_font)
    y_position += 40
    draw.text((50, y_position), "123 Healthcare Ave, Medical City, MC 12345", fill='black', font=body_font)
    y_position += 25
    draw.text((50, y_position), "Phone: (555) 123-4567 | Fax: (555) 123-4568", fill='black', font=body_font)
    y_position += 50
    
    # Prescription title
    draw.text((50, y_position), "PRESCRIPTION", fill='black', font=header_font)
    y_position += 40
    
    # Date
    date_str = (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%m/%d/%Y")
    draw.text((50, y_position), f"Date: {date_str}", fill='black', font=body_font)
    y_position += 40
    
    # Patient info
    patient_names = ["John Smith", "Mary Johnson", "Robert Williams", "Patricia Brown"]
    patient_name = random.choice(patient_names)
    draw.text((50, y_position), f"Patient Name: {patient_name}", fill='black', font=body_font)
    y_position += 25
    draw.text((50, y_position), f"DOB: {random.randint(1, 12)}/{random.randint(1, 28)}/{random.randint(1950, 2000)}", fill='black', font=body_font)
    y_position += 25
    draw.text((50, y_position), f"Address: {random.randint(100, 999)} Main St, City, ST {random.randint(10000, 99999)}", fill='black', font=body_font)
    y_position += 50
    
    # Medication
    medications = [
        ("Lisinopril", "10mg", "Once daily", "Take in the morning"),
        ("Metformin", "500mg", "Twice daily", "Take with meals"),
        ("Atorvastatin", "20mg", "Once daily at bedtime", "Take at night"),
        ("Amlodipine", "5mg", "Once daily", "Take in the morning")
    ]
    
    med = random.choice(medications)
    draw.text((50, y_position), "Rx:", fill='black', font=header_font)
    y_position += 30
    draw.text((70, y_position), f"{med[0]} {med[1]}", fill='black', font=body_font)
    y_position += 25
    draw.text((70, y_position), f"Sig: {med[2]}", fill='black', font=body_font)
    y_position += 25
    draw.text((70, y_position), f"Disp: 30 tablets", fill='black', font=body_font)
    y_position += 25
    draw.text((70, y_position), f"Refills: {random.randint(0, 3)}", fill='black', font=body_font)
    y_position += 25
    draw.text((70, y_position), f"Instructions: {med[3]}", fill='black', font=body_font)
    y_position += 50
    
    # Diagnosis
    diagnoses = ["Hypertension", "Type 2 Diabetes", "Hyperlipidemia", "Coronary Artery Disease"]
    draw.text((50, y_position), f"Diagnosis: {random.choice(diagnoses)}", fill='black', font=body_font)
    y_position += 50
    
    # Provider info
    doctors = ["Dr. Sarah Johnson, MD", "Dr. Michael Chen, MD", "Dr. Emily Rodriguez, MD"]
    draw.text((50, y_position), f"Prescriber: {random.choice(doctors)}", fill='black', font=body_font)
    y_position += 25
    draw.text((50, y_position), f"NPI: {random.randint(1000000000, 9999999999)}", fill='black', font=body_font)
    y_position += 25
    draw.text((50, y_position), "License: MD-12345", fill='black', font=body_font)
    y_position += 50
    
    # Signature line
    draw.line([(50, y_position), (300, y_position)], fill='black', width=2)
    y_position += 5
    draw.text((50, y_position), "Prescriber Signature", fill='gray', font=body_font)
    
    # Save image
    img.save(output_path)
    logger.info(f"Generated prescription image: {output_path}")


def main():
    """Generate multiple synthetic prescriptions"""
    print("📄 Generating Synthetic Prescription Data")
    print("=" * 50)
    
    output_dir = settings.synthetic_data_dir / "prescriptions"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    num_prescriptions = 5
    
    for i in range(num_prescriptions):
        output_path = output_dir / f"prescription_{i+1}.png"
        generate_prescription_image(output_path)
        print(f"✓ Generated: {output_path.name}")
    
    print(f"\n✅ Generated {num_prescriptions} synthetic prescriptions")
    print(f"Location: {output_dir}")


if __name__ == "__main__":
    main()
