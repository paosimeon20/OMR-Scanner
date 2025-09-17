# Functional Requirements Document (FRD)  
**Project**: Optical Mark Recognition (OMR) Scanner  
**Version**: 1.1  
**Date**: September 17, 2025  
**Author**: Paolo Simeon Satuito  

---

## Table of Contents
1. Executive Summary  
2. Business Context and Objectives  
3. Stakeholder Analysis  
4. Functional Requirements  
   - 4.1 User Functions  
   - 4.2 System Functions  
   - 4.3 Data Requirements  
5. Business Rules and Logic  
6. User Interface Requirements  
7. Reporting and Analytics  
8. Integration Requirements  
9. Security and Access Control  
10. Performance and Scalability  
11. Acceptance Criteria  
12. Requirements Traceability Matrix  

---

## 1. Executive Summary
### Project Overview  
The OMR Scanner is a software application that enables schools and educators to automatically check multiple-choice exam sheets using a **Windows mini PC** with a **USB webcam**. It supports 50-item ZipGrade-style answer sheets, student ID mapping, scoring, statistics generation, and result export.  

### Scope  
- **In-scope**: Answer sheet scanning, validation, annotation, scoring, statistics, result storage, and export.  
- **Out-of-scope**: Mobile-native apps, LMS integration, hardware OMR machines.  

### Stakeholders  
- Teachers (primary users)  
- Students (end beneficiaries)  
- School administrators (data consumers)  
- IT support staff (technical maintenance)  

### Success Criteria  
- Accuracy ≥ 95% in answer detection  
- Average processing time ≤ 5 seconds per sheet  
- Zero duplicate student IDs within a session  
- Exportable results in CSV/XLSX  

---

## 2. Business Context and Objectives
### Problem Statement  
Manual checking of exam sheets is time-consuming, error-prone, and inefficient.  

### Strategic Objectives  
- Automate grading to save teacher time  
- Provide instant feedback and statistics  
- Enable data-driven academic decisions  

### KPIs  
- Time saved per exam batch  
- Accuracy of scanned results  
- Teacher adoption rate  

### Assumptions & Constraints  
- Users have access to a **Windows 10/11 mini PC with webcam**  
- Answer sheet format follows standardized template (50 items, 5 choices)  

### Business Case  
The OMR scanner reduces grading time by up to 80%, improves accuracy, and provides administrators with insights into student performance trends.  

---

## 3. Stakeholder Analysis
| Stakeholder        | Role | Needs | Authority |  
|--------------------|------|-------|-----------|  
| Teacher            | Primary user | Accurate, fast grading | Approves usage in class |  
| Student            | Beneficiary | Fair and fast results | N/A |  
| Administrator      | Oversight | Access to statistics and trends | Approves deployment |  
| IT Staff           | Support | Ease of setup and troubleshooting | Maintains system |  

**User Personas**  
- **Tech-savvy teacher**: Wants fast exports & live preview.  
- **Non-technical teacher**: Needs simple, touch-friendly UI.  
- **Admin**: Focused on big-picture reporting.  

---

## 4. Functional Requirements

### 4.1 User Functions
**User Story Example**
```text
As a teacher,  
I want to scan student exam sheets using a webcam,  
So that I can automatically grade and export results.  

Acceptance Criteria:  
- Given a loaded answer key and class section  
- When I click "Scan" with a camera input  
- Then the system processes the sheet, validates answers, and displays scores.  
