#!/usr/bin/env python3
"""Example: How to test with real documents"""

import os
from pathlib import Path
from test_tesseract_accuracy import TesseractAccuracyTester

def setup_real_document_testing():
    """Setup for testing with real documents"""
    
    print("📁 Setting up real document testing...")
    
    # Create test documents folder
    test_folder = Path("test_documents")
    test_folder.mkdir(exist_ok=True)
    
    print(f"✅ Created folder: {test_folder}")
    print(f"📋 Place your test documents in: {test_folder.absolute()}")
    print("\nSupported formats:")
    print("  - PNG, JPG, JPEG (images)")
    print("  - PDF (scanned documents)")
    print("  - TIFF (high-quality scans)")
    
    print("\n📝 Manual verification process:")
    print("1. Place 5-10 clinical documents in the test_documents folder")
    print("2. Run the test script")
    print("3. Review extracted text for each document")
    print("4. Manually verify accuracy")
    print("5. Document any errors or improvements needed")
    
    return test_folder

def run_real_document_test():
    """Run test with real documents"""
    tester = TesseractAccuracyTester()
    
    # Check if test documents folder exists
    test_folder = "test_documents"
    if not os.path.exists(test_folder):
        print(f"❌ Test folder '{test_folder}' not found")
        print("Creating folder and instructions...")
        setup_real_document_testing()
        return
    
    # Count documents
    supported_extensions = ['.png', '.jpg', '.jpeg', '.pdf', '.tiff']
    documents = []
    
    for file_path in Path(test_folder).iterdir():
        if file_path.suffix.lower() in supported_extensions:
            documents.append(file_path)
    
    if not documents:
        print(f"❌ No supported documents found in '{test_folder}'")
        print("Please add some test documents and try again.")
        return
    
    print(f"📄 Found {len(documents)} test documents:")
    for doc in documents:
        print(f"  - {doc.name}")
    
    # Run the test
    results = tester.run_test("real", document_folder=test_folder)
    
    # Save results
    with open('real_document_test_results.json', 'w') as f:
        import json
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: real_document_test_results.json")
    
    # Manual verification instructions
    print("\n🔍 Manual Verification Instructions:")
    print("1. Review the extracted text for each document")
    print("2. Check for accuracy of:")
    print("   - Patient names")
    print("   - Dates")
    print("   - Medical terms")
    print("   - Numbers and measurements")
    print("3. Note any systematic errors")
    print("4. Consider adjusting OCR preprocessing if needed")

if __name__ == "__main__":
    run_real_document_test()
