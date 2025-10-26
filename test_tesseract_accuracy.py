#!/usr/bin/env python3
"""Tesseract OCR Accuracy Testing - Multiple Approaches"""

import tempfile
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from app.ocr_service import OCRService
import difflib
import re
from typing import List, Dict, Any, Optional
import os

class TesseractAccuracyTester:
    def __init__(self):
        self.ocr_service = OCRService()
        
    def approach_1_synthetic_data(self) -> List[Dict[str, Any]]:
        """Approach 1: Create synthetic test data (no manual labeling needed)"""
        print("🎨 Creating synthetic test data...")
        
        test_cases = [
            # Patient Information
            {
                "name": "patient_name_simple",
                "text": "Patient: John R. Doe",
                "expected": "John R. Doe",
                "category": "patient_info",
                "difficulty": "easy"
            },
            {
                "name": "patient_name_complex",
                "text": "Patient Name: Mary Elizabeth Smith-Johnson",
                "expected": "Mary Elizabeth Smith-Johnson", 
                "category": "patient_info",
                "difficulty": "medium"
            },
            
            # Demographics
            {
                "name": "date_of_birth",
                "text": "Date of Birth: 01/15/1980",
                "expected": "01/15/1980",
                "category": "demographics",
                "difficulty": "easy"
            },
            {
                "name": "patient_id",
                "text": "Patient ID: MR-123456789",
                "expected": "MR-123456789",
                "category": "identifiers",
                "difficulty": "medium"
            },
            
            # Vital Signs
            {
                "name": "vital_signs_basic",
                "text": "BP: 140/90 mmHg\nHR: 72 bpm",
                "expected": ["140/90", "72"],
                "category": "vitals",
                "difficulty": "easy"
            },
            {
                "name": "vital_signs_complex",
                "text": "Blood Pressure: 140/90 mmHg\nHeart Rate: 72 bpm\nTemperature: 98.6°F",
                "expected": ["140/90", "72", "98.6"],
                "category": "vitals",
                "difficulty": "medium"
            },
            
            # Diagnoses
            {
                "name": "diagnosis_single",
                "text": "Diagnosis: Hypertension",
                "expected": "Hypertension",
                "category": "diagnosis",
                "difficulty": "easy"
            },
            {
                "name": "diagnosis_multiple",
                "text": "Diagnoses:\n1. Hypertension\n2. Type 2 Diabetes\n3. Hyperlipidemia",
                "expected": ["Hypertension", "Type 2 Diabetes", "Hyperlipidemia"],
                "category": "diagnosis",
                "difficulty": "hard"
            },
            
            # Medications
            {
                "name": "medications_simple",
                "text": "Medications:\n- Lisinopril 10mg daily\n- Metformin 500mg twice daily",
                "expected": ["Lisinopril", "Metformin"],
                "category": "medications",
                "difficulty": "medium"
            },
            {
                "name": "medications_complex",
                "text": "Current Medications:\n1. Lisinopril 10mg PO QD\n2. Metformin 500mg PO BID\n3. Atorvastatin 20mg PO QHS",
                "expected": ["Lisinopril", "Metformin", "Atorvastatin"],
                "category": "medications",
                "difficulty": "hard"
            }
        ]
        
        return test_cases
    
    def approach_2_real_documents(self, document_folder: str) -> List[Dict[str, Any]]:
        """Approach 2: Test with real documents (requires manual verification)"""
        print(f"📁 Testing with real documents from: {document_folder}")
        
        if not os.path.exists(document_folder):
            print(f"❌ Folder {document_folder} does not exist")
            return []
        
        test_cases = []
        supported_extensions = ['.png', '.jpg', '.jpeg', '.pdf', '.tiff']
        
        for file_path in Path(document_folder).iterdir():
            if file_path.suffix.lower() in supported_extensions:
                test_cases.append({
                    "name": f"real_doc_{file_path.stem}",
                    "file_path": str(file_path),
                    "category": "real_document",
                    "difficulty": "unknown",
                    "needs_manual_verification": True
                })
        
        return test_cases
    
    def approach_3_ground_truth_dataset(self, dataset_file: str) -> List[Dict[str, Any]]:
        """Approach 3: Use pre-labeled dataset (most accurate)"""
        print(f"📊 Loading ground truth dataset from: {dataset_file}")
        
        if not os.path.exists(dataset_file):
            print(f"❌ Dataset file {dataset_file} does not exist")
            return []
        
        try:
            with open(dataset_file, 'r') as f:
                dataset = json.load(f)
            return dataset
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            return []
    
    def create_image_with_text(self, text: str, font_size: int = 24, image_size: tuple = (600, 300)) -> Image.Image:
        """Create a test image with the given text"""
        img = Image.new('RGB', image_size, color='white')
        draw = ImageDraw.Draw(img)
        
        # Try different fonts
        font = None
        font_options = ["arial.ttf", "calibri.ttf", "times.ttf", "helvetica.ttf"]
        
        for font_name in font_options:
            try:
                font = ImageFont.truetype(font_name, font_size)
                break
            except:
                continue
        
        if font is None:
            font = ImageFont.load_default()
        
        # Draw text
        draw.text((20, 50), text, fill='black', font=font)
        return img
    
    def test_single_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single case and return accuracy metrics"""
        print(f"Testing: {test_case['name']}")
        
        if 'file_path' in test_case:
            # Real document testing
            return self.test_real_document(test_case)
        else:
            # Synthetic data testing
            return self.test_synthetic_case(test_case)
    
    def test_synthetic_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Test synthetic test case"""
        # Create test image
        image = self.create_image_with_text(test_case['text'])
        
        # Convert to bytes
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            image.save(tmp_file.name)
            temp_path = tmp_file.name
        
        try:
            # Extract text using OCR
            extracted_text = self.ocr_service.extract_text_from_image(temp_path)
            
            # Calculate accuracy metrics
            metrics = self.calculate_accuracy_metrics(
                extracted_text, 
                test_case['expected'], 
                test_case['category']
            )
            
            return {
                "test_case": test_case['name'],
                "category": test_case['category'],
                "difficulty": test_case['difficulty'],
                "expected": test_case['expected'],
                "extracted": extracted_text,
                "metrics": metrics,
                "success": metrics['overall_accuracy'] > 0.7,
                "test_type": "synthetic"
            }
            
        finally:
            # Clean up
            if Path(temp_path).exists():
                Path(temp_path).unlink()
    
    def test_real_document(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Test real document (requires manual verification)"""
        file_path = test_case['file_path']
        
        try:
            # Extract text using OCR
            if file_path.lower().endswith('.pdf'):
                extracted_text = self.ocr_service.extract_text_from_scanned_pdf(file_path)
            else:
                extracted_text = self.ocr_service.extract_text_from_image(file_path)
            
            return {
                "test_case": test_case['name'],
                "category": test_case['category'],
                "file_path": file_path,
                "extracted": extracted_text,
                "needs_manual_verification": True,
                "test_type": "real_document"
            }
            
        except Exception as e:
            return {
                "test_case": test_case['name'],
                "category": test_case['category'],
                "file_path": file_path,
                "error": str(e),
                "test_type": "real_document"
            }
    
    def calculate_accuracy_metrics(self, extracted: str, expected: Any, category: str) -> Dict[str, float]:
        """Calculate various accuracy metrics"""
        if isinstance(expected, list):
            expected_str = " ".join(expected)
        else:
            expected_str = str(expected)
        
        # Character-level accuracy
        char_accuracy = self.calculate_char_accuracy(extracted, expected_str)
        
        # Word-level accuracy
        word_accuracy = self.calculate_word_accuracy(extracted, expected_str)
        
        # Sequence similarity
        similarity_ratio = difflib.SequenceMatcher(None, extracted.lower(), expected_str.lower()).ratio()
        
        # Category-specific accuracy
        category_accuracy = self.calculate_category_accuracy(extracted, expected, category)
        
        # Overall accuracy (weighted average)
        overall_accuracy = (
            char_accuracy * 0.3 +
            word_accuracy * 0.3 +
            similarity_ratio * 0.2 +
            category_accuracy * 0.2
        )
        
        return {
            "char_accuracy": char_accuracy,
            "word_accuracy": word_accuracy,
            "similarity_ratio": similarity_ratio,
            "category_accuracy": category_accuracy,
            "overall_accuracy": overall_accuracy
        }
    
    def calculate_char_accuracy(self, extracted: str, expected: str) -> float:
        """Calculate character-level accuracy"""
        if not expected:
            return 0.0
        
        extracted = extracted.lower().strip()
        expected = expected.lower().strip()
        
        matches = sum(1 for a, b in zip(extracted, expected) if a == b)
        max_len = max(len(extracted), len(expected))
        
        return matches / max_len if max_len > 0 else 0.0
    
    def calculate_word_accuracy(self, extracted: str, expected: str) -> float:
        """Calculate word-level accuracy"""
        extracted_words = set(extracted.lower().split())
        expected_words = set(expected.lower().split())
        
        if not expected_words:
            return 0.0
        
        matches = len(extracted_words.intersection(expected_words))
        return matches / len(expected_words)
    
    def calculate_category_accuracy(self, extracted: str, expected: Any, category: str) -> float:
        """Calculate category-specific accuracy"""
        extracted_lower = extracted.lower()
        
        if category == "patient_info":
            # Look for name patterns
            name_patterns = [
                r"[A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+",  # John R. Doe
                r"[A-Z][a-z]+ [A-Z][a-z]+",          # John Doe
                r"[A-Z][a-z]+ [A-Z][a-z]+-[A-Z][a-z]+"  # Smith-Johnson
            ]
            
            for pattern in name_patterns:
                if re.search(pattern, extracted):
                    return 1.0
            return 0.0
            
        elif category == "demographics":
            # Look for date patterns
            date_patterns = [
                r"\d{2}/\d{2}/\d{4}",  # MM/DD/YYYY
                r"\d{4}-\d{2}-\d{2}"   # YYYY-MM-DD
            ]
            
            for pattern in date_patterns:
                if re.search(pattern, extracted):
                    return 1.0
            return 0.0
            
        elif category == "vitals":
            # Look for vital sign patterns
            vital_patterns = [
                r"\d+/\d+",  # Blood pressure
                r"\d+\s*bpm",  # Heart rate
                r"\d+\.\d+\s*°F"  # Temperature
            ]
            
            matches = 0
            for pattern in vital_patterns:
                if re.search(pattern, extracted):
                    matches += 1
            
            return min(matches / len(vital_patterns), 1.0)
            
        elif category == "diagnosis":
            # Look for medical terms
            medical_terms = ["hypertension", "diabetes", "cancer", "pneumonia", "asthma"]
            matches = sum(1 for term in medical_terms if term in extracted_lower)
            return matches / len(medical_terms)
            
        elif category == "medications":
            # Look for medication patterns
            med_patterns = [
                r"[A-Z][a-z]+",  # Drug names
                r"\d+\s*mg",     # Dosage
                r"daily|twice|bid|tid"  # Frequency
            ]
            
            matches = 0
            for pattern in med_patterns:
                if re.search(pattern, extracted):
                    matches += 1
            
            return min(matches / len(med_patterns), 1.0)
            
        else:
            # Default: use similarity
            return difflib.SequenceMatcher(None, extracted.lower(), str(expected).lower()).ratio()
    
    def run_test(self, approach: str = "synthetic", **kwargs) -> Dict[str, Any]:
        """Run accuracy test with specified approach"""
        print(f"🧪 Running Tesseract OCR Accuracy Test - {approach.upper()} approach")
        print("=" * 60)
        
        # Get test cases based on approach
        if approach == "synthetic":
            test_cases = self.approach_1_synthetic_data()
        elif approach == "real":
            document_folder = kwargs.get('document_folder', 'test_documents')
            test_cases = self.approach_2_real_documents(document_folder)
        elif approach == "dataset":
            dataset_file = kwargs.get('dataset_file', 'ground_truth_dataset.json')
            test_cases = self.approach_3_ground_truth_dataset(dataset_file)
        else:
            raise ValueError(f"Unknown approach: {approach}")
        
        if not test_cases:
            print("❌ No test cases found")
            return {}
        
        # Run tests
        results = []
        for test_case in test_cases:
            result = self.test_single_case(test_case)
            results.append(result)
            
            # Print individual results
            self.print_single_result(result)
        
        # Generate summary
        summary = self.generate_summary(results)
        self.print_summary(summary)
        
        return {
            "approach": approach,
            "individual_results": results,
            "summary": summary
        }
    
    def print_single_result(self, result: Dict[str, Any]):
        """Print results for a single test case"""
        print(f"\n📋 {result['test_case']} ({result.get('category', 'unknown')})")
        
        if result.get('test_type') == 'real_document':
            print(f"File: {result.get('file_path', 'unknown')}")
            print(f"Extracted: {result.get('extracted', 'No text extracted')[:100]}...")
            print(f"Status: {'✅ SUCCESS' if 'error' not in result else '❌ ERROR'}")
            if 'error' in result:
                print(f"Error: {result['error']}")
        else:
            print(f"Expected: {result.get('expected', 'N/A')}")
            print(f"Extracted: {result.get('extracted', 'N/A')}")
            print(f"Overall Accuracy: {result.get('metrics', {}).get('overall_accuracy', 0):.2%}")
            print(f"Status: {'✅ PASS' if result.get('success', False) else '❌ FAIL'}")
    
    def generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate test summary"""
        synthetic_results = [r for r in results if r.get('test_type') == 'synthetic']
        real_results = [r for r in results if r.get('test_type') == 'real_document']
        
        summary = {
            "total_tests": len(results),
            "synthetic_tests": len(synthetic_results),
            "real_document_tests": len(real_results)
        }
        
        if synthetic_results:
            # Calculate synthetic test metrics
            passed_tests = sum(1 for r in synthetic_results if r.get('success', False))
            avg_char_accuracy = sum(r.get('metrics', {}).get('char_accuracy', 0) for r in synthetic_results) / len(synthetic_results)
            avg_word_accuracy = sum(r.get('metrics', {}).get('word_accuracy', 0) for r in synthetic_results) / len(synthetic_results)
            avg_overall_accuracy = sum(r.get('metrics', {}).get('overall_accuracy', 0) for r in synthetic_results) / len(synthetic_results)
            
            summary.update({
                "synthetic_pass_rate": passed_tests / len(synthetic_results),
                "avg_char_accuracy": avg_char_accuracy,
                "avg_word_accuracy": avg_word_accuracy,
                "avg_overall_accuracy": avg_overall_accuracy
            })
        
        if real_results:
            # Calculate real document metrics
            successful_extractions = sum(1 for r in real_results if 'error' not in r)
            summary["real_document_success_rate"] = successful_extractions / len(real_results)
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 ACCURACY TEST SUMMARY")
        print("=" * 60)
        
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Synthetic Tests: {summary['synthetic_tests']}")
        print(f"Real Document Tests: {summary['real_document_tests']}")
        
        if 'synthetic_pass_rate' in summary:
            print(f"\nSynthetic Test Results:")
            print(f"  Pass Rate: {summary['synthetic_pass_rate']:.2%}")
            print(f"  Avg Character Accuracy: {summary['avg_char_accuracy']:.2%}")
            print(f"  Avg Word Accuracy: {summary['avg_word_accuracy']:.2%}")
            print(f"  Avg Overall Accuracy: {summary['avg_overall_accuracy']:.2%}")
        
        if 'real_document_success_rate' in summary:
            print(f"\nReal Document Results:")
            print(f"  Success Rate: {summary['real_document_success_rate']:.2%}")


def main():
    """Main function to run different testing approaches"""
    tester = TesseractAccuracyTester()
    
    print("🎯 Choose your testing approach:")
    print("1. Synthetic Data (No manual labeling needed)")
    print("2. Real Documents (Requires manual verification)")
    print("3. Ground Truth Dataset (Most accurate)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        # Approach 1: Synthetic data
        results = tester.run_test("synthetic")
        
    elif choice == "2":
        # Approach 2: Real documents
        folder = input("Enter folder path with test documents: ").strip()
        if not folder:
            folder = "test_documents"
        
        results = tester.run_test("real", document_folder=folder)
        
    elif choice == "3":
        # Approach 3: Ground truth dataset
        dataset_file = input("Enter dataset file path: ").strip()
        if not dataset_file:
            dataset_file = "ground_truth_dataset.json"
        
        results = tester.run_test("dataset", dataset_file=dataset_file)
        
    else:
        print("Invalid choice. Running synthetic test by default.")
        results = tester.run_test("synthetic")
    
    # Save results
    output_file = f"tesseract_accuracy_results_{choice}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    main()
