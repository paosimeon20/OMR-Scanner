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



Requirements

REQ-U1: Load Answer Key (TXT) → must include exam name.

REQ-U2: Load Class Section (TXT) → includes student names + IDs.

REQ-U3: Capture image via webcam or upload.

REQ-U4: Annotate scanned sheet with GREEN (correct), RED (wrong), “NO ANSWER”.

REQ-U5: Display per-student scores.

REQ-U6: Export results (CSV/XLSX).

REQ-U7: Show statistics (mean, median, mode, trend).

REQ-U8: Prevent scanning without answer key and class section.

REQ-U9: Show error if duplicate student ID appears.

REQ-U10: Allow exam length selection (1–50).

4.2 System Functions

REQ-S1: Detect corner squares for alignment (half-size).

REQ-S2: Map bubbled answers (A–E).

REQ-S3: Validate answers vs. key.

REQ-S4: Store annotated images in session folder.

REQ-S5: Auto-create session folder <Exam> - <Section> - <Date>.

REQ-S6: Calculate score statistics dynamically.

4.3 Data Requirements

REQ-D1: Store exam name, section name, student names & IDs.

REQ-D2: Store answer keys and scanned results.

REQ-D3: Retain data until exported by teacher.

REQ-D4: Export in CSV/XLSX format.

5. Business Rules and Logic

Example Rule

BR-01: A student’s exam cannot be processed unless both an answer key and class section are loaded.  
Conditions: Scan attempted without setup  
Actions: Show error dialog  
Exceptions: None  


Other rules:

BR-02: Duplicate student ID → error + prevent scan.

BR-03: Max exam items defined by teacher → ignore excess items.

BR-04: Wrong answer = mark red; Correct = green; No answer = “NO ANSWER” label.

6. User Interface Requirements

Clean, professional layout with touch-friendly buttons.

Consistent color theme (#272757, #8686AC, #505081, #0F0E47).

Large dropdown for exam length.

Scrollable Scores and Statistics tabs.

Sticky bottom status bar.

7. Reporting and Analytics

REQ-R1: Student-level score reports.

REQ-R2: Class statistics (mean, median, mode).

REQ-R3: Highest/lowest score + student names.

REQ-R4: Trend chart of scores.

REQ-R5: Item analysis (% correct per question).

8. Integration Requirements

REQ-I1: Import answer key/class list from TXT.

REQ-I2: Export results in CSV/XLSX.

REQ-I3: Optional integration with Excel for analysis.

9. Security and Access Control

Local authentication not required (single-user design).

Student data must not be shared externally without consent.

System must generate logs of session activities.

10. Performance and Scalability

REQ-P1: Scan accuracy ≥ 95%.

REQ-P2: Max processing time ≤ 5s per sheet.

REQ-P3: Support up to 200 students per session.

REQ-P4: System available 99% of the time.

11. Acceptance Criteria

Functional: All REQ-U, REQ-S, REQ-D satisfied.

Accuracy: ≥ 95% recognition rate.

Performance: ≤ 5s per sheet.

Reliability: No duplicate ID entries allowed.

Compliance: Data export works on Windows 10/11 mini PCs.

12. Requirements Traceability Matrix
Requirement ID	Business Objective	Priority	Dependency	Verification Method
REQ-U1	Automate grading	High	None	Functional test
REQ-U3	Enable scanning	High	Webcam input	System test
REQ-U6	Export results	High	REQ-D4	User acceptance test
REQ-S2	Map answers	High	REQ-S1	System test
REQ-R4	Trend chart	Medium	REQ-D2	Functional test
REQ-P2	Fast grading	High	REQ-S2	Performance test
