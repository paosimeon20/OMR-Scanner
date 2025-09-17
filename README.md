# 📝 OMR Scanner (Optical Mark Recognition)

## 📖 Overview
OMR Scanner is a desktop application that automates the grading of multiple-choice exams using a **Windows Mini PC + webcam**.  
It detects filled answer bubbles, validates them against an answer key, and produces annotated sheets, scores, and class statistics.

## 🚀 Features
- Scan 50-item exam sheets using a USB webcam
- Student ID recognition & duplicate prevention
- Auto-grading with annotated feedback:
  - ✅ Green = Correct
  - ❌ Red = Wrong
  - 🚫 No Answer
- Score export in CSV/XLSX format
- Class statistics (mean, median, mode, trends)
- Touch-friendly and professional UI

## 🖥️ System Requirements
- **OS**: Windows 10/11  
- **Hardware**: Mini PC, UVC-compatible webcam  
- **Python**: 3.9+  

## ⚙️ Installation
```bash
# Clone repo
git clone https://github.com/paosimeon20/OMR-Scanner.git
cd OMR-Scanner

# Setup environment
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
