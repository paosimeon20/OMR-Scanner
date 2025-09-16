# config.py
# Centralized constants and calibration for the OMR app.

import os

# =============== Config ===============
OUTPUT_ROOT = "omr_annotations"   # root for all sessions
DEFAULT_KEY_FILE = "answer_key_50.txt"
LETTERS = ['A','B','C','D','E']
DIGITS_TOP_TO_BOTTOM = ['1','2','3','4','5','6','7','8','9','0']
WARP_W, WARP_H, PAD = 1200, 1600, 80
ROWS_PER_COL, COLS = 10, 5  # 10 rows × 5 cols per ROI = 50 items across 5 ROIs

# ---- Replace with your latest calibration if needed ----
CALIB = {
  "config": {
    "row_top_margin": 0.06,
    "row_bottom_margin": 0.06,
    "col_left_margin": 0.08,
    "col_right_margin": 0.08,
    "radius_scale": 0.39256198347107435,
    "abs_min": 0.01,
    "margin": 0.01,
    "z_min": 0.6,
    "row_shift_px": 0,
    "col_shift_px": 0,
    "force_pick": False,
    "mark_blanks": True
  },
  "rois_answers": [
    [0.558303886925795, 0.9063670411985019, 0.18815331010452963, 0.3763440860215054],
    [0.18374558303886926, 0.528957528957529, 0.43309859154929575, 0.6204379562043796],
    [0.558303886925795, 0.9073359073359073, 0.43661971830985913, 0.6167883211678832],
    [0.18374558303886926, 0.5328185328185329, 0.676056338028169, 0.8613138686131386],
    [0.56, 0.9073359073359073, 0.6725352112676056, 0.8613138686131386]
  ],
  "roi_id": [0.18021201413427562, 0.528957528957529, 0.18309859154929578, 0.38321167883211676]
}
CFG = CALIB["config"]
ANSWER_ROIS = CALIB["rois_answers"]
ROI_ID = CALIB["roi_id"]

