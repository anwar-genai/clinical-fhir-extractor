"""Pytest configuration and fixtures"""

import pytest


@pytest.fixture
def sample_clinical_text():
    """Fixture providing sample non-PHI clinical text"""
    return """
    Clinical Assessment
    
    Patient: Test Patient (Example)
    Date of Birth: 1975-05-20
    Gender: Male
    
    Presenting Problem: Routine checkup
    
    Vital Signs:
    - BP: 130/85 mmHg
    - HR: 78 bpm
    - Temp: 98.2°F
    - Weight: 80 kg
    - Height: 175 cm
    
    Current Diagnoses:
    1. Essential Hypertension
    2. Hyperlipidemia
    
    Current Medications:
    1. Atorvastatin 20mg once daily
    2. Losartan 50mg once daily
    
    Assessment: Stable, continue current treatment plan.
    """

