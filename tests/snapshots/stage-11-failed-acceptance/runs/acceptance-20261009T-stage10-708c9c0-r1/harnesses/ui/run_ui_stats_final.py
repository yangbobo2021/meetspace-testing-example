import run_ui_acceptance as b
from run_ui_acceptance import *
from run_ui_supplement import statistics
if __name__=='__main__':
 data=json.load(open(RUN/'ui-results.json'));b.results={r['method_id']:{k:v for k,v in r.items() if k!='method_id'} for r in data['method_results']};b.groups=json.load(open(E/'progress.json'))['groups'];b.serial=940
 with sync_playwright() as pw:
  b.browser=pw.chromium.launch(headless=True);group('stats-real-zero-per-day-and-identity',['AI-room-discovery-8','AI-WB-ui-filters-statistics'],statistics,True);b.browser.close()
