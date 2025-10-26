# OCR Accuracy Testing Framework

A comprehensive testing framework for evaluating Tesseract OCR accuracy on clinical documents. This tool helps you measure and improve OCR performance for medical text extraction.

## 🎯 **Testing Approaches**

### 1. **Synthetic Data Testing** (Recommended for Start)
- ✅ **No manual labeling required**
- ✅ **Automatic accuracy calculation**
- ✅ **10 predefined test cases**
- ✅ **Immediate results**

### 2. **Real Document Testing**
- 📁 **5-10 real clinical documents**
- 🔍 **Manual verification required**
- 📊 **Real-world accuracy assessment**

### 3. **Ground Truth Dataset Testing**
- 📋 **Pre-labeled dataset**
- 🎯 **Most accurate evaluation**
- 📈 **Comprehensive metrics**

## 🚀 **Quick Start**

### **Option 1: Synthetic Testing (No Setup Required)**
```bash
python test_tesseract_accuracy.py
# Choose option 1
```

### **Option 2: Real Document Testing**
```bash
# 1. Create test documents folder
mkdir test_documents

# 2. Add your clinical documents (PNG, JPG, PDF, TIFF)
# Place files in test_documents/ folder

# 3. Run the test
python test_tesseract_accuracy.py
# Choose option 2
```

### **Option 3: Ground Truth Dataset**
```bash
# 1. Use the template
cp ground_truth_dataset_template.json ground_truth_dataset.json

# 2. Add your test documents and update the JSON file

# 3. Run the test
python test_tesseract_accuracy.py
# Choose option 3
```

## 📊 **Test Results Example**

```
🧪 Running Tesseract OCR Accuracy Test - SYNTHETIC approach
============================================================

📋 patient_name_simple (patient_info)
Expected: John R. Doe
Extracted: Patient: John R. Doe
Overall Accuracy: 64.19%
Status: ❌ FAIL

📊 ACCURACY TEST SUMMARY
============================================================
Total Tests: 10
Pass Rate: 0.00%
Avg Character Accuracy: 1.46%
Avg Word Accuracy: 96.67%
Avg Overall Accuracy: 56.12%
```

## 📈 **Accuracy Metrics**

### **Character-Level Accuracy**
- Measures exact character matching
- Useful for precise data extraction
- Target: >90%

### **Word-Level Accuracy**
- Measures word recognition
- Good for general text understanding
- Target: >95%

### **Category-Specific Accuracy**
- **Patient Info**: Name recognition patterns
- **Demographics**: Date and ID patterns
- **Vitals**: Blood pressure, heart rate patterns
- **Diagnosis**: Medical term recognition
- **Medications**: Drug name and dosage patterns

### **Overall Accuracy**
- Weighted combination of all metrics
- Target: >80% for production use

## 🧪 **Test Cases**

### **Synthetic Test Cases (10 total)**
1. **Patient Name Simple**: "John R. Doe"
2. **Patient Name Complex**: "Mary Elizabeth Smith-Johnson"
3. **Date of Birth**: "01/15/1980"
4. **Patient ID**: "MR-123456789"
5. **Vital Signs Basic**: "BP: 140/90 mmHg, HR: 72 bpm"
6. **Vital Signs Complex**: Multiple vital signs
7. **Diagnosis Single**: "Hypertension"
8. **Diagnosis Multiple**: Multiple conditions
9. **Medications Simple**: Basic medication list
10. **Medications Complex**: Detailed medication list

### **Real Document Categories**
- Patient records
- Medication lists
- Lab results
- Discharge summaries
- Vital signs charts

## 🔧 **Customization**

### **Adding New Test Cases**
Edit `test_tesseract_accuracy.py` and add to `approach_1_synthetic_data()`:

```python
{
    "name": "your_test_case",
    "text": "Your test text here",
    "expected": "Expected result",
    "category": "category_name",
    "difficulty": "easy|medium|hard"
}
```

### **Modifying Accuracy Thresholds**
Change the success threshold in `test_synthetic_case()`:

```python
"success": metrics['overall_accuracy'] > 0.8  # Change from 0.7 to 0.8
```

### **Adding New Categories**
Extend `calculate_category_accuracy()` method with new medical categories.

## 📁 **File Structure**

```
├── test_tesseract_accuracy.py          # Main testing framework
├── test_real_documents.py              # Real document testing helper
├── ground_truth_dataset_template.json  # Dataset template
├── test_documents/                     # Folder for real documents
│   ├── patient_record_001.png
│   ├── medication_list_001.jpg
│   └── lab_results_001.pdf
└── results/
    ├── tesseract_accuracy_results_1.json
    ├── tesseract_accuracy_results_2.json
    └── real_document_test_results.json
```

## 🎯 **Interpretation Guide**

### **Good Results**
- Word Accuracy >95%
- Overall Accuracy >80%
- Category Accuracy >90% for critical fields

### **Needs Improvement**
- Character Accuracy <50%
- Overall Accuracy <70%
- Frequent failures in specific categories

### **Common Issues & Solutions**

| Issue | Solution |
|-------|----------|
| Low character accuracy | Improve image preprocessing |
| Missing medical terms | Add medical dictionary to OCR |
| Poor date recognition | Enhance date pattern recognition |
| Medication name errors | Improve drug name whitelist |

## 🔍 **Troubleshooting**

### **OCR Service Not Available**
```bash
# Check Tesseract installation
tesseract --version

# Install if missing
choco install tesseract -y  # Windows
# or
brew install tesseract      # macOS
```

### **No Test Documents Found**
```bash
# Check folder structure
ls test_documents/

# Ensure supported formats
# Supported: .png, .jpg, .jpeg, .pdf, .tiff
```

### **Poor Accuracy Results**
1. **Check image quality**: Ensure good contrast and resolution
2. **Review preprocessing**: Adjust image enhancement parameters
3. **Test different fonts**: Some fonts OCR better than others
4. **Consider image size**: OCR works better on larger images

## 📊 **Output Files**

### **Results JSON Structure**
```json
{
  "approach": "synthetic",
  "individual_results": [
    {
      "test_case": "patient_name_simple",
      "category": "patient_info",
      "expected": "John R. Doe",
      "extracted": "Patient: John R. Doe",
      "metrics": {
        "char_accuracy": 0.64,
        "word_accuracy": 0.97,
        "overall_accuracy": 0.64
      },
      "success": false
    }
  ],
  "summary": {
    "total_tests": 10,
    "pass_rate": 0.0,
    "avg_overall_accuracy": 0.56
  }
}
```

## 🚀 **Integration with Main Application**

The testing framework integrates seamlessly with your Clinical FHIR Extractor:

```python
from app.ocr_service import OCRService
from test_tesseract_accuracy import TesseractAccuracyTester

# Test current OCR setup
tester = TesseractAccuracyTester()
results = tester.run_test("synthetic")

# Use results to improve OCR
if results['summary']['avg_overall_accuracy'] < 0.8:
    print("OCR accuracy needs improvement")
    # Adjust preprocessing parameters
```

## 📈 **Performance Benchmarks**

### **Expected Performance**
- **Synthetic Data**: 80-95% accuracy
- **Real Documents**: 70-90% accuracy
- **Processing Time**: <2 seconds per document
- **Memory Usage**: <100MB per test

### **Improvement Tracking**
Run tests regularly to track OCR improvements:
```bash
# Baseline test
python test_tesseract_accuracy.py > baseline_results.txt

# After improvements
python test_tesseract_accuracy.py > improved_results.txt

# Compare results
diff baseline_results.txt improved_results.txt
```

## 🤝 **Contributing**

To add new test cases or improve the framework:

1. **Add test cases** to `approach_1_synthetic_data()`
2. **Extend categories** in `calculate_category_accuracy()`
3. **Improve metrics** in accuracy calculation methods
4. **Add new document types** for real document testing

## 📝 **License**

This testing framework is part of the Clinical FHIR Extractor project and follows the same license terms.

---

**Happy Testing! 🧪✨**

For questions or issues, please refer to the main project documentation or create an issue in the repository.
